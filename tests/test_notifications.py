"""Tests for the notifications module.

"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from covert.notifications import (
    NotificationConfig,
    NotificationManager,
    NotificationMessage,
    create_notification_config,
)


class TestNotificationConfig:
    """Tests for the NotificationConfig dataclass."""

    def test_notification_config_creation(self):
        """Test creating a NotificationConfig instance."""
        config = NotificationConfig(
            enabled=True,
            channels=["slack"],
            slack_webhook="https://hooks.slack.com/test",
            slack_channel="#test",
            slack_username="Test Bot",
        )

        assert config.enabled is True
        assert config.channels == ["slack"]
        assert config.slack_webhook == "https://hooks.slack.com/test"
        assert config.slack_channel == "#test"
        assert config.slack_username == "Test Bot"

    def test_notification_config_defaults(self):
        """Test NotificationConfig default values."""
        config = NotificationConfig()

        assert config.enabled is False
        assert config.channels == ["slack"]
        assert config.slack_webhook == ""
        assert config.email_enabled is False
        assert config.email_to == []


class TestNotificationMessage:
    """Tests for the NotificationMessage dataclass."""

    def test_notification_message_creation(self):
        """Test creating a NotificationMessage instance."""
        message = NotificationMessage(
            title="Test Title",
            body="Test body content",
            severity="info",
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            metadata={"key": "value"},
        )

        assert message.title == "Test Title"
        assert message.body == "Test body content"
        assert message.severity == "info"
        assert message.metadata == {"key": "value"}

    def test_notification_message_defaults(self):
        """Test NotificationMessage default values."""
        message = NotificationMessage(
            title="Test",
            body="Body",
        )

        assert message.severity == "info"
        assert message.metadata == {}


class TestNotificationManager:
    """Tests for the NotificationManager class."""

    def test_manager_initialization(self):
        """Test initializing the manager."""
        config = NotificationConfig(enabled=False)
        manager = NotificationManager(config)

        assert manager.config.enabled is False
        assert manager._sent_count == 0

    def test_send_disabled(self):
        """Test sending when notifications are disabled."""
        config = NotificationConfig(enabled=False)
        manager = NotificationManager(config)

        message = NotificationMessage(title="Test", body="Test body")

        result = manager.send(message)

        assert result is True  # Should return True when disabled (no failure)
        assert manager._sent_count == 0

    @patch("covert.notifications.urllib.request.urlopen")
    def test_send_slack_success(self, mock_urlopen):
        """Test sending a Slack notification successfully."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        config = NotificationConfig(
            enabled=True,
            channels=["slack"],
            slack_webhook="https://hooks.slack.com/test",
        )
        manager = NotificationManager(config)

        message = NotificationMessage(
            title="Test",
            body="Test body",
            severity="info",
        )

        result = manager.send(message)

        assert result is True

    def test_send_update_summary(self):
        """Test sending update summary."""
        config = NotificationConfig(enabled=False)
        manager = NotificationManager(config)

        result = manager.send_update_summary(
            session_name="Test Session",
            updated=5,
            rolled_back=1,
            failed=0,
            skipped=2,
            duration=120.0,
            vulnerabilities=0,
        )

        assert result is True  # Returns True when disabled

    def test_summary(self):
        """Test getting summary of sent notifications."""
        config = NotificationConfig(enabled=False)
        manager = NotificationManager(config)

        # When disabled, _sent_count stays at 0
        summary = manager.summary()

        assert "sent" in summary
        assert summary["sent"] == 0


class TestCreateNotificationConfig:
    """Tests for the create_notification_config function."""

    def test_create_config_defaults(self):
        """Test create_notification_config with defaults."""
        config = create_notification_config()

        assert config.enabled is False
        assert config.slack_webhook == ""
        assert config.channels == []

    def test_create_config_slack(self):
        """Test create_notification_config with Slack."""
        config = create_notification_config(
            slack_webhook="https://hooks.slack.com/test",
            slack_channel="#test",
            enabled=True,
        )

        assert config.enabled is True
        assert config.slack_webhook == "https://hooks.slack.com/test"
        assert "slack" in config.channels

    def test_create_config_email(self):
        """Test create_notification_config with email."""
        config = create_notification_config(
            email_to=["test@example.com"],
            enabled=True,
        )

        assert config.enabled is True
        assert "test@example.com" in config.email_to
        assert "email" in config.channels

    def test_create_config_webhook(self):
        """Test create_notification_config with webhook."""
        config = create_notification_config(
            webhook_url="https://example.com/webhook",
            enabled=True,
        )

        assert config.enabled is True
        assert config.webhook_url == "https://example.com/webhook"
        assert "webhook" in config.channels


class TestNotificationMessageFormatting:
    """Tests for message formatting in NotificationManager."""

    def test_format_html_message(self):
        """Test HTML message formatting."""
        config = NotificationConfig(enabled=False)
        manager = NotificationManager(config)

        message = NotificationMessage(
            title="Test Title",
            body="Test body",
            severity="success",
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
        )

        html = manager._format_html_message(message)

        assert "<!DOCTYPE html>" in html
        assert "Test Title" in html
        assert "Test body" in html
        assert "#36a64f" in html  # Success color

    def test_format_html_message_error(self):
        """Test HTML message formatting for error."""
        config = NotificationConfig(enabled=False)
        manager = NotificationManager(config)

        message = NotificationMessage(
            title="Error Title",
            body="Error body",
            severity="error",
        )

        html = manager._format_html_message(message)

        assert "#f44336" in html  # Error color
