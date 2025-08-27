import asyncio
from restq import AsyncQueue

REDIS_URL = "redis://localhost:6379/0"

async def main() -> None:

    queue = AsyncQueue(name="your-unique-queue-name", url=REDIS_URL)

    await queue.add(task_name="MyTask", kwargs={"foo": "bar"}, mode="json")

asyncio.run(main())

