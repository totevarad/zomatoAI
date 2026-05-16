"""Groq Chat Completions for candidate ranking (Phase 4)."""

from __future__ import annotations

import json
import re
from typing import Any

from groq import Groq

from app.config import Settings
from app.llm_types import LLMRankResponse
from app.prompts import build_ranking_messages
from app.records import RestaurantRecord
from app.schemas import RecommendRequest


class GroqRankingError(Exception):
    """Raised when Groq returns unusable output after retries."""


def _strip_code_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


def parse_rank_json(content: str) -> LLMRankResponse:
    raw = _strip_code_fence(content)
    data: Any = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return LLMRankResponse.model_validate(data)


def _call_groq(messages: list[dict[str, str]], settings: Settings) -> str:
    key = settings.resolved_groq_api_key()
    if not key:
        raise GroqRankingError("missing API key")
    client = Groq(api_key=key, timeout=settings.groq_timeout_seconds)
    model = settings.resolved_groq_model()
    base_kw: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": settings.groq_temperature,
    }
    attempts: list[dict[str, Any]] = []
    if settings.groq_json_mode:
        attempts.append({**base_kw, "response_format": {"type": "json_object"}})
    attempts.append(base_kw)

    last_err: Exception | None = None
    for kw in attempts:
        try:
            completion = client.chat.completions.create(**kw)
            choice = completion.choices[0].message
            if not choice or not choice.content:
                raise GroqRankingError("empty completion")
            return choice.content
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            continue
    assert last_err is not None
    raise GroqRankingError(str(last_err)) from last_err


def rank_with_groq(
    pool: list[RestaurantRecord],
    body: RecommendRequest,
    settings: Settings,
) -> LLMRankResponse:
    """
    One attempt + optional strict retry on parse/validation failure (architecture §7.4).
    """
    last_err: Exception | None = None
    for strict in (False, True):
        messages = build_ranking_messages(pool, body, strict=strict)
        try:
            content = _call_groq(messages, settings)
            return parse_rank_json(content)
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            continue
    assert last_err is not None
    raise GroqRankingError(str(last_err)) from last_err
