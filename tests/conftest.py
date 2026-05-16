"""Pytest fixtures: isolate tests from developer `.env` (Groq / LLM keys)."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _clear_groq_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "GROQ_API_KEY",
        "GROQ_MODEL",
        "GROQ_TIMEOUT_SECONDS",
        "GROQ_TEMPERATURE",
        "GROQ_JSON_MODE",
        "LLM_API_KEY",
        "LLM_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)
