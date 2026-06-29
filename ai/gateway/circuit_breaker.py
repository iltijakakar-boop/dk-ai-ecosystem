import time
from typing import Dict

from backend.app.config.settings import settings


class CircuitBreaker:
    """Very simple circuit‑breaker implementation per provider.

    * CLOSED – normal operation.
    * OPEN – provider considered unhealthy; requests are short‑circuited.
    * HALF‑OPEN – after a timeout we allow a single trial request.
    """

    def __init__(self):
        self.state: Dict[str, str] = {}  # provider_name -> state
        self.failure_count: Dict[str, int] = {}
        self.last_failure_ts: Dict[str, float] = {}
        self.max_retries = getattr(settings, "MAX_PROVIDER_RETRIES", 3)
        self.reset_timeout = 30  # seconds before trying HALF‑OPEN

    def _init_provider(self, name: str):
        if name not in self.state:
            self.state[name] = "CLOSED"
            self.failure_count[name] = 0
            self.last_failure_ts[name] = 0.0

    def is_closed(self, name: str) -> bool:
        self._init_provider(name)
        if self.state[name] == "OPEN":
            # Check if timeout expired to move to HALF‑OPEN
            if time.time() - self.last_failure_ts[name] > self.reset_timeout:
                self.state[name] = "HALF-OPEN"
        return self.state[name] == "CLOSED" or self.state[name] == "HALF-OPEN"

    def record_success(self, name: str):
        self._init_provider(name)
        # On success we move to CLOSED and reset counters
        self.state[name] = "CLOSED"
        self.failure_count[name] = 0
        self.last_failure_ts[name] = 0.0

    def record_failure(self, name: str, exc: Exception):
        self._init_provider(name)
        self.failure_count[name] += 1
        self.last_failure_ts[name] = time.time()
        if self.failure_count[name] >= self.max_retries:
            self.state[name] = "OPEN"
        else:
            self.state[name] = "HALF-OPEN"
        # Optionally log the exception; omitted for brevity

    def get_state(self, name: str) -> str:
        self._init_provider(name)
        return self.state[name]
