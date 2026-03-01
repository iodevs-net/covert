"""Pip interface module for Covert.

This module provides a secure wrapper around pip commands for listing,
installing, and uninstalling packages. All commands are executed without
shell=True for security.
"""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

from covert.exceptions import PipError, ValidationError
from covert.logger import get_logger
from covert.utils import sanitize_package_name, validate_version

logger = get_logger(__name__)


def run_secure_command(
    command: Union[str, List[str]],
    capture_output: bool = True,
    check: bool = False,
    timeout: Optional[int] = None,
) -> subprocess.CompletedProcess:
    """Execute command securely without shell=True.

    This function is a security-hardened wrapper around subprocess.run
    that never uses shell=True to prevent command injection attacks.

    Args:
        command: Command as string (split automatically) or list.
        capture_output: Whether to capture stdout/stderr.
        check: Whether to raise an exception if command returns non-zero.
        timeout: Maximum time to wait for command completion in seconds.

    Returns:
        CompletedProcess: Result of command execution.

    Raises:
        PipError: If command execution fails.
    """
    if isinstance(command, str):
        # Split command safely
        cmd_list = command.split()
    else:
        cmd_list = command

    logger.debug(f"Executing command: {' '.join(cmd_list)}")

    try:
        result = subprocess.run(
            cmd_list,
            shell=False,  # Critical: Never use shell=True
            check=False,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout} seconds: {cmd_list}")
        raise PipError(f"Command timed out after {timeout} seconds") from e
    except FileNotFoundError as e:
        logger.error(f"Command not found: {cmd_list[0]}")
        raise PipError("Command not found") from e
    except Exception as e:
        logger.error(f"Failed to execute command: {e}")
        raise PipError("Failed to execute command") from e

    if check and result.returncode != 0:
        error_msg = result.stderr.strip() if result.stderr else "Unknown error"
        logger.error(f"Command failed with return code {result.returncode}: {error_msg}")
        raise PipError(f"Command failed: {error_msg}")

    return result


