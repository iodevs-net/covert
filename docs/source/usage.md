# Usage Guide

This guide covers common usage scenarios and workflows for Covert.

## Basic Usage

### Running Updates

```bash
# Basic update (all defaults)
covert

# With custom configuration
covert -c my-config.yaml
```

### Dry Run Mode

Preview what would happen without making any changes:

```bash
covert --dry-run
```

This is useful to:
- See which packages would be updated
- Check the versions that would be installed
- Verify your configuration is correct

## Common Workflows

### Workflow 1: Conservative Updates

Use safe version policy to only update patch and minor versions:

```bash
covert --dry-run  # Preview first
covert            # Apply
```

With configuration:

```yaml
updates:
  version_policy: "safe"
```

### Workflow 2: Selective Updates

Update only specific packages:

```bash
# Only update these packages
covert --config config.yaml
```

With configuration:

```yaml
updates:
  allow_only_packages:
    - "requests"
    - "django"
```

### Workflow 3: Ignoring Problematic Packages

Skip specific packages that need manual handling:

```bash
covert --ignore django,celery
```

With configuration:

```yaml
updates:
  ignore_packages:
    - "django"    # Handle major upgrades manually
    - "celery"    # Complex dependency
```

### Workflow 4: Skip Tests or Backup

```bash
# Skip running tests (not recommended)
covert --no-tests

# Skip creating backup
covert --no-backup

# Skip both
covert --no-tests --no-backup
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/update-dependencies.yml
name: Update Dependencies

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Covert
        run: pip install covert-updater
      
      - name: Run Covert
        run: |
          covert --dry-run >> $GITHUB_STEP_SUMMARY
      
      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v5
        with:
          commit-message: 'chore: Update dependencies'
          title: 'Update Dependencies'
          body: |
            Automated dependency updates by Covert.
            See the dry-run output for details.
          branch: dependency-updates
```

### GitLab CI

```yaml
# .gitlab-ci.yml
update-dependencies:
  image: python:3.11-slim
  script:
    - pip install covert-updater
    - covert --dry-run
  only:
    - schedule
  schedule:
    - cron: '0 0 * * 0'
```

### CircleCI

```yaml
# .circleci/config.yml
jobs:
  update-dependencies:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - run:
          name: Install Covert
          command: pip install covert-updater
      - run:
          name: Update Dependencies
          command: covert --dry-run
workflows:
  nightly:
    jobs:
      - update-dependencies
    triggers:
      - schedule:
          cron: "0 0 * * *"
          filters:
            branches:
              only:
                - main
```

## Programmatic Usage

### Using the Python API

```python
from covert import Config, ProjectConfig, load_config
from covert.core import run_update_session

# Load configuration
config = load_config("covert.yaml")

# Run update session
session = run_update_session(
    config=config,
    dry_run=False,
    no_backup=False,
    no_tests=False,
)

# Check results
print(f"Updated: {session.updated_count}")
print(f"Rolled back: {session.rolled_back_count}")
print(f"Success: {session.success}")

# Access detailed results
for result in session.results:
    print(f"{result.package.name}: {result.status.value}")
```

### Creating Configuration Programmatically

```python
from covert.config import (
    Config,
    ProjectConfig,
    TestingConfig,
    UpdatesConfig,
    BackupConfig,
    LoggingConfig,
    SecurityConfig,
)

config = Config(
    project=ProjectConfig(
        name="My Project",
        python_version="3.11",
    ),
    testing=TestingConfig(
        enabled=True,
        command="pytest",
        args=["-v"],
    ),
    updates=UpdatesConfig(
        version_policy="safe",
    ),
    backup=BackupConfig(
        enabled=True,
    ),
)
```

## Advanced Usage

### Parallel Updates

Enable parallel updates for faster processing:

```bash
covert --parallel
```

With configuration:

```yaml
updates:
  strategy: "parallel"
  max_parallel: 3
```

### Verbose Logging

```bash
# INFO level (default)
covert

# DEBUG level
covert -v

# More verbose
covert -vv
```

## Troubleshooting

### Package Fails Tests

If a package update causes tests to fail, Covert will automatically:
1. Roll back to the previous version
2. Mark the package as "rolled_back"
3. Continue with the next package

Check the logs for details:

```bash
covert -vvv 2>&1 | tee debug.log
```

### Virtual Environment Issues

If you see "Virtual environment is required":

```bash
# Activate your virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Run Covert again
covert
```

Or disable the requirement (not recommended):

```yaml
security:
  require_virtualenv: false
```

### Configuration Errors

Validate your configuration:

```python
from covert.config import load_config, validate_config

config = load_config("covert.yaml")
validate_config(config)
```

## Best Practices

1. **Always run dry-run first**: Preview changes before applying
2. **Use safe version policy**: Avoid breaking changes
3. **Keep backups enabled**: Easy recovery from failures
4. **Test in CI first**: Verify updates work in CI before production
5. **Ignore problematic packages**: Handle complex packages manually

## Next Steps

- [CLI Reference](cli.md) - All command-line options
- [API Reference](api.md) - Programmatic API
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
