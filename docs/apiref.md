
## API Reference

### High-Level API (Global Runner)

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

###  `EventLoopThreadRunner` Methods

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