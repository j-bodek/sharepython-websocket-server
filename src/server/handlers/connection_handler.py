from server.channel import ChannelCache
from server.authentication import Authenticate
from sanic import Sanic, Websocket
from typing import Type
from server.base import AbstractClient
import json
from server.client import Client


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
        client = await channel.create_client(websocket)
        await channel.register(client)
        await cls.send_connection_succeed_msg(client)

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

    @classmethod
    async def send_connection_succeed_msg(cls, client: Type[AbstractClient]) -> None:
        """
        Inform client about successfull connection. In response send
        id assigned to client in channel
        """

        await client.send(
            json.dumps(
                {
                    "operation": "connected",
                    "data": {"id": client.id},
                }
            )
        )


connection_handler = ConnectionHandler()
