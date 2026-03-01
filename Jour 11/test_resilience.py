"""
tests/test_resilience.py
────────────────────────
Tests for RateLimiter and CircuitBreaker.
Run with: pytest tests/ -v
"""

import asyncio
import time

import pytest

from fetchers.resilience import RateLimiter, CircuitBreaker, CBState



#  RateLimiter tests

class TestRateLimiter:

    @pytest.mark.asyncio
    async def test_allows_calls_within_limit(self):
        """Should not delay when under the limit."""
        limiter = RateLimiter(max_calls=5, period=1.0)
        start = time.monotonic()
        for _ in range(5):
            await limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.5, "Should complete 5 calls instantly"

    @pytest.mark.asyncio
    async def test_blocks_when_limit_exceeded(self):
        """The 6th call should be delayed into the next window."""
        limiter = RateLimiter(max_calls=2, period=0.3)
        for _ in range(2):
            await limiter.acquire()
        start = time.monotonic()
        await limiter.acquire()   # this one must wait
        elapsed = time.monotonic() - start
        assert elapsed >= 0.2, "Should have waited for the rate window"

    @pytest.mark.asyncio
    async def test_sliding_window_resets(self):
        """After the period passes, the window resets and calls go through."""
        limiter = RateLimiter(max_calls=2, period=0.2)
        for _ in range(2):
            await limiter.acquire()
        await asyncio.sleep(0.25)           # wait for window to expire
        start = time.monotonic()
        await limiter.acquire()             # should be instant now
        assert time.monotonic() - start < 0.1



#  CircuitBreaker tests

class TestCircuitBreaker:

    def test_initial_state_is_closed(self):
        cb = CircuitBreaker(name="TestAPI")
        assert cb.state == "CLOSED"
        assert cb.is_available() is True

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(name="TestAPI", failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == "OPEN"
        assert cb.is_available() is False

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker(name="TestAPI", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.failures == 0
        assert cb.state == "CLOSED"

    def test_transitions_to_half_open_after_timeout(self):
        cb = CircuitBreaker(name="TestAPI", failure_threshold=1, recovery_timeout=0.1)
        cb.record_failure()
        assert cb.state == "OPEN"
        time.sleep(0.15)                    # wait for recovery timeout
        assert cb.is_available() is True    # triggers HALF-OPEN
        assert cb.state == "HALF-OPEN"

    def test_half_open_success_closes_circuit(self):
        cb = CircuitBreaker(name="TestAPI", failure_threshold=1, recovery_timeout=0.1)
        cb.record_failure()
        time.sleep(0.15)
        cb.is_available()                   # move to HALF-OPEN
        cb.record_success()
        assert cb.state == "CLOSED"

    def test_half_open_failure_reopens_circuit(self):
        cb = CircuitBreaker(name="TestAPI", failure_threshold=1, recovery_timeout=0.1)
        cb.record_failure()
        time.sleep(0.15)
        cb.is_available()                   # move to HALF-OPEN
        cb.record_failure()
        assert cb.state == "OPEN"

    def test_blocked_when_open(self):
        cb = CircuitBreaker(name="TestAPI", failure_threshold=1, recovery_timeout=60)
        cb.record_failure()
        assert cb.is_available() is False   # blocked for 60s
