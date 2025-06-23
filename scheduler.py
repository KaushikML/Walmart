import asyncio

from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

async def run_scheduler():
    while True:
        await liquidate()
        await asyncio.sleep(24 * 3600)

async def liquidate():
    response = client.post("/liquidate")
    return response.json()

if __name__ == "__main__":
    asyncio.run(liquidate())
