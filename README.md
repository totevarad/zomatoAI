# AI-powered restaurant recommender (Zomato-style exercise)

Python **3.11+** service that combines the [Hugging Face Zomato-style dataset](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) with **[Groq](https://groq.com/)** for ranked, natural-language explanations when `GROQ_API_KEY` is set; otherwise recommendations stay fully deterministic.

- Product intent: [docs/problemStatement.md](docs/problemStatement.md)
- System design: [docs/architecture.md](docs/architecture.md)
- Build plan: [docs/implementation-plan.md](docs/implementation-plan.md)
- Edge cases: [docs/edgecase.md](docs/edgecase.md)

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` only on your machine; do not commit real secrets. Optional: set `HF_TOKEN` for higher Hugging Face Hub rate limits during ingest. For AI ranking, set **`GROQ_API_KEY`** (and optionally **`GROQ_MODEL`**); see [Groq console](https://console.groq.com/).

## Groq (Phase 4)

When **`GROQ_API_KEY`** is present (or legacy **`LLM_API_KEY`**), `POST /recommend` sends the capped candidate list to Groq **Chat Completions** with `response_format: json_object` when supported, merges `restaurant_id` + explanations back onto **SQLite rows only**, and sets `meta.phase` to **`llm`**. If Groq errors or returns invalid JSON after an internal retry, the API falls back to deterministic ordering and sets `meta.phase` to **`deterministic`** with a short `meta.message`.

Environment variables: `GROQ_API_KEY`, `GROQ_MODEL` (default `llama-3.3-70b-versatile`), optional `GROQ_TIMEOUT_SECONDS`, `GROQ_TEMPERATURE`, `GROQ_JSON_MODE`.

## Data ingest (Phase 2)

**CLI (recommended for CI or refreshing the DB):**

```powershell
python -m app.ingest
```

This downloads the dataset, normalizes rows, and writes SQLite to `data/restaurants.sqlite` (override with `DATABASE_PATH` in `.env`).

**On first API boot:** if the SQLite file is missing, the app runs the same ingest automatically (can take tens of seconds and needs network access). If ingest fails, `GET /store/info` returns `ingest_error` and `row_count` stays `0`.

### HF → canonical column mapping

| Hugging Face column | Canonical field | Notes |
|---------------------|-----------------|--------|
| `url` (+ `name`, `address`) | `restaurant_id` | SHA-256 hex, first 16 chars, keyed primarily by `url` when present. |
| `name` | `name` | Trimmed; empty rows dropped. |
| `location` + `listed_in(city)` | `location` | `"{neighborhood}, {city_slot}"` — both from the dataset; used for substring search (e.g. “Banashankari”). |
| `cuisines` | `cuisine` | Trimmed; empty → `"Unknown"`. |
| `rate` | `rating` | Parses strings like `4.1/5`; `NEW`, `-`, unparsable → row dropped. |
| `approx_cost(for two people)` | `cost_band` | Digits only (commas stripped); missing → row dropped. Mapped: ≤400 **low**, 401–800 **medium**, ≥801 **high** (INR “for two”). |

### Rows dropped (cleaning rules)

Documented also in `app/ingest.py` module docstring:

1. Blank `name`.
2. No numeric rating from `rate`.
3. Missing / non-numeric `approx_cost(for two people)`.
4. Blank combined `location` after trimming both neighborhood and `listed_in(city)`.

**Typical scale (current HF revision):** about **51,717** raw training rows → about **41k** usable rows after cleaning (exact count depends on the dataset revision).

### Store verification

With the server running (or in Python using `TestClient` as a **context manager** so lifespan runs):

```http
GET http://127.0.0.1:8000/store/info
```

Example response shape: `{ "database_path": "...", "row_count": 41418, "ingest_error": null }`.

Programmatic filter smoke test (case-insensitive substring on `location`):

```python
from pathlib import Path
from app.config import get_settings
from app.store import RestaurantStore

store = RestaurantStore(Path(get_settings().database_path))
rows = store.find_by_location_substring("Banashankari", limit=5)
```

## Run locally

1. **Activate the virtual environment**:
   ```powershell
   .venv\Scripts\activate
   ```
2. **Start the server**:
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   *Note: If `uvicorn` is not found, use `.venv\Scripts\python -m uvicorn app.main:app ...`*

- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Store Info**: [http://127.0.0.1:8000/store/info](http://127.0.0.1:8000/store/info)
- **OpenAPI (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Web UI**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)


## Example request (`POST /recommend`)

Hard filters (substring, case-insensitive):

- **location** must appear inside the stored `location` string (`instr`, not `LIKE`, so `%` / `_` in input are literal).
- **cuisine** must appear inside the stored `cuisine` string (supports multi-label rows such as `"North Indian, Chinese"`).
- **budget** must match `cost_band` exactly (`low` / `medium` / `high`).
- **min_rating** requires `rating >= min_rating`.

Then: sort by **rating** descending, **cost_band** high → medium → low, **name** ascending; keep at most **`RECOMMEND_CANDIDATE_CAP`** (default 30) rows. If **Groq** is configured, the model returns JSON `ranked_ids` + `items[].explanation` (grounded to those ids only); otherwise explanations are a fixed deterministic line.

This dataset is mostly **Bangalore** area names (not literal “Delhi” city strings). Example that can match:

```powershell
curl -s -X POST http://127.0.0.1:8000/recommend ^
  -H "Content-Type: application/json" ^
  -d "{\"location\":\"Banashankari\",\"budget\":\"medium\",\"cuisine\":\"Chinese\",\"min_rating\":3.5,\"top_n\":5}"
```

If nothing matches, `results` is empty and `meta.message` explains next steps.

## Tests

```powershell
python -m pytest tests -v
```

## Stack

| Piece | Choice |
|-------|--------|
| Runtime | Python 3.11+ |
| HTTP API | FastAPI |
| Validation / types | Pydantic v2 |
| Config | pydantic-settings (env + optional `.env` file) |
| Dataset | `datasets` (Hugging Face) |
| Local store | SQLite (`data/restaurants.sqlite`) + indexes on `lower(location)`, `lower(cuisine)`, `rating` |
| Recommend | SQLite filter + cap; optional **Groq** JSON ranking + merge |
| Tests | `pytest` |
