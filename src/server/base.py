from abc import ABC, abstractmethod


class AbstractClient(ABC):
    @abstractmethod
    async def listen(self):
        pass

    @abstractmethod
    async def send(self, message: str):
        pass

    @abstractmethod
    async def close(self, code: int, reason: str):
        pass


class AbstractChannel(ABC):
    @abstractmethod
    async def listen(self):
        pass

    @abstractmethod
    async def register(self, message: str):
        pass

    @abstractmethod
    async def leave(self, code: int, reason: str):
        pass


class AbstractChannelCache(ABC):
    @abstractmethod
    async def get_or_create(self):
        pass

    @abstractmethod
    async def destroy_channel(self, code: int, reason: str):
        pass
