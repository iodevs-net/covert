"""Notification system module for Covert.

This module provides notification capabilities for sending alerts about
update status via various channels (Slack,).

"""

import json
import smtplib
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode


@dataclass
class NotificationConfig:
    """Configuration for notifications.

    Attributes:
        enabled: Whether notifications are enabled.
        channels: List of notification channels to use.
        slack_webhook: Slack webhook URL.
        slack_channel: Slack channel to post to.
        slack_username: Username for Slack bot.
        email_enabled: Whether email notifications are enabled.
        email_from: Sender email address.
        email_to: Recipient email addresses.
        email_smtp_host: SMTP server host.
        email_smtp_port: SMTP server port.
        email_username: SMTP username.
        email_password: SMTP password.
        email_use_tls: Whether to use TLS for email.
        webhook_url: Generic webhook URL.
        webhook_headers: Additional headers for webhook requests.
    """

    enabled: bool = False
    channels: List[str] = field(default_factory=lambda: ["slack"])
    slack_webhook: str = ""
    slack_channel: str = ""
    slack_username: str = "Covert Updater"
    email_enabled: bool = False
    email_from: str = ""
    email_to: List[str] = field(default_factory=list)
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_use_tls: bool = True
    webhook_url: str = ""
    webhook_headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class NotificationMessage:
    """Notification message content.

    Attributes:
        title: Message title.
        body: Message body.
        severity: Message severity (info, success, warning, error).
        timestamp: When the message was created.
        metadata: Additional metadata to include.
    """

    title: str
    body: str
    severity: str = "info"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class NotificationManager:
    """Manager for sending notifications through various channels.

    This class handles sending notifications via Slack, email, and webhooks.
    """

    def __init__(self, config: NotificationConfig):
        """Initialize the notification manager.

        Args:
            config: Notification configuration.
        """
        self.config = config
        self._sent_count: int = 0

    def send(self, message: NotificationMessage) -> bool:
        """Send a notification message.

        Args:
            message: Message to send.

        Returns:
            bool: True if all configured channels sent successfully.
        """
        if not self.config.enabled:
            return True

        success = True

        for channel in self.config.channels:
            if channel == "slack":
                if not self._send_slack(message):
                    success = False
            elif channel == "email":
                if not self._send_email(message):
                    success = False
            elif channel == "webhook":
                if not self._send_webhook(message):
                    success = False

        if success:
            self._sent_count += 1

        return success

    def summary(self) -> Dict[str, int]:
        """Get summary of notifications sent.

        Returns:
            Dict[str, int]: Summary with sent count.
        """
        return {"sent": self._sent_count}

    def send_update_summary(
        self,
        session_name: str,
        updated: int,
        rolled_back: int,
        failed: int,
        skipped: int,
        duration: float,
        vulnerabilities: int = 0,
    ) -> bool:
        """Send a summary notification of an update session.

        Args:
            session_name: Name of the update session.
            updated: Number of successfully updated packages.
            rolled_back: Number of rolled back packages.
            failed: Number of failed updates.
            skipped: Number of skipped packages.
            duration: Duration in seconds.
            vulnerabilities: Number of vulnerabilities found.

        Returns:
            bool: True if notification sent successfully.
        """
        if failed > 0 or rolled_back > 0:
            severity = "error"
        elif vulnerabilities > 0:
            severity = "warning"
        else:
            severity = "success"

        body = f"""Update Session: {session_name}

Summary:
- Updated: {updated}
- Rolled Back: {rolled_back}
- Failed: {failed}
- Skipped: {skipped}
- Duration: {duration:.2f} seconds
- Vulnerabilities Found: {vulnerabilities}

Timestamp: {datetime.now().isoformat()}"""

        message = NotificationMessage(
            title=f"Covert Update: {session_name}",
            body=body,
            severity=severity,
            metadata={
                "updated": updated,
                "rolled_back": rolled_back,
                "failed": failed,
                "skipped": skipped,
                "duration": duration,
                "vulnerabilities": vulnerabilities,
            },
        )

        return self.send(message)

    def _send_slack(self, message: NotificationMessage) -> bool:
        """Send notification to Slack.

        Args:
            message: Message to send.

        Returns:
            bool: True if sent successfully.
        """
        if not self.config.slack_webhook:
            return False

        # Map severity to Slack colors
        color_map = {
            "success": "#36a64f",
            "warning": "#ff9800",
            "error": "#f44336",
            "info": "#2196f3",
        }

        payload = {
            "username": self.config.slack_username,
            "attachments": [
                {
                    "color": color_map.get(message.severity, "#2196f3"),
                    "title": message.title,
                    "text": message.body,
                    "footer": "Covert Updater",
                    "ts": int(message.timestamp.timestamp()),
                }
            ],
        }

        if self.config.slack_channel:
            payload["channel"] = self.config.slack_channel

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.config.slack_webhook,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.status == 200
        except Exception:
            return False

    def _send_email(self, message: NotificationMessage) -> bool:
        """Send notification via email.

        Args:
            message: Message to send.

        Returns:
            bool: True if sent successfully.
        """
        if not self.config.email_enabled:
            return False

        if not self.config.email_from or not self.config.email_to:
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.title
            msg["From"] = self.config.email_from
            msg["To"] = ", ".join(self.config.email_to)

            # Plain text part
            text_part = MIMEText(message.body, "plain")
            msg.attach(text_part)

            # HTML part
            html_body = self._format_html_message(message)
            html_part = MIMEText(html_body, "html")
            msg.attach(html_part)

            # Connect to SMTP server and send
            server = smtplib.SMTP(
                self.config.email_smtp_host,
                self.config.email_smtp_port,
            )

            if self.config.email_use_tls:
                server.starttls()

            if self.config.email_username and self.config.email_password:
                server.login(self.config.email_username, self.config.email_password)

            server.sendmail(
                self.config.email_from,
                self.config.email_to,
                msg.as_string(),
            )
            server.quit()

            return True
        except Exception:
            return False

    def _send_webhook(self, message: NotificationMessage) -> bool:
        """Send notification to a generic webhook.

        Args:
            message: Message to send.

        Returns:
            bool: True if sent successfully.
        """
        if not self.config.webhook_url:
            return False

        payload = {
            "title": message.title,
            "body": message.body,
            "severity": message.severity,
            "timestamp": message.timestamp.isoformat(),
            "metadata": message.metadata,
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            headers = {"Content-Type": "application/json", **self.config.webhook_headers}
            req = urllib.request.Request(
                self.config.webhook_url,
                data=data,
                headers=headers,
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.status < 400
        except Exception:
            return False

    def _format_html_message(self, message: NotificationMessage) -> str:
        """Format message as HTML.

        Args:
            message: Message to format.

        Returns:
            str: HTML formatted message.
        """
        severity_colors = {
            "success": "#36a64f",
            "warning": "#ff9800",
            "error": "#f44336",
            "info": "#2196f3",
        }

        color = severity_colors.get(message.severity, "#2196f3")

        return f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: {color}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 20px; border-radius: 0 0 5px 5px; }}
        .footer {{ color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>{message.title}</h2>
        </div>
        <div class="content">
            <pre style="white-space: pre-wrap; font-family: Arial, sans-serif;">{message.body}</pre>
        </div>
        <div class="footer">
            Sent by Covert Updater at {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>"""


def create_notification_config(
    slack_webhook: str = "",
    slack_channel: str = "",
    email_to: Optional[List[str]] = None,
    webhook_url: str = "",
    enabled: bool = False,
) -> NotificationConfig:
    """Create a notification configuration.

    Args:
        slack_webhook: Slack webhook URL.
        slack_channel: Slack channel.
        email_to: List of email recipients.
        webhook_url: Generic webhook URL.
        enabled: Whether notifications are enabled.

    Returns:
        NotificationConfig: Configured notification settings.
    """
    channels = []

    if slack_webhook:
        channels.append("slack")
    if email_to:
        channels.append("email")
    if webhook_url:
        channels.append("webhook")

    return NotificationConfig(
        enabled=enabled,
        channels=channels,
        slack_webhook=slack_webhook,
        slack_channel=slack_channel,
        email_enabled=bool(email_to),
        email_to=email_to or [],
        webhook_url=webhook_url,
    )
