# Installation Guide

This guide covers all the ways to install Covert in your environment.

## Prerequisites

Before installing Covert, ensure you have:

- **Python 3.8 or higher**: Check with `python --version` or `python3 --version`
- **pip**: Latest version recommended (`pip install --upgrade pip`)
- **Virtual Environment**: Strongly recommended for isolation

## Python Version Support

Covert supports the following Python versions:

| Version | Status |
|---------|--------|
| 3.8 | ✅ Supported |
| 3.9 | ✅ Supported |
| 3.10 | ✅ Supported |
| 3.11 | ✅ Supported |
| 3.12 | ✅ Supported |

## Installation Methods

### Method 1: Install from PyPI (Recommended)

The easiest way to install Covert:

```bash
pip install covert-updater
```

To upgrade to the latest version:

```bash
pip install --upgrade covert-updater
```

### Method 2: Install with Extra Dependencies

#### Install with Development Dependencies

```bash
pip install covert-updater[dev]
```

This includes:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking support
- `black` - Code formatting
- `isort` - Import sorting
- `mypy` - Type checking
- `ruff` - Fast linting

#### Install with Documentation Dependencies

```bash
pip install covert-updater[docs]
```

This includes:
- `sphinx` - Documentation generator
- `sphinx-rtd-theme` - Read the Docs theme
- `myst-parser` - Markdown support for Sphinx

#### Install with Security Dependencies

```bash
pip install covert-updater[security]
```

This includes:
- `pip-audit` - Dependency vulnerability scanner
- `safety` - Security vulnerability checker

#### Install All Extras

```bash
pip install covert-updater[dev,docs,security]
```

### Method 3: Install from Source

```bash
# Clone the repository
git clone https://github.com/iodevs-net/covert.git
cd covert

# Install in editable mode
pip install -e .
```

### Method 4: Install in Virtual Environment

#### Using venv

```bash
# Create a new virtual environment
python -m venv venv

# Activate it (Linux/macOS)
source venv/bin/activate

# Activate it (Windows)
venv\Scripts\activate

# Install Covert
pip install covert-updater
```

#### Using Poetry

```bash
poetry add covert-updater
```

#### Using Pipenv

```bash
pipenv install covert-updater
```

## Verifying Installation

After installation, verify it works:

```bash
# Check version
covert --version

# Show help
covert --help
```

## Post-Installation Steps

### 1. Create Configuration File

Create a `covert.yaml` file in your project root:

```yaml
project:
  name: "My Project"
  python_version: "3.11"

testing:
  enabled: true
  command: "pytest"

updates:
  version_policy: "safe"

backup:
  enabled: true
```

### 2. Set Up Environment Variables (Optional)

You can configure Covert using environment variables:

```bash
export COVERT_CONFIG="./covert.yaml"
export COVERT_LOG_LEVEL="INFO"
```

### 3. Run a Test Update

```bash
covert --dry-run
```

## Troubleshooting Installation

### "command not found" Error

If the `covert` command is not found after installation, try:

```bash
# Reinstall
pip uninstall covert-updater
pip install covert-updater

# Or use Python module syntax
python -m covert --version
```

### Permission Errors

If you encounter permission errors:

```bash
# Use --user flag
pip install --user covert-updater

# Or use a virtual environment (recommended)
python -m venv venv
source venv/bin/activate
pip install covert-updater
```

### Python Version Mismatch

Ensure you're using the correct Python version:

```bash
# Check Python version
python --version

# If needed, specify Python version
python3.11 -m pip install covert-updater
```

## Uninstallation

To uninstall Covert:

```bash
pip uninstall covert-updater
```

If you installed from source and want to completely remove it:

```bash
# Remove the repository
rm -rf /path/to/covert

# Remove virtual environment (if created)
rm -rf venv/
```

## Next Steps

- [Quick Start](quickstart.md) - Get started with Covert
- [Configuration](configuration.md) - Customize Covert's behavior
- [Usage](usage.md) - Common usage scenarios
