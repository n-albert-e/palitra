"""A lightweight bridge for running async code from a sync context."""
from __future__ import annotations

from .exceptions import DeadlockError, PalitraError, RunnerError
from .runner import EventLoopThreadRunner
from .singleton import (
    gather,
    is_runner_alive,
    run,
    shutdown_global_runner,
)

__all__ = (
    "EventLoopThreadRunner",
    "PalitraError",
    "RunnerError",
    "DeadlockError",
    "gather",
    "is_runner_alive",
    "run",
    "shutdown_global_runner",
)
