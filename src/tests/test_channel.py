from unittest import IsolatedAsyncioTestCase, mock
from server.channel import Channel, ChannelCache


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
        Test if leave method close client connection and remove
        it instance from clients set
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
        Test if leave method close client connection and remove it instance
        from clients set and if destroy channel and reset pubsub
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


class TestChannelCache(IsolatedAsyncioTestCase):
    """
    Test ChannelCache class
    """

    def setUp(self):
        self.cache = ChannelCache()

    async def test_get_or_create_method_with_existing_channel(self):
        """
        Test if valid channel is returned without creating new instance
        """

        mock_channel = mock.Mock(id="channel_id")
        self.cache.channels = {mock_channel.id: mock_channel}
        channel, is_created = await self.cache.get_or_create(mock_channel.id)
        self.assertEqual(channel, mock_channel)
        self.assertFalse(is_created)
        self.assertEqual(len(self.cache.channels), 1)

    @mock.patch("server.channel.ChannelCache._ChannelCache__create_channel")
    @mock.patch("server.channel.REDIS.pubsub")
    async def test_get_or_create_method_with_new_channel(
        self, mocked_pubsub, mocked_create_channel
    ):
        """
        Test if new channel instance and PubSub instance is created
        """

        channel_id = "channel_id"
        mocked_create_channel.return_value = mock.Mock(id=channel_id)
        mocked_pubsub_instace = mock.AsyncMock()
        mocked_pubsub.return_value = mocked_pubsub_instace
        channel, is_created = await self.cache.get_or_create(channel_id)
        self.assertEqual(channel.id, channel_id)
        self.assertTrue(is_created)
        self.assertEqual(len(self.cache.channels), 1)
        mocked_pubsub_instace.subscribe.assert_called_once_with(channel_id)

    async def test_add_channel_method(self):
        """
        Test if add channel adds new channel instance to channels cache
        """

        channel = mock.Mock(id="channel_id")
        await self.cache._ChannelCache__add_channel(channel.id, channel)
        self.assertEqual(self.cache.channels[channel.id], channel)

    async def test_destory_channel_method(self):
        """
        Test if destory channel method remove channel instance from cache
        """

        channel = mock.Mock(id="channel_id")
        self.cache.channels = {channel.id: channel}
        await self.cache.destroy_channel(channel.id)
        self.assertEqual(self.cache.channels.get(channel.id), None)
