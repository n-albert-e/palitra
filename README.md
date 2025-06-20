# palitra

*a.k.a. "palette"* — reflects the library’s purpose: blending execution models (sync/async) like colors on an artist’s palette, enabling harmony between Python’s concurrency approaches.

> **⚠️ Experimental Warning**: This library is experimental and not production-ready. Use at your own risk.

> Inspired by [Running async code from sync in Python asyncio](https://death.andgravity.com/asyncio-bridge) by [lemon24](https://github.com/lemon24) and related discussions such as [Celery #9058](https://github.com/celery/celery/discussions/9058).

---

A lightweight bridge between **synchronous and asynchronous Python code**, maintaining a persistent event loop in a background thread. It allows you to call `async def` functions directly from regular (sync) code without blocking or complex event loop reentry.

## Comparison with Alternatives

| Feature                | `palitra`                        | `asyncio.run()` | `nest_asyncio` | ASGIRef (Django) |
| ---------------------- | ------------------------------- | --------------- | -------------- | ---------------- |
| **Loop Persistence**   | ✅ Persistent                   | ❌ Per call      | ✅ Patches      | ❌ Per call       |
| **Concurrency**        | ✅ Full                         | ❌ One-shot      | ✅ Limited      | ❌ One-shot       |
| **No Monkey Patching** | ✅ Yes                          | ✅ Yes           | ❌ Required     | ✅ Yes            |
| **Thread Safety**      | ✅⚠️ Basic, mostly tested         | ❌ No            | ❌ No           | ✅ Yes            |
| **Production Ready**   | ❌ Experimental                 | ✅ Yes           | ✅ Yes          | ✅ Yes            |
| **State Preservation** | ✅ Yes                          | ❌ No            | ✅ Yes          | ❌ No             |
| **Clean Shutdown**     | ✅⚠️ Partial, mostly reliable    | ✅ Yes           | ❌ Inconsistent | ✅ Yes            |

### Why these alternatives struggle in long-running applications:

* **`asyncio.run()`**:
  Designed for one-off coroutine execution; it **creates and closes a new event loop per call**. This leads to overhead, loss of persistent state, and inability to reuse the loop across multiple calls, making it inefficient for long-running applications.

* **`nest_asyncio`**:
  Enables re-entry into an existing event loop by patching the loop, but this monkey patching can introduce subtle bugs and race conditions. Its limited concurrency support and side effects on the event loop state make it **fragile and risky in production**, especially for complex, long-running programs.

* **`ASGIRef (Django)`**:
  Typically designed to run event loops per request or per task (one-shot). While safe and production-ready, this model **does not preserve loop state** between calls and incurs the cost of loop setup/teardown, which is inefficient in long-running, multi-call scenarios.

---

## ⚠️ Caveats & Limitations

1. **Not battle tested** — edge cases may be unhandled.
2. **Basic thread safety** — thread-safe for normal use, but not deeply audited.

Only use in production after careful evaluation in your environment.

---

## Features

- ✅ Runs a persistent asyncio event loop in a background thread
- ✅ Simple, thread-safe API for running coroutines from sync code
- ✅ No monkey patching or global loop overrides
- ✅ Automatic cleanup via `atexit`
- ✅ Lightweight: no external dependencies

---

## Usage Examples

### Flask with aiohttp

```python
from flask import Flask, jsonify
import palitra
import aiohttp
import asyncio

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
                'https://jsonplaceholder.typicode.com/comments/3',
            ]
            return await asyncio.gather(*[fetch_url(session, url) for url in urls])
    
    comments = palitra.run(fetch_all())
    return jsonify(comments)

if __name__ == '__main__':
    app.run()
```
---

### Celery

```python
import palitra
from celery import Celery
import asyncio
import time

celery_app = Celery('tasks', broker='pyamqp://guest@localhost//')

async def async_processing(data: str) -> dict:
    await asyncio.sleep(0.5)  # Simulate async I/O
    return {"input": data, "processed": True, "timestamp": time.time()}

@celery_app.task(name="process_async")
def sync_celery_wrapper(data: str):
    return palitra.run(async_processing(data))
```

---

## API Reference

### 🔹 High-Level API (Global Runner)

These top-level functions create and reuse a **singleton** `EventLoopThreadRunner` under the hood.

---

### `run(coro: Coroutine, timeout: float | None = None) -> Any`

Run a coroutine from synchronous code.

* Creates a shared event loop thread on first use.
* Internally calls `EventLoopThreadRunner.run(...)`.

```python
from palitra import run

result = run(my_async_func())
```

---

### `gather(*coros: Coroutine, return_exceptions: bool = False, timeout: float | None = None) -> list[Any]`

Run multiple coroutines concurrently from sync code.

* Like `asyncio.gather(...)`, but callable from sync.
* Uses the global shared runner.

```python
from palitra import gather

results = gather(coro1(), coro2(), coro3())
```

---

### `is_runner_alive() -> bool`

Check whether the global event loop runner currently exists and is alive.

---

### `shutdown_global_runner() -> None`

Explicitly shut down the global event loop runner and release resources.

* After calling this, subsequent calls to `run` or `gather` will create a new runner instance.
* Useful for cleanup or to reset the runner state.

---

### 🔸 `EventLoopThreadRunner` Methods

Use the class directly if you need more control or isolation (e.g., separate event loop threads).

---

### `run(self, coro: Coroutine, timeout: float | None = None) -> Any`

Run a coroutine on this runner’s background loop.

* **Returns**: The coroutine result
* **Raises**:

  * `TypeError` if input is not a coroutine
  * `asyncio.TimeoutError` if timeout expires
  * Exceptions from the coroutine itself

---

### `gather(self, *coros: Coroutine, return_exceptions: bool = False, timeout: float | None = None) -> list[Any]`

Run multiple coroutines concurrently via this runner.

* Returns list of results or exceptions (if `return_exceptions=True`).
* Raises exceptions same as `run`.

---

### `get_loop(self) -> asyncio.AbstractEventLoop`

Get the event loop managed by this runner.

Useful if you want to schedule coroutines directly.

---

### `close(self) -> None`

Stop the event loop and background thread.

* Idempotent — safe to call multiple times.
* Cleans up resources and stops the thread.

---

## How It Works

1. Starts a background thread that runs an `asyncio` event loop.
2. Coroutines are submitted to it via `run()` or `gather()`.
3. Internally uses `asyncio.run_coroutine_threadsafe(...)` for thread-safe execution.
4. Ensures cleanup via `atexit` and context manager support.

---


## Contributing

Pull requests are welcome! Please:

* Document known issues or caveats
* Include test coverage for new features
* Keep the code as simple and minimal as possible
* Prefer clarity over cleverness

**Things that need more work:**

* Proper stress testing
* Verifying thread safety in edge cases
* Detecting and eliminating memory leaks
* Ensuring reliable shutdown under all conditions

---

## License

BSD-3-Clause

