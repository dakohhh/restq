# Queue API Reference

## Queue Class

### Constructor

```python
Queue(name: str, url: str)
```

Creates a new synchronous queue instance.

**Parameters:**

- `name` (str): Unique identifier for the queue
- `url` (str): Redis connection URL

**Example:**
```python
queue = Queue(
    name="my-queue",
    url="redis://localhost:6379/0"
)
```

### Methods

#### add

```python
add(
    task_name: str,
    kwargs: Optional[dict[str, Any]] = None,
    mode: QueueAddMode = "json",
    delay: Optional[Union[int, float, timedelta]] = None
) -> None
```

Adds a task to the queue.

**Parameters:**

- `task_name` (str): Name of the task to execute
- `kwargs` (dict, optional): Task arguments
- `mode` (str, optional): Serialization mode ("json" or "pickle")
- `delay` (int/float/timedelta, optional): Delay before execution

**Example:**
```python
# Basic usage
queue.add("my_task", kwargs={"key": "value"})

# With delay
queue.add("delayed_task", kwargs={"key": "value"}, delay=60)

# With pickle mode
queue.add("complex_task", kwargs={"obj": my_object}, mode="pickle")
```

## AsyncQueue Class

### Constructor

```python
AsyncQueue(name: str, url: str)
```

Creates a new asynchronous queue instance.

**Parameters:**

- `name` (str): Unique identifier for the queue
- `url` (str): Redis connection URL

**Example:**
```python
async_queue = AsyncQueue(
    name="my-async-queue",
    url="redis://localhost:6379/0"
)
```

### Methods

#### add

```python
async add(
    task_name: str,
    kwargs: Optional[dict[str, Any]] = None,
    mode: QueueAddMode = "json",
    delay: Optional[Union[int, float, timedelta]] = None
) -> None
```

Asynchronously adds a task to the queue.

**Parameters:**

- `task_name` (str): Name of the task to execute
- `kwargs` (dict, optional): Task arguments
- `mode` (str, optional): Serialization mode ("json" or "pickle")
- `delay` (int/float/timedelta, optional): Delay before execution

**Example:**
```python
# Basic usage
await async_queue.add("my_task", kwargs={"key": "value"})

# With delay
await async_queue.add(
    "delayed_task",
    kwargs={"key": "value"},
    delay=timedelta(minutes=5)
)
```

## Types

### QueueAddMode

```python
QueueAddMode = Literal["json", "pickle"]
```

Defines the serialization mode for task arguments.

- `"json"`: Default mode, uses orjson for serialization
- `"pickle"`: For Python-specific complex objects

## Exceptions

### RestQException

Base exception class for RestQ-related errors.

```python
try:
    queue.add("my_task", kwargs={"key": "value"})
except RestQException as e:
    print(f"Queue error: {e}")
```
