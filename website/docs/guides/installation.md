---
id: installation
sidebar_position: 1
---

# Installation

## Requirements

- Python 3.10+
- An API key for at least one supported LLM provider (Anthropic or OpenAI)

The Behavior Latticing Python package is available on PyPl as `latticing`. We recommend setting up a virtual environment with venv or conda. 

```bash
pip install latticing
```

## Environment variables

Set your provider API key(s) in your environment or a `.env` file:

```bash
# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI (GPT)
OPENAI_API_KEY=sk-...
```

:construction: We are working on providing support for additional model providers. If there is a model provider you are interested in, please submit a Github [issue](https://github.com/StanfordHCI/lattice/issues).

Load them in your script with `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv()
```

