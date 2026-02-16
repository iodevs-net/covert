# CLI Reference

Complete reference for the Covert command-line interface.

## Usage

```bash
covert [OPTIONS]
```

## Options

### Configuration Options

`--config PATH`, `-c PATH`

: Path to configuration file (YAML or TOML format)

: Default: Searches for `covert.yaml`, `covert.toml`, or `.covert.yml`

: Example: `covert -c my-config.yaml`

`--ignore PACKAGES`

: Comma-separated list of packages to ignore during updates

: Example: `covert --ignore django,celery`

### Operation Modes

`--dry-run`

: Simulate updates without installing any packages

: Use this to preview what would happen without making changes

: Example: `covert --dry-run`

`--no-backup`

: Skip creating backup before updates

: Not recommended - backups provide protection against failures

: Example: `--no-backup`

`--no-tests`

: Skip running tests before and after updates

: Not recommended - tests verify that updates don't break functionality

: Example: `--no-tests`

`--parallel`

: Enable parallel package updates (experimental)

: Uses multiple threads to update packages concurrently

: May cause issues with tests that depend on package installation order

: Example: `--parallel`

### Output Options

`--verbose`, `-v`

: Increase verbosity level

: Can be used multiple times:
  - `-v` - INFO level
  - `-vv` - DEBUG level

: Example: `covert -vv`

### Information Options

`--version`

: Show version information and exit

: Example: `covert --version`

`--help`, `-h`

: Show help message and exit

: Example: `covert --help`

## Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | All updates completed successfully |
| 1 | General Error | An error occurred during the update process |
| 3 | Virtual Environment Required | Not running in a virtual environment |
| 4 | Elevated Privileges | Running as root/administrator |

## Environment Variables

`COVERT_CONFIG`

: Path to configuration file

: Default: `./covert.yaml`

: Example: `export COVERT_CONFIG=/path/to/config.yaml`

`COVERT_LOG_LEVEL`

: Logging level

: Default: `INFO`

: Valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

: Example: `export COVERT_LOG_LEVEL=DEBUG`

`COVERT_NO_COLOR`

: Disable colored output

: Default: `false`

: Example: `export COVERT_NO_COLOR=true`

`COVERT_DRY_RUN`

: Enable dry-run mode

: Default: `false`

: Example: `export COVERT_DRY_RUN=true`

## Examples

### Basic Usage

```bash
# Run with defaults
covert

# Run with specific config
covert -c my-config.yaml
```

### Preview Changes

```bash
# Dry run to see what would happen
covert --dry-run

# Verbose dry run
covert --dry-run -vv
```

### Selective Updates

```bash
# Ignore specific packages
covert --ignore package1,package2

# Only update specific packages (via config)
covert -c config-with-allow-list.yaml
```

### Debugging

```bash
# Maximum verbosity
covert -vvv

# Log to file
covert -vv 2>&1 | tee debug.log
```

### Skip Safety Features

```bash
# Skip backup (not recommended)
covert --no-backup

# Skip tests (not recommended)
covert --no-tests

# Skip both (not recommended)
covert --no-backup --no-tests
```

## Configuration vs CLI Arguments

CLI arguments take precedence over configuration file settings.

| CLI Argument | Config Option |
|--------------|---------------|
| `--ignore` | `updates.ignore_packages` |
| `--dry-run` | N/A (run-time only) |
| `--no-backup` | `backup.enabled: false` |
| `--no-tests` | `testing.enabled: false` |
| `--parallel` | `updates.strategy: parallel` |
| `-v` | `logging.level` |

## Interactive Usage

For interactive use, consider:

```bash
# Preview first
covert --dry-run

# If happy with changes, run actual update
covert
```

## Integration with Tools

### Shell Scripts

```bash
#!/bin/bash
# update-deps.sh

set -e

echo "Running Covert..."
covert --dry-run

read -p "Proceed with updates? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    covert
    echo "Updates complete!"
else
    echo "Updates cancelled."
fi
```

### Makefile

```makefile
.PHONY: update-deps

update-deps:
	covert --dry-run
	@read -p "Proceed with updates? (y/n) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$ ]]; then \
		covert; \
	fi
```

## Next Steps

- [Configuration](configuration.md) - Configuration file options
- [Usage](usage.md) - Common usage scenarios
- [API Reference](api.md) - Programmatic API
- [Troubleshooting](troubleshooting.md) - Common issues
