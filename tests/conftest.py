from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine, Generator
from typing import NoReturn

import pytest

from palitra import EventLoopThreadRunner

event_loop_policies: list[type[asyncio.AbstractEventLoopPolicy]] = [
    asyncio.DefaultEventLoopPolicy
]
try:
    import uvloop  # type: ignore

    event_loop_policies.append(uvloop.EventLoopPolicy)
except ImportError:
    pass


async def hello() -> str:
    """Simple async function for testing."""
    await asyncio.sleep(0)
    return "hello"


async def raises_exception() -> NoReturn:
    """Async function that raises an exception for testing."""
    await asyncio.sleep(0)
    raise ValueError("test error")


async def long_running() -> None:
    await asyncio.sleep(1)


@pytest.fixture(params=event_loop_policies, scope="function")
def event_loop_runner(
    request: pytest.FixtureRequest,
) -> Generator[EventLoopThreadRunner, None, None]:
    """Fixture providing EventLoopThreadRunner with different event loop policies."""
    asyncio.set_event_loop_policy(request.param())
    runner = EventLoopThreadRunner()
    yield runner
    runner.close()


@pytest.fixture
def sample_coroutine() -> Callable[[], Coroutine[None, None, str]]:
    """Fixture providing sample coroutines for testing."""
    return hello


@pytest.fixture
def exception_coroutine() -> Callable[[], Coroutine[None, None, NoReturn]]:
    """Fixture providing a coroutine that raises an exception."""
    return raises_exception


@pytest.fixture
def long_running_coroutine() -> Callable[[], Coroutine[None, None, None]]:
    return long_running
