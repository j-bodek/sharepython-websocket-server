from server.client import Client
from server.redis import REDIS
import asyncio
import aioredis
from server.handlers.message_handler import message_handler
from typing import Type
from sanic import Websocket
from dataclasses import dataclass, field
from server.base import AbstractChannel, AbstractChannelCache


@dataclass(repr=False, slots=True)
class Channel(AbstractChannel):
    """
    This class is used to store Client instances and send received messages to them.
    It represents communication channel created for particular codespace
    """

    cache: Type[AbstractChannelCache]
    pubsub: Type[aioredis.client.PubSub]
    channel_id: str
    clients: set = field(init=False, default_factory=lambda: set())
    lock: Type[asyncio.Lock] = field(init=False, default_factory=lambda: asyncio.Lock())
    # define messages that should be handled by channel not clients
    # for example 'expire' message send when codespace data is expired
    handle_messages: list = field(init=False, default_factory=lambda: ["expired"])

    async def listen(self) -> None:
        """
        Listen new pubsub messages and send them to connected clients
        """
        try:
            async for message in self.pubsub.listen():
                if message["type"] != "message":
                    continue

                if message["data"] in self.handle_messages:
                    await getattr(self, message["data"])()
                else:
                    # if message is not handled by channel
                    # broadcast it to clients
                    await self.broadcast(message)

        except aioredis.exceptions.ConnectionError:
            print(f"PUBSUB closed <{self.channel_id}>")

    async def expired(self) -> None:
        """
        Close connection for every client
        """

        for client in self.clients:
            await client.close(1011, "Codespace data expired from cache")

    async def broadcast(self, message: str) -> None:
        """
        Send message to all connected clients
        """

        payload = message["data"]
        for client in self.clients:
            await client.send(payload)

    async def register(self, client: Type[Client]):
        """
        Add client to clients set
        """

        async with self.lock:
            self.clients.add(client)

    async def create_client(self, websocket: Type[Websocket]) -> Type[Client]:
        """
        Create and return new client instance
        """
        return Client(
            protocol=websocket,
            channel_id=self.channel_id,
            message_handler=message_handler,
        )

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
                await self.cache.destroy_channel(self.channel_id)
                await self.pubsub.reset()


@dataclass(repr=False, slots=True)
class ChannelCache(AbstractChannelCache):
    """
    This class is used to store and manage channel instances
    """

    channels: set = field(init=False, default_factory=lambda: dict())
    lock: Type[asyncio.Lock] = field(init=False, default_factory=lambda: asyncio.Lock())

    async def get_or_create(self, channel_id: str) -> Type[AbstractChannel]:
        """
        If channel exists create new one, and return it's instance.
        Otherwise just return channel instance
        """

        async with self.lock:
            if channel_id not in self.channels:
                pubsub = REDIS.pubsub()
                await pubsub.subscribe(channel_id)
                await pubsub.subscribe(f"__keyspace@0__:{channel_id}")
                channel = await self.__create_channel(pubsub, channel_id)
                await self.__add_channel(channel_id, channel)
                return channel, True
            else:
                return self.channels.get(channel_id), False

    async def __create_channel(
        self, pubsub: REDIS.pubsub, channel_id: str
    ) -> Type[AbstractChannel]:
        """
        Creates and return new channel instance
        """

        return Channel(cache=self, pubsub=pubsub, channel_id=channel_id)

    async def __add_channel(
        self, channel_id: str, channel: Type[AbstractChannel]
    ) -> None:
        """
        Add new channel to channels dict
        """

        self.channels[channel_id] = channel

    async def destroy_channel(self, channel_id: str) -> None:
        """
        Delete channel from channels dict
        """

        async with self.lock:
            del self.channels[channel_id]
