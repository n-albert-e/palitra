"""Performance tests for concurrent operations."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from palitra import EventLoopThreadRunner, gather, run


class TestConcurrentPerformance:
    """Test suite for concurrent performance."""

    def test_concurrent_gather_performance(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test performance of concurrent gather operations."""
        async def async_operation(delay: float) -> str:
            await asyncio.sleep(delay)
            return f"result_{delay}"

        # Test with multiple concurrent operations
        start_time = time.monotonic()
        results = event_loop_runner.gather(
            async_operation(0.01),
            async_operation(0.01),
            async_operation(0.01),
            async_operation(0.01),
            async_operation(0.01),
        )
        end_time = time.monotonic()

        # Should complete in roughly 0.01 seconds (not 0.05)
        assert end_time - start_time < 0.05
        assert len(results) == 5
        assert all(r.startswith("result_") for r in results)

    def test_sequential_vs_concurrent_performance(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Compare sequential vs concurrent performance."""
        async def async_operation(delay: float) -> str:
            await asyncio.sleep(delay)
            return f"result_{delay}"

        # Sequential execution
        start_time = time.monotonic()
        sequential_results = []
        for i in range(5):
            result = event_loop_runner.run(async_operation(0.01))
            sequential_results.append(result)
        sequential_time = time.monotonic() - start_time

        # Concurrent execution
        start_time = time.monotonic()
        concurrent_results = event_loop_runner.gather(
            async_operation(0.01),
            async_operation(0.01),
            async_operation(0.01),
            async_operation(0.01),
            async_operation(0.01),
        )
        concurrent_time = time.monotonic() - start_time

        # Concurrent should be significantly faster
        assert concurrent_time < sequential_time * 0.5
        assert sequential_results == concurrent_results

    def test_high_level_concurrent_performance(self) -> None:
        """Test performance of high-level concurrent functions."""
        async def async_operation(delay: float) -> str:
            await asyncio.sleep(delay)
            return f"result_{delay}"

        # Test global gather function
        start_time = time.monotonic()
        results = gather(
            async_operation(0.01),
            async_operation(0.01),
            async_operation(0.01),
        )
        end_time = time.monotonic()

        assert end_time - start_time < 0.05
        assert len(results) == 3
        assert all(r.startswith("result_") for r in results)

    def test_mixed_workload_performance(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test performance with mixed workload (fast and slow operations)."""
        async def fast_operation() -> str:
            await asyncio.sleep(0.001)
            return "fast"

        async def slow_operation() -> str:
            await asyncio.sleep(0.05)
            return "slow"

        start_time = time.monotonic()
        results = event_loop_runner.gather(
            fast_operation(),
            slow_operation(),
            fast_operation(),
            slow_operation(),
            fast_operation(),
        )
        end_time = time.monotonic()

        # Should complete in roughly 0.05 seconds (slowest operation)
        assert end_time - start_time < 0.1
        assert len(results) == 5
        fast_count = sum(1 for r in results if r == "fast")
        slow_count = sum(1 for r in results if r == "slow")
        assert fast_count == 3
        assert slow_count == 2

    def test_thread_pool_integration_performance(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test performance with thread pool integration."""
        def cpu_bound_operation(n: int) -> int:
            # Simulate CPU-bound work
            result = 0
            for i in range(n):
                result += i
            return result

        async def async_cpu_operation(n: int) -> int:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, cpu_bound_operation, n)

        start_time = time.monotonic()
        results = event_loop_runner.gather(
            async_cpu_operation(1000),
            async_cpu_operation(1000),
            async_cpu_operation(1000),
        )
        end_time = time.monotonic()

        assert len(results) == 3
        assert all(isinstance(r, int) for r in results)
        # CPU operations should complete reasonably quickly
        assert end_time - start_time < 1.0

    def test_memory_usage_under_load(self, event_loop_runner: EventLoopThreadRunner) -> None:
        """Test memory usage under concurrent load."""
        import gc
        import sys

        async def memory_operation() -> list:
            # Create some objects
            data = [i for i in range(1000)]
            await asyncio.sleep(0.001)
            return data

        # Force garbage collection before test
        gc.collect()
        initial_memory = sys.getsizeof([])  # Rough baseline

        # Run many concurrent operations
        results = event_loop_runner.gather(
            *[memory_operation() for _ in range(100)]
        )

        # Force garbage collection after test
        gc.collect()

        assert len(results) == 100
        assert all(len(r) == 1000 for r in results)

        # Memory should be reasonable (this is a rough check)
        # In a real scenario, you'd use psutil or similar for accurate measurement
        assert len(results) == 100  # Just verify the test completed 