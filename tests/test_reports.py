"""Tests for the reports module.

"""

import json
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from covert.reports import ReportConfig, ReportData, ReportGenerator, create_report_config


class TestReportConfig:
    """Tests for the ReportConfig dataclass."""

    def test_report_config_creation(self):
        """Test creating a ReportConfig instance."""
        config = ReportConfig(
            enabled=True,
            format="json",
            output_path="./report.json",
        )

        assert config.enabled is True
        assert config.format == "json"
        assert config.output_path == "./report.json"

    def test_report_config_defaults(self):
        """Test ReportConfig default values."""
        config = ReportConfig()

        assert config.enabled is False
        assert config.format == "json"
        assert config.output_path == ""


class TestReportData:
    """Tests for the ReportData dataclass."""

    def test_report_data_creation(self):
        """Test creating a ReportData instance."""
        data = ReportData(
            session_name="Test Session",
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 5, 0),
            duration=300.0,
            total_packages=10,
            updated_packages=8,
            rolled_back_packages=1,
            failed_packages=1,
            skipped_packages=0,
            vulnerabilities_found=2,
            pre_test_passed=True,
            backup_file="./backups/test.txt",
            package_results=[],
        )

        assert data.session_name == "Test Session"
        assert data.duration == 300.0
        assert data.total_packages == 10
        assert data.updated_packages == 8


class TestReportGenerator:
    """Tests for the ReportGenerator class."""

    def test_generator_initialization(self):
        """Test initializing the generator."""
        config = ReportConfig(format="json")
        generator = ReportGenerator(config)

        assert generator.config.format == "json"

    def test_generate_json(self):
        """Test generating a JSON report."""
        config = ReportConfig(format="json")
        generator = ReportGenerator(config)

        data = ReportData(
            session_name="Test Session",
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 5, 0),
            duration=300.0,
            total_packages=3,
            updated_packages=2,
            rolled_back_packages=1,
            failed_packages=0,
            skipped_packages=0,
            vulnerabilities_found=0,
            pre_test_passed=True,
            package_results=[
                {
                    "name": "requests",
                    "current_version": "2.25.0",
                    "latest_version": "2.26.0",
                    "status": "updated",
                    "error": None,
                }
            ],
        )

        result = generator.generate(data)

        # Verify it's valid JSON
        parsed = json.loads(result)
        assert parsed["session_name"] == "Test Session"
        assert parsed["summary"]["updated"] == 2

    def test_generate_html(self):
        """Test generating an HTML report."""
        config = ReportConfig(format="html")
        generator = ReportGenerator(config)

        data = ReportData(
            session_name="Test Session",
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 5, 0),
            duration=300.0,
            total_packages=3,
            updated_packages=2,
            rolled_back_packages=1,
            failed_packages=0,
            skipped_packages=0,
            vulnerabilities_found=0,
            pre_test_passed=True,
            package_results=[],
        )

        result = generator.generate(data)

        assert "<!DOCTYPE html>" in result
        assert "Covert Update Report" in result
        assert "Test Session" in result

    def test_generate_markdown(self):
        """Test generating a Markdown report."""
        config = ReportConfig(format="markdown")
        generator = ReportGenerator(config)

        data = ReportData(
            session_name="Test Session",
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 5, 0),
            duration=300.0,
            total_packages=3,
            updated_packages=2,
            rolled_back_packages=1,
            failed_packages=0,
            skipped_packages=0,
            vulnerabilities_found=0,
            pre_test_passed=True,
            package_results=[],
        )

        result = generator.generate(data)

        assert "# Covert Update Report" in result
        assert "Test Session" in result

    def test_generate_and_save_json(self):
        """Test generating and saving a JSON report."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            config = ReportConfig(
                enabled=True,
                format="json",
                output_path=str(output_path),
            )
            generator = ReportGenerator(config)

            data = ReportData(
                session_name="Test Session",
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration=10.0,
                total_packages=1,
                updated_packages=1,
            )

            result = generator.generate_and_save(data)

            assert result is not None
            assert output_path.exists()

            # Verify content
            content = output_path.read_text()
            assert "Test Session" in content

    def test_generate_and_save_disabled(self):
        """Test generate_and_save when disabled."""
        config = ReportConfig(enabled=False)
        generator = ReportGenerator(config)

        data = ReportData(session_name="Test")

        result = generator.generate_and_save(data)

        assert result is None

    def test_generate_and_save_creates_directory(self):
        """Test that generate_and_save creates parent directories."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "report.json"
            config = ReportConfig(
                enabled=True,
                format="json",
                output_path=str(output_path),
            )
            generator = ReportGenerator(config)

            data = ReportData(session_name="Test")

            result = generator.generate_and_save(data)

            assert result is not None
            assert output_path.exists()


class TestCreateReportConfig:
    """Tests for the create_report_config function."""

    def test_create_report_config_defaults(self):
        """Test create_report_config with defaults."""
        config = create_report_config()

        assert config.enabled is False
        assert config.format == "json"
        assert config.output_path == ""

    def test_create_report_config_custom(self):
        """Test create_report_config with custom values."""
        config = create_report_config(
            output_path="./report.html",
            report_format="html",
            enabled=True,
        )

        assert config.enabled is True
        assert config.format == "html"
        assert config.output_path == "./report.html"
