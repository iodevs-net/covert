"""Test execution module for Covert.

This module provides functionality for running tests after package updates
to verify system integrity. It supports configurable test commands,
timeout handling, and result parsing.
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from covert.config import TestingConfig
from covert.exceptions import TestError
from covert.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TestResult:
    """Result of a test execution.

    Attributes:
        success: Whether tests passed.
        exit_code: Exit code of test command.
        output: Combined stdout and stderr output.
        duration: Time taken to run tests in seconds.
        passed: Number of passed tests.
        failed: Number of failed tests.
        skipped: Number of skipped tests.
        total: Total number of tests.
    """

    success: bool
    exit_code: int
    output: str
    duration: float
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total: int = 0


def run_tests(
    config: TestingConfig,
    extra_args: Optional[List[str]] = None,
) -> TestResult:
    """Run tests using the configured test command.

    Args:
        config: Testing configuration.
        extra_args: Additional arguments to pass to test command.

    Returns:
        TestResult: Result of test execution.

    Raises:
        TestError: If test command cannot be executed.
    """
    if not config.enabled:
        logger.info("Testing is disabled, skipping tests")
        return TestResult(
            success=True,
            exit_code=0,
            output="Testing is disabled",
            duration=0.0,
        )

    # Build command
    command = [config.command]
    command.extend(config.args)

    if extra_args:
        command.extend(extra_args)

    logger.info(f"Running tests: {' '.join(command)}")

    # Execute tests
    try:
        result = subprocess.run(
            command,
            shell=False,  # Security: Never use shell=True
            capture_output=True,
            text=True,
            timeout=config.timeout_seconds,
        )
    except subprocess.TimeoutExpired as e:
        logger.error(f"Tests timed out after {config.timeout_seconds} seconds")
        raise TestError(f"Tests timed out after {config.timeout_seconds} seconds") from e
    except FileNotFoundError as e:
        logger.error(f"Test command not found: {config.command}")
        raise TestError(f"Test command not found: {config.command}") from e
    except Exception as e:
        logger.error(f"Failed to run tests: {e}")
        raise TestError(f"Failed to run tests: {e}") from e

    # Combine output
    output = result.stdout
    if result.stderr:
        output += "\n" + result.stderr

    # Parse test results
    test_result = _parse_test_output(output, result.returncode)

    logger.info(
        f"Tests completed: {test_result.total} total, "
        f"{test_result.passed} passed, {test_result.failed} failed, "
        f"{test_result.skipped} skipped"
    )

    return test_result


def _parse_test_output(output: str, exit_code: int) -> TestResult:
    """Parse test output to extract statistics.

    Args:
        output: Combined stdout and stderr output.
        exit_code: Exit code of test command.

    Returns:
        TestResult: Parsed test result.
    """
    # Try to parse pytest output
    pytest_pattern = r"(\d+) passed(?:, (\d+) failed(?:, (\d+) skipped)?)?(?: in ([\d.]+)s)?"
    match = re.search(pytest_pattern, output)

    if match:
        passed = int(match.group(1)) if match.group(1) else 0
        failed = int(match.group(2)) if match.group(2) else 0
        skipped = int(match.group(3)) if match.group(3) else 0
        total = passed + failed + skipped
        duration = float(match.group(4)) if match.group(4) else 0.0
    else:
        # Try to parse unittest output
        unittest_pattern = r"Ran (\d+) test(?:s)? in ([\d.]+)s"
        match = re.search(unittest_pattern, output)

        if match:
            total = int(match.group(1))
            # Look for OK or FAILED
            if "OK" in output:
                passed = total
                failed = 0
                skipped = 0
            else:
                # Parse failures
                failed_pattern = r"FAILED \(failures=(\d+)(?:, errors=(\d+))?(?:, skipped=(\d+))?\)"
                failed_match = re.search(failed_pattern, output)
                if failed_match:
                    failed = int(failed_match.group(1)) if failed_match.group(1) else 0
                    errors = int(failed_match.group(2)) if failed_match.group(2) else 0
                    skipped = int(failed_match.group(3)) if failed_match.group(3) else 0
                    failed += errors
                    passed = total - failed - skipped
                else:
                    # Fallback
                    passed = 0
                    failed = total
                    skipped = 0
            duration = float(match.group(2))
        else:
            # Fallback - use exit code
            total = 0
            passed = 0
            failed = 0
            skipped = 0
            duration = 0.0

    success = exit_code == 0

    return TestResult(
        success=success,
        exit_code=exit_code,
        output=output,
        duration=duration,
        passed=passed,
        failed=failed,
        skipped=skipped,
        total=total,
    )


def check_test_command_available(command: str) -> bool:
    """Check if test command is available.

    Args:
        command: Test command to check.

    Returns:
        bool: True if command is available, False otherwise.
    """
    try:
        subprocess.run(
            [command, "--version"],
            shell=False,
            capture_output=True,
            timeout=5,
        )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False


def get_test_files(
    root_dir: Path,
    exclude_paths: Optional[List[str]] = None,
) -> List[Path]:
    """Find test files in a directory.

    Args:
        root_dir: Root directory to search for test files.
        exclude_paths: List of paths to exclude.

    Returns:
        List[Path]: List of test file paths.
    """
    if exclude_paths is None:
        exclude_paths = []

    test_files = []

    for pattern in ("test_*.py", "*_test.py"):
        for test_file in root_dir.rglob(pattern):
            # Check if file is in excluded path
            excluded = False
            for exclude_path in exclude_paths:
                if exclude_path in str(test_file):
                    excluded = True
                    break

            if not excluded:
                test_files.append(test_file)

    return sorted(test_files)


def validate_test_config(config: TestingConfig) -> bool:
    """Validate test configuration.

    Args:
        config: Testing configuration to validate.

    Returns:
        bool: True if configuration is valid, False otherwise.
    """
    if not config.command:
        logger.error("Test command is not configured")
        return False

    if config.timeout_seconds <= 0:
        logger.error(f"Invalid timeout: {config.timeout_seconds}")
        return False

    return True
