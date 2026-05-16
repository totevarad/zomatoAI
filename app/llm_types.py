"""Pydantic models for Groq JSON ranking output (architecture §7.2)."""

from pydantic import BaseModel, Field


class LLMRankItem(BaseModel):
    restaurant_id: str
    explanation: str = ""


class LLMRankResponse(BaseModel):
    ranked_ids: list[str] = Field(default_factory=list)
    items: list[LLMRankItem] = Field(default_factory=list)
