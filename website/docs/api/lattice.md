---
id: lattice
sidebar_position: 1
---

# Lattice

The main class. Orchestrates the full observation → insight → synthesis pipeline.

```python
from lattice import Lattice, AsyncLLM, SyncLLM
```

## Constructor

```python
Lattice(
    name: str,
    interactions: list,
    description: str,
    model: AsyncLLM,
    evidence_model: AsyncLLM,
    format_model: SyncLLM,
    observations: list | None = None,
    params: dict = {"max_concurrent": 100, "min_insights": 3, "window_size": 10},
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Display name for the user being analyzed (used in prompts) |
| `interactions` | `list` | List of session dicts — see [Data Format](../guides/data-format) |
| `description` | `str` | Natural-language description of the interaction source (e.g., `"the user's screen activity"`) |
| `model` | `AsyncLLM` | Primary async LLM — used for generating insights |
| `evidence_model` | `AsyncLLM` | Async LLM for mapping evidence — can be the same as `model` |
| `format_model` | `SyncLLM` | Sync LLM for JSON formatting fallback |
| `observations` | `list \| None` | Pre-computed observations to skip the observation step |
| `params` | `dict` | Runtime parameters (see below) |

### `params` keys

| Key | Default | Description |
|-----|---------|-------------|
| `max_concurrent` | `100` | Max simultaneous LLM calls |
| `min_insights` | `3` | Minimum insights requested per group |
| `window_size` | `10` | Interactions per observation window |

## Methods

### `build(config)` `async`

Run the complete pipeline. Calls `make_observations()` then `make_first_layer()` / `make_layer()` for each layer in `config`.

```python
await l.build(config)
```

**`config`** — a dict mapping zero-indexed layer numbers to separator configs:

```python
config = {
    0: {"type": "session", "value": "1"},
    1: {"type": "session", "value": "10"},
}
```

---

### `make_observations()` `async`

Generate layer 0 (observations) from `self.interactions`. Stores results in `self.observations` and `self.lattice["nodes"][0]`.

```python
obs = await l.make_observations()
```

**Returns** `list` of observation dicts.

---

### `make_first_layer(separator)` `async`

Transform observations (layer 0) into L1 insights (layer 1). Runs three stages in sequence: generate raw insights, format them with structured output, map evidence edges.

```python
from lattice import Separator
l1 = await l.make_first_layer(separator=Separator(type="session", value="1"))
```

**Returns** `list` of insight dicts.

---

### `make_layer(separator, input_layer=None)` `async`

Synthesize the current layer into a new layer of higher-level insights. `make_first_layer` must have been called first.

```python
l2 = await l.make_layer(separator=Separator(type="session", value="10"))
```

**`input_layer`** — override `self.current_layer` with a custom list.

**Returns** `list` of insight dicts.

---

### `print_layer(layer_num=None)`

Print a human-readable summary of a layer to stdout.

```python
l.print_layer()           # current layer
l.print_layer(layer_num=1)  # specific layer
```

---

### `save(save_path="lattice.json")`

Serialize `self.lattice` to a JSON file.

```python
l.save("output/lattice.json")
```

---

### `visualize(load_path=None)`

Return an interactive Plotly `Figure`.

```python
fig = l.visualize()           # use self.lattice
fig = l.visualize("lattice.json")  # load from file
fig.show()
```

**Returns** `plotly.graph_objects.Figure`.

## Instance attributes

| Attribute | Description |
|-----------|-------------|
| `l.lattice` | The full lattice dict — `{"nodes": {0: [...], 1: [...]}, "edges": {1: [...]}}` |
| `l.current_layer` | List of nodes in the most recently built layer |
| `l.observations` | Layer 0 observations list (or `None` before `make_observations()`) |
| `l.layer_num` | Index of the next layer to be built |
| `l.num_nodes` | List of node counts per layer |
