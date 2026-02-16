# Quick Start Guide

Get up and running with Covert in just a few minutes. This guide will walk you through the basics of installing and using Covert.

## Prerequisites

Before you begin, ensure you have:

- Python 3.8 or higher installed
- A virtual environment set up for your project
- pip is up to date

## Step 1: Install Covert

Install Covert using pip:

```bash
pip install covert-up
```

Or install from source:

```bash
git clone https://github.com/iodevs-net/covert.git
cd covert
pip install -e .
```

## Step 2: Verify Installation

Check that Covert is installed correctly:

```bash
covert --version
```

You should see output like:

```
Covert 0.1.0
```

## Step 3: Create a Configuration File (Optional)

While Covert works with defaults, creating a configuration file gives you more control. Create a `covert.yaml` file in your project root:

```yaml
project:
  name: "My Project"
  python_version: "3.11"

testing:
  enabled: true
  command: "pytest"
  args:
    - "-v"
  timeout_seconds: 300

updates:
  version_policy: "safe"
  ignore_packages: []

backup:
  enabled: true
  location: "./backups"

logging:
  level: "INFO"
  console: true
```

## Step 4: Run Your First Update

### Dry Run (Recommended First)

First, try a dry run to see what would happen without making any changes:

```bash
covert --dry-run
```

This will:
- Detect all outdated packages
- Show what versions would be installed
- NOT make any actual changes

### Actual Update

When ready to update:

```bash
covert
```

Covert will:
1. Check if you're in a virtual environment
2. Run pre-flight tests
3. Create a backup
4. Update each package one by one
5. Run tests after each update
6. Roll back if tests fail

## Understanding the Output

Here's what a typical Covert session looks like:

```
============================================================
Starting Covert update session
============================================================
Running pre-flight tests...
Pre-flight tests passed
Creating backup...
Backup created: backups/covert_2024_01_15_123456.txt
Checking for outdated packages...
Found 5 package(s) to update
------------------------------------------------------------
Updating package: requests
  Current: 2.25.0
  Latest:  2.31.0
Installing requests==2.31.0
Successfully installed requests==2.31.0
Running tests for requests...
Successfully updated requests
------------------------------------------------------------
Updating package: django
  Current: 4.1.0
  Latest:  4.2.0
Skipping django: version change is breaking under 'safe' policy
------------------------------------------------------------
Update session summary
============================================================
Duration: 45.23 seconds
Updated: 1
Rolled back: 0
Failed: 0
Skipped: 1
============================================================
```

## Common Commands

### Basic Usage

```bash
# Update all packages
covert

# Dry run
covert --dry-run

# With custom config
covert -c my-config.yaml
```

### Selective Updates

```bash
# Ignore specific packages
covert --ignore package1,package2

# Skip tests
covert --no-tests

# Skip backup
covert --no-backup
```

### Verbose Output

```bash
# Increase verbosity
covert -v      # INFO level
covert -vv     # DEBUG level
```

## Next Steps

Now that you're up and running, learn more about:

- [Configuration](configuration.md) - Customize Covert's behavior
- [Usage Examples](usage.md) - Common use cases and workflows
- [CLI Reference](cli.md) - All command-line options
- [API Reference](api.md) - Programmatic usage

## Troubleshooting

If you encounter issues, check the [Troubleshooting Guide](troubleshooting.md).
