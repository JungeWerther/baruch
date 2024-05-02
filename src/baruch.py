import websockets
import asyncio

async def connect():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as ws:
        while True:
            stream = await ws.recv()
            print(stream)

if __name__ == "__main__":
    asyncio.run(connect())
