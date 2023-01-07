import logging
import json
from server.redis import REDIS


class MessageHandler(object):

    operation_names = [
        "insert_value",
        "remove_value",
        "move_cursor",
    ]
    redis = REDIS

    async def dispatch(self, message, codespace_uuid, client):
        # Try to dispatch to the right operation; if a operation doesn't exist
        # close websocket connection
        message = json.loads(message)
        if (
            operation := message.get("operation")
        ) and operation in self.operation_names:
            handler = getattr(self, operation.lower())
        else:
            handler = self.operation_not_allowed

        await handler(message, codespace_uuid, client)

    async def operation_not_allowed(self, message, codespace_uuid, client):
        """
        Close websocket connection and return proper reason
        """

        logging.warning(
            f"{message.get('operation')} Operation Is Not Allowed",
        )

        await client.close(
            1011, f"'{message.get('operation')}' operation is not allowed"
        )

    async def insert_value(self, message, codespace_uuid, client) -> None:
        if (data := await self.redis.hget(codespace_uuid, "code")) is not None:
            data = (
                data[: message["input"]["position"]["start"]]
                + message["input"]["value"]
                + data[message["input"]["position"]["end"] :]
            )

            await self.redis.hset(codespace_uuid, "code", data)
            await self.publish(codespace_uuid, json.dumps(message))

    @classmethod
    async def publish(cls, channel_id, msg):
        # this method is used to publish message via redis
        await cls.redis.publish(channel_id, msg)


message_handler = MessageHandler()
