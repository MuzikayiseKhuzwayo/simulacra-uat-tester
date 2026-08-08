"""Environment-based configuration for TestScope AI."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


class ConfigurationError(RuntimeError):
    """Raised when required application configuration is unavailable."""


@dataclass(frozen=True)
class Settings:
    """Configuration values used by the application."""

    openai_api_key: str | None
    openai_model: str | None


def load_settings(*, require_api_key: bool = False) -> Settings:
    """Load local settings without exposing secret values.

    Args:
        require_api_key: Raise ``ConfigurationError`` when no API key exists.

    Returns:
        Immutable application settings.
    """

    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY", "").strip() or None
    model = os.getenv("OPENAI_MODEL", "").strip() or None

    if require_api_key and api_key is None:
        raise ConfigurationError(
            "OPENAI_API_KEY is not configured. Copy .env.example to .env "
            "and add your key locally."
        )

    return Settings(openai_api_key=api_key, openai_model=model)
