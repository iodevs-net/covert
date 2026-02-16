"""Vulnerability scanning module for Covert.

This module provides integration with vulnerability scanning tools like
pip-audit and safety for detecting known vulnerabilities in dependencies.

"""

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Vulnerability:
    """Represents a single vulnerability found in a package.

    Attributes:
        package_name: Name of the vulnerable package.
        installed_version: Currently installed version.
        vulnerabilities: List of vulnerability identifiers (e.g., CVE IDs).
        severity: Severity level (low, medium, high, critical).
        description: Description of the vulnerability.
        fix_versions: Versions that fix the vulnerability.
    """

    package_name: str
    installed_version: str
    vulnerabilities: List[str] = field(default_factory=list)
    severity: str = "unknown"
    description: str = ""
    fix_versions: List[str] = field(default_factory=list)


@dataclass
class VulnerabilityScanResult:
    """Result of a vulnerability scan.

    Attributes:
        timestamp: When the scan was performed.
        vulnerabilities: List of vulnerabilities found.
        scanned_count: Number of packages scanned.
        vulnerable_count: Number of packages with vulnerabilities.
        raw_output: Raw output from the scanning tool.
    """

    timestamp: datetime
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    scanned_count: int = 0
    vulnerable_count: int = 0
    raw_output: str = ""

    @property
    def has_vulnerabilities(self) -> bool:
        """Check if any vulnerabilities were found.

        Returns:
            bool: True if vulnerabilities were found.
        """
        return len(self.vulnerabilities) > 0


class VulnerabilityScanner:
    """Vulnerability scanner using pip-audit and safety tools.

    This class provides methods to scan installed packages for known
    vulnerabilities using pip-audit and safety.
    """

    def __init__(self, use_pip_audit: bool = True, use_safety: bool = True):
        """Initialize the vulnerability scanner.

        Args:
            use_pip_audit: Whether to use pip-audit for scanning.
            use_safety: Whether to use safety for scanning.
        """
        self.use_pip_audit = use_pip_audit
        self.use_safety = use_safety

    def scan(self, packages: Optional[List[Dict[str, str]]] = None) -> VulnerabilityScanResult:
        """Scan installed packages for vulnerabilities.

        Args:
            packages: Optional list of packages to scan. If None, scans all packages.

        Returns:
            VulnerabilityScanResult: Scan results including any vulnerabilities found.
        """
        result = VulnerabilityScanResult(timestamp=datetime.now())

        # Get packages to scan
        if packages is None:
            packages = self._get_all_packages()

        result.scanned_count = len(packages)

        # Run scans
        if self.use_pip_audit:
            self._run_pip_audit(result, packages)

        if self.use_safety:
            self._run_safety(result, packages)

        result.vulnerable_count = len(result.vulnerabilities)

        return result

    def scan_package(self, package_name: str, version: str) -> VulnerabilityScanResult:
        """Scan a specific package for vulnerabilities.

        Args:
            package_name: Name of the package to scan.
            version: Version of the package to scan.

        Returns:
            VulnerabilityScanResult: Scan results for the specific package.
        """
        result = VulnerabilityScanResult(timestamp=datetime.now())
        result.scanned_count = 1

        packages = [{"name": package_name, "version": version}]

        if self.use_pip_audit:
            self._run_pip_audit(result, packages)

        if self.use_safety:
            self._run_safety(result, packages)

        result.vulnerable_count = len(result.vulnerabilities)

        return result

    def _get_all_packages(self) -> List[Dict[str, str]]:
        """Get list of all installed packages.

        Returns:
            List[Dict[str, str]]: List of packages with name and version.
        """
        packages: List[Dict[str, str]] = []

        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                package_list = json.loads(result.stdout)
                packages = [{"name": p["name"], "version": p["version"]} for p in package_list]
        except (subprocess.SubprocessError, json.JSONDecodeError):
            pass

        return packages

    def _run_pip_audit(
        self, result: VulnerabilityScanResult, packages: List[Dict[str, str]]
    ) -> None:
        """Run pip-audit scan.

        Args:
            result: Result object to populate.
            packages: List of packages to scan.
        """
        try:
            proc = subprocess.run(
                ["pip-audit", "--format=json"],
                capture_output=True,
                text=True,
                check=False,
            )

            result.raw_output += f"\n--- pip-audit output ---\n{proc.stdout}"

            if proc.returncode in (0, 1):  # 0 = no vulns, 1 = vulns found
                try:
                    data = json.loads(proc.stdout)
                    # Handle both list and dict formats
                    if isinstance(data, list):
                        deps = data
                    elif isinstance(data, dict):
                        deps = data.get("dependencies", [])
                    else:
                        deps = []

                    for dep in deps:
                        if not isinstance(dep, dict):
                            continue
                        name = dep.get("name", "")
                        version = dep.get("version", "")
                        vulns = dep.get("vulns", [])

                        if vulns:
                            for vuln in vulns:
                                vulnerability = Vulnerability(
                                    package_name=name,
                                    installed_version=version,
                                    vulnerabilities=[vuln.get("id", "")],
                                    severity=vuln.get("severity", "unknown"),
                                    description=vuln.get("description", ""),
                                    fix_versions=vuln.get("fix_versions", []),
                                )
                                result.vulnerabilities.append(vulnerability)
                except json.JSONDecodeError:
                    pass
        except FileNotFoundError:
            # pip-audit not installed
            result.raw_output += "\n--- pip-audit not found ---\n"

    def _run_safety(
        self, result: VulnerabilityScanResult, packages: List[Dict[str, str]]
    ) -> None:
        """Run safety scan.

        Args:
            result: Result object to populate.
            packages: List of packages to scan.
        """
        try:
            # Use safety check with JSON output
            proc = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                check=False,
            )

            result.raw_output += f"\n--- safety output ---\n{proc.stdout}"

            if proc.returncode in (0, 1):  # 0 = no vulns, 1 = vulns found
                try:
                    data = json.loads(proc.stdout)

                    for item in data:
                        vulnerability = Vulnerability(
                            package_name=item.get("package", ""),
                            installed_version=item.get("installed_version", ""),
                            vulnerabilities=[item.get("vulnerability_id", "")],
                            severity=item.get("severity", "unknown"),
                            description=item.get("description", ""),
                            fix_versions=item.get("fixed_versions", []),
                        )
                        result.vulnerabilities.append(vulnerability)
                except (json.JSONDecodeError, TypeError):
                    pass
        except FileNotFoundError:
            # safety not installed
            result.raw_output += "\n--- safety not found ---\n"


def scan_vulnerabilities(
    use_pip_audit: bool = True,
    use_safety: bool = True,
    packages: Optional[List[Dict[str, str]]] = None,
) -> VulnerabilityScanResult:
    """Convenience function to scan for vulnerabilities.

    Args:
        use_pip_audit: Whether to use pip-audit.
        use_safety: Whether to use safety.
        packages: Optional list of packages to scan.

    Returns:
        VulnerabilityScanResult: Scan results.
    """
    scanner = VulnerabilityScanner(use_pip_audit=use_pip_audit, use_safety=use_safety)
    return scanner.scan(packages)
