# Installation

RestQ is designed to be easy to install and get started with. Here's how you can add it to your project.

## Requirements

Before installing RestQ, ensure you have:

- Python >= 3.9
- Redis server running
- Poetry (recommended) or pip

## Installing with Poetry

The recommended way to install RestQ is using Poetry:

```bash
poetry add restq
```

## Installing with pip

Alternatively, you can install using pip:

```bash
pip install restq
```

## Redis Setup

RestQ requires a Redis server. Here are a few ways to get Redis running:

### Using Docker

```bash
docker run -d --name redis -p 6379:6379 redis
```

### Local Installation

=== "macOS"
    ```bash
    brew install redis
    brew services start redis
    ```

=== "Ubuntu/Debian"
    ```bash
    sudo apt update
    sudo apt install redis-server
    sudo systemctl start redis-server
    ```

=== "Windows"
    Download the Redis installer from [Redis Downloads](https://redis.io/download) or use WSL2 with Ubuntu.

## Verifying Installation

You can verify your installation by running this simple test:

```python
from restq import Queue

# Initialize a queue
queue = Queue(name="test-queue", url="redis://localhost:6379/0")

# If no errors occur, installation is successful!
```

## Next Steps

Now that you have RestQ installed, check out the [Quick Start Guide](quickstart.md) to learn how to create your first task queue!
