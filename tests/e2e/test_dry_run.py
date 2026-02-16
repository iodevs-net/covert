"""End-to-end test for dry-run mode.

This module tests the dry-run functionality of Covert, which simulates
updates without making any actual changes to the system.
"""

from unittest.mock import MagicMock, patch

import pytest

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
class TestDryRunMode:
    """Test dry-run mode functionality."""

    def test_dry_run_no_actual_changes(self, tmp_path):
        """Test that dry-run doesn't make any actual changes."""
        config = Config(
            project=ProjectConfig(name="test-project", python_version="3.8"),
            testing=TestingConfig(enabled=True, command="pytest"),
            backup=BackupConfig(
                enabled=True,
                location=str(tmp_path / "backups"),
            ),
            updates=UpdatesConfig(strategy="sequential"),
            logging=LoggingConfig(level="INFO", format="simple", console=False),
            security=SecurityConfig(require_virtualenv=False),
        )

        with patch("covert.pip_interface.get_outdated_packages") as mock_outdated, patch(
            "covert.pip_interface.install_package"
        ) as mock_install, patch(
            "covert.pip_interface.uninstall_package"
        ) as mock_uninstall, patch(  # noqa: F841
            "covert.backup.create_backup"
        ) as mock_backup, patch(  # noqa: F841
            "covert.utils.is_in_virtualenv"
        ) as mock_venv:
            mock_venv.return_value = True
            mock_outdated.return_value = [
                {"name": "requests", "version": "2.28.0", "latest_version": "2.31.0"}
            ]

            # Run in dry-run mode
            session = run_update_session(
                config=config,
                dry_run=True,
                no_backup=False,
                no_tests=True,
            )

            # Verify no actual changes were made
            assert not mock_install.called
            assert not mock_uninstall.called
            # In dry-run, backup should be skipped
            assert session.dry_run is True

    def test_dry_run_reports_would_update(self, tmp_path):
        """Test that dry-run reports what would be updated."""
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

            # Verify that packages were identified for update
            assert len(session.results) == 2
            # Status should show as updated in dry-run
            assert session.results[0].status.value == "updated"

    def test_dry_run_skips_backup(self, tmp_path):
        """Test that dry-run skips backup creation."""
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()

        config = Config(
            project=ProjectConfig(name="test-project", python_version="3.8"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(
                enabled=True,
                location=str(backup_dir),
            ),
            updates=UpdatesConfig(),
            logging=LoggingConfig(level="INFO", format="simple", console=False),
            security=SecurityConfig(require_virtualenv=False),
        )

        with patch("covert.pip_interface.get_outdated_packages") as mock_outdated, patch(
            "covert.utils.is_in_virtualenv"
        ) as mock_venv:
            mock_venv.return_value = True
            mock_outdated.return_value = [
                {"name": "requests", "version": "2.28.0", "latest_version": "2.31.0"}
            ]

            session = run_update_session(
                config=config,
                dry_run=True,
                no_backup=False,  # Try to create backup
                no_tests=True,
            )

            # In dry-run, backup should not be created
            assert session.backup_file is None or session.backup_file == ""

    def test_dry_run_with_ignore_packages(self, tmp_path):
        """Test dry-run with ignore packages."""
        config = Config(
            project=ProjectConfig(name="test-project", python_version="3.8"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(ignore_packages=["flask"]),
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
                ignore_packages=["flask"],  # Also ignore from CLI
            )

            # Flask should be ignored
            assert len(session.results) == 1
            assert session.results[0].package.name == "requests"

    def test_dry_run_with_allow_only(self, tmp_path):
        """Test dry-run with allow_only_packages."""
        config = Config(
            project=ProjectConfig(name="test-project", python_version="3.8"),
            testing=TestingConfig(enabled=False),
            backup=BackupConfig(enabled=False),
            updates=UpdatesConfig(allow_only_packages=["requests"]),
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
                {"name": "django", "version": "4.0.0", "latest_version": "4.2.0"},
            ]

            session = run_update_session(
                config=config,
                dry_run=True,
                no_backup=True,
                no_tests=True,
            )

            # Only requests should be in results (based on allow_only_packages)
            assert len(session.results) == 1
            assert session.results[0].package.name == "requests"


@pytest.mark.e2e
class TestDryRunCLI:
    """Test dry-run mode via CLI."""

    def test_cli_dry_run_flag(self, tmp_path):
        """Test CLI --dry-run flag."""
        config_file = tmp_path / "covert.yaml"
        config_file.write_text("""
project:
  name: test-project
  python_version: "3.8"
testing:
  enabled: false
backup:
  enabled: true
  location: ./backups
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
                results=[
                    MagicMock(
                        package=MagicMock(name="requests"),
                        status=MagicMock(value="updated"),
                    )
                ],
                dry_run=True,
            )

            from covert.cli import main

            result = main(["--config", str(config_file), "--dry-run"])

            # Should succeed
            assert result == 0

            # Verify dry_run was passed
            call_kwargs = mock_session.call_args[1]
            assert call_kwargs["dry_run"] is True

    def test_cli_dry_run_with_verbose(self, tmp_path):
        """Test CLI --dry-run with verbose flag."""
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
  level: DEBUG
  format: detailed
  console: false
security:
  require_virtualenv: false
""")

        with patch("covert.cli.run_update_session") as mock_session:
            mock_session.return_value = MagicMock(success=True, results=[])

            from covert.cli import main

            # Test with -v flag
            result = main(["--config", str(config_file), "--dry-run", "-v"])

            assert result == 0

    def test_cli_dry_run_multiple_packages(self, tmp_path):
        """Test CLI dry-run with multiple packages."""
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
                results=[
                    MagicMock(package=MagicMock(name="flask"), status=MagicMock(value="updated")),
                    MagicMock(
                        package=MagicMock(name="requests"), status=MagicMock(value="updated")
                    ),
                    MagicMock(package=MagicMock(name="django"), status=MagicMock(value="skipped")),
                ],
            )

            from covert.cli import main

            result = main(["--config", str(config_file), "--dry-run"])

            assert result == 0
