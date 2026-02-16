# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-15

### Added

- **Core Package Structure**: Created the main `covert` package with modular architecture
- **Configuration System**: Implemented YAML/TOML configuration file support
- **Package Detection**: Added functionality to detect outdated packages using pip
- **Package Updates**: Implemented controlled package-by-package updates
- **Test Execution**: Added configurable test runner that runs after each update
- **Automatic Rollback**: Implemented automatic rollback when tests fail
- **Backup System**: Created backup functionality to save state before updates
- **CLI Interface**: Full command-line interface with argument parsing
- **Security Features**:
  - Virtual environment detection and enforcement
  - Root/elevated privilege detection
  - Package name and version validation
- **Version Policies**: Implemented version update policies (safe, latest, minor, patch)
- **Dry-Run Mode**: Added ability to simulate updates without making changes
- **Logging System**: Comprehensive logging with configurable levels and formats
- **Exception Handling**: Custom exception hierarchy for different error types

### Changed

- **Code Structure**: Converted from single script to proper Python package
- **Security Hardening**: Removed all `shell=True` subprocess calls for security
- **Language Standardization**: Converted all comments and logs to English

### Deprecated

Nothing deprecated in this release.

### Removed

Nothing removed in this release.

### Fixed

- Input validation for package names and versions
- Virtual environment detection on different platforms

### Security

- No `shell=True` in any subprocess call
- Package name validation to prevent injection attacks
- Virtual environment requirement to prevent system Python damage
- Privilege escalation warnings

## [1.0.0] - 2026-02-16

### Added

- Documentation structure with Sphinx
- Quick start guide
- Configuration reference
- Usage examples
- API documentation
- CLI reference
- Contributing guidelines
- Troubleshooting guide

### Changed

Nothing changed in this release.

### Deprecated

Nothing deprecated in this release.

### Removed

Nothing removed in this release.

### Fixed

Nothing fixed in this release.

### Security

Nothing security-related in this release.

---

## Version History

| Version | Status | Date |
|---------|--------|------|
| 0.1.0 | Alpha | 2024-01-15 |

## Upgrading

### From 0.1.0

No upgrade path needed as this is the initial release.

## Known Issues

- Parallel update mode is experimental
- Some edge cases in rollback may need additional testing
- CI/CD integration examples are provided as templates

## Migration Guides

### Coming from pip-tools or pip-review

Covert provides similar functionality but with additional safety features:

1. **Test After Each Update**: Covert runs your tests after each package update
2. **Automatic Rollback**: If tests fail, Covert automatically rolls back
3. **Backup Creation**: Covert creates backups before making changes
4. **Version Policies**: Covert supports safe version policies to avoid breaking changes

To migrate, simply:

```bash
pip install covert-up
dry-run  # Preview
covert --covert            # Run actual updates
```
