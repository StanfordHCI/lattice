# Behavior Latticing

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![arXiv](https://img.shields.io/badge/arXiv-2604.07629-b31b1b.svg)](https://arxiv.org/abs/2604.07629)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/latticing?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/latticing)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Latticing** is a Python library for transforming raw interaction traces into behavioral insights about the user's motivations.

Given a stream of user interactions — chat histories, screen activity logs, support tickets, behavior latticing induces user motivation through hierarchically grouping and interpreting user behavior. 

## Installation

```bash
pip install latticing
```

Set your LLM provider API key(s) in a `.env` file or your environment:

```bash
ANTHROPIC_API_KEY=sk-ant-...   # Anthropic (Claude)
OPENAI_API_KEY=sk-...          # OpenAI (GPT)
GOOGLE_API_KEY=...             # Google (Gemini)
TOGETHER_API_KEY=...           # Together AI
```

**Requirements:** Python 3.10+

## Quick start

```python
import os
import asyncio
from lattice import Lattice, AsyncLLM, SyncLLM
from dotenv import load_dotenv

load_dotenv()

# interaction_traces: list of sessions, each a dict with
# "interactions" (list of {interaction, metadata}) and "time"
l = Lattice(
    name="Alice",
    interactions=interaction_traces,
    description="the user's ChatGPT conversations",
    insight_model=AsyncLLM(name="claude-opus-4-6", api_key=os.getenv("ANTHROPIC_API_KEY")),
    observer_model=AsyncLLM(name="claude-sonnet-4-6", api_key=os.getenv("ANTHROPIC_API_KEY")),
    evidence_model=AsyncLLM(name="claude-sonnet-4-6", api_key=os.getenv("ANTHROPIC_API_KEY")),
    format_model=SyncLLM(name="claude-sonnet-4-6", api_key=os.getenv("ANTHROPIC_API_KEY")),
    params={"max_concurrent": 100, "min_insights": 3, "window_size": 100},
)

# Each config entry defines a layer: how to group inputs into insight clusters
config = {
    0: {"type": "session", "value": "5"},   # L1: synthesize observations across 5 chunks (i.e., chat conversations)
    1: {"type": "session", "value": "10"},  # L2: synthesize insights across 10 chunks from the layer below
}

asyncio.run(l.build(config))
l.save("lattice.json")

# Interactive Plotly figure
l.visualize().show()
```

## How it works

1. **Observe** — the `Observer` reads sliding windows of raw interactions and prompts an LLM to infer the user's behavior. 
2. **Synthesize** — observations are grouped by session and synthesized into titled, evidence-backed insights with context on when each pattern applies.
3. **Layer** — insights from multiple sessions are merged into higher-order patterns, revealing cross-session behaviors invisible at the individual session level.
4. **Explore** — navigate the resulting lattice interactively — hover any node to read its full text, trace it back to its supporting observations.

### Lattice structure

| Layer | Contents |
|-------|----------|
| 0 | Raw observations — inferred emotional/cognitive states from interaction windows |
| 1+ | Insights — higher-order inferred motivations that are induced from the layer below|

Edges link each insight back to the observations or lower-level insights that support it.

## Supported providers
Pass different providers per role for cost/quality tradeoffs:

```python
from lattice import AsyncLLM, SyncLLM

model = AsyncLLM(name="claude-opus-4-6", api_key=os.getenv("ANTHROPIC_API_KEY"))
format_model = SyncLLM(name="claude-haiku-4-5", api_key=os.getenv("ANTHROPIC_API_KEY"))
```

## Examples
Explore examples of how behavior latticing can be applied to different types of interaction data:

- LLM Chat Histories: [Colab Notebook](https://colab.research.google.com/drive/1gR9sAAiA7oq9PkcixrVmfp8uOM6Flr-a?usp=sharing)
- 

## Documentation

Full documentation is available at **[https://stanfordhci.github.io/lattice](https://stanfordhci.github.io/lattice)**.

## Citation

If you use Behavior Latticing in academic work, please cite:

```bibtex
@article{zhao2026behavior,
  title={Behavior Latticing: Inferring User Motivations from Unstructured Interactions},
  author={Zhao, Dora and Lam, Michelle S and Yang, Diyi and Bernstein, Michael S},
  journal={arXiv preprint arXiv:2604.07629},
  year={2026}
}
```

## License

MIT — see [LICENSE](LICENSE) for details.
