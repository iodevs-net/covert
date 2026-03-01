"""Core update orchestration module for Covert.

This module provides the main update workflow that coordinates package
updates, testing, backup creation, and rollback mechanisms.
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from covert.backup import create_backup
from covert.config import Config
from covert.exceptions import SecurityError, UpdateError, ValidationError
from covert.logger import get_logger
from covert.pip_interface import get_outdated_packages, install_package, uninstall_package
from covert.tester import run_tests
from covert.utils import (
    check_elevated_privileges,
    get_security_audit_info,
    is_breaking_change,
    is_in_virtualenv,
)

logger = get_logger(__name__)


class UpdateStatus(Enum):
    """Status codes for package updates."""

    UPDATED = "updated"
    ROLLED_BACK = "rolled_back"
    FAILED_INSTALL = "failed_install"
    CRITICAL_FAILURE = "critical_failure"
    SKIPPED = "skipped"
    PENDING = "pending"


@dataclass
class PackageInfo:
    """Information about a package.

    Attributes:
        name: Package name.
        current_version: Currently installed version.
        latest_version: Latest available version.
        package_type: Type of package (e.g., "regular").
    """

    name: str
    current_version: str
    latest_version: str
    package_type: str = "regular"


@dataclass
class UpdateResult:
    """Result of a package update attempt.

    Attributes:
        package: Package information.
        status: Update status.
        timestamp: When the update was attempted.
        error_message: Error message if update failed.
        test_output: Test output if tests were run.
        test_passed: Whether tests passed after update.
    """

    package: PackageInfo
    status: UpdateStatus
    timestamp: datetime
    error_message: Optional[str] = None
    test_output: Optional[str] = None
    test_passed: bool = False


@dataclass
class UpdateSession:
    """Tracks an entire update session.

    Attributes:
        start_time: When the session started.
        end_time: When the session ended.
        backup_file: Path to the backup file created.
        results: List of update results for each package.
        pre_test_passed: Whether pre-flight tests passed.
        dry_run: Whether this was a dry-run session.
    """

    start_time: datetime
    end_time: Optional[datetime] = None
    backup_file: Optional[str] = None
    results: List[UpdateResult] = field(default_factory=list)
    pre_test_passed: bool = False
    dry_run: bool = False

    @property
    def summary(self) -> Dict[str, int]:
        """Get summary statistics.

        Returns:
            Dict[str, int]: Count of packages by status.
        """
        stats = {status.value: 0 for status in UpdateStatus}
        for result in self.results:
            stats[result.status.value] += 1
        return stats

    @property
    def success(self) -> bool:
        """Check if the session was successful.

        Returns:
            bool: True if no critical failures occurred.
        """
        return self.summary.get("critical_failure", 0) == 0

    @property
    def updated_count(self) -> int:
        """Get number of successfully updated packages.

        Returns:
            int: Number of updated packages.
        """
        return self.summary.get("updated", 0)

    @property
    def rolled_back_count(self) -> int:
        """Get number of rolled back packages.

        Returns:
            int: Number of rolled back packages.
        """
        return self.summary.get("rolled_back", 0)


def run_update_session(
    config: Config,
    dry_run: bool = False,
    no_backup: bool = False,
    no_tests: bool = False,
    ignore_packages: Optional[List[str]] = None,
    allow_only_packages: Optional[List[str]] = None,
    parallel: bool = False,
) -> UpdateSession:
    """Run a complete update session.

    This is the main orchestration function that:
    1. Checks virtual environment
    2. Runs pre-flight tests
    3. Creates backup
    4. Gets outdated packages
    5. Updates each package (sequentially or in parallel)
    6. Verifies tests after each update
    7. Rolls back if tests fail

    Args:
        config: Configuration object.
        dry_run: If True, simulate updates without making changes.
        no_backup: If True, skip creating backup.
        no_tests: If True, skip running tests.
        ignore_packages: List of packages to ignore.
        allow_only_packages: List of packages to allow (exclusive mode).
        parallel: If True, update packages in parallel (experimental).

    Returns:
        UpdateSession: Session results and statistics.

    Raises:
        ValidationError: If configuration is invalid.
        UpdateError: If critical error occurs.
    """
    session = UpdateSession(
        start_time=datetime.now(),
        dry_run=dry_run,
    )

    logger.info("=" * 60)
    logger.info("Starting Covert update session")
    logger.info("=" * 60)

    # Log security audit info at start of session
    security_info = get_security_audit_info()
    logger.info(
        f"Security context: venv={security_info['running_in_venv']}, "
        f"elevated={security_info['elevated_privileges']}, "
        f"platform={security_info['platform']}"
    )

    try:
        # Step 1: Check virtual environment (for programmatic usage)
        # CLI handles this with proper exit code, but we check here too
        # for cases where run_update_session is called directly
        if config.security.require_virtualenv and not is_in_virtualenv():
            logger.error("Not running in a virtual environment")
            raise SecurityError(
                "Virtual environment is required. "
                "Please activate a virtual environment before running Covert."
            )

        # Step 2: Check for elevated privileges (for programmatic usage)
        if check_elevated_privileges():
            logger.warning(
                "Running with elevated privileges - this is not recommended. "
                "Operations will be blocked for safety."
            )
            raise SecurityError(
                "Covert cannot run with elevated privileges (root/admin). "
                "Please run as a regular user within a virtual environment."
            )

        # Step 3: Pre-flight test
        if not no_tests and config.testing.enabled:
            logger.info("Running pre-flight tests...")
            pre_test_result = run_tests(config.testing)
            session.pre_test_passed = pre_test_result.success

            if not pre_test_result.success:
                logger.error("Pre-flight tests failed. Aborting update session.")
                raise UpdateError(
                    f"Pre-flight tests failed: {pre_test_result.failed} test(s) failed"
                )

            logger.info("Pre-flight tests passed")

        # Step 4: Create backup
        if not no_backup and not dry_run:
            logger.info("Creating backup...")
            session.backup_file = create_backup(config.backup)
            logger.info(f"Backup created: {session.backup_file}")

        # Step 5: Get outdated packages
        logger.info("Checking for outdated packages...")
        outdated_packages = get_outdated_packages()

        if not outdated_packages:
            logger.info("No outdated packages found. All packages are up to date.")
            session.end_time = datetime.now()
            return session

        # Filter packages based on configuration
        packages_to_update = _filter_packages(
            outdated_packages,
            config.updates.ignore_packages,
            config.updates.allow_only_packages,
            ignore_packages,
            allow_only_packages,
        )

        if not packages_to_update:
            logger.info("No packages to update after filtering.")
            session.end_time = datetime.now()
            return session

        logger.info(f"Found {len(packages_to_update)} package(s) to update")

        # Step 6: Update each package
        if parallel:
            logger.info("Using parallel update mode")
            results = _update_packages_parallel(
                packages_to_update,
                config,
                dry_run,
                no_tests,
                config.updates.max_parallel,
            )
            session.results.extend(results)
        else:
            for pkg_data in packages_to_update:
                package = PackageInfo(
                    name=pkg_data["name"],
                    current_version=pkg_data["version"],
                    latest_version=pkg_data["latest_version"],
                    package_type=pkg_data.get("package_type", "regular"),
                )

                result = _update_package(
                    package,
                    config,
                    dry_run,
                    no_tests,
                )
                session.results.append(result)

        session.end_time = datetime.now()

        # Print summary
        _print_session_summary(session)

        return session

    except (SecurityError, ValidationError, UpdateError) as e:
        logger.error(f"Update session failed: {e}")
        session.end_time = datetime.now()
        raise


def _filter_packages(
    packages: List[Dict[str, str]],
    config_ignore: List[str],
    config_allow: Optional[List[str]],
    cli_ignore: Optional[List[str]],
    cli_allow: Optional[List[str]],
) -> List[Dict[str, str]]:
    """Filter packages based on configuration.

    Args:
        packages: List of package dictionaries.
        config_ignore: Packages to ignore from config.
        config_allow: Packages to allow from config (exclusive mode).
        cli_ignore: Packages to ignore from CLI.
        cli_allow: Packages to allow from CLI (exclusive mode).

    Returns:
        List[Dict[str, str]]: Filtered list of packages.
    """
    filtered = []

    for pkg in packages:
        name = pkg["name"]

        # Check ignore lists
        if config_ignore and name in config_ignore:
            logger.debug(f"Ignoring package (config): {name}")
            continue

        if cli_ignore and name in cli_ignore:
            logger.debug(f"Ignoring package (CLI): {name}")
            continue

        # Check allow lists (exclusive mode)
        if config_allow:
            if name not in config_allow:
                logger.debug(f"Excluding package (not in allow list): {name}")
                continue

        if cli_allow:
            if name not in cli_allow:
                logger.debug(f"Excluding package (not in CLI allow list): {name}")
                continue

        filtered.append(pkg)

    return filtered


def _update_package(
    package: PackageInfo,
    config: Config,
    dry_run: bool,
    no_tests: bool,
) -> UpdateResult:
    """Update a single package.

    Args:
        package: Package information.
        config: Configuration object.
        dry_run: If True, simulate update without making changes.
        no_tests: If True, skip running tests.

    Returns:
        UpdateResult: Result of the update attempt.
    """
    result = UpdateResult(
        package=package,
        status=UpdateStatus.PENDING,
        timestamp=datetime.now(),
    )

    logger.info("-" * 60)
    logger.info(f"Updating package: {package.name}")
    logger.info(f"  Current: {package.current_version}")
    logger.info(f"  Latest:  {package.latest_version}")

    try:
        # Check version policy
        is_breaking = is_breaking_change(
            package.current_version,
            package.latest_version,
            config.updates.version_policy,
        )

        if is_breaking:
            logger.warning(
                f"Skipping {package.name}: version change is breaking "
                f"under '{config.updates.version_policy}' policy"
            )
            result.status = UpdateStatus.SKIPPED
            return result

        # Dry run mode
        if dry_run:
            logger.info(f"[DRY RUN] Would update {package.name} to {package.latest_version}")
            result.status = UpdateStatus.UPDATED
            return result

        # Store current version for rollback
        old_version = package.current_version

        # Install new version (with hash verification if enabled)
        verify_hash = getattr(config.security, 'verify_hashes', False)
        logger.info(f"Installing {package.name}=={package.latest_version}")
        install_package(package.name, version=package.latest_version, verify_hash=verify_hash)
        logger.info(f"Successfully installed {package.name}=={package.latest_version}")

        # Run tests if enabled
        if not no_tests and config.testing.enabled:
            logger.info(f"Running tests for {package.name}...")
            test_result = run_tests(config.testing)
            result.test_output = test_result.output
            result.test_passed = test_result.success

            if not test_result.success:
                logger.warning(f"Tests failed after updating {package.name}")
                logger.info(f"Rolling back {package.name} to {old_version}")

                try:
                    uninstall_package(package.name)
                    install_package(package.name, version=old_version)
                    result.status = UpdateStatus.ROLLED_BACK
                    logger.info(f"Successfully rolled back {package.name}")
                except Exception as e:
                    logger.error(f"Failed to rollback {package.name}: {e}")
                    result.status = UpdateStatus.CRITICAL_FAILURE
                    result.error_message = str(e)

                return result

        result.status = UpdateStatus.UPDATED
        logger.info(f"Successfully updated {package.name}")

    except Exception as e:
        logger.error(f"Failed to update {package.name}: {e}")
        result.status = UpdateStatus.FAILED_INSTALL
        result.error_message = str(e)

    return result


def _update_packages_parallel(
    packages: List[Dict[str, str]],
    config: Config,
    dry_run: bool,
    no_tests: bool,
    max_workers: int,
) -> List[UpdateResult]:
    """Update multiple packages in parallel using thread pool.

    Args:
        packages: List of package dictionaries to update.
        config: Configuration object.
        dry_run: If True, simulate updates without making changes.
        no_tests: If True, skip running tests.
        max_workers: Maximum number of parallel workers.

    Returns:
        List[UpdateResult]: Results of update attempts.
    """
    results: List[UpdateResult] = []
    results_lock = threading.Lock()

    def update_worker(pkg_data: Dict[str, str]) -> UpdateResult:
        """Worker function for parallel package updates.

        Args:
            pkg_data: Package data dictionary.

        Returns:
            UpdateResult: Result of the update attempt.
        """
        package = PackageInfo(
            name=pkg_data["name"],
            current_version=pkg_data["version"],
            latest_version=pkg_data["latest_version"],
            package_type=pkg_data.get("package_type", "regular"),
        )
        return _update_package(package, config, dry_run, no_tests)

    # Use ThreadPoolExecutor for parallel updates
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all update tasks
        future_to_package = {executor.submit(update_worker, pkg): pkg for pkg in packages}

        # Collect results as they complete
        for future in as_completed(future_to_package):
            try:
                result = future.result()
                with results_lock:
                    results.append(result)
            except Exception as e:
                pkg = future_to_package[future]
                logger.error(f"Parallel update failed for {pkg['name']}: {e}")
                # Create a failure result
                package = PackageInfo(
                    name=pkg["name"],
                    current_version=pkg["version"],
                    latest_version=pkg["latest_version"],
                    package_type=pkg.get("package_type", "regular"),
                )
                result = UpdateResult(
                    package=package,
                    status=UpdateStatus.FAILED_INSTALL,
                    timestamp=datetime.now(),
                    error_message=str(e),
                )
                with results_lock:
                    results.append(result)

    return results


def _print_session_summary(session: UpdateSession) -> None:
    """Print a summary of the update session.

    Args:
        session: Update session to summarize.
    """
    logger.info("=" * 60)
    logger.info("Update session summary")
    logger.info("=" * 60)

    if session.end_time is None:
        logger.warning("Session end time not available")
        return

    duration = (session.end_time - session.start_time).total_seconds()
    logger.info(f"Duration: {duration:.2f} seconds")

    if session.backup_file:
        logger.info(f"Backup: {session.backup_file}")

    summary = session.summary
    logger.info(f"Updated: {summary.get('updated', 0)}")
    logger.info(f"Rolled back: {summary.get('rolled_back', 0)}")
    logger.info(f"Failed: {summary.get('failed_install', 0)}")
    logger.info(f"Skipped: {summary.get('skipped', 0)}")
    logger.info(f"Critical failures: {summary.get('critical_failure', 0)}")

    # Print detailed results
    if session.results:
        logger.info("")
        logger.info("Package details:")
        for result in session.results:
            pkg = result.package
            status = result.status.value.upper()
            logger.info(f"  {pkg.name}: {status}")
            if result.error_message:
                logger.info(f"    Error: {result.error_message}")

    logger.info("=" * 60)
