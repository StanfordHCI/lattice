import lattice
from test_data import MOCK_OBSERVATIONS
import asyncio
import os
import yaml
from dotenv import load_dotenv
load_dotenv()

async def test_lattice():
    with open("example.yaml", "r") as f:
        config = yaml.safe_load(f)


    l = lattice.Lattice(
        name="User",
        observations=MOCK_OBSERVATIONS, 
        model=lattice.AsyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        evidence_model=lattice.AsyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        format_model=lattice.SyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
    )

    for layer in config:
        if layer == 0:
            await l.make_first_layer(separator=config[layer])
        else:
            await l.make_layer(separator=config[layer])
    l._save_lattice()
    # await l.make_first_layer(separator={"type": "time", "value": "day"})

async def test_edges():
    l = lattice.Lattice(
        name="User",
        observations=MOCK_OBSERVATIONS, 
        model=lattice.AsyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        evidence_model=lattice.AsyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        format_model=lattice.SyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
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

def test_version():
    assert lattice.__version__ == "0.1.0"

if __name__ == "__main__":
    asyncio.run(test_lattice())
