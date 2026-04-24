---
id: quickstart
sidebar_position: 2
---

# Quickstart

This guide walks through a complete end-to-end example using a ChatGPT conversation export (`conversations.json`).

## 1. Prepare your data

Format your raw data into Lattice's interaction trace format — a list of sessions, each containing a list of `{ interaction, metadata }` objects:

```python
import json
from datetime import datetime

def process_chat_data(data, user_name, convo_min_len=10):
    interaction_traces = []
    for d in data:
        convo = []
        conversation_start = datetime.fromtimestamp(d['create_time']).strftime('%Y-%m-%d %H:%M:%S')
        for mid in d['mapping']:
            msg = d['mapping'][mid]['message']
            if msg is None:
                continue
            author = msg['author']['role']
            if author == "user":
                author = user_name
            create_time = msg['create_time']
            content = msg['content']
            if author == 'system' or create_time is None or "parts" not in content:
                continue
            readable_time = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S')
            try:
                text = " ".join(content['parts'])
            except Exception:
                text = ""
            if len(text) > 0:
                convo.append({
                    "interaction": f"{author}: {text}",
                    "metadata": {"time sent": readable_time}
                })
        if len(convo) > convo_min_len:
            interaction_traces.append({
                "interactions": convo,
                "time": conversation_start
            })
    return interaction_traces

data = json.load(open("conversations.json"))
interaction_traces = process_chat_data(data, user_name="Alice")
```

## 2. Create the Lattice

```python
import os
from lattice import Lattice, AsyncLLM, SyncLLM
from dotenv import load_dotenv

load_dotenv()

l = Lattice(
    name="Alice",
    interactions=interaction_traces,
    description="the user's conversation with ChatGPT",
    model=AsyncLLM(name="claude-sonnet-4-6", api_key=os.getenv("ANTHROPIC_API_KEY")),
    evidence_model=AsyncLLM(name="claude-sonnet-4-6", api_key=os.getenv("ANTHROPIC_API_KEY")),
    format_model=SyncLLM(name="claude-sonnet-4-6", api_key=os.getenv("ANTHROPIC_API_KEY")),
    params={"max_concurrent": 50, "min_insights": 3, "window_size": 10},
)
```

## 3. Define the build config

The config maps each layer to a `Separator` that controls how inputs are grouped:

```python
config = {
    0: {"type": "session", "value": "1"},   # L1: one group per session
    1: {"type": "session", "value": "10"},  # L2: synthesize every 10 sessions
}
```

## 4. Build

```python
# In a Jupyter notebook (async context):
await l.build(config)

# In a regular Python script:
import asyncio
asyncio.run(l.build(config))
```

## 5. Inspect results

```python
# Print current (top-most) layer
l.print_layer()

# Print a specific layer by number
l.print_layer(layer_num=1)
```

## 6. Save and visualize

```python
# Save to JSON
l.save("lattice.json")

# Interactive Plotly figure (works in Jupyter)
fig = l.visualize()
fig.show()

# Or open examples/visualize.html and upload lattice.json for a standalone viewer
```
