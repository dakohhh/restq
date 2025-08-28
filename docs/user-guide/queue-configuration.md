# Queue Configuration

RestQ provides both synchronous and asynchronous queue implementations to suit different application needs.

## Queue Types

### Synchronous Queue

The standard `Queue` class is perfect for synchronous applications or scripts:

```python
from restq import Queue

queue = Queue(
    name="my-queue",
    url="redis://localhost:6379/0"
)
```

### Asynchronous Queue

The `AsyncQueue` class is designed for async applications:

```python
from restq import AsyncQueue

async_queue = AsyncQueue(
    name="my-queue",
    url="redis://localhost:6379/0"
)

# Usage in async context
await async_queue.add(
    task_name="my_task",
    kwargs={"key": "value"}
)
```

## Configuration Options

### Queue Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | str | Yes | Unique identifier for your queue |
| `url` | str | Yes | Redis connection URL |

### Redis URL Format

The Redis URL follows this format:
```
redis://[[username]:[password]]@localhost:6379/0
```

Components:
- `username`: Redis username (optional)
- `password`: Redis password (optional)
- `localhost`: Redis host
- `6379`: Redis port
- `0`: Database number

## Adding Tasks

The `add` method is your primary interface for enqueueing tasks:

```python
queue.add(
    task_name="my_task",           # Required: Name of the task
    kwargs={"key": "value"},       # Optional: Task arguments
    mode="json",                   # Optional: Serialization mode
    delay=None                     # Optional: Delay in seconds
)
```

### Task Addition Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `task_name` | str | Yes | - | Name of the task to execute |
| `kwargs` | dict | No | None | Task arguments |
| `mode` | str | No | "json" | Serialization mode ("json" or "pickle") |
| `delay` | int/float/timedelta | No | None | Delay before execution |

## Delayed Tasks

RestQ supports delayed task execution in multiple formats:

```python
# Delay by seconds
queue.add(task_name="my_task", delay=60)

# Delay using timedelta
from datetime import timedelta
queue.add(task_name="my_task", delay=timedelta(minutes=5))
```

## Best Practices

1. **Queue Naming**:
   - Use descriptive, unique names
   - Consider prefixing for different environments
   - Example: "prod-email-notifications"

2. **Redis Connection**:
   - Use connection pooling for production
   - Consider Redis cluster for high availability
   - Monitor Redis memory usage

3. **Task Arguments**:
   - Keep task data small and serializable
   - Use JSON mode when possible
   - Avoid sending large payloads

4. **Error Handling**:
   ```python
   try:
       queue.add(task_name="my_task", kwargs={"key": "value"})
   except Exception as e:
       logger.error(f"Failed to enqueue task: {e}")
   ```

## Example Configurations

### Basic Queue
```python
queue = Queue(
    name="simple-queue",
    url="redis://localhost:6379/0"
)
```

### Production Queue
```python
queue = Queue(
    name="prod-background-tasks",
    url="redis://user:pass@prod.redis:6379/0"
)
```

### Development Queue
```python
queue = Queue(
    name="dev-tasks",
    url="redis://localhost:6379/1"  # Using different database
)
