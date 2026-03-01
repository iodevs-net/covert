"""Tests for the CLI module.

This module tests the command-line interface functionality including argument
parsing, configuration loading, and error handling.
"""

from unittest.mock import MagicMock, patch

import pytest

from covert.cli import load_configuration, main, parse_args, parse_ignore_list
from covert.config import (
    BackupConfig,
    Config,
    LoggingConfig,
    NotificationConfig,
    ProjectConfig,
    ReportConfig,
    SecurityConfig,
    TestingConfig,
    UpdatesConfig,
)
from covert.exceptions import ConfigError


def create_test_config():
    """Create a test Config object with all required attributes."""
    return Config(
        project=ProjectConfig(name="test", python_version="3.8"),
        testing=TestingConfig(),
        updates=UpdatesConfig(),
        backup=BackupConfig(),
        logging=LoggingConfig(),
        security=SecurityConfig(require_virtualenv=False),
        notifications=NotificationConfig(),
        reports=ReportConfig(),
    )


class TestParseArgs:
    """Test argument parsing functionality."""

    def test_parse_args_default(self):
        """Test parsing with no arguments."""
        args = parse_args([])
        assert args.config is None
        assert args.dry_run is False
        assert args.ignore is None
        assert args.verbose == 0
        assert args.no_backup is False
        assert args.no_tests is False
        assert args.version is False
        assert args.parallel is False

    def test_parse_args_config(self):
        """Test parsing --config argument."""
        args = parse_args(["--config", "covert.yaml"])
        assert args.config == "covert.yaml"

    def test_parse_args_config_short(self):
        """Test parsing -c argument."""
        args = parse_args(["-c", "covert.toml"])
        assert args.config == "covert.toml"

    def test_parse_args_dry_run(self):
        """Test parsing --dry-run argument."""
        args = parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_parse_args_ignore(self):
        """Test parsing --ignore argument."""
        args = parse_args(["--ignore", "package1,package2,package3"])
        assert args.ignore == "package1,package2,package3"

    def test_parse_args_verbose(self):
        """Test parsing --verbose argument."""
        args = parse_args(["--verbose"])
        assert args.verbose == 1

    def test_parse_args_verbose_short(self):
        """Test parsing -v argument."""
        args = parse_args(["-v"])
        assert args.verbose == 1

    def test_parse_args_verbose_multiple(self):
        """Test parsing multiple --verbose arguments."""
        args = parse_args(["-vv"])
        assert args.verbose == 2

    def test_parse_args_no_backup(self):
        """Test parsing --no-backup argument."""
        args = parse_args(["--no-backup"])
        assert args.no_backup is True

    def test_parse_args_no_tests(self):
        """Test parsing --no-tests argument."""
        args = parse_args(["--no-tests"])
        assert args.no_tests is True

    def test_parse_args_version(self):
        """Test parsing --version argument."""
        args = parse_args(["--version"])
        assert args.version is True

    def test_parse_args_parallel(self):
        """Test parsing --parallel argument."""
        args = parse_args(["--parallel"])
        assert args.parallel is True

    def test_parse_args_combined(self):
        """Test parsing multiple arguments together."""
        args = parse_args(
            [
                "--config",
                "covert.yaml",
                "--dry-run",
                "--ignore",
                "pkg1,pkg2",
                "-vv",
                "--no-backup",
                "--no-tests",
            ]
        )
        assert args.config == "covert.yaml"
        assert args.dry_run is True
        assert args.ignore == "pkg1,pkg2"
        assert args.verbose == 2
        assert args.no_backup is True
        assert args.no_tests is True


class TestParseIgnoreList:
    """Test ignore list parsing functionality."""

    def test_parse_ignore_list_none(self):
        """Test parsing None returns None."""
        result = parse_ignore_list(None)
        assert result is None

    def test_parse_ignore_list_single(self):
        """Test parsing single package."""
        result = parse_ignore_list("package1")
        assert result == ["package1"]

    def test_parse_ignore_list_multiple(self):
        """Test parsing multiple packages."""
        result = parse_ignore_list("package1,package2,package3")
        assert result == ["package1", "package2", "package3"]

    def test_parse_ignore_list_with_spaces(self):
        """Test parsing packages with spaces."""
        result = parse_ignore_list("package1, package2 , package3")
        assert result == ["package1", "package2", "package3"]

    def test_parse_ignore_list_empty_string(self):
        """Test parsing empty string returns empty list."""
        result = parse_ignore_list("")
        assert result == []

    def test_parse_ignore_list_trailing_comma(self):
        """Test parsing with trailing comma."""
        result = parse_ignore_list("package1,package2,")
        assert result == ["package1", "package2"]


