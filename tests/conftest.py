"""Pytest global configuration and fixtures."""

import os
import pytest


@pytest.fixture(autouse=True)
def configure_test_environment(monkeypatch: pytest.MonkeyPatch):
    """Ensure fast, deterministic unit test execution without consuming live API quota."""
    monkeypatch.setenv("SIMULACRA_USE_GEMINI", "false")
