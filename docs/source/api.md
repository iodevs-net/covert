# API Reference

This page documents the public API for Covert.

## Module: covert

The main package providing safe package updates.

```{toctree}
:hidden:

covert
```

## Core Functions

### run_update_session

Main function to run an update session.

```python
from covert.core import run_update_session

session = run_update_session(
    config: Config,
    dry_run: bool = False,
    no_backup: bool = False,
    no_tests: bool = False,
    ignore_packages: Optional[List[str]] = None,
    allow_only_packages: Optional[List[str]] = None,
    parallel: bool = False,
) -> UpdateSession
```

**Parameters:**

- `config` (Config): Configuration object
- `dry_run` (bool): If True, simulate updates without making changes
- `no_backup` (bool): If True, skip creating backup
- `no_tests` (bool): If True, skip running tests
- `ignore_packages` (Optional[List[str]]): List of packages to ignore
- `allow_only_packages` (Optional[List[str]]): List of packages to allow (exclusive mode)
- `parallel` (bool): If True, update packages in parallel

**Returns:**

- UpdateSession: Session results and statistics

**Raises:**

- ValidationError: If configuration is invalid
- UpdateError: If critical error occurs

## Configuration

### load_config

Load configuration from a YAML or TOML file.

```python
from covert.config import load_config

config = load_config(config_path: Optional[Union[str, Path]] = None) -> Config
```

**Parameters:**

- `config_path` (Optional[Union[str, Path]]): Path to configuration file. If None, searches for default files.

**Returns:**

- Config: Loaded configuration object

**Raises:**

- ConfigError: If configuration file cannot be found or read
- ValidationError: If configuration data is invalid

### save_config

Save configuration to a YAML or TOML file.

```python
from covert.config import save_config

save_config(config: Config, config_path: Union[str, Path]) -> None
```

**Parameters:**

- `config` (Config): Configuration object to save
- `config_path` (Union[str, Path]): Path where configuration file will be saved

**Raises:**

- ConfigError: If configuration file cannot be written

### validate_config

Validate a configuration object.

```python
from covert.config import validate_config

result = validate_config(config: Config) -> bool
```

**Parameters:**

- `config` (Config): Configuration object to validate

**Returns:**

- bool: True if configuration is valid

**Raises:**

- ValidationError: If configuration is invalid

## Configuration Classes

### Config

Main configuration class.

```python
from covert.config import Config

config = Config(
    project: ProjectConfig,
    testing: TestingConfig = field(default_factory=TestingConfig),
    updates: UpdatesConfig = field(default_factory=UpdatesConfig),
    backup: BackupConfig = field(default_factory=BackupConfig),
    logging: LoggingConfig = field(default_factory=LoggingConfig),
    security: SecurityConfig = field(default_factory=SecurityConfig),
)
```

### ProjectConfig

Project-specific configuration.

```python
from covert.config import ProjectConfig

project = ProjectConfig(
    name: str,
    python_version: str,
)
```

### TestingConfig

Testing configuration.

```python
from covert.config import TestingConfig

testing = TestingConfig(
    enabled: bool = True,
    command: str = "pytest",
    args: List[str] = ["-v", "--tb=short"],
    exclude_paths: List[str] = [],
    timeout_seconds: int = 300,
)
```

### UpdatesConfig

Package update configuration.

```python
from covert.config import UpdatesConfig

updates = UpdatesConfig(
    strategy: str = "sequential",
    max_parallel: int = 3,
    version_policy: str = "safe",
    ignore_packages: List[str] = [],
    allow_only_packages: Optional[List[str]] = None,
)
```

### BackupConfig

Backup configuration.

```python
from covert.config import BackupConfig

backup = BackupConfig(
    enabled: bool = True,
    location: str = "./backups",
    retention_days: int = 30,
    format: str = "txt",
)
```

### LoggingConfig

Logging configuration.

```python
from covert.config import LoggingConfig

logging_config = LoggingConfig(
    level: str = "INFO",
    format: str = "detailed",
    file: str = "covert.log",
    console: bool = True,
)
```

### SecurityConfig

Security configuration.

