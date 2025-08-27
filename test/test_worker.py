import asyncio
from restq import task, Worker
from multiprocessing import freeze_support


REDIS_URL = "redis://localhost:6379/0"


@task(name="MyTask")
async def handler(foo: str) -> None:
    print(f"Sending to ....{foo}")


async def main() -> None:
    worker = Worker(queue_name="your-unique-queue-name", url=REDIS_URL, tasks=[handler])

    await worker.start(concurrency=5)


asyncio.run(main())

