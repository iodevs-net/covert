# Configuration Reference

Covert can be configured using YAML or TOML configuration files. This page documents all available configuration options.

## Configuration File Discovery

Covert searches for configuration files in the following order:

1. Path specified via `--config` / `-c` command-line option
2. `COVERT_CONFIG` environment variable
3. Default files in current directory:
   - `covert.yaml`
   - `covert.toml`
   - `.covert.yml`

## Configuration Schema

### Project Configuration

```yaml
project:
  name: "My Project"           # Required: Project name
  python_version: "3.11"       # Required: Python version
```

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `name` | string | Yes | - | Name of your project |
| `python_version` | string | Yes | - | Python version being used (e.g., "3.11") |

### Testing Configuration

```yaml
testing:
  enabled: true                # Enable/disable testing
  command: "pytest"            # Test command to run
  args:                        # Arguments for test command
    - "-v"
    - "--tb=short"
  exclude_paths:               # Paths to exclude from tests
    - "tests/e2e"
    - "tests/integration"
  timeout_seconds: 300         # Test timeout in seconds
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Whether to run tests |
| `command` | string | `"pytest"` | Test command to run |
| `args` | list | `["-v", "--tb=short"]` | Arguments passed to test command |
| `exclude_paths` | list | `[]` | Paths to exclude from testing |
| `timeout_seconds` | integer | `300` | Maximum time to wait for tests |

### Updates Configuration

```yaml
updates:
  strategy: "sequential"      # Update strategy
  max_parallel: 3             # Max parallel updates
  version_policy: "safe"      # Version policy
  ignore_packages:             # Packages to ignore
    - "package1"
    - "package2"
  allow_only_packages:         # Packages to allow (exclusive)
    - "package3"
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `strategy` | string | `"sequential"` | Update strategy: `"sequential"` or `"parallel"` |
| `max_parallel` | integer | `3` | Maximum number of parallel updates |
| `version_policy` | string | `"safe"` | Version policy: `"safe"`, `"latest"`, `"minor"`, `"patch"` |
| `ignore_packages` | list | `[]` | List of packages to ignore during updates |
| `allow_only_packages` | list | `null` | If set, only update these packages |

#### Version Policies

| Policy | Description | Example |
|--------|-------------|---------|
| `safe` | Only update if no breaking changes detected | 2.0.0 → 2.1.0 (yes), 2.0.0 → 3.0.0 (no) |
| `latest` | Update to latest available version | 2.0.0 → 3.0.0 (yes) |
| `minor` | Update within minor version | 2.1.0 → 2.2.0 (yes), 2.1.0 → 3.0.0 (no) |
| `patch` | Update within patch version only | 2.1.1 → 2.1.2 (yes), 2.1.1 → 2.2.0 (no) |

### Backup Configuration

```yaml
backup:
  enabled: true                # Enable/disable backups
  location: "./backups"        # Backup directory
  retention_days: 30          # Days to keep backups
  format: "txt"               # Backup format: "txt" or "json"
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Whether to create backups |
| `location` | string | `"./backups"` | Directory to store backups |
| `retention_days` | integer | `30` | Number of days to keep backups |
| `format` | string | `"txt"` | Backup format: `"txt"` or `"json"` |

### Logging Configuration

```yaml
logging:
  level: "INFO"               # Log level
  format: "detailed"          # Log format
  file: "covert.log"          # Log file path
  console: true               # Output to console
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `level` | string | `"INFO"` | Log level: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"` |
| `format` | string | `"detailed"` | Log format: `"simple"`, `"detailed"`, `"json"` |
| `file` | string | `"covert.log"` | Path to log file |
| `console` | boolean | `true` | Whether to output logs to console |

### Security Configuration

```yaml
security:
  require_virtualenv: true    # Require virtual environment
  verify_signatures: false    # Verify package signatures
  check_vulnerabilities: true # Check for vulnerabilities
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `require_virtualenv` | boolean | `true` | Require running in a virtual environment |
| `verify_signatures` | boolean | `false` | Verify package signatures (requires additional setup) |
| `check_vulnerabilities` | boolean | `true` | Check for known vulnerabilities |

## Example Configurations

### Minimal Configuration

```yaml
project:
  name: "My Project"
  python_version: "3.11"
```

### Django Project Configuration

```yaml
project:
  name: "My Django Project"
  python_version: "3.11"

testing:
  enabled: true
  command: "pytest"
  args:
    - "--ds=myproject.settings.test"
    - "-v"
    - "--tb=short"
  exclude_paths:
    - "tests/e2e"
  timeout_seconds: 600

updates:
  strategy: "sequential"
  version_policy: "safe"
  ignore_packages:
    - "django"  # Handle Django upgrades manually
    - "djangorestframework"

backup:
  enabled: true
  location: "./backups"
  retention_days: 30

logging:
  level: "INFO"
  format: "detailed"
  console: true
```

### CI/CD Configuration

```yaml
project:
  name: "CI Project"
  python_version: "3.11"

testing:
  enabled: true
  command: "pytest"
  args:
    - "-v"
    - "--tb=short"
    - "-x"  # Stop on first failure

updates:
  strategy: "sequential"
  version_policy: "patch"  # Conservative for CI

backup:
  enabled: true
  location: "/tmp/covert-backups"
  retention_days: 1

logging:
  level: "DEBUG"
  format: "json"
  console: true
```

## Configuration Priority

Configuration values are resolved in the following priority order (highest to lowest):

1. Command-line arguments (e.g., `--ignore`, `--dry-run`)
2. Environment variables
3. Configuration file
4. Default values

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `COVERT_CONFIG` | Path to configuration file | `./covert.yaml` |
| `COVERT_LOG_LEVEL` | Logging level | `INFO` |
| `COVERT_NO_COLOR` | Disable colored output | `false` |
| `COVERT_DRY_RUN` | Enable dry-run mode | `false` |

## Loading Configuration Programmatically

```python
from covert.config import load_config, Config

# Load from file
config = load_config("covert.yaml")

# Access configuration
print(config.project.name)
print(config.updates.version_policy)

# Validate configuration
from covert.config import validate_config
validate_config(config)
```

## Next Steps

- [Usage Guide](usage.md) - Learn about common use cases
- [CLI Reference](cli.md) - Command-line options
- [API Reference](api.md) - Programmatic usage
