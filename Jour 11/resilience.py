"""
fetchers/resilience.py
──────────────────────
Two resilience patterns:

  RateLimiter    — sliding window, limits N calls per second
  CircuitBreaker — 3 states (CLOSED → OPEN → HALF-OPEN)
                   isolates a failing API automatically
"""

import asyncio
import time
import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# Rate Limiter
@dataclass
class RateLimiter:
    """
    Allows at most `max_calls` requests per `period` seconds.
    Uses a sliding window + asyncio.Lock for thread safety.
    """
    max_calls: int
    period:    float = 1.0
    _calls:    list  = field(default_factory=list)
    _lock:     asyncio.Lock = field(default_factory=asyncio.Lock)

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            # remove timestamps outside the current window
            self._calls = [t for t in self._calls if now - t < self.period]

            if len(self._calls) >= self.max_calls:
                sleep_for = self.period - (now - self._calls[0])
                if sleep_for > 0:
                    logger.debug(f"Rate limiter sleeping {sleep_for:.2f}s")
                    await asyncio.sleep(sleep_for)

            self._calls.append(time.monotonic())


# Circuit Breaker
class CBState(Enum):
    CLOSED    = "CLOSED"      # normal — requests go through
    OPEN      = "OPEN"        # failing — requests blocked
    HALF_OPEN = "HALF-OPEN"   # recovery probe — 1 request allowed


@dataclass
class CircuitBreaker:
    """
    Tracks failures for one API.

    CLOSED   → normal operation
    OPEN     → after `failure_threshold` consecutive failures,
               blocks all requests for `recovery_timeout` seconds
    HALF-OPEN→ after timeout, lets one request through to probe
               • success → back to CLOSED
               • failure → back to OPEN
    """
    name:              str
    failure_threshold: int   = 5
    recovery_timeout:  float = 30.0

    _failures:    int     = field(default=0, init=False)
    _state:       CBState = field(default=CBState.CLOSED, init=False)
    _opened_at:   float   = field(default=0.0, init=False)

    # Public API
    @property
    def state(self) -> str:
        return self._state.value

    @property
    def failures(self) -> int:
        return self._failures

    def is_available(self) -> bool:
        """Returns True if a request should be attempted."""
        if self._state == CBState.CLOSED:
            return True

        if self._state == CBState.OPEN:
            if time.monotonic() - self._opened_at >= self.recovery_timeout:
                self._transition(CBState.HALF_OPEN)
                return True
            return False  # still blocked

        # HALF-OPEN: allow exactly one probe
        return True

    def record_success(self) -> None:
        self._failures = 0
        self._transition(CBState.CLOSED)

    def record_failure(self) -> None:
        self._failures += 1
        if self._state == CBState.HALF_OPEN:
            # probe failed → reopen
            self._transition(CBState.OPEN)
        elif self._failures >= self.failure_threshold:
            self._transition(CBState.OPEN)

    # Internal
    def _transition(self, new_state: CBState) -> None:
        if new_state != self._state:
            logger.warning(f"[{self.name}] Circuit Breaker: {self._state.value} → {new_state.value}")
            self._state = new_state
            if new_state == CBState.OPEN:
                self._opened_at = time.monotonic()
