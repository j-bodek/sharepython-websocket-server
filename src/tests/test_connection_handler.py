from unittest import IsolatedAsyncioTestCase, mock
from server.handlers.connection_handler import connection_handler
from websockets.exceptions import ConnectionClosedOK
import json


class TestConnectionHandler(IsolatedAsyncioTestCase):
    """
    Test ConnectionHandler class
    """

    def setUp(self):
        self.connection_handler = connection_handler

    @mock.patch(
        "server.handlers.connection_handler.ConnectionHandler.perform_authentication",
        return_value=(None, None, False),
    )
    @mock.patch(
        "server.handlers.connection_handler.ConnectionHandler.channels.get_or_create"
    )
    async def test_with_unauthenticated_connection(
        self, patched_get_or_create, patched_perform_authentication
    ):
        """
        Test if connection is unauthenticated connection handler execution
        ends directly after perform_authentication
        """

        await self.connection_handler(mock.Mock(), "token", mock.Mock())
        self.assertEqual(patched_get_or_create.call_count, 0)

    @mock.patch("server.handlers.connection_handler.ConnectionHandler.authentication")
    async def test_perform_authentication_with_tmp_uuid(self, patched_authentication):
        """
        Test if authentication class will not be called, and tmp_uuid, "edit", True
        tuple will be returned
        """
        output = await self.connection_handler.perform_authentication(
            mock.AsyncMock(), "tmp-uuid"
        )
        self.assertEqual(output, ("tmp-uuid", "edit", True))
        self.assertEqual(patched_authentication.call_count, 0)

    @mock.patch(
        "server.handlers.connection_handler.ConnectionHandler.authentication",
        new_callable=mock.AsyncMock,
    )
    async def test_perform_authentication_with_normal_uuid(
        self, patched_authentication
    ):
        """
        Test if authentication class will not be called, and tmp_uuid, "edit", True
        tuple will be returned
        """
        expected_output = ("some_uuid", "view_only", True)
        patched_authentication.return_value = expected_output

        output = await self.connection_handler.perform_authentication(
            mock.AsyncMock(), "some_token"
        )
        self.assertEqual(output, expected_output)
        self.assertEqual(patched_authentication.call_count, 1)

    async def test_add_channel_listener_with_new_channel_created(self):
        """
        Test if new channel is created it is added to background tasks
        """

        mocked_channel = mock.MagicMock()
        mocked_app = mock.MagicMock()
        self.connection_handler.add_channel_listener(True, mocked_channel, mocked_app)
        mocked_app.add_task.assert_called_once_with(mocked_channel.listen())

    async def test_send_connection_succeed_msg_method(self):
        """
        Test if message informing about successfull connection is send
        """

        mocked_client = mock.AsyncMock(id="client_id", mode="edit")
        await self.connection_handler.send_connection_succeed_msg(mocked_client)
        self.assertEqual(mocked_client.send.call_count, 1)
        args, kwargs = mocked_client.send.call_args
        msg = json.loads(kwargs["message"])
        self.assertEqual(msg["operation"], "connected")
        self.assertEqual(msg["data"]["id"], "client_id")
        self.assertEqual(msg["data"]["mode"], "edit")

    async def test_add_client_listener_method(self):
        """
        Test if with valid connection client.listen() method is called
        """

        mocked_client = mock.AsyncMock()
        await self.connection_handler.add_client_listener(
            mocked_client, mock.AsyncMock()
        )
        self.assertEqual(mocked_client.listen.call_count, 1)

    async def test_if_connection_closed_channel_leave_executed(self):
        """
        Test if during client.listen() connection closed exection is raised
        channel.leave() will be executed
        """

        mocked_channel = mock.AsyncMock()
        mocked_client = mock.AsyncMock()
        mocked_client.side_effect = [ConnectionClosedOK]
        await self.connection_handler.add_client_listener(mocked_client, mocked_channel)
        mocked_channel.leave.assert_called_once_with(mocked_client)
