"""Tests for the vulnerability scanner module.

"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from covert.vuln_scanner import (
    Vulnerability,
    VulnerabilityScanResult,
    VulnerabilityScanner,
    scan_vulnerabilities,
)


class TestVulnerability:
    """Tests for the Vulnerability dataclass."""

    def test_vulnerability_creation(self):
        """Test creating a Vulnerability instance."""
        vuln = Vulnerability(
            package_name="requests",
            installed_version="2.25.0",
            vulnerabilities=["CVE-2023-1234"],
            severity="high",
            description="A security vulnerability",
            fix_versions=["2.26.0"],
        )

        assert vuln.package_name == "requests"
        assert vuln.installed_version == "2.25.0"
        assert vuln.vulnerabilities == ["CVE-2023-1234"]
        assert vuln.severity == "high"
        assert vuln.description == "A security vulnerability"
        assert vuln.fix_versions == ["2.26.0"]

    def test_vulnerability_defaults(self):
        """Test Vulnerability default values."""
        vuln = Vulnerability(
            package_name="test-package",
            installed_version="1.0.0",
        )

        assert vuln.vulnerabilities == []
        assert vuln.severity == "unknown"
        assert vuln.description == ""
        assert vuln.fix_versions == []


class TestVulnerabilityScanResult:
    """Tests for the VulnerabilityScanResult dataclass."""

    def test_scan_result_creation(self):
        """Test creating a VulnerabilityScanResult instance."""
        result = VulnerabilityScanResult(
            timestamp=datetime.now(),
            vulnerabilities=[],
            scanned_count=10,
            vulnerable_count=0,
        )

        assert result.scanned_count == 10
        assert result.vulnerable_count == 0
        assert result.vulnerabilities == []

    def test_has_vulnerabilities_property(self):
        """Test the has_vulnerabilities property."""
        result = VulnerabilityScanResult(
            timestamp=datetime.now(),
            vulnerabilities=[],
        )
        assert result.has_vulnerabilities is False

        vuln = Vulnerability(
            package_name="test",
            installed_version="1.0.0",
        )
        result.vulnerabilities.append(vuln)
        assert result.has_vulnerabilities is True


class TestVulnerabilityScanner:
    """Tests for the VulnerabilityScanner class."""

    def test_scanner_initialization(self):
        """Test initializing the scanner."""
        scanner = VulnerabilityScanner(use_pip_audit=True, use_safety=True)

        assert scanner.use_pip_audit is True
        assert scanner.use_safety is True

    def test_scanner_initialization_defaults(self):
        """Test scanner default initialization."""
        scanner = VulnerabilityScanner()

        assert scanner.use_pip_audit is True
        assert scanner.use_safety is True

    @patch("covert.vuln_scanner.subprocess.run")
    def test_get_all_packages(self, mock_run):
        """Test getting all packages."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps([
                {"name": "requests", "version": "2.25.0"},
                {"name": "django", "version": "4.0.0"},
            ]),
        )

        scanner = VulnerabilityScanner()
        packages = scanner._get_all_packages()

        assert len(packages) == 2
        assert packages[0]["name"] == "requests"
        assert packages[1]["name"] == "django"

    @patch("covert.vuln_scanner.subprocess.run")
    def test_get_all_packages_failure(self, mock_run):
        """Test getting all packages when pip fails."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")

        scanner = VulnerabilityScanner()
        packages = scanner._get_all_packages()

        assert packages == []

    @patch("covert.vuln_scanner.subprocess.run")
    def test_run_pip_audit_no_vulns(self, mock_run):
        """Test pip-audit with no vulnerabilities."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"dependencies": []}),
        )

        result = VulnerabilityScanResult(timestamp=datetime.now())
        scanner = VulnerabilityScanner()

        scanner._run_pip_audit(result, [{"name": "test", "version": "1.0.0"}])

        assert result.vulnerabilities == []

    @patch("covert.vuln_scanner.subprocess.run")
    def test_run_pip_audit_with_vulns(self, mock_run):
        """Test pip-audit with vulnerabilities."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=json.dumps({
                "dependencies": [
                    {
                        "name": "requests",
                        "version": "2.25.0",
                        "vulns": [
                            {
                                "id": "CVE-2023-1234",
                                "severity": "high",
                                "description": "Test vulnerability",
                                "fix_versions": ["2.26.0"],
                            }
                        ],
                    }
                ]
            }),
        )

        result = VulnerabilityScanResult(timestamp=datetime.now())
        scanner = VulnerabilityScanner()

        scanner._run_pip_audit(result, [{"name": "requests", "version": "2.25.0"}])

        assert len(result.vulnerabilities) == 1
        assert result.vulnerabilities[0].package_name == "requests"
        assert result.vulnerabilities[0].vulnerabilities == ["CVE-2023-1234"]

    @patch("covert.vuln_scanner.subprocess.run")
    def test_run_pip_audit_not_found(self, mock_run):
        """Test pip-audit when not installed."""
        mock_run.side_effect = FileNotFoundError()

        result = VulnerabilityScanResult(timestamp=datetime.now())
        scanner = VulnerabilityScanner()

        scanner._run_pip_audit(result, [])

        assert "pip-audit not found" in result.raw_output

    @patch("covert.vuln_scanner.subprocess.run")
    def test_run_safety_no_vulns(self, mock_run):
        """Test safety with no vulnerabilities."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="[]",
        )

        result = VulnerabilityScanResult(timestamp=datetime.now())
        scanner = VulnerabilityScanner()

        scanner._run_safety(result, [{"name": "test", "version": "1.0.0"}])

        assert result.vulnerabilities == []

    @patch("covert.vuln_scanner.subprocess.run")
    def test_scan_package(self, mock_run):
        """Test scanning a specific package."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="[]",
        )

        scanner = VulnerabilityScanner()
        result = scanner.scan_package("requests", "2.25.0")

        assert result.scanned_count == 1


class TestScanVulnerabilities:
    """Tests for the scan_vulnerabilities convenience function."""

    @patch("covert.vuln_scanner.VulnerabilityScanner.scan")
    def test_scan_vulnerabilities_function(self, mock_scan):
        """Test the scan_vulnerabilities function."""
        mock_scan.return_value = VulnerabilityScanResult(
            timestamp=datetime.now(),
        )

        result = scan_vulnerabilities(
            use_pip_audit=True,
            use_safety=False,
        )

        assert isinstance(result, VulnerabilityScanResult)
