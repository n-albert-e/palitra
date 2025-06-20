"""Inspired by https://death.andgravity.com/asyncio-bridge"""

from __future__ import annotations

import asyncio
import atexit
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop, Future
    from collections.abc import Coroutine
    from typing import Any

__all__ = ("EventLoopThreadRunner",)


def _run_forever(runner: EventLoopThreadRunner, loop_created: threading.Event):
    loop = runner.get_loop()
    asyncio.set_event_loop(loop)
    loop_created.set()
    loop.run_forever()


class EventLoopThreadRunner:
    """Manager class that keeps asyncio.Loop alive during whole script/app execution
    and provides helper API to execute async functions from sync environment
    """

    _runner = asyncio.Runner()

    loop_created = threading.Event()

    _thread = threading.Thread(
        target=_run_forever,
        name="LoopThread",
        args=(_runner, loop_created),
        daemon=True,
    )
    _thread.start()
    loop_created.wait()

    @classmethod
    def _close(cls) -> None:
        loop = cls.get_loop()
        loop.call_soon_threadsafe(loop.stop)
        cls._thread.join()

    @classmethod
    def get_loop(cls) -> AbstractEventLoop:
        return cls._runner.get_loop()

    @classmethod
    def run(cls, coro: Coroutine) -> Any:
        if not asyncio.iscoroutine(coro):
            raise NotImplementedError("Other awaitables currently not supported")
        loop = cls.get_loop()
        return asyncio.run_coroutine_threadsafe(coro, loop).result()

    @classmethod
    def gather(
        cls, *coros_or_futures: Coroutine | Future, return_exceptions: bool = False
    ) -> list[Any]:
        async def coro():
            return await asyncio.gather(
                *coros_or_futures, return_exceptions=return_exceptions
            )

        return cls.run(coro())


atexit.register(EventLoopThreadRunner._close)
