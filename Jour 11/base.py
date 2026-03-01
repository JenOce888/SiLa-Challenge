"""
fetchers/base.py
────────────────
Generic async HTTP GET with:
  • connect + read timeout split
  • exponential backoff retry
  • rate limiter integration
  • circuit breaker integration
  • structured logging
"""

import asyncio
import logging
from typing import Any, Optional

import aiohttp

from .resilience import RateLimiter, CircuitBreaker
from config import config

logger = logging.getLogger(__name__)


async def fetch(
    session:         aiohttp.ClientSession,
    url:             str,
    *,
    params:          dict | None = None,
    headers:         dict | None = None,
    rate_limiter:    RateLimiter | None = None,
    circuit_breaker: CircuitBreaker | None = None,
    api_name:        str = "API",
) -> Optional[Any]:
    """
    Performs a GET request and returns parsed JSON, or None on failure.

    Retry policy  : exponential backoff — waits backoff^attempt seconds
    Timeout       : connect_timeout=5s  |  read_timeout=10s  (separate)
    Rate limiting : waits if too many recent calls
    Circuit breaker: skips call entirely if the API is OPEN
    """
    # Circuit breaker check 
    if circuit_breaker and not circuit_breaker.is_available():
        logger.warning(f"[{api_name}] Circuit OPEN — request skipped")
        return None

    timeout = aiohttp.ClientTimeout(sock_connect=5, sock_read=10)

    for attempt in range(1, config.retry_count + 1):
        try:
            if rate_limiter:
                await rate_limiter.acquire()

            logger.debug(f"[{api_name}] GET {url} (attempt {attempt})")

            async with session.get(url, params=params, headers=headers, timeout=timeout) as resp:

                # Rate limited by the server
                if resp.status == 429:
                    wait = config.retry_backoff ** attempt
                    logger.warning(f"[{api_name}] 429 Too Many Requests — retry in {wait:.1f}s")
                    await asyncio.sleep(wait)
                    continue

                resp.raise_for_status()
                data = await resp.json()

                if circuit_breaker:
                    circuit_breaker.record_success()

                logger.info(f"[{api_name}] ✓ {resp.status} {url}")
                return data

        except aiohttp.ClientResponseError as e:
            logger.error(f"[{api_name}] HTTP {e.status}: {e.message}")
            if circuit_breaker:
                circuit_breaker.record_failure()
            _maybe_retry(api_name, attempt, e)

        except asyncio.TimeoutError:
            logger.error(f"[{api_name}] Timeout on attempt {attempt}")
            if circuit_breaker:
                circuit_breaker.record_failure()
            _maybe_retry(api_name, attempt, "timeout")

        except aiohttp.ClientError as e:
            logger.error(f"[{api_name}] Network error: {e}")
            if circuit_breaker:
                circuit_breaker.record_failure()
            _maybe_retry(api_name, attempt, e)

        if attempt < config.retry_count:
            await asyncio.sleep(config.retry_backoff ** attempt)

    logger.error(f"[{api_name}] All {config.retry_count} attempts failed.")
    return None


def _maybe_retry(api_name: str, attempt: int, error: Any) -> None:
    remaining = config.retry_count - attempt
    if remaining > 0:
        logger.info(f"[{api_name}] {remaining} retries remaining after: {error}")
