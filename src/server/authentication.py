import aiohttp


class Authenticate(object):

    # big thx https://stackoverflow.com/a/56297455/14579046
    # host should be name of container instead of localhost
    api_base_url = "http://api:8000/api/"

    async def __call__(self, websocket, token: str) -> str:
        """
        Authenticate request by given token and if token is valid
        update codespace_uuid
        """

        if not token:
            await websocket.close(1011, "Missing token")
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_base_url}codespace/{token}/?fields=uuid"
            ) as resp:
                if resp.status != 200:
                    await websocket.close(1011, "Invalid token")
                    return

                data = await resp.json()
                return data["uuid"]
