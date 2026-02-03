"""Application configuration settings."""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str
    timescaledb_enabled: bool = True

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl_signal: int = 3600  # 1 hour
    redis_cache_ttl_price: int = 300  # 5 minutes
    redis_cache_ttl_fundamental: int = 86400  # 24 hours

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # API Settings
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://localhost:8080,http://localhost:5173"

    # Rate Limiting
    rate_limit_per_minute: int = 100

    # Data Sources
    # Yahoo Finance (yfinance) - Primary and only data source
    yfinance_enabled: bool = True
    # NGX support disabled - no API available
    ngx_api_enabled: bool = False
    ngx_api_url: str = ""

    # Environment
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Security
    api_key_secret: str = ""
    
    # OpenAI (for future use - enhanced explanations, sentiment analysis)
    openai_api_key: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
