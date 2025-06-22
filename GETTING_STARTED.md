# Getting Started with Palitra

## 🚀 Quick Start

### 1. Installation
```bash
pip install palitra
```

### 2. Basic Usage
```python
import asyncio
from palitra import run, gather

# Run a single async function
async def my_function():
    await asyncio.sleep(1)
    return "Hello from async!"

result = run(my_function())
print(result)  # "Hello from async!"

# Run multiple functions concurrently
async def process_item(item):
    await asyncio.sleep(0.1)
    return f"Processed {item}"

items = ["A", "B", "C"]
results = gather(*[process_item(item) for item in items])
print(results)  # ["Processed A", "Processed B", "Processed C"]
```

## 📚 How to Use Palitra

### For Beginners

1. **Start with `quick_start.py`**:
   ```bash
   python quick_start.py
   ```

2. **Run the interactive demo**:
   ```bash
   python palitra_cli.py demo
   ```

3. **Check library info**:
   ```bash
   python palitra_cli.py info
   ```

### For Developers

1. **Run comprehensive examples**:
   ```bash
   python main.py
   ```

2. **Test functionality**:
   ```bash
   python palitra_cli.py test
   ```

## 🎯 Common Use Cases

### 1. API Calls
```python
import aiohttp
from palitra import gather

async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

urls = ["https://api1.com", "https://api2.com", "https://api3.com"]
results = gather(*[fetch_data(url) for url in urls])
```

### 2. Database Operations
```python
import asyncpg
from palitra import gather

async def fetch_user(user_id):
    conn = await asyncpg.connect("postgresql://...")
    try:
        return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    finally:
        await conn.close()

user_ids = [1, 2, 3, 4, 5]
users = gather(*[fetch_user(uid) for uid in user_ids])
```

### 3. File Processing
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

## 🔧 Advanced Usage

### Context Manager (Recommended)
```python
from palitra import EventLoopThreadRunner

with EventLoopThreadRunner() as runner:
    result1 = runner.run(async_function1())
    result2 = runner.run(async_function2())
    # Automatic cleanup when exiting context
```

### Manual Management
```python
from palitra import EventLoopThreadRunner

runner = EventLoopThreadRunner()
try:
    result = runner.run(my_async_function())
finally:
    runner.close()  # Always close manually
```

### Global Runner Lifecycle
```python
from palitra import run, shutdown_global_runner, is_runner_alive

# First call creates global runner
result1 = run(my_function())

# Check status
print(is_runner_alive())  # True

# Shutdown when done
shutdown_global_runner()

# Next call creates new runner
result2 = run(my_function())
```

## 🛠️ Error Handling

### Handle Exceptions Gracefully
```python
from palitra import gather

async def risky_operation(should_fail):
    if should_fail:
        raise ValueError("Operation failed!")
    return "Success"

# Continue on errors
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

### Timeout Handling
```python
from palitra import run

async def long_operation():
    await asyncio.sleep(10)
    return "Done"

try:
    result = run(long_operation(), timeout=1.0)
except Exception as e:
    print(f"Operation timed out: {e}")
```

## 📖 Documentation

### Available Files
- **`USAGE_GUIDE.md`** - Comprehensive usage guide
- **`PACKAGE_STRUCTURE.md`** - Package organization details
- **`main.py`** - Complete examples
- **`quick_start.py`** - Quick start examples
- **`palitra_cli.py`** - Interactive CLI tool

### Package Structure
```
palitra/
├── core/           # Core functionality
├── utils/          # Utilities and exceptions
├── api/            # High-level API
└── __init__.py     # Main interface
```

## 🎯 Best Practices

1. **Use `gather()` for multiple operations** - Much faster than multiple `run()` calls
2. **Handle errors appropriately** - Use `return_exceptions=True` when needed
3. **Use context managers** - Automatic cleanup is safer
4. **Set timeouts** - Prevent hanging operations
5. **Don't reuse coroutines** - Create new ones for each call

## 🚨 Common Pitfalls

1. **Reusing coroutines**:
   ```python
   # ❌ Wrong
   coro = my_async_function()
   result1 = run(coro)
   result2 = run(coro)  # Error!
   
   # ✅ Correct
   result1 = run(my_async_function())
   result2 = run(my_async_function())
   ```

2. **Not handling timeouts**:
   ```python
   # ❌ May hang
   result = run(network_operation())
   
   # ✅ Safe
   result = run(network_operation(), timeout=30.0)
   ```

3. **Manual cleanup**:
   ```python
   # ❌ Error-prone
   runner = EventLoopThreadRunner()
   result = runner.run(my_function())
   # Forgot to close!
   
   # ✅ Safe
   with EventLoopThreadRunner() as runner:
       result = runner.run(my_function())
   ```

## 🔍 Troubleshooting

### "cannot reuse already awaited coroutine"
- Create new coroutine objects for each call

### "The runner has been closed"
- Create a new runner or use the global runner

### "Deadlock detected"
- Don't call `run()` from within the runner's own thread

### Timeout errors
- Increase timeout or optimize your async function

## 📞 Getting Help

1. **Run examples** to see how it works
2. **Check the logs** for detailed information
3. **Use the CLI** for testing: `python palitra_cli.py test`
4. **Read the documentation** in the markdown files

## 🎉 You're Ready!

Start with `python quick_start.py` and explore the examples. The library is designed to be simple and intuitive - you can start using it immediately! 