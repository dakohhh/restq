import os
import orjson
import base64
import pickle
import inspect
import asyncio
from uuid import uuid4
from .logger import logger
from anyio import to_thread
from datetime import datetime
from .types import QueueAddMode
from .task import Task, TaskRecord
from redis.asyncio import Redis as AsyncRedis
from multiprocessing import Process, freeze_support
from typing import Callable, Any, Optional
from .clients import get_redis_async_client

class Worker:
    def __init__(self, *, queue_name: str, url: str, tasks:list[Callable[...,  Task]], name: Optional[str] = None):
        freeze_support()

        self.name = f"worker-{uuid4().hex[:8]}" if not name else name
        self.queue_name = queue_name
        self.tasks = tasks
        self.group_name = f"workers:{self.queue_name}"
        self.task_map = { task().name : task() for task in self.tasks }
        self.url = url
        self.redis = get_redis_async_client(url=self.url, decode_responses=True)

    async def loop(self) -> None:
        await asyncio.gather(
            self.get_delayed_tasks(), 
            self.execute_tasks(), 
            self.cleanup_tasks_on_pel()
        )

    # TODO: Implement Concurrency (threads/multiprocessing)
    async def start(self, concurrency: int = 1) -> None:
        # Check if the stream (queue name) exists
        stream_exists = await self.redis.exists(self.queue_name)
        if not stream_exists:
            logger.info(f"Queue {self.queue_name} not found")
            await asyncio.sleep(0.5)
            logger.info(f"Creating queue {self.queue_name}...")
            await asyncio.sleep(0.5)
            await self.redis.xadd(self.queue_name, { "type": "init" })
            logger.info(f"Queue: {self.queue_name} created ✅")

        # Ensure that the group name exists
        groups = await self.redis.xinfo_groups(self.queue_name)

        if not any(g["name"] == self.group_name for g in groups):
            logger.info(f"Creating Group: {self.group_name} 😁")
            await self.redis.xgroup_create(
                name=self.queue_name,
                groupname=self.group_name,
                id="$",
                mkstream=True
            )

        # Start the worker loop
        await self.loop()

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
        
        # TODO: Add a warning here for pickle mode

        logger.warning("Detected pickle mode. Ensure input is trusted!")
        
        # Decode Base64 back to bytes
        pickle_bytes = base64.b64decode(kwargs)

        # Load original object from Pickle
        return pickle.loads(pickle_bytes)
    
    async def run_task(self, task_record: TaskRecord) -> Any:
        task = self.task_map.get(task_record.name)

        # logger.info("Task Record: ", task_record)
        logger.info("Task Record: %s", task_record)

        if not task:
            logger.warning(f"No registered task with the name '{task_record.name}' on queue '{self.queue_name}'")
            return

        if not task.max_retry:
            await self._run_task_func(task.func, task_record)

            if task_record.stream_id:

                # Acknowledge the stream
                await self.redis.xack(self.queue_name, self.group_name, task_record.stream_id)

            logger.info("Task Executed")
            return

        for attempt in range(task.max_retry):
            try:
                await self._run_task_func(task.func, task_record)

                if task_record.stream_id:

                    # Acknowledge the stream
                    await self.redis.xack(self.queue_name, self.group_name, task_record.stream_id)

                logger.info("Task Executed")
                break
            except Exception as e:
                logger.error("Exception caught:", e)
                if attempt < task.max_retry - 1:
                    logger.info(f"Retrying in {task.retry_delay} seconds....")
                    await asyncio.sleep(task.retry_delay)
                else:
                    logger.warning("Max retries reached. Task failed.")
            
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

                await to_thread.run_sync(func, **processed_kwargs)
    
            else:
                await to_thread.run_sync(func)

      
    async def execute_tasks(self) -> None:
        while True:
            logger.info("Waiting for new tasks..")
            response = await self.redis.xreadgroup(groupname=self.group_name, consumername=self.name, streams={ self.queue_name: ">" }, block=0)

            task_record = TaskRecord(**self.parse_task_response(response))

            logger.info(f"Task Record: {task_record}")

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
                    logger.warning("Delayed Task not found")
                    continue

                lock_key = f"delayed-task-lock-{delayed_id}"
                lock_value = str(uuid4())
                lock_expires = 60
            
                is_locked = await self.redis.set(name=lock_key, value=lock_value, nx=True, ex=lock_expires)

                if not is_locked:
                    logger.info("Lock already exists so we move to another item")
                    continue

                logger.info("Locked was created and now executing until released")

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

                task_record = TaskRecord(
                    stream_id=message[0],
                    id=message[1]["id"],
                    name=message[1]["name"],
                    kwargs=message[1]["kwargs"],
                    mode=message[1]["mode"]
                )
            
                logger.info("Cleanup Task Record: ", task_record)

                asyncio.create_task(self.run_task(task_record))

            if cursor == "0-0":
                await asyncio.sleep(1)


