import json
from server.redis import REDIS
from typing import Type
from server.base import AbstractClient
from server.handlers.base import AbstractMessageHandler
import logging


class BaseMessageHandler(AbstractMessageHandler):
    """
    BaseMessageHandler provides generic methods dispatch and operation_not_allowed.
    It can be used to create more complex message handlers
    """

    operation_names = []
    redis = None

    async def dispatch(
        self, message: str, codespace_uuid: str, client: Type[AbstractClient]
    ) -> None:
        """
        Try to dispatch to the right operation; if a operation doesn't exist
        close websocket connection
        """

        try:
            message = json.loads(message)
            operation = message["operation"]
        except (ValueError, TypeError):
            await client.close(1011, "Message does not have specified 'operation'")
        else:
            # to check allowed operation is used class attribute instead of checking
            # of method exists by has attr because if method exists it doesn't mean
            # that it should be treated as operation (for example dispatch, if it
            # will be called infinie loop will occure)
            if operation in self.operation_names:
                handler = getattr(self, operation.lower())
            else:
                handler = self.operation_not_allowed
            await handler(message, codespace_uuid, client)

    async def operation_not_allowed(
        self, message: dict, codespace_uuid: str, client: Type[AbstractClient]
    ) -> None:
        """
        Close websocket connection and return proper reason
        """

        logging.warning(
            f"{message.get('operation')} Operation Is Not Allowed",
        )

        await client.close(
            1011, f"'{message.get('operation')}' operation is not allowed"
        )


class MessageHandler(BaseMessageHandler):
    """
    This class is used to handle incoming websocket messages.
    I created it to hermetise logic responsible for handling incoming messages,
    and to prevent creation of huge client class

    It handles messages in following format:
    {
        "operation":"operation_name",
        **kwargs
    }
    """

    # allowed operations
    operation_names = [
        "insert_value",
        "create_selection",
    ]
    redis = REDIS

    async def insert_value(
        self, message: dict, codespace_uuid: str, client: Type[AbstractClient]
    ) -> None:
        """
        This operation updates codespace code saved in redis and send
        message to redis pub/sub channel
        """

        # make sure to use asyncio lock when coroutine is suspended between retrieving
        # data from redis and seting new value back. This will prevent race condition
        # discribed here: https://superfastpython.com/asyncio-race-conditions/
        if (code := await self.redis.hget(codespace_uuid, "code")) is not None:

            # this function shouldn't be async because data value is copied form redis
            # and during update another worker can retrieve code data before updated
            # data will be saved
            code = self.__update_code_with_changes(code, message)

            # set updated client value
            await self.redis.hset(codespace_uuid, "code", code)
            # update expire time
            await self.redis.expire(codespace_uuid, client.codespace_expire_update)
            await self.publish(codespace_uuid, json.dumps(message))
        else:
            client.close(1011, "Can't find data for given codespace")

    def __update_code_with_changes(self, code: str, message: dict) -> str:
        """
        when updating string from last change we can be sure
        that insertion index of previous ones remain unchanged
        because insertion can't overlap each others
        message["changes"] is list in following format:
        [
            {"from":int, "to":int, "insert":str},
        ]
        """

        for change in message["changes"][::-1]:
            code = (
                code[: change["from"]] + change["insert"] + code[change["to"] :]  # noqa
            )

        return code

    async def create_selection(
        self, message: dict, codespace_uuid: str, client: Type[AbstractClient]
    ) -> None:
        """
        This operation is used to handle create_selection operation
        """

        await self.publish(codespace_uuid, json.dumps(message))

    @classmethod
    async def publish(cls, channel_id: str, msg: str) -> None:
        # this method is used to publish message via redis pub/sub channels
        await cls.redis.publish(channel_id, msg)


message_handler = MessageHandler()
