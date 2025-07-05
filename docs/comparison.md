
## Comparison with Alternatives

| Feature                | `palitra`                         | `asyncio.run()` | [`nest_asyncio`](https://github.com/erdewit/nest_asyncio) | [`asgiref.AsyncToSync`](https://github.com/django/asgiref) | [`xloem/async_to_sync`](https://github.com/xloem/async_to_sync) | [`miyakogi/syncer`](https://github.com/miyakogi/syncer) | [`Haskely/async-sync`](https://github.com/Haskely/async-sync) |
| ---------------------- | --------------------------------- | --------------- | --------------------------------------------------------- | ---------------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------- |
| **Loop Persistence**   | ✅ Persistent (background thread) | ❌ Per call     | ✅ Patches                                                | ✅❌ Per call (if no running event loop in main thread)                        | ✅ Persistent (background thread)                               | ❌ Per call                                             | ❌ Per call                                                   |
| **Concurrency**        | ✅ Full                           | ❌ One-shot     | ✅                                                        | ✅❌ Per call (if no running event loop in main thread)                                                     | ✅                                                              | ❌ Single-thread blocking                               | ❌ Blocking                                                   |
| **No Monkey Patching** | ✅ Yes                            | ✅ Yes          | ❌ Required                                               | ✅ Yes                                                     | ✅ Yes                                                          | ✅ Yes                                                  | ✅ Yes                                                        |

---

- **`palitra`**: Should be ideal for long-running synchronous apps (e.g. Flask, CLI, Celery) that need to reuse async state across multiple calls. Avoids monkey-patching and global loop interference by running a persistent background event loop thread.
- **`asyncio.run()`**: Best for short-lived scripts where a one-time coroutine needs to be run synchronously.
- **`nest_asyncio`**: Patches the global event loop to allow nested async calls. Can work in Jupyter or limited contexts but is fragile for production.
- **`asgiref.AsyncToSync`**: Meant firstly for Django/ASGI internals. Not for general async wrapping—uses a per-call scheduling model with strict thread management.
- **`xloem/async_to_sync`**: A lightweight wrapper that synchronously runs a coroutine using loop in background thread.
- **`syncer`**: Simple `sync`/`async` wrappers using `run_until_complete`.
- **`async-sync`**: Lightweight utility; wraps async-to-sync calls using `loop.run_until_complete()`.

## Comparison with `asgiref.sync.AsyncToSync`

While `palitra` and `asgiref.sync.AsyncToSync` both enable running async code from sync code, they differ significantly in architecture and use cases:

### Key Differences

| Aspect                       | `palitra`                                               | `asgiref.sync.AsyncToSync`                      |
| ---------------------------- | ------------------------------------------------------- | ----------------------------------------------- |
| **Event Loop**               | Persistent background loop (one per runner)             | Reuses loop if possible, else creates temporary |
| **Execution Model**          | Dedicated thread runs the event loop                    | Coroutine scheduled into existing thread/loop   |
| **Loop Lifetime**            | Explicitly managed or global singleton                  | Per-call if there is none in main thread (usually short-lived)                  |
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

- You’re building on top of Django/ASGI and already using `asgiref`.
- You need compatibility with Django’s sync/async internals (e.g. views, middleware, ORM).
- Thread affinity is critical (e.g. thread-sensitive DB connections in Django).
