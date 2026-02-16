"""Utility functions module for Covert.

This module provides utility functions for validation, version comparison,
virtual environment detection, and other common operations.
"""

import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple, Union

from packaging.version import InvalidVersion, Version

from covert.exceptions import ValidationError

if TYPE_CHECKING:
    import ctypes  # noqa: F401

# Valid Python package name regex (PEP 508)
PACKAGE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$")
# Version pattern (PEP 440 compliant)
VERSION_PATTERN = re.compile(r"^[0-9]+(\.[0-9]+)*([a-zA-Z0-9.+-]*)?$")


def validate_package_name(name: str) -> bool:
    """Validate package name follows PEP 508.

    Args:
        name: Package name to validate.

    Returns:
        bool: True if package name is valid, False otherwise.
    """
    return bool(PACKAGE_NAME_PATTERN.match(name))


def validate_version(version: str) -> bool:
    """Validate version string format.

    Args:
        version: Version string to validate.

    Returns:
        bool: True if version is valid, False otherwise.
    """
    return bool(VERSION_PATTERN.match(version))


def sanitize_package_name(name: str) -> str:
    """Sanitize package name to prevent injection.

    Validates and normalizes the package name.

    Args:
        name: Package name to sanitize.

    Returns:
        str: Sanitized package name in lowercase.

    Raises:
        ValidationError: If package name is invalid.
    """
    if not validate_package_name(name):
        raise ValidationError(f"Invalid package name: {name}")
    return name.lower()


def is_in_virtualenv() -> bool:
    """Check if running inside a virtual environment.

    Returns:
        bool: True if running in a virtual environment, False otherwise.
    """
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def get_venv_path() -> Optional[Path]:
    """Get path to current virtual environment.

    Returns:
        Optional[Path]: Path to virtual environment if active, None otherwise.
    """
    if is_in_virtualenv():
        return Path(sys.prefix)
    return None


def check_elevated_privileges() -> bool:
    """Check if running with elevated privileges.

    Returns:
        bool: True if running with elevated privileges (root/admin), False otherwise.
    """
    try:
        return os.geteuid() == 0  # Unix root check
    except AttributeError:
        # Windows - check if running as administrator
        try:
            import ctypes  # noqa: F401

            # Type ignore for Windows-specific code
            return bool(ctypes.windll.shell32.IsUserAnAdmin() != 0)  # type: ignore[attr-defined, no-any-return]
        except (AttributeError, OSError):
            return False


def parse_version(version: str) -> Version:
    """Parse version string into packaging.Version object.

    Args:
        version: Version string to parse.

    Returns:
        Version: Parsed version object.

    Raises:
        ValidationError: If version string is invalid.
    """
    if not validate_version(version):
        raise ValidationError(f"Invalid version format: {version}")
    try:
        return Version(version)
    except InvalidVersion as e:
        raise ValidationError(f"Failed to parse version '{version}': {e}") from e


def is_breaking_change(
    current_version: str, new_version: str, version_policy: str = "safe"
) -> bool:
    """Check if version update is a breaking change based on policy.

    Args:
        current_version: Current version string.
        new_version: New version string.
        version_policy: Version policy ("safe", "latest", "minor", "patch").

    Returns:
        bool: True if the update is a breaking change, False otherwise.

    Raises:
        ValidationError: If version strings are invalid.
    """
    current = parse_version(current_version)
    new = parse_version(new_version)

    # If new version is not greater, it's not an update
    if new <= current:
        return False

    # "latest" policy allows any update
    if version_policy == "latest":
        return False

    # Extract version components
    current_parts = current.release
    new_parts = new.release

    # Handle different version lengths
    max_len = max(len(current_parts), len(new_parts))
    current_parts = current_parts + (0,) * (max_len - len(current_parts))
    new_parts = new_parts + (0,) * (max_len - len(new_parts))

    # Check for breaking changes based on policy
    if version_policy == "patch":
        # Only allow patch updates (X.Y.Z -> X.Y.Z+1)
        return not (current_parts[0] == new_parts[0] and current_parts[1] == new_parts[1])
    elif version_policy == "minor":
        # Allow minor and patch updates (X.Y.Z -> X.Y+1.Z)
        return current_parts[0] != new_parts[0]
    elif version_policy == "safe":
        # "safe" is the same as "minor" - allow minor and patch updates
        return current_parts[0] != new_parts[0]
    else:
        # Unknown policy - be conservative and treat as breaking
        return True


