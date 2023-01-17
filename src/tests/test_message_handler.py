from unittest import IsolatedAsyncioTestCase, mock
from server.handlers.message_handler import BaseMessageHandler, message_handler
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


class TestMessageHandler(IsolatedAsyncioTestCase):
    """
    Test MessageHandler class
    """

    def setUp(self):
        self.message_handler = message_handler

    @mock.patch(
        "server.handlers.message_handler.MessageHandler.redis",
        new_callable=mock.AsyncMock,
    )
    async def test_insert_with_unexisting_codespace(self, patched_redis):
        """
        Test if code for codespace_uuid does not exists in redis
        """
        patched_redis.hget.return_value = None
        client = mock.AsyncMock()
        await self.message_handler.insert_value({}, "codespace_uuid", client)
        self.assertEqual(patched_redis.hset.call_count, 0)
        self.assertEqual(client.close.call_count, 1)

    @mock.patch(
        "server.handlers.message_handler.MessageHandler.redis",
        new_callable=mock.AsyncMock,
    )
    @mock.patch(
        "server.handlers.message_handler.MessageHandler.publish",
        new_callable=mock.AsyncMock,
    )
    async def test_insert_if_code_exists(self, patched_publish, patched_redis):
        """
        Test if code exists redis.hset with updated code should be called
        and publish method with incoming message
        """

        patched_redis.hget.return_value = ""
        await self.message_handler.insert_value(
            {"changes": []}, "codespace_uuid", mock.AsyncMock()
        )
        self.assertEqual(patched_redis.hset.call_count, 1)
        self.assertEqual(patched_publish.call_count, 1)

    @mock.patch(
        "server.handlers.message_handler.MessageHandler.redis",
        new_callable=mock.AsyncMock,
    )
    def test_insert_with_one_change(self, patched_redis):
        """
        Test if code is updated properly with one change
        """

        changes = [
            {"from": 6, "to": 11, "insert": "World"},
        ]
        code = "Hello dlroW"
        code = self.message_handler._MessageHandler__update_code_with_changes(
            code, {"changes": changes}
        )
        self.assertEqual(code, "Hello World")

    @mock.patch(
        "server.handlers.message_handler.MessageHandler.redis",
        new_callable=mock.AsyncMock,
    )
    def test_insert_with_multiple_changes(self, patched_redis):
        """
        Test if code is updated properly with multiple changes
        """

        changes = [
            {"from": 5, "to": 5, "insert": " Great"},
            {"from": 6, "to": 11, "insert": "World"},
        ]
        code = "Hello dlroW"
        code = self.message_handler._MessageHandler__update_code_with_changes(
            code, {"changes": changes}
        )
        self.assertEqual(code, "Hello Great World")

    @mock.patch(
        "server.handlers.message_handler.MessageHandler.publish",
        new_callable=mock.AsyncMock,
    )
    async def test_create_selection(self, patched_publish):
        """
        Test if publish method is called with codespace_uuid and incoming message
        """

        await self.message_handler.create_selection(
            {"operation": "create_selection"}, "codespace_uuid", "client"
        )
        patched_publish.assert_called_once_with(
            "codespace_uuid", json.dumps({"operation": "create_selection"})
        )

    @mock.patch(
        "server.handlers.message_handler.MessageHandler.redis",
        new_callable=mock.AsyncMock,
    )
    async def test_publish_method(self, patched_redis):
        """
        Test if incoming message is published properly to redis pub/sub channel
        """

        await self.message_handler.publish("channel_id", "msg")
        patched_redis.publish.assert_called_once_with("channel_id", "msg")
