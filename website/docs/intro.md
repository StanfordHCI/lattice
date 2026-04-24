---
id: intro
sidebar_position: 1
---

# Introduction

**Lattice** is a Python library for *Behavior Latticing* — a technique for transforming raw interaction traces into a structured, multi-layered graph of behavioral insights.

Given a stream of user interactions (e.g., screen activity logs, chat histories, click traces), Lattice:

1. **Observes** — uses an LLM to infer what the user is thinking and feeling from their raw actions.
2. **Generates insights** — synthesizes observations into named, evidence-backed behavioral insights.
3. **Builds layers** — recursively merges per-session insights into cross-session patterns.
4. **Visualizes** — renders the resulting lattice as an interactive graph.

## Core concepts

### Interaction trace
A sequence of timestamped user actions, grouped into sessions. Each session is a list of `{ interaction, metadata }` objects.

### Observation
A single inferred emotional or cognitive state extracted from a window of interactions. Observations answer: *what is this person thinking or feeling right now, and what behavior supports that?*

### Insight
A remarkable, evidence-backed realization about the user synthesized from a group of observations. Insights answer: *what pattern or tension emerges across many moments?*

### Lattice
The full hierarchical structure: layer 0 is raw observations, layer 1 is per-session insights, layer 2+ synthesizes across sessions. Edges link each insight back to the observations or lower-level insights that support it.

## When to use Lattice

- Analyzing user research session recordings
- Understanding behavioral patterns in chat logs or support tickets
- Synthesizing diary study data
- Any domain where you have rich sequential interaction data and want structured, model-grounded behavioral conclusions

## Quick look

```python
from lattice import Lattice, AsyncLLM, SyncLLM, Separator
import os

l = Lattice(
    name="Alice",
    interactions=interaction_traces,   # list of sessions
    description="the user's conversation history",
    model=AsyncLLM(name="claude-sonnet-4-6", api_key=os.getenv("ANTHROPIC_API_KEY")),
    evidence_model=AsyncLLM(name="claude-sonnet-4-6", api_key=os.getenv("ANTHROPIC_API_KEY")),
    format_model=SyncLLM(name="claude-sonnet-4-6", api_key=os.getenv("ANTHROPIC_API_KEY")),
)

config = {
    0: {"type": "session", "value": "1"},   # one group per session → L1 insights
    1: {"type": "session", "value": "10"},  # every 10 sessions → L2 synthesis
}

await l.build(config)
l.save("lattice.json")
```
