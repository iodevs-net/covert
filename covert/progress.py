"""Progress bars module for Covert.

This module provides progress bar functionality using the rich library
for displaying progress during package updates and test execution.

"""

from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)
from rich.style import Style


class ProgressManager:
    """Manager for displaying progress bars and spinners.

    This class provides progress bar functionality for package updates,
    test execution, and other long-running operations.
    """

    def __init__(self, enabled: bool = True, console: Optional[Console] = None):
        """Initialize the progress manager.

        Args:
            enabled: Whether progress bars are enabled.
            console: Optional rich Console instance.
        """
        self.enabled = enabled
        self.console = console or Console()
        self._progress: Optional[Progress] = None
        self._task_ids: Dict[str, int] = {}

    def create_progress_bar(self, description: str = "Working...") -> Optional[Progress]:
        """Create a progress bar for tracking a task.

        Args:
            description: Description of the task.

        Returns:
            Optional[Progress]: Progress bar instance, or None if disabled.
        """
        if not self.enabled:
            return None

        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
        )

        return self._progress

    def start_package_updates(self, total: int) -> Optional[int]:
        """Start progress tracking for package updates.

        Args:
            total: Total number of packages to update.

        Returns:
            Optional[int]: Task ID for updating progress.
        """
        if not self.enabled:
            return None

        self._progress = self.create_progress_bar("Updating packages...")
        if self._progress:
            self._progress.start()
            self._task_ids["packages"] = self._progress.add_task(
                "Updating packages",
                total=total,
            )
            return self._task_ids["packages"]

        return None

    def update_package_progress(
        self,
        package_name: str,
        package_number: int,
        total: int,
    ) -> None:
        """Update progress for package update.

        Args:
            package_name: Name of the package being updated.
            package_number: Current package number.
            total: Total number of packages.
        """
        if not self.enabled or "packages" not in self._task_ids:
            return

        if self._progress:
            self._progress.update(
                self._task_ids["packages"],
                advance=1,
                description=f"Updating {package_name} ({package_number}/{total})",
            )

    def complete_package_updates(self) -> None:
        """Complete the package updates progress bar."""
        if self._progress:
            self._progress.stop()
            self._progress = None

    def start_test_execution(self, test_command: str) -> Optional[int]:
        """Start progress tracking for test execution.

        Args:
            test_command: The test command being run.

        Returns:
            Optional[int]: Task ID for updating progress.
        """
        if not self.enabled:
            return None

        self._progress = self.create_progress_bar(f"Running {test_command}...")
        if self._progress:
            self._progress.start()
            self._task_ids["tests"] = self._progress.add_task(
                f"Running {test_command}",
                total=None,  # Unknown duration
            )
            return self._task_ids["tests"]

        return None

    def update_test_progress(self, description: str = "Running tests...") -> None:
        """Update progress for test execution.

        Args:
            description: Current test description.
        """
        if not self.enabled or "tests" not in self._task_ids:
            return

        if self._progress:
            self._progress.update(
                self._task_ids["tests"],
                description=description,
            )

    def complete_test_execution(self) -> None:
        """Complete the test execution progress bar."""
        if self._progress:
            self._progress.stop()
            self._progress = None

    def start_vulnerability_scan(self, total: int = 0) -> Optional[int]:
        """Start progress tracking for vulnerability scanning.

        Args:
            total: Total number of packages to scan.

        Returns:
            Optional[int]: Task ID for updating progress.
        """
        if not self.enabled:
            return None

        self._progress = self.create_progress_bar("Scanning for vulnerabilities...")
        if self._progress:
            self._progress.start()
            desc = "Scanning packages"
            if total > 0:
                desc = f"Scanning {total} packages"
            self._task_ids["vuln_scan"] = self._progress.add_task(
                desc,
                total=total if total > 0 else 100,
            )
            return self._task_ids["vuln_scan"]

        return None

    def update_vuln_scan_progress(self, package_name: str, completed: int, total: int) -> None:
        """Update progress for vulnerability scanning.

        Args:
            package_name: Name of the package being scanned.
            completed: Number of packages scanned.
            total: Total number of packages.
        """
        if not self.enabled or "vuln_scan" not in self._task_ids:
            return

        if self._progress:
            self._progress.update(
                self._task_ids["vuln_scan"],
                advance=1,
                description=f"Scanning {package_name} ({completed}/{total})",
            )

    def complete_vuln_scan(self, vulnerabilities_found: int) -> None:
        """Complete the vulnerability scan progress bar.

        Args:
            vulnerabilities_found: Number of vulnerabilities found.
        """
        if self._progress:
            self._progress.stop()
            self._progress = None

        if self.enabled and vulnerabilities_found > 0:
            self.console.print(
                f"[yellow]Warning:[/yellow] Found {vulnerabilities_found} vulnerabilities!",
                style=Style(color="yellow"),
            )

    def start_backup_creation(self) -> Optional[int]:
        """Start progress tracking for backup creation.

        Returns:
            Optional[int]: Task ID for updating progress.
        """
        if not self.enabled:
            return None

        self._progress = self.create_progress_bar("Creating backup...")
        if self._progress:
            self._progress.start()
            self._task_ids["backup"] = self._progress.add_task(
                "Creating backup",
                total=100,
            )
            return self._task_ids["backup"]

        return None

    def update_backup_progress(self, description: str = "Creating backup...") -> None:
        """Update progress for backup creation.

        Args:
            description: Current backup description.
        """
        if not self.enabled or "backup" not in self._task_ids:
            return

        if self._progress:
            self._progress.update(
                self._task_ids["backup"],
                advance=10,
                description=description,
            )

    def complete_backup_creation(self, backup_file: str) -> None:
        """Complete the backup creation progress bar.

        Args:
            backup_file: Path to the backup file.
        """
        if self._progress:
            self._progress.stop()
            self._progress = None

    def print_spinner(self, message: str, spin: bool = True) -> None:
        """Print a message with optional spinner.

        Args:
            message: Message to print.
            spin: Whether to show a spinner.
        """
        if self.enabled and spin:
            with self._console_spinner(message):
                pass
        else:
            self.console.print(message)

    def _console_spinner(self, message: str):
        """Create a console spinner context.

        Args:
            message: Message to display with spinner.
        """
        return self.console.status(f"[bold blue]{message}")


def create_progress_manager(enabled: bool = True) -> ProgressManager:
    """Create a progress manager.

    Args:
        enabled: Whether progress bars are enabled.

    Returns:
        ProgressManager: Configured progress manager.
    """
    return ProgressManager(enabled=enabled)
