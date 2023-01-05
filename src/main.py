from sanic import Sanic, Request, Websocket
from server.handler import WebSocketHandler
from server.authentication import Authenticate

app = Sanic(name="WebSocketServer")

handler = WebSocketHandler()
authenticate = Authenticate()


@app.websocket("/<token:str>/")
async def feed(request: Request, ws: Websocket, token: str):
    uuid = await authenticate(ws, token)
    await handler(ws, uuid)
