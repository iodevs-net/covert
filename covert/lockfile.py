"""Lock file generation module for Covert.

This module provides pip-tools-like functionality:
- Generate locked requirements.txt files
- Support for multiple input formats (requirements.in, pyproject.toml, setup.py)
- Generate hashes for security
- Diff/change reports before applying updates
"""

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from covert.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LockFileConfig:
    """Configuration for lock file generation."""

    output_file: str = "requirements.txt"
    generate_hashes: bool = False
    upgrade: bool = False
    upgrade_packages: List[str] = field(default_factory=list)
    resolver: str = "backtracking"  # or "legacy"
    dry_run: bool = False
    annotate: bool = True  # Add comments showing why each package is included


@dataclass
class PackageLock:
    """A locked package entry."""

    name: str
    version: str
    hashes: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    annotation: Optional[str] = None


@dataclass
class LockFileDiff:
    """Represents the difference between two lock files."""

    added: List[PackageLock] = field(default_factory=list)
    removed: List[PackageLock] = field(default_factory=list)
    upgraded: List[Tuple[PackageLock, PackageLock]] = field(default_factory=list)
    downgraded: List[Tuple[PackageLock, PackageLock]] = field(default_factory=list)


def parse_pyproject_dependencies(pyproject_path: Path) -> List[str]:
    """Parse dependencies from pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml

    Returns:
        List of dependency strings (e.g., ["requests>=2.25", "django>=3.2"])

    Raises:
        ValueError: If pyproject.toml is invalid.
    """
    import tomli

    try:
        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)
    except ImportError:
        # Fallback to tomllib (Python 3.11+)
        import tomllib

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

    deps = []

    # Check for project.dependencies
    if "project" in data and "dependencies" in data["project"]:
        deps.extend(data["project"]["dependencies"])

    # Check for project.optional-dependencies (extras)
    if "project" in data and "optional-dependencies" in data["project"]:
        for extra, extra_deps in data["project"]["optional-dependencies"].items():
            deps.extend([f"{dep} [{extra}]" for dep in extra_deps])

    # Check for setuptools dependencies (legacy)
    if "project" in data and "requires-python":
        deps.append(f"python>={data['project']['requires-python']}")

    # Check build-system if present
    if "build-system" in data:
        build_deps = data["build-system"].get("requires", [])
        deps.extend(build_deps)

    logger.debug(f"Parsed {len(deps)} dependencies from {pyproject_path}")
    return deps


def parse_setup_py_dependencies(setup_path: Path) -> List[str]:
    """Parse dependencies from setup.py.

    Args:
        setup_path: Path to setup.py

    Returns:
        List of dependency strings.

    Note:
        This is a basic parser. For complex setups, use setuptools directly.
    """
    deps = []

    try:
        content = setup_path.read_text()

        # Simple regex to find install_requires
        import re

        # Match install_requires=[...] or install_requires=(...)
        pattern = r"install_requires\s*=\s*\[(.*?)\]"
        matches = re.findall(pattern, content, re.DOTALL)

        for match in matches:
            # Split by comma and clean up
            for dep in match.split(","):
                dep = dep.strip().strip("'\"").strip()
                if dep:
                    deps.append(dep)

        # Also check for extras_require
        extras_pattern = r"extras_require\s*=\s*\{(.*?)\}"
        extras_matches = re.findall(extras_pattern, content, re.DOTALL)

        for match in extras_matches:
            # Extract extra name and its dependencies
            extra_pattern = r"['\"](\w+)['\"]\s*:\s*\[(.*?)\]"
            extra_deps = re.findall(extra_pattern, match)
            for extra_name, extra_dep_list in extra_deps:
                for dep in extra_dep_list.split(","):
                    dep = dep.strip().strip("'\"").strip()
                    if dep:
                        deps.append(f"{dep} [{extra_name}]")

    except Exception as e:
        logger.warning(f"Failed to parse setup.py: {e}")

    logger.debug(f"Parsed {len(deps)} dependencies from {setup_path}")
    return deps


def parse_requirements_in(requirements_path: Path) -> List[str]:
    """Parse dependencies from requirements.in.

    Args:
        requirements_path: Path to requirements.in

    Returns:
        List of dependency strings.
    """
    deps = []

    try:
        with open(requirements_path) as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith("#"):
                    deps.append(line)
    except Exception as e:
        logger.warning(f"Failed to parse requirements.in: {e}")

    logger.debug(f"Parsed {len(deps)} dependencies from {requirements_path}")
    return deps


