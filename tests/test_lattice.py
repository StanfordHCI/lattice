import lattice
from test_data import MOCK_OBSERVATIONS
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

async def test_lattice():
    l = lattice.Lattice(
        name="User",
        observations=MOCK_OBSERVATIONS, 
        model=lattice.AsyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        evidence_model=lattice.SyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        format_model=lattice.SyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
    )
    await l.make_first_layer(separator={"type": "time", "value": "day"})

def test_version():
    assert lattice.__version__ == "0.1.0"

if __name__ == "__main__":
    asyncio.run(test_lattice())
