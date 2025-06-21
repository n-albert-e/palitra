import asyncio
import gc
import threading
import weakref
from collections.abc import Generator
from multiprocessing import Process
from typing import Any, Never

import pytest
import uvloop

from palitra import (
    EventLoopThreadRunner,
    gather,
    is_runner_alive,
    run,
    shutdown_global_runner,
)


async def hello() -> str:
    await asyncio.sleep(0.01)
    return "hello"


async def raises_exception() -> Never:
    raise ValueError("test error")


@pytest.fixture(params=[asyncio.DefaultEventLoopPolicy, uvloop.EventLoopPolicy])
def event_loop_runner(
    request: pytest.FixtureRequest,
) -> Generator[EventLoopThreadRunner, None, None]:
    asyncio.set_event_loop_policy(request.param())
    runner = EventLoopThreadRunner()
    yield runner
    runner.close()


def test_loop_consistency(event_loop_runner: EventLoopThreadRunner) -> None:
    initial_loop = event_loop_runner.get_loop()
    event_loop_runner.run(hello())
    assert event_loop_runner.get_loop() is initial_loop


def test_exception_handling(event_loop_runner: EventLoopThreadRunner) -> None:
    with pytest.raises(ValueError, match="test error"):
        event_loop_runner.run(raises_exception())


def test_gather_operation(event_loop_runner: EventLoopThreadRunner) -> None:
    results = event_loop_runner.gather(hello(), hello(), hello())
    assert len(results) == 3
    assert all(r == "hello" for r in results)


def test_loop_state(event_loop_runner: EventLoopThreadRunner) -> None:
    loop = event_loop_runner.get_loop()
    assert loop.is_running()

    try:
        current = asyncio.get_running_loop()
    except RuntimeError:
        current = None

    assert current is None or current is not loop


def test_garbage_collection(event_loop_runner: EventLoopThreadRunner) -> None:
    async_task = hello()
    weak_ref = weakref.ref(async_task)
    event_loop_runner.run(async_task)
    del async_task
    gc.collect()
    assert weak_ref() is None


def test_multiple_operations(event_loop_runner: EventLoopThreadRunner) -> None:
    loop = event_loop_runner.get_loop()

    for _ in range(3):
        event_loop_runner.run(hello())
        assert event_loop_runner.get_loop() is loop

    with pytest.raises(ValueError):
        event_loop_runner.run(raises_exception())

    assert event_loop_runner.get_loop() is loop


def test_close_idempotent(event_loop_runner: EventLoopThreadRunner) -> None:
    event_loop_runner.close()
    event_loop_runner.close()


def test_run_with_non_coroutine(event_loop_runner: EventLoopThreadRunner) -> None:
    with pytest.raises(TypeError, match="Expected coroutine"):
        event_loop_runner.run("not a coro")  # type: ignore


def test_gather_with_exceptions(event_loop_runner: EventLoopThreadRunner) -> None:
    results = event_loop_runner.gather(
        hello(),
        raises_exception(),
        return_exceptions=True,
    )
    assert len(results) == 2
    assert results[0] == "hello"
    assert isinstance(results[1], ValueError)


def test_run_timeout(event_loop_runner: EventLoopThreadRunner) -> None:
    async def long_running() -> None:
        await asyncio.sleep(1)

    with pytest.raises(TimeoutError):
        event_loop_runner.run(long_running(), timeout=0.01)


def test_high_level_run() -> None:
    assert run(hello()) == "hello"


def test_high_level_gather() -> None:
    results = gather(hello(), hello(), hello())
    assert len(results) == 3
    assert all(r == "hello" for r in results)


def test_runner_atexit_behavior(capfd: pytest.CaptureFixture[str]) -> None:
    def child_process() -> None:
        from palitra import EventLoopThreadRunner

        runner = EventLoopThreadRunner()
        loop = runner.get_loop()
        print("loop running:", loop.is_running())

    p = Process(target=child_process)
    p.start()
    p.join()
    out, err = capfd.readouterr()
    assert "RuntimeError: Event loop is closed" not in err
    assert "loop running: True" in out


def test_schedule_after_close_raises(event_loop_runner: EventLoopThreadRunner) -> None:
    event_loop_runner.close()
    loop = event_loop_runner.get_loop()
    assert loop.is_closed()
    with pytest.raises(RuntimeError):
        loop.call_soon(lambda: None)


def test_run_from_child_thread(event_loop_runner: EventLoopThreadRunner) -> None:
    results: list[Any] = []

    def target() -> None:
        result = event_loop_runner.run(hello())
        results.append(result)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join()

    assert len(results) == 1
    assert results[0] == "hello"


def test_global_runner_lifecycle() -> None:
    shutdown_global_runner()
    assert not is_runner_alive()

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


def test_shutdown_is_idempotent_and_threadsafe() -> None:
    shutdown_global_runner()
    assert not is_runner_alive()

    shutdown_global_runner()
    shutdown_global_runner()
    assert not is_runner_alive()

    def thread_target() -> None:
        run(hello())

    t = threading.Thread(target=thread_target)
    t.start()
    t.join()

    assert is_runner_alive()

    shutdown_global_runner()
    assert not is_runner_alive()


def test_runner_garbage_collection_after_shutdown() -> None:
    shutdown_global_runner()
    run(hello())
    assert is_runner_alive()

    shutdown_global_runner()

    gc.collect()
    assert not is_runner_alive()
