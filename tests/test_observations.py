import lattice
import os
from dotenv import load_dotenv
import asyncio
from test_data import MOCK_INTERACTION_DATA
load_dotenv()

async def test_observations():
    Observer = lattice.Observer(
        name="User",
        model=lattice.AsyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        format_model=lattice.SyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        description="the user's actions and screen activities"
    )

    observations = await Observer.make_observations(
        interactions=MOCK_INTERACTION_DATA
    )

    print(observations)

if __name__ == "__main__":
    asyncio.run(test_observations())