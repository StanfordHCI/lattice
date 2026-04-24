---
id: building-layers
sidebar_position: 4
---

# Building Layers

A Lattice is built incrementally, one layer at a time. You can call `build()` for a fully automated pipeline, or step through each layer manually for more control.

## Automated: `build(config)`

The `build()` method processes the full pipeline end-to-end:

1. Calls `make_observations()` to generate layer 0
2. Calls `make_first_layer()` for the first config entry (layer 0 → 1)
3. Calls `make_layer()` for each subsequent config entry (layer N → N+1)

```python
config = {
    0: {"type": "session", "value": "1"},   # L1: one group per session
    1: {"type": "session", "value": "20"},  # L2: groups of 20 sessions
}
await l.build(config)
```

The config keys (0, 1, …) are layer indices — they must be zero-indexed and contiguous.

## Manual step-by-step

### Step 1: Make observations

```python
observations = await l.make_observations()
# observations is now in l.lattice["nodes"][0]
# l.current_layer points to observations
```

### Step 2: Make the first insight layer

Observations → L1 insights. This step also maps edges from each insight back to its supporting observations.

```python
from lattice import Separator

sep = Separator(type="session", value="1")
l1_insights = await l.make_first_layer(separator=sep)
```

### Step 3: Make subsequent layers

L1 insights → L2 insights (and so on). Each call uses `l.current_layer` as input by default.

```python
sep2 = Separator(type="session", value="10")
l2_insights = await l.make_layer(separator=sep2)
```

You can also pass a specific layer as `input_layer` to override `current_layer`:

```python
l2_insights = await l.make_layer(separator=sep2, input_layer=some_custom_list)
```

## Loading pre-computed observations

If you already have observations from a previous run, pass them to the constructor to skip the observation step:

```python
import json

with open("observations.json") as f:
    saved_obs = json.load(f)

l = Lattice(
    ...,
    observations=saved_obs,
)

# make_observations() is skipped; build starts at make_first_layer
await l.build(config)
```

## Error handling

Each stage in the pipeline uses per-item error recovery. If one LLM call fails:

- The failed item is **logged** at `WARNING` level
- It is **skipped** — the rest of the batch continues
- The lattice is built with however many items succeeded

This means a partial lattice is always better than a crash. Monitor the logs for `batched_call: item N failed` warnings.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_concurrent` | `100` | Max simultaneous LLM calls across all stages |
| `min_insights` | `3` | Minimum insights requested from the model per group |
| `window_size` | `10` | Number of interactions per observation window |

Set these via the `params` dict in the `Lattice` constructor:

```python
l = Lattice(
    ...,
    params={"max_concurrent": 50, "min_insights": 5, "window_size": 15},
)
```
