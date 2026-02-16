"""Command-line interface for Covert.

This module provides the CLI for Covert, a safe package updater for Python/Django
projects. It handles argument parsing, configuration loading, logging setup, and
orchestrates the update process.
"""

import argparse
import sys
from typing import List, Optional

from covert import __version__
from covert.config import Config, load_config
from covert.core import run_update_session
from covert.exceptions import ConfigError, CovertError, SecurityError
from covert.logger import get_logger, setup_logging
from covert.utils import check_elevated_privileges, is_in_virtualenv, sanitize_package_name

logger = get_logger(__name__)


# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_VIRTUAL_ENV_REQUIRED = 3
EXIT_PRIVILEGE_ESCALATION = 4


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: List of command-line arguments. If None, uses sys.argv[1:].

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog="covert",
        description="Safe package updater for Python/Django projects",
        epilog=(
            "Covert provides automated, safe dependency updates with automatic "
            "rollback on test failures. For more information, visit "
            "https://github.com/iodevs-net/covert"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Configuration options
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "--config",
        "-c",
        type=str,
        metavar="PATH",
        help="Path to configuration file (YAML or TOML format)",
    )
    config_group.add_argument(
        "--ignore",
        type=str,
        metavar="PACKAGES",
        help="Comma-separated list of packages to ignore during updates",
    )

    # Operation modes
    mode_group = parser.add_argument_group("Operation modes")
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate updates without installing any packages",
    )
    mode_group.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup before updates",
    )
    mode_group.add_argument(
        "--no-tests",
        action="store_true",
        help="Skip running tests before and after updates",
    )

    # Parallel updates (optional feature)
    mode_group.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel package updates (experimental)",
    )

    # Output options
    output_group = parser.add_argument_group("Output options")
    output_group.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase verbosity level (can be used multiple times: -v, -vv)",
    )

    # Information options
    info_group = parser.add_argument_group("Information")
    info_group.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit",
    )

    # Advanced features
    advanced_group = parser.add_argument_group("Advanced features")
    advanced_group.add_argument(
        "--scan-vulnerabilities",
        action="store_true",
        help="Scan for package vulnerabilities using pip-audit and safety",
    )
    advanced_group.add_argument(
        "--notify",
        type=str,
        metavar="CHANNEL",
        help="Send notifications via specified channel (slack, email, webhook)",
    )
    advanced_group.add_argument(
        "--report-format",
        type=str,
        choices=["json", "html", "markdown"],
        default="json",
        metavar="FORMAT",
        help="Report output format (json, html, markdown)",
    )
    advanced_group.add_argument(
        "--report-output",
        type=str,
        metavar="PATH",
        help="Path to save report file",
    )
    advanced_group.add_argument(
        "--interactive",
        action="store_true",
        help="Enable interactive mode with confirmation prompts",
    )
    advanced_group.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bars",
    )

    return parser.parse_args(args)


def load_configuration(
    config_path: Optional[str] = None,
) -> Optional[Config]:
    """Load configuration from file.

    Args:
        config_path: Path to configuration file. If None, returns default config.

    Returns:
        Optional[Config]: Loaded configuration or None if no path provided.

    Raises:
        ConfigError: If configuration file cannot be loaded or is invalid.
    """
    if config_path is None:
        return None

    try:
        config = load_config(config_path)
        logger.info(f"Loaded configuration from: {config_path}")
        return config
    except ConfigError as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


def setup_cli_logging(
    config: Optional[Config] = None,
    verbose_level: int = 0,
) -> None:
    """Set up logging for CLI based on configuration and verbosity.

    Args:
        config: Configuration object with logging settings.
        verbose_level: Verbosity level from command line (0, 1, or 2).
    """
    if config:
        setup_logging(config.logging, verbose_level=verbose_level)
    else:
        # Use default logging configuration if no config file
        from covert.config import LoggingConfig

        default_logging = LoggingConfig(
            level="INFO" if verbose_level == 0 else "DEBUG",
            format="detailed",
            file="covert.log",
            console=True,
        )
        setup_logging(default_logging, verbose_level=verbose_level)


