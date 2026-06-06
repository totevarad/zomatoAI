import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import get_settings
from app.store import RestaurantStore
from app.recommend_service import deterministic_recommend
from app.schemas import RecommendRequest, BudgetBand

def run_test_case(store, settings, name, payload):
    print(f"\n==================================================")
    print(f"TEST CASE: {name}")
    print(f"Payload: {payload}")
    print(f"==================================================")
    
    try:
        request_body = RecommendRequest(
            location=payload["location"],
            cuisine=payload["cuisine"],
            budget=BudgetBand(payload["budget"]),
            top_n=payload.get("top_n", 5),
            min_rating=payload.get("min_rating", 3.5),
            notes=payload.get("notes")
        )
        
        response = deterministic_recommend(store, request_body, settings=settings)
        
        print(f"Candidates found in database: {response.meta.candidate_count}")
        print(f"Phase: {response.meta.phase} (Model: {response.meta.model})")
        if response.meta.message:
            print(f"Metadata message: {response.meta.message}")
            
        print("\nResults returned:")
        for idx, res in enumerate(response.results):
            print(f"  {idx + 1}. {res.name} (*{res.rating})")
            print(f"     Cuisine: {res.cuisine} | Cost: {res.cost_band.value.upper()}")
            print(f"     URL: {res.url}")
            print(f"     Image URL: {res.image_url[:60] + '...' if res.image_url else 'None'}")
            print(f"     AI Explanation: {res.explanation[:150]}...")
            print("-" * 30)
            
    except Exception as e:
        print(f"Test case failed: {e}")

def main():
    settings = get_settings()
    db_path = Path(settings.database_path)
    
    print(f"Database Path: {db_path.absolute()}")
    if not db_path.is_file():
        print("Error: SQLite database file does not exist. Run ingestion first.")
        sys.exit(1)
        
    store = RestaurantStore(db_path)
    print(f"Store initialized. Total row count: {store.row_count()}")
    
    # 1. Indiranagar Italian Med-budget Test
    run_test_case(store, settings, "Indiranagar Italian (Medium Budget)", {
        "location": "Indiranagar",
        "cuisine": "Italian",
        "budget": "medium",
        "min_rating": 4.0,
        "top_n": 3,
        "notes": "cozy place for date night"
    })

    # 2. Koramangala Chinese Low-budget Test
    run_test_case(store, settings, "Koramangala Chinese (Low Budget)", {
        "location": "Koramangala",
        "cuisine": "Chinese",
        "budget": "low",
        "min_rating": 3.5,
        "top_n": 3,
        "notes": "quick dinner"
    })

    # 3. Jayanagar Cafe Med-budget Test
    run_test_case(store, settings, "Jayanagar Cafe (Medium Budget)", {
        "location": "Jayanagar",
        "cuisine": "Cafe",
        "budget": "medium",
        "min_rating": 4.2,
        "top_n": 2,
        "notes": "good coffee, quiet study spot"
    })

if __name__ == "__main__":
    main()
