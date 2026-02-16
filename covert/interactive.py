"""Interactive mode module for Covert.

This module provides interactive package selection and confirmation prompts
for guided updates.

"""

import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional


@dataclass
class InteractiveConfig:
    """Configuration for interactive mode.

    Attributes:
        enabled: Whether interactive mode is enabled.
        confirm_each: Confirm before each package update.
        show_diffs: Show version diffs before updating.
        allow_skip: Allow skipping packages during update.
    """

    enabled: bool = False
    confirm_each: bool = True
    show_diffs: bool = True
    allow_skip: bool = True


class InteractivePrompter:
    """Interactive prompter for guided package updates.

    This class handles user interaction for package updates, including
    confirmation prompts and package selection.
    """

    def __init__(self, config: InteractiveConfig, input_func: Optional[Callable[[str], str]] = None):
        """Initialize the interactive prompter.

        Args:
            config: Interactive mode configuration.
            input_func: Optional function for getting user input (for testing).
        """
        self.config = config
        self._input_func = input_func or input
        self._selected_packages: List[str] = []
        self._skipped_packages: List[str] = []

    def prompt_for_packages(
        self, packages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Prompt user to select packages to update.

        Args:
            packages: List of packages with available updates.

        Returns:
            List[Dict[str, str]]: Packages selected by user.
        """
        if not self.config.enabled:
            return packages

        self._print_banner("Package Selection")
        print(f"\nFound {len(packages)} package(s) with updates:\n")

        for i, pkg in enumerate(packages, 1):
            name = pkg.get("name", "unknown")
            current = pkg.get("version", "unknown")
            latest = pkg.get("latest_version", "unknown")
            print(f"  {i}. {name}: {current} → {latest}")

        print("\n" + "-" * 50)
        print("Options:")
        print("  [A]ll - Update all packages")
        print("  [N]one - Skip all updates")
        print("  [1,2,3] - Select specific packages (comma-separated)")
        print("  [Enter] - Update all (default)")
        print("-" * 50 + "\n")

        while True:
            try:
                response = self._input_func("Select packages to update: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n\nExiting interactive mode...")
                sys.exit(0)

            if not response or response == "a" or response == "all":
                self._selected_packages = [p.get("name", "") for p in packages]
                return packages

            if response == "n" or response == "none":
                print("No packages will be updated.")
                return []

            # Try to parse as package numbers
            try:
                indices = []
                for part in response.split(","):
                    part = part.strip()
                    if part.isdigit():
                        idx = int(part) - 1
                        if 0 <= idx < len(packages):
                            indices.append(idx)

                if indices:
                    selected = [packages[i] for i in indices]
                    self._selected_packages = [p.get("name", "") for p in selected]
                    return selected

                print("Invalid selection. Please try again.")
            except (ValueError, IndexError):
                print("Invalid selection. Please try again.")

    def confirm_update(
        self, package: Dict[str, str]
    ) -> bool:
        """Prompt user to confirm a package update.

        Args:
            package: Package information.

        Returns:
            bool: True if user confirms the update.
        """
        if not self.config.enabled or not self.config.confirm_each:
            return True

        name = package.get("name", "unknown")
        current = package.get("version", "unknown")
        latest = package.get("latest_version", "unknown")

        print("\n" + "=" * 50)
        print(f"Package: {name}")
        print(f"  Current: {current}")
        print(f"  Latest:  {latest}")
        print("=" * 50 + "\n")

        while True:
            try:
                response = self._input_func(
                    f"Update {name} to {latest}? [Y]es/[N]o/[S]kip all: "
                ).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n\nExiting interactive mode...")
                sys.exit(0)

            if response in ("y", "yes"):
                return True
            if response in ("n", "no"):
                return False
            if response == "s" and self.config.allow_skip:
                self._skipped_packages.append(name)
                return False

            print("Please enter Y, N, or S (if skipping all).")

    def prompt_continue_after_failure(
        self,
        package: Dict[str, str],
        error: str,
    ) -> bool:
        """Prompt user to continue after a package update failure.

        Args:
            package: Package that failed to update.
            error: Error message.

        Returns:
            bool: True if user wants to continue with remaining packages.
        """
        if not self.config.enabled:
            return False

        name = package.get("name", "unknown")

        print("\n" + "!" * 50)
        print(f"Update failed for {name}")
        print(f"Error: {error}")
        print("!" * 50 + "\n")

        while True:
            try:
                response = self._input_func(
                    "Continue with remaining packages? [Y]es/[N]o: "
                ).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n\nExiting interactive mode...")
                sys.exit(0)

            if response in ("y", "yes"):
                return True
            if response in ("n", "no"):
                return False

            print("Please enter Y or N.")

    def prompt_continue_after_rollback(
        self,
        package: Dict[str, str],
    ) -> bool:
        """Prompt user to continue after a package rollback.

        Args:
            package: Package that was rolled back.

        Returns:
            bool: True if user wants to continue with remaining packages.
        """
        if not self.config.enabled:
            return True

        name = package.get("name", "unknown")

        print("\n" + "!" * 50)
        print(f"Tests failed for {name} - rolled back to previous version")
        print("!" * 50 + "\n")

        while True:
            try:
                response = self._input_func(
                    "Continue with remaining packages? [Y]es/[N]o: "
                ).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n\nExiting interactive mode...")
                sys.exit(0)

            if response in ("y", "yes"):
                return True
            if response in ("n", "no"):
                return False

            print("Please enter Y or N.")

    def summary(self) -> Dict[str, List[str]]:
        """Get summary of interactive selections.

        Returns:
            Dict with 'selected' and 'skipped' package lists.
        """
        return {
            "selected": self._selected_packages,
            "skipped": self._skipped_packages,
        }

    def _print_banner(self, title: str) -> None:
        """Print a formatted banner.

        Args:
            title: Banner title.
        """
        width = 60
        print("\n" + "=" * width)
        print(f"  {title}".center(width))
        print("=" * width)


def create_interactive_config(
    enabled: bool = False,
    confirm_each: bool = True,
    show_diffs: bool = True,
    allow_skip: bool = True,
) -> InteractiveConfig:
    """Create an interactive configuration.

    Args:
        enabled: Whether interactive mode is enabled.
        confirm_each: Confirm before each update.
        show_diffs: Show version diffs.
        allow_skip: Allow skipping packages.

    Returns:
        InteractiveConfig: Configured interactive settings.
    """
    return InteractiveConfig(
        enabled=enabled,
        confirm_each=confirm_each,
        show_diffs=show_diffs,
        allow_skip=allow_skip,
    )
