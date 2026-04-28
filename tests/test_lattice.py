import latticing
from test_data import MOCK_OBSERVATIONS, MOCK_INTERACTION_DATA, MOCK_INTERACTION
import asyncio
import os
import yaml
from dotenv import load_dotenv
load_dotenv()

async def test_lattice():
    l = latticing.Lattice(
        name="User",
        interactions=MOCK_INTERACTION_DATA,
        description="the user's actions and screen activities",
        observer_model=latticing.AsyncLLM(name="claude-sonnet-4-6", api_key=os.getenv("ANTHROPIC_API_KEY")),
        insight_model=latticing.AsyncLLM(name="claude-sonnet-4-6", api_key=os.getenv("ANTHROPIC_API_KEY")),
        evidence_model=latticing.AsyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        format_model=latticing.SyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
    )
    config = l.auto_config()
    print(config)
    await l.build()
    l.save(save_path="test_lattice.json")
    # await l.make_first_layer(separator={"type": "time", "value": "day"})

async def test_edges():
    l = latticing.Lattice(
        name="User",
        observations=MOCK_OBSERVATIONS, 
        model=latticing.AsyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        evidence_model=latticing.AsyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        format_model=latticing.SyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
    )

    MOCK_O = [[
        {
            "id": 0,
            "observation": "User is feeling happy about the party",
            "confidence": 10,
            "metadata": {"input_session": 0, "time": "2026-04-21 10:00:00"}
        },
        {
            "id": 1,
            "observation": "User is feeling sad about the party",
            "confidence": 10,
            "metadata": {"input_session": 0, "time": "2026-04-21 10:05:00"}
        },
        {
            "id": 2,
            "observation": "User is feeling happy about the party",
            "confidence": 10,
            "metadata": {"input_session": 0, "time": "2026-04-21 10:10:00"}
        },
        {
            "id": 3,
            "observation": "User is feeling sad about the party",
            "confidence": 10,
            "metadata": {"input_session": 0, "time": "2026-04-21 10:15:00"}
        }
    ]]
    MOCK_I = [
        {
            "id": 0,
            "title": "User is feeling happy about the party",
            "tagline": "User is feeling happy about the party",
            "insight": "User is feeling happy about the party",
            "context": "User is feeling happy about the party",
            "supporting_evidence": "User is feeling happy about the party",
            "metadata": {"input_session": 0, "time": "2026-04-21 10:00:00"}
        }
    ]
    edges = await l._build_first_edges(MOCK_O, MOCK_I)
    print(edges)

def test_mock_auto_config(size: int = 100):
    interactions = [MOCK_INTERACTION for _ in range(size)]
    l = latticing.Lattice(
        name="User",
        interactions=interactions,
        description="the user's actions and screen activities",
        observer_model=latticing.AsyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        insight_model=latticing.AsyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        evidence_model=latticing.AsyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        format_model=latticing.SyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
    )
    config = l.auto_config()
    print(config)
    return config

def test_visualize():
    l = latticing.Lattice(
        name="User",
        interactions=MOCK_INTERACTION_DATA,
        description="the user's actions and screen activities",
        model=latticing.AsyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        evidence_model=latticing.AsyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        format_model=latticing.SyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
    )
    fig = l.visualize(load_path="../examples/lattice.json")
    fig.show()

def test_version():
    assert latticing.__version__ == "0.1.0"

if __name__ == "__main__":
    asyncio.run(test_lattice())