def format_version_range(
    min_version: Optional[str] = None, max_version: Optional[str] = None
) -> str:
    """Format version range for pip requirements.

    Args:
        min_version: Minimum version (inclusive).
        max_version: Maximum version (exclusive).

    Returns:
        str: Formatted version range string.
    """
    parts = []
    if min_version:
        parts.append(f">={min_version}")
    if max_version:
        parts.append(f"<{max_version}")
    return ",".join(parts) if parts else ""


def compare_versions(version1: str, version2: str) -> int:
    """Compare two version strings.

    Args:
        version1: First version string.
        version2: Second version string.

    Returns:
        int: -1 if version1 < version2, 0 if equal, 1 if version1 > version2.

    Raises:
        ValidationError: If version strings are invalid.
    """
    v1 = parse_version(version1)
    v2 = parse_version(version2)

    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    else:
        return 0


def get_python_version() -> Tuple[int, int, int]:
    """Get the current Python version as a tuple.

    Returns:
        Tuple[int, int, int]: Python version as (major, minor, micro).
    """
    return sys.version_info[:3]


def is_compatible_python_version(
    required_version: str, current_version: Optional[Tuple[int, int, int]] = None
) -> bool:
    """Check if current Python version meets requirements.

    Args:
        required_version: Required version string (e.g., ">=3.8").
        current_version: Current Python version tuple. If None, uses sys.version_info.

    Returns:
        bool: True if compatible, False otherwise.
    """
    if current_version is None:
        current_version = get_python_version()

    # Simple version comparison for common patterns
    # This is a simplified implementation
    if required_version.startswith(">="):
        min_ver = parse_version(required_version[2:])
        return Version(f"{current_version[0]}.{current_version[1]}.{current_version[2]}") >= min_ver
    elif required_version.startswith(">"):
        min_ver = parse_version(required_version[1:])
        return Version(f"{current_version[0]}.{current_version[1]}.{current_version[2]}") > min_ver
    elif required_version.startswith("=="):
        exact_ver = parse_version(required_version[2:])
        return (
            Version(f"{current_version[0]}.{current_version[1]}.{current_version[2]}") == exact_ver
        )

    # Default to True if we can't parse the requirement
    return True


def validate_path(path: Union[str, Path]) -> bool:
    """Validate that a path is safe to use.

    This function checks that a path:
    - Does not contain path traversal attempts (../)
    - Does not contain null bytes
    - Is not an absolute path (unless explicitly allowed)
    - Does not contain suspicious characters

    Args:
        path: Path to validate.

    Returns:
        bool: True if path is safe, False otherwise.
    """
    if not path:
        return False

    path_str = str(path)

    # Check for null bytes
    if "\x00" in path_str:
        return False

    # Check for path traversal attempts
    if "../" in path_str or "..\\" in path_str:
        return False

    # Check for suspicious characters in path components
    suspicious_chars = ["\x00", "\r", "\n"]
    if any(char in path_str for char in suspicious_chars):
        return False

    # Additional checks can be added here as needed
    return True


def sanitize_path(path: Union[str, Path], allow_absolute: bool = False) -> Path:
    """Sanitize and validate a path for safe use.

    Args:
        path: Path to sanitize.
        allow_absolute: Whether to allow absolute paths.

    Returns:
        Path: Sanitized path.

    Raises:
        ValidationError: If path is invalid or unsafe.
    """
    if not validate_path(path):
        raise ValidationError(f"Invalid or unsafe path: {path}")

    path_obj = Path(path)

    # Check if absolute path is allowed
    if not allow_absolute and path_obj.is_absolute():
        raise ValidationError(f"Absolute paths are not allowed: {path}")

    return path_obj.resolve()
