"""Unit tests for the utils module."""

import pytest

from covert.exceptions import ValidationError
from covert.utils import (
    check_elevated_privileges,
    compare_versions,
    format_version_range,
    get_python_version,
    get_venv_path,
    is_breaking_change,
    is_compatible_python_version,
    is_in_virtualenv,
    parse_version,
    sanitize_package_name,
    validate_package_name,
    validate_version,
)


class TestValidatePackageName:
    """Tests for validate_package_name function."""

    def test_valid_package_names(self):
        """Test that valid package names pass validation."""
        valid_names = [
            "requests",
            "Django",
            "pytest",
            "my-package",
            "my_package",
            "my.package",
            "a",
            "A1",
            "package-123",
            "Package_123",
        ]
        for name in valid_names:
            assert validate_package_name(name) is True

    def test_invalid_package_names(self):
        """Test that invalid package names fail validation."""
        invalid_names = [
            "-package",
            "package-",
            "_package",
            "package_",
            ".package",
            "package.",
            "",
            " package",
            "package ",
            "package name",
            "package@name",
        ]
        for name in invalid_names:
            assert validate_package_name(name) is False


class TestValidateVersion:
    """Tests for validate_version function."""

    def test_valid_versions(self):
        """Test that valid versions pass validation."""
        valid_versions = [
            "1.0.0",
            "1.0",
            "1",
            "1.2.3.4",
            "1.0.0a1",
            "1.0.0.dev1",
            "1.0.0rc1",
            "1.0.0.post1",
            "2.0.0+local",
        ]
        for version in valid_versions:
            assert validate_version(version) is True

    def test_invalid_versions(self):
        """Test that invalid versions fail validation."""
        invalid_versions = [
            "",
            "v1.0.0",
            "1.0.0-",
            "1.0.0-rc",
            "1..0",
            ".1.0",
            "1.0.",
        ]
        for version in invalid_versions:
            assert validate_version(version) is False


class TestSanitizePackageName:
    """Tests for sanitize_package_name function."""

    def test_sanitization(self):
        """Test that package names are sanitized correctly using canonicalize_name."""
        # canonicalize_name normalizes according to PEP 503
        assert sanitize_package_name("MyPackage") == "mypackage"
        assert sanitize_package_name("MY-PACKAGE") == "my-package"
        # underscores are converted to hyphens per PEP 503
        assert sanitize_package_name("my_package") == "my-package"

    def test_invalid_name_raises_error(self):
        """Test that invalid package names raise ValidationError."""
        with pytest.raises(ValidationError):
            sanitize_package_name("-invalid")


class TestIsInVirtualenv:
    """Tests for is_in_virtualenv function."""

    def test_returns_bool(self):
        """Test that function returns a boolean."""
        result = is_in_virtualenv()
        assert isinstance(result, bool)


class TestGetVenvPath:
    """Tests for get_venv_path function."""

    def test_returns_path_or_none(self):
        """Test that function returns Path or None."""
        result = get_venv_path()
        assert result is None or hasattr(result, "exists")


class TestCheckElevatedPrivileges:
    """Tests for check_elevated_privileges function."""

    def test_returns_bool(self):
        """Test that function returns a boolean."""
        result = check_elevated_privileges()
        assert isinstance(result, bool)


class TestParseVersion:
    """Tests for parse_version function."""

    def test_parse_valid_version(self):
        """Test parsing valid versions."""
        v = parse_version("1.2.3")
        assert str(v) == "1.2.3"

    def test_parse_invalid_version_raises_error(self):
        """Test that invalid versions raise ValidationError."""
        with pytest.raises(ValidationError):
            parse_version("invalid")


class TestIsBreakingChange:
    """Tests for is_breaking_change function."""

    def test_no_change(self):
        """Test that non-updates are not breaking."""
        assert is_breaking_change("1.0.0", "1.0.0") is False
        assert is_breaking_change("1.0.0", "0.9.0") is False

    def test_patch_update_not_breaking(self):
        """Test that patch updates are not breaking."""
        assert is_breaking_change("1.0.0", "1.0.1", "patch") is False
        assert is_breaking_change("1.0.0", "1.0.1", "minor") is False
        assert is_breaking_change("1.0.0", "1.0.1", "safe") is False

    def test_minor_update_not_breaking_for_safe_policy(self):
        """Test that minor updates are not breaking for safe policy."""
        assert is_breaking_change("1.0.0", "1.1.0", "safe") is False
        assert is_breaking_change("1.0.0", "1.1.0", "minor") is False

    def test_minor_update_breaking_for_patch_policy(self):
        """Test that minor updates are breaking for patch policy."""
        assert is_breaking_change("1.0.0", "1.1.0", "patch") is True

    def test_major_update_breaking_for_safe_policy(self):
        """Test that major updates are breaking for safe policy."""
        assert is_breaking_change("1.0.0", "2.0.0", "safe") is True
        assert is_breaking_change("1.0.0", "2.0.0", "minor") is True
        assert is_breaking_change("1.0.0", "2.0.0", "patch") is True

    def test_latest_policy_allows_any_update(self):
        """Test that latest policy allows any update."""
        assert is_breaking_change("1.0.0", "2.0.0", "latest") is False
        assert is_breaking_change("1.0.0", "1.1.0", "latest") is False
        assert is_breaking_change("1.0.0", "1.0.1", "latest") is False


class TestFormatVersionRange:
    """Tests for format_version_range function."""

    def test_no_range(self):
        """Test formatting with no range."""
        assert format_version_range() == ""

    def test_min_version_only(self):
        """Test formatting with minimum version only."""
        assert format_version_range("1.0.0") == ">=1.0.0"

    def test_max_version_only(self):
        """Test formatting with maximum version only."""
        assert format_version_range(max_version="2.0.0") == "<2.0.0"

    def test_both_versions(self):
        """Test formatting with both versions."""
        result = format_version_range("1.0.0", "2.0.0")
        assert ">=1.0.0" in result
        assert "<2.0.0" in result


class TestCompareVersions:
    """Tests for compare_versions function."""

    def test_less_than(self):
        """Test comparing less than versions."""
        assert compare_versions("1.0.0", "1.0.1") == -1
        assert compare_versions("1.0.0", "1.1.0") == -1
        assert compare_versions("1.0.0", "2.0.0") == -1

    def test_equal(self):
        """Test comparing equal versions."""
        assert compare_versions("1.0.0", "1.0.0") == 0

    def test_greater_than(self):
        """Test comparing greater than versions."""
        assert compare_versions("1.0.1", "1.0.0") == 1
        assert compare_versions("1.1.0", "1.0.0") == 1
        assert compare_versions("2.0.0", "1.0.0") == 1


class TestGetPythonVersion:
    """Tests for get_python_version function."""

    def test_returns_tuple(self):
        """Test that function returns a tuple."""
        version = get_python_version()
        assert isinstance(version, tuple)
        assert len(version) == 3
        assert all(isinstance(x, int) for x in version)


class TestIsCompatiblePythonVersion:
    """Tests for is_compatible_python_version function."""

    def test_greater_than_or_equal(self):
        """Test >= comparison."""
        current = get_python_version()
        assert is_compatible_python_version(f">={current[0]}.{current[1]}.{current[2]}") is True

    def test_greater_than(self):
        """Test > comparison."""
        current = get_python_version()
        assert is_compatible_python_version(f">{current[0]}.{current[1]}.{current[2]}") is False

    def test_equal(self):
        """Test == comparison."""
        current = get_python_version()
        assert is_compatible_python_version(f"=={current[0]}.{current[1]}.{current[2]}") is True
