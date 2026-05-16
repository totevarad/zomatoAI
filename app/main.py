import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.ingest import ingest_to_sqlite
from app.recommend_service import deterministic_recommend
from app.schemas import RecommendRequest, RecommendResponse
from app.store import RestaurantStore


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("zomato-ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    db_path = Path(settings.database_path)
    app.state.store = RestaurantStore(db_path)
    app.state.ingest_error = None
    if not db_path.is_file():
        try:
            ingest_to_sqlite(db_path, settings)
        except Exception as exc:  # noqa: BLE001 — surface any HF/SQLite failure at runtime
            app.state.ingest_error = repr(exc)
    yield


app = FastAPI(
    title="Restaurant recommender",
    description="Phase 4: Groq-backed ranking when GROQ_API_KEY is set; otherwise deterministic.",
    version="0.4.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        "Method: %s Path: %s Status: %s Duration: %.2fs",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    return response


@app.get("/health")
def health() -> dict[str, str]:
    """Smoke test and deploy probes."""
    return {"status": "ok"}


@app.get("/store/info")
def store_info(request: Request) -> dict:
    """Row count and DB path for operators (Phase 2 exit criteria)."""
    store: RestaurantStore = request.app.state.store
    settings = get_settings()
    return {
        "database_path": str(Path(settings.database_path).resolve()),
        "row_count": store.row_count(),
        "ingest_error": getattr(request.app.state, "ingest_error", None),
    }


@app.post("/recommend", response_model=RecommendResponse)
def recommend(body: RecommendRequest, request: Request) -> RecommendResponse:
    """Filter + cap + deterministic sort; Phase 4 will optionally replace explanations via LLM."""
    settings = get_settings()
    store: RestaurantStore = request.app.state.store
    return deterministic_recommend(store, body, settings=settings)


# Phase 5: UI entry point and static assets
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_index():
    return FileResponse("static/index.html")
