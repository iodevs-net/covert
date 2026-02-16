"""Example usage of Covert Python API.

This module demonstrates how to use Covert programmatically in Python code.
"""

from covert import Config, ProjectConfig, load_config
from covert.config import (
    TestingConfig,
    UpdatesConfig,
    BackupConfig,
    LoggingConfig,
    SecurityConfig,
)
from covert.core import run_update_session


def basic_usage():
    """Basic usage example - load config and run updates."""
    # Load configuration from file
    config = load_config("covert.yaml")

    # Run update session
    session = run_update_session(
        config=config,
        dry_run=True,  # Preview without making changes
    )

    # Print results
    print(f"Updated: {session.updated_count}")
    print(f"Rolled back: {session.rolled_back_count}")
    print(f"Success: {session.success}")

    # Access detailed results
    for result in session.results:
        print(f"  {result.package.name}: {result.status.value}")


def programmatic_config():
    """Create configuration programmatically."""
    config = Config(
        project=ProjectConfig(
            name="My Project",
            python_version="3.11",
        ),
        testing=TestingConfig(
            enabled=True,
            command="pytest",
            args=["-v", "--tb=short"],
            timeout_seconds=300,
        ),
        updates=UpdatesConfig(
            version_policy="safe",
            ignore_packages=["django", "celery"],
        ),
        backup=BackupConfig(
            enabled=True,
            location="./backups",
            retention_days=30,
        ),
        logging=LoggingConfig(
            level="INFO",
            format="detailed",
        ),
        security=SecurityConfig(
            require_virtualenv=True,
        ),
    )

    return config


def selective_updates():
    """Run selective updates using allow_only_packages."""
    config = load_config("covert.yaml")

    # Only update specific packages
    session = run_update_session(
        config=config,
        allow_only_packages=["requests", "flask"],
    )

    print(f"Updated: {session.updated_count}")


def custom_filters():
    """Run updates with custom ignore filters."""
    config = load_config("covert.yaml")

    # Ignore specific packages at runtime
    session = run_update_session(
        config=config,
        ignore_packages=["package1", "package2"],
    )


if __name__ == "__main__":
    # Basic usage
    print("=== Basic Usage ===")
    # basic_usage()

    # Programmatic config
    print("\n=== Programmatic Config ===")
    config = programmatic_config()
    print(f"Project: {config.project.name}")
    print(f"Version policy: {config.updates.version_policy}")
