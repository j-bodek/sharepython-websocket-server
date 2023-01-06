import aioredis
import os

REDIS = aioredis.Redis(
    host=os.environ.get("REDIS_HOST"),
    port=os.environ.get("REDIS_PORT"),
    password=os.environ.get("REDIS_PASS"),
    encoding="utf-8",
    decode_responses=True,
)