def get_package_hashes(package_name: str, version: str) -> List[str]:
    """Get hashes for a specific package version from PyPI.

    Args:
        package_name: Name of the package.
        version: Version string.

    Returns:
        List of hash strings (sha256).
    """
    import urllib.request

    hashes = []

    try:
        # Get package info from PyPI JSON API
        url = f"https://pypi.org/pypi/{package_name}/{version}/json"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())

            # Get hashes from files
            for file_info in data.get("urls", []):
                if file_info.get("digests", {}).get("sha256"):
                    hashes.append(f"sha256:{file_info['digests']['sha256']}")

    except Exception as e:
        logger.debug(f"Could not get hashes for {package_name}=={version}: {e}")

    return hashes


def generate_requirements_line(
    package_name: str,
    version: str,
    include_hash: bool = False,
    annotation: Optional[str] = None,
) -> str:
    """Generate a requirements.txt line for a package.

    Args:
        package_name: Package name.
        version: Package version.
        include_hash: Whether to include hash.
        annotation: Comment explaining why package is included.

    Returns:
        Formatted requirements line.
    """
    line = f"{package_name}=={version}"

    # Add hash if requested
    if include_hash:
        hashes = get_package_hashes(package_name, version)
        if hashes:
            # Use hash from first file
            hash_part = hashes[0]
            line = f"{line} \\\n    --hash={hash_part}"

    # Add annotation as comment
    if annotation:
        line = f"{line}\n    # {annotation}"

    return line


def generate_lock_file(
    packages: List[Dict[str, str]],
    output_path: str,
    config: LockFileConfig,
) -> None:
    """Generate a locked requirements.txt file.

    Args:
        packages: List of package dictionaries with name, version, latest_version.
        output_path: Path to write the lock file.
        config: Lock file configuration.
    """
    lines: List[str] = []

    # Header comment
    lines.append("# Generated by Covert")
    lines.append(f"# DO NOT EDIT - manually maintained lockfiles may be overwritten")
    lines.append(f"# Use 'covert --upgrade' to update")
    lines.append("")

    for pkg in packages:
        name = pkg["name"]
        version = pkg.get("latest_version", pkg.get("version", ""))

        # Get annotation if enabled
        annotation = None
        if config.annotate:
            # Check if it's a new package or upgrade
            if pkg.get("version") != pkg.get("latest_version"):
                annotation = f"via {name} (was {pkg.get('version', 'unknown')})"

        line = generate_requirements_line(
            name,
            version,
            include_hash=config.generate_hashes,
            annotation=annotation,
        )
        lines.append(line)
        lines.append("")

    # Write to file
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines))

    logger.info(f"Generated lock file: {output_path}")


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hex-encoded SHA256 hash.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_existing_lock_file(lock_path: Path) -> Dict[str, PackageLock]:
    """Load existing lock file to compare against.

    Args:
        lock_path: Path to requirements.txt

    Returns:
        Dictionary mapping package names to PackageLock objects.
    """
    packages: Dict[str, PackageLock] = {}

    if not lock_path.exists():
        return packages

    current_package: Optional[str] = None

    try:
        with open(lock_path) as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Parse package==version
                if "==" in line:
                    # Handle multi-line with backslash
                    base = line.split("==")[0]
                    version_part = line.split("==")[1].split(";")[0].strip()
                    packages[base] = PackageLock(name=base, version=version_part)

    except Exception as e:
        logger.warning(f"Could not parse existing lock file: {e}")

    return packages


def compute_diff(
    old_packages: Dict[str, PackageLock],
    new_packages: List[Dict[str, str]],
) -> LockFileDiff:
    """Compute diff between old and new lock files.

    Args:
        old_packages: Dictionary of existing locked packages.
        new_packages: List of new package data.

    Returns:
        LockFileDiff with all changes.
    """
    diff = LockFileDiff()

    new_names = {pkg["name"] for pkg in new_packages}
    old_names = set(old_packages.keys())

    # Added packages
    for pkg in new_packages:
        if pkg["name"] not in old_names:
            diff.added.append(PackageLock(
                name=pkg["name"],
                version=pkg.get("latest_version", pkg.get("version", "")),
            ))

    # Removed packages
    for name in old_names:
        if name not in new_names:
            diff.removed.append(old_packages[name])

    # Upgraded/Downgraded
    for pkg in new_packages:
        name = pkg["name"]
        if name in old_names:
            old_pkg = old_packages[name]
            new_version = pkg.get("latest_version", pkg.get("version", ""))

            # Simple version comparison
            from packaging.version import parse as parse_version
            try:
                old_v = parse_version(old_pkg.version)
                new_v = parse_version(new_version)
                if new_v > old_v:
                    diff.upgraded.append((
                        old_pkg,
                        PackageLock(name=name, version=new_version),
                    ))
                elif new_v < old_v:
                    diff.downgraded.append((
                        old_pkg,
                        PackageLock(name=name, version=new_version),
                    ))
            except Exception:
                pass

    return diff


