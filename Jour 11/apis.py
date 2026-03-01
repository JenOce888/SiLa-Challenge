"""
fetchers/apis.py
────────────────
One async function per API:
  fetch_github()  → GitHubData
  fetch_weather() → WeatherData | None
  fetch_news()    → NewsData | None

Each has its own CircuitBreaker instance so failures
are isolated and don't affect the other APIs.
"""

import asyncio
import logging

import aiohttp

from .base import fetch
from .resilience import RateLimiter, CircuitBreaker
from models.types import GitHubData, WeatherData, NewsData
from config import config

logger = logging.getLogger(__name__)

# Shared rate limiter (all APIs share the same pool) 
_rate_limiter = RateLimiter(
    max_calls=config.rate_limit_calls,
    period=config.rate_limit_period,
)

# Per-API circuit breakers
_cb_github  = CircuitBreaker(name="GitHub")
_cb_weather = CircuitBreaker(name="OpenWeatherMap")
_cb_news    = CircuitBreaker(name="NewsAPI")


def get_circuit_breakers() -> dict[str, CircuitBreaker]:
    """Expose breakers so the dashboard can display their state."""
    return {
        "GitHub":        _cb_github,
        "OpenWeatherMap": _cb_weather,
        "NewsAPI":       _cb_news,
    }


# GitHub 
async def fetch_github(session: aiohttp.ClientSession) -> GitHubData:
    base    = "https://api.github.com"
    headers = {"Accept": "application/vnd.github+json"}
    kwargs  = dict(headers=headers, rate_limiter=_rate_limiter,
                   circuit_breaker=_cb_github, api_name="GitHub")

    user_data, repos_data = await asyncio.gather(
        fetch(session, f"{base}/users/{config.github_username}", **kwargs),
        fetch(session, f"{base}/users/{config.github_username}/repos",
              params={"per_page": 5, "sort": "stars"}, **kwargs),
    )
    return GitHubData(user=user_data, repos=repos_data or [])


# OpenWeatherMap
async def fetch_weather(session: aiohttp.ClientSession) -> WeatherData | None:
    return await fetch(
        session,
        "https://api.openweathermap.org/data/2.5/weather",
        params={
            "q":     config.city,
            "appid": config.owm_api_key,
            "units": "metric",
            "lang":  "en",
        },
        rate_limiter=_rate_limiter,
        circuit_breaker=_cb_weather,
        api_name="OpenWeatherMap",
    )


# NewsAPI 
async def fetch_news(session: aiohttp.ClientSession) -> NewsData | None:
    return await fetch(
        session,
        "https://newsapi.org/v2/everything",
        params={
            "q":        config.news_query,
            "apiKey":   config.news_api_key,
            "pageSize": 5,
            "sortBy":   "publishedAt",
            "language": "en",
        },
        rate_limiter=_rate_limiter,
        circuit_breaker=_cb_news,
        api_name="NewsAPI",
    )


# Aggregate: parallel fetch 
async def fetch_all(session: aiohttp.ClientSession):
    """Runs all 3 API calls concurrently."""
    github, weather, news = await asyncio.gather(
        fetch_github(session),
        fetch_weather(session),
        fetch_news(session),
    )
    return {"github": github, "weather": weather, "news": news}
