from server.client import Client
from server.redis import REDIS
import asyncio
import aioredis


class Channel(object):
    def __init__(self, cache, pubsub, channel_id):
        self.clients = set()
        self.cache = cache
        self.pubsub = pubsub
        self.channel_id = channel_id
        self.lock = asyncio.Lock()

    async def listen(self):
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

    async def broadcast(self, message):
        """
        Send message to connected clients
        """

        payload = message["data"]
        for client in self.clients:
            await client.send(payload)

    async def register(self, websocket):
        """
        Create new client instance and add it to client set
        """
        async with self.lock:
            client = Client(protocol=websocket, channel_id=self.channel_id)
            self.clients.add(client)
            return client

    async def leave(self, client):
        async with self.lock:
            if client in self.clients:
                await client.close(1011, "Connection closed")
                self.clients.remove(client)

            if not self.clients:
                await self.cache.destory_channel(self.channel_id)
                await self.pubsub.reset()


class ChannelCache(object):
    def __init__(self):
        self.channels = dict()
        self.lock = asyncio.Lock()

    async def get_or_create(self, channel_id: str) -> Channel:
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

    async def __add_channel(self, channel_id, channel):
        """
        Add new channel to channels dict
        """

        self.channels[channel_id] = channel

    async def destory_channel(self, channel_id):
        async with self.lock:
            del self.channels[channel_id]
