"""Recommendation orchestration: deterministic filters + optional Groq ranking (Phase 4)."""

from app.config import Settings
from app.groq_rank import rank_with_groq
from app.merge_ranking import merge_ranked_with_pool
from app.records import RestaurantRecord
from app.schemas import RecommendMeta, RecommendRequest, RecommendResponse, RestaurantResult
from app.store import RestaurantStore

_EMPTY_STORE_MESSAGE = (
    "Restaurant database is empty or not loaded. Run `python -m app.ingest` "
    "or check `ingest_error` on GET /store/info."
)
_NO_MATCH_MESSAGE = (
    "No restaurants matched your filters. Try a broader location or cuisine, "
    "a different budget band, or a lower minimum rating."
)
_DETERMINISTIC_EXPLANATION = "Ranked by rating and cost band (deterministic; Groq not used)."
_LLM_FALLBACK_MESSAGE = (
    "AI ranking was unavailable; results use deterministic order from the database."
)


def _record_to_result(rec: RestaurantRecord, explanation: str) -> RestaurantResult:
    return RestaurantResult(
        restaurant_id=rec.restaurant_id,
        name=rec.name,
        cuisine=rec.cuisine,
        rating=rec.rating,
        cost_band=rec.cost_band,
        explanation=explanation,
    )


def _deterministic_results(pool: list[RestaurantRecord], body: RecommendRequest) -> list[RestaurantResult]:
    slice_n = min(body.top_n, len(pool))
    return [_record_to_result(r, _DETERMINISTIC_EXPLANATION) for r in pool[:slice_n]]


def deterministic_recommend(
    store: RestaurantStore,
    body: RecommendRequest,
    *,
    settings: Settings,
) -> RecommendResponse:
    if not store.exists() or store.row_count() == 0:
        return RecommendResponse(
            results=[],
            meta=RecommendMeta(
                candidate_count=0,
                model=None,
                phase="deterministic",
                message=_EMPTY_STORE_MESSAGE,
            ),
        )

    cap = settings.recommend_candidate_cap
    total, pool = store.filter_candidates(
        location_substr=body.location,
        cuisine_substr=body.cuisine,
        budget=body.budget,
        min_rating=body.min_rating,
        cap=cap,
    )
    if total == 0:
        return RecommendResponse(
            results=[],
            meta=RecommendMeta(
                candidate_count=0,
                model=None,
                phase="deterministic",
                message=_NO_MATCH_MESSAGE,
            ),
        )

    api_key = settings.resolved_groq_api_key()
    model_name = settings.resolved_groq_model()

    if api_key:
        try:
            parsed = rank_with_groq(pool, body, settings)
            results = merge_ranked_with_pool(
                pool,
                parsed,
                top_n=body.top_n,
                fallback_explanation=_DETERMINISTIC_EXPLANATION,
            )
            return RecommendResponse(
                results=results,
                meta=RecommendMeta(
                    candidate_count=total,
                    model=model_name,
                    phase="llm",
                    message=None,
                ),
            )
        except Exception as exc:  # noqa: BLE001 — any Groq/network/parse failure → deterministic fallback
            results = _deterministic_results(pool, body)
            short = f"{type(exc).__name__}: {exc!s}"
            if len(short) > 220:
                short = short[:217] + "..."
            return RecommendResponse(
                results=results,
                meta=RecommendMeta(
                    candidate_count=total,
                    model=model_name,
                    phase="deterministic",
                    message=f"{_LLM_FALLBACK_MESSAGE} ({short})",
                ),
            )

    results = _deterministic_results(pool, body)
    return RecommendResponse(
        results=results,
        meta=RecommendMeta(
            candidate_count=total,
            model=None,
            phase="deterministic",
            message=None,
        ),
    )
