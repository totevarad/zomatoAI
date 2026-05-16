from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load secrets and service config from the environment only (no secrets in code)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    hf_token: str | None = None
    database_path: str = "data/restaurants.sqlite"
    #: Max rows after hard filters before projection / Groq payload (architecture §4).
    recommend_candidate_cap: int = 30

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    groq_timeout_seconds: float = 60.0
    groq_temperature: float = 0.25
    groq_json_mode: bool = True

    #: Deprecated aliases (same as Groq) for older `.env` files.
    llm_api_key: str | None = None
    llm_model: str | None = None

    def resolved_groq_api_key(self) -> str | None:
        k = (self.groq_api_key or self.llm_api_key or "").strip()
        return k or None

    def resolved_groq_model(self) -> str:
        m = (self.groq_model or self.llm_model or "llama-3.3-70b-versatile").strip()
        return m or "llama-3.3-70b-versatile"


@lru_cache
def get_settings() -> Settings:
    return Settings()
