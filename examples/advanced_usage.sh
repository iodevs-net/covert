#!/bin/bash
# Advanced usage examples for Covert

# This script demonstrates advanced usage patterns

echo "=== Covert Advanced Usage Examples ==="

# -----------------------------
# Basic Usage
# -----------------------------

echo ""
echo "--- Basic Usage ---"

# Run with defaults
echo "$ covert"
#covert

# -----------------------------
# Dry Run Mode
# -----------------------------

echo ""
echo "--- Dry Run Mode ---"

# Preview without making changes
echo "$ covert --dry-run"
#covert --dry-run

# -----------------------------
# Configuration Files
# -----------------------------

echo ""
echo "--- Configuration Files ---"

# Use specific config file
echo "$ covert -c config.yaml"
#covert -c config.yaml

# Use TOML config
echo "$ covert -c config.toml"
#covert -c config.toml

# -----------------------------
# Selective Updates
# -----------------------------

echo ""
echo "--- Selective Updates ---"

# Ignore specific packages
echo "$ covert --ignore package1,package2"
#covert --ignore django,celery

# -----------------------------
# Testing Options
# -----------------------------

echo ""
echo "--- Testing Options ---"

# Skip tests
echo "$ covert --no-tests"
#covert --no-tests

# Skip backup
echo "$ covert --no-backup"
#covert --no-backup

# -----------------------------
# Verbose Output
# -----------------------------

echo ""
echo "--- Verbose Output ---"

# Increase verbosity
echo "$ covert -v      # INFO level"
echo "$ covert -vv     # DEBUG level"
echo "$ covert -vvv    # Maximum verbosity"

# -----------------------------
# Parallel Updates
# -----------------------------

echo ""
echo "--- Parallel Updates (Experimental) ---"

# Enable parallel updates
echo "$ covert --parallel"
#covert --parallel

# -----------------------------
# Combining Options
# -----------------------------

echo ""
echo "--- Combining Options ---"

# Common production use
echo "$ covert -c production.yaml --dry-run -v"

# CI/CD use
echo "$ covert -c ci-config.yaml -v --no-backup"

# -----------------------------
# Environment Variables
# -----------------------------

echo ""
echo "--- Environment Variables ---"

# Using environment variables
echo "$ export COVERT_CONFIG=./covert.yaml"
echo "$ export COVERT_LOG_LEVEL=DEBUG"
echo "$ export COVERT_DRY_RUN=true"
echo "$ covert"

# -----------------------------
# Exit Codes
# -----------------------------

echo ""
echo "--- Exit Codes ---"

echo "0  - Success"
echo "1  - General error"
echo "3  - Virtual environment required"
echo "4  - Elevated privileges detected"

# -----------------------------
# Logging
# -----------------------------

echo ""
echo "--- Log Output ---"

# Check logs after run
echo "$ cat covert.log"

# Use custom log location
echo "# With custom config:"
echo "logging:"
echo "  file: /var/log/covert.log"

# -----------------------------
# Programmatic Usage
# -----------------------------

echo ""
echo "--- Programmatic Usage (Python) ---"

cat << 'EOF'
# Using Covert in Python code
from covert import load_config
from covert.core import run_update_session

config = load_config("covert.yaml")
session = run_update_session(config, dry_run=True)

print(f"Updated: {session.updated_count}")
print(f"Success: {session.success}")
EOF

# -----------------------------
# Troubleshooting
# -----------------------------

echo ""
echo "--- Troubleshooting ---"

# Maximum verbosity for debugging
echo "$ covert -vvv 2>&1 | tee debug.log"

# Check configuration
echo "# Validate configuration"
echo "$ python -c \"from covert.config import load_config; c = load_config('config.yaml'); print(c)\""

echo ""
echo "=== Examples Complete ==="
