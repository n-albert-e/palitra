"""
Core implementation of the EventLoopThreadRunner.
"""
from __future__ import annotations

import asyncio
import atexit
from collections.abc import Coroutine
from concurrent.futures import Future, TimeoutError
from threading import Event, Thread, get_ident
from typing import Any, TypeVar

from ..utils.exceptions import DeadlockError, RunnerError
from ..utils.logging import logger

# For a significant performance boost, users can install uvloop. This is an
# optional dependency. `uvloop.install()` replaces the default asyncio event
# loop policy with a high-performance one.
try:
    import uvloop

    uvloop.install()
except ImportError:
    pass

T = TypeVar("T")


class EventLoopThreadRunner:
    """
    Manages a dedicated asyncio event loop running in a background thread.

    This class provides a thread-safe mechanism to run coroutines on a persistent
    event loop. It is ideal for calling async code from a synchronous context
    without the overhead of creating and tearing down a new loop for each call.

    It also supports usage as a context manager for guaranteed cleanup.
    """

    _loop: asyncio.AbstractEventLoop
    _thread: Thread
    _started: Event

    def __init__(self) -> None:
        """
        Initializes the runner and starts the background event loop thread.

        The thread is created as a daemon, so it won't prevent the application
        from exiting if the main thread finishes.
        """
        self._loop = asyncio.new_event_loop()
        self._thread = Thread(target=self._run_loop_forever, daemon=True)
        self._started = Event()
        self._thread.start()

        # Block until the background thread confirms that the loop is running.
        # This prevents race conditions where `run` might be called before the
        # loop is ready.
        self._started.wait()
        logger.success(f"Runner thread started (id={self._thread.ident}).")

        # Ensure that `close()` is called automatically when the interpreter exits,
        # providing a graceful shutdown.
        atexit.register(self.close)

    def __enter__(self) -> EventLoopThreadRunner:
        """Enter the context manager, returning the runner instance."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager, ensuring the runner is closed."""
        logger.debug("Exiting context manager, closing runner.")
        self.close()

    def _run_loop_forever(self) -> None:
        """
        The main entry point for the background thread.

        This function sets the current event loop for this thread and runs it
        indefinitely until `stop()` is called from another thread.
        """
        asyncio.set_event_loop(self._loop)
        self._started.set()  # Signal that the loop is ready.
        try:
            self._loop.run_forever()
        finally:
            # This cleanup code runs inside the event loop's thread right after
            # `run_forever` returns.
            self._shutdown_loop()

    def _shutdown_loop(self) -> None:
        """
        Gracefully shuts down the event loop.

        It cancels all running tasks before closing the loop. This allows tasks
        to run their cleanup code (e.g., in `finally` blocks) upon cancellation.
        """
        if self._loop.is_closed():
            return

        # Gather all tasks running on the loop.
        tasks = asyncio.all_tasks(self._loop)
        if not tasks:
            self._loop.close()
            return

        # `task.cancel()` is idempotent and requests the task to stop.
        for task in tasks:
            task.cancel()

        # Create a "gathering" task to wait for all other tasks to finish their
        # cancellation sequence. This ensures that `await task` in a cancelled
        # task's `finally` block can run to completion.
        async def _gather_cancelled_tasks() -> None:
            await asyncio.gather(*tasks, return_exceptions=True)

        try:
            self._loop.run_until_complete(_gather_cancelled_tasks())
        finally:
            # Ensure the loop is always closed, even if the gathering task fails.
            self._loop.close()

    def run(self, coro: Coroutine[Any, Any, T], timeout: float | None = None) -> T:
        """
        Runs a coroutine on the background event loop and waits for its result.

        Args:
            coro: The coroutine to execute.
            timeout: Optional timeout in seconds to wait for the result.

        Returns:
            The result of the coroutine.

        Raises:
            TypeError: If `coro` is not a coroutine object.
            concurrent.futures.TimeoutError: If the execution times out.
            Exception: Any exception raised by the coroutine will be re-raised
                       in the calling (synchronous) thread.
        """
        if not self._loop.is_running():
            logger.error("Attempted to run a task on a closed runner.")
            raise RunnerError("The runner has been closed and cannot accept new tasks.")

        if get_ident() == self._thread.ident:
            logger.error("Deadlock detected: run() called from the runner's own thread.")
            raise DeadlockError(
                "Cannot call `run()` from within the runner's own event loop thread. "
                "This would cause a deadlock."
            )

        if not asyncio.iscoroutine(coro):
            logger.warning(f"run() received a non-coroutine type: {type(coro).__name__}")
            raise TypeError("A coroutine object is required")

        # `run_coroutine_threadsafe` is the only safe way to schedule work
        # on an event loop that is running in another thread.
        future: Future[T] = asyncio.run_coroutine_threadsafe(coro, self._loop)

        # This call blocks the calling (synchronous) thread until the future
        # is resolved in the background thread.
        try:
            return future.result(timeout)
        except TimeoutError as e:
            logger.warning(f"Task timed out after {timeout}s.")
            future.cancel()
            raise e
        except Exception as e:
            logger.error(f"An exception occurred in the coroutine: {e}", exc_info=True)
            raise

    def gather(
        self,
        *coros: Coroutine[Any, Any, T],
        return_exceptions: bool = False,
        timeout: float | None = None,
    ) -> list[T | BaseException]:
        """
        Runs multiple coroutines concurrently on the background loop.

        This method is a thread-safe, synchronous equivalent of `asyncio.gather`.

        Args:
            *coros: The coroutines to execute concurrently.
            return_exceptions: If True, exceptions from coroutines are returned
                               in the result list instead of being raised.
            timeout: An optional total timeout for all coroutines. If the
                     timeout is reached, a `TimeoutError` is raised.

        Returns:
            A list containing the results or exceptions from the coroutines.
        """
        if not all(asyncio.iscoroutine(c) for c in coros):
            raise TypeError("All arguments must be coroutine objects")

        # Create a single `gather` coroutine that wraps the user's coroutines.
        # This is more efficient than scheduling each one individually.
        async def _gather_wrapper() -> list[T | BaseException]:
            return await asyncio.gather(*coros, return_exceptions=return_exceptions)

        # The gather operation itself is run as a single coroutine with a timeout.
        return self.run(_gather_wrapper(), timeout=timeout)

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """
        Returns the event loop managed by this runner.

        Warning:
            Direct manipulation of the loop from outside the runner's thread
            is not thread-safe. Use `run_coroutine_threadsafe` for scheduling
            coroutines or `call_soon_threadsafe` for regular functions.
        """
        return self._loop

    def close(self) -> None:
        """
        Stops the event loop and joins the background thread.

        This method is idempotent and thread-safe. It cancels all running
        tasks and waits for the background thread to exit gracefully.
        """
        if not self._loop.is_running():
            return

        logger.debug("Closing runner...")
        self._loop.call_soon_threadsafe(self._loop.stop)

        # Wait for the background thread to terminate. A timeout is included
        # to prevent the application from hanging indefinitely on shutdown.
        if self._thread.is_alive():
            self._thread.join(timeout=10)
            if self._thread.is_alive():
                logger.warning("Runner thread did not exit within the 10s timeout.")

        # Unregister the atexit callback to prevent it from running again.
        # This is useful if `close()` is called manually before exit.
        try:
            atexit.unregister(self.close)
        except Exception:
            # This can fail if it was already unregistered in a race condition,
            # which is safe to ignore.
            pass

        logger.success(f"Runner thread (id={self._thread.ident}) has been closed.")
