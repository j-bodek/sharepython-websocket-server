from unittest import IsolatedAsyncioTestCase, mock
from server.channel import Channel


class TestChannel(IsolatedAsyncioTestCase):
    """
    Test Channel Class
    """

    def setUp(self):
        self.channel_id = "channel_id"
        self.pubsub = mock.MagicMock()
        self.cache = mock.MagicMock()
        self.channel = Channel(
            channel_id=self.channel_id, pubsub=self.pubsub, cache=self.cache
        )

    @mock.patch("server.channel.Channel.broadcast")
    async def test_listen_method_with_message_type_message(self, patched_broadcast):
        """
        Test if broadcast method is called
        """

        self.pubsub.listen.return_value.__aiter__.return_value = [
            {"type": "message"},
        ]
        await self.channel.listen()
        self.assertEqual(patched_broadcast.call_count, 1)
        patched_broadcast.assert_called_once_with({"type": "message"})

    @mock.patch("server.channel.Channel.broadcast")
    async def test_listen_method_with_message_type_not_message(self, patched_broadcast):
        """
        Test if broadcast method is not called
        """

        self.pubsub.listen.return_value.__aiter__.return_value = [
            {"type": "not_message"},
        ]
        await self.channel.listen()
        self.assertEqual(patched_broadcast.call_count, 0)

    async def test_broadcast_method(self):
        """
        Test if broadcast method send message to every connected client
        """
        clients = {mock.AsyncMock() for _ in range(4)}
        self.channel.clients = clients
        await self.channel.broadcast({"data": "some_data"})
        for client in clients:
            client.send.assert_called_once_with("some_data")

    async def test_register_method(self):
        """
        Test if register method create client instance and add it to clients set
        """

        await self.channel.register("client")
        self.assertIn("client", self.channel.clients)

    async def test_leave_method(self):
        """
        Test if leave method close client connection and remove it instance from clients set
        """
        client1 = mock.AsyncMock()
        client2 = mock.AsyncMock()
        self.channel.clients = {client1, client2}
        await self.channel.leave(client1)
        client1.close.assert_called_once_with(1011, "Connection closed")
        self.assertNotIn(client1, self.channel.clients)
        self.assertIn(client2, self.channel.clients)

    async def test_leave_method_with_last_client(self):
        """
        Test if leave method close client connection and remove it instance from clients set and
        if destroy channel and reset pubsub
        """

        client1 = mock.AsyncMock()
        self.channel.clients = {client1}
        self.channel.cache = mock.AsyncMock()
        self.channel.pubsub = mock.AsyncMock()
        await self.channel.leave(client1)
        client1.close.assert_called_once_with(1011, "Connection closed")
        self.assertNotIn(client1, self.channel.clients)
        self.assertEqual(self.channel.pubsub.reset.call_count, 1)
        self.channel.cache.destroy_channel.assert_called_once_with(self.channel_id)
