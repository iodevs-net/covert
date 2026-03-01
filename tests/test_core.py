"""Unit tests for core module."""

from datetime import datetime
from unittest.mock import patch

import pytest

from covert.config import (
    BackupConfig,
    Config,
    ProjectConfig,
    SecurityConfig,
    TestingConfig,
    UpdatesConfig,
)
from covert.core import (
    PackageInfo,
    UpdateResult,
    UpdateSession,
    UpdateStatus,
    _filter_packages,
    _update_package,
    run_update_session,
)
from covert.exceptions import SecurityError, UpdateError, ValidationError


class TestUpdateStatus:
    """Tests for UpdateStatus enum."""

    def test_status_values(self):
        """Test that all status values are defined."""
        assert UpdateStatus.UPDATED.value == "updated"
        assert UpdateStatus.ROLLED_BACK.value == "rolled_back"
        assert UpdateStatus.FAILED_INSTALL.value == "failed_install"
        assert UpdateStatus.CRITICAL_FAILURE.value == "critical_failure"
        assert UpdateStatus.SKIPPED.value == "skipped"
        assert UpdateStatus.PENDING.value == "pending"


class TestPackageInfo:
    """Tests for PackageInfo dataclass."""

    def test_package_info_creation(self):
        """Test creating PackageInfo."""
        pkg = PackageInfo(
            name="requests",
            current_version="2.25.0",
            latest_version="2.31.0",
            package_type="regular",
        )

        assert pkg.name == "requests"
        assert pkg.current_version == "2.25.0"
        assert pkg.latest_version == "2.31.0"
        assert pkg.package_type == "regular"


class TestUpdateResult:
    """Tests for UpdateResult dataclass."""

    def test_update_result_creation(self):
        """Test creating UpdateResult."""
        pkg = PackageInfo(
            name="requests",
            current_version="2.25.0",
            latest_version="2.31.0",
        )
        result = UpdateResult(
            package=pkg,
            status=UpdateStatus.UPDATED,
            timestamp=datetime.now(),
        )

        assert result.package.name == "requests"
        assert result.status == UpdateStatus.UPDATED
        assert result.test_passed is False


class TestUpdateSession:
    """Tests for UpdateSession dataclass."""

    def test_session_creation(self):
        """Test creating UpdateSession."""
        session = UpdateSession(
            start_time=datetime.now(),
        )

        assert session.results == []
        assert session.pre_test_passed is False

    def test_summary_property(self):
        """Test summary property."""
        session = UpdateSession(
            start_time=datetime.now(),
            results=[
                UpdateResult(
                    package=PackageInfo("pkg1", "1.0", "2.0"),
                    status=UpdateStatus.UPDATED,
                    timestamp=datetime.now(),
                ),
                UpdateResult(
                    package=PackageInfo("pkg2", "1.0", "2.0"),
                    status=UpdateStatus.ROLLED_BACK,
                    timestamp=datetime.now(),
                ),
            ],
        )

        summary = session.summary

        assert summary["updated"] == 1
        assert summary["rolled_back"] == 1

    def test_success_property(self):
        """Test success property."""
        session = UpdateSession(
            start_time=datetime.now(),
            results=[
                UpdateResult(
                    package=PackageInfo("pkg1", "1.0", "2.0"),
                    status=UpdateStatus.UPDATED,
                    timestamp=datetime.now(),
                ),
            ],
        )

        assert session.success is True

    def test_success_property_with_critical_failure(self):
        """Test success property with critical failure."""
        session = UpdateSession(
            start_time=datetime.now(),
            results=[
                UpdateResult(
                    package=PackageInfo("pkg1", "1.0", "2.0"),
                    status=UpdateStatus.CRITICAL_FAILURE,
                    timestamp=datetime.now(),
                ),
            ],
        )

        assert session.success is False

    def test_updated_count_property(self):
        """Test updated_count property."""
        session = UpdateSession(
            start_time=datetime.now(),
            results=[
                UpdateResult(
                    package=PackageInfo("pkg1", "1.0", "2.0"),
                    status=UpdateStatus.UPDATED,
                    timestamp=datetime.now(),
                ),
                UpdateResult(
                    package=PackageInfo("pkg2", "1.0", "2.0"),
                    status=UpdateStatus.UPDATED,
                    timestamp=datetime.now(),
                ),
            ],
        )

        assert session.updated_count == 2

    def test_rolled_back_count_property(self):
        """Test rolled_back_count property."""
        session = UpdateSession(
            start_time=datetime.now(),
            results=[
                UpdateResult(
                    package=PackageInfo("pkg1", "1.0", "2.0"),
                    status=UpdateStatus.ROLLED_BACK,
                    timestamp=datetime.now(),
                ),
            ],
        )

        assert session.rolled_back_count == 1


