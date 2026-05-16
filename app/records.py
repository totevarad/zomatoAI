"""Canonical restaurant row for the local store (architecture §5)."""

from pydantic import BaseModel, Field

from app.schemas import BudgetBand


class RestaurantRecord(BaseModel):
    restaurant_id: str
    name: str
    location: str
    cuisine: str
    rating: float
    cost_band: BudgetBand
    url: str | None = Field(default=None, description="Source Zomato URL when present.")
