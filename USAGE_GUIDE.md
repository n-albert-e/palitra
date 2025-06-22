# Palitra Library - Usage Guide

## Quick Start

### Installation
```bash
pip install palitra
```

### Basic Usage
```python
import asyncio
from palitra import run, gather

# Run a single async function
async def my_async_function():
    await asyncio.sleep(1)
    return "Hello from async!"

result = run(my_async_function())
print(result)  # "Hello from async!"

# Run multiple functions concurrently
async def process_item(item):
    await asyncio.sleep(0.1)
    return f"Processed {item}"

items = ["A", "B", "C"]
results = gather(*[process_item(item) for item in items])
print(results)  # ["Processed A", "Processed B", "Processed C"]
```

## Core Concepts

### 1. The `run()` Function
Use `run()` to execute a single coroutine from synchronous code:

```python
from palitra import run
import asyncio

async def fetch_data():
    await asyncio.sleep(0.1)
    return {"status": "success"}

# This blocks until the coroutine completes
data = run(fetch_data())
print(data)  # {"status": "success"}
```

### 2. The `gather()` Function
Use `gather()` to run multiple coroutines concurrently:

```python
from palitra import gather
import asyncio

async def fetch_user(user_id):
    await asyncio.sleep(0.1)
    return {"id": user_id, "name": f"User {user_id}"}

# Fetch multiple users concurrently
user_ids = [1, 2, 3, 4, 5]
users = gather(*[fetch_user(uid) for uid in user_ids])
print(users)  # List of user dictionaries
```

### 3. Error Handling
Handle errors with `return_exceptions=True`:

```python
from palitra import gather

async def risky_operation(should_fail):
    if should_fail:
        raise ValueError("Operation failed!")
    return "Success"

# This won't raise an exception
results = gather(
    risky_operation(False),
    risky_operation(True),
    risky_operation(False),
    return_exceptions=True
)

for i, result in enumerate(results):
    if isinstance(result, Exception):
        print(f"Task {i} failed: {result}")
    else:
        print(f"Task {i} succeeded: {result}")
```

### 4. Timeouts
Set timeouts to prevent hanging operations:

```python
from palitra import run

async def long_operation():
    await asyncio.sleep(10)  # This takes 10 seconds
    return "Done"

try:
    # This will timeout after 1 second
    result = run(long_operation(), timeout=1.0)
except Exception as e:
    print(f"Operation timed out: {e}")
```

## Advanced Usage

### Context Manager
Use `EventLoopThreadRunner` as a context manager for automatic cleanup:

```python
from palitra import EventLoopThreadRunner
import asyncio

async def my_task():
    await asyncio.sleep(0.1)
    return "Task completed"

# Automatic cleanup when exiting the context
with EventLoopThreadRunner() as runner:
    result1 = runner.run(my_task())
    result2 = runner.run(my_task())
    print(f"Results: {result1}, {result2}")
```

### Manual Runner Management
Create and manage runners manually:

```python
from palitra import EventLoopThreadRunner

runner = EventLoopThreadRunner()
try:
    result = runner.run(my_async_function())
finally:
    runner.close()  # Always close the runner
```

### Global Runner Lifecycle
The global runner is automatically managed, but you can control it:

```python
from palitra import run, shutdown_global_runner, is_runner_alive

# First call creates the global runner
result1 = run(my_async_function())

# Check if runner is alive
print(is_runner_alive())  # True

# Shutdown the global runner
shutdown_global_runner()

# Next call creates a new runner
result2 = run(my_async_function())
```

## Real-World Examples

### API Calls
```python
import aiohttp
from palitra import gather

async def fetch_api_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

urls = [
    "https://api.example.com/users",
    "https://api.example.com/posts",
    "https://api.example.com/comments"
]

# Fetch all data concurrently
results = gather(*[fetch_api_data(url) for url in urls])
```

### Database Operations
```python
import asyncpg
from palitra import gather

async def fetch_user_data(user_id):
    conn = await asyncpg.connect("postgresql://user:pass@localhost/db")
    try:
        return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    finally:
        await conn.close()

user_ids = [1, 2, 3, 4, 5]
users = gather(*[fetch_user_data(uid) for uid in user_ids])
```

### File Processing
```python
import aiofiles
from palitra import gather

async def process_file(filename):
    async with aiofiles.open(filename, 'r') as f:
        content = await f.read()
        return len(content)

files = ["file1.txt", "file2.txt", "file3.txt"]
sizes = gather(*[process_file(f) for f in files])
```

## Best Practices

### 1. Use `gather()` for Multiple Operations
```python
# Good - concurrent execution
results = gather(*[process_item(item) for item in items])

# Bad - sequential execution
results = [run(process_item(item)) for item in items]
```

### 2. Handle Errors Appropriately
```python
# For operations where you want to continue on errors
results = gather(*coroutines, return_exceptions=True)

# For operations where any error should stop execution
results = gather(*coroutines)  # Will raise first exception
```

### 3. Use Context Managers
```python
# Good - automatic cleanup
with EventLoopThreadRunner() as runner:
    result = runner.run(my_function())

# Bad - manual cleanup required
runner = EventLoopThreadRunner()
try:
    result = runner.run(my_function())
finally:
    runner.close()
```

### 4. Set Appropriate Timeouts
```python
# Always set timeouts for network operations
result = run(fetch_data(), timeout=30.0)

# Use shorter timeouts for quick operations
result = run(quick_operation(), timeout=1.0)
```

## Troubleshooting

### Common Issues

1. **"cannot reuse already awaited coroutine"**
   - Don't reuse coroutine objects. Create new ones for each call.

2. **"The runner has been closed"**
   - The runner was closed. Create a new one or use the global runner.

3. **"Deadlock detected"**
   - Don't call `run()` from within the runner's own thread.

4. **Timeout errors**
   - Increase the timeout or optimize your async function.

### Performance Tips

1. Use `gather()` instead of multiple `run()` calls
2. Set appropriate timeouts
3. Use context managers for automatic cleanup
4. Consider using `uvloop` for better performance (optional dependency)

## Examples

Run the examples to see palitra in action:

```bash
# Quick start
python quick_start.py

# Comprehensive examples
python main.py
```

## API Reference

### Functions
- `run(coro, timeout=None)` - Run a single coroutine
- `gather(*coros, return_exceptions=False, timeout=None)` - Run multiple coroutines
- `shutdown_global_runner()` - Shutdown the global runner
- `is_runner_alive()` - Check if global runner is alive

### Classes
- `EventLoopThreadRunner` - Manages a background event loop thread

### Exceptions
- `PalitraError` - Base exception class
- `DeadlockError` - Raised when deadlock is detected
- `RunnerError` - Raised for runner-related errors 