def format_diff_text(diff: LockFileDiff) -> str:
    """Format diff as human-readable text.

    Args:
        diff: Lock file diff.

    Returns:
        Formatted diff string.
    """
    lines: List[str] = []

    if not diff.added and not diff.removed and not diff.upgraded and not diff.downgraded:
        return "No changes detected."

    lines.append("=" * 60)
    lines.append("Lock File Diff")
    lines.append("=" * 60)
    lines.append("")

    if diff.added:
        lines.append(f"Added packages ({len(diff.added)}):")
        for pkg in diff.added:
            lines.append(f"  + {pkg.name}=={pkg.version}")
        lines.append("")

    if diff.upgraded:
        lines.append(f"Upgraded packages ({len(diff.upgraded)}):")
        for old_pkg, new_pkg in diff.upgraded:
            lines.append(f"  ^ {old_pkg.name}: {old_pkg.version} -> {new_pkg.version}")
        lines.append("")

    if diff.downgraded:
        lines.append(f"Downgraded packages ({len(diff.downgraded)}):")
        for old_pkg, new_pkg in diff.downgraded:
            lines.append(f"  v {old_pkg.name}: {old_pkg.version} -> {new_pkg.version}")
        lines.append("")

    if diff.removed:
        lines.append(f"Removed packages ({len(diff.removed)}):")
        for pkg in diff.removed:
            lines.append(f"  - {pkg.name}=={pkg.version}")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


def find_input_files() -> Dict[str, Path]:
    """Find available input files in current directory.

    Returns:
        Dictionary mapping input type to file path.
    """
    inputs: Dict[str, Path] = {}
    cwd = Path.cwd()

    # Check for pyproject.toml
    pyproject = cwd / "pyproject.toml"
    if pyproject.exists():
        inputs["pyproject"] = pyproject

    # Check for setup.py
    setup_py = cwd / "setup.py"
    if setup_py.exists():
        inputs["setup.py"] = setup_py

    # Check for requirements.in
    req_in = cwd / "requirements.in"
    if req_in.exists():
        inputs["requirements.in"] = req_in

    return inputs


@dataclass
class SyncConfig:
    """Configuration for pip-sync style operations."""

    requirements_files: List[str] = field(default_factory=list)
    constraints_file: Optional[str] = None
    dry_run: bool = False
    force: bool = False  # Force installation even if already satisfied
    dont_upgrade: List[str] = field(default_factory=list)  # Packages to never upgrade
    dont_sync: List[str] = field(default_factory=list)  # Packages to never sync
    pip_args: str = ""  # Additional pip arguments


@dataclass
class SyncAction:
    """Represents a sync action to be performed."""

    action_type: str  # "install", "upgrade", "uninstall"
    package_name: str
    old_version: Optional[str] = None
    new_version: Optional[str] = None


