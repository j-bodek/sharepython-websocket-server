import aiohttp
from urllib import parse
import logging
import json
from .redis import REDIS
import websockets
import secrets


class WebSocketHandler(object):

    # big thx https://stackoverflow.com/a/56297455/14579046
    # host should be name of container instead of localhost
    api_base_url = "http://api:8000/api/"
    operation_names = [
        "insert_value",
        "remove_value",
        "move_cursor",
    ]
    redis = REDIS

    def __init__(self):
        self.websockets = set()
        self.codespace_uuid = None

    async def __call__(self, websocket):
        # self.websocket = websocket

        token = parse.parse_qs(parse.urlparse(websocket.path).query).get(
            "token", [None]
        )[0]
        # if request not authenticated connection will be closed
        await self.authenticate(token, websocket)

        # This will be iterating over messages received on
        # the connection until the client disconnects
        try:
            self.websockets.add(websocket)
            # send connected message
            await websocket.send(
                json.dumps(
                    {
                        "operation": "connected",
                        "data": {"id": secrets.token_urlsafe(12)},
                    }
                )
            )
            # listen client messages
            async for message in websocket:
                await self.dispatch(message, websocket)
        finally:
            self.websockets.remove(websocket)

    async def authenticate(self, token: str, websocket) -> None:
        """
        Authenticate request by given token and if token is valid
        update codespace_uuid
        """

        if not token:
            await websocket.close(1011, "Missing token")
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_base_url}codespace/{token}/?fields=uuid"
            ) as resp:
                if resp.status != 200:
                    await websocket.close(1011, "Invalid token")
                    return

                data = await resp.json()
                self.codespace_uuid = data["uuid"]

    async def dispatch(self, message, websocket):
        # Try to dispatch to the right operation; if a operation doesn't exist
        # close websocket connection

        message = json.loads(message)
        if (
            operation := message.get("operation")
        ) and operation in self.operation_names:
            handler = getattr(self, operation.lower())
        else:
            handler = self.operation_not_allowed

        await handler(message, websocket)

    async def operation_not_allowed(self, message, websocket):
        """
        Close websocket connection and return proper reason
        """

        logging.warning(
            f"{message.get('operation')} Operation Is Not Allowed",
        )

        await websocket.close(
            1011, f"'{message.get('operation')}' operation is not allowed"
        )

    async def insert_value(self, message, websocket) -> None:
        if data := self.redis.hgetall(self.codespace_uuid):
            data["code"] = (
                data["code"][: message["input"]["position"]["start"]]
                + message["input"]["value"]
                + data["code"][message["input"]["position"]["end"] :]
            )

            self.redis.hmset(self.codespace_uuid, data)

            websockets.broadcast(self.websockets, json.dumps(message))
