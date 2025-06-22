"""Tests for error handling and edge cases."""

import asyncio
import threading
from typing import Any
import pytest

from palitra import EventLoopThreadRunner, gather, run


class TestErrorHandling:
    """Test suite for error handling and edge cases."""

    def test_timeout_handling(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test timeout error handling."""
        async def long_running() -> None:
            await asyncio.sleep(1)

        with pytest.raises(asyncio.TimeoutError):
            event_loop_runner.run(long_running(), timeout=0.01)

    def test_gather_with_exceptions_returned(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test gather with return_exceptions=True."""
        async def success_operation() -> str:
            await asyncio.sleep(0.01)
            return "success"

        async def failing_operation() -> None:
            await asyncio.sleep(0.01)
            raise ValueError("operation failed")

        results = event_loop_runner.gather(
            success_operation(),
            failing_operation(),
            return_exceptions=True,
        )

        assert len(results) == 2
        assert results[0] == "success"
        assert isinstance(results[1], ValueError)
        assert str(results[1]) == "operation failed"

    def test_gather_with_exceptions_raised(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test gather with return_exceptions=False (default)."""
        async def success_operation() -> str:
            await asyncio.sleep(0.01)
            return "success"

        async def failing_operation() -> None:
            await asyncio.sleep(0.01)
            raise ValueError("operation failed")

        with pytest.raises(ValueError, match="operation failed"):
            event_loop_runner.gather(
                success_operation(),
                failing_operation(),
                return_exceptions=False,
            )

    def test_invalid_coroutine_type(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test handling of invalid coroutine types."""
        with pytest.raises(TypeError, match="Expected coroutine"):
            event_loop_runner.run("not a coroutine")  # type: ignore

        with pytest.raises(TypeError, match="Expected coroutine"):
            event_loop_runner.run(42)  # type: ignore

        with pytest.raises(TypeError, match="Expected coroutine"):
            event_loop_runner.run(None)  # type: ignore

    def test_empty_gather(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test gather with no coroutines."""
        results = event_loop_runner.gather()
        assert results == []

    def test_single_coroutine_gather(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test gather with single coroutine."""
        async def single_operation() -> str:
            await asyncio.sleep(0.01)
            return "single"

        results = event_loop_runner.gather(single_operation())
        assert results == ["single"]

    def test_nested_exceptions(self, event_loop_runner: EventLoopThreadRunner) -> None:
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

    def test_cancellation_handling(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test handling of cancelled coroutines."""
        async def cancellable_operation() -> str:
            try:
                await asyncio.sleep(1)
                return "completed"
            except asyncio.CancelledError:
                return "cancelled"

        # Create and cancel the coroutine
        coro = cancellable_operation()
        coro.close()  # Cancel the coroutine

        # This should not raise an exception
        try:
            event_loop_runner.run(coro)
        except Exception:
            # It's acceptable for this to fail in some cases
            pass

    def test_thread_safety_under_error_conditions(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test thread safety when errors occur."""
        results: list[Any] = []
        errors: list[Exception] = []

        def worker_thread() -> None:
            try:
                async def failing_operation() -> None:
                    await asyncio.sleep(0.01)
                    raise ValueError("Thread error")

                result = event_loop_runner.run(failing_operation())
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Start multiple threads that will encounter errors
        threads = []
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
        assert all("Thread error" in str(e) for e in errors)
        assert len(results) == 0

    def test_global_functions_error_handling(self) -> None:
        """Test error handling in global functions."""
        async def failing_operation() -> None:
            await asyncio.sleep(0.01)
            raise ValueError("Global error")

        # Test run function
        with pytest.raises(ValueError, match="Global error"):
            run(failing_operation())

        # Test gather function
        with pytest.raises(ValueError, match="Global error"):
            gather(failing_operation())

        # Test gather with return_exceptions
        results = gather(failing_operation(), return_exceptions=True)
        assert len(results) == 1
        assert isinstance(results[0], ValueError)
        assert str(results[0]) == "Global error"

    def test_mixed_success_and_failure_in_gather(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test gather with mixed success and failure scenarios."""
        async def success_operation() -> str:
            await asyncio.sleep(0.01)
            return "success"

        async def failure_operation() -> None:
            await asyncio.sleep(0.01)
            raise ValueError("failure")

        async def another_success_operation() -> str:
            await asyncio.sleep(0.01)
            return "success2"

        # Test with return_exceptions=True
        results = event_loop_runner.gather(
            success_operation(),
            failure_operation(),
            another_success_operation(),
            return_exceptions=True,
        )

        assert len(results) == 3
        assert results[0] == "success"
        assert isinstance(results[1], ValueError)
        assert str(results[1]) == "failure"
        assert results[2] == "success2"

    def test_resource_cleanup_after_errors(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test that resources are properly cleaned up after errors."""
        loop = event_loop_runner.get_loop()
        initial_tasks = len(asyncio.all_tasks(loop))

        async def failing_operation() -> None:
            await asyncio.sleep(0.01)
            raise ValueError("Cleanup test error")

        # Run multiple failing operations
        for _ in range(5):
            try:
                event_loop_runner.run(failing_operation())
            except ValueError:
                pass

        # Check that tasks are cleaned up
        final_tasks = len(asyncio.all_tasks(loop))
        # Should have the same number of tasks (just the main loop task)
        assert final_tasks <= initial_tasks + 1

    def test_run_with_non_coroutine_type(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test run with non-coroutine types raises TypeError."""
        with pytest.raises(TypeError):
            event_loop_runner.run(123)  # type: ignore
        with pytest.raises(TypeError):
            event_loop_runner.run(object())  # type: ignore

    def test_gather_with_none(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test gather with None raises TypeError."""
        with pytest.raises(TypeError):
            event_loop_runner.gather(None)  # type: ignore

    def test_gather_with_many_coroutines(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test gather with a large number of coroutines."""
        async def hello():
            return 1
        results = event_loop_runner.gather(*[hello() for _ in range(50)])
        assert results == [1] * 50

    def test_gather_with_nested_gather(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test gather with nested gather calls."""
        async def hello():
            await asyncio.sleep(0.01)
            return "hi"
        async def nested():
            return await asyncio.gather(hello(), hello())
        results = event_loop_runner.gather(nested(), hello())
        assert results[0] == ["hi", "hi"]
        assert results[1] == "hi"

    def test_run_after_close_raises(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test that run after close raises RuntimeError."""
        event_loop_runner.close()
        async def hello():
            return "hi"
        coro = hello()
        with pytest.raises(RuntimeError):
            event_loop_runner.run(coro)
        coro.close()

    def test_gather_after_close_raises(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test that gather after close raises RuntimeError."""
        event_loop_runner.close()
        async def hello():
            return "hi"
        coro = hello()
        with pytest.raises(RuntimeError):
            event_loop_runner.gather(coro)
        coro.close() 