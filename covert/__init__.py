"""Covert - Safe package updater for Python/Django projects.

Covert provides automated, safe dependency updates for Python projects with
the following core capabilities:
- Detect outdated packages using pip
- Update packages one-by-one in a controlled manner
- Run automated tests after each update to verify system integrity
- Automatically roll back updates if tests fail
- Create backups before making any changes
- Support dry-run mode for simulation without actual changes
"""

__version__ = "1.1.0"
__author__ = "iodevs-net"
__license__ = "MIT"

# Public API exports
from covert.config import (
    BackupConfig,
    Config,
    LoggingConfig,
    ProjectConfig,
    SecurityConfig,
    TestingConfig,
    UpdatesConfig,
    load_config,
    save_config,
    validate_config,
)
from covert.exceptions import (
    BackupError,
    ConfigError,
    CovertError,
    PipError,
    TestError,
    UpdateError,
    ValidationError,
)
from covert.logger import get_logger, setup_logging

__all__ = [
    # Version
    "__version__",
    # Config
    "Config",
    "ProjectConfig",
    "TestingConfig",
    "UpdatesConfig",
    "BackupConfig",
    "LoggingConfig",
    "SecurityConfig",
    "load_config",
    "save_config",
    "validate_config",
    # Exceptions
    "CovertError",
    "ConfigError",
    "UpdateError",
    "TestError",
    "BackupError",
    "PipError",
    "ValidationError",
    # Logger
    "setup_logging",
    "get_logger",
]
