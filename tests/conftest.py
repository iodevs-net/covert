"""Pytest configuration and fixtures for Covert tests."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from covert.config import Config, ProjectConfig


@pytest.fixture
def temp_dir():
    """Temporary directory for tests.

    Yields:
        Path: Path to temporary directory.
    """
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config(temp_dir):
    """Sample configuration file.

    Creates a sample YAML configuration file in the temporary directory.

    Args:
        temp_dir: Temporary directory fixture.

    Yields:
        Path: Path to sample configuration file.
    """
    config_path = temp_dir / "covert.yaml"
    config_path.write_text("""project:
  name: "Test Project"
  python_version: "3.11"
testing:
  enabled: true
  command: "pytest"
  args:
    - "-v"
    - "--tb=short"
  exclude_paths:
    - "tests/e2e"
    - "soporte/tests/e2e"
  timeout_seconds: 300
updates:
  strategy: "sequential"
  max_parallel: 3
  version_policy: "safe"
  ignore_packages:
    - "package-to-ignore"
    - "another-package"
  allow_only_packages: null
backup:
  enabled: true
  location: "./backups"
  retention_days: 30
  format: "txt"
logging:
  level: "INFO"
  format: "detailed"
  file: "covert.log"
  console: true
security:
  require_virtualenv: true
  verify_signatures: false
  check_vulnerabilities: true
""")
    return config_path


@pytest.fixture
def sample_toml_config(temp_dir):
    """Sample TOML configuration file.

    Creates a sample TOML configuration file in the temporary directory.

    Args:
        temp_dir: Temporary directory fixture.

    Yields:
        Path: Path to sample TOML configuration file.
    """
    config_path = temp_dir / "covert.toml"
    config_path.write_text("""[project]
name = "Test Project"
python_version = "3.11"

[testing]
enabled = true
command = "pytest"
args = ["-v", "--tb=short"]
exclude_paths = ["tests/e2e", "soporte/tests/e2e"]
timeout_seconds = 300

[updates]
strategy = "sequential"
max_parallel = 3
version_policy = "safe"
ignore_packages = ["package-to-ignore", "another-package"]
allow_only_packages = []

[backup]
enabled = true
location = "./backups"
retention_days = 30
format = "txt"

[logging]
level = "INFO"
format = "detailed"
file = "covert.log"
console = true

[security]
require_virtualenv = true
verify_signatures = false
check_vulnerabilities = true
""")
    return config_path


@pytest.fixture
def mock_config():
    """Mock configuration object.

    Returns:
        Config: A sample configuration object for testing.
    """
    return Config(project=ProjectConfig(name="Test Project", python_version="3.11"))


@pytest.fixture
def mock_pip_output():
    """Mock pip list --outdated output.

    Returns:
        list: Mock pip output as a list of dictionaries.
    """
    return [
        {
            "name": "requests",
            "version": "2.25.0",
            "latest_version": "2.31.0",
            "latest_filetype": "wheel",
            "package_type": "regular",
        },
        {
            "name": "django",
            "version": "4.2.0",
            "latest_version": "5.0.0",
            "latest_filetype": "wheel",
            "package_type": "regular",
        },
    ]


@pytest.fixture
def mock_test_output():
    """Mock test execution output.

    Returns:
        str: Mock test output.
    """
    return """============================= test session starts ==============================
collected 5 items

test_example.py .....                                                   [100%]

============================== 5 passed in 0.5s ===============================
"""


@pytest.fixture
def mock_backup_file(temp_dir):
    """Mock backup file.

    Creates a sample backup file in the temporary directory.

    Args:
        temp_dir: Temporary directory fixture.

    Yields:
        Path: Path to sample backup file.
    """
    backup_path = temp_dir / "backups" / "backup.txt"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text("""requests==2.25.0
django==4.2.0
pyyaml==6.0
""")
    return backup_path
