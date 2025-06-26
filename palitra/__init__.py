"""A lightweight bridge for running async code from a sync context."""
from __future__ import annotations

from .utils.exceptions import DeadlockError, PalitraError, RunnerError
from .core.runner import EventLoopThreadRunner
from .api.singleton import (
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
