import abc
from typing import Any, Dict, List


class BaseProvider(abc.ABC):
    """Abstract interface that all model providers must implement.

    Each concrete provider should implement the methods below. Unsupported
    capabilities may raise ``NotImplementedError``.
    """

    @abc.abstractmethod
    def chat(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Generate a chat completion.

        Parameters
        ----------
        messages: List[Dict[str, Any]]
            List of ``{"role": str, "content": str}`` messages.
        **kwargs: Any
            Additional provider‑specific parameters (e.g., temperature).

        Returns
        -------
        Dict[str, Any]
            Provider‑specific response payload.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def embed(self, texts: List[str], **kwargs) -> List[List[float]]:
        """Return embeddings for a list of texts.

        Parameters
        ----------
        texts: List[str]
            Texts to embed.
        **kwargs: Any
            Provider‑specific options.

        Returns
        -------
        List[List[float]]
            Embedding vectors for each input text.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def stream(self, messages: List[Dict[str, Any]], **kwargs) -> Any:
        """Yield streamed token chunks for a chat request.

        The concrete return type is provider dependent – typically an async
        generator yielding strings or delta objects.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Return health information for the provider.

        Should include at minimum a ``status`` key with values ``"healthy"`` or
        ``"unhealthy"`` and may contain additional metrics such as latency.
        """
        raise NotImplementedError
