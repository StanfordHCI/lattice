---
id: llm
sidebar_position: 3
---

# LLM Wrappers

Lattice abstracts over four LLM providers through two wrapper classes: `AsyncLLM` (for concurrent batch processing) and `SyncLLM` (for sequential formatting fallbacks).

```python
from lattice import AsyncLLM, SyncLLM
```

## Supported models

| Provider | Example model names |
|----------|-------------------|
| Anthropic | `claude-sonnet-4-6`, `claude-opus-4-6`, `claude-haiku-4-5` |
| OpenAI | `gpt-4o`, `gpt-4o-mini`, `o3-mini` |
| Google | `gemini-2.0-flash`, `gemini-1.5-pro` |
| Together AI | See `consts.py` `MODEL_FAMILIES` |

All models must be listed in the internal `MODEL_FAMILIES` registry (`src/lattice/consts.py`). If a model is missing, add it there.

## AsyncLLM

Use for all primary LLM calls (observations, insight generation, evidence mapping).

```python
AsyncLLM(
    name: str,
    api_key: str,
    provider: str | None = None,
)
```

| Parameter | Description |
|-----------|-------------|
| `name` | Model identifier string |
| `api_key` | Provider API key |
| `provider` | Override auto-detected provider (`"anthropic"`, `"openai"`, `"google"`, `"together"`) |

Concurrency is controlled by an internal `asyncio.Semaphore` seeded from the `LLM_CONCURRENCY` environment variable (default: 16). The higher `max_concurrent` on `Lattice` is an outer semaphore that throttles the number of simultaneous tasks submitted to `batched_call`.

### `call(prompt, resp_format=None)` `async`

```python
result = await llm.call("Summarize this observation: ...")

# With structured output (returns a validated Pydantic instance)
from lattice.models import Insights
insights = await llm.call(prompt, resp_format=Insights)
```

When `resp_format` is provided, the call uses provider-native structured output:
- **Anthropic** — forced tool use with `tool_choice: {type: "tool"}`
- **OpenAI** — `client.responses.parse()` with `text_format`
- **Google** — `response_mime_type: "application/json"` with schema
- **Together** — `response_format: {type: "json_schema"}`

**Returns** a `str` (no `resp_format`) or a validated Pydantic model instance (`resp_format` given).

## SyncLLM

Use as a fallback formatter when async structured output fails. Has the same constructor signature as `AsyncLLM`.

```python
format_model = SyncLLM(name="claude-sonnet-4-6", api_key=os.getenv("ANTHROPIC_API_KEY"))
```

### `call(prompt, resp_format=None)` (sync)

Identical interface to `AsyncLLM.call` but synchronous. Used internally by `parse_model_json_with_fallback`.

## Retry behavior

All provider call functions use `tenacity` with exponential backoff:

| Provider | Retries | Max wait |
|----------|---------|----------|
| Anthropic | 3 | 6 s |
| OpenAI | 5 | 60 s |
| Google | 5 | 60 s |
| Together | 5 | 60 s |

Failures that exhaust retries are surfaced as `RetryError` exceptions, which `batched_call` captures per-item rather than letting them crash the entire batch.