def get_installed_packages() -> Dict[str, str]:
    """Get currently installed packages.

    Returns:
        Dictionary mapping package names to versions.
    """
    import subprocess

    installed: Dict[str, str] = {}

    try:
        result = subprocess.run(
            ["pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            shell=False,
            timeout=30,
        )

        if result.returncode == 0:
            import json

            packages = json.loads(result.stdout)
            for pkg in packages:
                # Normalize name (lowercase, replace underscores with hyphens)
                name = pkg["name"].lower().replace("_", "-")
                installed[name] = pkg["version"]

    except Exception as e:
        logger.warning(f"Could not get installed packages: {e}")

    return installed


def parse_requirements_file(req_path: Path) -> Dict[str, str]:
    """Parse a requirements.txt file.

    Args:
        req_path: Path to requirements.txt

    Returns:
        Dictionary mapping package names to versions.
    """
    packages: Dict[str, str] = {}

    try:
        with open(req_path) as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Skip flags like --hash=sha256:...
                if line.startswith("--"):
                    continue

                # Parse package==version
                if "==" in line:
                    # Handle extras like package[extra]==version
                    name = line.split("==")[0].split("[")[0]
                    version = line.split("==")[1].split(";")[0].strip()

                    # Normalize name
                    name = name.lower().replace("_", "-")

                    packages[name] = version

    except Exception as e:
        logger.warning(f"Could not parse requirements file: {e}")

    return packages


def compute_sync_actions(
    required: Dict[str, str],
    installed: Dict[str, str],
    config: SyncConfig,
) -> List[SyncAction]:
    """Compute actions needed to sync environment.

    Args:
        required: Required packages from lock file.
        installed: Currently installed packages.
        config: Sync configuration.

    Returns:
        List of actions to perform.
    """
    actions: List[SyncAction] = []

    required_names = set(required.keys())
    installed_names = set(installed.keys())

    # Packages to install (in required but not installed)
    for name in required_names - installed_names:
        if name not in config.dont_sync:
            actions.append(SyncAction(
                action_type="install",
                package_name=name,
                new_version=required[name],
            ))

    # Packages to uninstall (installed but not in required)
    for name in installed_names - required_names:
        # Never uninstall pip, setuptools, wheel, or packages in dont_sync
        if name not in ["pip", "setuptools", "wheel"] and name not in config.dont_sync:
            actions.append(SyncAction(
                action_type="uninstall",
                package_name=name,
                old_version=installed[name],
            ))

    # Packages to upgrade/downgrade
    for name in required_names & installed_names:
        if name in config.dont_upgrade or name in config.dont_sync:
            continue

        required_version = required[name]
        installed_version = installed[name]

        if required_version != installed_version:
            actions.append(SyncAction(
                action_type="upgrade",
                package_name=name,
                old_version=installed_version,
                new_version=required_version,
            ))

    return actions


def format_sync_actions(actions: List[SyncAction]) -> str:
    """Format sync actions as human-readable text.

    Args:
        actions: List of sync actions.

    Returns:
        Formatted string.
    """
    if not actions:
        return "Environment is already in sync."

    lines = ["Sync Actions:", "=" * 40]

    install_actions = [a for a in actions if a.action_type == "install"]
    upgrade_actions = [a for a in actions if a.action_type == "upgrade"]
    uninstall_actions = [a for a in actions if a.action_type == "uninstall"]

    if install_actions:
        lines.append(f"\nInstall ({len(install_actions)}):")
        for action in install_actions:
            lines.append(f"  + {action.package_name}=={action.new_version}")

    if upgrade_actions:
        lines.append(f"\nUpgrade ({len(upgrade_actions)}):")
        for action in upgrade_actions:
            lines.append(f"  ^ {action.package_name}: {action.old_version} -> {action.new_version}")

    if uninstall_actions:
        lines.append(f"\nUninstall ({len(uninstall_actions)}):")
        for action in uninstall_actions:
            lines.append(f"  - {action.package_name}=={action.old_version}")

    return "\n".join(lines)


def sync_environment(
    requirements_files: List[str],
    config: Optional[SyncConfig] = None,
) -> bool:
    """Sync environment to match requirements files (pip-sync style).

    Args:
        requirements_files: List of requirements.txt files to sync.
        config: Sync configuration.

    Returns:
        True if sync was successful.
    """
    if config is None:
        config = SyncConfig(requirements_files=requirements_files)

    logger.info(f"Syncing environment with {len(requirements_files)} requirements file(s)")

    # Parse all requirements files
    required: Dict[str, str] = {}
    for req_file in requirements_files:
        req_path = Path(req_file)
        if not req_path.exists():
            logger.warning(f"Requirements file not found: {req_file}")
            continue

        packages = parse_requirements_file(req_path)
        required.update(packages)
        logger.debug(f"Loaded {len(packages)} packages from {req_file}")

    if not required:
        logger.error("No packages to sync")
        return False

    # Get currently installed packages
    installed = get_installed_packages()
    logger.debug(f"Found {len(installed)} installed packages")

    # Compute actions
    actions = compute_sync_actions(required, installed, config)

    if not actions:
        logger.info("Environment is already in sync with requirements")
        return True

    # Show what will happen
    logger.info(format_sync_actions(actions))

    if config.dry_run:
        logger.info("Dry-run mode - no changes will be made")
        return True

    # Perform actions
    from covert.pip_interface import install_package, uninstall_package

    success = True

    # First uninstall (to handle version conflicts)
    for action in actions:
        if action.action_type == "uninstall":
            try:
                logger.info(f"Uninstalling {action.package_name}")
                uninstall_package(action.package_name)
            except Exception as e:
                logger.error(f"Failed to uninstall {action.package_name}: {e}")
                success = False

    # Then install/upgrade
    for action in actions:
        if action.action_type in ["install", "upgrade"]:
            try:
                logger.info(f"Installing {action.package_name}=={action.new_version}")
                install_package(action.package_name, version=action.new_version)
            except Exception as e:
                logger.error(f"Failed to install {action.package_name}: {e}")
                success = False

    if success:
        logger.info("Environment synced successfully")
    else:
        logger.error("Environment sync completed with errors")

    return success
