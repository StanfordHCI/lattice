from prompts import OBSERVATION_TO_INSIGHT_PROMPT, MAP_EVIDENCE_PROMPT, FORMAT_INSIGHT_PROMPT
from consts import MAX_CONCURRENT, MIN_INSIGHTS
from utils import batched_call, parse_model_json, parse_model_json_with_fallback
from AsyncLLM import AsyncLLM
from SyncLLM import SyncLLM
from models import Insights

class Lattice:
    def __init__(self, name: str, observations: list, model: AsyncLLM, evidence_model: SyncLLM, format_model: SyncLLM):
        self.name = name    
        self.observations = observations
        self.lattice = {"nodes": {0: self.observations}, "edges": {1: []}}
        self.model = model
        self.evidence_model = evidence_model
        self.format_model = format_model
        self.current_layer = 1
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
    
    def _build_first_edges(self, observations: list, insights: list):
        """
        Build the edges for the first layer of the lattice.
        """
        
        prompt = MAP_EVIDENCE_PROMPT.format(observations=observations, insights=insights)
        edges = self.evidence_model.call(prompt)
        return edges
    

    async def make_first_layer(self, separator: dict):
        """
        Make the first layer of the lattice turning observations into insights.
        """

        def _fmt_nodes(nodes: list):
            """
            Format the nodes for the model.
            """
            fmt_nodes = []
            for node in nodes:
                fmt_nodes.append(f"ID: {node['id']} | {node['observation']}\n")
            return "\n".join(fmt_nodes)

        if separator["type"] not in ["time", "observations", "sessions"]:
            raise ValueError(f"Separator type {separator['type']} not supported")
        else:
            grouped_nodes = self._split_input(self.observations, separator)
        
        # Generate insights for each group of observations
        print(f"Generating insights for {len(grouped_nodes)} groups of observations")
        tasks = []
        for group in grouped_nodes:
            fmt_nodes = _fmt_nodes(group)
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
        for sid, insights in enumerate(formatted_insights):
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
        for insight in output_insights:
            sid = insight["metadata"]["input_session"]



        # Add the insights to the lattice
        print(f"Number of nodes in layer {self.current_layer}: ", len(output_insights))
        self.lattice["nodes"][1] = output_insights 
        self.current_layer += 1
        self.num_nodes.append(len(output_insights))
        return output_insights
    
    def make_layer(self, layer_input: list, separator: dict):
        """
        Makes subsequent layers of the lattice by synthesizing insights from the previous layer.
        """
        if separator["type"] not in ["time", "observations", "sessions"]:
            raise ValueError(f"Separator type {separator['type']} not supported")
        else:
            layer_input = self._split_input(layer_input, separator)
        
        return insights
    