import plotly.graph_objects as go
import json
import textwrap

class Visualizer:
    def __init__(self, lattice: dict):
        self.lattice = lattice

    # ── helpers shared by both visualisations ────────────────────────
    @staticmethod
    def _layer_keys(lattice: dict) -> list:
        """Return node layer keys sorted numerically."""
        return sorted(lattice["nodes"].keys(), key=lambda k: int(k))

    @staticmethod
    def _edge_key(lattice: dict, layer: int):
        """Return the edge-dict key for *layer* (handles int vs str keys)."""
        for k in lattice["edges"]:
            if int(k) == layer:
                return k
        return None


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

    def visualize_widget(self):
        """
        Return an ipywidgets inspector for the last layer of the lattice.

        Left panel  — scrollable Select list of every node in the last layer.
        Right panel — full detail of the selected node, followed by collapsible
                      sections for every lower layer, each showing the nodes
                      reachable from the selection via edges.

        Requires ``ipywidgets`` (``pip install ipywidgets``).
        """
        try:
            import ipywidgets as widgets
            from IPython.display import display as _display, HTML as _IPHTML
        except ImportError as exc:
            raise ImportError(
                "ipywidgets is required for visualize_widget: pip install ipywidgets"
            ) from exc

        nodes_data = self.lattice["nodes"]
        layer_keys = self._layer_keys(self.lattice)

        if not layer_keys:
            return widgets.HTML("<i>Lattice is empty.</i>")

        last_key = layer_keys[-1]
        last_layer = int(last_key)
        last_nodes = nodes_data[last_key]

        # ── precompute per-layer lookups ───────────────────────────────
        nodes_by_layer: dict[str, dict[str, dict]] = {}
        for lk in layer_keys:
            li = str(lk)
            nodes_by_layer[li] = {str(n["id"]): n for n in nodes_data[lk]}

        edge_maps: dict[int, dict[int, list[int]]] = {}
        for lk in layer_keys:
            li = int(lk)
            ek = self._edge_key(self.lattice, li)
            if ek is not None:
                emap: dict[str, list[str]] = {}
                for edge in self.lattice["edges"][ek]:
                    emap.setdefault(str(edge["source"]), []).append(str(edge["target"]))
                edge_maps[str(li)] = emap

        # ── CSS injected via Output (not sanitized) ────────────────────
        _CSS = """
<style>
.lw-root { font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif; }
.lw-hdr  { font-size: 10px; font-weight: 700; letter-spacing: .1em;
           text-transform: uppercase; color: #999; margin-bottom: 12px; }
.lw-card { background: #fff; border: 1px solid #e8e8e6; border-radius: 10px;
           padding: 14px 16px; margin-bottom: 10px; }
.lw-card--obs { background: #fafaf9; }
.lw-title   { font-size: 13.5px; font-weight: 700; color: #111;
              margin-bottom: 4px; line-height: 1.4; }
.lw-tagline { font-size: 11.5px; font-style: italic; color: #666;
              margin-bottom: 8px; line-height: 1.55; }
.lw-body    { font-size: 12.5px; color: #333; line-height: 1.7; margin-bottom: 6px; }
.lw-ctx     { font-size: 11px; color: #999; font-style: italic; line-height: 1.55; }
.lw-obs-lbl { font-size: 9.5px; font-weight: 700; letter-spacing: .1em;
              text-transform: uppercase; color: #bbb; margin-bottom: 6px; }
.lw-badge   { display: inline-block; font-size: 9.5px; font-weight: 600;
              background: #f0f0ee; color: #888; padding: 1px 6px;
              border-radius: 4px; margin-left: 6px; }
.lw-sec > summary {
  font-size: 10px; font-weight: 700; letter-spacing: .08em;
  text-transform: uppercase; color: #888; cursor: pointer;
  padding: 10px 0 8px; border-top: 1px solid #ebebeb;
  list-style: none; display: flex; align-items: center; gap: 6px;
  user-select: none;
}
.lw-sec > summary::before { content: '▶'; font-size: 8px; color: #bbb;
                             display: inline-block; transition: transform .18s; }
.lw-sec[open] > summary::before { transform: rotate(90deg); }
.lw-sec  { margin-top: 4px; }
.lw-pane { padding: 6px 0 4px; }
</style>
"""

        def _layer_name(layer: int) -> str:
            return "Observations" if layer == 0 else f"Layer {layer} Insights"

        def _render_card(node: dict) -> str:
            if "title" in node:
                return (
                    '<div class="lw-card">'
                    f'<div class="lw-title">{node["title"]}</div>'
                    f'<div class="lw-tagline">{node.get("tagline", "")}</div>'
                    f'<div class="lw-body">{node.get("insight", "")}</div>'
                    f'<div class="lw-ctx">{node.get("context", "")}</div>'
                    '</div>'
                )
            obs = node.get("observation", "")
            return (
                '<div class="lw-card lw-card--obs">'
                f'<div class="lw-obs-lbl">Observation</div>'
                f'<div class="lw-body">{obs}</div>'
                '</div>'
            )

        def _build_detail_html(node_id: int) -> str:
            node = nodes_by_layer[str(last_layer)].get(str(node_id))
            if node is None:
                return '<div class="lw-root"><i>Node not found.</i></div>'

            parts = [
                '<div class="lw-root">',
                f'<div class="lw-hdr">{_layer_name(last_layer)}</div>',
                _render_card(node),
            ]

            current_ids: set[int] = {node_id}
            for layer in range(last_layer, 0, -1):
                emap = edge_maps.get(str(layer), {})
                next_ids: set[int] = set()
                for cid in current_ids:
                    next_ids.update(emap.get(str(cid), []))
                if not next_ids:
                    break
                prev_layer = layer - 1
                lookup = nodes_by_layer.get(str(prev_layer), {})
                found = [lookup[str(nid)] for nid in sorted(next_ids) if str(nid) in lookup]
                if found:
                    cards = "".join(_render_card(n) for n in found)
                    label = f"{_layer_name(prev_layer)}  ({len(found)})"
                    parts.append(
                        f'<details class="lw-sec" open>'
                        f'<summary>{label}</summary>'
                        f'<div class="lw-pane">{cards}</div>'
                        f'</details>'
                    )
                current_ids = next_ids

            parts.append('</div>')
            return "".join(parts)

        # ── widget layout ─────────────────────────────────────────────
        def _select_label(n: dict) -> str:
            if "title" in n:
                t = n["title"]
                return (t[:55] + "…") if len(t) > 55 else t
            obs = n.get("observation", "")
            return (obs[:55] + "…") if len(obs) > 55 else obs

        options = [(_select_label(n), n["id"]) for n in last_nodes]

        select = widgets.Select(
            options=options,
            value=options[0][1] if options else None,
            layout=widgets.Layout(width="300px", height="460px"),
        )

        # Use Output (not VBox) so HTML+CSS renders without sanitization.
        detail_out = widgets.Output(
            layout=widgets.Layout(
                flex="1",
                overflow_y="auto",
                max_height="500px",
                padding="0 6px 0 14px",
            )
        )

        def _render_detail(node_id: int):
            detail_out.clear_output(wait=True)
            with detail_out:
                _display(_IPHTML(_CSS + _build_detail_html(node_id)))

        def _on_change(change):
            if change["new"] is not None:
                try:
                    _render_detail(change["new"])
                except Exception as exc:
                    detail_out.clear_output(wait=True)
                    with detail_out:
                        _display(_IPHTML(f"<i style='color:red'>Error: {exc}</i>"))

        select.observe(_on_change, names="value")

        if options:
            _render_detail(options[0][1])

        _HDR_CSS = (
            "font-size:10px;font-weight:700;letter-spacing:.1em;"
            "text-transform:uppercase;color:#999;margin-bottom:10px"
        )

        left = widgets.VBox(
            [widgets.HTML(f'<div style="{_HDR_CSS}">{_layer_name(last_layer)}</div>'), select],
            layout=widgets.Layout(padding="4px 0"),
        )
        right = widgets.VBox(
            [widgets.HTML(f'<div style="{_HDR_CSS}">Details</div>'), detail_out],
            layout=widgets.Layout(flex="1"),
        )

        return widgets.HBox(
            [left, right],
            layout=widgets.Layout(
                border="1px solid #e8e8e6",
                padding="20px",
                width="100%",
                align_items="flex-start",
            ),
        )
    