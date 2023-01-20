from unittest import IsolatedAsyncioTestCase, mock
from server.authentication import Authenticate


class TestAuthentication(IsolatedAsyncioTestCase):
    """
    Test Authenticate Class
    """

    def setUp(self):
        self.authenticator = Authenticate()

    async def test_without_token(self):
        """
        Test if connection is closed and tuple of None, None, False is returned
        """

        mocked_websocket = mock.AsyncMock()
        uuid, mode, is_authenticated = await self.authenticator(mocked_websocket, None)
        self.assertEqual(mocked_websocket.close.call_count, 1)
        self.assertEqual(uuid, None)
        self.assertEqual(mode, None)
        self.assertFalse(is_authenticated)

    @mock.patch("server.authentication.aiohttp.ClientSession.get")
    async def test_with_invalid_token(self, patched_get):
        """
        Test if connection is closed and tuple of None, False is returned
        """

        patched_get.return_value.__aenter__.return_value = mock.AsyncMock(status=301)
        mocked_websocket = mock.AsyncMock()
        uuid, mode, is_authenticated = await self.authenticator(
            mocked_websocket, "invalid_token"
        )
        self.assertEqual(mocked_websocket.close.call_count, 1)
        self.assertEqual(uuid, None)
        self.assertEqual(mode, None)
        self.assertFalse(is_authenticated)

    @mock.patch("server.authentication.aiohttp.ClientSession.get")
    async def test_with_valid_token(self, patched_get):
        """
        Test if tuple of uuid, True is returned
        """

        mocked_resp = mock.AsyncMock(status=200)
        mocked_resp.json.return_value = {"uuid": "codespace_uuid", "mode": "edit"}
        patched_get.return_value.__aenter__.return_value = mocked_resp
        mocked_websocket = mock.AsyncMock()
        uuid, mode, is_authenticated = await self.authenticator(
            mocked_websocket, "valid_token"
        )
        self.assertEqual(mocked_websocket.close.call_count, 0)
        self.assertEqual(uuid, "codespace_uuid")
        self.assertEqual(mode, "edit")
        self.assertTrue(is_authenticated)
