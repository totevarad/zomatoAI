"""SQLite access layer for restaurant rows (Phase 2)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.records import RestaurantRecord
from app.schemas import BudgetBand


class RestaurantStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        try:
            cur = conn.cursor()
            cur.execute("SELECT image_url FROM restaurants LIMIT 1")
        except sqlite3.OperationalError:
            try:
                conn.execute("ALTER TABLE restaurants ADD COLUMN image_url TEXT")
                conn.commit()
            except Exception:
                pass
        return conn

    def exists(self) -> bool:
        return self.db_path.is_file()

    def row_count(self) -> int:
        if not self.exists():
            return 0
        conn = self._connect()
        try:
            cur = conn.execute("SELECT COUNT(*) FROM restaurants")
            return int(cur.fetchone()[0])
        finally:
            conn.close()

    def find_by_location_substring(self, needle: str, limit: int = 10) -> list[RestaurantRecord]:
        """Case-insensitive substring match on canonical `location` (for smoke tests / docs)."""
        if not self.exists():
            return []
        needle = needle.strip().lower()
        if not needle:
            return []
        conn = self._connect()
        try:
            cur = conn.execute(
                """
                SELECT restaurant_id, name, location, cuisine, rating, cost_band, url, image_url
                FROM restaurants
                WHERE lower(location) LIKE '%' || ? || '%'
                ORDER BY rating DESC
                LIMIT ?
                """,
                (needle, limit),
            )
            return [_row_to_record(t) for t in cur.fetchall()]
        finally:
            conn.close()

    def filter_candidates(
        self,
        *,
        location_substr: str,
        cuisine_substr: str,
        budget: BudgetBand,
        min_rating: float,
        cap: int,
    ) -> tuple[int, list[RestaurantRecord]]:
        """
        Hard filters: substring on location and cuisine (case-insensitive), exact cost_band, rating >= min_rating.

        Returns (total_match_count, capped_ordered_rows). Ordering: rating DESC, cost_band high→medium→low, name ASC.
        Uses instr() instead of LIKE so user input cannot inject wildcards.
        """
        if not self.exists():
            return 0, []

        loc = location_substr.strip().lower()
        cui = cuisine_substr.strip().lower()
        if not loc or not cui:
            return 0, []

        where = """
            instr(lower(location), ?) > 0
            AND instr(lower(cuisine), ?) > 0
            AND cost_band = ?
            AND rating >= ?
        """
        order = """
            ORDER BY rating DESC,
                CASE cost_band WHEN 'high' THEN 3 WHEN 'medium' THEN 2 ELSE 1 END DESC,
                name ASC
        """
        params_count = (loc, cui, budget.value, min_rating)
        params_fetch = (*params_count, cap)

        conn = self._connect()
        try:
            cur = conn.execute(f"SELECT COUNT(*) FROM restaurants WHERE {where}", params_count)
            total = int(cur.fetchone()[0])
            if total == 0:
                return 0, []
            cur = conn.execute(
                f"""
                SELECT restaurant_id, name, location, cuisine, rating, cost_band, url, image_url
                FROM restaurants
                WHERE {where}
                {order}
                LIMIT ?
                """,
                params_fetch,
            )
            rows = [_row_to_record(t) for t in cur.fetchall()]
            return total, rows
        finally:
            conn.close()

    def update_image_url(self, restaurant_id: str, image_url: str) -> None:
        if not self.exists():
            return
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE restaurants SET image_url = ? WHERE restaurant_id = ?",
                (image_url, restaurant_id),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()


def _row_to_record(t: tuple) -> RestaurantRecord:
    if len(t) == 8:
        rid, name, location, cuisine, rating, cost_band, url, image_url = t
    else:
        rid, name, location, cuisine, rating, cost_band, url = t
        image_url = None
    return RestaurantRecord(
        restaurant_id=rid,
        name=name,
        location=location,
        cuisine=cuisine,
        rating=float(rating),
        cost_band=BudgetBand(cost_band),
        url=url,
        image_url=image_url,
    )

