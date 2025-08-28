# Quick Start Guide

This guide will help you get up and running with RestQ in minutes. We'll create a simple task processing system.

## Basic Setup

First, let's create a simple project structure:

```
your_project/
├── worker.py
└── publisher.py
```

## Define a Task

In `worker.py`, let's create a simple task that processes orders:

```python
import asyncio
from restq import task, Worker

REDIS_URL = "redis://localhost:6379/0"

@task(
    name="process_order",
    max_retry=3,        # Retry up to 3 times
    retry_delay=5       # Wait 5 seconds between retries
)
async def process_order(order_id: str, amount: float) -> None:
    print(f"Processing order {order_id} for ${amount}")
    # Your order processing logic here
    await asyncio.sleep(1)  # Simulate some work
    print(f"Order {order_id} processed successfully!")

async def main() -> None:
    # Initialize the worker
    worker = Worker(
        queue_name="orders",
        url=REDIS_URL,
        tasks=[process_order]
    )

    # Start processing tasks
    await worker.start()

if __name__ == "__main__":
    asyncio.run(main())
```

## Queue Tasks

In `publisher.py`, let's add some tasks to the queue:

```python
from restq import Queue

# Initialize the queue
queue = Queue(
    name="orders",
    url="redis://localhost:6379/0"
)

# Add immediate tasks
queue.add(
    task_name="process_order",
    kwargs={
        "order_id": "ORD-001",
        "amount": 99.99
    }
)

# Add delayed task (runs after 60 seconds)
queue.add(
    task_name="process_order",
    kwargs={
        "order_id": "ORD-002",
        "amount": 149.99
    },
    delay=60
)
```

## Run the System

1. Start the worker:
```bash
python worker.py
```

2. In another terminal, run the publisher:
```bash
python publisher.py
```

You should see the worker processing the tasks!

## What's Happening?

1. The worker starts and connects to Redis
2. It waits for tasks on the "orders" queue
3. The publisher adds tasks to the queue
4. Worker picks up tasks and executes them
5. If a task fails, it's automatically retried

## Next Steps

Now that you have a basic system working, explore:

1. [Queue Configuration](../user-guide/queue-configuration.md) - Learn about queue options
2. [Task Arguments](../user-guide/task-arguments.md) - Understanding task data handling
3. [Worker Configuration](../user-guide/worker-configuration.md) - Configure workers for production
4. [Advanced Usage](../user-guide/advanced-usage.md) - Explore advanced features
