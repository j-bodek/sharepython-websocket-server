import asyncio
import websockets
from handler import WebSocketHandler


handler = WebSocketHandler()


async def main():
    async with websockets.serve(handler, "", 8888):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
