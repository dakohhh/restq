# Worker Configuration

Workers are responsible for executing tasks from the queue. This guide covers worker configuration, task handling, and best practices.

## Basic Worker Setup

```python
from restq import Worker, task

@task(name="my_task")
async def my_task(arg1: str, arg2: int):
    # Task implementation
    pass

worker = Worker(
    queue_name="my-queue",
    url="redis://localhost:6379/0",
    tasks=[my_task],
    name="worker-1"  # Optional worker name
)

await worker.start()
```

## Task Definition

### Basic Task
```python
@task(name="simple_task")
async def simple_task(message: str):
    print(f"Processing: {message}")
```

### Task with Retries
```python
@task(
    name="reliable_task",
    max_retry=3,        # Maximum retry attempts
    retry_delay=5      # Seconds between retries
)
async def reliable_task(data: dict):
    # Implementation
    pass
```

## Worker Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `queue_name` | str | Yes | Queue to process tasks from |
| `url` | str | Yes | Redis connection URL |
| `tasks` | list | Yes | List of task handlers |
| `name` | str | No | Worker identifier |

## Task Decorator Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | str | Required | Unique task identifier |
| `max_retry` | int | None | Maximum retry attempts |
| `retry_delay` | int | 0 | Seconds between retries |

## Error Handling

### Task-Level Error Handling
```python
@task(name="handle_errors")
async def handle_errors(data: dict):
    try:
        result = await process_data(data)
    except ValueError as e:
        # Handle validation errors
        logger.error(f"Validation error: {e}")
        raise
    except ConnectionError as e:
        # Handle connection issues
        logger.error(f"Connection failed: {e}")
        raise
```

### Retry Behavior
```python
@task(
    name="retry_task",
    max_retry=3,
    retry_delay=5
)
async def retry_task(user_id: str):
    try:
        await external_service_call(user_id)
    except TemporaryError:
        # Will be retried automatically
        raise
    except PermanentError:
        # Won't be retried
        logger.error("Permanent failure")
        return
```

## Worker Lifecycle

### Starting Workers
```python
import asyncio
from restq import Worker

async def main():
    worker = Worker(
        queue_name="my-queue",
        url="redis://localhost:6379/0",
        tasks=[my_task]
    )
    
    await worker.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### Graceful Shutdown
The worker handles SIGINT and SIGTERM signals automatically, ensuring:
1. Current tasks complete
2. No new tasks are accepted
3. Resources are properly cleaned up

## Production Considerations

### Worker Naming
Use descriptive names to identify workers:

```python
worker = Worker(
    queue_name="email-queue",
    url=REDIS_URL,
    tasks=[send_email],
    name="email-worker-001"
)
```

## Deployment Strategies

### Single Worker
```python
worker = Worker(
    queue_name="main-queue",
    url=REDIS_URL,
    tasks=[task1, task2, task3]
)
```

### Multiple Workers
Run multiple worker processes for better throughput:

```bash
# worker1.py
worker = Worker(
    queue_name="main-queue",
    url=REDIS_URL,
    tasks=[task1, task2],
    name="worker-1"
)

# worker2.py
worker = Worker(
    queue_name="main-queue",
    url=REDIS_URL,
    tasks=[task1, task2],
    name="worker-2"
)
```

### Specialized Workers
Dedicate workers to specific task types:

```python
# email_worker.py
email_worker = Worker(
    queue_name="email-queue",
    url=REDIS_URL,
    tasks=[send_email],
    name="email-worker"
)

# processing_worker.py
processing_worker = Worker(
    queue_name="processing-queue",
    url=REDIS_URL,
    tasks=[process_data],
    name="processing-worker"
)
```
