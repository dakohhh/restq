import time
import orjson
import base64
import pickle
import os
import hashlib

from uuid import uuid4
import asyncio
from typing import Callable, Any, Optional, Coroutine, Literal, Union
from functools import wraps
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field
from redis.asyncio import Redis as AsyncRedis, from_url as redis_from_url

def get_file_absolute_hash() -> str:
    file_path = os.path.abspath(__file__)
    file_hash = hashlib.sha1(file_path.encode()).hexdigest()
    return file_hash

RESTQ_REDIS_URL = "redis://localhost:6379/0"

QueueAddMode = Literal["json", "pickle"]

class RestQException(Exception):
    """ Base exception for RestQ """

class Task(BaseModel):

    name: str = Field(description="A unique name given to the task")

    func: Callable[..., Any]

    max_retry: int

    retry_delay: Optional[int] = Field(description="The time delayed before a retry of task begins in seconds")


class TaskRecord(BaseModel):
    name: str

    delay: Optional[datetime] = None

    args: Optional[str] = None

    mode: QueueAddMode

    is_completed: bool




# Decorator that creates a task from a function
def task(name: str, max_retry: int = 3, retry_delay: Optional[int] = None) -> Callable[[Callable[..., Any]], Callable[..., Task]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Task]:
        @wraps(func)
        def wrapper() -> Task:
            return Task(name=name, func=func, max_retry=max_retry,retry_delay=retry_delay)
        return wrapper
    return decorator


@task(name="SomeTask1", max_retry=3, retry_delay=3)
def sleep_3_seconds() -> None:
    time.sleep(3)


@task(name="SomeTask2", max_retry=3, retry_delay=3)
def sleep_4_seconds() -> None:
    time.sleep(3)


@task(name="SomeTask3", max_retry=3, retry_delay=3)
def sleep_5_seconds() -> None:
    time.sleep(3)


class Queue:
    def __init__(self, name: str, redis: AsyncRedis):# type: ignore
        self.name = name
        self.redis = redis

    async def add(self, *, task_name: str, args: Optional[dict[str, Any]] = None, mode: QueueAddMode = "json", delay: Optional[Union[int, float, timedelta]] = None) -> None:
        
        delayed_datetime: Optional[datetime] = None
        if delay:
            if isinstance(delay, (float, int, )):

                delayed_datetime = datetime.now(timezone.utc) + timedelta(seconds=delay)
            elif isinstance(delay, timedelta):

                delayed_datetime = datetime.now(timezone.utc) + delay
            else:
                raise RestQException("Invalid type for delay, must be int, float or timedelta")
        
        processed_args = None
        if args:
            if mode == "pickle":
                pickle_bytes = pickle.dumps(args)

                processed_args = base64.b64encode(pickle_bytes).decode("utf-8")
            else:
                # Default mode uses JSON for Task Arguments
                processed_args = orjson.dumps(args).decode("utf-8")
        
        task_record = TaskRecord(name=task_name, delay=delayed_datetime, args=processed_args, mode=mode, is_completed=False)

        print(task_record)
        print(task_record)
        print(task_record)
        # publish the task for the workers
        await self.redis.xadd(self.name, task_record.model_dump())


class Worker:
    def __init__(self, *, queue_name: str, redis: AsyncRedis, tasks:list[Callable[...,  Task]], name: Optional[str] = None): # type: ignore
        self.name = f"worker-{uuid4().hex[:8]}"
        self.queue_name = queue_name
        self.tasks = tasks
        self.redis = redis

    async def start(self) -> None:
        group_info = await self.redis.xinfo_groups(name=self.queue_name) # type: ignore

        group_exists  = False
        for info in group_info:
            if info["name"] == self.queue_name:
                group_exists = True
                break

        if not group_exists:
            await self.redis.xgroup_create(name=self.queue_name, groupname=f"workers:{self.queue_name}", id="$")
    
        while True:
            print("Waiting for new tasks..")
            response = await self.redis.xreadgroup(groupname=f"workers:{self.queue_name}", consumername=self.name, streams={ self.queue_name: ">" }, block=0)

            print(response)


async def get_redis_client(*args: Any, **kwargs: Any) -> AsyncRedis: # type: ignore
    redis = await redis_from_url(RESTQ_REDIS_URL, *args, **kwargs)

    return redis



async def main() -> None:
    redis = await get_redis_client(decode_responses=True)

    queue = Queue("SleepQueue", redis=redis)

    worker = Worker(queue_name="SleepQueue", redis=redis, tasks=[sleep_3_seconds, sleep_4_seconds, sleep_5_seconds])

    await queue.add(task_name="SomeTask1")


asyncio.run(main())

