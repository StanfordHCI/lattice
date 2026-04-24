---
id: intro
sidebar_position: 1
---

# Introduction

**Latticing** is a Python library for *Behavior Latticing* — a technique for transforming raw interaction traces into a structured, multi-layered graph of behavioral insights.

Given a stream of user interactions (e.g., screen activity logs, chat histories, click traces), Lattice:

1. **Observes** — uses an LLM to infer what the user is thinking and feeling from their raw actions.
2. **Generates insights** — synthesizes observations into named, evidence-backed behavioral insights.
3. **Builds layers** — recursively merges per-session insights into cross-session patterns.
4. **Visualizes** — renders the resulting lattice as an interactive graph.


## When to use Behavior Latticing
Behavior latticing is **flexible across input type**. Examples of input types are as follows:
- Messages with LLM-based chatbots (e.g., ChatGPT, Claude) ([link](examples/chatgpt.md))
- Interactions with coding agents (e.g., Claude Code)
- Screen recordings of computer usage ([link](https://arxiv.org/abs/2604.07629))

See our [Gallery](/gallery) for what others have built using Behavior Latticing.


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
