from server.channel import ChannelCache
import asyncio


class ConnectionHandler(object):
    """
    This class is responsible for handling websocket connection
    """

    channels = ChannelCache()

    @classmethod
    async def __call__(cls, websocket, codespace_uuid):

        # This will be iterating over messages received on
        # the connection until the client disconnects

        channel, is_created = await cls.channels.get_or_create(codespace_uuid)

        if is_created:
            # run channel.listen() method in background
            asyncio.create_task(channel.listen())

        client = await channel.register(websocket)

        try:
            # listen client messages
            await client.listen()
        finally:
            await client.close(1011, "Connection closed")
            await channel.leave(client)
