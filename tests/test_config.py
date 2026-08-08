"""Tests for environment-based application configuration."""

import pytest

from src.config import ConfigurationError, load_settings


def test_settings_are_optional_before_agent_integration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.config.load_dotenv", lambda: False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    settings = load_settings()

    assert settings.openai_api_key is None
    assert settings.openai_model is None


def test_required_api_key_has_a_safe_clear_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("src.config.load_dotenv", lambda: False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY is not configured"):
        load_settings(require_api_key=True)
