import asyncio
from typing import Any
from restq import Queue
from test_pickle import TestPickleClass
from redis.asyncio import Redis as AsyncRedis, from_url as redis_from_url


REDIS_URL = "redis://localhost:6379/0"

async def get_redis_client(*args: Any, **kwargs: Any) -> AsyncRedis: # type: ignore
    redis = await redis_from_url(REDIS_URL, *args, **kwargs)

    return redis


async def main() -> None:
    redis = await get_redis_client(decode_responses=True)

    queue = Queue(name="email-queue", redis=redis)

    await queue.add(task_name="sendWorkEmailTask", delay=100, kwargs={"name": "Wisdom"}, mode="json")



asyncio.run(main())
