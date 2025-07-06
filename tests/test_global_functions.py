"""Tests for global functions: run, gather, shutdown_global_runner, is_runner_alive."""

import asyncio
import gc
import sys
import threading
from collections.abc import Callable, Coroutine
from multiprocessing import Process
from typing import TypeVar, Union

import pytest

from palitra import gather, is_runner_alive, run, shutdown_global_runner

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

T = TypeVar("T")
P = ParamSpec("P")


def test_high_level_run(
    sample_coroutine: Callable[[], Coroutine[None, None, str]],
) -> None:
    """Test the global run function."""
    assert run(sample_coroutine()) == "hello"


def test_high_level_gather(
    sample_coroutine: Callable[[], Coroutine[None, None, str]],
) -> None:
    """Test the global gather function."""
    results = gather(sample_coroutine(), sample_coroutine(), sample_coroutine())
    assert len(results) == 3
    assert all(r == "hello" for r in results)


def test_global_runner_lifecycle(
    sample_coroutine: Callable[[], Coroutine[None, None, str]],
) -> None:
    """Test global runner lifecycle management."""
    shutdown_global_runner()
    assert not is_runner_alive()

    result = run(sample_coroutine())
    assert result == "hello"
    assert is_runner_alive()

    results = gather(sample_coroutine(), sample_coroutine())
    assert results == ["hello", "hello"]
    assert is_runner_alive()

    shutdown_global_runner()
    assert not is_runner_alive()

    result2 = run(sample_coroutine())
    assert result2 == "hello"
    assert is_runner_alive()

    shutdown_global_runner()


def test_shutdown_is_idempotent_and_threadsafe(
    sample_coroutine: Callable[[], Coroutine[None, None, str]],
) -> None:
    """Test that shutdown is idempotent and thread-safe."""
    shutdown_global_runner()
    assert not is_runner_alive()

    shutdown_global_runner()
    shutdown_global_runner()
    assert not is_runner_alive()

    def thread_target() -> None:
        run(sample_coroutine())

    t = threading.Thread(target=thread_target)
    t.start()
    t.join()

    assert is_runner_alive()

    shutdown_global_runner()
    assert not is_runner_alive()


def test_runner_garbage_collection_after_shutdown(
    sample_coroutine: Callable[[], Coroutine[None, None, str]],
) -> None:
    """Test garbage collection behavior after shutdown."""
    shutdown_global_runner()

    run(sample_coroutine())
    assert is_runner_alive()

    shutdown_global_runner()

    gc.collect()
    assert not is_runner_alive()


def test_runner_garbage_collection_during_execution() -> None:
    """Test garbage collection behavior triggered during execution."""

    async def sample_coroutine() -> str:
        await asyncio.sleep(0.01)
        gc.collect()
        return "hello"

    run(sample_coroutine())
    assert is_runner_alive()


def test_multiple_gc_collect_during_execution() -> None:
    """Test multiple garbage collections during coroutine execution."""
    collected = 0

    async def task() -> int:
        nonlocal collected
        for _ in range(3):
            await asyncio.sleep(0.01)
            gc.collect()
            collected += 1
        return collected

    result = run(task())
    assert result == 3
    assert is_runner_alive()


def test_gc_collect_with_exception_handling() -> None:
    """Test gc.collect() behavior when exceptions occur."""

    async def failing_task() -> Union[str, None]:
        try:
            await asyncio.sleep(0.01)
            gc.collect()
            raise ValueError("test error")
        except ValueError:
            gc.collect()  # Collect during exception handling
            return "handled"

    result = run(failing_task())
    assert result == "handled"
    assert is_runner_alive()


def test_nested_gc_collect_in_tasks() -> None:
    """Test nested garbage collection in multiple tasks."""

    async def child_task() -> str:
        await asyncio.sleep(0.01)
        gc.collect()
        return "child"

    async def parent_task() -> str:
        t = asyncio.create_task(child_task())
        gc.collect()
        result = await t
        gc.collect()
        return f"parent-{result}"

    result = run(parent_task())
    assert result == "parent-child"
    assert is_runner_alive()


def test_gc_collect_with_complex_object_graph() -> None:
    """Test gc.collect() with circular references in task."""

    class Node:
        def __init__(self) -> None:
            self.ref: Union[None, Node] = None

    async def task() -> bool:
        # Create circular reference
        a = Node()
        b = Node()
        a.ref = b
        b.ref = a
        await asyncio.sleep(0.01)
        del a, b
        collected = gc.collect()
        return collected > 0  # Expect some objects were collected

    result = run(task())
    assert result is True
    assert is_runner_alive()


def child_process() -> None:
    """Child process function for atexit test."""
    from palitra import EventLoopThreadRunner

    runner = EventLoopThreadRunner()
    loop = runner.get_loop()
    print("loop running:", loop.is_running())


@pytest.mark.xfail(
    sys.platform == "win32" and not getattr(sys, "_is_gil_enabled", lambda: True)(),
    reason="Freethreading is experimental, idk how to debug this",
)  # FIXME: how to debug this...
def test_runner_atexit_behavior(capfd: pytest.CaptureFixture[str]) -> None:
    """Test atexit behavior in child processes."""

    p = Process(target=child_process)
    p.start()
    p.join()
    out, err = capfd.readouterr()
    assert "RuntimeError" not in err
    assert "loop running: True" in out


def test_run_after_shutdown_creates_new_runner(
    sample_coroutine: Callable[[], Coroutine[None, None, str]],
) -> None:
    """Test that run after shutdown creates a new runner automatically."""
    shutdown_global_runner()
    assert not is_runner_alive()

    result = run(sample_coroutine())
    assert result == "hello"
    assert is_runner_alive()


def test_gather_after_shutdown_creates_new_runner(
    sample_coroutine: Callable[[], Coroutine[None, None, str]],
) -> None:
    """Test that gather after shutdown creates a new runner automatically."""
    shutdown_global_runner()
    assert not is_runner_alive()

    results = gather(sample_coroutine(), sample_coroutine())
    assert results == ["hello", "hello"]
    assert is_runner_alive()
