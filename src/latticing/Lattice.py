from prompts import OBSERVATION_TO_INSIGHT_PROMPT, MAP_EVIDENCE_PROMPT, FORMAT_INSIGHT_PROMPT, INSIGHT_SYNTHESIS_PROMPT
from utils import batched_call, parse_model_json, parse_model_json_with_fallback
from AsyncLLM import AsyncLLM
from SyncLLM import SyncLLM
from Observer import Observer
from Visualize import Visualizer
from Layers import LatticeLayer, Sequential, SessionLayer, AllLayer
from models import Insights, SupportingObservationsResponse
import json
import logging
import numpy as np
import math
import pickle
import time
from tqdm import tqdm

logger = logging.getLogger(__name__)


class Lattice:
    def __init__(self, 
        name: str, 
        interactions: list, 
        description: str,
        insight_model: AsyncLLM, 
        observer_model: AsyncLLM,
        evidence_model: AsyncLLM, 
        format_model: SyncLLM, 
        config: Sequential | None = None,
        observations: list | None = None, 
        params: dict = {"max_concurrent": 100, "min_insights": 3, "window_size": 10}
    ):
        # set parameters
        self.max_concurrent = params["max_concurrent"] if "max_concurrent" in params else 100
        self.min_insights = params["min_insights"] if "min_insights" in params else 3
        self.window_size = params["window_size"] if "window_size" in params else 10

        self.observer = Observer(name=name, model=observer_model, format_model=format_model, description=description, params={"window_size": self.window_size, "max_concurrent": self.max_concurrent})

        self.interactions = interactions
        self.name = name    
        self.lattice = {"nodes": {0: []}, "edges": {1: []}}
        self.model = insight_model
        self.evidence_model = evidence_model
        self.format_model = format_model
        self.config = config


        if observations is not None:
            self.observations = observations
            self.lattice["nodes"][0] = self.observations
            self.current_layer = self.observations
            self.num_nodes = [len(self.observations)]
            self.layer_num = 1
        else:
            self.current_layer = []
            self.num_nodes = []
            self.layer_num = 0
            self.observations = None

    
    
    def _fmt_nodes(self, nodes: list, node_type: str):
        """
        Format the nodes for the model.
        """
        fmt_nodes = []
        for node in nodes:
            if node_type == "observation":
                fmt_nodes.append(f"ID: {node['id']} | {node['observation']}\n")
            elif node_type == "insight":
                fmt_nodes.append(f"ID: {node['id']} | {node['title']}: {node['insight']} | Context Insight Applies: {node['context']}\n")
            else:
                raise ValueError(f"Node type {node_type} not supported")
        return "\n".join(fmt_nodes)
    
    def auto_config(self, target_layer_num: int | None = None):
        # suggests config for the lattice based on rough heuristics
        # TODO: Update this to be more sophisticated
        num_interactions = len(self.interactions)
        nminus_layer_size = 10
        if num_interactions < nminus_layer_size:
            self.config = Sequential(SessionLayer(n=1), AllLayer())
            return self.config
        if target_layer_num is None:
            target_layer_num = max(2, math.floor(math.log(num_interactions, 10)))    
        n = max(2, math.ceil(math.log(num_interactions / nminus_layer_size, target_layer_num)))
        layers = [SessionLayer(n=n) for _ in range(target_layer_num)]
        layers.append(AllLayer())
        print(f"Generated a config with {target_layer_num} layers")
        self.config = Sequential(*layers)
        return self.config
    
    def print_layer(self, layer_num: int | None = None):
        """
        Print the insights in a layer (defaults to the current layer).
        """
        nodes = self.lattice["nodes"][layer_num] if layer_num is not None else self.current_layer
        if not nodes:
            print("(empty layer)")
            return
        sample = nodes[0]
        is_insight = "title" in sample

        for node in nodes:
            if is_insight:
                print(f"[{node['id']}] {node['title']}")
                print(f"     {node['insight']}")
                print(f"     Context: {node['context']}")
                meta = node.get("metadata", {})
                if meta:
                    print(f"     Metadata: {meta}")
            else:
                print(f"[{node['id']}] {node['observation']}")
                meta = node.get("metadata", {})
                if meta:
                    print(f"     Metadata: {meta}")
            print()


    async def _build_first_edges(self, grouped_obs: list, insights: list):
        """
        Build the edges for the first layer of the lattice.

        Returns one result per insight (same order).  Failed items are
        returned as BaseException instances so callers can skip them without
        losing the rest of the batch.
        """
        edges = []
        for insight in insights:
            sid = insight["metadata"]["input_session"]
            session_observations = self._fmt_nodes(grouped_obs[sid], "observation")
            prompt = MAP_EVIDENCE_PROMPT.format(observations=session_observations, evidence=insight["supporting_evidence"]) 
            edges.append(self.evidence_model.call(prompt,       resp_format=SupportingObservationsResponse))
        return await batched_call(edges, max_concurrent=self.max_concurrent, return_exceptions=True)
    
    async def make_observations(self):
        """
        Make observations for the interactions.
        """
        print(f"[Lattice] Making observations for {len(self.interactions)} interactions...")
        t0 = time.time()
        self.observations = await self.observer.observe(self.interactions)
        self.lattice["nodes"][0] = self.observations
        self.current_layer = self.observations
        self.layer_num = 1
        self.num_nodes.append(len(self.observations))
        print(f"[Lattice] Observations done: {len(self.observations)} observations in {time.time()-t0:.1f}s")
        return self.observations
    
    async def make_first_layer(self, layer: LatticeLayer):
        """
        Make the first layer of the lattice turning observations into insights.
        """
        grouped_nodes = layer.split(self.current_layer)
        n_groups = len(grouped_nodes)

        # Stage 1: generate raw insights per group
        print(f"[Layer {self.layer_num}] Generating insights for {n_groups} groups of observations...")
        t0 = time.time()
        raw_results = await batched_call(
            [
                self.model.call(OBSERVATION_TO_INSIGHT_PROMPT.format(
                    user_name=self.name,
                    observations=self._fmt_nodes(group, "observation"),
                    limit=self.min_insights,
                ))
                for group in tqdm(grouped_nodes, desc="  Preparing prompts", leave=False)
            ],
            max_concurrent=self.max_concurrent,
            return_exceptions=True,
        )
        print(f"[Layer {self.layer_num}] Raw insights done in {time.time()-t0:.1f}s")

        valid_raw: list[tuple[int, str]] = []
        for sid, result in enumerate(raw_results):
            if isinstance(result, BaseException):
                logger.error("Insight generation failed for group %d, skipping: %s", sid, result)
            else:
                valid_raw.append((sid, result))
        print(f"[Layer {self.layer_num}] {len(valid_raw)}/{n_groups} groups succeeded, formatting...")

        # Stage 2: format valid raw insights
        t1 = time.time()
        formatted_results = await batched_call(
            [self.model.call(FORMAT_INSIGHT_PROMPT.format(insights=raw), Insights) for _, raw in valid_raw],
            max_concurrent=self.max_concurrent,
            return_exceptions=True,
        )
        print(f"[Layer {self.layer_num}] Formatting done in {time.time()-t1:.1f}s")

        output_insights = []
        insight_id = 0
        for (sid, _), formatted in zip(valid_raw, formatted_results):
            if isinstance(formatted, BaseException):
                logger.error("Insight formatting failed for group %d, skipping: %s", sid, formatted)
                logger.error(formatted)
                continue
            insights = Insights.model_validate(formatted) if not isinstance(formatted, Insights) else formatted
            for insight in insights.insights:
                insight_dict = insight.model_dump()
                insight_dict["id"] = insight_id
                insight_dict["metadata"] = {"input_session": sid}
                node_meta = grouped_nodes[sid][-1].get("metadata", {})
                if "time" in node_meta:
                    insight_dict["metadata"]["time"] = node_meta["time"]
                output_insights.append(insight_dict)
                insight_id += 1

        # Stage 3: build edges
        print(f"[Layer {self.layer_num}] Building edges for {len(output_insights)} insights...")
        t2 = time.time()
        edges = await self._build_first_edges(grouped_nodes, output_insights)
        print(f"[Layer {self.layer_num}] Edges done in {time.time()-t2:.1f}s")

        for eid, edge in enumerate(edges):
            if isinstance(edge, BaseException):
                logger.warning("Edge mapping failed for insight %d, skipping: %s", output_insights[eid]["id"], edge)
                continue
            edge = SupportingObservationsResponse.model_validate(edge)
            iid = output_insights[eid]["id"]
            output_insights[eid]["merged"] = edge.supporting_ids
            for supporting_id in edge.supporting_ids:
                self.lattice["edges"][self.layer_num].append({"source": iid, "target": supporting_id})

        print(f"[Layer {self.layer_num}] Complete: {len(output_insights)} insights (total {time.time()-t0:.1f}s)")
        self.lattice["nodes"][self.layer_num] = output_insights
        self.layer_num += 1
        self.num_nodes.append(len(output_insights))
        self.current_layer = output_insights
        return output_insights
    
    async def make_layer(self, layer: LatticeLayer, input_layer: list = None):
        """
        Make subsequent layers of the lattice turning insights into new insights.
        """
        if self.layer_num < 2:
            raise ValueError("Call make_first_layer first")

        if input_layer is not None:
            self.current_layer = input_layer

        grouped_nodes = layer.split(self.current_layer)
        n_groups = len(grouped_nodes)

        print(f"[Layer {self.layer_num}] Synthesizing insights for {n_groups} groups...")
        t0 = time.time()
        tasks = [
            self.model.call(INSIGHT_SYNTHESIS_PROMPT.format(
                user_name=self.name,
                insights=self._fmt_nodes(group, "insight"),
                limit=self.min_insights,
            ))
            for group in tqdm(grouped_nodes, desc="  Preparing prompts", leave=False)
        ]
        group_insights = await batched_call(tasks, max_concurrent=self.max_concurrent, return_exceptions=True)
        print(f"[Layer {self.layer_num}] Synthesis done in {time.time()-t0:.1f}s")

        output_insights = []
        insight_id = 0
        for sid, insights in enumerate(group_insights):
            if isinstance(insights, BaseException):
                logger.error("Insight synthesis failed for group %d, skipping: %s", sid, insights)
                continue
            try:
                insights = parse_model_json(insights)
            except Exception as e:
                logger.error("Error parsing insights for group %d: %s", sid, e)
                try:
                    insights = parse_model_json_with_fallback(insights, self.format_model, Insights)
                    insights = insights.model_dump()
                except Exception as e2:
                    logger.error("FallWback parsing failed for group %d, skipping: %s", sid, e2)
                    continue
            for insight_dict in insights['insights']:
                insight_dict["id"] = insight_id
                insight_dict["metadata"] = {"input_session": sid}
                node_meta = grouped_nodes[sid][-1].get("metadata", {})
                if "time" in node_meta:
                    insight_dict["metadata"]["time"] = node_meta["time"]
                output_insights.append(insight_dict)
                insight_id += 1

        self.lattice["edges"][self.layer_num] = []
        for insight in output_insights:
            if "merged" in insight and insight["merged"] is not None:
                for merged_id in insight["merged"]:
                    self.lattice["edges"][self.layer_num].append({"source": insight["id"], "target": merged_id})

        print(f"[Layer {self.layer_num}] Complete: {len(output_insights)} insights (total {time.time()-t0:.1f}s)")
        self.lattice["nodes"][self.layer_num] = output_insights
        self.layer_num += 1
        self.num_nodes.append(len(output_insights))
        self.current_layer = output_insights

        return output_insights
    
    async def forward(self):
        """
        One forward pass through the lattice.
        """
        if self.config is None:
            raise ValueError("No config provided. Run auto_config() to generate a default config or provide a custom config.")
        layers = self.config

        n_layers = len(layers)
        print(f"[Lattice] Building with {n_layers} layer(s): {layers}")
        t_total = time.time()

        if self.observations is None:
            await self.make_observations()
            print(f"Saving observations")
            json.dump(self.observations, open("observations.json", "w")) # TODO: save to a more permanent location
        else:
            print(f"[Lattice] Using {len(self.observations)} pre-loaded observations")

        for i, layer in tqdm(enumerate(layers), total=n_layers, desc="Lattice layers"):
            if i == 0:
                await self.make_first_layer(layer=layer)
            else:
                await self.make_layer(layer=layer)

        print(f"[Lattice] Build complete in {time.time()-t_total:.1f}s | layers: {self.num_nodes}")

    def save(self, save_path: str = "lattice.json"):
        """
        Save the lattice to a file.
        """
        with open(save_path, "w") as f:
            json.dump(self.lattice, f)
        
    def save_object(self, save_path: str = "lattice.pkl"):
        """
        Save the lattice to a pickle file.
        """
        output = {
            "lattice": self.lattice,
            "config": self.config,
            "interactions": self.interactions,
            "observations": self.observations,
            "name": self.name,
        }
        with open(save_path, "wb") as f:
            pickle.dump(output, f)
    
    async def backward(self):
        return ValueError("Backward pass not implemented")
    
    async def build(self):
        """
        Build the lattice through passes
        TODO: Implement backward pass
        """
        await self.forward()
    
    def visualize(self, load_path: str | None = None):
        """
        Return an interactive Plotly figure of the lattice.

        Nodes are arranged by layer on the y-axis and distributed evenly on the
        x-axis.  Hover over any node to read its full text.  Call
        ``fig.show()`` on the returned figure to open it in a browser, or pass
        it directly to Dash / Streamlit.

        Args:
            load_path: Optional path to a saved lattice JSON file.  If given,
                       the file is loaded and visualized instead of
                       ``self.lattice``.
        """
        if load_path is not None:
            with open(load_path, "r") as f:
                to_diagram = json.load(f)
        else:
            to_diagram = self.lattice
        visualizer = Visualizer(to_diagram)
        return visualizer.basic_diagram()

    def visualize_widget(self, load_path: str | None = None):
        """
        Return an ipywidgets inspector for the last layer of the lattice.

        Displays a scrollable list of nodes in the last layer on the left.
        Selecting a node renders its full detail and all directly connected
        nodes from the layer below on the right.

        Args:
            load_path: Optional path to a saved lattice JSON file.
        """
        if load_path is not None:
            with open(load_path, "r") as f:
                to_diagram = json.load(f)
        else:
            to_diagram = self.lattice
        visualizer = Visualizer(to_diagram)
        return visualizer.visualize_widget()
