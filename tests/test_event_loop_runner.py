"""Tests for EventLoopThreadRunner class."""

import asyncio
import threading
from collections.abc import Coroutine
from typing import Any, Callable

import pytest

from palitra import EventLoopThreadRunner


def test_loop_consistency(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test that the same loop instance is returned consistently."""
    initial_loop = event_loop_runner.get_loop()
    event_loop_runner.run(asyncio.sleep(0.01))
    assert event_loop_runner.get_loop() is initial_loop


def test_gather_operation(
    event_loop_runner: EventLoopThreadRunner,
    sample_coroutine: Callable[[], Coroutine[None, None, str]],
) -> None:
    """Test gather method with multiple coroutines."""

    results = event_loop_runner.gather(
        sample_coroutine(), sample_coroutine(), sample_coroutine()
    )
    assert len(results) == 3
    assert all(r == "hello" for r in results)


def test_loop_state(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test that the loop is running and not the current loop."""
    loop = event_loop_runner.get_loop()
    assert loop.is_running()

    with pytest.raises(RuntimeError):
        asyncio.get_running_loop()


def test_close_idempotent(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test that close method is idempotent."""
    event_loop_runner.close()
    event_loop_runner.close()


def test_run_from_child_thread(
    event_loop_runner: EventLoopThreadRunner,
    sample_coroutine: Callable[[], Coroutine[None, None, str]],
) -> None:
    """Test running coroutines from child threads."""
    results: list[Any] = []

    def target() -> None:
        result = event_loop_runner.run(sample_coroutine())
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


def test_run_with_nested_coroutine(
    event_loop_runner: EventLoopThreadRunner,
    sample_coroutine: Callable[[], Coroutine[None, None, str]],
) -> None:
    """Test run with a coroutine that awaits another coroutine."""

    async def outer() -> str:
        return await sample_coroutine()

    result = event_loop_runner.run(outer())
    assert result == "hello"


def test_gather_large_data(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test gather with coroutines returning large data."""

    async def big() -> list[int]:
        return list(range(10000))

    results = event_loop_runner.gather(big(), big(), return_exceptions=False)
    assert all(isinstance(r, list) and len(r) == 10000 for r in results)


def test_gather_with_many_coroutines(
    event_loop_runner: EventLoopThreadRunner,
    sample_coroutine: Callable[[], Coroutine[None, None, str]],
) -> None:
    """Test gather with a large number of coroutines."""

    results = event_loop_runner.gather(*[sample_coroutine() for _ in range(500)])
    assert results == ["hello"] * 500


def test_gather_with_nested_gather(
    event_loop_runner: EventLoopThreadRunner,
    sample_coroutine: Callable[[], Coroutine[None, None, str]],
) -> None:
    """Test gather with nested gather calls."""

    async def nested() -> tuple[str, str]:
        return await asyncio.gather(sample_coroutine(), sample_coroutine())

    results = event_loop_runner.gather(nested(), sample_coroutine())
    assert results[0] == ["hello", "hello"]
    assert results[1] == "hello"
