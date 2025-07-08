# palitra

A lightweight bridge between **synchronous and asynchronous Python code**, maintaining a **persistent** event loop in a background thread. It allows you to call `async def` functions directly from regular (sync) code without blocking or complex event loop reentry.

Unlike `asyncio.run()`, which creates and tears down a new event loop on each call, using `palitra.run()` eliminates that overhead — preserving async state and resources (like aiohttp sessions or database connections) across multiple calls.

> _a.k.a. "palette"_ — captures the essence of the library: blending differently colored (sync/async) functions like on an artist’s palette.

> **⚠️ Known issues**: unexpected behaivour in 3.13t build.

If something breaks in your environment, please report an issue — the whole purpose of this library is to spare developers from reinventing async/sync bridges in every project. Your feedback directly helps improve its reliability and real-world compatibility.

> Inspired by [Running async code from sync in Python asyncio](https://death.andgravity.com/asyncio-bridge) by [lemon24](https://github.com/lemon24) and related discussions such as [Celery #9058](https://github.com/celery/celery/discussions/9058).


## Features

- ✅ Runs a persistent asyncio event loop in a background thread
- ✅ Simple, thread-safe API for running coroutines from sync code
- ✅ No monkey patching or global loop overrides
- ✅ Automatic cleanup via `atexit` and weakref to global runner (if used)
- ✅ Lightweight: no external dependencies


## [Documentation](https://github.com/abebus/palitra/tree/main/docs)

[Why this even exists?](https://github.com/abebus/palitra/tree/main/docs/faq.md)

## Usage Examples

This is not ideal, but in real-world scenarios, migrating to ASGI isn’t always possible.
When stuck with WSGI, palitra lets you still use async features to get things working.

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
    await asyncio.sleep(0.5)  # simulate async I/O
    return {"input": data, "processed": True, "timestamp": time.time()}

@celery_app.task(name="process_async")
def sync_celery_wrapper(data: str):
    return palitra.run(async_processing(data))
```


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
