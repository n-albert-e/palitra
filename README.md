# palitra
(a variant of "palette" found across Eastern Europe and Central Asia) reflects the library’s purpose: to blend execution models (sync/async) like colors on an artist’s palette, creating harmony between Python’s concurrency approaches. 


> **Important Note**: This is experimental code. Not production-ready. Use at your own risk.

> This implementation was inspired (a.k.a. stolen) from [Running async code from sync in Python asyncio](https://death.andgravity.com/asyncio-bridge) by [lemon24](https://github.com/lemon24)

A bridge between synchronous and asynchronous Python code that maintains a persistent event loop, enabling you to call async functions from synchronous code.

## ⚠️ Important Caveats

1. **Not fully tested** - Edge cases may exist
2. **Thread safety concerns** - While basic operations are thread-safe, complex scenarios may reveal issues
3. **Resource cleanup** - Proper shutdown in all scenarios isn't guaranteed
4. **Performance characteristics** - Not benchmarked for high-load scenarios

**Use in production only after thorough testing in your specific environment.**

## Features

- Runs a persistent asyncio event loop in a background thread
- Provides simple API to execute coroutines from synchronous code
- Thread-safe operations with proper event loop management
- Automatic cleanup on program exit
- Lightweight with no external dependencies


## Usage Example: Flask with aiohttp

> **Warning**: This example demonstrates the concept but hasn't been stress-tested for production workloads.


```python
from flask import Flask, jsonify
from palitra import EventLoopThreadRunner
import aiohttp

app = Flask(__name__)

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.json()

@app.route('/api/comments')
def get_comments():
    async def fetch_all():
        async with aiohttp.ClientSession() as session:
            urls = [
                'https://jsonplaceholder.typicode.com/comments/1',
                'https://jsonplaceholder.typicode.com/comments/2',
                'https://jsonplaceholder.typicode.com/comments/3'
            ]
            return await EventLoopThreadRunner.gather(
                *[fetch_url(session, url) for url in urls]
            )
    
    comments = EventLoopThreadRunner.run(fetch_all())
    return jsonify(comments)

if __name__ == '__main__':
    app.run()
```

## API Reference

### `EventLoopThreadRunner.run(coro: Coroutine) -> Any`

Execute a single coroutine in the background event loop and return its result.

- `coro`: The coroutine to execute
- Returns: The result of the coroutine execution
- Raises: 
  - `NotImplementedError` if non-coroutine awaitable is passed
  - Any exception raised by the coroutine

### `EventLoopThreadRunner.gather(*coros_or_futures: Coroutine | Future, return_exceptions: bool = False) -> list[Any]`

Run multiple coroutines concurrently and return their results in order.

- `coros_or_futures`: Coroutines or Futures to execute
- Returns: List of results in the same order as input
- Raises: Any exception raised by the first failing coroutine

### `EventLoopThreadRunner.get_loop() -> AbstractEventLoop`

Get the running event loop instance from thread.

## How It Works

1. Creates a dedicated thread running an asyncio event loop
2. Provides thread-safe methods to interact with the loop
3. Automatically cleans up the thread on program exit
4. Uses `asyncio.run_coroutine_threadsafe` for safe execution

## Comparison with Alternatives

| Feature                | EventLoopThreadRunner | asyncio.run | nest_asyncio |
|------------------------|-----------------------|-------------|--------------|
| Production Readiness   | ❌ Not verified       | ✅ Yes      | ✅ Yes       |
| Persistent loop        | ✅ Yes                | ❌ No       | ✅ Yes       |
| Thread Safety          | ⚠️ Limited testing    | ❌ No       | ❌ No        |
| Clean shutdown         | ⚠️ Partial            | ✅ Yes      | ❌ Sometimes |

## Contributing

Pull requests are very welcome! Please:

1. Clearly document any limitations you discover
2. Include tests for new functionality
3. Add warnings for edge cases
4. Keep the implementation simple and transparent

Current areas needing attention:
- Proper stress testing
- Thread safety verification
- Memory leak detection
- Clean shutdown in all scenarios

## License
BSD-3

