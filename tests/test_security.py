"""Security-focused tests for Covert.

This module contains tests that verify security features including:
- Command injection prevention
- Input validation
- Virtual environment enforcement
- Privilege escalation detection
"""

import pytest

from covert.exceptions import SecurityError, ValidationError
from covert.utils import (
    check_elevated_privileges,
    is_in_virtualenv,
    sanitize_package_name,
    validate_package_name,
    validate_path,
    validate_version,
)


class TestCommandInjectionPrevention:
    """Test that command injection attempts are prevented."""

    def test_valid_package_names(self):
        """Test that valid package names are accepted."""
        valid_names = [
            "requests",
            "django",
            "flask",
            "numpy",
            "pandas",
            "my-package",
            "my_package",
            "MyPackage",
        ]
        for name in valid_names:
            assert validate_package_name(name), f"{name} should be valid"

    def test_invalid_package_names_with_injection(self):
        """Test that package names with injection attempts are rejected."""
        invalid_names = [
            "requests; rm -rf /",
            "django && evil-command",
            "flask|cat /etc/passwd",
            "numpy`whoami`",
            "pandas$(evil)",
            "requests; evil",
            "django\nmalicious",
            "requests\r\nmalicious",
        ]
        for name in invalid_names:
            assert not validate_package_name(name), f"{name} should be invalid"

    def test_sanitize_package_name_rejects_injection(self):
        """Test that sanitize_package_name raises error for injection attempts."""
        malicious_names = [
            "requests; rm -rf /",
            "django && evil-command",
            "flask|cat /etc/passwd",
        ]
        for name in malicious_names:
            with pytest.raises(ValidationError):
                sanitize_package_name(name)


class TestInputValidation:
    """Test input validation functions."""

    def test_validate_version_valid(self):
        """Test that valid versions are accepted."""
        valid_versions = [
            "1.0.0",
            "2.31.0",
            "3.11.1",
            "1.0",
            "2",
            "1.0.0a1",
            "2.0.0b2",
            "3.0.0rc1",
            "1.0.0.dev1",
            "1.0.0.post1",
        ]
        for version in valid_versions:
            assert validate_version(version), f"{version} should be valid"

    def test_validate_version_invalid(self):
        """Test that invalid versions are rejected."""
        invalid_versions = [
            "",
            "1.0.",
            ".1.0",
            "1..0",
            "1.0.0.0.0",
            "version",
            "1.0.0; rm -rf /",
            "1.0.0 && evil",
            "1.0.0\nmalicious",
        ]
        for version in invalid_versions:
            assert not validate_version(version), f"{version} should be invalid"

    def test_validate_path_valid(self):
        """Test that valid paths are accepted."""
        valid_paths = [
            "./backups",
            "backups",
            "backups/backup.txt",
            "relative/path",
            "safe_dir",
        ]
        for path in valid_paths:
            assert validate_path(path), f"{path} should be valid"

    def test_validate_path_path_traversal(self):
        """Test that path traversal attempts are rejected."""
        invalid_paths = [
            "../etc/passwd",
            "..\\windows\\system32",
            "./../etc",
            "safe/../../../etc",
            "path/..",
            "..",
        ]
        for path in invalid_paths:
            assert not validate_path(path), f"{path} should be invalid"

    def test_validate_path_null_bytes(self):
        """Test that paths with null bytes are rejected."""
        invalid_paths = [
            "path\x00with\x00null",
            "\x00",
            "safe\x00path",
        ]
        for path in invalid_paths:
            assert not validate_path(path), f"{path} should be invalid"

    def test_validate_path_empty(self):
        """Test that empty paths are rejected."""
        assert not validate_path("")
        assert not validate_path(None)

    def test_sanitize_package_name_valid(self):
        """Test that valid package names are sanitized correctly."""
        # canonicalize_name normalizes underscores to hyphens per PEP 503
        assert sanitize_package_name("Requests") == "requests"
        assert sanitize_package_name("MyPackage") == "mypackage"
        assert sanitize_package_name("valid-name") == "valid-name"
        # underscores are converted to hyphens per PEP 503
        assert sanitize_package_name("valid_name") == "valid-name"

    def test_sanitize_package_name_invalid_raises(self):
        """Test that invalid package names raise ValidationError."""
        invalid_names = [
            "",
            "1invalid",
            "invalid!",
            "-invalid",
            "invalid-",
            "_invalid",
            "invalid_",
        ]
        for name in invalid_names:
            with pytest.raises(ValidationError):
                sanitize_package_name(name)


