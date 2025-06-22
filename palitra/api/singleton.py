"""
Global singleton runner and high-level API functions.

This module provides a convenient, globally accessible instance of the
`EventLoopThreadRunner`. It uses a singleton pattern to ensure that all calls
to `run()` and `gather()` from anywhere in the application share the same
background event loop thread.

The singleton is managed using `weakref` to allow for garbage collection when
it is no longer in use, and `atexit` ensures graceful shutdown.
"""
from __future__ import annotations

import weakref
from collections.abc import Coroutine
from threading import Lock
from typing import Any, TypeVar

from ..core.runner import EventLoopThreadRunner
from ..utils.logging import logger

__all__ = (
    "gather",
    "is_runner_alive",
    "run",
    "shutdown_global_runner",
)

# A generic type variable for coroutine return types.
T = TypeVar("T")

# A lock to ensure that the singleton creation is thread-safe.
_runner_lock = Lock()
_runner_ref: weakref.ReferenceType[EventLoopThreadRunner] | None = None
_finalizer = None


def _get_runner() -> EventLoopThreadRunner:
    """
    Return the global EventLoopThreadRunner instance, creating it if necessary.

    This function implements the thread-safe singleton pattern. It uses a weak
    reference to allow the runner to be garbage-collected if it's no longer
    referenced elsewhere, preventing resource leaks.
    """
    global _runner_ref

    with _runner_lock:
        runner = _runner_ref() if _runner_ref else None
        if runner is None or not runner.get_loop().is_running():
            logger.info("No active global runner found. Creating a new one.")
            runner = EventLoopThreadRunner()
            _runner_ref = weakref.ref(runner)
        else:
            logger.debug("Reusing existing global runner.")
        return runner


def run(coro: Coroutine[Any, Any, T], timeout: float | None = None) -> T:
    """
    Run a coroutine in the global background event loop and wait for its result.

    This is the simplest way to call an async function from a sync context.

    Args:
        coro: The coroutine to execute.
        timeout: Optional timeout in seconds.

    Returns:
        The result of the coroutine.
    """
    return _get_runner().run(coro, timeout)


def gather(
    *coros: Coroutine[Any, Any, T],
    return_exceptions: bool = False,
    timeout: float | None = None,
) -> list[T | BaseException]:
    """
    Run multiple coroutines concurrently in the global event loop.

    Args:
        *coros: The coroutines to execute concurrently.
        return_exceptions: If True, exceptions are returned as results
                           instead of being raised.
        timeout: Optional total timeout for all coroutines.

    Returns:
        A list of results or exceptions.
    """
    return _get_runner().gather(
        *coros,
        return_exceptions=return_exceptions,
        timeout=timeout,
    )


def shutdown_global_runner() -> None:
    """
    Explicitly shut down the global event loop runner.

    This stops the background thread and closes the event loop. Subsequent
    calls to `run` or `gather` will create a new runner instance. This is
    useful for resource cleanup in tests or long-running applications.
    """
    global _runner_ref
    with _runner_lock:
        runner = _runner_ref() if _runner_ref else None
        if runner:
            logger.info("Shutting down global runner.")
            runner.close()
        else:
            logger.debug("Shutdown called, but no global runner was active.")
        _runner_ref = None


def is_runner_alive() -> bool:
    """
    Check if the global event loop runner exists and is currently active.

    Returns:
        True if the runner's event loop is running, False otherwise.
    """
    with _runner_lock:
        runner = _runner_ref() if _runner_ref else None
        return runner is not None and runner.get_loop().is_running() 