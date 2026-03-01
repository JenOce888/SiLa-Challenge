"""
Config.py
─────────
Loads all settings from the .env file using python-dotenv.
A single Config object is imported everywhere in the project.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()  # reads .env file and injects into os.environ


@dataclass(frozen=True)
class Config:
    # API keys
    owm_api_key:  str = os.getenv("OWM_API_KEY", "")
    news_api_key: str = os.getenv("NEWS_API_KEY", "")

    # Query settings
    github_username: str = os.getenv("GITHUB_USERNAME", "torvalds")
    city:            str = os.getenv("CITY", "Yaounde")
    news_query:      str = os.getenv("NEWS_QUERY", "artificial intelligence")

    # Rate limiter
    rate_limit_calls:  int   = int(os.getenv("RATE_LIMIT_CALLS", 5))
    rate_limit_period: float = float(os.getenv("RATE_LIMIT_PERIOD", 1.0))

    # Retry policy
    retry_count:   int   = int(os.getenv("RETRY_COUNT", 3))
    retry_backoff: float = float(os.getenv("RETRY_BACKOFF", 1.5))

    # Dashboard
    refresh_interval: int = int(os.getenv("REFRESH_INTERVAL", 30))  # seconds
    cache_ttl:        int = int(os.getenv("CACHE_TTL", 300))         # seconds


# Singleton — import this everywhere
config = Config()
