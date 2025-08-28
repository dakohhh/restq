# RestQ

RestQ is a lightweight, and fully async task queue built on top of Redis. It provides a simple yet powerful way to handle task job processing in your Python applications. Think of it as your application's personal assistant that diligently processes tasks whenever you need them done (and Redis is up and running 😅).

I built this for 3 reasons:
1. For Fun 🤗
2. To finally land a job... by building a job queue 🎯
3. I needed a way to separate the task enqueueing process from the worker execution i.e workers can live anywhere, even in different projects/repos, and don’t need your app logic baked in.

## Installation

You can install RestQ using Poetry:

```bash
poetry add restq
```

Or using pip:

```bash
pip install restq
```

## Requirements

- Python >= 3.9
- Redis server

## Quick Start

Here's a simple example of how to use RestQ:


### Define the worker (worker.py)

```python
import asyncio
from restq import task, Worker

REDIS_URL = "redis://localhost:6379/0"

@task(name="MyTask")
async def handler(foo: str) -> None:
    print(f"Sending to ....{foo}")


async def main() -> None:
    worker = Worker(queue_name="your-unique-queue-name", url=REDIS_URL, tasks=[handler])

    await worker.start()


asyncio.run(main())
```


### Define the Queue (queue.py)

```python
from restq import Queue, Task

# Initialize the queue
REDIS_URL = "redis://localhost:6379/0"

queue = Queue(name="your-unique-queue-name", url=REDIS_URL)


# Enqueue a task
queue.add(task_name="MyTask", kwargs={"foo": "bar"}, mode="json")
```


## Advanced Usage

### Task Retries

```python
from restq import task

@task(max_retries=3, retry_delay=60)
def sensitive_operation():
    # Your code here
    pass
```

## Configuration

### Queue Configuration

The `Queue` class is the main entry point for adding tasks to your queue. It provides both synchronous and asynchronous implementations through `Queue` and `AsyncQueue` respectively.

```python
from restq import Queue, AsyncQueue

# Synchronous Queue
queue = Queue(
    name="your-queue-name",    # Unique name for your queue
    url="redis://localhost:6379/0"  # Redis connection URL
)

# Asynchronous Queue
async_queue = AsyncQueue(
    name="your-queue-name",
    url="redis://localhost:6379/0"
)
```

### Adding Tasks

The `add` method allows you to enqueue tasks with various options:

```python
# Basic task addition
queue.add(
    task_name="MyTask",           # Name of the task to execute
    kwargs={"key": "value"},      # Task arguments (optional)
    mode="json",                  # Serialization mode: "json" (default) or "pickle"
    delay=None                    # Delay execution (optional)
)

# Task with delay (seconds)
queue.add(
    task_name="DelayedTask",
    kwargs={"key": "value"},
    delay=60  # Task will execute after 60 seconds
)

# Task with timedelta delay
from datetime import timedelta

queue.add(
    task_name="DelayedTask",
    kwargs={"key": "value"},
    delay=timedelta(minutes=5)  # Task will execute after 5 minutes
)
```

### Why kwargs and JSON?

RestQ uses kwargs (keyword arguments) for task data and JSON serialization by default. Here's why:

#### Universal Communication
JSON works everywhere - Python, Node.js, Go, Rust, this means:
- Your Python app can queue tasks today
- Your Node.js service can queue and run tasks tomorrow
- Your Go microservice can queue and run tasks next week
- Workers would process them all the same way!

#### Javascript
``` javascript
await queue.add("process_order", { orderId: "123", amount: 99.99 })
```

#### Go
``` go
queue.Add("process_order", map[string]interface{}{"order_id": "123", "amount": 99.99})
```


#### Serialization Modes
- `json` (default): Uses orjson for fast JSON serialization. Best for most use cases and future language clients.
- `pickle`: Allows serialization of complex Python objects. Use with trusted input only, and only when you need Python-specific features.

### Worker Configuration

Workers are responsible for executing tasks from the queue. They can be configured with various options:

```python
from restq import Worker, task

# Define your task
@task(
    name="MyTask",           # Task name (required)
    max_retry=3,            # Maximum retry attempts (optional)
    retry_delay=5          # Delay between retries in seconds (optional)
)
async def my_task(key: str) -> None:
    print(f"Processing {key}")

# Initialize the worker
worker = Worker(
    queue_name="your-queue-name",    # Queue to listen to
    url="redis://localhost:6379/0",   # Redis connection URL
    tasks=[my_task],                  # List of task handlers
    name="worker-1"                   # Optional worker name
)

# Start the worker
await worker.start(concurrency=1)  # Number of concurrent tasks (default: 1)
```

#### Worker Features
- Automatic task retries with configurable delay
- Delayed task execution
- Task persistence through Redis streams
- Automatic recovery of pending tasks
- Distributed task processing across multiple workers

## Dependencies

- redis==5.3.1
- orjson==^3.11.1
- colorama==^0.4.6
- pydantic==^2.11.7
- anyio==^4.10.0

## Development

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/restq.git
cd restq

# Install dependencies
poetry install

```

## Future Features
- Task status monitoring
- Multi process handling

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

- dakohhh (wiizzydreadmill@gmail.com)

## Support

If you encounter any issues or have questions, please file an issue on the GitHub repository.

