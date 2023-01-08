from server.client import Client
from server.redis import REDIS
import asyncio
import aioredis
from server.handlers.message_hanlder import message_handler
from typing import Type
from sanic import Websocket


class Channel(object):
    """
    This class is used to store Client instances and send received messages to them.
    It represents communication channel created for particular codespace
    """

    def __init__(
        self, cache, pubsub: Type[aioredis.client.PubSub], channel_id: str
    ) -> None:
        self.clients = set()
        self.cache = cache
        self.pubsub = pubsub
        self.channel_id = channel_id
        self.lock = asyncio.Lock()

    async def listen(self) -> None:
        """
        Listen new pubsub messages and send them to connected clients
        """
        try:
            async for message in self.pubsub.listen():
                if message["type"] != "message":
                    continue

                await self.broadcast(message)

        except aioredis.exceptions.ConnectionError:
            print(f"PUBSUB closed <{self.channel_id}>")

    async def broadcast(self, message: str) -> None:
        """
        Send message to all connected clients
        """

        payload = message["data"]
        for client in self.clients:
            await client.send(payload)

    async def register(self, websocket: Type[Websocket]) -> Type[Client]:
        """
        Create new client instance and add it to clients set
        """

        async with self.lock:
            client = Client(
                protocol=websocket,
                channel_id=self.channel_id,
                message_handler=message_handler,
            )
            self.clients.add(client)
            return client

    async def leave(self, client: Type[Client]) -> None:
        """
        Remove client from clients set and if no client left
        destroy channel and reset pubsub
        """

        async with self.lock:
            if client in self.clients:
                await client.close(1011, "Connection closed")
                self.clients.remove(client)

            if not self.clients:
                await self.cache.destory_channel(self.channel_id)
                await self.pubsub.reset()


class ChannelCache(object):
    """
    This class is used to store and manage channel instances
    """

    def __init__(self):
        self.channels = dict()
        self.lock = asyncio.Lock()

    async def get_or_create(self, channel_id: str) -> Type[Channel]:
        """
        If channel exists create new one, and return it's instance.
        Otherwise just return channel instance
        """

        async with self.lock:
            if not channel_id in self.channels:
                pubsub = REDIS.pubsub()
                await pubsub.subscribe(channel_id)
                channel = Channel(self, pubsub, channel_id)
                await self.__add_channel(channel_id, channel)
                return channel, True
            else:
                return self.channels.get(channel_id), False

    async def __add_channel(self, channel_id: str, channel: Type[Channel]) -> None:
        """
        Add new channel to channels dict
        """

        self.channels[channel_id] = channel

    async def destory_channel(self, channel_id: str) -> None:
        """
        Delete channel from channels dict
        """

        async with self.lock:
            del self.channels[channel_id]
