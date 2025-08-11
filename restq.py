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
from pydantic import BaseModel, Field, field_serializer
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
    id: str

    name: str

    delay: Optional[datetime] = None

    kwargs: Optional[str] = None

    mode: QueueAddMode

    @field_serializer('delay')
    def serialize_delay(self, delay: datetime) -> str:
        return str(delay)

    

# Decorator that creates a task from a function
def task(name: str, max_retry: int = 3, retry_delay: Optional[int] = None) -> Callable[[Callable[..., Any]], Callable[..., Task]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Task]:
        @wraps(func)
        def wrapper() -> Task:
            return Task(name=name, func=func, max_retry=max_retry,retry_delay=retry_delay)
        return wrapper
    return decorator



class Queue:
    def __init__(self, name: str, redis: AsyncRedis):# type: ignore
        self.name = name
        self.redis = redis

    async def add(self, *, task_name: str, kwargs: Optional[dict[str, Any]] = None, mode: QueueAddMode = "json", delay: Optional[Union[int, float, timedelta]] = None) -> None:
        
        processed_kwargs = None
        if kwargs:
            if mode == "pickle":
                pickle_bytes = pickle.dumps(kwargs)

                processed_kwargs = base64.b64encode(pickle_bytes).decode("utf-8")
            else:
                # Default mode uses JSON for Task Arguments
                processed_kwargs = orjson.dumps(kwargs).decode("utf-8")
        
        if not delay:
            # Publish the Task immediately for the workers
            task_record = TaskRecord(id=str(uuid4()), name=task_name, delay=None, kwargs=processed_kwargs, mode=mode)
            await self.redis.xadd(name=self.name, fields=task_record.model_dump(exclude_none=True))
        else:
            # Add it to a sorted redis set with the timestamp as the score
            if isinstance(delay, (float, int, )):

                delayed_datetime = datetime.now(timezone.utc) + timedelta(seconds=delay)
            elif isinstance(delay, timedelta):

                delayed_datetime = datetime.now(timezone.utc) + delay
            else:
                raise RestQException("Invalid type for delay, must be int, float or timedelta")
    
            task_record = TaskRecord(id=str(uuid4()), name=task_name, delay=None, kwargs=processed_kwargs, mode=mode)
            # Create a reference key value map
            delayed_task_id = f"delayed-task-{task_record.id}"

            await self.redis.set(delayed_task_id, value=task_record.model_dump_json(exclude_none=True))
    
            await self.redis.zadd(f"{self.name}-delayed", mapping={delayed_task_id: delayed_datetime.timestamp()})

class Worker:
    def __init__(self, *, queue_name: str, redis: AsyncRedis, tasks:list[Callable[...,  Task]], name: Optional[str] = None): # type: ignore
        self.name = f"worker-{uuid4().hex[:8]}"
        self.queue_name = queue_name
        self.tasks = tasks
        self.redis = redis
        self.group_name = f"workers:{self.queue_name}"
        self.task_map = { task().name : task() for task in self.tasks }

    async def start(self) -> None:
        # Start sub-worker for delayed task
    
        # Check if the stream (queue name) exists
        stream_exists = await self.redis.exists(self.queue_name)
        if not stream_exists:
            print(f"Queue {self.queue_name} not found")
            await asyncio.sleep(0.5)
            print(f"Creating queue {self.queue_name}...")
            await asyncio.sleep(0.5)
            await self.redis.xadd(self.queue_name, { "type": "init" })
            print(f"Queue: {self.queue_name} created ✅")

        # Ensure that the group name exists
        groups = await self.redis.xinfo_groups(self.queue_name) # type: ignore
        if not any(g["name"] == self.group_name for g in groups):
            print(f"Creating Group: {self.group_name} 😁")
            await self.redis.xgroup_create(
                name=self.queue_name,
                groupname=self.group_name,
                id="$",
                mkstream=True
            )
            
        await asyncio.gather(self.get_delayed_tasks(), self.execute_tasks())


    def parse_task_response(self, response: Any) -> dict[str, Any]:
        if not response or not response[0][1]:
            return {}

        message_id, data = response[0][1][0]

        return {
            "id": message_id,
            "name": data.get("name"),
            "kwargs": data.get("kwargs"),
            "delay": data.get("delay"),
            "mode": data.get("mode"),
        }



    def deserialize_kwargs(self, kwargs: str, mode: QueueAddMode) -> Any:
        if mode == "json":
            return orjson.loads(kwargs)
        
        # Decode Base64 back to bytes
        pickle_bytes = base64.b64decode(kwargs)
        print(pickle_bytes)
        # Load original object from Pickle
        return pickle.loads(pickle_bytes)
    

    async def run_task(self, task_record: TaskRecord) -> Any:

        task = self.task_map.get(task_record.name)

        if task:
            if task_record.kwargs:
                processed_kwargs = self.deserialize_kwargs(kwargs=task_record.kwargs, mode=task_record.mode)
                task.func(**processed_kwargs)
            else:
                task.func()
                print("Task Executed")
        else:
            print(f"No registered task with the name '{task_record.name}' on queue '{self.queue_name}'")

    async def execute_tasks(self) -> None:
        while True:
            print("Waiting for new tasks..")
            response = await self.redis.xreadgroup(groupname=self.group_name, consumername=self.name, streams={ self.queue_name: ">" }, block=0)

            task_record = TaskRecord(**self.parse_task_response(response))

            asyncio.create_task(self.run_task(task_record))


    async def get_delayed_tasks(self) -> None:
        while True:
            sorted_set_name = f"{self.queue_name}-delayed"

            # Get the item from the sorted set with the least score
            lowest = await self.redis.zrange(sorted_set_name, 0, 0, withscores=True)

            if lowest:
                delayed_id, timestamp = lowest[0]

                # Get the Delayed task from redis
                value = await self.redis.get(name=delayed_id)

                if value:
                    lock_key = f"delayed-task-lock-{delayed_id}"
                    lock_value = str(uuid4())
                    lock_expires = 60
                
                    is_locked = await self.redis.set(name=lock_key, value=lock_value, nx=True, ex=lock_expires)

                    if is_locked:
                        print("Locked was created and now exucting until released")
                        # We would delay execution till the timestamp the least task is reached
                        delayed_seconds = timestamp - datetime.now().timestamp()

                        if delayed_seconds > 0:
                            print(f"We delaying y'all for {int(delayed_seconds)} seconds")
                            await asyncio.sleep(delayed_seconds)

                        # Publish the Task immediately for the workers
                        await self.redis.xadd(name=self.queue_name, fields=orjson.loads(value))

                        # Remove from the sorted set
                        await self.redis.zrem(sorted_set_name, delayed_id)

                        # Remove delayed task record
                        await self.redis.delete(delayed_id)

                        # Release the lock if we still own it

                        release_lock_value = await self.redis.get(lock_key)

                        if release_lock_value == lock_value:
                            await self.redis.delete(release_lock_value)

                    else:
                        print("Lock already exists so we move to another item")
                        await asyncio.sleep(1)

                else:
                    print("Delayed Task not found")
            else:
                # print("Sleeping delay worker for 5 seconds...")
                await asyncio.sleep(5)


        


async def get_redis_client(*args: Any, **kwargs: Any) -> AsyncRedis: # type: ignore
    redis = await redis_from_url(RESTQ_REDIS_URL, *args, **kwargs)

    return redis

