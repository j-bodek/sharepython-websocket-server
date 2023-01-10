from sanic import Sanic, Request, Websocket
from server.handlers.connection_handler import connection_handler
from typing import Type
import os

app = Sanic(name="WebSocketServer")


@app.websocket("/<token:str>/")
async def codespace(request: Type[Request], ws: Type[Websocket], token: str) -> None:
    await connection_handler(ws, token, request.app)


if __name__ == "__main__":
    app.run(port=os.environ.get("PORT"))
