import asyncio
import time
from typing import Any
from restq import Worker, task
from redis.asyncio import Redis as AsyncRedis, from_url as redis_from_url


REDIS_URL = "redis://localhost:6379/0"

# async def get_redis_client(*args: Any, **kwargs: Any) -> AsyncRedis: # type: ignore
#     redis = await redis_from_url(REDIS_URL, *args, **kwargs)

#     return redis

@task(name="sendWorkEmailTask")
async def send_work_email(name: str) -> None:
    print("Started something task async")
    print(f"Sending.... work email to {name}")
    print("Done")



async def main() -> None:
    # redis = await get_redis_client(decode_responses=True)

    worker = Worker(queue_name="email-queue", url=REDIS_URL, tasks=[send_work_email])

    await worker.start()


asyncio.run(main())