class TestLoadConfiguration:
    """Test configuration loading functionality."""

    @patch("covert.cli.load_config")
    def test_load_configuration_success(self, mock_load_config, sample_config):
        """Test successful configuration loading."""
        mock_load_config.return_value = create_test_config()

        config = load_configuration(str(sample_config))
        assert config is not None
        mock_load_config.assert_called_once_with(str(sample_config))

    @patch("covert.cli.load_config")
    def test_load_configuration_none(self, mock_load_config):
        """Test loading with None path returns None."""
        config = load_configuration(None)
        assert config is None
        mock_load_config.assert_not_called()

    @patch("covert.cli.load_config")
    @patch("covert.cli.logger")
    def test_load_configuration_error(self, mock_logger, mock_load_config):
        """Test configuration loading error handling."""
        mock_load_config.side_effect = ConfigError("Invalid config")

        with pytest.raises(ConfigError):
            load_configuration("nonexistent.yaml")

        mock_logger.error.assert_called()


class TestMain:
    """Test main CLI entry point."""

    @patch("covert.cli.setup_cli_logging")
    @patch("covert.cli.run_update_session")
    @patch("covert.cli.load_configuration")
    def test_main_version(self, mock_load_config, mock_run_session, mock_setup_logging):
        """Test --version flag."""
        exit_code = main(["--version"])
        assert exit_code == 0
        mock_load_config.assert_not_called()
        mock_run_session.assert_not_called()
        mock_setup_logging.assert_not_called()

    @patch("covert.cli.setup_cli_logging")
    @patch("covert.cli.run_update_session")
    @patch("covert.cli.load_configuration")
    def test_main_success(self, mock_load_config, mock_run_session, mock_setup_logging):
        """Test successful execution."""
        mock_config = MagicMock()
        mock_config.security.require_virtualenv = False  # Mock the security attribute
        mock_load_config.return_value = mock_config

        mock_session = MagicMock()
        mock_session.success = True
        mock_run_session.return_value = mock_session

        exit_code = main([])
        assert exit_code == 0
        mock_load_config.assert_called_once()
        mock_setup_logging.assert_called_once()
        mock_run_session.assert_called_once()

    @patch("covert.cli.setup_cli_logging")
    @patch("covert.cli.run_update_session")
    @patch("covert.cli.load_configuration")
    def test_main_with_config(
        self,
        mock_load_config,
        mock_run_session,
        mock_setup_logging,
        temp_dir,
    ):
        """Test execution with config file."""
        config_path = temp_dir / "covert.yaml"
        config_path.write_text("project:\n  name: Test\n  python_version: '3.11'\n")

        mock_config = create_test_config()
        mock_load_config.return_value = mock_config

        mock_session = MagicMock()
        mock_session.success = True
        mock_run_session.return_value = mock_session

        exit_code = main(["--config", str(config_path)])
        assert exit_code == 0
        mock_load_config.assert_called_once_with(str(config_path))

    @patch("covert.cli.setup_cli_logging")
    @patch("covert.cli.run_update_session")
    @patch("covert.cli.load_configuration")
    def test_main_with_dry_run(
        self,
        mock_load_config,
        mock_run_session,
        mock_setup_logging,
    ):
        """Test dry-run mode."""
        mock_config = create_test_config()
        mock_load_config.return_value = mock_config

        mock_session = MagicMock()
        mock_session.success = True
        mock_run_session.return_value = mock_session

        exit_code = main(["--dry-run"])
        assert exit_code == 0

        # Verify dry_run was passed to run_update_session
        call_kwargs = mock_run_session.call_args[1]
        assert call_kwargs["dry_run"] is True

    @patch("covert.cli.setup_cli_logging")
    @patch("covert.cli.run_update_session")
    @patch("covert.cli.load_configuration")
    def test_main_with_ignore(
        self,
        mock_load_config,
        mock_run_session,
        mock_setup_logging,
    ):
        """Test with ignore list."""
        mock_config = create_test_config()
        mock_load_config.return_value = mock_config

        mock_session = MagicMock()
        mock_session.success = True
        mock_run_session.return_value = mock_session

        exit_code = main(["--ignore", "package1,package2"])
        assert exit_code == 0

        # Verify ignore_packages was passed to run_update_session
        call_kwargs = mock_run_session.call_args[1]
        assert call_kwargs["ignore_packages"] == ["package1", "package2"]

    @patch("covert.cli.setup_cli_logging")
    @patch("covert.cli.run_update_session")
    @patch("covert.cli.load_configuration")
    def test_main_with_no_backup(
        self,
        mock_load_config,
        mock_run_session,
        mock_setup_logging,
    ):
        """Test with --no-backup flag."""
        mock_config = create_test_config()
        mock_load_config.return_value = mock_config

        mock_session = MagicMock()
        mock_session.success = True
        mock_run_session.return_value = mock_session

        exit_code = main(["--no-backup"])
        assert exit_code == 0

        # Verify no_backup was passed to run_update_session
        call_kwargs = mock_run_session.call_args[1]
        assert call_kwargs["no_backup"] is True

    @patch("covert.cli.setup_cli_logging")
    @patch("covert.cli.run_update_session")
    @patch("covert.cli.load_configuration")
    def test_main_with_no_tests(
        self,
        mock_load_config,
        mock_run_session,
        mock_setup_logging,
    ):
        """Test with --no-tests flag."""
        mock_config = create_test_config()
        mock_load_config.return_value = mock_config

        mock_session = MagicMock()
        mock_session.success = True
        mock_run_session.return_value = mock_session

        exit_code = main(["--no-tests"])
        assert exit_code == 0

        # Verify no_tests was passed to run_update_session
        call_kwargs = mock_run_session.call_args[1]
        assert call_kwargs["no_tests"] is True

    @patch("covert.cli.setup_cli_logging")
    @patch("covert.cli.run_update_session")
    @patch("covert.cli.load_configuration")
    def test_main_session_failure(
        self,
        mock_load_config,
        mock_run_session,
        mock_setup_logging,
    ):
        """Test session with failures returns non-zero exit code."""
        mock_config = create_test_config()
        mock_load_config.return_value = mock_config

        mock_session = MagicMock()
        mock_session.success = False
        mock_run_session.return_value = mock_session

        exit_code = main([])
        assert exit_code == 1

    @patch("covert.cli.setup_cli_logging")
    @patch("covert.cli.run_update_session")
    @patch("covert.cli.load_configuration")
    def test_main_keyboard_interrupt(
        self,
        mock_load_config,
        mock_run_session,
        mock_setup_logging,
    ):
        """Test keyboard interrupt handling."""
        mock_config = create_test_config()
        mock_load_config.return_value = mock_config

        mock_run_session.side_effect = KeyboardInterrupt()

        exit_code = main([])
        assert exit_code == 130

    @patch("covert.cli.setup_cli_logging")
    @patch("covert.cli.run_update_session")
    @patch("covert.cli.load_configuration")
    def test_main_covert_error(
        self,
        mock_load_config,
        mock_run_session,
        mock_setup_logging,
    ):
        """Test CovertError handling."""
        mock_config = create_test_config()
        mock_load_config.return_value = mock_config

        from covert.exceptions import UpdateError

        mock_run_session.side_effect = UpdateError("Update failed")

        exit_code = main([])
        assert exit_code == 1

    @patch("covert.cli.setup_cli_logging")
    @patch("covert.cli.run_update_session")
    @patch("covert.cli.load_configuration")
    def test_main_unexpected_error(
        self,
        mock_load_config,
        mock_run_session,
        mock_setup_logging,
    ):
        """Test unexpected error handling."""
        mock_config = create_test_config()
        mock_load_config.return_value = mock_config

        mock_run_session.side_effect = RuntimeError("Unexpected error")

        exit_code = main([])
        assert exit_code == 1

    @patch("covert.cli.setup_cli_logging")
    @patch("covert.cli.run_update_session")
    @patch("covert.cli.load_configuration")
    def test_main_config_error(
        self,
        mock_load_config,
        mock_run_session,
        mock_setup_logging,
    ):
        """Test ConfigError handling."""
        mock_load_config.side_effect = ConfigError("Invalid config")

        exit_code = main(["--config", "invalid.yaml"])
        assert exit_code == 1
        mock_run_session.assert_not_called()

    @patch("covert.cli.setup_cli_logging")
    @patch("covert.cli.run_update_session")
    @patch("covert.cli.load_configuration")
    def test_main_verbose_levels(
        self,
        mock_load_config,
        mock_run_session,
        mock_setup_logging,
    ):
        """Test different verbosity levels."""
        mock_config = create_test_config()
        mock_load_config.return_value = mock_config

        mock_session = MagicMock()
        mock_session.success = True
        mock_run_session.return_value = mock_session

        # Test -v
        exit_code = main(["-v"])
        assert exit_code == 0
        # Second argument is verbose_level (positional)
        call_args = mock_setup_logging.call_args[0]
        assert call_args[1] == 1

        # Test -vv
        exit_code = main(["-vv"])
        assert exit_code == 0
        call_args = mock_setup_logging.call_args[0]
        assert call_args[1] == 2
