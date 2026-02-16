"""Tests for the interactive module.

"""

import pytest
from unittest.mock import MagicMock

from covert.interactive import (
    InteractiveConfig,
    InteractivePrompter,
    create_interactive_config,
)


class TestInteractiveConfig:
    """Tests for the InteractiveConfig dataclass."""

    def test_interactive_config_creation(self):
        """Test creating an InteractiveConfig instance."""
        config = InteractiveConfig(
            enabled=True,
            confirm_each=True,
            show_diffs=True,
            allow_skip=True,
        )

        assert config.enabled is True
        assert config.confirm_each is True
        assert config.show_diffs is True
        assert config.allow_skip is True

    def test_interactive_config_defaults(self):
        """Test InteractiveConfig default values."""
        config = InteractiveConfig()

        assert config.enabled is False
        assert config.confirm_each is True
        assert config.show_diffs is True
        assert config.allow_skip is True


class TestInteractivePrompter:
    """Tests for the InteractivePrompter class."""

    def test_prompter_initialization(self):
        """Test initializing the prompter."""
        config = InteractiveConfig(enabled=False)
        prompter = InteractivePrompter(config)

        assert prompter.config.enabled is False
        assert prompter._selected_packages == []
        assert prompter._skipped_packages == []

    def test_prompter_with_custom_input(self):
        """Test prompter with custom input function."""
        config = InteractiveConfig(enabled=False)
        mock_input = MagicMock(return_value="")
        prompter = InteractivePrompter(config, input_func=mock_input)

        assert prompter._input_func == mock_input

    def test_prompt_for_packages_disabled(self):
        """Test prompt_for_packages when disabled."""
        config = InteractiveConfig(enabled=False)
        prompter = InteractivePrompter(config)

        packages = [
            {"name": "requests", "version": "2.25.0", "latest_version": "2.26.0"},
            {"name": "django", "version": "4.0.0", "latest_version": "4.1.0"},
        ]

        result = prompter.prompt_for_packages(packages)

        # When disabled, should return all packages unchanged
        assert result == packages

    def test_prompt_for_packages_enabled_select_all(self):
        """Test prompt_for_packages with 'all' selection."""
        config = InteractiveConfig(enabled=True)
        mock_input = MagicMock(return_value="a")
        prompter = InteractivePrompter(config, input_func=mock_input)

        packages = [
            {"name": "requests", "version": "2.25.0", "latest_version": "2.26.0"},
            {"name": "django", "version": "4.0.0", "latest_version": "4.1.0"},
        ]

        result = prompter.prompt_for_packages(packages)

        assert result == packages
        assert prompter._selected_packages == ["requests", "django"]

    def test_prompt_for_packages_enabled_select_none(self):
        """Test prompt_for_packages with 'none' selection."""
        config = InteractiveConfig(enabled=True)
        mock_input = MagicMock(return_value="n")
        prompter = InteractivePrompter(config, input_func=mock_input)

        packages = [
            {"name": "requests", "version": "2.25.0", "latest_version": "2.26.0"},
        ]

        result = prompter.prompt_for_packages(packages)

        assert result == []

    def test_prompt_for_packages_enabled_select_specific(self):
        """Test prompt_for_packages with specific selection."""
        config = InteractiveConfig(enabled=True)
        mock_input = MagicMock(return_value="1")
        prompter = InteractivePrompter(config, input_func=mock_input)

        packages = [
            {"name": "requests", "version": "2.25.0", "latest_version": "2.26.0"},
            {"name": "django", "version": "4.0.0", "latest_version": "4.1.0"},
        ]

        result = prompter.prompt_for_packages(packages)

        assert len(result) == 1
        assert result[0]["name"] == "requests"

    def test_confirm_update_disabled(self):
        """Test confirm_update when disabled."""
        config = InteractiveConfig(enabled=False)
        prompter = InteractivePrompter(config)

        package = {"name": "requests", "version": "2.25.0", "latest_version": "2.26.0"}

        result = prompter.confirm_update(package)

        assert result is True

    def test_confirm_update_enabled_yes(self):
        """Test confirm_update with yes response."""
        config = InteractiveConfig(enabled=True, confirm_each=True)
        mock_input = MagicMock(return_value="y")
        prompter = InteractivePrompter(config, input_func=mock_input)

        package = {"name": "requests", "version": "2.25.0", "latest_version": "2.26.0"}

        result = prompter.confirm_update(package)

        assert result is True

    def test_confirm_update_enabled_no(self):
        """Test confirm_update with no response."""
        config = InteractiveConfig(enabled=True, confirm_each=True)
        mock_input = MagicMock(return_value="n")
        prompter = InteractivePrompter(config, input_func=mock_input)

        package = {"name": "requests", "version": "2.25.0", "latest_version": "2.26.0"}

        result = prompter.confirm_update(package)

        assert result is False

    def test_confirm_update_enabled_skip_all(self):
        """Test confirm_update with skip all response."""
        config = InteractiveConfig(enabled=True, confirm_each=True, allow_skip=True)
        mock_input = MagicMock(return_value="s")
        prompter = InteractivePrompter(config, input_func=mock_input)

        package = {"name": "requests", "version": "2.25.0", "latest_version": "2.26.0"}

        result = prompter.confirm_update(package)

        assert result is False
        assert "requests" in prompter._skipped_packages

    def test_prompt_continue_after_failure_disabled(self):
        """Test prompt_continue_after_failure when disabled."""
        config = InteractiveConfig(enabled=False)
        prompter = InteractivePrompter(config)

        package = {"name": "requests", "version": "2.25.0"}

        result = prompter.prompt_continue_after_failure(package, "Test error")

        # When disabled, should return False (don't continue)
        assert result is False

    def test_prompt_continue_after_failure_enabled_yes(self):
        """Test prompt_continue_after_failure with yes."""
        config = InteractiveConfig(enabled=True)
        mock_input = MagicMock(return_value="y")
        prompter = InteractivePrompter(config, input_func=mock_input)

        package = {"name": "requests", "version": "2.25.0"}

        result = prompter.prompt_continue_after_failure(package, "Test error")

        assert result is True

    def test_prompt_continue_after_failure_enabled_no(self):
        """Test prompt_continue_after_failure with no."""
        config = InteractiveConfig(enabled=True)
        mock_input = MagicMock(return_value="n")
        prompter = InteractivePrompter(config, input_func=mock_input)

        package = {"name": "requests", "version": "2.25.0"}

        result = prompter.prompt_continue_after_failure(package, "Test error")

        assert result is False

    def test_summary(self):
        """Test summary method."""
        config = InteractiveConfig(enabled=False)
        prompter = InteractivePrompter(config)

        prompter._selected_packages = ["requests", "django"]
        prompter._skipped_packages = ["flask"]

        result = prompter.summary()

        assert result["selected"] == ["requests", "django"]
        assert result["skipped"] == ["flask"]


class TestCreateInteractiveConfig:
    """Tests for the create_interactive_config function."""

    def test_create_config_defaults(self):
        """Test create_interactive_config with defaults."""
        config = create_interactive_config()

        assert config.enabled is False
        assert config.confirm_each is True
        assert config.show_diffs is True
        assert config.allow_skip is True

    def test_create_config_custom(self):
        """Test create_interactive_config with custom values."""
        config = create_interactive_config(
            enabled=True,
            confirm_each=False,
            show_diffs=False,
            allow_skip=False,
        )

        assert config.enabled is True
        assert config.confirm_each is False
        assert config.show_diffs is False
        assert config.allow_skip is False
