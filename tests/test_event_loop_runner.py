"""Tests for EventLoopThreadRunner class."""

import asyncio
import threading
from typing import Any

import pytest

from palitra import EventLoopThreadRunner


def test_loop_consistency(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test that the same loop instance is returned consistently."""
    initial_loop = event_loop_runner.get_loop()
    event_loop_runner.run(asyncio.sleep(0.01))
    assert event_loop_runner.get_loop() is initial_loop


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


def test_gather_with_many_coroutines(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test gather with a large number of coroutines."""

    async def hello() -> int:
        return 1

    results = event_loop_runner.gather(*[hello() for _ in range(500)])
    assert results == [1] * 500


def test_gather_with_nested_gather(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test gather with nested gather calls."""

    async def hello() -> str:
        await asyncio.sleep(0.01)
        return "hi"

    async def nested() -> tuple[str, str]:
        return await asyncio.gather(hello(), hello())

    results = event_loop_runner.gather(nested(), hello())
    assert results[0] == ["hi", "hi"]
    assert results[1] == "hi"
