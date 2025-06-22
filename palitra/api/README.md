# API Package

This package provides the high-level API for the palitra library.

## Contents

- **`singleton.py`**: Global singleton runner and convenience functions
- **`singleton.pyi`**: Type stub file for the singleton module

## High-Level API Functions

### run()
Run a single coroutine in the global background event loop.

```python
from palitra.api import run
import asyncio

async def my_function():
    await asyncio.sleep(1)
    return "Done!"

result = run(my_function())
print(result)  # "Done!"
```

### gather()
Run multiple coroutines concurrently in the global event loop.

```python
from palitra.api import gather
import asyncio

async def task1():
    await asyncio.sleep(1)
    return "Task 1"

async def task2():
    await asyncio.sleep(2)
    return "Task 2"

results = gather(task1(), task2())
print(results)  # ["Task 1", "Task 2"]
```

### shutdown_global_runner()
Explicitly shut down the global event loop runner.

```python
from palitra.api import shutdown_global_runner

# Clean up resources
shutdown_global_runner()
```

### is_runner_alive()
Check if the global event loop runner exists and is active.

```python
from palitra.api import is_runner_alive

if is_runner_alive():
    print("Global runner is active")
else:
    print("Global runner is not active")
```

## Global Singleton Pattern

The API uses a singleton pattern to ensure all calls share the same background event loop thread. This provides:

- Automatic resource management
- Thread safety
- Efficient resource usage
- Automatic cleanup on application exit

## Usage Examples

```python
from palitra.api import run, gather, shutdown_global_runner
import asyncio

# Simple async function call
async def fetch_data():
    await asyncio.sleep(0.1)
    return {"status": "success"}

data = run(fetch_data())

# Concurrent execution
async def process_item(item):
    await asyncio.sleep(0.1)
    return f"Processed {item}"

items = ["A", "B", "C"]
results = gather(*[process_item(item) for item in items])

# Clean up when done
shutdown_global_runner()
``` 