def parse_ignore_list(ignore_arg: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated ignore list argument.

    Args:
        ignore_arg: Comma-separated string of package names.

    Returns:
        Optional[List[str]]: List of package names, or None if not provided.

    Raises:
        ValidationError: If any package name is invalid.
    """
    if ignore_arg is None:
        return None

    packages = [pkg.strip() for pkg in ignore_arg.split(",")]
    # Validate and sanitize each package name
    validated_packages = []
    for pkg in packages:
        if pkg:
            try:
                validated_packages.append(sanitize_package_name(pkg))
            except Exception:
                # Log warning but continue - invalid names will be filtered later
                logger.warning(f"Skipping invalid package name in ignore list: {pkg}")
    return validated_packages


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the Covert CLI.

    This function:
    1. Parses command-line arguments
    2. Loads configuration from file if provided
    3. Performs security checks (virtual environment, privileges)
    4. Sets up logging based on config and verbosity
    5. Runs the update session
    6. Returns appropriate exit code

    Args:
        args: List of command-line arguments. If None, uses sys.argv[1:].

    Returns:
        int: Exit code (0 for success, non-zero for error).
    """
    parsed_args = parse_args(args)

    # Handle --version flag
    if parsed_args.version:
        print(f"Covert {__version__}")
        return EXIT_SUCCESS

    # Load configuration
    config = None
    try:
        config = load_configuration(parsed_args.config)
    except ConfigError:
        return EXIT_ERROR

    # Use default configuration if none loaded
    if config is None:
        from covert.config import Config, ProjectConfig

        config = Config(project=ProjectConfig(name="Covert", python_version="3.8"))

    # Set up logging before security checks
    setup_cli_logging(config, parsed_args.verbose)

    # Security check: Virtual environment
    if config.security.require_virtualenv and not is_in_virtualenv():
        logger.error(
            "Covert requires a virtual environment for safety. "
            "Please activate a virtual environment before running Covert."
        )
        return EXIT_VIRTUAL_ENV_REQUIRED

    # Security check: Elevated privileges
    if check_elevated_privileges():
        logger.error(
            "Covert should not be run with elevated privileges (root/administrator). "
            "This is a security risk and can damage your Python environment."
        )
        return EXIT_PRIVILEGE_ESCALATION

    # Override configuration with CLI arguments
    if parsed_args.dry_run:
        logger.info("Dry-run mode enabled - no changes will be made")

    if parsed_args.no_backup:
        logger.info("Backup creation disabled")

    if parsed_args.no_tests:
        logger.info("Testing disabled")

    if parsed_args.parallel:
        logger.info("Parallel updates enabled (experimental)")

    # Handle progress bar flag
    if parsed_args.no_progress:
        logger.info("Progress bars disabled")
        config.progress.enabled = False

    # Handle interactive mode
    if parsed_args.interactive:
        logger.info("Interactive mode enabled")
        config.interactive.enabled = True

    # Handle vulnerability scanning
    scan_vulnerabilities = parsed_args.scan_vulnerabilities
    if scan_vulnerabilities:
        logger.info("Vulnerability scanning enabled")

    # Handle report generation
    report_enabled = parsed_args.report_output is not None
    if report_enabled:
        logger.info(f"Report generation enabled: {parsed_args.report_output}")
        config.reports.enabled = True
        config.reports.output_path = parsed_args.report_output
        if parsed_args.report_format:
            config.reports.format = parsed_args.report_format

    # Handle notifications
    notify_channel = parsed_args.notify
    if notify_channel:
        logger.info(f"Notifications enabled via {notify_channel}")
        config.notifications.enabled = True
        if notify_channel not in config.notifications.channels:
            config.notifications.channels.append(notify_channel)

    # Parse ignore list
    ignore_packages = parse_ignore_list(parsed_args.ignore)
    if ignore_packages:
        logger.info(f"Ignoring packages: {', '.join(ignore_packages)}")

    # Run update session
    try:
        session = run_update_session(
            config=config,
            dry_run=parsed_args.dry_run,
            no_backup=parsed_args.no_backup,
            no_tests=parsed_args.no_tests,
            ignore_packages=ignore_packages,
            parallel=parsed_args.parallel,
        )

        # Run vulnerability scanning if requested
        vulnerabilities_found = 0
        if scan_vulnerabilities and not parsed_args.dry_run:
            from covert.vuln_scanner import scan_vulnerabilities

            logger.info("Running vulnerability scan...")
            vuln_result = scan_vulnerabilities()
            vulnerabilities_found = vuln_result.vulnerable_count
            if vuln_result.has_vulnerabilities:
                logger.warning(
                    f"Found {vulnerabilities_found} vulnerabilities in packages:"
                )
                for vuln in vuln_result.vulnerabilities:
                    logger.warning(
                        f"  - {vuln.package_name} ({vuln.installed_version}): "
                        f"{', '.join(vuln.vulnerabilities)}"
                    )
            else:
                logger.info("No vulnerabilities found in packages")

        # Generate report if requested
        if report_enabled and session:
            from covert.reports import ReportData, ReportGenerator

            report_data = ReportData(
                session_name=config.project.name,
                start_time=session.start_time,
                end_time=session.end_time,
                duration=(session.end_time - session.start_time).total_seconds()
                if session.end_time
                else 0.0,
                total_packages=len(session.results),
                updated_packages=session.updated_count,
                rolled_back_packages=session.rolled_back_count,
                failed_packages=session.summary.get("failed_install", 0),
                skipped_packages=session.summary.get("skipped", 0),
                vulnerabilities_found=vulnerabilities_found,
                pre_test_passed=session.pre_test_passed,
                backup_file=session.backup_file,
                package_results=[
                    {
                        "name": r.package.name,
                        "current_version": r.package.current_version,
                        "latest_version": r.package.latest_version,
                        "status": r.status.value,
                        "error": r.error_message,
                    }
                    for r in session.results
                ],
            )

            generator = ReportGenerator(config.reports)
            report_path = generator.generate_and_save(report_data)
            if report_path:
                logger.info(f"Report saved to: {report_path}")

        # Send notifications if requested
        if notify_channel and session:
            from covert.notifications import NotificationManager

            duration = (session.end_time - session.start_time).total_seconds() if session.end_time else 0.0

            notifier = NotificationManager(config.notifications)
            notifier.send_update_summary(
                session_name=config.project.name,
                updated=session.updated_count,
                rolled_back=session.rolled_back_count,
                failed=session.summary.get("failed_install", 0),
                skipped=session.summary.get("skipped", 0),
                duration=duration,
                vulnerabilities=vulnerabilities_found,
            )

        # Determine exit code based on session results
        if session.success:
            return EXIT_SUCCESS
        else:
            logger.warning("Update session completed with some failures")
            return EXIT_ERROR

    except KeyboardInterrupt:
        logger.info("Update session interrupted by user")
        return 130  # Standard exit code for SIGINT

    except SecurityError as e:
        logger.error(f"Security error: {e}")
        return EXIT_ERROR

    except CovertError as e:
        logger.error(f"Update session failed: {e}")
        return EXIT_ERROR

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
