# palitra

_a.k.a. "palette"_ — reflects the library’s purpose: blending execution models (sync/async) like colors on an artist’s palette, enabling harmony between Python’s concurrency approaches.

> **⚠️ Experimental Warning**: This library is experimental and not production-ready. Use at your own risk.

> Inspired by [Running async code from sync in Python asyncio](https://death.andgravity.com/asyncio-bridge) by [lemon24](https://github.com/lemon24) and related discussions such as [Celery #9058](https://github.com/celery/celery/discussions/9058).

---

A lightweight bridge between **synchronous and asynchronous Python code**, maintaining a persistent event loop in a background thread. It allows you to call `async def` functions directly from regular (sync) code without blocking or complex event loop reentry.

---

## 🔄 Comparison with Alternatives

| Feature                | `palitra`                         | `asyncio.run()`  | [`nest_asyncio`](https://github.com/erdewit/nest_asyncio)      | [`asgiref.AsyncToSync`](https://github.com/django/asgiref)               | [`xloem/async_to_sync`](https://github.com/xloem/async_to_sync) | [`miyakogi/syncer`](https://github.com/miyakogi/syncer) | [`Haskely/async-sync`](https://github.com/Haskely/async-sync) |
| ---------------------- | --------------------------------- | ---------------- | ------------------- | ----------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------- |
| **Loop Persistence**   | ✅ Persistent (background thread) | ❌ Per call      | ✅ Patches          | ❌ Per call (sync <-> async switch) | ❌ Per call                                                     | ❌ Per call                                             | ❌ Per call                                                   |
| **Concurrency**        | ✅ Full                           | ❌ One-shot      | ✅ Limited          | ✅ Yes (thread-safe queue)          | ✅ Limited                                                      | ❌ Single-thread blocking                               | ❌ Blocking                                                   |
| **No Monkey Patching** | ✅ Yes                            | ✅ Yes           | ❌ Required         | ✅ Yes                              | ✅ Yes                                                          | ✅ Yes                                                  | ✅ Yes                                                        |
| **Thread Safety**      | ✅⚠️ Basic, mostly tested         | ❌ No            | ❌ No               | ✅ Yes                              | ⚠️ No explicit handling                                         | ❌ No                                                   | ❌ No                                                         |
| **Production Ready**   | ❌ Experimental                   | ✅ Yes           | ⚠️ At your own risk | ✅ Yes                              | ⚠️ Unclear                                                      | ⚠️ Not production focused                               | ⚠️ Unclear                                                    |
| **State Preservation** | ✅ Yes                            | ❌ No            | ✅ Yes              | ❌ No (reschedules work)            | ❌ No                                                           | ❌ No                                                   | ❌ No                                                         |
| **Clean Shutdown**     | ✅⚠️ Partial, mostly reliable     | ✅ Yes           | ❌ Inconsistent     | ✅ Yes (clean detach)               | ✅ Yes (simple)                                                 | ✅ Yes (simple)                                         | ⚠️ Unknown                                                    |
| **Loop Isolation**     | ✅ Own thread & loop              | ❌ Global loop   | ❌ Shared loop      | ❌ Main thread only                 | ❌ Main thread                                                  | ❌ Main thread                                          | ❌ Main thread                                                |
| **Best Use Case**      | Sync apps needing async reuse     | One-shot scripts | Notebooks, REPL     | Django views/middleware             | Simple CLI calls                                                | Testing, quick tools                                    | Simple utilities                                              |


---

- **`palitra`**: Should be ideal for long-running synchronous apps (e.g. Flask, CLI, Celery) that need to reuse async state across multiple calls. Avoids monkey-patching and global loop interference by running a persistent background event loop thread.
- **`asyncio.run()`**: Best for short-lived scripts where a one-time coroutine needs to be run synchronously.
- **`nest_asyncio`**: Patches the global event loop to allow nested async calls. Can work in Jupyter or limited contexts but is fragile for production.
- **`asgiref.AsyncToSync`**: Meant for Django/ASGI internals. Not for general async wrapping—uses a per-call scheduling model with strict thread management.
- **`xloem/async_to_sync`**: A lightweight wrapper that synchronously runs a coroutine using the current loop. No isolation, and reuses the main thread loop.
- **`syncer`**: Simple `sync`/`async` wrappers using `run_until_complete`. Very easy but blocks the main thread and lacks isolation.
- **`async-sync`**: Lightweight utility; wraps async-to-sync calls using `loop.run_until_complete()`. Limited concurrency, no threading support.
## 🔍 Comparison with `asgiref.sync.AsyncToSync`

While `palitra` and `asgiref.sync.AsyncToSync` both enable running async code from sync code, they differ significantly in architecture and use cases:

### Key Differences

| Aspect                       | `palitra`                                               | `asgiref.sync.AsyncToSync`                      |
| ---------------------------- | ------------------------------------------------------- | ----------------------------------------------- |
| **Event Loop**               | Persistent background loop (one per runner)             | Reuses loop if possible, else creates temporary |
| **Execution Model**          | Dedicated thread runs the event loop                    | Coroutine scheduled into existing thread/loop   |
| **Loop Lifetime**            | Explicitly managed or global singleton                  | Per-call (usually short-lived)                  |
| **Thread Handling**          | Coroutines run in background thread, sync caller blocks | Complex dance to preserve thread affinity       |
| **Performance (Multi-call)** | Efficient — no repeated loop creation                   | Overhead from loop setup/teardown               |
| **State Preservation**       | Loop state preserved across sync calls                  | State lost unless explicitly preserved          |
| **Shutdown Control**         | `shutdown_global_runner()` available                    | No manual lifecycle management                  |

### Best Use Cases

**Use `palitra` when:**

- You need to call async code from sync repeatedly or over a long lifetime (e.g. Flask, CLI tools, Celery).
- You want to maintain event loop state between calls (e.g. reuse aiohttp sessions, connection pools).
- You want a lightweight, self-contained solution with explicit lifecycle control.

**Use `asgiref.sync.AsyncToSync` when:**

- You’re building on top of Django/ASGI and already use `asgiref`.
- You need compatibility with Django’s sync/async internals (e.g. views, ORM).
- Thread affinity is critical (e.g. thread-sensitive DB connections in Django).

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
- ✅ Automatic cleanup via `atexit` and weakref to global runner (if used)
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

- Creates a shared event loop thread on first use.
- Internally calls `EventLoopThreadRunner.run(...)`.

```python
from palitra import run

result = run(my_async_func())
```

---

### `gather(*coros: Coroutine, return_exceptions: bool = False, timeout: float | None = None) -> list[Any]`

Run multiple coroutines concurrently from sync code.

- Like `asyncio.gather(...)`, but callable from sync.
- Uses the global shared runner.

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

- After calling this, subsequent calls to `run` or `gather` will create a new runner instance.
- Useful for cleanup or to reset the runner state.

---

### 🔸 `EventLoopThreadRunner` Methods

Use the class directly if you need more control or isolation (e.g., separate event loop threads).

---

### `run(self, coro: Coroutine, timeout: float | None = None) -> Any`

Run a coroutine on this runner’s background loop.

- **Returns**: The coroutine result
- **Raises**:

  - `TypeError` if input is not a coroutine
  - `asyncio.TimeoutError` if timeout expires
  - Exceptions from the coroutine itself

---

### `gather(self, *coros: Coroutine, return_exceptions: bool = False, timeout: float | None = None) -> list[Any]`

Run multiple coroutines concurrently via this runner.

- Returns list of results or exceptions (if `return_exceptions=True`).
- Raises exceptions same as `run`.

---

### `get_loop(self) -> asyncio.AbstractEventLoop`

Get the event loop managed by this runner.

Useful if you want to schedule coroutines directly.

---

### `close(self) -> None`

Stop the event loop and background thread.

- Idempotent — safe to call multiple times.
- Cleans up resources and stops the thread.

---

## How It Works

1. Starts a background thread that runs an `asyncio` event loop.
2. Coroutines are submitted to it via `run()` or `gather()`.
3. Internally uses `asyncio.run_coroutine_threadsafe(...)` for thread-safe execution.
4. Ensures cleanup via `atexit` and context manager support.

---

## Contributing

Pull requests are welcome! Please:

- Document known issues or caveats
- Include test coverage for new features
- Keep the code as simple and minimal as possible
- Prefer clarity over cleverness

**Things that need more work:**

- Proper stress testing
- Verifying thread safety in edge cases
- Detecting and eliminating memory leaks
- Ensuring reliable shutdown under all conditions

---

## License

BSD-3-Clause
