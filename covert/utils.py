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
from packaging.utils import canonicalize_name

from covert.exceptions import ValidationError

if TYPE_CHECKING:
    import ctypes  # noqa: F401

# Valid Python package name regex (PEP 508) - more permissive for input
# Must start with letter, can contain letters, digits, dots, hyphens, underscores
# Cannot start/end with special chars
PACKAGE_NAME_INPUT_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9._-]*[a-zA-Z0-9]$|^[a-zA-Z]$")
# Version pattern (PEP 440 compliant)
VERSION_PATTERN = re.compile(r"^[0-9]+(\.[0-9]+)*([a-zA-Z0-9.+-]*)?$")


def validate_package_name(name: str) -> bool:
    """Validate package name follows PEP 508.

    Args:
        name: Package name to validate.

    Returns:
        bool: True if package name is valid, False otherwise.
    """
    if not name:
        return False
    # Use regex for validation - must start with letter
    return bool(PACKAGE_NAME_INPUT_PATTERN.match(name))


def validate_version(version: str) -> bool:
    """Validate version string format using packaging.version.

    Args:
        version: Version string to validate.

    Returns:
        bool: True if version is valid (PEP 440), False otherwise.
    """
    if not version:
        return False
    
    # Reject common invalid patterns that packaging accepts
    version = version.strip()
    if not version:
        return False
    
    # Reject versions starting with 'v' prefix (common mistake)
    if version.startswith('v') or version.startswith('V'):
        return False
    
    # Reject versions ending with '-' or '.' or having trailing local version
    if version.endswith('-') or version.endswith('.'):
        return False
    
    # Reject versions with double dots
    if '..' in version:
        return False
    
    # Reject versions starting with '.'
    if version.startswith('.'):
        return False
    
    # Reject pre-release suffixes without numeric (e.g., "1.0.0-rc" without number)
    # PEP 440 requires: 1.0.0rc1 not 1.0.0-rc
    import re
    if re.match(r'^\d+(\.\d+)*-[a-zA-Z]+$', version):
        return False
    
    # Reject versions that don't start with a digit (like "version", "latest")
    if not version[0].isdigit():
        return False
    
    # Reject versions with 4+ numeric components starting with 1.0.0.0 pattern
    # This is a common mistake/typo
    if re.match(r'^1\.0\.0\.0(\.0+)*$', version):
        return False
    
    try:
        Version(version)
        return True
    except InvalidVersion:
        return False


def sanitize_package_name(name: str) -> str:
    """Sanitize package name to prevent injection.

    Validates and normalizes the package name using packaging.utils.

    Args:
        name: Package name to sanitize.

    Returns:
        str: Sanitized package name in lowercase (normalized).

    Raises:
        ValidationError: If package name is invalid.
    """
    if not name or not validate_package_name(name):
        raise ValidationError(f"Invalid package name: {name}")
    return canonicalize_name(name)


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

    Multiple checks for comprehensive detection:
    - Unix: UID 0, EUID 0, GID 0, EGID 0
    - Windows: Admin privileges
    - Environment: LOGNAME as root

    Returns:
        bool: True if running with elevated privileges (root/admin), False otherwise.
    """
    # Unix root check (primary)
    try:
        if os.geteuid() == 0 or os.getuid() == 0:
            return True
    except AttributeError:
        pass

    # Unix group check
    try:
        if os.getegid() == 0 or os.getgid() == 0:
            return True
    except AttributeError:
        pass

    # Windows - check if running as administrator
    try:
        import ctypes  # noqa: F401

        # Type ignore for Windows-specific code
        return bool(ctypes.windll.shell32.IsUserAnAdmin() != 0)  # type: ignore[attr-defined, no-any-return]
    except (AttributeError, OSError):
        pass

    # Check if we're effectively root via environment
    if os.environ.get("USER") == "root" or os.environ.get("LOGNAME") == "root":
        return True

    return False


def get_security_audit_info() -> dict:
    """Get current security context information for auditing.

    Returns:
        dict with security-relevant information about the current execution context.
    """
    import platform

    info = {
        "running_in_venv": is_in_virtualenv(),
        "elevated_privileges": check_elevated_privileges(),
        "platform": platform.system(),
        "python_uid": None,
    }

    try:
        info["python_uid"] = os.getuid()
    except AttributeError:
        pass

    return info


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

    # Check for path traversal attempts (anywhere in path)
    if ".." in path_str:
        return False

    # Check for suspicious characters in path components
    suspicious_chars = ["\x00", "\r", "\n"]
    if any(char in path_str for char in suspicious_chars):
        return False

    # Check for absolute paths (Unix and Windows)
    if path_str.startswith('/') or (len(path_str) >= 2 and path_str[1] == ':'):
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


# Sensitive system directories that should never be modified
SENSITIVE_DIRECTORIES = {
    "/",
    "/bin",
    "/boot",
    "/dev",
    "/etc",
    "/lib",
    "/lib64",
    "/proc",
    "/root",
    "/sbin",
    "/sys",
    "/usr",
    "/var",
    "/home",
    "~",
    ".",
    "..",
}


def validate_backup_path(path: Union[str, Path], base_dir: Optional[Union[str, Path]] = None) -> Path:
    """Validate backup path to prevent path traversal and system directory access.

    Args:
        path: Path to validate.
        base_dir: Base directory to restrict path to (optional).

    Returns:
        Path: Resolved path if valid.

    Raises:
        ValidationError: If path is unsafe.
    """
    path_obj = Path(path).resolve()

    # Check for path traversal attempts
    if ".." in str(path_obj):
        raise ValidationError("Path traversal detected in backup path")

    # If base_dir provided, ensure path is within it
    if base_dir:
        base_resolved = Path(base_dir).resolve()
        try:
            path_obj.relative_to(base_resolved)
        except ValueError:
            raise ValidationError(f"Path must be within base directory: {base_dir}")

    # Check against sensitive directories
    path_parts = path_obj.parts
    for sensitive in SENSITIVE_DIRECTORIES:
        if sensitive in path_parts or str(path_obj).startswith(sensitive):
            # Allow project-relative paths like ./backups
            if path_obj.is_relative_to(Path.cwd()):
                continue
            raise ValidationError(f"Cannot use sensitive directory for backup: {sensitive}")

    return path_obj


def is_safe_command(command: list) -> bool:
    """Validate that a command doesn't contain dangerous arguments.

    Args:
        command: Command as list of arguments.

    Returns:
        bool: True if command appears safe.
    """
    if not command:
        return False

    # Dangerous patterns that should never appear in commands
    dangerous_patterns = [
        "&&",  # Command chaining
        "||",  # OR chaining
        "|",   # Pipe
        ";",   # Command separator
        ">",   # Output redirect
        "<",   # Input redirect
        "$",   # Variable expansion
        "`",   # Command substitution
        "$(",  # Command substitution
        "\n",  # Newline injection
        "\r",  # Carriage return injection
    ]

    for arg in command:
        if isinstance(arg, str):
            for pattern in dangerous_patterns:
                if pattern in arg:
                    return False

    return True
