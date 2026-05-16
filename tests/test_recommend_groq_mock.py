"""Recommend flow with mocked Groq (no network)."""

from pathlib import Path
from unittest.mock import patch

from app.config import Settings
from app.ingest import write_sqlite
from app.llm_types import LLMRankItem, LLMRankResponse
from app.records import RestaurantRecord
from app.recommend_service import deterministic_recommend
from app.schemas import BudgetBand, RecommendRequest
from app.store import RestaurantStore


def _db(tmp: Path) -> Path:
    p = tmp / "r.sqlite"
    rows = [
        RestaurantRecord(
            restaurant_id="r1",
            name="First",
            location="Koramangala, Bangalore",
            cuisine="Chinese",
            rating=4.0,
            cost_band=BudgetBand.medium,
            url=None,
        ),
        RestaurantRecord(
            restaurant_id="r2",
            name="Second",
            location="Koramangala, Bangalore",
            cuisine="Chinese",
            rating=4.5,
            cost_band=BudgetBand.medium,
            url=None,
        ),
    ]
    write_sqlite(p, rows)
    return p


def test_groq_path_uses_merge_order(tmp_path: Path) -> None:
    db = _db(tmp_path)
    store = RestaurantStore(db)
    settings = Settings(
        _env_file=None,
        database_path=str(db),
        recommend_candidate_cap=10,
        groq_api_key="test-key",
        groq_model="test-model",
    )
    body = RecommendRequest(
        location="koramangala",
        budget=BudgetBand.medium,
        cuisine="chinese",
        min_rating=3.0,
        top_n=2,
    )
    fake = LLMRankResponse(
        ranked_ids=["r2", "r1"],
        items=[
            LLMRankItem(restaurant_id="r2", explanation="Groq likes r2"),
            LLMRankItem(restaurant_id="r1", explanation="Groq likes r1"),
        ],
    )
    with patch("app.recommend_service.rank_with_groq", return_value=fake):
        resp = deterministic_recommend(store, body, settings=settings)
    assert resp.meta.phase == "llm"
    assert resp.meta.model == "test-model"
    assert [r.restaurant_id for r in resp.results] == ["r2", "r1"]
    assert resp.results[0].explanation == "Groq likes r2"


def test_groq_failure_falls_back_deterministic(tmp_path: Path) -> None:
    db = _db(tmp_path)
    store = RestaurantStore(db)
    settings = Settings(
        _env_file=None,
        database_path=str(db),
        recommend_candidate_cap=10,
        groq_api_key="test-key",
    )
    body = RecommendRequest(
        location="koramangala",
        budget=BudgetBand.medium,
        cuisine="chinese",
        min_rating=3.0,
        top_n=2,
    )
    with patch("app.recommend_service.rank_with_groq", side_effect=RuntimeError("boom")):
        resp = deterministic_recommend(store, body, settings=settings)
    assert resp.meta.phase == "deterministic"
    assert resp.meta.message is not None
    assert "unavailable" in resp.meta.message.lower()
    # rating desc: r2 4.5 then r1 4.0
    assert [r.restaurant_id for r in resp.results] == ["r2", "r1"]
