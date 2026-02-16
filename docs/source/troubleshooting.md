# Troubleshooting Guide

This guide covers common issues you might encounter when using Covert and how to resolve them.

## Common Issues

### Virtual Environment Errors

#### Issue: "Virtual environment is required"

**Error message:**
```
Not running in a virtual environment. Please activate a virtual environment before running Covert.
```

**Cause:** Covert requires running in a virtual environment for safety.

**Solution:**
```bash
# Activate your virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Run Covert
covert
```

**Alternative:** If you must run outside a virtual environment, disable the requirement (not recommended):

```yaml
# covert.yaml
security:
  require_virtualenv: false
```

### Privilege Errors

#### Issue: "Running with elevated privileges"

**Error message:**
```
Covert should not be run with elevated privileges (root/administrator).
```

**Cause:** Running Covert as root can damage your Python environment.

**Solution:**
- Create a non-root user and run Covert as that user
- Use a virtual environment owned by a non-root user

### Configuration Errors

#### Issue: "Configuration file not found"

**Error message:**
```
Configuration file not found: covert.yaml
```

**Cause:** Covert cannot find the configuration file.

**Solution:**
```bash
# Use explicit path
covert -c /path/to/config.yaml

# Or ensure config is in current directory
ls -la covert.yaml
```

#### Issue: "Invalid configuration"

**Error message:**
```
Invalid configuration: Project name is required
```

**Cause:** Missing required configuration fields.

**Solution:** Ensure your configuration has required fields:

```yaml
project:
  name: "My Project"         # Required
  python_version: "3.11"    # Required
```

### Test Errors

#### Issue: "Pre-flight tests failed"

**Error message:**
```
Pre-flight tests failed. Aborting update session.
```

**Cause:** Tests are failing before any updates are applied.

**Solution:**
1. Fix your test suite first
2. Or skip pre-flight tests temporarily:

```bash
covert --no-tests
```

3. Or disable in configuration:

```yaml
testing:
  enabled: false
```

#### Issue: "Tests failed after updating package"

**Error message:**
```
Tests failed after updating package: requests
```

**Cause:** The updated package broke your tests.

**Solution:**
1. Covert should automatically rollback the package
2. Check the logs for details
3. Add the package to ignore list:

```bash
covert --ignore problematic-package
```

### Installation Errors

#### Issue: "command not found: covert"

**Error message:**
```
bash: covert: command not found
```

**Cause:** Covert is not installed or not in PATH.

**Solution:**
```bash
# Install Covert
pip install covert-up

# Verify installation
pip show covert-up

# Or use Python module syntax
python -m covert --version
```

#### Issue: "pip install fails"

**Error message:**
```
ERROR: Could not find a version that satisfies the requirement...
```

**Cause:** Python version or platform incompatibility.

**Solution:**
```bash
# Check Python version
python --version

# Ensure using correct pip
python -m pip install covert-up
```

### Backup Errors

#### Issue: "Failed to create backup"

**Error message:**
```
Failed to create backup: [Errno 17] File exists: ./backups
```

**Cause:** Backup directory doesn't exist or permission issues.

**Solution:**
```bash
# Create backup directory
mkdir -p backups

# Or change backup location in config
backup:
  location: "/tmp/covert-backups"
```

### Network Errors

#### Issue: "Connection timeout"

**Error message:**
```
ConnectionError: HTTPSConnectionPool: Read timed out
```

**Cause:** Network issues or PyPI is slow.

**Solution:**
1. Retry the operation
2. Use a PyPI mirror
3. Check your network connection

## Debugging Steps

### Enable Verbose Logging

```bash
# Maximum verbosity
covert -vvv 2>&1 | tee debug.log
```

### Check Configuration

```python
from covert.config import load_config, validate_config

config = load_config("covert.yaml")
validate_config(config)
print(config)
```

### Dry Run First

Always try dry run first:

```bash
covert --dry-run -vv
```

### Check Logs

```bash
# Default log location
cat covert.log

# Or check console output
covert -vv
```

## Exit Codes

| Code | Issue | Solution |
|------|-------|----------|
| 0 | Success | No action needed |
| 1 | General Error | Check logs for details |
| 3 | Virtual env required | Activate virtual environment |
| 4 | Elevated privileges | Run as non-root user |

## Getting Help

### Check Logs

Logs contain detailed information about what happened:

```bash
# Check log file
cat covert.log

# Or run with verbose output
covert -vv
```

### Enable Debug Mode

```bash
covert -vvv
```

### Common Fixes

1. **Restart fresh**: Delete cache and try again
   ```bash
   rm -rf .covert_cache covert.log backups/
   covert --dry-run
   ```

2. **Check Python environment**
   ```bash
   which python
   python --version
   pip list | grep covert
   ```

3. **Verify virtual environment**
   ```bash
   python -c "import sys; print(sys.prefix)"
   ```

## Reporting Issues

If you encounter a bug:

1. Check if it's a [known issue](https://github.com/iodevs-net/covert/issues)
2. Include:
   - Covert version: `covert --version`
   - Python version: `python --version`
   - Full error message
   - Configuration file (sanitized)
   - Steps to reproduce

## Next Steps

- [Configuration](configuration.md) - Configuration options
- [Usage](usage.md) - Common usage scenarios
- [API Reference](api.md) - Programmatic API
