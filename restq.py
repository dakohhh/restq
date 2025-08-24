import orjson
import base64
import pickle
import os
import hashlib
import inspect
from uuid import uuid4
import asyncio
from typing import Callable, Any, Optional, Coroutine, Literal, Union
from functools import wraps
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field, field_serializer
from redis import Redis, from_url as sync_redis_from_url
from redis.asyncio import Redis as AsyncRedis, from_url as async_redis_from_url

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

    max_retry: Optional[int]

    retry_delay: float = Field(default=1, description="The time (in seconds) delayed before a retry of task begins in seconds, defaults to 1 if not provided")


class TaskRecord(BaseModel):
    id: str

    stream_id: Optional[str] = None

    name: str

    delay: Optional[datetime] = None

    kwargs: Optional[str] = None

    mode: QueueAddMode

    @field_serializer('delay')
    def serialize_delay(self, delay: datetime) -> str:
        return str(delay)



def get_redis_async_client(url: str, *args: Any, **kwargs: Any) -> AsyncRedis:
    redis = async_redis_from_url(url, *args, **kwargs) # type: ignore

    return redis #type: ignore

def get_redis_sync_client(url: str, *args: Any, **kwargs: Any) -> Redis:
    redis = sync_redis_from_url(url, *args, **kwargs) # type: ignore

    return redis #type: ignore
    

# Decorator that creates a task from a function
def task(name: str, max_retry: Optional[int] = None, retry_delay: float = 1) -> Callable[[Callable[..., Any]], Callable[..., Task]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Task]:
        @wraps(func)
        def wrapper() -> Task:
            return Task(name=name, func=func, max_retry=max_retry,retry_delay=retry_delay)
        return wrapper
    return decorator



class AsyncQueue:
    def __init__(self, name: str, url: Optional[str] = None, redis: Optional[AsyncRedis] = None):
        self.name = name

        if not url and not redis:
            raise RestQException("Redis url or Client is required")

        if url:
            self.redis = get_redis_async_client(url=url, decode_responses=True)
        
        if redis:
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
            await self.redis.xadd(name=self.name, fields=task_record.model_dump(exclude_none=True)) # type: ignore
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


class Queue:
    def __init__(self, name: str, url: Optional[str] = None, redis: Optional[Redis] = None):
        self.name = name

        if not url and not redis:
            raise RestQException("Redis url or Client is required")

        if url:
            self.redis = get_redis_sync_client(url=url, decode_responses=True)
        
        if redis:
            self.redis = redis
    
    def add(self, *, task_name: str, kwargs: Optional[dict[str, Any]] = None, mode: QueueAddMode = "json", delay: Optional[Union[int, float, timedelta]] = None) -> None:
        
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
            self.redis.xadd(name=self.name, fields=task_record.model_dump(exclude_none=True)) # type: ignore
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

            self.redis.set(delayed_task_id, value=task_record.model_dump_json(exclude_none=True))
    
            self.redis.zadd(f"{self.name}-delayed", mapping={delayed_task_id: delayed_datetime.timestamp()})