class TestVirtualEnvironmentDetection:
    """Test virtual environment detection."""

    def test_is_in_virtualenv_returns_bool(self):
        """Test that is_in_virtualenv returns a boolean."""
        result = is_in_virtualenv()
        assert isinstance(result, bool)

    def test_is_in_virtualenv_consistent(self):
        """Test that is_in_virtualenv returns consistent results."""
        result1 = is_in_virtualenv()
        result2 = is_in_virtualenv()
        assert result1 == result2


class TestPrivilegeEscalationDetection:
    """Test privilege escalation detection."""

    def test_check_elevated_privileges_returns_bool(self):
        """Test that check_elevated_privileges returns a boolean."""
        result = check_elevated_privileges()
        assert isinstance(result, bool)

    def test_check_elevated_privileges_consistent(self):
        """Test that check_elevated_privileges returns consistent results."""
        result1 = check_elevated_privileges()
        result2 = check_elevated_privileges()
        assert result1 == result2


class TestSecurityError:
    """Test SecurityError exception."""

    def test_security_error_message(self):
        """Test that SecurityError stores message correctly."""
        msg = "Test security error"
        error = SecurityError(msg)
        assert error.message == msg
        assert str(error) == msg

    def test_security_error_inherits_from_covert_error(self):
        """Test that SecurityError inherits from CovertError."""
        from covert.exceptions import CovertError

        error = SecurityError("Test")
        assert isinstance(error, CovertError)


class TestPackageValidationEdgeCases:
    """Test edge cases in package name validation."""

    def test_package_name_single_char(self):
        """Test that single character package names are valid."""
        assert validate_package_name("a")
        assert validate_package_name("Z")

    def test_package_name_long(self):
        """Test that long package names are valid."""
        long_name = "a" * 200
        assert validate_package_name(long_name)

    def test_package_name_with_numbers(self):
        """Test that package names with numbers are valid."""
        assert validate_package_name("package123")
        assert validate_package_name("pkg2go")
        assert validate_package_name("django3")

    def test_package_name_case_preserved_in_sanitize(self):
        """Test that sanitize_package_name lowercases the name."""
        assert sanitize_package_name("Django") == "django"
        assert sanitize_package_name("FLASK") == "flask"
        assert sanitize_package_name("Requests") == "requests"


class TestVersionValidationEdgeCases:
    """Test edge cases in version validation."""

    def test_version_single_number(self):
        """Test that single number versions are valid."""
        assert validate_version("1")
        assert validate_version("2")
        assert validate_version("10")

    def test_version_many_components(self):
        """Test that versions with many components are valid."""
        assert validate_version("1.2.3.4.5")
        assert validate_version("1.2.3.4.5.6.7.8.9")

    def test_version_with_prerelease(self):
        """Test that versions with prerelease tags are valid."""
        assert validate_version("1.0.0a1")
        assert validate_version("1.0.0.alpha")
        assert validate_version("1.0.0b2")
        assert validate_version("1.0.0.beta")
        assert validate_version("1.0.0rc1")
        assert validate_version("1.0.0.rc")

    def test_version_with_dev(self):
        """Test that dev versions are valid."""
        assert validate_version("1.0.0.dev1")
        assert validate_version("1.0.0.dev")
        assert validate_version("1.0.0.dev123")

    def test_version_with_post(self):
        """Test that post versions are valid."""
        assert validate_version("1.0.0.post1")
        assert validate_version("1.0.0.post")
        assert validate_version("1.0.0.post123")


