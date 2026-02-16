"""Unit tests for pip_interface module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from covert.exceptions import PipError, ValidationError
from covert.pip_interface import (
    check_package_exists,
    freeze_requirements,
    get_outdated_packages,
    get_package_version,
    install_package,
    list_installed_packages,
    run_secure_command,
    uninstall_package,
)


class TestRunSecureCommand:
    """Tests for run_secure_command function."""

    @patch("covert.pip_interface.subprocess.run")
    def test_command_as_string(self, mock_run):
        """Test executing command as string."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = run_secure_command("echo hello")

        mock_run.assert_called_once()
        assert result.returncode == 0

    @patch("covert.pip_interface.subprocess.run")
    def test_command_as_list(self, mock_run):
        """Test executing command as list."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = run_secure_command(["echo", "hello"])

        mock_run.assert_called_once()
        assert result.returncode == 0

    @patch("covert.pip_interface.subprocess.run")
    def test_shell_false(self, mock_run):
        """Test that shell=False is always used."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        run_secure_command("echo hello")

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["shell"] is False

    @patch("covert.pip_interface.subprocess.run")
    def test_timeout_expired(self, mock_run):
        """Test handling of timeout."""
        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired("cmd", 10)

        with pytest.raises(PipError):
            run_secure_command("sleep 100", timeout=10)

    @patch("covert.pip_interface.subprocess.run")
    def test_file_not_found(self, mock_run):
        """Test handling of command not found."""
        mock_run.side_effect = FileNotFoundError("cmd not found")

        with pytest.raises(PipError):
            run_secure_command("nonexistent_command")

    @patch("covert.pip_interface.subprocess.run")
    def test_check_true_raises_on_error(self, mock_run):
        """Test that check=True raises error on non-zero exit."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error"
        mock_run.return_value = mock_result

        with pytest.raises(PipError):
            run_secure_command("false", check=True)


class TestGetOutdatedPackages:
    """Tests for get_outdated_packages function."""

    @patch("covert.pip_interface.run_secure_command")
    def test_successful_list(self, mock_run):
        """Test successful listing of outdated packages."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            [
                {"name": "requests", "version": "2.25.0", "latest_version": "2.31.0"},
                {"name": "django", "version": "4.2.0", "latest_version": "5.0.0"},
            ]
        )
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        packages = get_outdated_packages()

        assert len(packages) == 2
        assert packages[0]["name"] == "requests"
        assert packages[1]["name"] == "django"

    @patch("covert.pip_interface.run_secure_command")
    def test_no_outdated_packages(self, mock_run):
        """Test handling when no outdated packages."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"
        mock_result.stderr = "WARNING: No packages found"
        mock_run.return_value = mock_result

        packages = get_outdated_packages()

        assert packages == []

    @patch("covert.pip_interface.run_secure_command")
    def test_invalid_json(self, mock_run):
        """Test handling of invalid JSON output."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "invalid json"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        with pytest.raises(PipError):
            get_outdated_packages()

    @patch("covert.pip_interface.run_secure_command")
    def test_command_failure(self, mock_run):
        """Test handling of pip command failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "pip error"
        mock_run.return_value = mock_result

        with pytest.raises(PipError):
            get_outdated_packages()


class TestInstallPackage:
    """Tests for install_package function."""

    @patch("covert.pip_interface.run_secure_command")
    @patch("covert.pip_interface.get_package_version")
    def test_install_with_version(self, mock_get_version, mock_run):
        """Test installing a specific version."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully installed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        mock_get_version.return_value = "2.31.0"

        result = install_package("requests", version="2.31.0")

        assert result["name"] == "requests"
        assert result["version"] == "2.31.0"

    @patch("covert.pip_interface.run_secure_command")
    @patch("covert.pip_interface.get_package_version")
    def test_install_without_version(self, mock_get_version, mock_run):
        """Test installing without specifying version."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully installed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        mock_get_version.return_value = "2.31.0"

        result = install_package("requests")

        assert result["name"] == "requests"
        assert result["version"] == "2.31.0"

    @patch("covert.pip_interface.run_secure_command")
    def test_install_with_upgrade(self, mock_run):
        """Test installing with upgrade flag."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully installed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        install_package("requests", upgrade=True)

        call_args = mock_run.call_args[0][0]
        assert "--upgrade" in call_args

    @patch("covert.pip_interface.run_secure_command")
    def test_install_with_pre_release(self, mock_run):
        """Test installing with pre-release flag."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully installed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        install_package("requests", pre_release=True)

        call_args = mock_run.call_args[0][0]
        assert "--pre" in call_args

    @patch("covert.pip_interface.run_secure_command")
    def test_install_failure(self, mock_run):
        """Test handling of installation failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Installation failed"
        mock_run.return_value = mock_result

        with pytest.raises(PipError):
            install_package("nonexistent-package")

    def test_invalid_version_raises_error(self):
        """Test that invalid version raises ValidationError."""
        with pytest.raises(ValidationError):
            install_package("requests", version="invalid.version")


