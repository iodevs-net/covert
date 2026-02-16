"""Unit tests for backup module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from covert.backup import (
    cleanup_old_backups,
    create_backup,
    get_latest_backup,
    list_backups,
    restore_backup,
    validate_backup_file,
)
from covert.config import BackupConfig
from covert.exceptions import BackupError, PipError


class TestCreateBackup:
    """Tests for create_backup function."""

    @patch("covert.backup.freeze_requirements")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.mkdir")
    def test_create_txt_backup(self, mock_mkdir, mock_write, mock_freeze):
        """Test creating a txt backup."""
        mock_freeze.return_value = "requests==2.31.0\ndjango==5.0.0\n"

        config = BackupConfig(
            enabled=True,
            location="./backups",
            retention_days=30,
            format="txt",
        )

        backup_path = create_backup(config)

        assert backup_path.endswith(".txt")
        mock_freeze.assert_called_once_with(format_type="txt")

    @patch("covert.backup.freeze_requirements")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.mkdir")
    def test_create_json_backup(self, mock_mkdir, mock_write, mock_freeze):
        """Test creating a JSON backup."""
        mock_freeze.return_value = [
            {"name": "requests", "version": "2.31.0"},
            {"name": "django", "version": "5.0.0"},
        ]

        config = BackupConfig(
            enabled=True,
            location="./backups",
            retention_days=30,
            format="json",
        )

        backup_path = create_backup(config)

        assert backup_path.endswith(".json")
        mock_freeze.assert_called_once_with(format_type="json")

    def test_disabled_backup(self):
        """Test that disabled backup returns empty string."""
        config = BackupConfig(enabled=False)

        backup_path = create_backup(config)

        assert backup_path == ""

    @patch("covert.backup.freeze_requirements")
    @patch("pathlib.Path.mkdir")
    def test_backup_directory_creation(self, mock_mkdir, mock_freeze):
        """Test that backup directory is created."""
        mock_freeze.return_value = "requests==2.31.0\n"

        config = BackupConfig(
            enabled=True,
            location="./backups",
            retention_days=30,
            format="txt",
        )

        create_backup(config)

        mock_mkdir.assert_called_once()

    @patch("covert.backup.freeze_requirements")
    def test_freeze_failure(self, mock_freeze):
        """Test handling of freeze failure."""
        mock_freeze.side_effect = PipError("Failed to freeze")

        config = BackupConfig(
            enabled=True,
            location="./backups",
            retention_days=30,
            format="txt",
        )

        with pytest.raises(BackupError):
            create_backup(config)


class TestRestoreBackup:
    """Tests for restore_backup function."""

    @patch("covert.backup.install_package")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_restore_txt_backup(self, mock_exists, mock_read, mock_install):
        """Test restoring from txt backup."""
        mock_exists.return_value = True
        mock_read.return_value = "requests==2.31.0\ndjango==5.0.0\n"

        restore_backup("backup.txt")

        assert mock_install.call_count == 2

    @patch("covert.backup.install_package")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_restore_json_backup(self, mock_exists, mock_read, mock_install):
        """Test restoring from JSON backup."""
        mock_exists.return_value = True
        mock_read.return_value = json.dumps(
            [
                {"name": "requests", "version": "2.31.0"},
                {"name": "django", "version": "5.0.0"},
            ]
        )

        restore_backup("backup.json")

        assert mock_install.call_count == 2

    @patch("pathlib.Path.exists")
    def test_backup_not_found(self, mock_exists):
        """Test handling of missing backup file."""
        mock_exists.return_value = False

        with pytest.raises(BackupError):
            restore_backup("nonexistent.txt")

    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_invalid_json(self, mock_exists, mock_read):
        """Test handling of invalid JSON."""
        mock_exists.return_value = True
        mock_read.return_value = "invalid json"

        with pytest.raises(BackupError):
            restore_backup("backup.json")

    @patch("covert.backup.install_package")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_dry_run(self, mock_exists, mock_read, mock_install):
        """Test dry run mode."""
        mock_exists.return_value = True
        mock_read.return_value = "requests==2.31.0\n"

        result = restore_backup("backup.txt", dry_run=True)

        mock_install.assert_not_called()
        assert isinstance(result, list)

    @patch("covert.backup.install_package")
    @patch("covert.backup.get_logger")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_partial_failure(self, mock_exists, mock_read, mock_logger, mock_install):
        """Test handling of partial restoration failure."""
        mock_exists.return_value = True
        mock_read.return_value = "requests==2.31.0\ndjango==5.0.0\n"
        mock_install.side_effect = [
            None,  # First succeeds
            PipError("Failed"),  # Second fails
        ]

        # Should not raise, just log warning
        restore_backup("backup.txt")

        assert mock_install.call_count == 2


class TestCleanupOldBackups:
    """Tests for cleanup_old_backups function."""

    @patch("pathlib.Path.unlink")
    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.exists")
    def test_cleanup_by_count(self, mock_exists, mock_glob, mock_unlink):
        """Test cleanup by keeping N backups."""
        mock_exists.return_value = True

        # Mock backup files with timestamps
        mock_files = [
            MagicMock(spec=Path, name="backup_20240101_120000.txt"),
            MagicMock(spec=Path, name="backup_20240102_120000.txt"),
            MagicMock(spec=Path, name="backup_20240103_120000.txt"),
            MagicMock(spec=Path, name="backup_20240104_120000.txt"),
        ]
        mock_glob.return_value = iter(mock_files)

        # Mock stat for sorting
        for i, f in enumerate(mock_files):
            f.stat.return_value.st_mtime = 1000 + i

        config = BackupConfig(
            enabled=True,
            location="./backups",
            retention_days=30,
            format="txt",
        )

        deleted = cleanup_old_backups(config, keep_count=2)

        assert len(deleted) == 2

    @patch("pathlib.Path.unlink")
    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.exists")
    def test_cleanup_by_retention(self, mock_exists, mock_glob, mock_unlink):
        """Test cleanup by retention days."""
        from datetime import datetime

        mock_exists.return_value = True

        # Mock backup files
        mock_files = [
            MagicMock(spec=Path, name="backup_old.txt"),
            MagicMock(spec=Path, name="backup_new.txt"),
        ]
        mock_glob.return_value = iter(mock_files)

        # Mock stat - one old, one new
        now = datetime.now().timestamp()
        mock_files[0].stat.return_value.st_mtime = now - (40 * 24 * 60 * 60)  # 40 days old
        mock_files[1].stat.return_value.st_mtime = now - (10 * 24 * 60 * 60)  # 10 days old

        config = BackupConfig(
            enabled=True,
            location="./backups",
            retention_days=30,
            format="txt",
        )

        deleted = cleanup_old_backups(config)

        assert len(deleted) == 1

    def test_disabled_cleanup(self):
        """Test that disabled cleanup returns empty list."""
        config = BackupConfig(enabled=False)

        deleted = cleanup_old_backups(config)

        assert deleted == []

    @patch("pathlib.Path.exists")
    def test_no_backup_directory(self, mock_exists):
        """Test handling of missing backup directory."""
        mock_exists.return_value = False

        config = BackupConfig(
            enabled=True,
            location="./backups",
            retention_days=30,
            format="txt",
        )

        deleted = cleanup_old_backups(config)

        assert deleted == []


class TestListBackups:
    """Tests for list_backups function."""

    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.exists")
    def test_list_backups(self, mock_exists, mock_glob):
        """Test listing backup files."""
        mock_exists.return_value = True

        # Mock backup files
        mock_files = [
            MagicMock(spec=Path, name="backup_20240101_120000.txt"),
            MagicMock(spec=Path, name="backup_20240102_120000.json"),
        ]
        mock_glob.return_value = iter(mock_files)

        # Mock stat
        for f in mock_files:
            f.stat.return_value.st_mtime = 1000
            f.stat.return_value.st_size = 1000

        config = BackupConfig(
            enabled=True,
            location="./backups",
            retention_days=30,
            format="txt",
        )

        backups = list_backups(config)

        assert len(backups) == 2

    @patch("pathlib.Path.exists")
    def test_no_backup_directory(self, mock_exists):
        """Test handling of missing backup directory."""
        mock_exists.return_value = False

        config = BackupConfig(
            enabled=True,
            location="./backups",
            retention_days=30,
            format="txt",
        )

        backups = list_backups(config)

        assert backups == []


class TestGetLatestBackup:
    """Tests for get_latest_backup function."""

    @patch("covert.backup.list_backups")
    def test_get_latest_backup(self, mock_list):
        """Test getting the latest backup."""
        mock_list.return_value = [
            {
                "path": "./backups/backup_20240101_120000.txt",
                "name": "backup_20240101_120000.txt",
                "size": 1000,
                "modified": 1000,
                "format": "txt",
            },
        ]

        config = BackupConfig(
            enabled=True,
            location="./backups",
            retention_days=30,
            format="txt",
        )

        latest = get_latest_backup(config)

        assert latest is not None
        assert isinstance(latest, Path)

    @patch("covert.backup.list_backups")
    def test_no_backups(self, mock_list):
        """Test handling when no backups exist."""
        mock_list.return_value = []

        config = BackupConfig(
            enabled=True,
            location="./backups",
            retention_days=30,
            format="txt",
        )

        latest = get_latest_backup(config)

        assert latest is None


class TestValidateBackupFile:
    """Tests for validate_backup_file function."""

    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_valid_txt_backup(self, mock_exists, mock_read):
        """Test validation of valid txt backup."""
        mock_exists.return_value = True
        mock_read.return_value = "requests==2.31.0\ndjango==5.0.0\n"

        result = validate_backup_file("backup.txt")

        assert result is True

    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_valid_json_backup(self, mock_exists, mock_read):
        """Test validation of valid JSON backup."""
        mock_exists.return_value = True
        mock_read.return_value = json.dumps(
            [
                {"name": "requests", "version": "2.31.0"},
            ]
        )

        result = validate_backup_file("backup.json")

        assert result is True

    @patch("pathlib.Path.exists")
    def test_file_not_exists(self, mock_exists):
        """Test validation of non-existent file."""
        mock_exists.return_value = False

        result = validate_backup_file("nonexistent.txt")

        assert result is False

    @patch("pathlib.Path.exists")
    def test_invalid_extension(self, mock_exists):
        """Test validation of invalid file extension."""
        mock_exists.return_value = True

        result = validate_backup_file("backup.xml")

        assert result is False

    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_invalid_json(self, mock_exists, mock_read):
        """Test validation of invalid JSON."""
        mock_exists.return_value = True
        mock_read.return_value = "invalid json"

        result = validate_backup_file("backup.json")

        assert result is False

    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_invalid_txt_format(self, mock_exists, mock_read):
        """Test validation of invalid txt format."""
        mock_exists.return_value = True
        mock_read.return_value = "invalid==\n"

        result = validate_backup_file("backup.txt")

        assert result is False
