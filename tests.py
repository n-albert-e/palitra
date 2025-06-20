import asyncio
import weakref

import pytest

from . import EventLoopThreadRunner


@pytest.fixture
def event_loop_runner():
    yield EventLoopThreadRunner


async def hello():
    await asyncio.sleep(0.01)
    return "hello"


async def raises_exception():
    raise ValueError("test error")


def test_loop_consistency(event_loop_runner):
    initial_loop = event_loop_runner.get_loop()
    event_loop_runner.run(hello())
    assert event_loop_runner.get_loop() is initial_loop


def test_exception_handling(event_loop_runner):
    with pytest.raises(ValueError, match="test error"):
        event_loop_runner.run(raises_exception())


def test_gather_operation(event_loop_runner):
    results = event_loop_runner.gather(hello(), hello(), hello())
    assert len(results) == 3
    assert all(r == "hello" for r in results)


def test_loop_state(event_loop_runner):
    loop = event_loop_runner.get_loop()
    assert loop.is_running()
    assert asyncio.get_event_loop() is not loop


def test_garbage_collection(event_loop_runner):
    async_task = hello()
    weak_ref = weakref.ref(async_task)
    event_loop_runner.run(async_task)
    del async_task
    import gc

    gc.collect()
    assert weak_ref() is None


def test_multiple_operations(event_loop_runner):
    loop = event_loop_runner.get_loop()

    for _ in range(3):
        event_loop_runner.run(hello())
        assert event_loop_runner.get_loop() is loop

    with pytest.raises(ValueError):
        event_loop_runner.run(raises_exception())

    assert event_loop_runner.get_loop() is loop