class TestUninstallPackage:
    """Tests for uninstall_package function."""

    @patch("covert.pip_interface.run_secure_command")
    def test_successful_uninstall(self, mock_run):
        """Test successful uninstallation."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully uninstalled"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        uninstall_package("requests")

        call_args = mock_run.call_args[0][0]
        assert "uninstall" in call_args
        assert "-y" in call_args

    @patch("covert.pip_interface.run_secure_command")
    def test_uninstall_failure(self, mock_run):
        """Test handling of uninstallation failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Uninstallation failed"
        mock_run.return_value = mock_result

        with pytest.raises(PipError):
            uninstall_package("requests")


class TestFreezeRequirements:
    """Tests for freeze_requirements function."""

    @patch("covert.pip_interface.run_secure_command")
    def test_freeze_txt_format(self, mock_run):
        """Test freezing requirements in txt format."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "requests==2.31.0\ndjango==5.0.0\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = freeze_requirements(format_type="txt")

        assert result == "requests==2.31.0\ndjango==5.0.0\n"

    @patch("covert.pip_interface.run_secure_command")
    def test_freeze_json_format(self, mock_run):
        """Test freezing requirements in JSON format."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "requests==2.31.0\ndjango==5.0.0\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = freeze_requirements(format_type="json")

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "requests"
        assert result[0]["version"] == "2.31.0"

    @patch("covert.pip_interface.run_secure_command")
    def test_invalid_format(self, mock_run):
        """Test that invalid format raises ValidationError."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        with pytest.raises(ValidationError):
            freeze_requirements(format_type="invalid")

    @patch("covert.pip_interface.run_secure_command")
    @patch("pathlib.Path.write_text")
    def test_save_to_file(self, mock_write, mock_run):
        """Test saving requirements to file."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "requests==2.31.0\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        freeze_requirements(output_path="requirements.txt", format_type="txt")

        mock_write.assert_called_once()


class TestGetPackageVersion:
    """Tests for get_package_version function."""

    @patch("covert.pip_interface.run_secure_command")
    def test_get_version(self, mock_run):
        """Test getting package version."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Name: requests\nVersion: 2.31.0\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        version = get_package_version("requests")

        assert version == "2.31.0"

    @patch("covert.pip_interface.run_secure_command")
    def test_package_not_found(self, mock_run):
        """Test handling of package not found."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        version = get_package_version("nonexistent")

        assert version is None


class TestListInstalledPackages:
    """Tests for list_installed_packages function."""

    @patch("covert.pip_interface.run_secure_command")
    def test_list_packages(self, mock_run):
        """Test listing installed packages."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            [
                {"name": "requests", "version": "2.31.0"},
                {"name": "django", "version": "5.0.0"},
            ]
        )
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        packages = list_installed_packages()

        assert len(packages) == 2
        assert packages[0]["name"] == "requests"

    @patch("covert.pip_interface.run_secure_command")
    def test_command_failure(self, mock_run):
        """Test handling of command failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error"
        mock_run.return_value = mock_result

        with pytest.raises(PipError):
            list_installed_packages()


class TestCheckPackageExists:
    """Tests for check_package_exists function."""

    @patch("covert.pip_interface.run_secure_command")
    def test_package_exists(self, mock_run):
        """Test that existing package returns True."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = check_package_exists("requests")

        assert result is True

    @patch("covert.pip_interface.run_secure_command")
    def test_package_not_exists(self, mock_run):
        """Test that non-existing package returns False."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = check_package_exists("nonexistent-package-123")

        assert result is False
