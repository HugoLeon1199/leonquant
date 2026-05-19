"""Per-domain polite pacing."""

from __future__ import annotations

import threading
import time


class DomainRateLimiter:
    """Simple delay between requests for the same registrable domain."""

    def __init__(self, delay_seconds: float) -> None:
        self.delay_seconds = delay_seconds
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()

    def wait(self, domain: str) -> None:
        if self.delay_seconds <= 0:
            return
        with self._lock:
            now = time.monotonic()
            last = self._last.get(domain, 0.0)
            wait_for = self.delay_seconds - (now - last)
            if wait_for > 0:
                time.sleep(wait_for)
            self._last[domain] = time.monotonic()
