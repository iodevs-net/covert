"""Backup management module for Covert.

This module provides functionality for creating, restoring, and managing
backups of package requirements before and after updates.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from covert.config import BackupConfig
from covert.exceptions import BackupError, PipError, ValidationError
from covert.logger import get_logger
from covert.pip_interface import freeze_requirements, install_package
from covert.utils import validate_backup_path

logger = get_logger(__name__)


def create_backup(
    config: BackupConfig,
    custom_path: Optional[Union[str, Path]] = None,
) -> str:
    """Create a backup of current package requirements.

    Args:
        config: Backup configuration.
        custom_path: Optional custom path for the backup file.

    Returns:
        str: Path to the created backup file.

    Raises:
        BackupError: If backup creation fails.
    """
    if not config.enabled:
        logger.info("Backup is disabled, skipping backup creation")
        return ""

    # Determine backup location
    if custom_path:
        try:
            backup_path = validate_backup_path(custom_path)
        except ValidationError as e:
            logger.error(f"Invalid backup path: {e}")
            raise BackupError(f"Invalid backup path: {e}") from e
    else:
        try:
            backup_dir = validate_backup_path(config.location)
        except ValidationError as e:
            logger.error(f"Invalid backup directory: {e}")
            raise BackupError(f"Invalid backup directory: {e}") from e
        
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create backup directory: {e}")
            raise BackupError("Failed to create backup directory") from e

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"backup_{timestamp}.{config.format}"

    logger.info(f"Creating backup at: {backup_path}")

    try:
        # Get requirements using pip freeze
        if config.format == "json":
            requirements = freeze_requirements(format_type="json")
            content = json.dumps(requirements, indent=2)
        else:
            content = str(freeze_requirements(format_type="txt"))

        # Write backup file
        backup_path.write_text(content)
        logger.info(f"Backup created successfully: {backup_path}")

        return str(backup_path)
    except PipError as e:
        logger.error(f"Failed to get requirements for backup: {e}")
        raise BackupError("Failed to get requirements for backup") from e
    except OSError as e:
        logger.error(f"Failed to write backup file: {e}")
        raise BackupError("Failed to write backup file") from e


def restore_backup(
    backup_path: Union[str, Path],
    dry_run: bool = False,
) -> List[Dict[str, str]]:
    """Restore packages from a backup file.

    Args:
        backup_path: Path to the backup file.
        dry_run: If True, only print what would be restored.

    Returns:
        List[Dict[str, str]]: List of restored packages.

    Raises:
        BackupError: If backup restoration fails.
        PipError: If package installation fails.
    """
    backup_path = Path(backup_path)

    if not backup_path.exists():
        logger.error(f"Backup file not found: {backup_path}")
        raise BackupError("Backup file not found")

    logger.info(f"Restoring from backup: {backup_path}")

    try:
        # Read backup file
        content = backup_path.read_text()

        # Parse backup content
        if backup_path.suffix == ".json":
            packages = json.loads(content)
        else:
            # Parse requirements.txt format
            packages = []
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    if "==" in line:
                        name, version = line.split("==", 1)
                        packages.append({"name": name, "version": version})
                    else:
                        # Package without version
                        packages.append({"name": line, "version": None})

        logger.info(f"Found {len(packages)} package(s) in backup")

        if dry_run:
            logger.info("Dry run: would restore the following packages:")
            for pkg in packages:
                logger.info(
                    f"  - {pkg['name']}" + (f"=={pkg['version']}" if pkg["version"] else "")
                )
            return packages  # type: ignore[no-any-return]

        # Restore packages
        restored = []
        for pkg in packages:
            name = pkg["name"]
            version = pkg["version"]

            try:
                if version:
                    install_package(name, version=version)
                else:
                    install_package(name)
                restored.append(pkg)
                logger.info(f"Restored: {name}" + (f"=={version}" if version else ""))
            except PipError as e:
                logger.warning(f"Failed to restore {name}: {e}")
                # Continue with other packages

        logger.info(f"Restored {len(restored)} package(s)")
        return restored

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse backup file: {e}")
        raise BackupError("Failed to parse backup file") from e
    except OSError as e:
        logger.error(f"Failed to read backup file: {e}")
        raise BackupError("Failed to read backup file") from e


def cleanup_old_backups(
    config: BackupConfig,
    keep_count: Optional[int] = None,
) -> List[Path]:
    """Clean up old backup files based on retention policy.

    Args:
        config: Backup configuration.
        keep_count: Number of backups to keep. If None, uses retention_days.

    Returns:
        List[Path]: List of deleted backup files.

    Raises:
        BackupError: If cleanup fails.
    """
    if not config.enabled:
        logger.info("Backup is disabled, skipping cleanup")
        return []

    backup_dir = Path(config.location)

    if not backup_dir.exists():
        logger.info(f"Backup directory does not exist: {backup_dir}")
        return []

    logger.info(f"Cleaning up old backups in: {backup_dir}")

    try:
        # Get all backup files
        backup_files: List[Path] = []
        for pattern in ("backup_*.txt", "backup_*.json"):
            backup_files.extend(backup_dir.glob(pattern))

        if not backup_files:
            logger.info("No backup files found")
            return []

        # Sort by modification time (newest first)
        backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Determine which files to delete
        files_to_delete = []

        if keep_count is not None:
            # Keep N most recent backups
            files_to_delete = backup_files[keep_count:]
        else:
            # Delete files older than retention_days
            cutoff_time = datetime.now().timestamp() - (config.retention_days * 24 * 60 * 60)
            files_to_delete = [f for f in backup_files if f.stat().st_mtime < cutoff_time]

        # Delete old backups
        deleted = []
        for backup_file in files_to_delete:
            try:
                backup_file.unlink()
                deleted.append(backup_file)
                logger.info(f"Deleted old backup: {backup_file}")
            except OSError as e:
                logger.warning(f"Failed to delete {backup_file}: {e}")

        logger.info(f"Cleaned up {len(deleted)} old backup file(s)")
        return deleted

    except OSError as e:
        logger.error(f"Failed to clean up backups: {e}")
        raise BackupError("Failed to clean up backups") from e


def list_backups(
    config: BackupConfig,
) -> List[Dict[str, Union[str, float]]]:
    """List all backup files in the backup directory.

    Args:
        config: Backup configuration.

    Returns:
        List[Dict[str, Union[str, float]]]: List of backup files with metadata.

    Raises:
        BackupError: If listing fails.
    """
    backup_dir = Path(config.location)

    if not backup_dir.exists():
        return []

    try:
        backups = []
        for pattern in ("backup_*.txt", "backup_*.json"):
            for backup_file in backup_dir.glob(pattern):
                stat = backup_file.stat()
                backups.append(
                    {
                        "path": str(backup_file),
                        "name": backup_file.name,
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "format": backup_file.suffix[1:],  # Remove dot
                    }
                )

        # Sort by modification time (newest first)
        backups.sort(key=lambda b: b["modified"], reverse=True)  # type: ignore[arg-type, return-value]

        return backups  # type: ignore[return-value]

    except OSError as e:
        logger.error(f"Failed to list backups: {e}")
        raise BackupError("Failed to list backups") from e


def get_latest_backup(config: BackupConfig) -> Optional[Path]:
    """Get the most recent backup file.

    Args:
        config: Backup configuration.

    Returns:
        Optional[Path]: Path to the latest backup, or None if no backups exist.

    Raises:
        BackupError: If listing fails.
    """
    backups = list_backups(config)

    if backups:
        return Path(str(backups[0]["path"]))
    return None


def validate_backup_file(backup_path: Union[str, Path]) -> bool:
    """Validate a backup file.

    Args:
        backup_path: Path to the backup file.

    Returns:
        bool: True if backup file is valid, False otherwise.
    """
    backup_path = Path(backup_path)

    if not backup_path.exists():
        return False

    if backup_path.suffix not in (".txt", ".json"):
        return False

    try:
        content = backup_path.read_text()

        if backup_path.suffix == ".json":
            json.loads(content)
        else:
            # Basic validation for txt format
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    if "==" in line:
                        name, version = line.split("==", 1)
                        if not name or not version:
                            return False

        return True

    except (json.JSONDecodeError, OSError, ValueError):
        return False
