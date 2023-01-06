from sanic import Sanic, Request, Websocket
from server.handlers import ConnectionHandler
from server.authentication import Authenticate

app = Sanic(name="WebSocketServer")

connection_handler = ConnectionHandler()
authenticate = Authenticate()


@app.websocket("/<token:str>/")
async def feed(request: Request, ws: Websocket, token: str):
    uuid = await authenticate(ws, token)
    await connection_handler(ws, uuid)
