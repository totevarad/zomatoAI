import pytest
from pathlib import Path
from app.config import Settings
from app.ingest import write_sqlite
from app.records import RestaurantRecord
from app.recommend_service import deterministic_recommend
from app.schemas import BudgetBand, RecommendRequest
from app.store import RestaurantStore

def _setup_bangalore_db(path: Path):
    rows = [
        RestaurantRecord(
            restaurant_id="b1",
            name="Indiranagar Cafe",
            location="Indiranagar, Bangalore",
            cuisine="Cafe",
            rating=4.5,
            cost_band=BudgetBand.medium,
            url=None,
        ),
        RestaurantRecord(
            restaurant_id="b2",
            name="Koramangala Italian",
            location="Koramangala, Bangalore",
            cuisine="Italian",
            rating=4.0,
            cost_band=BudgetBand.high,
            url=None,
        ),
        RestaurantRecord(
            restaurant_id="b3",
            name="Jayanagar Dosa",
            location="Jayanagar, Bangalore",
            cuisine="South Indian",
            rating=4.8,
            cost_band=BudgetBand.low,
            url=None,
        )
    ]
    write_sqlite(path, rows)

def test_bangalore_area_filtering(tmp_path: Path):
    """Verify that searching for a specific Bangalore area works."""
    db = tmp_path / "bangalore.sqlite"
    _setup_bangalore_db(db)
    store = RestaurantStore(db)
    settings = Settings(_env_file=None, database_path=str(db), recommend_candidate_cap=10)
    
    # Test Indiranagar
    request = RecommendRequest(
        location="Indiranagar",
        cuisine="Cafe",
        budget=BudgetBand.medium,
        min_rating=4.0,
        top_n=5
    )
    response = deterministic_recommend(store, request, settings=settings)
    assert len(response.results) == 1
    assert response.results[0].name == "Indiranagar Cafe"

def test_bangalore_city_wide_search(tmp_path: Path):
    """Verify that searching for 'Bangalore' returns multiple areas."""
    db = tmp_path / "bangalore.sqlite"
    _setup_bangalore_db(db)
    store = RestaurantStore(db)
    settings = Settings(_env_file=None, database_path=str(db), recommend_candidate_cap=10)
    
    request = RecommendRequest(
        location="Bangalore",
        cuisine=None,
        budget=None,
        min_rating=0.0,
        top_n=10
    )
    response = deterministic_recommend(store, request, settings=settings)
    assert len(response.results) == 3
