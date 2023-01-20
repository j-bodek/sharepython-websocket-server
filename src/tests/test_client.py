from unittest import IsolatedAsyncioTestCase, mock
from server.client import Client


class TestClient(IsolatedAsyncioTestCase):
    """
    Test Client class
    """

    def setUp(self):
        self.protocol = mock.MagicMock()
        self.message_handler = mock.MagicMock()
        self.channel_id = "channel_id"
        self.client = Client(
            protocol=self.protocol,
            channel_id=self.channel_id,
            message_handler=self.message_handler,
            mode="edit",
        )

    async def test_if_dispatch_called_on_new_message(self):
        """
        Test if in listen method when new websocket message arives.
        dispatch method is called
        """

        self.message_handler.dispatch = mock.AsyncMock()
        messages = ["message 1", "message 2"]
        self.protocol.__aiter__.return_value = messages
        await self.client.listen()
        self.assertEqual(self.message_handler.dispatch.call_count, 2)

    @mock.patch("server.client.REDIS.publish", new_callable=mock.AsyncMock)
    async def test_publish_method(self, patched_publish):
        """
        Test if redis publish method is called properly
        """

        await self.client.publish("message")
        patched_publish.assert_called_once_with(self.channel_id, "message")

    async def test_close_method(self):
        """
        Test if close method close websocket connection
        """

        args = [1011, "close reason"]
        self.protocol.close = mock.AsyncMock()
        await self.client.close(*args)
        self.protocol.close.assert_called_once_with(*args)

    async def test_send_method(self):
        """
        Test if send method send message to websocket
        """

        self.protocol.send = mock.AsyncMock()
        await self.client.send("message")
        self.protocol.send.assert_called_once_with("message")
