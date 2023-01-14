from unittest import IsolatedAsyncioTestCase, mock
from server.handlers.message_handler import BaseMessageHandler, MessageHandler
import json


class TestBaseMessageHandler(IsolatedAsyncioTestCase):
    """
    Test BaseMessageHandler class
    """

    def setUp(self):
        self.message_handler = BaseMessageHandler()

    async def test_dispatch_with_invalid_message(self):
        """
        Test if message don't have operation or is not json serializable
        connection is closed
        """

        not_json_serializable = [1, 2, 3]
        without_operation = {"data": "message"}
        client = mock.AsyncMock()
        for attempt, message in enumerate(
            [not_json_serializable, without_operation], start=1
        ):
            await self.message_handler.dispatch(message, "codespace_uuid", client)
            self.assertEqual(client.close.call_count, attempt)

    @mock.patch(
        "server.handlers.message_handler.BaseMessageHandler.operation_not_allowed"
    )
    async def test_distpatch_with_invalid_operation(
        self, patched_operation_not_allowed
    ):
        """
        Test if operation is invalid 'operation_not_allowed' method is executed
        """

        message = json.dumps({"operation": "invalid_operation", "data": "message"})
        await self.message_handler.dispatch(message, "codespace_uuid", mock.AsyncMock())
        self.assertEqual(patched_operation_not_allowed.call_count, 1)

    async def test_with_allowed_operation(self):
        """
        Test if operation is allowed corresponding method should be called
        """

        self.message_handler.mocked_operation = mock.AsyncMock()
        self.message_handler.operation_names = ["mocked_operation"]
        message = json.dumps({"operation": "mocked_operation", "data": "message"})
        await self.message_handler.dispatch(message, "codespace_uuid", mock.AsyncMock())
        self.assertEqual(self.message_handler.mocked_operation.call_count, 1)

    async def test_operation_not_allowed_method(self):
        """
        Test if client connection is closed
        """

        mocked_client = mock.AsyncMock()
        await self.message_handler.operation_not_allowed(
            {"operation": "invalid_operation"}, "codespace_uuid", mocked_client
        )
        self.assertEqual(mocked_client.close.call_count, 1)