```python
from covert.config import SecurityConfig

security = SecurityConfig(
    require_virtualenv: bool = True,
    verify_signatures: bool = False,
    check_vulnerabilities: bool = True,
)
```

## Data Classes

### UpdateSession

Tracks an entire update session.

```python
from covert.core import UpdateSession

session = UpdateSession(
    start_time: datetime,
    end_time: Optional[datetime] = None,
    backup_file: Optional[str] = None,
    results: List[UpdateResult] = [],
    pre_test_passed: bool = False,
    dry_run: bool = False,
)
```

**Properties:**

- `summary` (Dict[str, int]): Count of packages by status
- `success` (bool): True if no critical failures occurred
- `updated_count` (int): Number of successfully updated packages
- `rolled_back_count` (int): Number of rolled back packages

### UpdateResult

Result of a package update attempt.

```python
from covert.core import UpdateResult, UpdateStatus

result = UpdateResult(
    package: PackageInfo,
    status: UpdateStatus,
    timestamp: datetime,
    error_message: Optional[str] = None,
    test_output: Optional[str] = None,
    test_passed: bool = False,
)
```

### PackageInfo

Information about a package.

```python
from covert.core import PackageInfo

package = PackageInfo(
    name: str,
    current_version: str,
    latest_version: str,
    package_type: str = "regular",
)
```

### UpdateStatus

Enum for update status values.

```python
from covert.core import UpdateStatus

status = UpdateStatus.UPDATED
status = UpdateStatus.ROLLED_BACK
status = UpdateStatus.FAILED_INSTALL
status = UpdateStatus.CRITICAL_FAILURE
status = UpdateStatus.SKIPPED
status = UpdateStatus.PENDING
```

## Utility Functions

### is_in_virtualenv

Check if running inside a virtual environment.

```python
from covert.utils import is_in_virtualenv

result = is_in_virtualenv() -> bool
```

### check_elevated_privileges

Check if running with elevated privileges.

```python
from covert.utils import check_elevated_privileges

result = check_elevated_privileges() -> bool
```

### validate_package_name

Validate a package name.

```python
from covert.utils import validate_package_name

result = validate_package_name(name: str) -> bool
```

### sanitize_package_name

Sanitize a package name.

```python
from covert.utils import sanitize_package_name

name = sanitize_package_name(name: str) -> str
```

### is_breaking_change

Check if a version change is breaking.

```python
from covert.utils import is_breaking_change

result = is_breaking_change(
    current_version: str,
    new_version: str,
    policy: str,
) -> bool
```

## Exceptions

All exceptions inherit from CovertError.

```python
from covert.exceptions import (
    CovertError,
    ConfigError,
    ValidationError,
    UpdateError,
    TestError,
    BackupError,
    PipError,
    SecurityError,
)
```

### Exception Hierarchy

```
CovertError (base)
├── ConfigError
├── ValidationError
├── UpdateError
├── TestError
├── BackupError
├── PipError
└── SecurityError
```

## Logger

### setup_logging

Set up logging for Covert.

```python
from covert.logger import setup_logging

setup_logging(
    logging_config: LoggingConfig,
    verbose_level: int = 0,
) -> None
```

### get_logger

Get a logger for a module.

```python
from covert.logger import get_logger

logger = get_logger(name: str) -> logging.Logger
```

## CLI Entry Point

### main

Main CLI entry point.

```python
from covert.cli import main

exit_code = main(args: Optional[List[str]] = None) -> int
```

**Returns:**

- int: Exit code (0 for success, non-zero for error)

## Complete Example

```python
from covert import load_config, Config
from covert.core import run_update_session
from covert.exceptions import CovertError

try:
    # Load configuration
    config = load_config("covert.yaml")
    
    # Run update session
    session = run_update_session(
        config=config,
        dry_run=True,  # Preview only
    )
    
    # Check results
    print(f"Updated: {session.updated_count}")
    print(f"Rolled back: {session.rolled_back_count}")
    print(f"Success: {session.success}")
    
except CovertError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Next Steps

- [CLI Reference](cli.md) - Command-line options
- [Configuration](configuration.md) - Configuration options
- [Troubleshooting](troubleshooting.md) - Common issues
