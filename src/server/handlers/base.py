import logging
import json
from typing import Type
from server.base import AbstractClient
from abc import ABC, abstractmethod


class AbstractMessageHandler(ABC):
    """
    Abstract MessageHandler classs. Provides basic interface
    that can be used to create more complex message handlers
    """

    @classmethod
    @abstractmethod
    def operation_names(cls):
        raise NotImplementedError("'operation_names' class attribute is not specified")

    @classmethod
    @abstractmethod
    def redis(cls):
        raise NotImplementedError("'redis' class attribute is not specified")

    async def dispatch(
        self, message: str, codespace_uuid: str, client: Type[AbstractClient]
    ) -> None:
        """
        Try to dispatch to the right operation; if a operation doesn't exist
        close websocket connection
        """

        try:
            message = json.loads(message)
            operation = message.get("operation")
        except AttributeError:
            await client.close(1011, f"Message has no 'operation' attribute")
        else:
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
