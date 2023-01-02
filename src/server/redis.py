import redis
import os

REDIS = redis.Redis(
    host=os.environ.get("REDIS_HOST"),
    port=os.environ.get("REDIS_PORT"),
    password=os.environ.get("REDIS_PASS"),
    charset="utf-8",
    decode_responses=True,
)