class TestPathValidationEdgeCases:
    """Test edge cases in path validation."""

    def test_path_with_spaces(self):
        """Test that paths with spaces are valid."""
        assert validate_path("my path")
        assert validate_path("path with spaces")

    def test_path_with_dots(self):
        """Test that paths with dots are valid."""
        assert validate_path("./path")
        assert validate_path("path/to/file.txt")
        assert validate_path(".hidden")

    def test_path_with_underscores(self):
        """Test that paths with underscores are valid."""
        assert validate_path("my_path")
        assert validate_path("path_to_file")

    def test_path_with_special_chars(self):
        """Test that paths with some special characters are valid."""
        assert validate_path("path-with-dashes")
        assert validate_path("path.with.dots")
        assert validate_path("path_with_underscores")

    def test_path_absolute_rejected_by_default(self):
        """Test that absolute paths are rejected."""
        assert not validate_path("/etc/passwd")
        assert not validate_path("C:\\Windows\\System32")
        assert not validate_path("/usr/bin")


class TestBackupPathValidation:
    """Test backup path validation for security."""

    def test_validate_backup_path_rejects_etc(self):
        """Test that /etc is rejected as backup path."""
        from covert.utils import validate_backup_path, ValidationError

        with pytest.raises(ValidationError):
            validate_backup_path("/etc/passwd")

    def test_validate_backup_path_rejects_root(self):
        """Test that / (root) is rejected as backup path."""
        from covert.utils import validate_backup_path, ValidationError

        with pytest.raises(ValidationError):
            validate_backup_path("/")

    def test_validate_backup_path_accepts_relative(self):
        """Test that relative paths like ./backups are accepted."""
        from covert.utils import validate_backup_path

        # Should not raise
        result = validate_backup_path("./backups")
        assert result is not None

    def test_validate_backup_path_accepts_subdirectory(self):
        """Test that subdirectories within project are accepted."""
        from covert.utils import validate_backup_path

        result = validate_backup_path("backups/mybackups")
        assert result is not None


class TestSecurityAuditInfo:
    """Test security audit information gathering."""

    def test_get_security_audit_info_returns_dict(self):
        """Test that security audit info returns a dictionary."""
        from covert.utils import get_security_audit_info

        info = get_security_audit_info()
        assert isinstance(info, dict)
        assert "running_in_venv" in info
        assert "elevated_privileges" in info
        assert "platform" in info

    def test_get_security_audit_info_values(self):
        """Test that security audit info contains expected values."""
        from covert.utils import get_security_audit_info

        info = get_security_audit_info()
        assert isinstance(info["running_in_venv"], bool)
        assert isinstance(info["elevated_privileges"], bool)
        assert isinstance(info["platform"], str)


class TestCommandSafetyValidation:
    """Test command safety validation."""

    def test_is_safe_command_valid(self):
        """Test that valid commands are accepted."""
        from covert.utils import is_safe_command

        assert is_safe_command(["pip", "list"])
        assert is_safe_command(["python", "-m", "pytest"])
        assert is_safe_command(["git", "status"])

    def test_is_safe_command_rejects_dangerous(self):
        """Test that commands with dangerous patterns are rejected."""
        from covert.utils import is_safe_command

        assert not is_safe_command(["pip", "list && rm -rf /"])
        assert not is_safe_command(["pip", "list | cat /etc/passwd"])
        assert not is_safe_command(["python", "-c", "import os; os.system('evil')"])
        assert not is_safe_command(["pip", "install --help > /etc/passwd"])

    def test_is_safe_command_empty(self):
        """Test that empty commands are rejected."""
        from covert.utils import is_safe_command

        assert not is_safe_command([])
        assert not is_safe_command(None)
