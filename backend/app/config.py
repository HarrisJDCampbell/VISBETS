import os
from dotenv import load_dotenv
from functools import lru_cache
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # BallDontLie API Settings
    BALLDONTLIE_API_KEY: str = ""
    BALLDONTLIE_BASE_URL: str = "https://api.balldontlie.io/v1"

    # NBA API Settings (optional, can be empty for BallDontLie-only usage)
    NBA_API_KEY: str = ""
    NBA_API_HOST: str = ""
    NBA_API_BASE_URL: str = "wss://api.geniussports.com/nbangss/stream"

    # Database Settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./visbets.db"

    # App Settings
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Scraping Settings
    SCRAPING_DELAY: int = 2
    MAX_RETRIES: int = 3

    # Rate Limiting
    API_RATE_LIMIT_PER_MINUTE: int = 60
    API_RATE_LIMIT_DELAY: float = 1.0

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings() 