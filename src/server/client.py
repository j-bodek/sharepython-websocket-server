import secrets
from server.redis import REDIS
from typing import Type
from dataclasses import dataclass, field
from sanic import Websocket
from server.handlers.base import AbstractMessageHandler
from server.base import AbstractClient
import os

# slots makes instance attribute access faster and save some space
# https://stackoverflow.com/a/28059785/14579046
@dataclass(frozen=True, repr=False, slots=True)
class Client(AbstractClient):
    """
    This class wraps single websocket connection to represent connected
    client
    """

    id: str = field(init=False, default_factory=lambda: secrets.token_urlsafe(12))
    protocol: Type[Websocket]
    channel_id: str
    message_handler: Type[AbstractMessageHandler]
    # this value will be used to update codespace expiration
    # time everytime client add changes
    codespace_expire_update: int = field(init=False, default=0)

    def __post_init__(self):
        """
        Set codespace expire update
        """

        if self.channel_id.startswith("tmp-"):
            codespace_expire_update = int(
                os.environ.get("TMP_CODESPACE_EXPIRE_UPDATE", 0)
            )
        else:
            codespace_expire_update = int(os.environ.get("CODESPACE_EXPIRE_UPDATE", 0))

        # because dataclass is frozen regular setattr will raise error
        object.__setattr__(self, "codespace_expire_update", codespace_expire_update)

    async def listen(self) -> None:
        """
        Listen for incoming websocket messages
        """

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
