---
id: installation
sidebar_position: 1
---

# Installation

## Requirements

- Python 3.9+
- An API key for at least one supported LLM provider (Anthropic, OpenAI, Google, or Together AI)

## Install from source

Lattice is not yet published to PyPI. Clone the repository and install it in editable mode:

```bash
git clone https://github.com/dorazhao99/lattice.git
cd lattice
pip install -e .
```

## Install dependencies only

If you want to pin your own versions, the core runtime dependencies are:

```
anthropic>=0.96.0
openai>=2.32.0
google-genai>=1.47.0
together>=2.9.0
plotly>=5.0.0
tenacity>=9.1.2
pyyaml>=6.0.3
```

## Environment variables

Set your provider API key(s) in your environment or a `.env` file:

```bash
# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI (GPT)
OPENAI_API_KEY=sk-...

# Google (Gemini)
GOOGLE_API_KEY=...

# Together AI
TOGETHER_API_KEY=...
```

Load them in your script with `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv()
```

## Jupyter notebooks

If you are working inside a Jupyter notebook and cannot install the package (e.g., due to conda/pip conflicts), add the source directory to the path manually:

```python
import sys, os
sys.path.insert(0, os.path.abspath('/path/to/lattice/src'))
```

## Logging

Lattice follows Python logging best practices for libraries — it attaches a `NullHandler` and never calls `basicConfig`. Configure logging in your application:

```python
import logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger('lattice').setLevel(logging.INFO)  # show lattice logs only
```
