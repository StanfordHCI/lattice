---
id: visualization
sidebar_position: 5
---

# Visualization

Lattice provides two ways to visualize the resulting graph.

## Python: Plotly figure

`Lattice.visualize()` returns an interactive [Plotly](https://plotly.com/python/) figure. Use it in Jupyter notebooks or any Plotly-compatible environment.

```python
fig = l.visualize()
fig.show()  # opens in browser
```

You can also load a saved lattice JSON instead of using the in-memory one:

```python
fig = l.visualize(load_path="lattice.json")
fig.show()
```

The figure shows:
- **Layer 0 (observations)** — colored circle per observation
- **Layer 1+ (insights)** — one circle per insight per layer, with distinct colors
- **Edges** — gray lines connecting insights to their supporting nodes
- **Hover text** — full observation or insight text on hover

Pass the figure to Dash or Streamlit for embedding in a web app:

```python
import dash
from dash import html, dcc

app = dash.Dash()
app.layout = html.Div([dcc.Graph(figure=l.visualize())])
app.run_server()
```

## Browser: standalone HTML viewer

`examples/visualize.html` is a self-contained viewer that requires no server. Open it in any browser and upload a `lattice.json` file.

Features:
- Plotly.js canvas with scroll-to-zoom and drag-to-pan
- Three node types with distinct markers (observations, L1 insights, L2 insights)
- Click any node to open a detail panel on the right
- From an insight, see supporting observations or merged lower-level insights
- From an observation, see which insights reference it

To use:
1. Run `l.save("lattice.json")` after building
2. Open `examples/visualize.html` in your browser
3. Click **Upload lattice.json** and select your file
