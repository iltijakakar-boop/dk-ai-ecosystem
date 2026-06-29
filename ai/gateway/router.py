from .provider_registry import ProviderRegistry
from .circuit_breaker import CircuitBreaker
from .base_provider import BaseProvider
from backend.app.config.settings import settings


class Router:
    """Selects an appropriate provider based on routing policies.

    For the first iteration we implement a simple policy that always returns the
    default provider unless it is in an OPEN state, in which case we fall back
    to the mock provider (or raise an error if none are healthy).
    """

    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
        # Future: load routing policies from settings (e.g., cost, latency)

    def select_provider(self) -> BaseProvider:
        """Return an instantiated provider ready to handle a request.

        The circuit breaker is consulted first. If the default provider is
        unhealthy (circuit OPEN), we try the fallback mock provider.
        """
        default_name = getattr(settings, "DEFAULT_PROVIDER", "mock")
        if not self.circuit_breaker.is_closed(default_name):
            # Default provider is unhealthy – try fallback
            fallback = ProviderRegistry.get("mock")
            return fallback
        return ProviderRegistry.get(default_name)

    def record_success(self, provider_name: str):
        self.circuit_breaker.record_success(provider_name)

    def record_failure(self, provider_name: str, exc: Exception):
        self.circuit_breaker.record_failure(provider_name, exc)
