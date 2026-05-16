"""Build Chat Completions messages for Groq (architecture §7.1)."""

from __future__ import annotations

import json
from typing import Any

from app.records import RestaurantRecord
from app.schemas import RecommendRequest


def _candidate_dict(r: RestaurantRecord) -> dict[str, Any]:
    return {
        "restaurant_id": r.restaurant_id,
        "name": r.name[:120],
        "location": r.location[:160],
        "cuisine": r.cuisine[:200],
        "rating": r.rating,
        "cost_band": r.cost_band.value,
    }


def build_ranking_messages(
    candidates: list[RestaurantRecord],
    body: RecommendRequest,
    *,
    strict: bool = False,
) -> list[dict[str, str]]:
    prefs: dict[str, Any] = {
        "location": body.location,
        "budget": body.budget.value,
        "cuisine": body.cuisine,
        "min_rating": body.min_rating,
        "top_n": body.top_n,
    }
    if body.notes:
        prefs["notes"] = body.notes[:2000]

    user_payload = {
        "preferences": prefs,
        "candidates": [_candidate_dict(r) for r in candidates],
    }

    strict_extra = (
        " Output must be a single JSON object only, no markdown fences, no prose before or after."
        if strict
        else ""
    )
    system = (
        "You rank restaurants for a food-discovery app. You MUST only rank and explain venues "
        "listed in user JSON under `candidates`. Never invent a restaurant_id or name that is not "
        "in that list. Prefer 2–4 sentences per explanation tied to the user's preferences and optional notes."
        + strict_extra
    )
    schema_hint = (
        'Return JSON with shape: {"ranked_ids": ["id1","id2",...], "items": ['
        '{"restaurant_id":"id1","explanation":"..."}, ...]}. '
        "`ranked_ids` should list every candidate you want to recommend, best first; "
        "each id in `ranked_ids` must appear in `candidates`. "
        "`items` should include an explanation for each id you care to justify (at least for the top picks)."
    )
    user = schema_hint + "\n\n" + json.dumps(user_payload, ensure_ascii=False)
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
