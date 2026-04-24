---
id: observer
sidebar_position: 2
---

# Observer

Converts raw interaction traces into behavioral observations using an LLM.

You typically don't instantiate `Observer` directly — `Lattice` creates and manages one internally. It is exported for advanced use cases.

```python
from lattice import Observer
```

## Constructor

```python
Observer(
    name: str,
    model: AsyncLLM,
    format_model: SyncLLM,
    description: str = "the user's actions and screen activities",
    params: dict = {"window_size": 10, "max_concurrent": 100},
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | User display name (injected into prompts) |
| `model` | `AsyncLLM` | Async LLM for generating observations |
| `format_model` | `SyncLLM` | Sync LLM used as a fallback JSON parser |
| `description` | `str` | Description of the interaction source used in prompts |
| `params` | `dict` | `window_size` and `max_concurrent` |

## Methods

### `observe(interactions, observer_types=["default"])` `async`

Make observations for a full list of sessions.

```python
observations = await observer.observe(interaction_traces)
```

**Returns** a flat list of observation dicts:

```json
[
  {
    "id": 0,
    "observation": "User appears stressed, rapidly switching between tabs.",
    "confidence": 4,
    "metadata": {"input_session": 0}
  }
]
```

Each interaction window produces both a `think_feel` observation (inferred emotional/cognitive state) and an `actions` observation (behavioral evidence), resulting in up to `2 × ceil(session_length / window_size)` observations per session.

---

### `make_session_observation(session, observer_types=["default"])` `async`

Make observations for a single session.

```python
obs = await observer.make_session_observation(session["interactions"])
```

**`session`** — a list of `{ interaction, metadata }` dicts.

**Returns** a list of raw LLM response strings (one per window).

## Observation prompt

The observer uses a structured prompt (`OBSERVE_PROMPT`) that instructs the model to:

- Focus on behavioral cues (typing speed, switching, pausing) rather than content sentiment
- Name specific entities (apps, people, tools) in every observation
- Rate confidence on a 1–10 scale
- Return empty observations when the evidence is ambiguous

Low-confidence observations (< 5) are expected and appropriate — they are filtered at the insight stage.