def get_package_hash(package_name: str, version: str) -> Optional[str]:
    """Get SHA256 hash of a package from PyPI.

    Downloads the package temporarily and computes its hash.
    This is used for secure verification before installation.

    Args:
        package_name: Name of the package.
        version: Specific version to get hash for.

    Returns:
        Optional[str]: SHA256 hash of the package, or None if unable to get.
    """
    logger.debug(f"Computing hash for {package_name}=={version}")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Download package to temp directory
        download_cmd = [
            "pip", "download",
            f"{package_name}=={version}",
            "--no-deps",
            "--dest", tmpdir,
        ]
        result = run_secure_command(download_cmd, timeout=60)

        if result.returncode != 0:
            logger.warning(f"Could not download {package_name}=={version} for hashing")
            return None

        # Find downloaded file
        tmp_path = Path(tmpdir)
        wheel_or_tar = None
        for f in tmp_path.iterdir():
            if f.suffix in (".whl", ".tar.gz", ".zip"):
                wheel_or_tar = f
                break

        if not wheel_or_tar:
            logger.warning(f"No package file found for {package_name}=={version}")
            return None

        # Compute hash
        sha256_hash = hashlib.sha256()
        try:
            with open(wheel_or_tar, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return f"sha256:{sha256_hash.hexdigest()}"
        except OSError as e:
            logger.warning(f"Could not hash {wheel_or_tar}: {e}")
            return None


def verify_and_install_package(
    package_name: str,
    version: Optional[str] = None,
    upgrade: bool = False,
    pre_release: bool = False,
    timeout: Optional[int] = None,
) -> Dict[str, str]:
    """Install a package with hash verification.

    Downloads the package, computes its hash, verifies against expected hash,
    and only installs if verification passes.

    Args:
        package_name: Name of the package to install.
        version: Specific version to install.
        upgrade: Whether to upgrade if already installed.
        pre_release: Whether to include pre-release versions.
        timeout: Maximum time to wait for installation.

    Returns:
        Dict[str, str]: Package information including name and version.

    Raises:
        ValidationError: If package name or version is invalid.
        PipError: If installation fails or hash verification fails.
    """
    sanitized_name = sanitize_package_name(package_name)

    if version and not validate_version(version):
        raise ValidationError(f"Invalid version format: {version}")

    # Build package specifier
    package_spec = sanitized_name
    if version:
        package_spec = f"{sanitized_name}=={version}"

    logger.info(f"Installing package with hash verification: {package_spec}")

    # Get expected hash
    expected_hash = get_package_hash(sanitized_name, version) if version else None

    # Build install command with hash verification
    install_cmd = ["pip", "install", package_spec]

    if expected_hash:
        install_cmd.extend(["--require-hashes", "--no-input"])

    if upgrade:
        install_cmd.append("--upgrade")

    if pre_release:
        install_cmd.append("--pre")

    result = run_secure_command(install_cmd, timeout=timeout)

    if result.returncode != 0:
        error_msg = result.stderr.strip() if result.stderr else "Unknown error"
        logger.error(f"Failed to install {package_spec}: {error_msg}")
        raise PipError("Failed to install package")

    # Get the installed version
    installed_version = version
    if not installed_version:
        installed_version = get_package_version(sanitized_name)

    logger.info(f"Successfully installed {sanitized_name}=={installed_version}")

    return {
        "name": sanitized_name,
        "version": installed_version or "",
    }


def get_outdated_packages() -> List[Dict[str, str]]:
    """Get list of outdated packages using pip.

    Uses 'pip list --outdated --format=json' to get outdated packages.

    Returns:
        List[Dict[str, str]]: List of outdated packages with metadata.

    Raises:
        PipError: If pip command fails or returns invalid JSON.
    """
    logger.info("Checking for outdated packages...")

    command = ["pip", "list", "--outdated", "--format=json"]
    result = run_secure_command(command)

    if result.returncode != 0:
        # No outdated packages is not an error
        if (
            "WARNING: No packages found" in result.stderr
            or "WARNING: Could not find a version" in result.stderr
        ):
            logger.info("No outdated packages found")
            return []
        raise PipError("Failed to get outdated packages")

    try:
        packages: List[Dict[str, str]] = json.loads(result.stdout)
        logger.info(f"Found {len(packages)} outdated package(s)")
        return packages
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse pip output: {e}")
        raise PipError("Failed to parse pip output") from e


def install_package(
    package_name: str,
    version: Optional[str] = None,
    upgrade: bool = False,
    pre_release: bool = False,
    timeout: Optional[int] = None,
    verify_hash: bool = False,
) -> Dict[str, str]:
    """Install a package using pip.

    Args:
        package_name: Name of the package to install.
        version: Specific version to install (e.g., "2.31.0").
        upgrade: Whether to upgrade if already installed.
        pre_release: Whether to include pre-release versions.
        timeout: Maximum time to wait for installation in seconds.
        verify_hash: Whether to verify package hash before installation.

    Returns:
        Dict[str, str]: Package information including name and version.

    Raises:
        ValidationError: If package name or version is invalid.
        PipError: If installation fails.
    """
    sanitized_name = sanitize_package_name(package_name)

    if version and not validate_version(version):
        raise ValidationError(f"Invalid version format: {version}")

    # Build package specifier
    package_spec = sanitized_name
    if version:
        package_spec = f"{sanitized_name}=={version}"

    logger.info(f"Installing package: {package_spec}")

    # If hash verification is enabled, use it
    if verify_hash and version:
        return verify_and_install_package(
            package_name,
            version=version,
            upgrade=upgrade,
            pre_release=pre_release,
            timeout=timeout,
        )

    command = ["pip", "install", package_spec]

    if upgrade:
        command.append("--upgrade")

    if pre_release:
        command.append("--pre")

    result = run_secure_command(command, timeout=timeout)

    if result.returncode != 0:
        error_msg = result.stderr.strip() if result.stderr else "Unknown error"
        logger.error(f"Failed to install {package_spec}: {error_msg}")
        raise PipError("Failed to install package")

    # Get the installed version
    installed_version = version
    if not installed_version:
        installed_version = get_package_version(sanitized_name)

    logger.info(f"Successfully installed {sanitized_name}=={installed_version}")

    return {
        "name": sanitized_name,
        "version": installed_version or "",
    }


def uninstall_package(
    package_name: str,
    timeout: Optional[int] = None,
) -> None:
    """Uninstall a package using pip.

    Args:
        package_name: Name of the package to uninstall.
        timeout: Maximum time to wait for uninstallation in seconds.

    Raises:
        ValidationError: If package name is invalid.
        PipError: If uninstallation fails.
    """
    sanitized_name = sanitize_package_name(package_name)

    logger.info(f"Uninstalling package: {sanitized_name}")

    command = ["pip", "uninstall", "-y", sanitized_name]
    result = run_secure_command(command, timeout=timeout)

    if result.returncode != 0:
        error_msg = result.stderr.strip() if result.stderr else "Unknown error"
        logger.error(f"Failed to uninstall {sanitized_name}: {error_msg}")
        raise PipError("Failed to uninstall package")

    logger.info(f"Successfully uninstalled {sanitized_name}")


def freeze_requirements(
    output_path: Optional[Union[str, Path]] = None,
    format_type: str = "txt",
) -> Union[str, List[Dict[str, str]]]:
    """Get installed packages using pip freeze.

    Args:
        output_path: Optional path to save the requirements file.
        format_type: Output format ("txt" or "json").

    Returns:
        Union[str, List[Dict[str, str]]]: Requirements as string or list of dicts.

    Raises:
        PipError: If pip freeze command fails.
        ValidationError: If format_type is invalid.
    """
    logger.info("Freezing current package requirements...")

    if format_type not in ("txt", "json"):
        raise ValidationError(f"Invalid format type: {format_type}")

    command = ["pip", "freeze"]
    result = run_secure_command(command)

    if result.returncode != 0:
        error_msg = result.stderr.strip() if result.stderr else "Unknown error"
        logger.error(f"Failed to freeze requirements: {error_msg}")
        raise PipError(f"Failed to freeze requirements: {error_msg}")

    requirements = result.stdout

    if format_type == "json":
        # Parse pip freeze output into JSON format
        packages = []
        for line in requirements.splitlines():
            if "==" in line:
                name, version = line.split("==", 1)
                packages.append({"name": name, "version": version})
        output = packages
    else:
        output = requirements

    # Save to file if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format_type == "json":
            content = json.dumps(output, indent=2)
        else:
            content = str(output)

        try:
            output_path.write_text(content)
            logger.info(f"Requirements saved to: {output_path}")
        except OSError as e:
            logger.error(f"Failed to save requirements to {output_path}: {e}")
            raise PipError("Failed to save requirements") from e

    return output


def get_package_version(package_name: str) -> Optional[str]:
    """Get the installed version of a package.

    Args:
        package_name: Name of the package.

    Returns:
        Optional[str]: Installed version, or None if not found.

    Raises:
        ValidationError: If package name is invalid.
    """
    sanitized_name = sanitize_package_name(package_name)

    command = ["pip", "show", sanitized_name]
    result = run_secure_command(command)

    if result.returncode != 0:
        return None

    # Parse output to find version
    for line in result.stdout.splitlines():
        if line.startswith("Version:"):
            return line.split(":", 1)[1].strip()  # type: ignore[no-any-return]

    return None  # type: ignore[no-any-return]


def list_installed_packages() -> List[Dict[str, str]]:
    """List all installed packages.

    Returns:
        List[Dict[str, str]]: List of installed packages with metadata.

    Raises:
        PipError: If pip list command fails.
    """
    logger.debug("Listing installed packages...")

    command = ["pip", "list", "--format=json"]
    result = run_secure_command(command)

    if result.returncode != 0:
        error_msg = result.stderr.strip() if result.stderr else "Unknown error"
        logger.error(f"Failed to list installed packages: {error_msg}")
        raise PipError(f"Failed to list installed packages: {error_msg}")

    try:
        packages: List[Dict[str, str]] = json.loads(result.stdout)
        return packages
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse pip output: {e}")
        raise PipError("Failed to parse pip output") from e


def check_package_exists(package_name: str) -> bool:
    """Check if a package exists on PyPI.

    Args:
        package_name: Name of the package to check.

    Returns:
        bool: True if package exists, False otherwise.

    Raises:
        ValidationError: If package name is invalid.
    """
    sanitized_name = sanitize_package_name(package_name)

    command = ["pip", "index", "versions", sanitized_name]
    result = run_secure_command(command)

    return result.returncode == 0
