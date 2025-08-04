import time
from restq import Worker, task


async def get_redis_client(*args: Any, **kwargs: Any) -> AsyncRedis: # type: ignore
    redis = await redis_from_url(RESTQ_REDIS_URL, *args, **kwargs)

    return redis

@task(name="sendWorkEmailTask")
def send_work_email(name: str) -> None:
    print("Started something task")
    time.sleep(3)


async def get_redis_client(*args: Any, **kwargs: Any) -> AsyncRedis: # type: ignore
    redis = await redis_from_url(RESTQ_REDIS_URL, *args, **kwargs)

    return redis

worker = Worker(queue_name="email-queue", )