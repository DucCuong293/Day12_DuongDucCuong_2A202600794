"""
Production config — 12-Factor: tất cả từ environment variables.

Dùng pydantic-settings để validate tự động.
Production sẽ fail ngay khi thiếu config quan trọng.
"""
import os
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    """Application settings — tất cả đọc từ env vars hoặc .env file."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"
    debug: bool = False

    # App
    app_name: str = "Production AI Agent"
    app_version: str = "1.0.0"

    # LLM
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # Security — BẮT BUỘC thay trong production
    agent_api_key: str = "dev-key-change-me-in-production"
    allowed_origins: str = "*"

    # Rate limiting
    rate_limit_per_minute: int = 10

    # Budget — monthly per user
    monthly_budget_usd: float = 10.0

    # Storage
    redis_url: str = "redis://localhost:6379/0"

    # Logging
    log_level: str = "INFO"

    model_config = {
        "env_file": ".env.local",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @field_validator("agent_api_key")
    @classmethod
    def validate_api_key_in_production(cls, v):
        env = os.getenv("ENVIRONMENT", "development")
        if env == "production" and v == "dev-key-change-me-in-production":
            raise ValueError(
                "AGENT_API_KEY must be changed from default in production!"
            )
        return v

    def get_allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS từ comma-separated string."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
