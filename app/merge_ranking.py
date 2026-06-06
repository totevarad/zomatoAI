"""Merge Groq-ranked ids with SQLite rows; grounding (architecture §7)."""

from __future__ import annotations

from app.llm_types import LLMRankResponse
from app.records import RestaurantRecord
from app.schemas import RestaurantResult


def explanations_from_llm(parsed: LLMRankResponse) -> dict[str, str]:
    out: dict[str, str] = {}
    for it in parsed.items:
        rid = (it.restaurant_id or "").strip()
        if rid:
            out[rid] = (it.explanation or "").strip()
    return out


def ordered_ranked_ids(parsed: LLMRankResponse, valid_ids: set[str]) -> list[str]:
    """Prefer ranked_ids order; fill gaps using items order; drop unknown / duplicate."""
    seen: set[str] = set()
    ordered: list[str] = []

    for rid in parsed.ranked_ids:
        rid = (rid or "").strip()
        if rid in valid_ids and rid not in seen:
            seen.add(rid)
            ordered.append(rid)

    for it in parsed.items:
        rid = (it.restaurant_id or "").strip()
        if rid in valid_ids and rid not in seen:
            seen.add(rid)
            ordered.append(rid)

    return ordered


def merge_ranked_with_pool(
    pool: list[RestaurantRecord],
    parsed: LLMRankResponse,
    *,
    top_n: int,
    fallback_explanation: str,
) -> list[RestaurantResult]:
    """
    Ground on `pool` only: drop hallucinated ids, append remaining pool rows in deterministic pool order.
    Display fields always come from `RestaurantRecord`, not from the model.
    """
    id_to_rec = {r.restaurant_id: r for r in pool}
    valid = set(id_to_rec.keys())
    llm_order = ordered_ranked_ids(parsed, valid)
    explanations = explanations_from_llm(parsed)

    final_ids: list[str] = list(llm_order)
    pool_ids = [r.restaurant_id for r in pool]
    for rid in pool_ids:
        if rid not in final_ids:
            final_ids.append(rid)

    out: list[RestaurantResult] = []
    for rid in final_ids[:top_n]:
        rec = id_to_rec[rid]
        expl = explanations.get(rid, "").strip() or fallback_explanation
        out.append(
            RestaurantResult(
                restaurant_id=rec.restaurant_id,
                name=rec.name,
                cuisine=rec.cuisine,
                rating=rec.rating,
                cost_band=rec.cost_band,
                explanation=expl,
                url=rec.url,
                image_url=rec.image_url,
            )

        )
    return out

