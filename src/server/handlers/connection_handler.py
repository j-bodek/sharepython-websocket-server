from server.channel import ChannelCache
from server.authentication import Authenticate
from sanic import Sanic, Websocket
from typing import Type


class ConnectionHandler:
    """
    This class is responsible for handling new websocket connections
    """

    channels = ChannelCache()
    authentication = Authenticate()

    @classmethod
    async def __call__(
        cls, websocket: Type[Websocket], token: str, app: Type[Sanic]
    ) -> None:
        # Authenticate incoming connection
        codespace_uuid, is_authenticated = await cls.perform_authentication(
            websocket, token
        )

        if not is_authenticated:
            return

        # get or create channel for codespace
        channel, is_created = await cls.channels.get_or_create(codespace_uuid)

        # if new channel run in background method listening for new messages
        if is_created:
            app.add_task(channel.listen())

        # register new client in channel
        client = await channel.register(websocket)

        try:
            # listen new messages coming from websocket connection
            await client.listen()
        finally:
            # after connection lost leave client from channel
            await channel.leave(client)

    @classmethod
    async def perform_authentication(
        cls, websocket: Type[Websocket], token: str
    ) -> tuple[str, bool]:
        """
        Perform authentication. Returns codespace uuid, and is_authenticated
        """

        return await cls.authentication(websocket, token)


connection_handler = ConnectionHandler()
