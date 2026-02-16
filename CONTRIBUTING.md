# Contributing to Covert

Thank you for your interest in contributing to Covert! This document provides guidelines for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Commit Messages](#commit-messages)
- [Pull Requests](#pull-requests)
- [Questions](#questions)

## Code of Conduct

Please be respectful and professional when contributing to this project. We follow the [Python Community Code of Conduct](https://www.python.org/community/code-of-conduct/).

## Getting Started

1. **Fork the repository** - Click the "Fork" button on [GitHub](https://github.com/iodevs-net/covert)
2. **Clone your fork** - `git clone https://github.com/YOUR_USERNAME/covert.git`
3. **Explore the codebase** - Read the [README](README.md) and [documentation](docs/)

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- pip

### Setup Steps

1. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

2. **Install development dependencies**

   ```bash
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks**

   ```bash
   pre-commit install
   ```

4. **Verify installation**

   ```bash
   pytest --version
   covert --version
   ```

## Making Changes

1. **Create a branch**

   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

2. **Make your changes**

   - Follow the coding standards
   - Write tests for new functionality
   - Update documentation

3. **Run tests**

   ```bash
   pytest
   ```

4. **Run linters**

   ```bash
   black covert tests
   isort covert tests
   ruff check covert tests
   mypy covert
   ```

5. **Commit your changes**

   See [Commit Messages](#commit-messages) for guidelines.

6. **Push and create PR**

   ```bash
   git push origin feature/your-feature-name
   ```

## Coding Standards

### Code Style

- Use [Black](https://github.com/psf/black) for code formatting (line length: 100)
- Use [isort](https://github.com/PyCQA/isort) for import sorting
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)

### Type Hints

Add type hints to all function signatures:

```python
def example(name: str, value: Optional[int] = None) -> Dict[str, Any]:
    """Example function with type hints."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Short description.

    Longer description if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: Description of when this is raised.
    """
```

### Naming Conventions

| Type | Convention |
|------|------------|
| Functions/Variables | `snake_case` |
| Classes | `PascalCase` |
| Constants | `UPPER_SNAKE_CASE` |
| Modules | `snake_case` |

## Testing Guidelines

### Test Structure

```python
import pytest
from covert.module import function_to_test

class TestFunctionName:
    """Tests for function_name."""

    def test_basic_case(self):
        """Test basic functionality."""
        result = function_to_test("input")
        assert result == "expected"

    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            function_to_test("invalid")
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_core.py

# Run tests with coverage
pytest --cov=covert --cov-report=html
```

### Test Coverage

- Aim for >90% test coverage
- Test edge cases and error conditions
- Include integration tests for core workflows

## Documentation

### Code Documentation

- Write docstrings for all public functions and classes
- Keep docstrings in sync with code
- Include usage examples in docstrings when helpful

### Project Documentation

- Keep the README up to date
- Update configuration documentation when adding options
- Add migration guides for breaking changes

## Commit Messages

Use clear, descriptive commit messages:

```
type(scope): short description

Longer description if needed.

Fixes #123
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance

### Examples

```
feat(config): add TOML configuration support

Added support for TOML configuration files, allowing users
to choose between YAML and TOML formats.

Closes #45
```

```
fix(backup): handle missing backup directory

Create backup directory if it doesn't exist before
attempting to write backup file.

Fixes #78
```

## Pull Requests

### Before Submitting

1. Run all tests and linters
2. Update documentation if needed
3. Add tests for new functionality
4. Ensure commit history is clean

### PR Description

Include in your PR description:

- **Summary**: What does this PR do?
- **Changes**: What files were changed?
- **Testing**: How was it tested?
- **Related Issues**: Link any related issues

### Review Process

1. A maintainer will review your PR
2. Address any feedback
3. Once approved, the PR will be merged

## Questions?

- **Bugs**: Open an [issue](https://github.com/iodevs-net/covert/issues)
- **Feature Requests**: Open an [issue](https://github.com/iodevs-net/covert/issues)
- **General Questions**: Start a [discussion](https://github.com/iodevs-net/covert/discussions)

## Recognition

Contributors will be recognized in the README and release notes.

---

Thank you for contributing to Covert!
