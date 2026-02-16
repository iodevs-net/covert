"""End-to-end test for rollback scenarios.

This module tests the rollback functionality of Covert, including:
- Automatic rollback on test failure
- Manual rollback from backup
- Rollback verification
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from covert.backup import restore_backup
from covert.config import (
    BackupConfig,
    Config,
    LoggingConfig,
    ProjectConfig,
    SecurityConfig,
    TestingConfig,
    UpdatesConfig,
)
from covert.core import UpdateStatus, _update_package
from covert.exceptions import BackupError


@pytest.mark.e2e
class TestRollbackScenario:
    """Test rollback scenarios."""

    def test_rollback_on_test_failure(self, tmp_path):
        """Test automatic rollback when tests fail after update."""
        from covert.core import PackageInfo

        # Create config
        config = Config(
            project=ProjectConfig(name="test-project", python_version="3.8"),
            testing=TestingConfig(
                enabled=True,
                command="pytest",
                args=["-v"],
            ),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(),
            logging=LoggingConfig(level="INFO", format="simple", console=False),
            security=SecurityConfig(require_virtualenv=False),
        )

        # Mock the update package function
        with patch("covert.pip_interface.install_package") as mock_install, patch(
            "covert.pip_interface.uninstall_package"
        ) as mock_uninstall, patch("covert.tester.run_tests") as mock_tests:
            # Set up mocks
            mock_install.return_value = {"name": "requests", "version": "2.31.0"}
            mock_tests.return_value = MagicMock(success=False)  # Tests fail

            # Create package info
            package = PackageInfo(
                name="requests",
                current_version="2.28.0",
                latest_version="2.31.0",
            )

            # Run update (should rollback)
            result = _update_package(
                package=package,
                config=config,
                dry_run=False,
                no_tests=False,
            )

            # Verify rollback occurred
            assert result.status == UpdateStatus.ROLLED_BACK
            assert mock_uninstall.called
            # Should have called install to restore old version
            assert mock_install.call_count == 2  # First for update, second for rollback

    def test_rollback_successful_update(self, tmp_path):
        """Test successful update without rollback."""
        from covert.core import PackageInfo

        config = Config(
            project=ProjectConfig(name="test-project", python_version="3.8"),
            testing=TestingConfig(enabled=True, command="pytest", args=["-v"]),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(),
            logging=LoggingConfig(level="INFO", format="simple", console=False),
            security=SecurityConfig(require_virtualenv=False),
        )

        with patch("covert.pip_interface.install_package") as mock_install, patch(
            "covert.tester.run_tests"
        ) as mock_tests:
            mock_install.return_value = {"name": "requests", "version": "2.31.0"}
            mock_tests.return_value = MagicMock(success=True)  # Tests pass

            package = PackageInfo(
                name="requests",
                current_version="2.28.0",
                latest_version="2.31.0",
            )

            result = _update_package(
                package=package,
                config=config,
                dry_run=False,
                no_tests=False,
            )

            # Verify successful update
            assert result.status == UpdateStatus.UPDATED
            assert result.test_passed is True

    def test_restore_backup_from_file(self, tmp_path):
        """Test restoring packages from backup file."""
        # Create backup file
        backup_file = tmp_path / "backup.txt"
        backup_file.write_text("requests==2.28.0\nflask==2.0.0\n")

        # Mock install_package
        with patch("covert.pip_interface.install_package") as mock_install:
            mock_install.return_value = {"name": "requests", "version": "2.28.0"}

            # Restore from backup
            restored = restore_backup(backup_file, dry_run=False)

            # Verify restoration
            assert len(restored) == 2
            assert mock_install.call_count == 2

    def test_restore_backup_dry_run(self, tmp_path):
        """Test restoring packages in dry-run mode."""
        # Create backup file
        backup_file = tmp_path / "backup.txt"
        backup_file.write_text("requests==2.28.0\ndjango==4.0.0\n")

        with patch("covert.pip_interface.install_package") as mock_install:
            # Restore in dry-run mode
            restored = restore_backup(backup_file, dry_run=True)

            # Verify no actual restoration
            assert len(restored) == 2
            assert not mock_install.called

    def test_restore_json_backup(self, tmp_path):
        """Test restoring from JSON format backup."""
        # Create JSON backup file
        backup_file = tmp_path / "backup.json"
        backup_file.write_text(
            json.dumps(
                [
                    {"name": "requests", "version": "2.28.0"},
                    {"name": "flask", "version": "2.0.0"},
                ]
            )
        )

        with patch("covert.pip_interface.install_package") as mock_install:
            mock_install.return_value = {"name": "requests", "version": "2.28.0"}

            restored = restore_backup(backup_file, dry_run=False)

            assert len(restored) == 2

    def test_restore_nonexistent_backup(self):
        """Test restoring from non-existent backup file."""
        with pytest.raises(BackupError, match="Backup file not found"):
            restore_backup("/nonexistent/path/backup.txt")


@pytest.mark.e2e
class TestRollbackEdgeCases:
    """Test edge cases in rollback scenarios."""

    def test_partial_rollback_on_multiple_failures(self, tmp_path):
        """Test partial rollback when some packages fail to restore."""
        from covert.core import PackageInfo

        config = Config(
            project=ProjectConfig(name="test-project", python_version="3.8"),
            testing=TestingConfig(enabled=True, command="pytest"),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(),
            logging=LoggingConfig(level="INFO", format="simple", console=False),
            security=SecurityConfig(require_virtualenv=False),
        )

        with patch("covert.pip_interface.install_package") as mock_install, patch(
            "covert.tester.run_tests"
        ) as mock_tests:
            # First call succeeds, second call (rollback) fails
            mock_install.side_effect = [
                {"name": "requests", "version": "2.31.0"},  # Initial install succeeds
                Exception("Rollback failed"),  # Rollback fails
            ]
            mock_tests.return_value = MagicMock(success=False)  # Tests fail

            package = PackageInfo(
                name="requests",
                current_version="2.28.0",
                latest_version="2.31.0",
            )

            result = _update_package(
                package=package,
                config=config,
                dry_run=False,
                no_tests=False,
            )

            # Should be critical failure because rollback failed
            assert result.status == UpdateStatus.CRITICAL_FAILURE

    def test_update_with_disabled_rollback(self, tmp_path):
        """Test update when backup is disabled (no rollback possible)."""
        from covert.core import PackageInfo

        config = Config(
            project=ProjectConfig(name="test-project", python_version="3.8"),
            testing=TestingConfig(enabled=False),  # Tests disabled
            backup=BackupConfig(enabled=False),  # Backup disabled
            updates=UpdatesConfig(),
            logging=LoggingConfig(level="INFO", format="simple", console=False),
            security=SecurityConfig(require_virtualenv=False),
        )

        with patch("covert.pip_interface.install_package") as mock_install:
            mock_install.return_value = {"name": "requests", "version": "2.31.0"}

            package = PackageInfo(
                name="requests",
                current_version="2.28.0",
                latest_version="2.31.0",
            )

            result = _update_package(
                package=package,
                config=config,
                dry_run=False,
                no_tests=True,
            )

            # Update should succeed (tests disabled, so no rollback needed)
            assert result.status == UpdateStatus.UPDATED
