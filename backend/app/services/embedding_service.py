import abc
import time
import random
import hashlib
import httpx
from typing import List, Optional
from app.config.settings import settings
from app.core.logging.logger import logger

class EmbeddingProvider(abc.ABC):
    """
    Abstract interface for generating vector embeddings from text blocks.
    """
    @abc.abstractmethod
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        pass


class MockEmbedding(EmbeddingProvider):
    """
    Mock embedding provider generating deterministic, seed-based floating-point vectors (1536 dim).
    """
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        dimension = 1536
        results = []
        for text in texts:
            # Seed generator based on MD5 checksum hash of the text
            seed_val = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) % 1000000
            rng = random.Random(seed_val)
            vector = [rng.uniform(-1.0, 1.0) for _ in range(dimension)]
            results.append(vector)
        return results


class GeminiEmbedding(EmbeddingProvider):
    """
    Adapter invoking Google Generative Language Embeddings API.
    """
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured in settings.")

        model = settings.EMBEDDING_MODEL
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={api_key}"
        
        results = []
        for text in texts:
            payload = {
                "model": f"models/{model}",
                "content": {"parts": [{"text": text}]}
            }
            with httpx.Client() as client:
                res = client.post(url, json=payload, timeout=settings.API_TIMEOUT)
            res.raise_for_status()
            vector = res.json()["embedding"]["values"]
            results.append(vector)
        return results


class OpenAIEmbedding(EmbeddingProvider):
    """
    Adapter invoking OpenAI Embeddings completions API.
    """
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured in settings.")

        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "text-embedding-ada-002",
            "input": texts
        }
        with httpx.Client() as client:
            res = client.post(url, json=payload, headers=headers, timeout=settings.API_TIMEOUT)
        res.raise_for_status()
        
        data = res.json()["data"]
        # Maintain batch indices
        sorted_data = sorted(data, key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]


class EmbeddingService:
    """
    Global service coordinator managing provider resolution, BATCH_SIZE splits,
    and exponential backoff retries.
    """
    def get_provider(self) -> EmbeddingProvider:
        provider_name = settings.EMBEDDING_PROVIDER.lower()
        if provider_name == "gemini":
            return GeminiEmbedding()
        elif provider_name == "openai":
            return OpenAIEmbedding()
        return MockEmbedding()

    def get_embeddings_with_retry(self, texts: List[str]) -> List[List[float]]:
        """
        Processes text lists in BATCH_SIZE chunks, resolving embeddings with up to 3 retries.
        """
        if not texts:
            return []

        provider = self.get_provider()
        batch_size = getattr(settings, "BATCH_SIZE", 32)
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            
            max_retries = 3
            backoff_seconds = 1.0
            
            for attempt in range(max_retries):
                try:
                    embeddings = provider.generate_embeddings(batch_texts)
                    all_embeddings.extend(embeddings)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Embedding generation failed after {max_retries} attempts: {e}")
                        raise e
                    logger.warning(
                        f"Embedding call failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {backoff_seconds} seconds..."
                    )
                    time.sleep(backoff_seconds)
                    backoff_seconds *= 2.0  # Exponential increase

        return all_embeddings

# Global EmbeddingService instance
embedding_service = EmbeddingService()
