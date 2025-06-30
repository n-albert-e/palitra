"""Tests for error handling and edge cases."""

import asyncio
import contextlib
import sys
import threading
from collections.abc import Callable, Coroutine
from typing import Any, NoReturn, TypeVar

import pytest

from palitra import EventLoopThreadRunner, gather, run

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec
T = TypeVar("T")
P = ParamSpec("P")


def test_timeout_handling(
    event_loop_runner: EventLoopThreadRunner,
    long_running_coroutine: Callable[[], Coroutine[None, None, str]],
) -> None:
    """Test timeout error handling."""
    with pytest.raises(asyncio.TimeoutError):
        event_loop_runner.run(long_running_coroutine(), timeout=0.01)


def test_gather_with_exceptions_returned(
    event_loop_runner: EventLoopThreadRunner,
    exception_coroutine: Callable[[], Coroutine[None, None, NoReturn]],
    sample_coroutine: Callable[[], Coroutine[None, None, str]],
) -> None:
    """Test gather with return_exceptions=True."""

    results = event_loop_runner.gather(
        sample_coroutine(),
        exception_coroutine(),
        return_exceptions=True,
    )

    assert len(results) == 2
    assert results[0] == "hello"
    assert isinstance(results[1], ValueError)
    assert str(results[1]) == "test error"


def test_gather_with_exceptions_raised(
    event_loop_runner: EventLoopThreadRunner,
    exception_coroutine: Callable[[], Coroutine[None, None, NoReturn]],
    sample_coroutine: Callable[[], Coroutine[None, None, str]],
) -> None:
    """Test gather with return_exceptions=False (default)."""

    with pytest.raises(ValueError, match="test error"):
        event_loop_runner.gather(
            sample_coroutine(),
            exception_coroutine(),
            return_exceptions=False,
        )


def test_invalid_coroutine_type(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test handling of invalid coroutine types."""
    with pytest.raises(
        TypeError,
        match=(
            r"(object str can't be used in 'await' expression)"
            r"|"
            r"('str' object can't be awaited)"
        ),
    ):
        event_loop_runner.run("not a coroutine")  # type: ignore

    with pytest.raises(
        TypeError,
        match=(
            r"(object int can't be used in 'await' expression)"
            r"|"
            r"('int' object can't be awaited)"
        ),
    ):
        event_loop_runner.run(42)  # type: ignore

    with pytest.raises(
        TypeError,
        match=(
            r"(object NoneType can't be used in 'await' expression)"
            r"|"
            r"('NoneType' object can't be awaited)"
        ),
    ):
        event_loop_runner.run(None)  # type: ignore


def test_empty_gather(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test gather with no coroutines."""
    results = event_loop_runner.gather()
    assert results == []


def test_single_coroutine_gather(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test gather with single coroutine."""

    async def single_operation() -> str:
        await asyncio.sleep(0.01)
        return "single"

    results = event_loop_runner.gather(single_operation())
    assert results == ["single"]


def test_nested_exceptions(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test handling of nested exceptions."""

    async def outer_operation() -> None:
        try:
            await inner_operation()
        except ValueError as e:
            raise RuntimeError(f"Wrapped: {e}") from e

    async def inner_operation() -> None:
        await asyncio.sleep(0.01)
        raise ValueError("Inner error")

    with pytest.raises(RuntimeError, match="Wrapped: Inner error"):
        event_loop_runner.run(outer_operation())


def test_cancellation_handling(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test handling of cancelled coroutines."""

    async def cancellable_operation() -> str:
        try:
            await asyncio.sleep(1)
            return "completed"
        except asyncio.CancelledError:
            return "cancelled"

    coro = cancellable_operation()
    coro.close()

    with pytest.raises(RuntimeError, match="cannot reuse already awaited coroutine"):
        event_loop_runner.run(coro)


def test_thread_safety_under_error_conditions(
    event_loop_runner: EventLoopThreadRunner,
    exception_coroutine: Callable[[], Coroutine[None, None, NoReturn]],
) -> None:
    """Test thread safety when errors occur."""
    results: list[Any] = []
    errors: list[Exception] = []

    def worker_thread() -> None:
        try:
            result: NoReturn = event_loop_runner.run(exception_coroutine())
            results.append(result)
        except Exception as e:
            errors.append(e)

    # Start multiple threads that will encounter errors
    threads: list[threading.Thread] = []
    for _ in range(3):
        thread = threading.Thread(target=worker_thread)
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # All threads should have encountered errors
    assert len(errors) == 3
    assert all(isinstance(e, ValueError) for e in errors)
    assert all("test error" in str(e) for e in errors)
    assert len(results) == 0


def test_global_functions_error_handling(
    exception_coroutine: Callable[[], Coroutine[None, None, NoReturn]],
) -> None:
    """Test error handling in global functions."""

    # Test run function
    with pytest.raises(ValueError, match="test error"):
        run(exception_coroutine())

    # Test gather function
    with pytest.raises(ValueError, match="test error"):
        gather(exception_coroutine())

    # Test gather with return_exceptions
    results = gather(exception_coroutine(), return_exceptions=True)
    assert len(results) == 1
    assert isinstance(results[0], ValueError)
    assert str(results[0]) == "test error"


def test_mixed_success_and_failure_in_gather(
    event_loop_runner: EventLoopThreadRunner,
) -> None:
    """Test gather with mixed success and failure scenarios."""

    async def sample_coroutine() -> str:
        await asyncio.sleep(0.01)
        return "success"

    async def failure_operation() -> None:
        await asyncio.sleep(0.01)
        raise ValueError("failure")

    async def another_sample_coroutine() -> str:
        await asyncio.sleep(0.01)
        return "success2"

    # Test with return_exceptions=True
    results = event_loop_runner.gather(
        sample_coroutine(),
        failure_operation(),
        another_sample_coroutine(),
        return_exceptions=True,
    )

    assert len(results) == 3
    assert results[0] == "success"
    assert isinstance(results[1], ValueError)
    assert str(results[1]) == "failure"
    assert results[2] == "success2"


def test_resource_cleanup_after_errors(
    event_loop_runner: EventLoopThreadRunner,
    exception_coroutine: Callable[[], Coroutine[None, None, NoReturn]],
) -> None:
    """Test that resources are properly cleaned up after errors."""
    loop = event_loop_runner.get_loop()
    initial_tasks = len(asyncio.all_tasks(loop))

    # Run multiple failing operations
    for _ in range(5):
        with contextlib.suppress(ValueError):
            event_loop_runner.run(exception_coroutine())

    # Check that tasks are cleaned up
    final_tasks = len(asyncio.all_tasks(loop))
    # Should have the same number of tasks (just the main loop task)
    assert final_tasks <= initial_tasks + 1


def test_gather_with_none(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test gather with None raises TypeError."""
    with pytest.raises(
        TypeError, match=r"An asyncio.Future, a coroutine or an awaitable is required"
    ):
        event_loop_runner.gather(None)  # type: ignore


def test_gather_with_many_coroutines(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test gather with a large number of coroutines."""

    async def hello() -> int:
        await asyncio.sleep(0)
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
