"""Dependency analysis module for Covert.

This module provides integration with pip-tools and pip commands to analyze
dependency graphs and detect broken dependencies before and after installation.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from covert.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DependencyCheckResult:
    """Result of a dependency check.

    Attributes:
        is_valid: Whether dependencies are valid.
        broken_packages: List of packages with broken dependencies.
        message: Human-readable message describing the result.
    """

    is_valid: bool
    broken_packages: List[Dict[str, str]]
    message: str


def check_current_dependencies() -> DependencyCheckResult:
    """Check if current installed packages have broken dependencies.

    Uses 'pip check' to verify all dependencies are satisfied.

    Returns:
        DependencyCheckResult with broken packages if any.
    """
    from covert.pip_interface import run_secure_command

    logger.debug("Checking current dependencies...")

    result = run_secure_command(["pip", "check"])

    if result.returncode == 0:
        return DependencyCheckResult(
            is_valid=True,
            broken_packages=[],
            message="All dependencies are satisfied",
        )

    # Parse broken dependencies from output
    broken = []
    for line in result.stdout.splitlines():
        # Format: "package requires otherpackage>=1.0"
        if " requires " in line:
            parts = line.split(" requires ")
            if len(parts) == 2:
                broken.append({
                    "package": parts[0].strip(),
                    "requirement": parts[1].strip(),
                })

    return DependencyCheckResult(
        is_valid=False,
        broken_packages=broken,
        message=result.stdout.strip(),
    )


def dry_run_install(
    package_name: str,
    version: Optional[str] = None,
) -> DependencyCheckResult:
    """Simulate package installation to check if dependencies can be resolved.

    Uses 'pip install --dry-run --ignore-installed' to attempt resolution
    without actually installing. This is similar to pip-tools pip-compile
    but for single packages.

    Args:
        package_name: Name of package to check.
        version: Specific version to check.

    Returns:
        DependencyCheckResult with resolution status.
    """
    from covert.pip_interface import run_secure_command, sanitize_package_name

    sanitized = sanitize_package_name(package_name)

    package_spec = sanitized
    if version:
        package_spec = f"{sanitized}=={version}"

    logger.info(f"Checking if {package_spec} can be resolved...")

    # Use pip install --dry-run to check resolution
    # --ignore-installed to not use already installed packages
    command = [
        "pip", "install",
        "--dry-run",
        "--ignore-installed",
        "--report", "/dev/stdout",
        package_spec,
    ]

    result = run_secure_command(command, timeout=120)

    if result.returncode == 0:
        return DependencyCheckResult(
            is_valid=True,
            broken_packages=[],
            message=f"{package_spec} can be resolved",
        )

    # Parse error message
    error_msg = result.stderr.strip() if result.stderr else "Unknown error"

    # Check for specific error types
    if "ResolutionTooDeep" in error_msg:
        return DependencyCheckResult(
            is_valid=False,
            broken_packages=[],
            message=f"Dependency resolution too deep for {package_spec}",
        )

    if "Could not find a version" in error_msg:
        return DependencyCheckResult(
            is_valid=False,
            broken_packages=[],
            message=f"Package {package_spec} not found on PyPI",
        )

    return DependencyCheckResult(
        is_valid=False,
        broken_packages=[],
        message=f"Cannot resolve {package_spec}: {error_msg}",
    )


def analyze_package_impact(
    package_name: str,
    version: str,
) -> Dict[str, any]:
    """Analyze the potential impact of installing a package.

    This function integrates pip-tools style analysis by:
    1. Checking current dependency state
    2. Attempting dry-run resolution
    3. Predicting potential conflicts

    Args:
        package_name: Package to analyze.
        version: Version to analyze.

    Returns:
        Dictionary with analysis results.
    """
    logger.info(f"Analyzing impact of {package_name}=={version}...")

    # Step 1: Check current state
    current_state = check_current_dependencies()

    # Step 2: Try to resolve the package
    resolution = dry_run_install(package_name, version)

    # Step 3: Build analysis result
    analysis = {
        "package": package_name,
        "version": version,
        "can_resolve": resolution.is_valid,
        "current_deps_ok": current_state.is_valid,
        "current_broken": current_state.broken_packages,
        "resolution_error": resolution.message if not resolution.is_valid else None,
        "recommendation": _get_recommendation(resolution, current_state),
    }

    logger.info(f"Analysis complete: {analysis['recommendation']}")

    return analysis


def _get_recommendation(
    resolution: DependencyCheckResult,
    current: DependencyCheckResult,
) -> str:
    """Get recommendation based on analysis results."""
    if not resolution.is_valid:
        return "BLOCK - Cannot resolve package dependencies"

    if not current.is_valid:
        return "WARNING - Current environment has broken dependencies"

    return "OK - Package can be installed safely"
