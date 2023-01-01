import aiohttp
from urllib import parse


class WebSocketHandler(object):

    # big thx https://stackoverflow.com/a/56297455/14579046
    # host should be name of container instead of localhost
    api_base_url = "http://api:8000/api/"

    def __init__(self):
        self.websocket = None
        self.codespace_uuid = None

    async def __call__(self, websocket):
        self.websocket = websocket
        token = parse.parse_qs(parse.urlparse(self.websocket.path).query).get(
            "token", [None]
        )[0]
        # if request not authenticated connection will be closed
        await self.authenticate(token)

        # This will be iterating over messages received on
        # the connection until the client disconnects
        async for message in self.websocket:
            print(self.codespace_uuid, message)

    async def authenticate(self, token: str) -> None:
        """
        Authenticate request by given token and if token is valid
        update codespace_uuid
        """

        if not token:
            await self.websocket.close(1011, "Missing token")
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_base_url}codespace/{token}/?fields=uuid"
            ) as resp:
                if resp.status != 200:
                    await self.websocket.close(1011, "Invalid token")
                    return

                data = await resp.json()
                self.codespace_uuid = data["uuid"]
