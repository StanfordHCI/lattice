import plotly.graph_objects as go
import json
import textwrap

class Visualizer:
    def __init__(self, lattice: dict):
        self.lattice = lattice


    def basic_diagram(self):
        def _wrap(text: str, width: int = 60) -> str:
            """Wrap long text into HTML line-breaks for Plotly hover labels."""
            return "<br>".join(textwrap.wrap(str(text), width))

        # Build (layer, node_id) -> position and hover text maps.
        # Layer keys are ints in memory but strings after a JSON round-trip.
        nodes_data = self.lattice["nodes"]
        layers = sorted(nodes_data.keys(), key=lambda k: int(k))

        pos: dict[tuple[int, int], tuple[float, int]] = {}
        hover_text: dict[tuple[int, int], str] = {}
        node_label: dict[tuple[int, int], str] = {}

        for layer_key in layers:
            layer = int(layer_key)
            layer_nodes = nodes_data[layer_key]
            n = len(layer_nodes)
            for idx, node in enumerate(layer_nodes):
                key = (layer, node["id"])
                pos[key] = (idx - (n - 1) / 2.0, layer)
                if "title" in node:  # insight node
                    hover_text[key] = (
                        f"<b>{_wrap(node['title'])}</b><br><br>"
                        f"{_wrap(node['insight'])}<br><br>"
                        f"<i>Context: {_wrap(node.get('context', ''))}</i>"
                    )
                    title = node["title"]
                    node_label[key] = title[:35] + ("…" if len(title) > 35 else "")
                else:  # observation node
                    obs = node.get("observation", "")
                    hover_text[key] = _wrap(obs)
                    node_label[key] = (obs[:35] + "…") if len(obs) > 35 else obs

        # Edge traces: one continuous Scatter with None separators between segments.
        edge_x: list[float | None] = []
        edge_y: list[float | None] = []
        for layer_key in sorted(self.lattice["edges"].keys(), key=lambda k: int(k)):
            layer = int(layer_key)
            for edge in self.lattice["edges"][layer_key]:
                src = (layer, edge["source"])
                tgt = (layer - 1, edge["target"])
                if src in pos and tgt in pos:
                    x0, y0 = pos[src]
                    x1, y1 = pos[tgt]
                    edge_x += [x0, x1, None]
                    edge_y += [y0, y1, None]

        traces: list[go.BaseTraceType] = [
            go.Scatter(
                x=edge_x,
                y=edge_y,
                mode="lines",
                line=dict(width=1, color="#cccccc"),
                hoverinfo="none",
                showlegend=False,
            )
        ]

        # One node Scatter per layer for distinct colors and a legend entry.
        palette = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3", "#FF6692", "#B6E880"]
        for i, layer_key in enumerate(layers):
            layer = int(layer_key)
            layer_nodes = nodes_data[layer_key]
            if not layer_nodes:
                continue

            xs = [pos[(layer, nd["id"])][0] for nd in layer_nodes]
            ys = [pos[(layer, nd["id"])][1] for nd in layer_nodes]
            hovers = [hover_text[(layer, nd["id"])] for nd in layer_nodes]

            traces.append(go.Scatter(
                x=xs,
                y=ys,
                mode="markers+text",
                marker=dict(
                    size=18,
                    color=palette[i % len(palette)],
                    line=dict(width=1.5, color="white"),
                ),
                hovertext=hovers,
                hoverinfo="text",
                name="Observations" if layer == 0 else f"Insights — layer {layer}",
            ))

        tick_labels = ["Observations"] + [f"Layer {i}" for i in range(1, len(layers))]
        fig = go.Figure(
            data=traces,
            layout=go.Layout(
                title=dict(text="Behavior Lattice", font=dict(size=18)),
                showlegend=True,
                hovermode="closest",
                plot_bgcolor="white",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="#eeeeee",
                    zeroline=False,
                    tickmode="array",
                    tickvals=list(range(len(layers))),
                    ticktext=tick_labels,
                ),
                margin=dict(b=20, l=100, r=20, t=60),
            ),
        )
        return fig
    