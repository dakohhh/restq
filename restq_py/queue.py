import orjson
import base64
import pickle
from uuid import uuid4
from .logger import logger
from .task import TaskRecord
from .types import QueueAddMode
from .exceptions import RestQException
from typing import Any, Optional, Union
from datetime import datetime, timedelta, timezone
from .clients import get_redis_async_client, get_redis_sync_client


class AsyncQueue:
    def __init__(self, name: str, url: str):
        self.name = name

        self.redis = get_redis_async_client(url=url, decode_responses=True)

    async def add(self, *, task_name: str, kwargs: Optional[dict[str, Any]] = None, mode: QueueAddMode = "json", delay: Optional[Union[int, float, timedelta]] = None) -> None:
        processed_kwargs = None
        if kwargs:
            if mode == "pickle":
                logger.warning("Queue '%s' used pickle mode. Ensure input is trusted!", self.name)

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
    def __init__(self, name: str, url: str):
        self.name = name

        self.redis = get_redis_sync_client(url=url, decode_responses=True)
    
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
