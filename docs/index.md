# Welcome to RestQ

RestQ is a lightweight, and fully async task queue built on top of Redis. It provides a simple yet powerful way to handle task job processing in your Python applications. Think of it as your application's personal assistant that diligently processes tasks whenever you need them done.

## Why RestQ?

RestQ was created with three core principles in mind:

1. **Simplicity First**: Built for developers who want to focus on writing code, not managing infrastructure.
2. **Language Agnostic**: Designed to work seamlessly across different programming languages and environments.
3. **Distributed by Design**: Task scheduling and worker execution are completely decoupled, allowing for flexible deployment patterns.

## Key Features

- 🚀 **Fully Async**: Built for modern Python applications with asyncio at its core
- 🔄 **Redis Streams**: Reliable task persistence and distribution
- 💪 **Language Agnostic**: JSON-first approach enables cross-language compatibility
- ⚡ **High Performance**: Optimized for throughput with minimal overhead
- 🔌 **Easy Integration**: Simple API that gets out of your way
- 🎯 **Automatic Retries**: Built-in retry mechanisms with configurable backoff
- 🛡️ **Error Handling**: Robust error handling and task recovery
- ⏰ **Delayed Tasks**: Schedule tasks for future execution

## Quick Example

```python
from restq import Queue, task

# Define your task
@task(name="send_email")
async def send_email(to: str, subject: str):
    # Your email sending logic here
    print(f"Sending email to {to}: {subject}")

# Initialize the queue
queue = Queue(name="email-queue", url="redis://localhost:6379/0")

# Add a task
queue.add(
    task_name="send_email",
    kwargs={
        "to": "user@example.com",
        "subject": "Welcome!"
    }
)
```

## Cross-Language Support

RestQ is designed to be language-agnostic. Here's how task enqueueing looks in different languages:

=== "Python"
    ```python
    queue.add("process_order", kwargs={"order_id": "123", "amount": 99.99})
    ```

=== "JavaScript (Coming Soon)"
    ```javascript
    await queue.add("process_order", { orderId: "123", amount: 99.99 })
    ```

=== "Go (Coming Soon)"
    ```go
    queue.Add("process_order", map[string]interface{}{
        "order_id": "123",
        "amount": 99.99,
    })
    ```

## Getting Started

Check out our [Quick Start Guide](getting-started/quickstart.md) to begin using RestQ in your projects.
