from .task import Task
from functools import wraps
from typing import Callable, Any, Optional


# Decorator that creates a task from a function
def task(name: str, max_retry: Optional[int] = None, retry_delay: float = 1) -> Callable[[Callable[..., Any]], Callable[..., Task]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Task]:
        @wraps(func)
        def wrapper() -> Task:
            return Task(name=name, func=func, max_retry=max_retry,retry_delay=retry_delay)
        return wrapper
    return decorator
