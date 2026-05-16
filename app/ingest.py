"""
Load ManikaSaini/zomato-restaurant-recommendation from Hugging Face,
normalize to canonical fields, and persist to SQLite.

Null / invalid handling (see README § Data ingestion):
- Drop rows with missing or blank `name`.
- Drop rows with no parseable numeric rating (`rate` is None, "NEW", "-", etc.).
- Drop rows with missing `approx_cost(for two people)` (cannot assign cost_band).
- `cuisines` empty -> replaced with "Unknown" so cuisine column stays filterable.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path

from datasets import load_dataset

from app.config import Settings, get_settings
from app.records import RestaurantRecord
from app.schemas import BudgetBand

DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"

_RATE_PATTERN = re.compile(r"^([\d.]+)\s*/\s*5\s*$")
_RATE_FALLBACK = re.compile(r"([\d.]+)")


def _parse_rating(raw: object) -> float | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.upper() == "NEW" or s == "-":
        return None
    m = _RATE_PATTERN.match(s)
    if m:
        return float(m.group(1))
    m = _RATE_FALLBACK.search(s)
    if m:
        v = float(m.group(1))
        return v if 0 <= v <= 5 else None
    return None


def _parse_cost_for_two(raw: object) -> int | None:
    if raw is None:
        return None
    s = str(raw).replace(",", "").strip()
    if not s.isdigit():
        return None
    return int(s)


def _cost_to_band(cost: int) -> BudgetBand:
    # Documented thresholds (INR approx for two); adjust if product rules change.
    if cost <= 400:
        return BudgetBand.low
    if cost <= 800:
        return BudgetBand.medium
    return BudgetBand.high


def _make_restaurant_id(url: str | None, name: str, address: str | None) -> str:
    key = (url or "").strip() or f"{name.strip()}|{(address or '').strip()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def _compose_location(neighborhood: str | None, city_slot: str | None) -> str:
    parts: list[str] = []
    for p in (neighborhood, city_slot):
        if p and (t := str(p).strip()):
            parts.append(t)
    return ", ".join(parts) if parts else ""


def raw_row_to_record(row: dict) -> RestaurantRecord | None:
    name = (row.get("name") or "").strip()
    if not name:
        return None

    rating = _parse_rating(row.get("rate"))
    if rating is None:
        return None

    cost_val = _parse_cost_for_two(row.get("approx_cost(for two people)"))
    if cost_val is None:
        return None

    location = _compose_location(row.get("location"), row.get("listed_in(city)"))
    if not location:
        return None

    cuisines = (row.get("cuisines") or "").strip()
    if not cuisines:
        cuisines = "Unknown"

    url = row.get("url")
    if url is not None:
        url = str(url).strip() or None

    rid = _make_restaurant_id(url, name, row.get("address"))

    return RestaurantRecord(
        restaurant_id=rid,
        name=name,
        location=location,
        cuisine=cuisines,
        rating=rating,
        cost_band=_cost_to_band(cost_val),
        url=url,
    )


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode = WAL;
        CREATE TABLE IF NOT EXISTS restaurants (
            restaurant_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            cuisine TEXT NOT NULL,
            rating REAL NOT NULL,
            cost_band TEXT NOT NULL,
            url TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_restaurants_location_lower
            ON restaurants (lower(location));
        CREATE INDEX IF NOT EXISTS idx_restaurants_cuisine_lower
            ON restaurants (lower(cuisine));
        CREATE INDEX IF NOT EXISTS idx_restaurants_rating ON restaurants (rating DESC);
        """
    )


def write_sqlite(db_path: Path, records: list[RestaurantRecord]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DROP TABLE IF EXISTS restaurants")
        _init_schema(conn)
        conn.executemany(
            """
            INSERT INTO restaurants (restaurant_id, name, location, cuisine, rating, cost_band, url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    r.restaurant_id,
                    r.name,
                    r.location,
                    r.cuisine,
                    r.rating,
                    r.cost_band.value,
                    r.url,
                )
                for r in records
            ],
        )
        conn.commit()
    finally:
        conn.close()


def ingest_to_sqlite(db_path: Path, settings: Settings | None = None) -> tuple[int, int]:
    """
    Returns (kept_rows, raw_rows) where raw_rows is HF train split size after fetch.
    """
    settings = settings or get_settings()
    kwargs: dict = {}
    if settings.hf_token:
        kwargs["token"] = settings.hf_token
    ds = load_dataset(DATASET_ID, split="train", **kwargs)
    raw_len = len(ds)
    records: list[RestaurantRecord] = []
    for row in ds:
        rec = raw_row_to_record(row)
        if rec is not None:
            records.append(rec)
    write_sqlite(db_path, records)
    return len(records), raw_len


def main() -> None:
    settings = get_settings()
    path = Path(settings.database_path)
    kept, raw = ingest_to_sqlite(path, settings)
    print(f"Ingest complete: {kept} rows kept of {raw} raw (see README for drop rules).")
    print(f"SQLite file: {path.resolve()}")


if __name__ == "__main__":
    main()
