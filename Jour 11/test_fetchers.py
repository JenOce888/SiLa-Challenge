"""
tests/test_fetchers.py
──────────────────────
Tests for the HTTP fetch layer.
Uses `aioresponses` to mock HTTP calls — no real network needed.

Run with: pytest tests/ -v
"""

import pytest
from aioresponses import aioresponses
import aiohttp

from fetchers.base import fetch
from fetchers.resilience import RateLimiter, CircuitBreaker


MOCK_URL = "https://api.example.com/data"
MOCK_JSON = {"status": "ok", "value": 42}



#  fetch() — success case

class TestFetchSuccess:

    @pytest.mark.asyncio
    async def test_returns_json_on_200(self):
        with aioresponses() as mock:
            mock.get(MOCK_URL, payload=MOCK_JSON, status=200)
            async with aiohttp.ClientSession() as session:
                result = await fetch(session, MOCK_URL, api_name="Test")
        assert result == MOCK_JSON

    @pytest.mark.asyncio
    async def test_records_success_on_circuit_breaker(self):
        cb = CircuitBreaker(name="Test", failure_threshold=3)
        cb.record_failure()                 # one failure before
        with aioresponses() as mock:
            mock.get(MOCK_URL, payload=MOCK_JSON, status=200)
            async with aiohttp.ClientSession() as session:
                await fetch(session, MOCK_URL, circuit_breaker=cb, api_name="Test")
        assert cb.failures == 0             # reset on success



#  fetch() — failure + retry case

class TestFetchRetry:

    @pytest.mark.asyncio
    async def test_retries_on_429_and_succeeds(self):
        """First response is 429, second is 200 — should succeed."""
        with aioresponses() as mock:
            mock.get(MOCK_URL, status=429)
            mock.get(MOCK_URL, payload=MOCK_JSON, status=200)
            async with aiohttp.ClientSession() as session:
                result = await fetch(session, MOCK_URL, api_name="Test")
        assert result == MOCK_JSON

    @pytest.mark.asyncio
    async def test_returns_none_after_all_retries_fail(self):
        with aioresponses() as mock:
            # fail all 3 attempts (default retry_count from config)
            for _ in range(3):
                mock.get(MOCK_URL, status=500)
            async with aiohttp.ClientSession() as session:
                result = await fetch(session, MOCK_URL, api_name="Test")
        assert result is None

    @pytest.mark.asyncio
    async def test_circuit_breaker_records_failure_on_error(self):
        cb = CircuitBreaker(name="Test", failure_threshold=10)
        with aioresponses() as mock:
            for _ in range(3):
                mock.get(MOCK_URL, status=500)
            async with aiohttp.ClientSession() as session:
                await fetch(session, MOCK_URL, circuit_breaker=cb, api_name="Test")
        assert cb.failures > 0



#  fetch() — circuit breaker block

class TestFetchCircuitOpen:

    @pytest.mark.asyncio
    async def test_skips_request_when_circuit_open(self):
        """Open circuit → fetch returns None without making any HTTP call."""
        cb = CircuitBreaker(name="Test", failure_threshold=1, recovery_timeout=60)
        cb.record_failure()                 # opens the circuit
        assert cb.state == "OPEN"

        with aioresponses() as mock:
            # Register a response — it must NOT be called
            mock.get(MOCK_URL, payload=MOCK_JSON, status=200)
            async with aiohttp.ClientSession() as session:
                result = await fetch(session, MOCK_URL, circuit_breaker=cb, api_name="Test")

        assert result is None
        # aioresponses raises if an unmatched call is made, so no assert needed
