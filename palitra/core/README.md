# Core Package

This package contains the core functionality of the palitra library.

## Contents

- **`runner.py`**: The main `EventLoopThreadRunner` class that manages a dedicated asyncio event loop in a background thread.
- **`runner.pyi`**: Type stub file for the runner module.

## EventLoopThreadRunner

The `EventLoopThreadRunner` class is the heart of the palitra library. It provides:

- A persistent background event loop thread
- Thread-safe methods to run coroutines from synchronous code
- Context manager support for automatic cleanup
- Concurrent execution of multiple coroutines via `gather()`
- Proper shutdown and resource management

## Usage

```python
from palitra.core import EventLoopThreadRunner
import asyncio

async def my_async_function():
    await asyncio.sleep(1)
    return "Hello from async!"

# Using as a context manager (recommended)
with EventLoopThreadRunner() as runner:
    result = runner.run(my_async_function())
    print(result)  # "Hello from async!"

# Or manually
runner = EventLoopThreadRunner()
try:
    result = runner.run(my_async_function())
finally:
    runner.close()
``` 