"""
TokenOps Configuration
All settings loaded from .env — never hardcode values elsewhere.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # --- API Keys ---
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    groq_api_key: str = Field(default="", env="GROQ_API_KEY")
    tokentamer_api_key: str = Field(default="tokentamer-secret-key-change-me", env="TOKENTAMER_API_KEY")

    # --- Database ---
    database_url: str = Field(default="sqlite:///./tokentamer.db", env="DATABASE_URL")

    # --- Server ---
    host: str = Field(default="127.0.0.1", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=True, env="DEBUG")

    # --- Policy Defaults ---
    max_tokens_per_request: int = Field(default=4096, env="MAX_TOKENS_PER_REQUEST")
    daily_budget_cap_usd: float = Field(default=5.0, env="DAILY_BUDGET_CAP_USD")
    rate_limit_rpm: int = Field(default=50, env="RATE_LIMIT_RPM")
    routing_strategy: str = Field(default="hybrid", env="ROUTING_STRATEGY")

    # --- Cache ---
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    cache_max_size: int = Field(default=500, env="CACHE_MAX_SIZE")

    # --- Model Pricing Table (USD per 1K tokens) ---
    # Add new providers here — no other file needs changing
    model_pricing: dict = {
        # Google Gemini
        "gemini-1.5-flash": {
            "provider": "google",
            "input_per_1k": 0.000075,
            "output_per_1k": 0.0003,
            "tier": "cheap",
            "display_name": "Gemini 1.5 Flash"
        },
        "gemini-1.5-pro": {
            "provider": "google",
            "input_per_1k": 0.00125,
            "output_per_1k": 0.005,
            "tier": "premium",
            "display_name": "Gemini 1.5 Pro"
        },
        "gemini-2.0-flash": {
            "provider": "google",
            "input_per_1k": 0.0001,
            "output_per_1k": 0.0004,
            "tier": "cheap",
            "display_name": "Gemini 2.0 Flash"
        },
        # Groq
        "llama3-8b-8192": {
            "provider": "groq",
            "input_per_1k": 0.00005,
            "output_per_1k": 0.00008,
            "tier": "cheap",
            "display_name": "LLaMA 3 8B (Groq)"
        },
        "llama3-70b-8192": {
            "provider": "groq",
            "input_per_1k": 0.00059,
            "output_per_1k": 0.00079,
            "tier": "premium",
            "display_name": "LLaMA 3 70B (Groq)"
        },
        "mixtral-8x7b-32768": {
            "provider": "groq",
            "input_per_1k": 0.00024,
            "output_per_1k": 0.00024,
            "tier": "mid",
            "display_name": "Mixtral 8x7B (Groq)"
        },
        # Reference-only entries (for cost comparison display)
        "gpt-4o": {
            "provider": "openai",
            "input_per_1k": 0.005,
            "output_per_1k": 0.015,
            "tier": "premium",
            "display_name": "GPT-4o (reference)"
        },
        "gpt-4o-mini": {
            "provider": "openai",
            "input_per_1k": 0.00015,
            "output_per_1k": 0.0006,
            "tier": "cheap",
            "display_name": "GPT-4o Mini (reference)"
        },
    }

    # --- Allowed Models (policy enforcement) ---
    allowed_models: List[str] = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash",
        "llama3-8b-8192",
        "llama3-70b-8192",
        "mixtral-8x7b-32768",
    ]

    # --- Default model per provider ---
    default_cheap_model: str = "llama3-8b-8192"
    default_premium_model: str = "llama3-70b-8192"

    # --- Alert Thresholds ---
    alert_budget_pct_warning: float = 0.80    # warn at 80% of daily budget
    alert_spike_multiplier: float = 10.0      # spike if cost > 10x avg
    alert_error_rate_threshold: float = 0.30  # alert if 30% of recent requests fail
    alert_rate_surge_pct: float = 0.75        # alert if at 75% of rate limit

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Module-level singleton — import this everywhere
settings = get_settings()