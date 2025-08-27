from datetime import datetime
from .types import QueueAddMode
from typing import Callable, Any, Optional
from pydantic import BaseModel, Field, field_serializer


class Task(BaseModel):
    name: str = Field(description="A unique name given to the task")

    func: Callable[..., Any]

    max_retry: Optional[int]

    retry_delay: float = Field(default=1, description="The time (in seconds) delayed before a retry of task begins in seconds, defaults to 1 if not provided")


# TODO: Implementation of Repeated/Scheduled Task with Cron Expression
class RepeatedTask(Task):
    wait_first: Optional[float]


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
