"""Report generation module for Covert.

This module provides functionality to generate reports in various formats
(JSON, HTML, Markdown) for update sessions.

"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ReportConfig:
    """Configuration for report generation.

    Attributes:
        enabled: Whether report generation is enabled.
        format: Report format (json, html, markdown).
        output_path: Path where report should be saved.
        include_raw_output: Whether to include raw command output.
    """

    enabled: bool = False
    format: str = "json"
    output_path: str = ""
    include_raw_output: bool = False


@dataclass
class ReportData:
    """Data for generating a report.

    Attributes:
        session_name: Name of the update session.
        start_time: When the session started.
        end_time: When the session ended.
        duration: Duration in seconds.
        total_packages: Total packages scanned.
        updated_packages: Number of packages updated.
        rolled_back_packages: Number of packages rolled back.
        failed_packages: Number of packages that failed to update.
        skipped_packages: Number of packages skipped.
        vulnerabilities_found: Number of vulnerabilities found.
        pre_test_passed: Whether pre-flight tests passed.
        backup_file: Path to backup file if created.
        package_results: Detailed results for each package.
    """

    session_name: str = "Update Session"
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration: float = 0.0
    total_packages: int = 0
    updated_packages: int = 0
    rolled_back_packages: int = 0
    failed_packages: int = 0
    skipped_packages: int = 0
    vulnerabilities_found: int = 0
    pre_test_passed: bool = True
    backup_file: Optional[str] = None
    package_results: List[Dict[str, Any]] = field(default_factory=list)


class ReportGenerator:
    """Generator for creating update reports in various formats.

    This class handles generating reports in JSON, HTML, and Markdown formats.
    """

    def __init__(self, config: ReportConfig):
        """Initialize the report generator.

        Args:
            config: Report configuration.
        """
        self.config = config

    def generate(self, data: ReportData) -> str:
        """Generate a report from the given data.

        Args:
            data: Report data.

        Returns:
            str: Generated report content.
        """
        if self.config.format.lower() == "json":
            return self._generate_json(data)
        elif self.config.format.lower() == "html":
            return self._generate_html(data)
        elif self.config.format.lower() in ("markdown", "md"):
            return self._generate_markdown(data)
        else:
            return self._generate_json(data)

    def generate_and_save(self, data: ReportData) -> Optional[Path]:
        """Generate a report and save it to a file.

        Args:
            data: Report data.

        Returns:
            Optional[Path]: Path to the saved report, or None if not saved.
        """
        if not self.config.enabled:
            return None

        content = self.generate(data)

        output_path = Path(self.config.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path

    def _generate_json(self, data: ReportData) -> str:
        """Generate a JSON report.

        Args:
            data: Report data.

        Returns:
            str: JSON formatted report.
        """
        report: Dict[str, Any] = {
            "session_name": data.session_name,
            "timestamp": data.start_time.isoformat(),
            "duration_seconds": data.duration,
            "summary": {
                "total_packages": data.total_packages,
                "updated": data.updated_packages,
                "rolled_back": data.rolled_back_packages,
                "failed": data.failed_packages,
                "skipped": data.skipped_packages,
                "vulnerabilities_found": data.vulnerabilities_found,
            },
            "pre_test_passed": data.pre_test_passed,
            "backup_file": data.backup_file,
            "packages": data.package_results,
        }

        return json.dumps(report, indent=2, default=str)

    def _generate_html(self, data: ReportData) -> str:
        """Generate an HTML report.

        Args:
            data: Report data.

        Returns:
            str: HTML formatted report.
        """
        # Determine status color
        if data.failed_packages > 0 or data.rolled_back_packages > 0:
            status_color = "#f44336"
            status_text = "Completed with failures"
        elif data.vulnerabilities_found > 0:
            status_color = "#ff9800"
            status_text = "Completed with warnings"
        else:
            status_color = "#4caf50"
            status_text = "Completed successfully"

        # Build package table rows
        package_rows = ""
        for pkg in data.package_results:
            status = pkg.get("status", "unknown")
            status_class = f"status-{status}"
            package_rows += f"""
            <tr>
                <td>{pkg.get('name', 'N/A')}</td>
                <td>{pkg.get('current_version', 'N/A')}</td>
                <td>{pkg.get('latest_version', 'N/A')}</td>
                <td><span class="{status_class}">{status}</span></td>
                <td>{pkg.get('error', '-')}</td>
            </tr>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Covert Update Report - {data.session_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
        }}
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }}
        .summary-card .label {{
            color: #666;
            font-size: 0.9em;
        }}
        .status-bar {{
            background: {status_color};
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-updated {{
            color: #4caf50;
            font-weight: bold;
        }}
        .status-rolled_back {{
            color: #ff9800;
            font-weight: bold;
        }}
        .status-failed_install, .status-critical_failure {{
            color: #f44336;
            font-weight: bold;
        }}
        .status-skipped {{
            color: #9e9e9e;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Covert Update Report</h1>
        
        <div class="status-bar">
            {status_text}
        </div>

        <div class="summary">
            <div class="summary-card">
                <div class="value">{data.updated_packages}</div>
                <div class="label">Updated</div>
            </div>
            <div class="summary-card">
                <div class="value">{data.rolled_back_packages}</div>
                <div class="label">Rolled Back</div>
            </div>
            <div class="summary-card">
                <div class="value">{data.failed_packages}</div>
                <div class="label">Failed</div>
            </div>
            <div class="summary-card">
                <div class="value">{data.skipped_packages}</div>
                <div class="label">Skipped</div>
            </div>
            <div class="summary-card">
                <div class="value">{data.vulnerabilities_found}</div>
                <div class="label">Vulnerabilities</div>
            </div>
            <div class="summary-card">
                <div class="value">{data.duration:.2f}s</div>
                <div class="label">Duration</div>
            </div>
        </div>

        <h2>Package Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Package</th>
                    <th>Current Version</th>
                    <th>New Version</th>
                    <th>Status</th>
                    <th>Error</th>
                </tr>
            </thead>
            <tbody>
                {package_rows if package_rows else '<tr><td colspan="5">No packages processed</td></tr>'}
            </tbody>
        </table>

        <div class="footer">
            <p>Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Covert - Safe Package Updater</p>
        </div>
    </div>
</body>
</html>"""

    def _generate_markdown(self, data: ReportData) -> str:
        """Generate a Markdown report.

        Args:
            data: Report data.

        Returns:
            str: Markdown formatted report.
        """
        # Determine status badge
        if data.failed_packages > 0 or data.rolled_back_packages > 0:
            status_badge = "🔴 Completed with failures"
        elif data.vulnerabilities_found > 0:
            status_badge = "🟡 Completed with warnings"
        else:
            status_badge = "🟢 Completed successfully"

        # Build package list
        package_lines = []
        for pkg in data.package_results:
            name = pkg.get("name", "N/A")
            current = pkg.get("current_version", "N/A")
            latest = pkg.get("latest_version", "N/A")
            status = pkg.get("status", "unknown")
            error = pkg.get("error", "")

            status_emoji = {
                "updated": "✅",
                "rolled_back": "🔄",
                "failed_install": "❌",
                "critical_failure": "⛔",
                "skipped": "⏭️",
            }.get(status, "❓")

            line = f"- **{name}**: {current} → {latest} {status_emoji} ({status})"
            if error:
                line += f" - Error: {error}"
            package_lines.append(line)

        packages_text = "\n".join(package_lines) if package_lines else "No packages processed"

        return f"""# Covert Update Report

## {status_badge}

### Summary

| Metric | Value |
|--------|-------|
| Updated | {data.updated_packages} |
| Rolled Back | {data.rolled_back_packages} |
| Failed | {data.failed_packages} |
| Skipped | {data.skipped_packages} |
| Vulnerabilities | {data.vulnerabilities_found} |
| Duration | {data.duration:.2f} seconds |

### Session Details

- **Name**: {data.session_name}
- **Start Time**: {data.start_time.strftime('%Y-%m-%d %H:%M:%S')}
- **End Time**: {data.end_time.strftime('%Y-%m-%d %H:%M:%S') if data.end_time else 'N/A'}
- **Pre-test Passed**: {'Yes' if data.pre_test_passed else 'No'}
- **Backup File**: {data.backup_file or 'None'}

### Package Details

{packages_text}

---

*Report generated by Covert - Safe Package Updater*
"""


def create_report_config(
    output_path: str = "",
    report_format: str = "json",
    enabled: bool = False,
) -> ReportConfig:
    """Create a report configuration.

    Args:
        output_path: Path where report should be saved.
        report_format: Report format (json, html, markdown).
        enabled: Whether report generation is enabled.

    Returns:
        ReportConfig: Configured report settings.
    """
    return ReportConfig(
        enabled=enabled,
        format=report_format,
        output_path=output_path,
    )
