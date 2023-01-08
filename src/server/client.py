import secrets
import json
from server.redis import REDIS
from sanic import Websocket
from typing import Type


class Client(object):
    """
    This class wraps single websocket connection to represent connected
    client
    """

    def __init__(
        self, protocol: Type[Websocket], channel_id: str, message_handler
    ) -> None:
        self.id = secrets.token_urlsafe(12)
        self.protocol = protocol
        self.channel_id = channel_id
        self.message_handler = message_handler

    async def listen(self) -> None:
        """
        Listen for incoming websocket messages
        """

        # send message informing about successfull connection
        await self.protocol.send(
            json.dumps(
                {
                    "operation": "connected",
                    "data": {"id": self.id},
                }
            )
        )

        # This will be iterating over messages received on
        # the connection until the client disconnects
        async for message in self.protocol:
            await self.message_handler.dispatch(message, self.channel_id, self)

    async def publish(self, message: str) -> None:
        # this method is used to publish message via redis pub/sub

        await REDIS.publish(self.channel_id, message)

    async def close(self, code: int, reason: str) -> None:
        # close websocket connection

        await self.protocol.close(code, reason)

    async def send(self, message: str) -> None:
        # send message only to client

        await self.protocol.send(message)
