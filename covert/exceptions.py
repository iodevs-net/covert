"""Custom exception classes for the Covert package.

This module defines all custom exceptions used throughout the Covert package
to provide clear, specific error handling.
"""


class CovertError(Exception):
    """Base exception class for all Covert errors.

    All custom exceptions in the Covert package inherit from this class,
    allowing users to catch all Covert-specific errors with a single
    except clause.

    Attributes:
        message: Human-readable error message.
    """

    def __init__(self, message: str) -> None:
        """Initialize the CovertError.

        Args:
            message: Human-readable error message.
        """
        self.message = message
        super().__init__(self.message)


class ConfigError(CovertError):
    """Exception raised for configuration-related errors.

    This exception is raised when there are issues with loading,
    parsing, or accessing configuration files or values.

    Examples:
        - Configuration file not found
        - Invalid configuration file format
        - Missing required configuration values
    """

    def __init__(self, message: str) -> None:
        """Initialize the ConfigError.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message)


class UpdateError(CovertError):
    """Exception raised for package update-related errors.

    This exception is raised when there are issues during the package
    update process, including installation failures, rollback failures,
    or other update-related problems.

    Examples:
        - Package installation failed
        - Package rollback failed
        - Version conflict during update
    """

    def __init__(self, message: str) -> None:
        """Initialize the UpdateError.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message)


class TestError(CovertError):
    """Exception raised for test execution errors.

    This exception is raised when there are issues with running tests,
    including test failures, timeouts, or execution problems.

    Examples:
        - Tests failed after package update
        - Test execution timed out
        - Test command not found
    """

    def __init__(self, message: str) -> None:
        """Initialize the TestError.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message)


class BackupError(CovertError):
    """Exception raised for backup-related errors.

    This exception is raised when there are issues with creating,
    restoring, or managing backups.

    Examples:
        - Failed to create backup
        - Failed to restore from backup
        - Backup file not found
        - Backup directory not accessible
    """

    def __init__(self, message: str) -> None:
        """Initialize the BackupError.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message)


class PipError(CovertError):
    """Exception raised for pip-related errors.

    This exception is raised when there are issues with pip operations,
    including listing packages, installing packages, or other pip commands.

    Examples:
        - Pip command failed
        - Package not found
        - Pip not installed
        - Invalid pip command
    """

    def __init__(self, message: str) -> None:
        """Initialize the PipError.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message)


class ValidationError(CovertError):
    """Exception raised for validation errors.

    This exception is raised when input validation fails, including
    invalid configuration values, invalid package names, or other
    validation-related issues.

    Examples:
        - Invalid configuration value
        - Invalid package name format
        - Invalid version string
        - Missing required field
    """

    def __init__(self, message: str) -> None:
        """Initialize the ValidationError.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message)


class SecurityError(CovertError):
    """Exception raised for security-related errors.

    This exception is raised when security checks fail, including
    virtual environment violations, privilege escalation attempts,
    or other security-related issues.

    Examples:
        - Not running in a virtual environment
        - Running with elevated privileges
        - Command injection attempt detected
        - Invalid package name detected
    """

    def __init__(self, message: str) -> None:
        """Initialize the SecurityError.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message)
