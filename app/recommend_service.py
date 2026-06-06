"""Recommendation orchestration: deterministic filters + optional Groq ranking (Phase 4)."""

import concurrent.futures
import re
import requests

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
        url=rec.url,
        image_url=rec.image_url,
    )


def _deterministic_results(pool: list[RestaurantRecord], body: RecommendRequest) -> list[RestaurantResult]:
    slice_n = min(body.top_n, len(pool))
    return [_record_to_result(r, _DETERMINISTIC_EXPLANATION) for r in pool[:slice_n]]


def fetch_zomato_image(url: str) -> str | None:
    if not url:
        return None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    try:
        response = requests.get(url, headers=headers, timeout=2.5)
        if response.status_code == 200:
            img_urls = re.findall(r'https://b.zmtcdn.com/data/pictures/[^\s"\']+\.(?:jpg|jpeg|png|webp)', response.text)
            if img_urls:
                return img_urls[0]
    except Exception:
        pass
    return None


def populate_images(results: list[RestaurantResult], store: RestaurantStore) -> None:
    to_fetch = [r for r in results if not r.image_url and r.url]
    if not to_fetch:
        return
        
    def fetch_and_save(res: RestaurantResult):
        img = fetch_zomato_image(res.url)
        if img:
            res.image_url = img
            store.update_image_url(res.restaurant_id, img)
            
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(fetch_and_save, to_fetch))


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
            populate_images(results, store)
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
            populate_images(results, store)
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
    populate_images(results, store)
    return RecommendResponse(
        results=results,
        meta=RecommendMeta(
            candidate_count=total,
            model=None,
            phase="deterministic",
            message=None,
        ),
    )

