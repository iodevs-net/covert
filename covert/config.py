"""Configuration management module for Covert.

This module provides dataclasses for configuration and functions to load,
save, and validate configuration from YAML and TOML files.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

import toml
import yaml

from covert.exceptions import ConfigError, ValidationError
from covert.utils import validate_package_name


@dataclass
class ProjectConfig:
    """Project-specific configuration.

    Attributes:
        name: Name of the project.
        python_version: Python version being used.
    """

    name: str
    python_version: str


@dataclass
class TestingConfig:
    """Testing configuration.

    Attributes:
        enabled: Whether testing is enabled.
        command: Command to run tests (e.g., "pytest").
        args: Arguments to pass to the test command.
        exclude_paths: Paths to exclude from testing.
        timeout_seconds: Maximum time to wait for tests to complete.
    """

    enabled: bool = True
    command: str = "pytest"
    args: List[str] = field(default_factory=lambda: ["-v", "--tb=short"])
    exclude_paths: List[str] = field(default_factory=list)
    timeout_seconds: int = 300


@dataclass
class UpdatesConfig:
    """Package update configuration.

    Attributes:
        strategy: Update strategy ("sequential" or "parallel").
        max_parallel: Maximum number of parallel updates.
        version_policy: Version update policy ("safe", "latest", "minor", "patch").
        ignore_packages: List of packages to ignore during updates.
        allow_only_packages: Optional list of packages to allow (exclusive mode).
    """

    strategy: str = "sequential"
    max_parallel: int = 3
    version_policy: str = "safe"
    ignore_packages: List[str] = field(default_factory=list)
    allow_only_packages: Optional[List[str]] = None


@dataclass
class BackupConfig:
    """Backup configuration.

    Attributes:
        enabled: Whether backup creation is enabled.
        location: Directory where backups are stored.
        retention_days: Number of days to retain backups.
        format: Backup format ("txt" or "json").
    """

    enabled: bool = True
    location: str = "./backups"
    retention_days: int = 30
    format: str = "txt"


@dataclass
class LoggingConfig:
    """Logging configuration.

    Attributes:
        level: Logging level ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
        format: Log format ("simple", "detailed", "json").
        file: Path to log file.
        console: Whether to output logs to console.
    """

    level: str = "INFO"
    format: str = "detailed"
    file: str = "covert.log"
    console: bool = True


@dataclass
class SecurityConfig:
    """Security configuration.

    Attributes:
        require_virtualenv: Whether to require a virtual environment.
        verify_signatures: Whether to verify package signatures.
        check_vulnerabilities: Whether to check for known vulnerabilities.
    """

    require_virtualenv: bool = True
    verify_signatures: bool = False
    check_vulnerabilities: bool = True


@dataclass
class NotificationConfig:
    """Notification configuration.

    Attributes:
        enabled: Whether notifications are enabled.
        slack_webhook: Slack webhook URL for notifications.
        slack_channel: Slack channel name.
        email_enabled: Whether email notifications are enabled.
        email_to: List of email recipients.
        webhook_url: Generic webhook URL for notifications.
    """

    enabled: bool = False
    slack_webhook: str = ""
    slack_channel: str = ""
    email_enabled: bool = False
    email_to: List[str] = field(default_factory=list)
    webhook_url: str = ""


@dataclass
class ReportConfig:
    """Report configuration.

    Attributes:
        enabled: Whether report generation is enabled.
        format: Report format (json, html, markdown).
        output_path: Path where report should be saved.
    """

    enabled: bool = False
    format: str = "json"
    output_path: str = ""


@dataclass
class InteractiveConfig:
    """Interactive mode configuration.

    Attributes:
        enabled: Whether interactive mode is enabled.
        confirm_each: Confirm before each package update.
    """

    enabled: bool = False
    confirm_each: bool = True


@dataclass
class ProgressConfig:
    """Progress bar configuration.

    Attributes:
        enabled: Whether progress bars are enabled.
    """

    enabled: bool = True


@dataclass
class Config:
    """Main configuration class.

    Attributes:
        project: Project configuration.
        testing: Testing configuration.
        updates: Updates configuration.
        backup: Backup configuration.
        logging: Logging configuration.
        security: Security configuration.
        notifications: Notification configuration.
        reports: Report configuration.
        interactive: Interactive mode configuration.
        progress: Progress bar configuration.
    """

    project: ProjectConfig
    testing: TestingConfig = field(default_factory=TestingConfig)
    updates: UpdatesConfig = field(default_factory=UpdatesConfig)
    backup: BackupConfig = field(default_factory=BackupConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    reports: ReportConfig = field(default_factory=ReportConfig)
    interactive: InteractiveConfig = field(default_factory=InteractiveConfig)
    progress: ProgressConfig = field(default_factory=ProgressConfig)


def load_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """Load configuration from a YAML or TOML file.

    Args:
        config_path: Path to configuration file. If None, searches for
            covert.yaml, covert.toml, or .covert.yml in current directory.

    Returns:
        Config: Loaded configuration object.

    Raises:
        ConfigError: If configuration file cannot be found or read.
        ValidationError: If configuration data is invalid.
    """
    if config_path is None:
        config_path = _find_config_file()
    else:
        config_path = Path(config_path)

    if not config_path or not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path) as f:
            if config_path.suffix in (".yaml", ".yml"):
                data = yaml.safe_load(f)
            elif config_path.suffix == ".toml":
                data = toml.load(f)
            else:
                raise ConfigError(f"Unsupported configuration file format: {config_path.suffix}")
    except (yaml.YAMLError, toml.TomlDecodeError) as e:
        raise ConfigError(f"Failed to parse configuration file: {e}") from e
    except OSError as e:
        raise ConfigError(f"Failed to read configuration file: {e}") from e

    if not data:
        raise ConfigError("Configuration file is empty")

    try:
        return _parse_config(data)
    except (KeyError, TypeError, ValueError) as e:
        raise ValidationError(f"Invalid configuration: {e}") from e


def _find_config_file() -> Optional[Path]:
    """Find configuration file in current directory.

    Searches for covert.yaml, covert.toml, or .covert.yml in order.

    Returns:
        Path to configuration file if found, None otherwise.
    """
    config_names = ["covert.yaml", "covert.toml", ".covert.yml"]
    for name in config_names:
        path = Path(name)
        if path.exists():
            return path
    return None


def _parse_config(data: dict) -> Config:
    """Parse configuration data dictionary into Config object.

    Args:
        data: Configuration data dictionary.

    Returns:
        Config: Parsed configuration object.

    Raises:
        KeyError: If required configuration keys are missing.
        TypeError: If configuration values have wrong type.
    """
    project_data = data.get("project", {})
    if not project_data.get("name"):
        raise ValidationError("Project name is required")
    if not project_data.get("python_version"):
        raise ValidationError("Python version is required")

    project = ProjectConfig(
        name=project_data["name"],
        python_version=project_data["python_version"],
    )

    testing_data = data.get("testing", {})
    testing = TestingConfig(
        enabled=testing_data.get("enabled", True),
        command=testing_data.get("command", "pytest"),
        args=testing_data.get("args", ["-v", "--tb=short"]),
        exclude_paths=testing_data.get("exclude_paths", []),
        timeout_seconds=testing_data.get("timeout_seconds", 300),
    )

    updates_data = data.get("updates", {})
    updates = UpdatesConfig(
        strategy=updates_data.get("strategy", "sequential"),
        max_parallel=updates_data.get("max_parallel", 3),
        version_policy=updates_data.get("version_policy", "safe"),
        ignore_packages=updates_data.get("ignore_packages", []),
        allow_only_packages=updates_data.get("allow_only_packages"),
    )

    backup_data = data.get("backup", {})
    backup = BackupConfig(
        enabled=backup_data.get("enabled", True),
        location=backup_data.get("location", "./backups"),
        retention_days=backup_data.get("retention_days", 30),
        format=backup_data.get("format", "txt"),
    )

    logging_data = data.get("logging", {})
    logging_config = LoggingConfig(
        level=logging_data.get("level", "INFO"),
        format=logging_data.get("format", "detailed"),
        file=logging_data.get("file", "covert.log"),
        console=logging_data.get("console", True),
    )

    security_data = data.get("security", {})
    security = SecurityConfig(
        require_virtualenv=security_data.get("require_virtualenv", True),
        verify_signatures=security_data.get("verify_signatures", False),
        check_vulnerabilities=security_data.get("check_vulnerabilities", True),
    )

    # Parse notification config
    notification_data = data.get("notifications", {})
    notifications = NotificationConfig(
        enabled=notification_data.get("enabled", False),
        slack_webhook=notification_data.get("slack_webhook", ""),
        slack_channel=notification_data.get("slack_channel", ""),
        email_enabled=notification_data.get("email_enabled", False),
        email_to=notification_data.get("email_to", []),
        webhook_url=notification_data.get("webhook_url", ""),
    )

    # Parse report config
    report_data = data.get("reports", {})
    reports = ReportConfig(
        enabled=report_data.get("enabled", False),
        format=report_data.get("format", "json"),
        output_path=report_data.get("output_path", ""),
    )

    # Parse interactive config
    interactive_data = data.get("interactive", {})
    interactive = InteractiveConfig(
        enabled=interactive_data.get("enabled", False),
        confirm_each=interactive_data.get("confirm_each", True),
    )

    # Parse progress config
    progress_data = data.get("progress", {})
    progress = ProgressConfig(
        enabled=progress_data.get("enabled", True),
    )

    return Config(
        project=project,
        testing=testing,
        updates=updates,
        backup=backup,
        logging=logging_config,
        security=security,
        notifications=notifications,
        reports=reports,
        interactive=interactive,
        progress=progress,
    )


def save_config(config: Config, config_path: Union[str, Path]) -> None:
    """Save configuration to a YAML or TOML file.

    Args:
        config: Configuration object to save.
        config_path: Path where configuration file will be saved.

    Raises:
        ConfigError: If configuration file cannot be written.
    """
    config_path = Path(config_path)

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ConfigError(f"Failed to create configuration directory: {e}") from e

    data = {
        "project": {
            "name": config.project.name,
            "python_version": config.project.python_version,
        },
        "testing": {
            "enabled": config.testing.enabled,
            "command": config.testing.command,
            "args": config.testing.args,
            "exclude_paths": config.testing.exclude_paths,
            "timeout_seconds": config.testing.timeout_seconds,
        },
        "updates": {
            "strategy": config.updates.strategy,
            "max_parallel": config.updates.max_parallel,
            "version_policy": config.updates.version_policy,
            "ignore_packages": config.updates.ignore_packages,
            "allow_only_packages": config.updates.allow_only_packages,
        },
        "backup": {
            "enabled": config.backup.enabled,
            "location": config.backup.location,
            "retention_days": config.backup.retention_days,
            "format": config.backup.format,
        },
        "logging": {
            "level": config.logging.level,
            "format": config.logging.format,
            "file": config.logging.file,
            "console": config.logging.console,
        },
        "security": {
            "require_virtualenv": config.security.require_virtualenv,
            "verify_signatures": config.security.verify_signatures,
            "check_vulnerabilities": config.security.check_vulnerabilities,
        },
        "notifications": {
            "enabled": config.notifications.enabled,
            "slack_webhook": config.notifications.slack_webhook,
            "slack_channel": config.notifications.slack_channel,
            "email_enabled": config.notifications.email_enabled,
            "email_to": config.notifications.email_to,
            "webhook_url": config.notifications.webhook_url,
        },
        "reports": {
            "enabled": config.reports.enabled,
            "format": config.reports.format,
            "output_path": config.reports.output_path,
        },
        "interactive": {
            "enabled": config.interactive.enabled,
            "confirm_each": config.interactive.confirm_each,
        },
        "progress": {
            "enabled": config.progress.enabled,
        },
    }

    try:
        with open(config_path, "w") as f:
            if config_path.suffix in (".yaml", ".yml"):
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            elif config_path.suffix == ".toml":
                toml.dump(data, f)
            else:
                raise ConfigError(f"Unsupported configuration file format: {config_path.suffix}")
    except (yaml.YAMLError, toml.TomlDecodeError) as e:
        raise ConfigError(f"Failed to serialize configuration: {e}") from e
    except OSError as e:
        raise ConfigError(f"Failed to write configuration file: {e}") from e


def validate_config(config: Config) -> bool:
    """Validate configuration object.

    Args:
        config: Configuration object to validate.

    Returns:
        bool: True if configuration is valid.

    Raises:
        ValidationError: If configuration is invalid.
    """
    # Validate project config
    if not config.project.name:
        raise ValidationError("Project name cannot be empty")

    if not config.project.python_version:
        raise ValidationError("Python version cannot be empty")

    # Validate testing config
    if not config.testing.command:
        raise ValidationError("Test command cannot be empty")

    if config.testing.timeout_seconds <= 0:
        raise ValidationError("Test timeout must be positive")

    # Validate updates config
    valid_strategies = ["sequential", "parallel"]
    if config.updates.strategy not in valid_strategies:
        raise ValidationError(
            f"Invalid update strategy: {config.updates.strategy}. "
            f"Must be one of: {', '.join(valid_strategies)}"
        )

    if config.updates.max_parallel <= 0:
        raise ValidationError("Max parallel updates must be positive")

    # Validate ignore_packages list
    if config.updates.ignore_packages:
        for pkg in config.updates.ignore_packages:
            if not validate_package_name(pkg):
                raise ValidationError(f"Invalid package name in ignore list: {pkg}")

    # Validate allow_only_packages list
    if config.updates.allow_only_packages:
        for pkg in config.updates.allow_only_packages:
            if not validate_package_name(pkg):
                raise ValidationError(f"Invalid package name in allow list: {pkg}")

    valid_policies = ["safe", "latest", "minor", "patch"]
    if config.updates.version_policy not in valid_policies:
        raise ValidationError(
            f"Invalid version policy: {config.updates.version_policy}. "
            f"Must be one of: {', '.join(valid_policies)}"
        )

    # Validate backup config
    valid_formats = ["txt", "json"]
    if config.backup.format not in valid_formats:
        raise ValidationError(
            f"Invalid backup format: {config.backup.format}. "
            f"Must be one of: {', '.join(valid_formats)}"
        )

    if config.backup.retention_days < 0:
        raise ValidationError("Backup retention days cannot be negative")

    # Validate logging config
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config.logging.level not in valid_levels:
        raise ValidationError(
            f"Invalid logging level: {config.logging.level}. "
            f"Must be one of: {', '.join(valid_levels)}"
        )

    valid_formats = ["simple", "detailed", "json"]
    if config.logging.format not in valid_formats:
        raise ValidationError(
            f"Invalid logging format: {config.logging.format}. "
            f"Must be one of: {', '.join(valid_formats)}"
        )

    # Validate report config
    if config.reports.format:
        valid_report_formats = ["json", "html", "markdown", "md"]
        if config.reports.format not in valid_report_formats:
            raise ValidationError(
                f"Invalid report format: {config.reports.format}. "
                f"Must be one of: {', '.join(valid_report_formats)}"
            )

    return True
