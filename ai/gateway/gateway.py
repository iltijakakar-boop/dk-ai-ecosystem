from typing import Any, Dict, List

from .router import Router


class ModelGateway:
    """Public façade for all model interactions.

    The class methods delegate to a selected provider via the ``Router``.  The
    router consults the circuit‑breaker before choosing a provider.  After a
    successful call the router records success; on exception it records a
    failure which may trip the circuit breaker.
    """

    _router = Router()

    @classmethod
    def chat(cls, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        provider = cls._router.select_provider()
        provider_name = provider.__class__.__name__.lower()
        try:
            response = provider.chat(messages, **kwargs)
            cls._router.record_success(provider_name)
            return response
        except Exception as exc:
            cls._router.record_failure(provider_name, exc)
            raise

    @classmethod
    def embed(cls, texts: List[str], **kwargs) -> List[List[float]]:
        provider = cls._router.select_provider()
        provider_name = provider.__class__.__name__.lower()
        try:
            embeddings = provider.embed(texts, **kwargs)
            cls._router.record_success(provider_name)
            return embeddings
        except Exception as exc:
            cls._router.record_failure(provider_name, exc)
            raise

    @classmethod
    def stream(cls, messages: List[Dict[str, Any]], **kwargs) -> Any:
        provider = cls._router.select_provider()
        provider_name = provider.__class__.__name__.lower()
        try:
            generator = provider.stream(messages, **kwargs)
            # Stream is lazy; record success after first item if possible.
            # For simplicity we record success immediately.
            cls._router.record_success(provider_name)
            return generator
        except Exception as exc:
            cls._router.record_failure(provider_name, exc)
            raise

    @classmethod
    def health_check(cls, provider_name: str = None) -> Dict[str, Any]:
        """Return health info for a specific provider or the default one.

        If ``provider_name`` is omitted the default provider (as configured) is
        used.
        """
        if provider_name:
            provider = ProviderRegistry.get(provider_name)
        else:
            provider = cls._router.select_provider()
        return provider.health_check()
