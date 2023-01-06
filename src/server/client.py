import secrets
import json
from server.redis import REDIS
from server.handlers.message_hanlder import message_handler


class Client(object):

    message_handler = message_handler

    def __init__(self, protocol, channel_id):
        self.id = secrets.token_urlsafe(12)
        self.protocol = protocol
        self.channel_id = channel_id

    async def listen(self):
        # this method listen for new websocket messages

        # send connected message
        await self.protocol.send(
            json.dumps(
                {
                    "operation": "connected",
                    "data": {"id": self.id},
                }
            )
        )

        # listen for new messages
        async for message in self.protocol:
            await self.message_handler.dispatch(message, self.channel_id, self)

    async def publish(self, message):
        # this method is used to publish message via redis

        await REDIS.publish(self.channel_id, message)

    async def close(self, code: int, reason: str):
        await self.protocol.close(code, reason)

    async def send(self, message):
        await self.protocol.send(message)
