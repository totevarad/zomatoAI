from enum import Enum

from pydantic import BaseModel, Field, field_validator


class BudgetBand(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RecommendRequest(BaseModel):
    """POST /recommend body — aligned with docs/architecture.md §8."""

    location: str = Field(..., min_length=1, max_length=200)
    budget: BudgetBand
    cuisine: str = Field(..., min_length=1, max_length=200)
    min_rating: float = Field(..., ge=0.0, le=5.0)
    notes: str | None = Field(default=None, max_length=4000)
    top_n: int = Field(default=5, ge=1, le=50)

    @field_validator("location", "cuisine")
    @classmethod
    def strip_not_empty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("must not be empty or whitespace-only")
        return s


class RestaurantResult(BaseModel):
    restaurant_id: str
    name: str
    cuisine: str
    rating: float
    cost_band: BudgetBand
    explanation: str = ""


class RecommendMeta(BaseModel):
    candidate_count: int = 0
    model: str | None = None
    phase: str = "deterministic"
    message: str | None = None


class RecommendResponse(BaseModel):
    results: list[RestaurantResult] = Field(default_factory=list)
    meta: RecommendMeta = Field(default_factory=RecommendMeta)
