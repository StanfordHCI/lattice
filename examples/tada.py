import json
import argparse
import asyncio
from latticing import Lattice, AsyncLLM, SyncLLM, TimeLayer, Sequential, AllLayer
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
load_dotenv()

def read_jsonl(filepath):
    with open(filepath, "r") as f:
        return [json.loads(line) for line in f]

def sessionize_data(data):
    if not data:
        return []
    sessions = []
    current_session = [data[0]]
    for item in data[1:]:
        gap = datetime.strptime(item["metadata"]["time"], "%Y-%m-%d %H:%M:%S") - datetime.strptime(current_session[-1]["metadata"]["time"], "%Y-%m-%d %H:%M:%S")
        if gap >= timedelta(hours=3):
            sessions.append({
                "interactions": current_session,
                "time": current_session[0]["metadata"]["time"]
                })
            current_session = []
        current_session.append(item)
    sessions.append({
        "interactions": current_session,
        "time": current_session[0]["metadata"]["time"]
    })
    print(f"Found {len(sessions)} sessions")
    return sessions

def process_tada_data(data):
    interactions = []
    print(f"Processing {len(data)} items")
    for i,item in enumerate(data):
        interactions.append({
            "interaction": f"{item['text']} {item['dense_caption']}",
            "metadata": {
                "time": datetime.strptime(item["start_time"], "%Y-%m-%d_%H-%M-%S-%f").strftime("%Y-%m-%d %H:%M:%S")
            }
        })
    return sessionize_data(interactions)

async def make_lattice(interactions: list, user_name: str):
    config = Sequential(
        TimeLayer(by="day"),
        TimeLayer(by="week"),
        AllLayer(),
    )

    l = Lattice(
        name=user_name,
        interactions=interactions,
        description=f"{user_name}'s screen activities",
        observer_model=AsyncLLM(name="claude-sonnet-4-6", api_key=os.getenv("ANTHROPIC_API_KEY")),
        insight_model=AsyncLLM(name="claude-sonnet-4-6", api_key=os.getenv("ANTHROPIC_API_KEY")),
        evidence_model=AsyncLLM(name="gpt-5.1", provider="openai", api_key=os.getenv("OPENAI_API_KEY")),
        format_model=SyncLLM(name="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY")),
        config=config,
        params={"max_concurrent": 100, "min_insights": 3, "window_size": 25},
    )

    await l.build()
    l.save(save_path="tada_lattice.json")
    l.save_object(save_path="tada_lattice.pkl")

def run():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--user_name", type=str, required=True)
    argparser.add_argument("--data_path", type=str, required=True)
    args = argparser.parse_args()
    data = read_jsonl(args.data_path)
    interactions = process_tada_data(data)
    asyncio.run(make_lattice(interactions, args.user_name))

if __name__ == "__main__":
    run()