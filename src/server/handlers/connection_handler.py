from server.channel import ChannelCache
from server.authentication import Authenticate
from sanic import Sanic, Websocket
from typing import Type
from server.base import AbstractClient, AbstractChannel
import json


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
        cls.add_channel_listener(is_created, channel, app)

        # register new client in channel
        client = await channel.create_client(websocket)
        await channel.register(client)
        await cls.send_connection_succeed_msg(client)
        await cls.add_client_listener(client, channel)

    @classmethod
    async def add_client_listener(
        cls, client: Type[AbstractClient], channel: Type[AbstractChannel]
    ) -> None:
        """
        Run client.listen() method
        """

        try:
            # listen new messages coming from websocket connection
            await client.listen()
        finally:
            # after connection lost leave client from channel
            await channel.leave(client)

    @classmethod
    def add_channel_listener(
        cls, is_created: bool, channel: Type[AbstractChannel], app: Type[Sanic]
    ) -> None:
        """
        Run channel.listen() method in background
        """

        if is_created:
            app.add_task(channel.listen())

    @classmethod
    async def perform_authentication(
        cls, websocket: Type[Websocket], token: str
    ) -> tuple[str, bool]:
        """
        Perform authentication. Returns codespace uuid, and is_authenticated
        """

        return await cls.authentication(websocket, token)

    @classmethod
    async def send_connection_succeed_msg(cls, client: Type[AbstractClient]) -> None:
        """
        Inform client about successfull connection. In response send
        id assigned to client in channel
        """

        await client.send(
            message=json.dumps(
                {
                    "operation": "connected",
                    "data": {"id": client.id},
                }
            )
        )


connection_handler = ConnectionHandler()
