# Worker API Reference

## Worker Class

### Constructor

```python
Worker(
    queue_name: str,
    url: str,
    tasks: list[Callable[..., Task]],
    name: Optional[str] = None
)
```

Creates a new worker instance.

**Parameters:**

- `queue_name` (str): Name of the queue to process
- `url` (str): Redis connection URL
- `tasks` (list): List of task handler functions
- `name` (str, optional): Worker identifier

**Example:**
```python
worker = Worker(
    queue_name="my-queue",
    url="redis://localhost:6379/0",
    tasks=[my_task, another_task],
    name="worker-1"
)
```

### Methods

#### start

```python
async start(concurrency: int = 1) -> None
```

Starts the worker and begins processing tasks.

**Parameters:**

- `concurrency` (int, optional): Number of concurrent tasks (default: 1)

**Example:**
```python
await worker.start(concurrency=1)
```

#### loop

```python
async loop() -> None
```

Internal method that runs the main worker loop.

## Task Decorator

### Constructor

```python
@task(
    name: str,
    max_retry: Optional[int] = None,
    retry_delay: Optional[int] = None
)
```

Decorator for defining task handlers.

**Parameters:**

- `name` (str): Unique task identifier
- `max_retry` (int, optional): Maximum retry attempts
- `retry_delay` (int, optional): Seconds between retries

**Example:**
```python
@task(
    name="process_data",
    max_retry=3,
    retry_delay=5
)
async def process_data(data: dict):
    # Task implementation
    pass
```

### Methods

#### func

```python
@property
func(self) -> Callable
```

Returns the task's handler function.

## TaskRecord Class

Internal class for task record management.

### Properties

- `id` (str): Unique task identifier
- `name` (str): Task name
- `kwargs` (Optional[str]): Serialized task arguments
- `delay` (Optional[Union[int, float]]): Execution delay
- `mode` (QueueAddMode): Serialization mode
- `stream_id` (Optional[str]): Redis stream ID

## Internal Methods

### run_task

```python
async run_task(task_record: TaskRecord) -> Any
```

Executes a task from its record.

### _run_task_func

```python
async _run_task_func(
    func: Callable[..., Any],
    task_record: TaskRecord
) -> None
```

Internal method for task function execution.

### execute_tasks

```python
async execute_tasks() -> None
```

Main task execution loop.


Processes delayed tasks.

### cleanup_tasks_on_pel

```python
async cleanup_tasks_on_pel() -> None
```

Handles pending task cleanup.
