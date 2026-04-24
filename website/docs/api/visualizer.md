---
id: visualize
sidebar_position: 4
---

# Visualizer

Renders a built lattice as an interactive diagram or a widget-based inspector.

```python
from latticing import Visualizer
```

## Constructor

```python
Visualizer(lattice: dict)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `lattice` | `dict` | A lattice dict — typically `Lattice.lattice` after calling `build()` |

**Example:**

```python
viz = Visualizer(lattice=l.lattice)
# or load from a saved file
import json
with open("lattice.json") as f:
    viz = Visualizer(json.load(f))
```

## Methods

### `basic_diagram()`

Return an interactive Plotly `Figure` showing every layer as a horizontal row of nodes connected by edges. Hover over any node to see its full text.

```python
fig = viz.basic_diagram()
fig.show()
```

**Returns** `plotly.graph_objects.Figure`.

Each layer is rendered in a distinct color and appears in the legend:

| Layer | Legend label |
|-------|-------------|
| 0 | Observations |
| 1+ | Insights — layer *N* |

---

### `visualize_widget()`

Return an `ipywidgets` side-by-side inspector for the top layer of the lattice. The left panel lists every node in the last layer; selecting one populates the right panel with its full detail and collapsible sections showing every lower layer reachable via edges.

```python
widget = viz.visualize_widget()
display(widget)
```

**Returns** `ipywidgets.HBox`.

**Requires** `ipywidgets`:

```bash
pip install ipywidgets
```

The widget renders unsanitized HTML/CSS so it must be run inside a Jupyter notebook or JupyterLab environment.
