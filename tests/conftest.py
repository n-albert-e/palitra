"""Common test fixtures and configuration for palitra tests."""

import asyncio
from collections.abc import Coroutine, Generator

import pytest

from palitra import EventLoopThreadRunner

# Try to import uvloop, but make it optional
try:
    import uvloop
    UVLOOP_AVAILABLE = True
except ImportError:
    UVLOOP_AVAILABLE = False


async def hello() -> str:
    """Simple async function for testing."""
    await asyncio.sleep(0.01)
    return "hello"


async def raises_exception() -> None:
    """Async function that raises an exception for testing."""
    raise ValueError("test error")


# Create event loop policies for testing
event_loop_policies = [asyncio.DefaultEventLoopPolicy]
if UVLOOP_AVAILABLE:
    event_loop_policies.append(uvloop.EventLoopPolicy)


@pytest.fixture(params=event_loop_policies)
def event_loop_runner(
    request: pytest.FixtureRequest,
) -> Generator[EventLoopThreadRunner, None, None]:
    """Fixture providing EventLoopThreadRunner with different event loop policies."""
    asyncio.set_event_loop_policy(request.param())
    runner = EventLoopThreadRunner()
    yield runner
    runner.close()


@pytest.fixture
def sample_coroutines() -> tuple:
    """Fixture providing sample coroutines for testing."""
    return (hello(), hello(), hello())


@pytest.fixture
def exception_coroutine() -> Coroutine[None, None, None]:
    """Fixture providing a coroutine that raises an exception."""
    return raises_exception() 