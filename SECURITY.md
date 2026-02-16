# Security Policy

## Security Features

Covert implements multiple security features to ensure safe package updates and prevent common security vulnerabilities.

### Secure Command Execution

All subprocess calls in Covert use `shell=False` to prevent command injection attacks. Commands are executed as lists of arguments rather than shell strings, which eliminates the risk of shell metacharacters being interpreted.

```python
# Secure - always used in Covert
subprocess.run(["pip", "install", "requests"], shell=False, ...)

# Insecure - never used in Covert
subprocess.run("pip install requests", shell=True, ...)
```

### Input Validation

Covert validates all user inputs before use:

- **Package Names**: Validated against PEP 508 specification to prevent injection attempts
- **Version Strings**: Validated against PEP 440 specification
- **Paths**: Validated to prevent path traversal attacks (e.g., `../etc/passwd`)
- **Configuration Values**: All configuration values are validated before use

### Virtual Environment Enforcement

Covert requires running in a virtual environment by default. This prevents accidental modifications to system Python packages and provides isolation for package updates.

**Exit Code**: If not running in a virtual environment, Covert exits with code `3`.

To disable this check, set `security.require_virtualenv = false` in your configuration file (not recommended).

### Privilege Escalation Prevention

Covert detects when running with elevated privileges (root/administrator) and exits with an error. Running package managers with elevated privileges is a security risk and can damage your Python environment.

**Exit Code**: If running with elevated privileges, Covert exits with code `4`.

### Error Message Hardening

Error messages in Covert are designed to avoid exposing sensitive information:

- System paths are not included in user-facing error messages
- Detailed error information is logged but not shown to users
- Generic error messages are used for security-sensitive operations

## Security Best Practices

### For Users

1. **Always run in a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Never run Covert with elevated privileges**
   - Do not use `sudo` with Covert
   - Do not run as Administrator on Windows

3. **Review configuration files**
   - Ensure configuration files are not world-writable
   - Use secure file permissions (e.g., `chmod 600` for sensitive configs)

4. **Keep Covert updated**
   - Regularly update Covert to get the latest security patches

5. **Use secure package sources**
   - Configure pip to use trusted package indexes
   - Avoid using untrusted package sources

### For Developers

1. **Never use `shell=True` in subprocess calls**
   - Always pass commands as lists
   - Use `subprocess.run(cmd_list, shell=False, ...)`

2. **Validate all user inputs**
   - Use the provided validation functions in `covert.utils`
   - Never trust user input without validation

3. **Sanitize error messages**
   - Avoid exposing system paths
   - Avoid exposing configuration details
   - Log detailed errors but show generic messages to users

4. **Follow the principle of least privilege**
   - Only request necessary permissions
   - Avoid running with elevated privileges

## Reporting Vulnerabilities

If you discover a security vulnerability in Covert, please report it responsibly.

### How to Report

1. **Do not** create a public issue
2. **Do** send an email to: `security@iodevs.net`
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if known)

### Response Timeline

- Initial response within 48 hours
- Detailed response within 7 days
- Security advisory published within 90 days of fix

### Security Updates

Security updates will be:

1. Released as patch versions (e.g., `1.0.1`, `1.0.2`)
2. Announced in the release notes
3. Published on GitHub with security advisories
4. Available via PyPI immediately

## Security Configuration

Covert provides security-related configuration options:

```yaml
security:
  # Require virtual environment (default: true)
  require_virtualenv: true

  # Verify package signatures (future feature, default: false)
  verify_signatures: false

  # Check for known vulnerabilities (future feature, default: true)
  check_vulnerabilities: true
```

### Virtual Environment Requirement

When `require_virtualenv` is `true` (default):
- Covert will exit with code `3` if not in a virtual environment
- This prevents accidental system package modifications
- Recommended for production use

When `require_virtualenv` is `false`:
- Covert will run without checking for virtual environment
- **Not recommended** - can lead to system package modifications
- Use only in controlled environments

## Exit Codes

Covert uses specific exit codes for security-related errors:

| Exit Code | Meaning |
|------------|----------|
| 0 | Success |
| 1 | General error |
| 3 | Not running in a virtual environment |
| 4 | Running with elevated privileges |

## Security Testing

Covert includes comprehensive security tests:

- Command injection prevention tests
- Input validation tests
- Path traversal prevention tests
- Virtual environment detection tests
- Privilege escalation detection tests

Run security tests:

```bash
pytest tests/test_security.py -v
```

## Dependencies

Covert's dependencies are regularly audited for security vulnerabilities:

- `packaging` - Version parsing and comparison
- `pyyaml` - YAML configuration parsing
- `toml` - TOML configuration parsing

All dependencies are sourced from PyPI and verified before inclusion.

## Known Security Considerations

### Backup Files

Backup files created by Covert may contain:
- Package names and versions
- Installation timestamps
- Project-specific package requirements

Ensure backup files are stored securely:
- Use appropriate file permissions
- Store in secure directories
- Remove old backups regularly

### Log Files

Log files may contain:
- Package names and versions
- Error messages
- System paths (in debug mode)

Ensure log files are:
- Not world-writable
- Rotated regularly
- Stored in secure directories

### Test Execution

Covert runs user-configured test commands. Ensure:
- Test commands are from trusted sources
- Test commands do not expose sensitive data
- Test output does not contain secrets

## Compliance

Covert is designed with security best practices from:

- [PEP 508](https://peps.python.org/pep/pep-0508/) - Package name specification
- [PEP 440](https://peps.python.org/peps/pep-0440/) - Version specification
- [CWE-78](https://cwe.mitre.org/data/definitions/78.html) - OS Command Injection
- [CWE-22](https://cwe.mitre.org/data/definitions/22.html) - Path Traversal

## License

This security policy is part of the Covert project and is licensed under the MIT License.
