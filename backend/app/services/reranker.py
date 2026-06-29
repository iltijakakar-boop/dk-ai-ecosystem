import abc
from typing import List, Dict, Any
from app.config.settings import settings
from app.core.logging.logger import logger

class BaseReranker(abc.ABC):
    @abc.abstractmethod
    def rerank(self, query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass


class MockReranker(BaseReranker):
    """
    Ranks context blocks based on overlapping term occurrences and returns adjusted score mappings.
    """
    def rerank(self, query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        words = [w.lower() for w in query.split() if len(w) > 2]
        if not words or not chunks:
            return chunks

        reranked = []
        for item in chunks:
            text = item["text"].lower()
            overlap_count = sum(1 for w in words if w in text)
            
            # Adjust score using a term overlap boost factor
            boost = (overlap_count / len(words)) * 0.2
            new_score = item["score"] + boost
            
            item_copy = dict(item)
            item_copy["score"] = min(new_score, 1.0) # Cap at 1.0
            item_copy["rerank_score"] = item_copy["score"]
            reranked.append(item_copy)

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked


class GeminiReranker(BaseReranker):
    """
    Stubs for Google Gemini reranking. Delegates to MockReranker when API is mock.
    """
    def __init__(self):
        self.mock_fallback = MockReranker()

    def rerank(self, query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.info("Executing Gemini Reranker (Mock Fallback)...")
        return self.mock_fallback.rerank(query, chunks)


class OpenAIReranker(BaseReranker):
    """
    Stubs for OpenAI reranking. Delegates to MockReranker when API is mock.
    """
    def __init__(self):
        self.mock_fallback = MockReranker()

    def rerank(self, query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.info("Executing OpenAI Reranker (Mock Fallback)...")
        return self.mock_fallback.rerank(query, chunks)


class RerankerService:
    def get_reranker(self) -> BaseReranker:
        provider = settings.RERANKING_PROVIDER.lower()
        if provider == "gemini":
            return GeminiReranker()
        elif provider == "openai":
            return OpenAIReranker()
        return MockReranker()

# Global RerankerService instance
reranker_service = RerankerService()