class Worker:
    def __init__(self, *, queue_name: str, url: Optional[str] = None, redis: Optional[AsyncRedis] = None, tasks:list[Callable[...,  Task]], name: Optional[str] = None):
        self.name = f"worker-{uuid4().hex[:8]}" if not name else name
        self.queue_name = queue_name
        self.tasks = tasks
        self.group_name = f"workers:{self.queue_name}"
        self.task_map = { task().name : task() for task in self.tasks }


        if not url and not redis:
            raise RestQException("Redis url or Client is required")

        if url:
            self.redis = get_redis_async_client(url=url, decode_responses=True)
        
        if redis:
            self.redis = redis

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
        groups = await self.redis.xinfo_groups(self.queue_name)

        if not any(g["name"] == self.group_name for g in groups):
            print(f"Creating Group: {self.group_name} 😁")
            await self.redis.xgroup_create(
                name=self.queue_name,
                groupname=self.group_name,
                id="$",
                mkstream=True
            )
            
        await asyncio.gather(self.get_delayed_tasks(), self.execute_tasks(), self.cleanup_tasks_on_pel())


    def parse_task_response(self, response: Any) -> dict[str, Any]:
        if not response or not response[0][1]:
            return {}
        

        message_id, data = response[0][1][0]

        return {
            "stream_id": message_id,
            "id": data.get("id"),
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

        print("Task Record: ", task_record)

        if not task:
            print(f"No registered task with the name '{task_record.name}' on queue '{self.queue_name}'")
            return

        if not task.max_retry:
            await self._run_task_func(task.func, task_record)

            if task_record.stream_id:

                # Acknowledge the stream
                await self.redis.xack(self.queue_name, self.group_name, task_record.stream_id)

            print("Task Executed")
            return

        for attempt in range(task.max_retry):
            try:
                await self._run_task_func(task.func, task_record)

                if task_record.stream_id:

                    # Acknowledge the stream
                    await self.redis.xack(self.queue_name, self.group_name, task_record.stream_id)

                print("Task Executed")
                break
            except Exception as e:
                print("Exception caught:", e)
                if attempt < task.max_retry - 1:
                    print(f"Retrying in {task.retry_delay} seconds....")
                    await asyncio.sleep(task.retry_delay)
                else:
                    print("Max retries reached. Task failed.")
            
    async def _run_task_func(self, func: Callable[..., Any], task_record: TaskRecord) -> None:
        if inspect.iscoroutinefunction(func):
            if task_record.kwargs:
                processed_kwargs = self.deserialize_kwargs(
                    kwargs=task_record.kwargs, mode=task_record.mode
                )
                await func(**processed_kwargs)
            else:
                await func()
        else:
            if task_record.kwargs:
                processed_kwargs = self.deserialize_kwargs(
                    kwargs=task_record.kwargs, mode=task_record.mode
                )
                func(**processed_kwargs)
            else:
                func()

      
    async def execute_tasks(self) -> None:
        while True:
            print("Waiting for new tasks..")
            response = await self.redis.xreadgroup(groupname=self.group_name, consumername=self.name, streams={ self.queue_name: ">" }, block=0)

            task_record = TaskRecord(**self.parse_task_response(response))

            print("Task Record: ", task_record)

            asyncio.create_task(self.run_task(task_record))


    async def get_delayed_tasks(self) -> None:
        while True:
            sorted_set_name = f"{self.queue_name}-delayed"

            # Get the task from the sorted set with the least score (earliest timestamp)
            tasks = await self.redis.zrange(sorted_set_name, 0, -1, withscores=True)

            if not tasks:
                await asyncio.sleep(5)

            earliest_delayed_future_time = None

            for delayed_id, timestamp in tasks:

                # Get the Delayed task from redis
                value = await self.redis.get(name=delayed_id)

                if not value:
                    print("Delayed Task not found")
                    continue

                lock_key = f"delayed-task-lock-{delayed_id}"
                lock_value = str(uuid4())
                lock_expires = 60
            
                is_locked = await self.redis.set(name=lock_key, value=lock_value, nx=True, ex=lock_expires)

                if not is_locked:
                    print("Lock already exists so we move to another item")
                    continue

                print("Locked was created and now executing until released")

                # We would delay execution till the timestamp the least task is reached
                delayed_seconds = timestamp - datetime.now().timestamp()

                if delayed_seconds > 0:
                    if earliest_delayed_future_time is None or delayed_seconds < earliest_delayed_future_time:
                        earliest_delayed_future_time = delayed_seconds

                    # Release the lock if we still own it
                    release_lock_value = await self.redis.get(lock_key)

                    if release_lock_value == lock_value:
                        await self.redis.delete(lock_key)
                    continue
                
                # Publish the Task immediately for the workers
                await self.redis.xadd(name=self.queue_name, fields=orjson.loads(value))

                # Remove from the sorted set
                await self.redis.zrem(sorted_set_name, delayed_id)

                # Remove delayed task record
                await self.redis.delete(delayed_id)


                # Release the lock if we still own it
                release_lock_value = await self.redis.get(lock_key)

                if release_lock_value == lock_value:
                    await self.redis.delete(lock_key)

            if earliest_delayed_future_time is not None:
                # Sleep until the earliest task comes in
                await asyncio.sleep(earliest_delayed_future_time)

    # Automatically claim all pending tasks that wasn't pushed to the consumer group
    async def cleanup_tasks_on_pel(self) -> None:
        cursor = "0-0"
        min_idle_time = 60000
        count = 10
    
        while True:

            cursor, messages, deleted = await self.redis.xautoclaim(
                name=self.queue_name,
                groupname=self.group_name,
                min_idle_time=min_idle_time,
                consumername=self.name,
                start_id=cursor,
                count=count
            )

            if not messages:
                await asyncio.sleep(1)
                continue

            for message in messages:


                print(message)
                print(message)
                print(message)

                task_record = TaskRecord(
                    stream_id=message[0],
                    id=message[1]["id"],
                    name=message[1]["name"],
                    kwargs=message[1]["kwargs"],
                    mode=message[1]["mode"]
                )
                print("Cleanup Task Record: ", task_record)

                asyncio.create_task(self.run_task(task_record))

            if cursor == "0-0":
                # print("No more task in PEL")
                await asyncio.sleep(1)