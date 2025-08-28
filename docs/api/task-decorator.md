# Task Decorator API Reference

## Overview

The `@task` decorator is used to define task handlers in RestQ. It provides configuration options for task execution and retry behavior.

## Basic Usage

```python
from restq import task

@task(name="my_task")
async def my_task(arg1: str, arg2: int):
    # Task implementation
    pass
```

## Constructor

```python
@task(
    name: str,
    max_retry: Optional[int] = None,
    retry_delay: Optional[int] = None
)
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | str | Yes | - | Unique task identifier |
| `max_retry` | int | No | None | Maximum retry attempts |
| `retry_delay` | int | No | None | Seconds between retries |

## Examples

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
    max_retry=3,
    retry_delay=5
)
async def reliable_task(data: dict):
    try:
        await process_data(data)
    except TemporaryError:
        # Will be retried up to 3 times
        raise
```

### Synchronous Task
```python
@task(name="sync_task")
def sync_task(data: dict):
    # Synchronous implementation
    process_data(data)
```

## Task Handler Requirements

### Function Signature
- Can be async or sync
- Must accept kwargs defined in task call
- Return value is ignored

### Error Handling
- Unhandled exceptions trigger retry mechanism
- After max retries, task is marked as failed

## Best Practices

### 1. Unique Names
```python
# Good - Clear, unique names
@task(name="send_welcome_email")
async def send_welcome_email(user_id: str):
    pass

@task(name="send_password_reset")
async def send_password_reset(user_id: str):
    pass

# Bad - Generic, potentially conflicting names
@task(name="send_email")
async def send_welcome(user_id: str):
    pass

@task(name="send_email")  # Name conflict!
async def send_reset(user_id: str):
    pass
```

### 2. Type Hints
```python
@task(name="process_user")
async def process_user(
    user_id: str,
    update_data: dict[str, Any],
    notify: bool = False
) -> None:
    # Implementation with clear type hints
    pass
```

### 3. Documentation
```python
@task(name="process_payment")
async def process_payment(
    amount: Decimal,
    currency: str,
    user_id: str
) -> None:
    """Process a payment transaction.
    
    Args:
        amount: Transaction amount
        currency: Three-letter currency code
        user_id: User identifier
    
    Raises:
        PaymentError: If payment processing fails
        ValidationError: If input data is invalid
    """
    pass
```

### 4. Retry Configuration
```python
# Short-lived task, no retries needed
@task(name="cache_data")
async def cache_data(key: str, value: Any):
    pass

# Network operation, retry with backoff
@task(
    name="external_api_call",
    max_retry=3,
    retry_delay=5
)
async def external_api_call(endpoint: str, data: dict):
    pass
```

## Advanced Usage

### Custom Error Handling
```python
@task(
    name="handle_errors",
    max_retry=3,
    retry_delay=5
)
async def handle_errors(data: dict):
    try:
        await process_data(data)
    except TemporaryError:
        # Will be retried
        raise
    except PermanentError:
        # Log error but don't retry
        logger.error("Permanent error occurred")
        return
    except Exception as e:
        # Unexpected error
        logger.critical(f"Unexpected error: {e}")
        raise
```

### Resource Management
```python
@task(name="db_operation")
async def db_operation(query: str, params: dict):
    async with get_db_connection() as conn:
        async with conn.transaction():
            return await conn.execute(query, **params)
```

### Task Context
```python
@task(name="contextual_task")
async def contextual_task(
    data: dict,
    context: dict[str, Any]
):
    logger.info(
        "Processing task",
        extra={
            "task_id": context.get("task_id"),
            "trace_id": context.get("trace_id")
        }
    )
    # Implementation
    pass
```
