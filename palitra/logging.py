"""
Logging configuration for the palitra library using Loguru.

This module sets up a logger that behaves differently based on the
`PALITRA_ENV` environment variable:

- `development` (default): Logs are sent to the console (stderr) with a
  simple, colorful format. Log level is set to DEBUG.
- `production`: Logs are written to a file (`logs/palitra.log`) with
  rotation and compression. Log level is set to WARNING.

The logger is configured once upon the first import of this module.
"""
import os
import sys

from loguru import logger

# Remove the default handler to prevent duplicate logs.
logger.remove()

# Determine the environment and configure the logger accordingly.
env = os.getenv("PALITRA_ENV", "development").lower()

if env == "production":
    # Production logging: to a file, with rotation and higher log level.
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "palitra.log")

    logger.add(
        log_path,
        level="WARNING",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",  # New file when the size reaches 10 MB
        compression="zip", # Compress old log files
        enqueue=True,      # Make logging non-blocking
        backtrace=False,   # Do not show full stack traces
        diagnose=False,
    )
    logger.info("Logger configured for PRODUCTION environment.")
else:
    # Development logging: to the console, with a simpler format and lower log level.
    logger.add(
        sys.stderr,
        level="DEBUG",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    logger.info("Logger configured for DEVELOPMENT environment.")

# Export the configured logger for use in other modules.
__all__ = ["logger"] 