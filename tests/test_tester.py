"""Unit tests for tester module."""

from unittest.mock import MagicMock, patch

import pytest

from covert.config import TestingConfig
from covert.exceptions import TestError
from covert.tester import (
    TestResult,
    check_test_command_available,
    get_test_files,
    run_tests,
    validate_test_config,
)


class TestRunTests:
    """Tests for run_tests function."""

    @patch("covert.tester.subprocess.run")
    def test_successful_tests(self, mock_run):
        """Test successful test execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "5 passed in 0.5s"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        config = TestingConfig(
            enabled=True,
            command="pytest",
            args=["-v"],
            timeout_seconds=300,
        )

        result = run_tests(config)

        assert result.success is True
        assert result.exit_code == 0

    @patch("covert.tester.subprocess.run")
    def test_failed_tests(self, mock_run):
        """Test failed test execution."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "1 failed, 4 passed in 0.5s"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        config = TestingConfig(
            enabled=True,
            command="pytest",
            args=["-v"],
            timeout_seconds=300,
        )

        result = run_tests(config)

        assert result.success is False
        assert result.exit_code == 1

    @patch("covert.tester.subprocess.run")
    def test_disabled_testing(self, mock_run):
        """Test that disabled testing returns success."""
        config = TestingConfig(enabled=False)

        result = run_tests(config)

        assert result.success is True
        assert result.exit_code == 0
        mock_run.assert_not_called()

    @patch("covert.tester.subprocess.run")
    def test_timeout(self, mock_run):
        """Test handling of test timeout."""
        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired("pytest", 300)

        config = TestingConfig(
            enabled=True,
            command="pytest",
            args=[],
            timeout_seconds=300,
        )

        with pytest.raises(TestError):
            run_tests(config)

    @patch("covert.tester.subprocess.run")
    def test_command_not_found(self, mock_run):
        """Test handling of command not found."""
        mock_run.side_effect = FileNotFoundError("pytest not found")

        config = TestingConfig(
            enabled=True,
            command="pytest",
            args=[],
            timeout_seconds=300,
        )

        with pytest.raises(TestError):
            run_tests(config)

    @patch("covert.tester.subprocess.run")
    def test_with_extra_args(self, mock_run):
        """Test test execution with extra arguments."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "5 passed in 0.5s"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        config = TestingConfig(
            enabled=True,
            command="pytest",
            args=["-v"],
            timeout_seconds=300,
        )

        run_tests(config, extra_args=["--cov=covert"])

        call_args = mock_run.call_args[0][0]
        assert "--cov=covert" in call_args


class TestParseTestOutput:
    """Tests for _parse_test_output function."""

    def test_pytest_output(self):
        """Test parsing pytest output."""
        from covert.tester import _parse_test_output, TestResult

        output = "5 passed in 1.23s"
        result = _parse_test_output(output, 0)

        assert result.success is True
        assert result.passed == 5
        assert result.failed == 0
        assert result.total == 5
        assert result.duration == 1.23


class TestCheckTestCommandAvailable:
    """Tests for check_test_command_available function."""

    @patch("covert.tester.subprocess.run")
    def test_command_available(self, mock_run):
        """Test that available command returns True."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "pytest 7.0.0"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = check_test_command_available("pytest")

        assert result is True

    @patch("covert.tester.subprocess.run")
    def test_command_not_available(self, mock_run):
        """Test that unavailable command returns False."""
        mock_run.side_effect = FileNotFoundError("pytest not found")

        result = check_test_command_available("pytest")

        assert result is False


class TestGetTestFiles:
    """Tests for get_test_files function."""

    @patch("covert.tester.Path.rglob")
    def test_find_test_files(self, mock_rglob):
        """Test finding test files."""
        from pathlib import Path

        # Mock test files
        mock_files = [
            Path("tests/test_example.py"),
            Path("tests/utils_test.py"),
            Path("tests/e2e/test_e2e.py"),
        ]
        mock_rglob.return_value = iter(mock_files)

        test_files = get_test_files(Path("tests"))

        assert len(test_files) == 3

    @patch("covert.tester.Path.rglob")
    def test_exclude_paths(self, mock_rglob):
        """Test excluding certain paths."""
        from pathlib import Path

        # Mock test files
        mock_files = [
            Path("tests/test_example.py"),
            Path("tests/e2e/test_e2e.py"),
        ]
        mock_rglob.return_value = iter(mock_files)

        test_files = get_test_files(Path("tests"), exclude_paths=["tests/e2e"])

        assert len(test_files) == 1
        assert test_files[0] == Path("tests/test_example.py")


class TestValidateTestConfig:
    """Tests for validate_test_config function."""

    def test_valid_config(self):
        """Test validation of valid config."""
        config = TestingConfig(
            enabled=True,
            command="pytest",
            args=["-v"],
            timeout_seconds=300,
        )

        result = validate_test_config(config)

        assert result is True

    def test_missing_command(self):
        """Test validation fails without command."""
        config = TestingConfig(
            enabled=True,
            command="",
            args=[],
            timeout_seconds=300,
        )

        result = validate_test_config(config)

        assert result is False

    def test_invalid_timeout(self):
        """Test validation fails with invalid timeout."""
        config = TestingConfig(
            enabled=True,
            command="pytest",
            args=[],
            timeout_seconds=0,
        )

        result = validate_test_config(config)

        assert result is False

    def test_negative_timeout(self):
        """Test validation fails with negative timeout."""
        config = TestingConfig(
            enabled=True,
            command="pytest",
            args=[],
            timeout_seconds=-10,
        )

        result = validate_test_config(config)

        assert result is False


class TestTestResult:
    """Tests for TestResult dataclass."""

    def test_test_result_creation(self):
        """Test creating a TestResult."""
        result = TestResult(
            success=True,
            exit_code=0,
            output="5 passed in 0.5s",
            duration=0.5,
            passed=5,
            failed=0,
            skipped=0,
            total=5,
        )

        assert result.success is True
        assert result.exit_code == 0
        assert result.passed == 5
        assert result.failed == 0
        assert result.skipped == 0
        assert result.total == 5
