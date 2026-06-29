import abc
import httpx
from typing import Any, Dict, List, Optional
from app.config.settings import settings
from app.core.logging import logger


class BaseProvider(abc.ABC):
    """
    Abstract base class for LLM API providers.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.DEFAULT_MODEL

    @abc.abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs,
    ) -> str:
        """
        Generates text completion based on prompt and system prompt.
        """
        pass


class GeminiProvider(BaseProvider):
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs,
    ) -> str:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("GEMINI_API_KEY not set. Using Gemini mock response.")
            return f"[Gemini Mock Response for model={self.model_name}] Received prompt: {prompt}"

        # Call Google Gemini API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={api_key}"

        contents = {"parts": [{"text": prompt}]}
        payload: Dict[str, Any] = {"contents": [contents]}

        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        try:
            with httpx.Client(timeout=settings.API_TIMEOUT) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                res_data = response.json()
                # Parse candidates
                text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                return text
        except Exception as e:
            logger.exception("Error calling Gemini API:")
            raise RuntimeError(f"Gemini API failure: {str(e)}")


class OpenAIProvider(BaseProvider):
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs,
    ) -> str:
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            logger.warning("OPENAI_API_KEY not set. Using OpenAI mock response.")
            return f"[OpenAI Mock Response for model={self.model_name}] Received prompt: {prompt}"

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": settings.MAX_OUTPUT_TOKENS,
        }

        try:
            with httpx.Client(timeout=settings.API_TIMEOUT) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                res_data = response.json()
                return res_data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.exception("Error calling OpenAI API:")
            raise RuntimeError(f"OpenAI API failure: {str(e)}")


class AnthropicProvider(BaseProvider):
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs,
    ) -> str:
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set. Using Anthropic mock response.")
            return f"[Anthropic Mock Response for model={self.model_name}] Received prompt: {prompt}"

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model_name,
            "max_tokens": settings.MAX_OUTPUT_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with httpx.Client(timeout=settings.API_TIMEOUT) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                res_data = response.json()
                return res_data["content"][0]["text"]
        except Exception as e:
            logger.exception("Error calling Anthropic API:")
            raise RuntimeError(f"Anthropic API failure: {str(e)}")


class OllamaProvider(BaseProvider):
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs,
    ) -> str:
        base_url = settings.OLLAMA_BASE_URL or "http://localhost:11434"
        url = f"{base_url}/api/chat"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": self.model_name, "messages": messages, "stream": False}

        try:
            with httpx.Client(timeout=settings.API_TIMEOUT) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                res_data = response.json()
                return res_data["message"]["content"]
        except Exception as e:
            logger.warning(
                f"Failed to connect to local Ollama server: {str(e)}. Falling back to Ollama mock."
            )
            return f"[Ollama Mock Response for model={self.model_name}] Received prompt: {prompt}"


class OpenRouterProvider(BaseProvider):
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Any]] = None,
        **kwargs,
    ) -> str:
        api_key = settings.OPENROUTER_API_KEY
        if not api_key:
            logger.warning(
                "OPENROUTER_API_KEY not set. Using OpenRouter mock response."
            )
            return f"[OpenRouter Mock Response for model={self.model_name}] Received prompt: {prompt}"

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": self.model_name, "messages": messages}

        try:
            with httpx.Client(timeout=settings.API_TIMEOUT) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                res_data = response.json()
                return res_data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.exception("Error calling OpenRouter API:")
            raise RuntimeError(f"OpenRouter API failure: {str(e)}")


class ProviderManager:
    """
    Manages loading and resolving pluggable LLM provider instances.
    """

    def __init__(self):
        self._provider_registry: Dict[str, type[BaseProvider]] = {
            "gemini": GeminiProvider,
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "ollama": OllamaProvider,
            "openrouter": OpenRouterProvider,
        }
        self._cached_providers: Dict[str, BaseProvider] = {}

    def get_provider(
        self, provider_name: str, model_name: Optional[str] = None
    ) -> BaseProvider:
        """
        Gets or creates a provider instance by name.
        """
        name_lower = provider_name.lower()
        if name_lower not in self._provider_registry:
            raise ValueError(
                f"Unknown AI Provider: {provider_name}. Supported: {list(self._provider_registry.keys())}"
            )

        cache_key = f"{name_lower}:{model_name or ''}"
        if cache_key not in self._cached_providers:
            provider_cls = self._provider_registry[name_lower]
            self._cached_providers[cache_key] = provider_cls(model_name=model_name)

        return self._cached_providers[cache_key]


# Global Provider Manager instance
provider_manager = ProviderManager()
