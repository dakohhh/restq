import asyncio
from typing import Any
from restq import AsyncQueue, Queue
from test_pickle import TestPickleClass
from redis import Redis, from_url as redis_from_url


REDIS_URL = "redis://localhost:6379/0"


async def main() -> None:

    queue = Queue(name="email-queue", redis=redis_from_url(url=REDIS_URL, decode_responses=True)) # type: ignore

    queue.add(task_name="sendWorkEmailTask", kwargs={"name": "Wisdom"}, mode="json")



asyncio.run(main())
