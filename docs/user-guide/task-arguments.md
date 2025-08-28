# Task Arguments

RestQ uses a language-agnostic approach to task arguments, making it perfect for polyglot microservice architectures.

## Understanding kwargs

RestQ uses Python's keyword arguments (kwargs) pattern for task data, which is serialized to JSON by default. This design enables:

1. Cross-language compatibility
2. Type safety through serialization
3. Clear data structure

## Serialization Modes

### JSON Mode (Default)

JSON is the default and recommended serialization mode:

```python
queue.add(
    task_name="process_order",
    kwargs={
        "order_id": "123",
        "amount": 99.99,
        "items": ["item1", "item2"]
    },
    mode="json"  # This is default, so can be omitted
)
```

#### Supported Types in JSON Mode
- Strings
- Numbers (int, float)
- Booleans
- Lists
- Dictionaries
- Null
- Nested combinations of the above

### Pickle Mode

For Python-specific use cases requiring complex objects:

```python
from datetime import datetime

queue.add(
    task_name="process_data",
    kwargs={
        "timestamp": datetime.now(),
        "custom_object": MyCustomClass()
    },
    mode="pickle"
)
```

!!! warning "Security Note"
    Pickle mode should only be used with trusted data as it can execute arbitrary code during deserialization.

## Cross-Language Examples

### Python
```python
queue.add(
    task_name="process_order",
    kwargs={"order_id": "123", "amount": 99.99}
)
```

### JavaScript (Future)
```javascript
await queue.add("process_order", {
    orderId: "123",
    amount: 99.99
})
```

### Go (Future)
```go
queue.Add("process_order", map[string]interface{}{
    "order_id": "123",
    "amount": 99.99,
})
```

## Best Practices

### 1. Keep Data Simple
```python
# Good - Simple, flat structure
queue.add(
    task_name="send_email",
    kwargs={
        "to": "user@example.com",
        "subject": "Welcome",
        "template_id": "welcome_001"
    }
)

# Avoid - Complex nested structure
queue.add(
    task_name="send_email",
    kwargs={
        "user": {
            "contact": {
                "email": {
                    "address": "user@example.com"
                }
            }
        },
        "email": {
            "content": {
                "subject": "Welcome",
                "template": {
                    "id": "welcome_001"
                }
            }
        }
    }
)
```

### 2. Use Appropriate Types
```python
# Good - Using native types
queue.add(
    task_name="process_payment",
    kwargs={
        "amount": 99.99,           # float for currency
        "user_id": "usr_123",      # string for IDs
        "is_premium": True,        # boolean
        "items": [1, 2, 3]         # list
    }
)
```

### 3. Handle Large Data
For large datasets, consider passing references instead of raw data:

```python
# Bad - Sending large data directly
queue.add(
    task_name="process_image",
    kwargs={
        "image_data": large_binary_data  # Don't do this
    }
)

# Good - Sending reference to data
queue.add(
    task_name="process_image",
    kwargs={
        "image_url": "s3://bucket/image.jpg",
        "image_id": "img_123"
    }
)
```

### 4. Validation in Tasks
Always validate task arguments:

```python
@task(name="process_order")
async def process_order(order_id: str, amount: float):
    # Validate inputs
    if not isinstance(order_id, str):
        raise ValueError("order_id must be a string")
    if not isinstance(amount, (int, float)):
        raise ValueError("amount must be a number")
    if amount <= 0:
        raise ValueError("amount must be positive")
    
    # Process the order
    ...
```

## Common Patterns

### 1. Task Context
Pass necessary context with each task:

```python
queue.add(
    task_name="process_order",
    kwargs={
        "order_id": "123",
        "context": {
            "tenant_id": "t_123",
            "environment": "production",
            "trace_id": "trace_abc123"
        }
    }
)
```

### 2. Batch Operations
Group related items:

```python
queue.add(
    task_name="process_batch",
    kwargs={
        "batch_id": "batch_123",
        "items": [
            {"id": "1", "action": "process"},
            {"id": "2", "action": "validate"},
            {"id": "3", "action": "archive"}
        ]
    }
)
```
