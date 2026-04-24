---
id: data-format
sidebar_position: 3
---

# Data Format

## Input: interaction traces

Lattice expects a list of **sessions**. Each session is a dict with the following keys:

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `interactions` | `list` | Yes | Ordered list of interaction objects |
| `time` | `str` | No | ISO datetime string for the session start (used for time-based splitting) |

Each **interaction** object has:

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `interaction` | `str` | Yes | The raw interaction text (e.g., `"Alice: what is the capital of France?"`) |
| `metadata` | `dict` | No | Arbitrary key-value pairs — all values are passed to the LLM as context |

### Example

```python
interaction_traces = [
    {
        "interactions": [
            {
                "interaction": "Alice: how do I center a div in CSS?",
                "metadata": {"time sent": "2026-01-01 10:00:00"}
            },
            {
                "interaction": "assistant: Use flexbox: display:flex; justify-content:center; align-items:center",
                "metadata": {"time sent": "2026-01-01 10:00:05"}
            },
        ],
        "time": "2026-01-01 10:00:00"
    },
    # ... more sessions
]
```

## Output: lattice JSON

After calling `l.save("lattice.json")`, the file has this structure:

```json
{
  "nodes": {
    "0": [ /* observations */ ],
    "1": [ /* L1 insights */ ],
    "2": [ /* L2 insights (if built) */ ]
  },
  "edges": {
    "1": [ /* edges from L1 insights → observations */ ],
    "2": [ /* edges from L2 insights → L1 insights */ ]
  }
}
```

### Observation node (layer 0)

```json
{
  "id": 0,
  "observation": "Alice appears frustrated, rapidly re-typing the same query multiple times.",
  "confidence": 4,
  "metadata": {
    "input_session": 0,
    "time": "2026-01-01 10:00:00"
  }
}
```

### Insight node (layer 1+)

```json
{
  "id": 0,
  "title": "Alice Debugs by Brute Force",
  "tagline": "Alice tends to retry without reading error messages carefully.",
  "insight": "Rather than reading error output, Alice immediately re-runs with small random changes...",
  "context": "Applies when Alice is blocked on a technical task.",
  "supporting_evidence": ["Observation IDs 2, 5, 8 all show rapid retries without pausing."],
  "merged": [2, 5, 8],
  "metadata": {
    "input_session": 0,
    "time": "2026-01-01 10:00:00"
  }
}
```

### Edge

```json
{ "source": 0, "target": 2 }
```

`source` is the higher-layer node id; `target` is the lower-layer node id.

## Separator

The `Separator` dataclass controls how nodes are grouped when building each layer.

| `type` | `value` | Behavior |
|--------|---------|----------|
| `"session"` | `"1"` | Each session is its own group |
| `"session"` | `"10"` | Every 10 consecutive sessions form one group |
| `"time"` | `"day"` | Group by calendar day (requires `time` in metadata) |
| `"time"` | `"week"` | Group by ISO calendar week |
| `"time"` | `"month"` | Group by month |
| `"time"` | `"year"` | Group by year |
