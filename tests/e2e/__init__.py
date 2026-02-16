"""End-to-end tests for Covert.

This package contains end-to-end tests that verify the complete workflow
of the Covert package updater. These tests are marked with the 'e2e' marker
and can be run with: pytest -m e2e
"""

import pytest  # noqa: F401

pytest_plugins = []


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "e2e: End-to-end tests")
