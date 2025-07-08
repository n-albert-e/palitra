"""Inspired by https://death.andgravity.com/asyncio-bridge"""

from __future__ import annotations

import asyncio
import atexit
import threading
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


class EventLoopThreadRunner:
    """Runs an asyncio event loop in a dedicated background thread.

    Provides synchronous methods to run async coroutines safely from any thread,
    allowing seamless bridging between synchronous and asynchronous code.

    Usage:
        runner = EventLoopThreadRunner()
        result = runner.run(some_coroutine())
        runner.close()

    Methods:
        - run(coro, timeout=None): Run a coroutine and wait for the result.
        - gather(*coros, return_exceptions=False, timeout=None): Run multiple coroutines concurrently and collect results.
        - get_loop(): Access the underlying event loop object.
        - close(): Stop the loop and clean up resources.

    """  # noqa: E501

    __slots__ = ("__weakref__", "_loop", "_loop_created", "_thread")

    def __init__(self) -> None:
        """The thread starts immediately, and the loop runs forever until closed.
        Registers atexit handler to close the loop on interpreter shutdown.
        """
        atexit.register(self.close)

        self._loop = asyncio.new_event_loop()
        self._loop_created = threading.Event()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="LoopThread",
            daemon=True,
        )
        self._thread.start()
        self._loop_created.wait()

    def _run_loop(self) -> None:
        """Target function for the background thread.

        Sets and runs the event loop forever until stopped.
        """
        asyncio.set_event_loop(self._loop)
        self._loop_created.set()
        try:
            self._loop.run_forever()
        except:
            raise
        finally:
            self._loop.close()

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """Return the underlying asyncio event loop instance.

        Returns:
            asyncio.AbstractEventLoop: The background event loop.

        """
        return self._loop

    def run(
        self,
        coro: Coroutine[Any, Any, T],
        *,
        timeout: float | None = None,
        debug: bool | None = None,
        loop_factory: Callable[[], asyncio.AbstractEventLoop] | None = None,
    ) -> T:
        """Run a coroutine in the background event loop and wait for its result.

        Args:
            coro (Coroutine): The coroutine to run.
            timeout (float | None): Optional timeout in seconds.

        Returns:
            Any: The result returned by the coroutine.

        Raises:
            TypeError: If `coro` is not a coroutine.
            asyncio.TimeoutError: If the coroutine does not complete before `timeout`.
            Exception: Any exception raised by the coroutine itself.

        """
        if loop_factory is not None:
            raise NotImplementedError("`loop_factory` currently not implemented.")

        if debug is not None:
            self.get_loop().set_debug(debug)

        async def wrapped() -> T:
            return await asyncio.wait_for(coro, timeout)

        future = asyncio.run_coroutine_threadsafe(wrapped(), self._loop)
        return future.result()

    def gather(
        self,
        *coros_or_futures: asyncio.Future[T] | Awaitable[T],
        return_exceptions: bool = False,
        timeout: float | None = None,
    ) -> list[T | BaseException]:
        """Run multiple coroutines concurrently, waiting for all to complete.

        Args:
            *coros (Coroutine): Coroutines to run concurrently.
            return_exceptions (bool): If True, exceptions are returned in results rather than raised.
            timeout (float | None): Optional timeout in seconds for the entire gather operation.

        Returns:
            List[Any]: List of results from the coroutines (or exceptions if `return_exceptions=True`).

        Raises:
            asyncio.TimeoutError: If the gather operation times out.
            Exception: Any exception from coroutines, unless suppressed by `return_exceptions=True`.

        """  # noqa: E501

        async def gatherer() -> list[T | BaseException]:
            return await asyncio.gather(
                *coros_or_futures, return_exceptions=return_exceptions
            )

        return self.run(gatherer(), timeout=timeout)

    def close(self) -> None:
        """Stop the event loop and wait for the thread to finish.

        This method is idempotent — calling it multiple times has no effect.

        Cleans up resources registered in the internal context stack.
        """
        loop = self.get_loop()
        if loop.is_closed():
            return
        loop.call_soon_threadsafe(loop.stop)
        self._thread.join()
