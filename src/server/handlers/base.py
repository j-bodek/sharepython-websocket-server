from typing import Type
from server.base import AbstractClient
from abc import ABC, abstractmethod


class AbstractMessageHandler(ABC):
    """
    Abstract MessageHandler class. Defines basic message handler interface
    """

    @classmethod
    @abstractmethod
    def operation_names(cls):
        raise NotImplementedError("'operation_names' class attribute is not specified")

    @classmethod
    @abstractmethod
    def redis(cls):
        raise NotImplementedError("'redis' class attribute is not specified")

    @abstractmethod
    async def dispatch(
        self, message: str, codespace_uuid: str, client: Type[AbstractClient]
    ) -> None:
        pass

    @abstractmethod
    async def operation_not_allowed(
        self, message: dict, codespace_uuid: str, client: Type[AbstractClient]
    ) -> None:
        pass
