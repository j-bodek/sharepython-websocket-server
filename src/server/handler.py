import logging
import json
from .redis import REDIS
import secrets
from server.channel import WebSocketChannels


class WebSocketHandler(object):

    operation_names = [
        "insert_value",
        "remove_value",
        "move_cursor",
    ]
    redis = REDIS

    def __init__(self):
        self.channels = WebSocketChannels()
        # self.codespace_uuid = None

    async def __call__(self, websocket, codespace_uuid):

        # This will be iterating over messages received on
        # the connection until the client disconnects
        try:
            self.channels.add_client(codespace_uuid, websocket)
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
                await self.dispatch(message, codespace_uuid, websocket)
        finally:
            self.channels.remove_client(codespace_uuid, websocket)

    async def dispatch(self, message, codespace_uuid, websocket):
        # Try to dispatch to the right operation; if a operation doesn't exist
        # close websocket connection

        message = json.loads(message)
        if (
            operation := message.get("operation")
        ) and operation in self.operation_names:
            handler = getattr(self, operation.lower())
        else:
            handler = self.operation_not_allowed

        await handler(message, codespace_uuid, websocket)

    async def operation_not_allowed(self, message, codespace_uuid, websocket):
        """
        Close websocket connection and return proper reason
        """

        logging.warning(
            f"{message.get('operation')} Operation Is Not Allowed",
        )

        await websocket.close(
            1011, f"'{message.get('operation')}' operation is not allowed"
        )

    async def insert_value(self, message, codespace_uuid, websocket) -> None:
        if data := self.redis.hgetall(codespace_uuid):
            data["code"] = (
                data["code"][: message["input"]["position"]["start"]]
                + message["input"]["value"]
                + data["code"][message["input"]["position"]["end"] :]
            )

            self.redis.hmset(codespace_uuid, data)

            await self.broadcast(codespace_uuid, json.dumps(message))

    async def broadcast(self, codespace_uuid, msg):
        for client in self.channels.get_clients(codespace_uuid):
            await client.send(msg)
