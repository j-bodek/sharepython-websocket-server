import aiohttp
from typing import Type
from sanic import Websocket


class Authenticate(object):
    """
    This class is used to authenticate incoming websocket connection.
    It sends async request to api to check given token
    """

    # big thx https://stackoverflow.com/a/56297455/14579046
    # host should be name of container instead of localhost
    api_base_url = "http://api:8000/api/"

    async def __call__(
        self, websocket: Type[Websocket], token: str
    ) -> tuple[str, bool]:
        """
        Authenticate request by given token and if token is valid
        return codespace uuid, and is_created value set to True
        """

        if not token:
            await websocket.close(1011, "Missing token")
            return None, False

        # send async request
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_base_url}codespace/{token}/?fields=uuid"
            ) as resp:

                if resp.status != 200:
                    await websocket.close(1011, "Invalid token")
                    return None, False

                data = await resp.json()
                return data["uuid"], True
