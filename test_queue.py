import asyncio
from restq import AsyncQueue

REDIS_URL = "redis://localhost:6379/0"

async def main() -> None:

    queue = AsyncQueue(name="your-unique-queue-name", url=REDIS_URL)

    await queue.add(task_name="MyTask", delay=30, kwargs={"foo": "bar"}, mode="pickle")

asyncio.run(main())

