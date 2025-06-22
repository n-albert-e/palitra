"""Tests for global functions: run, gather, shutdown_global_runner, is_runner_alive."""

import asyncio
import gc
import threading
from multiprocessing import Process
import pytest

from palitra import gather, is_runner_alive, run, shutdown_global_runner


def child_process() -> None:
    """Child process function for atexit test."""
    from palitra import EventLoopThreadRunner

    runner = EventLoopThreadRunner()
    loop = runner.get_loop()
    print("loop running:", loop.is_running())


class TestGlobalFunctions:
    """Test suite for global functions."""

    def test_high_level_run(self) -> None:
        """Test the global run function."""
        async def hello() -> str:
            await asyncio.sleep(0.01)
            return "hello"

        assert run(hello()) == "hello"

    def test_high_level_gather(self) -> None:
        """Test the global gather function."""
        async def hello() -> str:
            await asyncio.sleep(0.01)
            return "hello"

        results = gather(hello(), hello(), hello())
        assert len(results) == 3
        assert all(r == "hello" for r in results)

    def test_global_runner_lifecycle(self) -> None:
        """Test global runner lifecycle management."""
        shutdown_global_runner()
        assert not is_runner_alive()

        async def hello() -> str:
            await asyncio.sleep(0.01)
            return "hello"

        result = run(hello())
        assert result == "hello"
        assert is_runner_alive()

        results = gather(hello(), hello())
        assert results == ["hello", "hello"]
        assert is_runner_alive()

        shutdown_global_runner()
        assert not is_runner_alive()

        result2 = run(hello())
        assert result2 == "hello"
        assert is_runner_alive()

        shutdown_global_runner()

    def test_shutdown_is_idempotent_and_threadsafe(self) -> None:
        """Test that shutdown is idempotent and thread-safe."""
        shutdown_global_runner()
        assert not is_runner_alive()

        shutdown_global_runner()
        shutdown_global_runner()
        assert not is_runner_alive()

        async def hello() -> str:
            await asyncio.sleep(0.01)
            return "hello"

        def thread_target() -> None:
            run(hello())

        t = threading.Thread(target=thread_target)
        t.start()
        t.join()

        assert is_runner_alive()

        shutdown_global_runner()
        assert not is_runner_alive()

    def test_runner_garbage_collection_after_shutdown(self) -> None:
        """Test garbage collection behavior after shutdown."""
        shutdown_global_runner()
        
        async def hello() -> str:
            await asyncio.sleep(0.01)
            return "hello"

        run(hello())
        assert is_runner_alive()

        shutdown_global_runner()

        gc.collect()
        assert not is_runner_alive()

    def test_runner_atexit_behavior(self, capfd) -> None:
        """Test atexit behavior in child processes."""
        p = Process(target=child_process)
        p.start()
        p.join()
        out, err = capfd.readouterr()
        assert "RuntimeError: Event loop is closed" not in err
        assert "loop running: True" in out

    def test_run_after_shutdown_creates_new_runner(self) -> None:
        """Test that run after shutdown creates a new runner automatically."""
        shutdown_global_runner()
        assert not is_runner_alive()
        async def hello():
            return "hi"
        result = run(hello())
        assert result == "hi"
        assert is_runner_alive()

    def test_gather_after_shutdown_creates_new_runner(self) -> None:
        """Test that gather after shutdown creates a new runner automatically."""
        shutdown_global_runner()
        assert not is_runner_alive()
        async def hello():
            return "hi"
        results = gather(hello(), hello())
        assert results == ["hi", "hi"]
        assert is_runner_alive()

    def test_run_with_none_raises(self) -> None:
        """Test that run with None raises TypeError."""
        with pytest.raises(TypeError):
            run(None)  # type: ignore

    def test_gather_with_none_raises(self) -> None:
        """Test that gather with None raises TypeError."""
        with pytest.raises(TypeError):
            gather(None)  # type: ignore

    def test_gather_with_large_number_of_coroutines(self) -> None:
        """Test gather with a large number of coroutines."""
        async def hello():
            return 1
        results = gather(*[hello() for _ in range(100)])
        assert results == [1] * 100

    def test_gather_with_nested_gather(self) -> None:
        """Test gather with nested gather calls."""
        async def hello():
            await asyncio.sleep(0.01)
            return "hi"
        async def nested():
            return await asyncio.gather(hello(), hello())
        results = gather(nested(), hello())
        assert results[0] == ["hi", "hi"]
        assert results[1] == "hi"

    def test_gather_with_timeout(self) -> None:
        """Test gather with timeout argument."""
        async def sleeper():
            await asyncio.sleep(1)
        with pytest.raises(asyncio.TimeoutError):
            gather(sleeper(), timeout=0.01) 