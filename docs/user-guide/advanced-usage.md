# Advanced Usage

This guide covers advanced features and patterns for getting the most out of RestQ.

## Delayed Task Execution

### Using Seconds
```python
# Execute after 60 seconds
queue.add(
    task_name="delayed_task",
    kwargs={"key": "value"},
    delay=60
)
```

### Using timedelta
```python
from datetime import timedelta

# Execute after 1 hour
queue.add(
    task_name="delayed_task",
    kwargs={"key": "value"},
    delay=timedelta(hours=1)
)
```