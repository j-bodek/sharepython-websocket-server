from sanic import Sanic, Request, Websocket
from server.handlers import connection_handler
from typing import Type

app = Sanic(name="WebSocketServer")


@app.websocket("/<token:str>/")
async def codespace(request: Type[Request], ws: Type[Websocket], token: str) -> None:
    await connection_handler(ws, token, request.app)
