"""Logging infrastructure module for Covert.

This module provides logging setup with configurable levels, formats,
and output destinations (file and console). It uses Rich for enhanced
terminal output when available.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

from covert.config import LoggingConfig
from covert.exceptions import ConfigError


def setup_logging(
    logging_config: LoggingConfig,
    verbose_level: int = 0,
) -> logging.Logger:
    """Set up logging with the specified configuration.

    Args:
        logging_config: Logging configuration object.
        verbose_level: Additional verbosity level (0 = normal, 1 = verbose, 2 = debug).

    Returns:
        Logger: Configured root logger.

    Raises:
        ConfigError: If log file cannot be created.
    """
    # Determine the effective log level
    level = _get_log_level(logging_config.level, verbose_level)

    # Get root logger
    logger = logging.getLogger("covert")
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Set up formatters
    if logging_config.format == "json":
        formatter: logging.Formatter = JsonFormatter()
    else:
        formatter = _get_formatter(logging_config.format)

    # Set up console handler
    if logging_config.console:
        console_handler = _get_console_handler(logging_config.format, level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Set up file handler
    if logging_config.file:
        file_handler = _get_file_handler(logging_config.file, level)
        if file_handler:
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def _get_log_level(config_level: str, verbose_level: int) -> int:
    """Determine the effective log level.

    Args:
        config_level: Configured log level.
        verbose_level: Additional verbosity level from command line.

    Returns:
        int: Logging level constant.
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    base_level = level_map.get(config_level.upper(), logging.INFO)

    # Adjust based on verbose level
    if verbose_level >= 2:
        return logging.DEBUG
    elif verbose_level >= 1:
        return min(base_level, logging.DEBUG)

    return base_level


def _get_formatter(format_type: str) -> logging.Formatter:
    """Get a log formatter based on the format type.

    Args:
        format_type: Format type ("simple" or "detailed").

    Returns:
        logging.Formatter: Configured formatter.
    """
    if format_type == "simple":
        return logging.Formatter("%(levelname)s: %(message)s")
    else:  # detailed
        return logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def _get_console_handler(format_type: str, level: int) -> logging.Handler:
    """Get a console handler based on the format type.

    Args:
        format_type: Format type ("simple", "detailed", or "json").
        level: Log level for the handler.

    Returns:
        logging.Handler: Configured console handler.
    """
    if format_type == "json":
        handler = logging.StreamHandler(sys.stdout)
    else:
        # Use Rich for enhanced terminal output
        console = Console(stderr=True)
        handler = RichHandler(  # type: ignore[assignment]
            console=console,
            show_time=format_type == "detailed",
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )

    handler.setLevel(level)
    return handler


def _get_file_handler(file_path: str, level: int) -> Optional[logging.Handler]:
    """Get a file handler for logging to a file.

    Args:
        file_path: Path to the log file.
        level: Log level for the handler.

    Returns:
        Optional[logging.Handler]: Configured file handler, or None if creation fails.

    Raises:
        ConfigError: If log file directory cannot be created.
    """
    path = Path(file_path)

    try:
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ConfigError(f"Failed to create log directory: {e}") from e

    try:
        handler = logging.FileHandler(path, mode="a", encoding="utf-8")
        handler.setLevel(level)
        return handler
    except OSError as e:
        # Log to stderr but don't fail the application
        print(f"Warning: Failed to create log file {file_path}: {e}", file=sys.stderr)
        return None


class JsonFormatter(logging.Formatter):
    """JSON log formatter for structured logging.

    Formats log records as JSON objects for easier parsing by log
    aggregation tools and monitoring systems.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format.

        Returns:
            str: JSON-formatted log message.
        """
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        Logger: Logger instance.
    """
    return logging.getLogger(f"covert.{name}")
