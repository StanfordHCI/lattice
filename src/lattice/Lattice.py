from re import S
from prompts import OBSERVATION_TO_INSIGHT_PROMPT, MAP_EVIDENCE_PROMPT, FORMAT_INSIGHT_PROMPT, INSIGHT_SYNTHESIS_PROMPT
from utils import batched_call, parse_model_json, parse_model_json_with_fallback
from AsyncLLM import AsyncLLM
from SyncLLM import SyncLLM
from Observer import Observer
from Visualize import Visualizer
from models import Insights, Separator, SupportingObservationsResponse
import json
import logging
import textwrap

logger = logging.getLogger(__name__)


class Lattice:
    def __init__(self, name: str, interactions: list, description: str,
    model: AsyncLLM, evidence_model: AsyncLLM, format_model: SyncLLM, observations: list | None = None, params: dict = {"max_concurrent": 100, "min_insights": 3, "window_size": 10}):
        # set parameters
        self.max_concurrent = params["max_concurrent"] if "max_concurrent" in params else 100
        self.min_insights = params["min_insights"] if "min_insights" in params else 3
        self.window_size = params["window_size"] if "window_size" in params else 10

        self.observer = Observer(name=name, model=model, format_model=format_model, description=description, params={"window_size": self.window_size, "max_concurrent": self.max_concurrent})

        self.interactions = interactions
        self.name = name    
        self.lattice = {"nodes": {0: []}, "edges": {1: []}}
        self.model = model
        self.evidence_model = evidence_model
        self.format_model = format_model



        if observations is not None:
            self.observations = observations
            self.current_layer = self.observations
            self.num_nodes = [len(self.observations)]
            self.layer_num = 1
        else:
            self.current_layer = []
            self.num_nodes = []
            self.layer_num = 0
            self.observations = None

    
    def _split_by_time(self, nodes: list, separate_by: str) -> list:
        """
        Validate that every node has a 'time' field in its metadata, then
        group nodes into buckets by day, week, month, or year.

        Args:
            nodes: List of node dicts, each with metadata["time"] as a
                   datetime-parseable string.
            separate_by: One of "day", "week", "month", "year".

        Returns:
            List of lists; each inner list contains all nodes that share the
            same time bucket, in chronological order within the bucket.
            Buckets themselves are ordered chronologically.
        """
        from datetime import datetime

        if separate_by not in ("day", "week", "month", "year"):
            raise ValueError(
                f"separate_by must be 'day', 'week', 'month', or 'year'; got '{separate_by}'."
            )

        missing = [i for i, n in enumerate(nodes) if "time" not in n.get("metadata", {})]
        if missing:
            raise ValueError(
                f"Nodes at indices {missing} are missing 'time' in metadata."
            )

        def bucket_key(node):
            dt = datetime.fromisoformat(node["metadata"]["time"])
            if separate_by == "day":
                return (dt.year, dt.month, dt.day)
            elif separate_by == "week":
                iso = dt.isocalendar()
                return (iso.year, iso.week)
            elif separate_by == "month":
                return (dt.year, dt.month)
            else:  # year
                return (dt.year,)

        sorted_nodes = sorted(nodes, key=bucket_key)

        groups = []
        current_key = None
        for node in sorted_nodes:
            key = bucket_key(node)
            if key != current_key:
                groups.append([])
                current_key = key
            groups[-1].append(node)

        return groups

    def _split_by_session(self, nodes: list, session_number: int) -> list:
        """
        Sort nodes by metadata["input_session"], group them into per-session
        buckets, then chunk those buckets into groups of *session_number*.

        Args:
            nodes: List of node dicts, each with metadata["input_session"] as
                   an integer session identifier.
            session_number: How many sessions to merge into each output group.
                            1 → each session is its own group.
                            2 → every two consecutive sessions form one group.

        Returns:
            List of lists ordered by session; each inner list contains all
            nodes belonging to that chunk of sessions.
        """
        if session_number < 1:
            raise ValueError(f"session_number must be >= 1; got {session_number}.")

        missing = [i for i, n in enumerate(nodes) if "input_session" not in n.get("metadata", {})]
        if missing:
            raise ValueError(f"Nodes at indices {missing} are missing 'input_session' in metadata.")

        sorted_nodes = sorted(nodes, key=lambda n: n["metadata"]["input_session"])

        # Collect nodes into ordered per-session buckets
        session_buckets: dict[int, list] = {}
        for node in sorted_nodes:
            sid = node["metadata"]["input_session"]
            if sid not in session_buckets:
                session_buckets[sid] = []
            session_buckets[sid].append(node)

        # Chunk the buckets and flatten each chunk into one group
        ordered = list(session_buckets.values())
        groups = []
        for i in range(0, len(ordered), session_number):
            chunk = ordered[i : i + session_number]
            groups.append([node for session in chunk for node in session])

        return groups

    def _split_input(self, input_nodes: list, separator: Separator):
        """
        Split the input into a list of strings based on the separator.
        """
        if separator.type == "time":
            return self._split_by_time(input_nodes, separator.value)
        elif separator.type == "session":
            return self._split_by_session(input_nodes, int(separator.value))
        elif separator.type == "number":
            return self._split_by_number(input_nodes, int(separator.value))
        else:
            raise ValueError(f"Separator type {separator.type!r} not supported")
    
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
        self.observations = await self.observer.observe(self.interactions)
        self.lattice["nodes"][0] = self.observations
        self.current_layer = self.observations
        self.layer_num = 1
        self.num_nodes.append(len(self.observations))
        return self.observations
    
    async def make_first_layer(self, separator: Separator):
        """
        Make the first layer of the lattice turning observations into insights.
        """
        grouped_nodes = self._split_input(self.current_layer, separator)

        # Stage 1: generate raw insights per group
        logger.info("Generating insights for %d groups of observations", len(grouped_nodes))
        raw_results = await batched_call(
            [
                self.model.call(OBSERVATION_TO_INSIGHT_PROMPT.format(
                    user_name=self.name,
                    observations=self._fmt_nodes(group, "observation"),
                    limit=self.min_insights,
                ))
                for group in grouped_nodes
            ],  
            max_concurrent=self.max_concurrent,
            return_exceptions=True,
        )

        valid_raw: list[tuple[int, str]] = []  # (original group index, raw text)
        for sid, result in enumerate(raw_results):
            if isinstance(result, BaseException):
                logger.error("Insight generation failed for group %d, skipping: %s", sid, result)
            else:
                valid_raw.append((sid, result))

        # Stage 2: format valid raw insights
        logger.info("Formatting insights for %d groups", len(valid_raw))
        formatted_results = await batched_call(
            [self.model.call(FORMAT_INSIGHT_PROMPT.format(insights=raw), Insights) for _, raw in valid_raw],
            max_concurrent=self.max_concurrent,
            return_exceptions=True,
        )

        output_insights = []
        insight_id = 0
        for (sid, _), formatted in zip(valid_raw, formatted_results):
            if isinstance(formatted, BaseException):
                logger.error("Insight formatting failed for group %d, skipping: %s", sid, formatted)
                continue
            insights = Insights.model_validate(formatted) if not isinstance(formatted, Insights) else formatted
            for insight in insights.insights:
                insight_dict = insight.model_dump()
                insight_dict["id"] = insight_id
                insight_dict["metadata"] = {"input_session": sid}
                if "time" in grouped_nodes[sid][-1]["metadata"]:
                    insight_dict["metadata"]["time"] = grouped_nodes[sid][-1]["metadata"]["time"]
                output_insights.append(insight_dict)
                insight_id += 1

        # Stage 3: build edges; _build_first_edges returns exceptions in-place
        logger.info("Building edges mapping observations to insights")
        edges = await self._build_first_edges(grouped_nodes, output_insights)

        for eid, edge in enumerate(edges):
            if isinstance(edge, BaseException):
                logger.warning("Edge mapping failed for insight %d, skipping: %s", output_insights[eid]["id"], edge)
                continue
            edge = SupportingObservationsResponse.model_validate(edge)
            iid = output_insights[eid]["id"]
            output_insights[eid]["merged"] = edge.supporting_ids
            for supporting_id in edge.supporting_ids:
                self.lattice["edges"][self.layer_num].append({"source": iid, "target": supporting_id})

        logger.info("Number of nodes in layer %d: %d", self.layer_num, len(output_insights))
        self.lattice["nodes"][self.layer_num] = output_insights
        self.layer_num += 1
        self.num_nodes.append(len(output_insights))
        self.current_layer = output_insights
        return output_insights
    
    async def make_layer(self, separator: Separator, input_layer: list = None):
        """
        Make subsequent layers of the lattice turning insights into new insights.
        """
        if self.layer_num < 2:
            raise ValueError("Call make_first_layer first")

        if input_layer is not None:
            self.current_layer = input_layer

        grouped_nodes = self._split_input(self.current_layer, separator)
        
        # Generate insights for each group of observations
        logger.info(f"Generating insights for {len(grouped_nodes)} groups of insights")
        tasks = []
        for group in grouped_nodes:
            fmt_nodes = self._fmt_nodes(group, "insight")
            input_prompt = INSIGHT_SYNTHESIS_PROMPT.format(user_name=self.name, insights=fmt_nodes, limit=self.min_insights)
            tasks.append(self.model.call(input_prompt))
        group_insights = await batched_call(tasks, max_concurrent=self.max_concurrent, return_exceptions=True)

        output_insights = []
        insight_id = 0
        for sid, insights in enumerate(group_insights):
            if isinstance(insights, BaseException):
                logger.error("Insight synthesis failed for group %d, skipping: %s", sid, insights)
                continue
            try:
                insights = parse_model_json(insights)
            except Exception as e:
                logger.error(f"Error parsing insights: {e}")
                insights = parse_model_json_with_fallback(insights, self.format_model, Insights)
                insights = insights.model_dump()
            for insight_dict in insights['insights']:
                insight_dict["id"] = insight_id
                insight_dict["metadata"] = {
                    "input_session": sid,
                }
                if "time" in grouped_nodes[sid][-1]["metadata"]:
                    # inherit the time of the last node in the group
                    insight_dict["metadata"]["time"] = grouped_nodes[sid][-1]["metadata"]["time"]
                output_insights.append(insight_dict)
                insight_id += 1
        
        # Add edges for the new insights
        logger.info(f"Building edges mapping insights to insights")
        self.lattice["edges"][self.layer_num] = []
        for insight in output_insights:
            if "merged" in insight and insight["merged"] is not None:
                for merged_id in insight["merged"]:
                    self.lattice["edges"][self.layer_num].append({"source": insight["id"], "target": merged_id})

        # Add the insights to the lattice
        logger.info(f"Number of nodes in layer {self.layer_num}: {len(output_insights)}")
        self.lattice["nodes"][self.layer_num] = output_insights 
        self.layer_num += 1
        self.num_nodes.append(len(output_insights))
        self.current_layer = output_insights

        return output_insights
    
    async def build(self, config: dict):
        """
        Build the lattice according to the config.
        """
        
        logger.info(f"Building lattice with config: {config}")
        if self.observations is None:
            logger.info(f"Making observations")
            await self.make_observations()
        else:
            logger.info(f"Observations loaded")

        for layer in config:
            logger.info(f"Building layer {self.layer_num}")
            config_layer = Separator(type=config[layer]["type"], value=config[layer]["value"])
            if layer == 0:
                await self.make_first_layer(separator=config_layer)
            else:
                await self.make_layer(separator=config_layer)

    def save(self, save_path: str = "lattice.json"):
        """
        Save the lattice to a file.
        """
        with open(save_path, "w") as f:
            json.dump(self.lattice, f)
    
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

    