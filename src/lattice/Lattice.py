from prompts import OBSERVATION_TO_INSIGHT_PROMPT, MAP_EVIDENCE_PROMPT, FORMAT_INSIGHT_PROMPT, INSIGHT_SYNTHESIS_PROMPT
from consts import MAX_CONCURRENT, MIN_INSIGHTS
from utils import batched_call, parse_model_json, parse_model_json_with_fallback
from AsyncLLM import AsyncLLM
from SyncLLM import SyncLLM
from models import Insights, SupportingObservationsResponse
import json 

class Lattice:
    def __init__(self, name: str, observations: list, 
    model: AsyncLLM, evidence_model: AsyncLLM, format_model: SyncLLM):
        self.name = name    
        self.observations = observations
        self.lattice = {"nodes": {0: self.observations}, "edges": {1: []}}
        self.model = model
        self.evidence_model = evidence_model
        self.format_model = format_model
        self.layer_num = 1
        self.current_layer = self.observations
        self.num_nodes = [len(self.observations)]
    
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

    def _split_input(self, input_nodes: list, separator: dict):
        """
        Split the input into a list of strings based on the separator.
        """
        if separator["type"] == "time":
            return self._split_by_time(input_nodes, separator["value"])
        # elif separator["type"] == "observations":
        #     return input.split(separator["value"])
        # elif separator["type"] == "sessions":
        #     return input.split(separator["value"])
    
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
    
    def _save_lattice(self):
        """
        Save the lattice to a file.
        """
        with open("lattice.json", "w") as f:
            json.dump(self.lattice, f)

    async def _build_first_edges(self, grouped_obs: list, insights: list):
        """
        Build the edges for the first layer of the lattice.
        """
        edges = []
        for insight in insights:
            sid = insight["metadata"]["input_session"]
            session_observations = self._fmt_nodes(grouped_obs[sid], "observation")
            prompt = MAP_EVIDENCE_PROMPT.format(observations=session_observations, evidence=insight["supporting_evidence"])
            edges.append(self.evidence_model.call(prompt, resp_format=SupportingObservationsResponse))
        edges = await batched_call(edges, max_concurrent=MAX_CONCURRENT)
        return edges
        
    async def make_first_layer(self, separator: dict):
        """
        Make the first layer of the lattice turning observations into insights.
        """

        if separator["type"] not in ["time", "observations", "sessions"]:
            raise ValueError(f"Separator type {separator['type']} not supported")
        else:
            grouped_nodes = self._split_input(self.current_layer, separator)
        
        # Generate insights for each group of observations
        print(f"Generating insights for {len(grouped_nodes)} groups of observations")
        tasks = []
        for group in grouped_nodes:
            fmt_nodes = self._fmt_nodes(group, "observation")
            input_prompt = OBSERVATION_TO_INSIGHT_PROMPT.format(user_name=self.name, observations=fmt_nodes, limit=MIN_INSIGHTS)
            tasks.append(self.model.call(input_prompt))
        raw_insights = await batched_call(tasks, max_concurrent=MAX_CONCURRENT)

        print(f"Formatting insights")
        format_tasks = []
        for raw_insight in raw_insights:
            format_tasks.append(self.model.call(FORMAT_INSIGHT_PROMPT.format(insights=raw_insight), Insights))
        formatted_insights = await batched_call(format_tasks, max_concurrent=MAX_CONCURRENT)

        # Format the insights into a list of dicts
        output_insights = []
        insight_id = 0
        for sid, raw in enumerate(formatted_insights):
            insights = Insights.model_validate(raw) if not isinstance(raw, Insights) else raw
            for insight in insights.insights:
                insight_dict = insight.model_dump()
                insight_dict["id"] = insight_id
                insight_dict["metadata"] = {
                    "input_session": sid,
                }
                if "time" in grouped_nodes[sid][-1]["metadata"]:
                    # inherit the time of the last node in the group
                    insight_dict["metadata"]["time"] = grouped_nodes[sid][-1]["metadata"]["time"]
                output_insights.append(insight_dict)
                insight_id += 1

        # Build the edges for the first layer
        print(f"Building edges mapping observations to insights")
        edges = await self._build_first_edges(grouped_nodes, output_insights)
        print(edges)

        for eid, edge in enumerate(edges):
            edge = SupportingObservationsResponse.model_validate(edge)
            output_insights[eid]["merged"] = edge.supporting_ids
            insight_id = output_insights[eid]["id"]
            for supporting_id in edge.supporting_ids:
                self.lattice["edges"][self.layer_num].append({"source": insight_id, "target": supporting_id})

        print(self.lattice["edges"][self.layer_num])

        # Add the insights to the lattice
        print(f"Number of nodes in layer {self.layer_num}: ", len(output_insights))
        self.lattice["nodes"][self.layer_num] = output_insights 
        self.layer_num += 1
        self.num_nodes.append(len(output_insights))
        self.current_layer = output_insights
        return output_insights
    
    async def make_layer(self, separator: dict, input_layer: list = None):
        """
        Make subsequent layers of the lattice turning insights into new insights.
        """
        if input_layer is not None:
            self.current_layer = input_layer

        if separator["type"] not in ["time", "observations", "sessions"]:
            raise ValueError(f"Separator type {separator['type']} not supported")
        else:
            grouped_nodes = self._split_input(self.current_layer, separator)
        
        # Generate insights for each group of observations
        print(f"Generating insights for {len(grouped_nodes)} groups of insights")
        tasks = []
        for group in grouped_nodes:
            fmt_nodes = self._fmt_nodes(group, "insight")
            input_prompt = INSIGHT_SYNTHESIS_PROMPT.format(user_name=self.name, insights=fmt_nodes, limit=MIN_INSIGHTS)
            tasks.append(self.model.call(input_prompt))
        print(input_prompt)
        group_insights = await batched_call(tasks, max_concurrent=MAX_CONCURRENT)
        print(group_insights)

        output_insights = []
        insight_id = 0
        for sid, insights in enumerate(group_insights):
            try:
                insights = parse_model_json(insights)
            except Exception as e:
                print(f"Error parsing insights: {e}")
                insights = parse_model_json_with_fallback(insights, self.format_model, Insights)
                insights = insights.model_dump()
            for insight_dict in insights['insights']:
                print(insight_dict)
                insight_dict["id"] = insight_id
                insight_dict["metadata"] = {
                    "input_session": sid,
                }
                if "time" in grouped_nodes[sid][-1]["metadata"]:
                    # inherit the time of the last node in the group
                    insight_dict["metadata"]["time"] = grouped_nodes[sid][-1]["metadata"]["time"]
                output_insights.append(insight_dict)
        
        # Add edges for the new insights
        print(f"Building edges mapping insights to insights")
        self.lattice["edges"][self.layer_num] = []
        for insight in output_insights:
            for merged_id in insight["merged"]:
                self.lattice["edges"][self.layer_num].append({"source": insight["id"], "target": merged_id})

        # Add the insights to the lattice
        print(f"Number of nodes in layer {self.layer_num}: ", len(output_insights))
        self.lattice["nodes"][self.layer_num] = output_insights 
        self.layer_num += 1
        self.num_nodes.append(len(output_insights))
        self.current_layer = output_insights

        return output_insights
    

    