class TestFilterPackages:
    """Tests for _filter_packages function."""

    def test_no_filtering(self):
        """Test filtering with no filters."""
        packages = [
            {"name": "pkg1", "version": "1.0"},
            {"name": "pkg2", "version": "2.0"},
        ]

        filtered = _filter_packages(packages, [], None, None, None)

        assert len(filtered) == 2

    def test_ignore_from_config(self):
        """Test ignoring packages from config."""
        packages = [
            {"name": "pkg1", "version": "1.0"},
            {"name": "pkg2", "version": "2.0"},
        ]

        filtered = _filter_packages(packages, ["pkg1"], None, None, None)

        assert len(filtered) == 1
        assert filtered[0]["name"] == "pkg2"

    def test_ignore_from_cli(self):
        """Test ignoring packages from CLI."""
        packages = [
            {"name": "pkg1", "version": "1.0"},
            {"name": "pkg2", "version": "2.0"},
        ]

        filtered = _filter_packages(packages, [], None, ["pkg1"], None)

        assert len(filtered) == 1
        assert filtered[0]["name"] == "pkg2"

    def test_allow_only_from_config(self):
        """Test allowing only specific packages from config."""
        packages = [
            {"name": "pkg1", "version": "1.0"},
            {"name": "pkg2", "version": "2.0"},
        ]

        filtered = _filter_packages(packages, [], ["pkg1"], None, None)

        assert len(filtered) == 1
        assert filtered[0]["name"] == "pkg1"

    def test_allow_only_from_cli(self):
        """Test allowing only specific packages from CLI."""
        packages = [
            {"name": "pkg1", "version": "1.0"},
            {"name": "pkg2", "version": "2.0"},
        ]

        filtered = _filter_packages(packages, [], None, None, ["pkg1"])

        assert len(filtered) == 1
        assert filtered[0]["name"] == "pkg1"


