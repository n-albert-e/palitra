
## How It Works

1. Starts a background thread that runs an `asyncio` event loop.
2. Internally uses `asyncio.run_coroutine_threadsafe(...)` for thread-safe execution.
3. Ensures cleanup via `atexit` and context manager support.
4. If used via high-level api (`run`, `gather`), global runner object created using weakref.

## Why is this even needed?

In many real-world Python projects — especially those using **WSGI frameworks** like Flask or tools like **Celery** — migrating to an async runtime (like ASGI) isn't always feasible. Yet, the need to interact with **async libraries** (e.g., `aiohttp`, async database clients) continues to grow.

Using `asyncio.run()` inside sync code creates and destroys a new event loop on every call. This introduces overhead, makes resource reuse (like sessions or connections) difficult, and often breaks in threaded or long-running environments.

**palitra** provides a lightweight, consistent solution: it runs a **persistent asyncio event loop in a background thread**, allowing sync code to run `async def` functions with minimal ceremony — no blocking, no loop reentry errors, and no need to rewrite your whole app.

Instead of copy-pasting custom "run-a-coroutine-from-sync" boilerplate in every project, just use **palitra**.
