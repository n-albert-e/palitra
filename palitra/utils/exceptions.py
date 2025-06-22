"""
Custom exception types for the palitra library.
"""

class PalitraError(Exception):
    """Base exception class for all palitra-specific errors."""
    pass


class DeadlockError(PalitraError, RuntimeError):
    """
    Raised when an operation would cause a deadlock.

    This typically occurs when `run()` is called from within the runner's
    own event loop thread, which is not allowed.
    """
    pass


class RunnerError(PalitraError, RuntimeError):
    """
    Raised for general errors related to the runner's state.

    For example, this is raised if an operation is attempted on a runner
    that has already been closed.
    """
    pass 