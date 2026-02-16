# Contributing Guide

Thank you for your interest in contributing to Covert! This guide will help you get started with development.

## Code of Conduct

Please be respectful and professional when contributing. We follow the [Python Community Code of Conduct](https://www.python.org/community/code-of-conduct/).

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- A text editor or IDE

### Setup Development Environment

1. **Fork the repository**

   Click the "Fork" button on the [GitHub repository](https://github.com/iodevs-net/covert).

2. **Clone your fork**

   ```bash
   git clone https://github.com/YOUR_USERNAME/covert.git
   cd covert
   ```

3. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

4. **Install development dependencies**

   ```bash
   pip install -e ".[dev]"
   ```

5. **Install pre-commit hooks**

   ```bash
   pre-commit install
   ```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/my-new-feature
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes

- Follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Add type hints to new functions
- Write docstrings for new functions (Google or NumPy style)
- Keep functions focused and small

### 3. Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_core.py

# Run with coverage
pytest --cov=covert --cov-report=html
```

### 4. Run Linters

```bash
# Format code
black covert tests

# Sort imports
isort covert tests

# Check code
ruff check covert tests

# Type checking
mypy covert
```

### 5. Commit Your Changes

Follow the commit message format:

```
type(scope): short description

Longer description if needed.

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting)
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance

Example:

```
feat(config): add support for TOML configuration files

Added TOML support to the configuration loader. This allows users
to use either YAML or TOML format for their configuration files.

Closes #45
```

### 6. Push and Create PR

```bash
git push origin feature/my-new-feature
```

Then create a Pull Request on GitHub.

## Project Structure

```
covert/
├── covert/                 # Main package
│   ├── __init__.py        # Package initialization
│   ├── cli.py             # Command-line interface
│   ├── config.py          # Configuration management
│   ├── core.py            # Core update logic
│   ├── backup.py          # Backup functionality
│   ├── tester.py          # Test execution
│   ├── pip_interface.py   # Pip wrapper
│   ├── logger.py          # Logging
│   ├── exceptions.py      # Exceptions
│   └── utils.py           # Utilities
├── tests/                  # Test suite
│   ├── test_*.py          # Unit tests
│   └── conftest.py        # Test fixtures
├── docs/                   # Documentation
│   └── source/            # Sphinx source
└── examples/              # Example configurations
```

## Coding Standards

### Code Style

- Use [Black](https://github.com/psf/black) for formatting (line length: 100)
- Use [isort](https://github.com/PyCQA/isort) for import sorting
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)

### Type Hints

- Add type hints to all function signatures
- Use `Optional` for nullable types
- Use `List`, `Dict` from typing (or Python 3.9+ built-ins)

```python
def example_function(name: str, value: Optional[int] = None) -> Dict[str, Any]:
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Short description of the function.

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

- `snake_case` for functions, variables, and modules
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants

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

    def test_edge_case(self):
        """Test edge case."""
        result = function_to_test("")
        assert result == ""
```

### Test Coverage

- Aim for >90% test coverage
- Test edge cases
- Test error conditions

## Documentation Guidelines

### Docstrings

- Write clear, concise docstrings
- Include examples when helpful
- Keep docstrings in sync with code

### README

- Keep the README up to date
- Include installation instructions
- Provide usage examples

### Changelog

- Add entry for significant changes
- Follow Keep a Changelog format

## Questions?

- Open an [issue](https://github.com/iodevs-net/covert/issues) for bugs or feature requests
- Use [discussions](https://github.com/iodevs-net/covert/discussions) for questions
