"""Environment-based configuration for TestScope AI."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


class ConfigurationError(RuntimeError):
    """Raised when required application configuration is unavailable."""


@dataclass(frozen=True)
class Settings:
    """Configuration values used by the application."""

    gemini_api_key: str | None = None
    gemini_model: str | None = "gemini-2.5-flash"
    openai_api_key: str | None = None
    openai_model: str | None = None


def load_settings(*, require_api_key: bool = False) -> Settings:
    """Load local settings without exposing secret values.

    Args:
        require_api_key: Raise ``ConfigurationError`` when no API key exists.

    Returns:
        Immutable application settings.
    """

    load_dotenv()

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip() or None
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

    # Backward compatibility with OpenAI environment variables
    openai_key = os.getenv("OPENAI_API_KEY", "").strip() or None
    openai_model = os.getenv("OPENAI_MODEL", "").strip() or None

    effective_key = gemini_key or openai_key

    if require_api_key and effective_key is None:
        raise ConfigurationError(
            "GEMINI_API_KEY (or OPENAI_API_KEY) is not configured. Copy .env.example to .env "
            "and add your key locally."
        )

    return Settings(
        gemini_api_key=gemini_key,
        gemini_model=gemini_model,
        openai_api_key=openai_key,
        openai_model=openai_model,
    )


def get_gemini_api_key() -> str | None:
    """Return the configured Gemini API key if present."""
    load_dotenv()
    return os.getenv("GEMINI_API_KEY", "").strip() or None


def get_gemini_model() -> str:
    """Return the configured Gemini model name."""
    load_dotenv()
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"


def get_gemini_client():
    """Return an initialized Google GenAI Client or None if key is absent."""
    api_key = get_gemini_api_key()
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception:
        return None

