"""Unit tests for Phase 3 deterministic filtering (no HF, no live API)."""

from pathlib import Path

from app.config import Settings
from app.ingest import write_sqlite
from app.records import RestaurantRecord
from app.recommend_service import deterministic_recommend
from app.schemas import BudgetBand, RecommendRequest
from app.store import RestaurantStore


def _tiny_db(path: Path) -> None:
    rows = [
        RestaurantRecord(
            restaurant_id="a1",
            name="Low Rated",
            location="Koramangala, South Bangalore",
            cuisine="Chinese, Thai",
            rating=3.0,
            cost_band=BudgetBand.low,
            url=None,
        ),
        RestaurantRecord(
            restaurant_id="a2",
            name="Mid Chinese",
            location="Koramangala, South Bangalore",
            cuisine="Chinese",
            rating=4.2,
            cost_band=BudgetBand.medium,
            url=None,
        ),
        RestaurantRecord(
            restaurant_id="a3",
            name="Top Chinese",
            location="Koramangala, South Bangalore",
            cuisine="North Indian, Chinese",
            rating=4.5,
            cost_band=BudgetBand.medium,
            url=None,
        ),
        RestaurantRecord(
            restaurant_id="a4",
            name="Wrong cuisine",
            location="Koramangala, South Bangalore",
            cuisine="Italian",
            rating=4.9,
            cost_band=BudgetBand.medium,
            url=None,
        ),
        RestaurantRecord(
            restaurant_id="a5",
            name="Apple Tie",
            location="Koramangala, South Bangalore",
            cuisine="Chinese",
            rating=4.5,
            cost_band=BudgetBand.medium,
            url=None,
        ),
        RestaurantRecord(
            restaurant_id="a6",
            name="Zebra Tie",
            location="Koramangala, South Bangalore",
            cuisine="Chinese",
            rating=4.5,
            cost_band=BudgetBand.medium,
            url=None,
        ),
    ]
    write_sqlite(path, rows)


def test_ordering_rating_then_name(tmp_path: Path) -> None:
    db = tmp_path / "t.sqlite"
    _tiny_db(db)
    store = RestaurantStore(db)
    settings = Settings(
        _env_file=None,
        database_path=str(db),
        recommend_candidate_cap=10,
    )
    body = RecommendRequest(
        location="koramangala",
        budget=BudgetBand.medium,
        cuisine="chinese",
        min_rating=4.0,
        top_n=3,
    )
    resp = deterministic_recommend(store, body, settings=settings)
    # a2, a3, a5, a6 (medium + chinese substring + rating >= 4.0); a4 Italian out
    assert resp.meta.candidate_count == 4
    assert len(resp.results) == 3
    # rating 4.5: name ASC -> Apple Tie, Top Chinese, Zebra Tie
    assert [r.restaurant_id for r in resp.results] == ["a5", "a3", "a6"]
    assert all("deterministic" in r.explanation.lower() for r in resp.results)


def test_no_match_message(tmp_path: Path) -> None:
    db = tmp_path / "t.sqlite"
    _tiny_db(db)
    store = RestaurantStore(db)
    settings = Settings(_env_file=None, database_path=str(db), recommend_candidate_cap=10)
    body = RecommendRequest(
        location="indiranagar",
        budget=BudgetBand.low,
        cuisine="chinese",
        min_rating=4.0,
        top_n=5,
    )
    resp = deterministic_recommend(store, body, settings=settings)
    assert resp.results == []
    assert resp.meta.candidate_count == 0
    assert resp.meta.message is not None


def test_empty_store_message(tmp_path: Path) -> None:
    db = tmp_path / "missing.sqlite"
    store = RestaurantStore(db)
    settings = Settings(_env_file=None, database_path=str(db), recommend_candidate_cap=10)
    body = RecommendRequest(
        location="x",
        budget=BudgetBand.low,
        cuisine="y",
        min_rating=3.0,
        top_n=5,
    )
    resp = deterministic_recommend(store, body, settings=settings)
    assert resp.results == []
    assert "ingest" in (resp.meta.message or "").lower()


def test_cap_limits_pool_but_count_full(tmp_path: Path) -> None:
    db = tmp_path / "t.sqlite"
    rows = [
        RestaurantRecord(
            restaurant_id=f"id{i}",
            name=f"R{i}",
            location="Testville, Zone",
            cuisine="Chinese",
            rating=4.0,
            cost_band=BudgetBand.low,
            url=None,
        )
        for i in range(25)
    ]
    write_sqlite(db, rows)
    store = RestaurantStore(db)
    settings = Settings(_env_file=None, database_path=str(db), recommend_candidate_cap=10)
    body = RecommendRequest(
        location="testville",
        budget=BudgetBand.low,
        cuisine="chinese",
        min_rating=3.0,
        top_n=50,
    )
    resp = deterministic_recommend(store, body, settings=settings)
    assert resp.meta.candidate_count == 25
    assert len(resp.results) == 10
