from typing import Dict, Type

from .base_provider import BaseProvider
from .mock_provider import MockProvider
from backend.app.config.settings import settings


class ProviderRegistry:
    """Singleton registry for model providers.

    Providers are stored by name. The registry is populated with built‑in
    providers (currently only ``mock``) and can be extended at runtime.
    """

    _providers: Dict[str, Type[BaseProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: Type[BaseProvider]):
        cls._providers[name] = provider_cls

    @classmethod
    def get(cls, name: str) -> BaseProvider:
        provider_cls = cls._providers.get(name)
        if provider_cls is None:
            raise ValueError(f"Provider '{name}' not found in registry")
        return provider_cls()

    @classmethod
    def default(cls) -> BaseProvider:
        default_name = getattr(settings, "DEFAULT_PROVIDER", "mock")
        return cls.get(default_name)


# Register built‑in providers
ProviderRegistry.register("mock", MockProvider)
