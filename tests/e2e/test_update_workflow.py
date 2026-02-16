"""End-to-end test for complete update workflow.

This module tests the complete update workflow of Covert, including:
- Configuration loading
- Backup creation
- Package detection
- Package update
- Test execution
- Result reporting
"""

from unittest.mock import MagicMock, patch

import pytest

from covert.cli import main
from covert.config import (
    BackupConfig,
    Config,
    LoggingConfig,
    ProjectConfig,
    SecurityConfig,
    TestingConfig,
    UpdatesConfig,
)
from covert.core import run_update_session


@pytest.mark.e2e
class TestUpdateWorkflow:
    """Test complete update workflow."""

    def test_update_workflow_with_mocked_operations(self, tmp_path):
        """Test update workflow with mocked pip operations."""
        # Create temporary directory for backup
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()

        # Create config
        config = Config(
            project=ProjectConfig(name="test-project", python_version="3.8"),
            testing=TestingConfig(enabled=False),  # Disable tests for mock test
            backup=BackupConfig(
                enabled=True,
                location=str(backup_dir),
                retention_days=7,
                format="txt",
            ),
            updates=UpdatesConfig(
                strategy="sequential",
                version_policy="safe",
            ),
            logging=LoggingConfig(
                level="INFO",
                format="simple",
                console=False,
            ),
            security=SecurityConfig(
                require_virtualenv=False,
            ),
        )

        # Mock the pip operations
        with patch("covert.pip_interface.get_outdated_packages") as mock_outdated, patch(
            "covert.backup.create_backup"
        ) as mock_backup, patch("covert.utils.is_in_virtualenv") as mock_venv:
            # Set up mocks
            mock_venv.return_value = True
            mock_backup.return_value = str(backup_dir / "backup_test.txt")

            mock_outdated.return_value = [
                {"name": "requests", "version": "2.28.0", "latest_version": "2.31.0"}
            ]

            # Run update session
            session = run_update_session(
                config=config,
                dry_run=False,
                no_backup=True,  # Skip actual backup
                no_tests=True,
            )

            # Verify results
            assert session is not None
            assert session.start_time is not None
            assert len(session.results) == 1

    def test_update_workflow_dry_run_mode(self, tmp_path):
        """Test update workflow in dry-run mode."""
        # Create config with dry-run
        config = Config(
            project=ProjectConfig(name="test-project", python_version="3.8"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=True, location=str(tmp_path / "backups")),
            updates=UpdatesConfig(strategy="sequential"),
            logging=LoggingConfig(level="INFO", format="simple", console=False),
            security=SecurityConfig(require_virtualenv=False),
        )

        with patch("covert.pip_interface.get_outdated_packages") as mock_outdated, patch(
            "covert.utils.is_in_virtualenv"
        ) as mock_venv:
            mock_venv.return_value = True
            mock_outdated.return_value = [
                {"name": "flask", "version": "2.0.0", "latest_version": "2.3.0"}
            ]

            # Run with dry_run=True
            session = run_update_session(
                config=config,
                dry_run=True,
                no_backup=True,
                no_tests=True,
            )

            # In dry-run, the backup should NOT be created
            assert session.dry_run is True

    def test_update_workflow_with_ignore_list(self, tmp_path):
        """Test update workflow with package ignore list."""
        config = Config(
            project=ProjectConfig(name="test-project", python_version="3.8"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(
                strategy="sequential",
                ignore_packages=["flask", "django"],  # Ignore these packages
            ),
            logging=LoggingConfig(level="INFO", format="simple", console=False),
            security=SecurityConfig(require_virtualenv=False),
        )

        with patch("covert.pip_interface.get_outdated_packages") as mock_outdated, patch(
            "covert.utils.is_in_virtualenv"
        ) as mock_venv:
            mock_venv.return_value = True
            mock_outdated.return_value = [
                {"name": "flask", "version": "2.0.0", "latest_version": "2.3.0"},
                {"name": "requests", "version": "2.28.0", "latest_version": "2.31.0"},
            ]

            session = run_update_session(
                config=config,
                dry_run=True,
                no_backup=True,
                no_tests=True,
                ignore_packages=["flask"],  # Also ignore flask from CLI
            )

            # Verify flask was ignored
            assert len(session.results) == 1
            assert session.results[0].package.name == "requests"

    def test_cli_main_update_flow(self, tmp_path):
        """Test CLI main function update flow."""
        config_file = tmp_path / "covert.yaml"
        config_file.write_text("""
project:
  name: test-project
  python_version: "3.8"
testing:
  enabled: false
backup:
  enabled: false
updates:
  strategy: sequential
  version_policy: safe
logging:
  level: INFO
  format: simple
  console: false
security:
  require_virtualenv: false
""")

        with patch("covert.cli.run_update_session") as mock_session:
            mock_session.return_value = MagicMock(
                success=True,
                results=[],
                pre_test_passed=True,
            )

            result = main(["--config", str(config_file), "--no-tests"])

            # Should succeed
            assert result == 0

    def test_cli_dry_run_flag(self, tmp_path):
        """Test CLI dry-run flag."""
        config_file = tmp_path / "covert.yaml"
        config_file.write_text("""
project:
  name: test-project
  python_version: "3.8"
testing:
  enabled: false
backup:
  enabled: false
updates:
  strategy: sequential
logging:
  level: INFO
  format: simple
  console: false
security:
  require_virtualenv: false
""")

        with patch("covert.cli.run_update_session") as mock_session:
            mock_session.return_value = MagicMock(
                success=True,
                results=[],
            )

            result = main(["--config", str(config_file), "--dry-run"])

            # Should succeed
            assert result == 0


@pytest.mark.e2e
class TestUpdateWorkflowEdgeCases:
    """Test edge cases in update workflow."""

    def test_no_outdated_packages(self, tmp_path):
        """Test workflow when no packages are outdated."""
        config = Config(
            project=ProjectConfig(name="test-project", python_version="3.8"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(),
            logging=LoggingConfig(level="INFO", format="simple", console=False),
            security=SecurityConfig(require_virtualenv=False),
        )

        with patch("covert.pip_interface.get_outdated_packages") as mock_outdated, patch(
            "covert.utils.is_in_virtualenv"
        ) as mock_venv:
            mock_venv.return_value = True
            mock_outdated.return_value = []  # No outdated packages

            session = run_update_session(
                config=config,
                dry_run=True,
                no_backup=True,
                no_tests=True,
            )

            # Should complete successfully with no results
            assert session is not None
            assert len(session.results) == 0

    def test_allow_only_packages_filter(self, tmp_path):
        """Test workflow with allow_only_packages filter."""
        config = Config(
            project=ProjectConfig(name="test-project", python_version="3.8"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(allow_only_packages=["requests"]),  # Only allow requests
            logging=LoggingConfig(level="INFO", format="simple", console=False),
            security=SecurityConfig(require_virtualenv=False),
        )

        with patch("covert.pip_interface.get_outdated_packages") as mock_outdated, patch(
            "covert.utils.is_in_virtualenv"
        ) as mock_venv:
            mock_venv.return_value = True
            mock_outdated.return_value = [
                {"name": "flask", "version": "2.0.0", "latest_version": "2.3.0"},
                {"name": "requests", "version": "2.28.0", "latest_version": "2.31.0"},
            ]

            session = run_update_session(
                config=config,
                dry_run=True,
                no_backup=True,
                no_tests=True,
            )

            # Only requests should be updated
            assert len(session.results) == 1
            assert session.results[0].package.name == "requests"
