"""
High-level API for the palitra library.

This package provides convenient functions for running async code from sync context.
"""

from .singleton import run, gather, shutdown_global_runner, is_runner_alive

__all__ = ["run", "gather", "shutdown_global_runner", "is_runner_alive"] 