class TestUpdatePackage:
    """Tests for _update_package function."""

    @patch("covert.core.is_breaking_change")
    @patch("covert.core.install_package")
    def test_successful_update(self, mock_install, mock_breaking):
        """Test successful package update."""
        mock_breaking.return_value = False
        mock_install.return_value = {"name": "requests", "version": "2.31.0"}

        config = Config(
            project=ProjectConfig(name="Test", python_version="3.11"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(version_policy="safe"),
            security=SecurityConfig(require_virtualenv=False),
        )

        pkg = PackageInfo(
            name="requests",
            current_version="2.25.0",
            latest_version="2.31.0",
        )

        result = _update_package(pkg, config, dry_run=False, no_tests=True)

        assert result.status == UpdateStatus.UPDATED

    @patch("covert.core.is_breaking_change")
    def test_breaking_change_skipped(self, mock_breaking):
        """Test that breaking changes are skipped."""
        mock_breaking.return_value = True

        config = Config(
            project=ProjectConfig(name="Test", python_version="3.11"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(version_policy="safe"),
            security=SecurityConfig(require_virtualenv=False),
        )

        pkg = PackageInfo(
            name="requests",
            current_version="1.0.0",
            latest_version="2.0.0",
        )

        result = _update_package(pkg, config, dry_run=False, no_tests=True)

        assert result.status == UpdateStatus.SKIPPED

    @patch("covert.core.install_package")
    def test_dry_run(self, mock_install):
        """Test dry run mode."""
        config = Config(
            project=ProjectConfig(name="Test", python_version="3.11"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(version_policy="safe"),
            security=SecurityConfig(require_virtualenv=False),
        )

        pkg = PackageInfo(
            name="requests",
            current_version="2.25.0",
            latest_version="2.31.0",
        )

        result = _update_package(pkg, config, dry_run=True, no_tests=True)

        assert result.status == UpdateStatus.UPDATED
        mock_install.assert_not_called()

    @patch("covert.core.is_breaking_change")
    @patch("covert.core.install_package")
    def test_install_failure(self, mock_install, mock_breaking):
        """Test handling of installation failure."""
        from covert.exceptions import PipError

        mock_breaking.return_value = False
        mock_install.side_effect = PipError("Installation failed")

        config = Config(
            project=ProjectConfig(name="Test", python_version="3.11"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(version_policy="safe"),
            security=SecurityConfig(require_virtualenv=False),
        )

        pkg = PackageInfo(
            name="requests",
            current_version="2.25.0",
            latest_version="2.31.0",
        )

        result = _update_package(pkg, config, dry_run=False, no_tests=True)

        assert result.status == UpdateStatus.FAILED_INSTALL
        assert result.error_message is not None


class TestRunUpdateSession:
    """Tests for run_update_session function."""

    @patch("covert.core.is_in_virtualenv")
    @patch("covert.core.get_outdated_packages")
    def test_no_virtualenv_raises_error(self, mock_outdated, mock_venv):
        """Test that missing virtualenv raises error."""
        from covert.exceptions import SecurityError

        mock_venv.return_value = False

        config = Config(
            project=ProjectConfig(name="Test", python_version="3.11"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(version_policy="safe"),
            security=SecurityConfig(require_virtualenv=True),
        )

        with pytest.raises(SecurityError):
            run_update_session(config)

    @patch("covert.core.is_in_virtualenv")
    @patch("covert.core.get_outdated_packages")
    def test_no_outdated_packages(self, mock_outdated, mock_venv):
        """Test handling when no outdated packages exist."""
        mock_venv.return_value = True
        mock_outdated.return_value = []

        config = Config(
            project=ProjectConfig(name="Test", python_version="3.11"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(version_policy="safe"),
            security=SecurityConfig(require_virtualenv=False),
        )

        session = run_update_session(config)

        assert session.updated_count == 0

    @patch("covert.core.is_in_virtualenv")
    @patch("covert.core._update_package")
    @patch("covert.core.get_outdated_packages")
    def test_successful_session(self, mock_outdated, mock_update, mock_venv):
        """Test successful update session."""
        mock_venv.return_value = True
        mock_outdated.return_value = [
            {"name": "requests", "version": "2.25.0", "latest_version": "2.31.0"},
        ]

        pkg = PackageInfo(
            name="requests",
            current_version="2.25.0",
            latest_version="2.31.0",
        )
        mock_update.return_value = UpdateResult(
            package=pkg,
            status=UpdateStatus.UPDATED,
            timestamp=datetime.now(),
        )

        config = Config(
            project=ProjectConfig(name="Test", python_version="3.11"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(version_policy="safe"),
            security=SecurityConfig(require_virtualenv=False),
        )

        session = run_update_session(config)

        assert session.updated_count == 1

    @patch("covert.core.is_in_virtualenv")
    @patch("covert.core.run_tests")
    @patch("covert.core.get_outdated_packages")
    def test_preflight_test_failure(self, mock_outdated, mock_tests, mock_venv):
        """Test handling of preflight test failure."""
        from covert.exceptions import UpdateError
        from covert.tester import TestResult

        mock_venv.return_value = True
        mock_outdated.return_value = []
        mock_tests.return_value = TestResult(
            success=False,
            exit_code=1,
            output="Tests failed",
            duration=1.0,
            passed=0,
            failed=1,
            skipped=0,
            total=1,
        )

        config = Config(
            project=ProjectConfig(name="Test", python_version="3.11"),
            testing=TestingConfig(enabled=True),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(version_policy="safe"),
            security=SecurityConfig(require_virtualenv=False),
        )

        with pytest.raises(UpdateError):
            run_update_session(config)

    @patch("covert.core.is_in_virtualenv")
    @patch("covert.core.create_backup")
    @patch("covert.core.get_outdated_packages")
    def test_backup_creation(self, mock_outdated, mock_backup, mock_venv):
        """Test that backup is created."""
        mock_venv.return_value = True
        mock_outdated.return_value = []
        mock_backup.return_value = "backup.txt"

        config = Config(
            project=ProjectConfig(name="Test", python_version="3.11"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=True, location="./backups"),
            updates=UpdatesConfig(version_policy="safe"),
            security=SecurityConfig(require_virtualenv=False),
        )

        session = run_update_session(config)

        assert session.backup_file == "backup.txt"
        mock_backup.assert_called_once()

    @patch("covert.core.is_in_virtualenv")
    @patch("covert.core._update_packages_parallel")
    @patch("covert.core.get_outdated_packages")
    def test_parallel_update_mode(
        self,
        mock_outdated,
        mock_parallel,
        mock_venv,
    ):
        """Test parallel update mode."""
        from covert.core import PackageInfo, UpdateResult, UpdateStatus

        mock_venv.return_value = True
        mock_outdated.return_value = [
            {"name": "pkg1", "version": "1.0", "latest_version": "2.0"},
            {"name": "pkg2", "version": "1.0", "latest_version": "2.0"},
        ]

        mock_parallel.return_value = [
            UpdateResult(
                package=PackageInfo("pkg1", "1.0", "2.0"),
                status=UpdateStatus.UPDATED,
                timestamp=datetime.now(),
            ),
            UpdateResult(
                package=PackageInfo("pkg2", "1.0", "2.0"),
                status=UpdateStatus.UPDATED,
                timestamp=datetime.now(),
            ),
        ]

        config = Config(
            project=ProjectConfig(name="Test", python_version="3.11"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(version_policy="safe", max_parallel=3),
            security=SecurityConfig(require_virtualenv=False),
        )

        session = run_update_session(config, parallel=True)

        assert session.updated_count == 2
        mock_parallel.assert_called_once()
        call_args = mock_parallel.call_args
        assert call_args[0][4] == 3  # max_parallel

    @patch("covert.core.is_in_virtualenv")
    @patch("covert.core._update_packages_parallel")
    @patch("covert.core.get_outdated_packages")
    def test_parallel_update_with_failures(
        self,
        mock_outdated,
        mock_parallel,
        mock_venv,
    ):
        """Test parallel update mode with some failures."""
        from covert.core import PackageInfo, UpdateResult, UpdateStatus

        mock_venv.return_value = True
        mock_outdated.return_value = [
            {"name": "pkg1", "version": "1.0", "latest_version": "2.0"},
            {"name": "pkg2", "version": "1.0", "latest_version": "2.0"},
        ]

        mock_parallel.return_value = [
            UpdateResult(
                package=PackageInfo("pkg1", "1.0", "2.0"),
                status=UpdateStatus.UPDATED,
                timestamp=datetime.now(),
            ),
            UpdateResult(
                package=PackageInfo("pkg2", "1.0", "2.0"),
                status=UpdateStatus.FAILED_INSTALL,
                timestamp=datetime.now(),
                error_message="Install failed",
            ),
        ]

        config = Config(
            project=ProjectConfig(name="Test", python_version="3.11"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(version_policy="safe"),
            security=SecurityConfig(require_virtualenv=False),
        )

        session = run_update_session(config, parallel=True)

        assert session.updated_count == 1
        assert session.summary.get("failed_install") == 1
        assert session.success is True  # No critical failures


class TestUpdatePackagesParallel:
    """Tests for _update_packages_parallel function."""

    @patch("covert.core._update_package")
    def test_parallel_updates_success(self, mock_update):
        """Test successful parallel updates."""
        from covert.core import PackageInfo, UpdateResult, UpdateStatus, _update_packages_parallel

        # Mock successful updates
        mock_update.side_effect = [
            UpdateResult(
                package=PackageInfo("pkg1", "1.0", "2.0"),
                status=UpdateStatus.UPDATED,
                timestamp=datetime.now(),
            ),
            UpdateResult(
                package=PackageInfo("pkg2", "1.0", "2.0"),
                status=UpdateStatus.UPDATED,
                timestamp=datetime.now(),
            ),
        ]

        packages = [
            {"name": "pkg1", "version": "1.0", "latest_version": "2.0"},
            {"name": "pkg2", "version": "1.0", "latest_version": "2.0"},
        ]

        config = Config(
            project=ProjectConfig(name="Test", python_version="3.11"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(version_policy="safe"),
            security=SecurityConfig(require_virtualenv=False),
        )

        results = _update_packages_parallel(packages, config, False, False, 2)

        assert len(results) == 2
        assert all(r.status == UpdateStatus.UPDATED for r in results)
        assert mock_update.call_count == 2

    @patch("covert.core._update_package")
    def test_parallel_updates_with_exception(self, mock_update):
        """Test parallel updates with exception handling."""
        from covert.core import PackageInfo, UpdateResult, UpdateStatus, _update_packages_parallel

        # Mock one update to fail with exception
        mock_update.side_effect = [
            UpdateResult(
                package=PackageInfo("pkg1", "1.0", "2.0"),
                status=UpdateStatus.UPDATED,
                timestamp=datetime.now(),
            ),
            RuntimeError("Update failed"),
        ]

        packages = [
            {"name": "pkg1", "version": "1.0", "latest_version": "2.0"},
            {"name": "pkg2", "version": "1.0", "latest_version": "2.0"},
        ]

        config = Config(
            project=ProjectConfig(name="Test", python_version="3.11"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(version_policy="safe"),
            security=SecurityConfig(require_virtualenv=False),
        )

        results = _update_packages_parallel(packages, config, False, False, 2)

        assert len(results) == 2
        assert results[0].status == UpdateStatus.UPDATED
        assert results[1].status == UpdateStatus.FAILED_INSTALL
        assert results[1].error_message == "Update failed"
