from __future__ import annotations

import asyncio
import sys
import weakref
from collections.abc import Awaitable, Callable, Coroutine
from threading import Lock
from typing import Any, TypeVar

from ._core import EventLoopThreadRunner

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

T = TypeVar("T")
P = ParamSpec("P")

_runner_lock = Lock()
_runner_ref: weakref.ReferenceType[EventLoopThreadRunner] | None = None
_finalizer = None


def _get_runner() -> EventLoopThreadRunner:
    """Return the global EventLoopThreadRunner instance, creating it if necessary."""
    global _runner_ref, _finalizer

    with _runner_lock:
        runner = _runner_ref() if _runner_ref else None
        if runner is None:
            runner = EventLoopThreadRunner()
            _runner_ref = weakref.ref(runner)

            _finalizer = weakref.finalize(runner, shutdown_global_runner)
        return runner


def run(
    coro: Coroutine[Any, Any, T],
    *,
    timeout: float | None = None,
    debug: bool | None = None,
    loop_factory: Callable[[], asyncio.AbstractEventLoop] | None = None,
) -> T:
    """Run a coroutine in the global background event loop and wait for its result.

    Args:
        coro (Coroutine): Coroutine to execute.
        timeout (float | None): Optional timeout in seconds.

    Returns:
        Any: The result returned by the coroutine.

    Raises:
        TypeError: If `coro` is not a coroutine.
        asyncio.TimeoutError: If the coroutine does not complete before `timeout`.
        Exception: Any exception raised by the coroutine itself.

    """
    return _get_runner().run(
        coro, timeout=timeout, debug=debug, loop_factory=loop_factory
    )


def gather(
    *coros_or_futures: asyncio.Future[T] | Awaitable[T],
    return_exceptions: bool = False,
    timeout: float | None = None,
) -> list[T | BaseException]:
    """Run multiple coroutines concurrently in the global event loop and collect results.

    Args:
        *coros (Coroutine): Coroutines to execute concurrently.
        return_exceptions (bool): If True, exceptions are returned as results instead of raised.
        timeout (float | None): Optional timeout in seconds for the entire gather.

    Returns:
        List[Any]: Results of the coroutines or exceptions if `return_exceptions=True`.

    Raises:
        asyncio.TimeoutError: If the gather operation exceeds the timeout.
        Exception: Any exception from coroutines unless `return_exceptions=True`.

    """  # noqa: E501
    return _get_runner().gather(
        *coros_or_futures,
        return_exceptions=return_exceptions,
        timeout=timeout,
    )


def shutdown_global_runner() -> None:
    """Explicitly shut down the global event loop runner and release resources.

    After calling this, subsequent calls to `run` or `gather` will create a new runner.
    """
    global _runner_ref, _finalizer
    with _runner_lock:
        runner = _runner_ref() if _runner_ref else None
        if runner:
            runner.close()
        _runner_ref = None
        if _finalizer:
            _finalizer.detach()
            _finalizer = None


def is_runner_alive() -> bool:
    """Check whether the global event loop runner currently exists and is alive.

    Returns:
        bool: True if the global runner exists and is not garbage collected, False otherwise.

    """  # noqa: E501
    with _runner_lock:
        runner = _runner_ref() if _runner_ref else None
        return runner is not None
