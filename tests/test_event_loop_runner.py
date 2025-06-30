"""Tests for EventLoopThreadRunner class."""

import asyncio
import concurrent.futures
import gc
import threading
import weakref
from typing import Any, Never

import pytest

from palitra import EventLoopThreadRunner


def test_loop_consistency(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test that the same loop instance is returned consistently."""
    initial_loop = event_loop_runner.get_loop()
    event_loop_runner.run(asyncio.sleep(0.01))
    assert event_loop_runner.get_loop() is initial_loop


def test_exception_handling(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test that exceptions from coroutines are properly propagated."""

    async def raises_exception() -> None:
        raise ValueError("test error")

    with pytest.raises(ValueError, match="test error"):
        event_loop_runner.run(raises_exception())


def test_gather_operation(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test gather method with multiple coroutines."""

    async def hello() -> str:
        await asyncio.sleep(0.01)
        return "hello"

    results = event_loop_runner.gather(hello(), hello(), hello())
    assert len(results) == 3
    assert all(r == "hello" for r in results)


def test_loop_state(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test that the loop is running and not the current loop."""
    loop = event_loop_runner.get_loop()
    assert loop.is_running()

    try:
        current = asyncio.get_running_loop()
    except RuntimeError:
        current = None

    assert current is None or current is not loop


def test_garbage_collection(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test that coroutines are properly garbage collected."""

    async def hello() -> str:
        await asyncio.sleep(0.01)
        return "hello"

    async_task = hello()
    weak_ref = weakref.ref(async_task)
    event_loop_runner.run(async_task)
    del async_task
    gc.collect()
    assert weak_ref() is None


def test_multiple_operations(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test multiple operations maintain loop consistency."""
    loop = event_loop_runner.get_loop()

    async def hello() -> str:
        await asyncio.sleep(0.01)
        return "hello"

    async def raises_exception() -> None:
        raise ValueError("test error")

    for _ in range(3):
        event_loop_runner.run(hello())
        assert event_loop_runner.get_loop() is loop

    with pytest.raises(ValueError):
        event_loop_runner.run(raises_exception())

    assert event_loop_runner.get_loop() is loop


def test_close_idempotent(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test that close method is idempotent."""
    event_loop_runner.close()
    event_loop_runner.close()


def test_run_with_non_coroutine(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test that run raises TypeError for non-coroutines."""
    with pytest.raises(
        TypeError, match="object str can't be used in 'await' expression"
    ):
        event_loop_runner.run("not a coro")  # type: ignore


def test_gather_with_exceptions(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test gather with return_exceptions=True."""

    async def hello() -> str:
        await asyncio.sleep(0.01)
        return "hello"

    async def raises_exception() -> None:
        raise ValueError("test error")

    results = event_loop_runner.gather(
        hello(),
        raises_exception(),
        return_exceptions=True,
    )
    assert len(results) == 2
    assert results[0] == "hello"
    assert isinstance(results[1], ValueError)


def test_run_timeout(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test timeout functionality in run method."""

    async def long_running() -> None:
        await asyncio.sleep(1)

    with pytest.raises(asyncio.TimeoutError):
        event_loop_runner.run(long_running(), timeout=0.01)


def test_schedule_after_close_raises(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test that scheduling after close raises RuntimeError."""
    event_loop_runner.close()
    loop = event_loop_runner.get_loop()
    assert loop.is_closed()
    with pytest.raises(RuntimeError):
        loop.call_soon(lambda: None)


def test_run_from_child_thread(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test running coroutines from child threads."""
    results: list[Any] = []

    async def hello() -> str:
        await asyncio.sleep(0.01)
        return "hello"

    def target() -> None:
        result = event_loop_runner.run(hello())
        results.append(result)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join()

    assert len(results) == 1
    assert results[0] == "hello"


def test_gather_empty(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test gather with no coroutines returns empty list."""
    results = event_loop_runner.gather()
    assert results == []


def test_run_with_nested_coroutine(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test run with a coroutine that awaits another coroutine."""

    async def inner() -> str:
        await asyncio.sleep(0.01)
        return "inner"

    async def outer() -> str:
        return await inner()

    result = event_loop_runner.run(outer())
    assert result == "inner"


def test_gather_with_various_return_types(
    event_loop_runner: EventLoopThreadRunner,
) -> None:
    """Test gather with coroutines returning different types."""

    async def coro_dict() -> dict[str, int]:
        return {"a": 1}

    async def coro_list() -> list[int]:
        return [1, 2, 3]

    async def coro_tuple() -> tuple[int, int]:
        return (1, 2)

    results = event_loop_runner.gather(coro_dict(), coro_list(), coro_tuple())
    assert results[0] == {"a": 1}
    assert results[1] == [1, 2, 3]
    assert results[2] == (1, 2)


def test_run_with_custom_exception(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test run with coroutine raising a custom exception."""

    class MyError(Exception):
        pass

    async def fail() -> Never:
        raise MyError("custom error")

    with pytest.raises(MyError, match="custom error"):
        event_loop_runner.run(fail())


def test_gather_with_multiple_exceptions(
    event_loop_runner: EventLoopThreadRunner,
) -> None:
    """Test gather with multiple coroutines raising different exceptions."""

    async def ok() -> str:
        return "ok"

    async def fail1() -> Never:
        raise ValueError("fail1")

    async def fail2() -> Never:
        raise KeyError("fail2")

    results = event_loop_runner.gather(ok(), fail1(), fail2(), return_exceptions=True)
    assert results[0] == "ok"
    assert isinstance(results[1], ValueError)
    assert isinstance(results[2], KeyError)


def test_run_with_cancelled_coroutine(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test run with coroutine that is cancelled."""

    async def cancellable() -> Never:
        raise asyncio.CancelledError()

    with pytest.raises((asyncio.CancelledError, concurrent.futures.CancelledError)):
        event_loop_runner.run(cancellable())


def test_gather_with_cancelled_coroutine(
    event_loop_runner: EventLoopThreadRunner,
) -> None:
    """Test gather with cancelled coroutine."""

    async def cancellable() -> Never:
        raise asyncio.CancelledError()

    results = event_loop_runner.gather(cancellable(), return_exceptions=True)
    assert isinstance(results[0], asyncio.CancelledError)


def test_run_with_timeout_zero(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test run with timeout=0 always times out."""

    async def sleeper() -> None:
        await asyncio.sleep(0.01)

    with pytest.raises(asyncio.TimeoutError):
        event_loop_runner.run(sleeper(), timeout=0)


def test_gather_large_data(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test gather with coroutines returning large data."""

    async def big() -> list[int]:
        return list(range(10000))

    results = event_loop_runner.gather(big(), big(), return_exceptions=False)
    assert all(isinstance(r, list) and len(r) == 10000 for r in results)
