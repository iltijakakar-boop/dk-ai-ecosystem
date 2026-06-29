from typing import Any, Dict, List

from .base_provider import BaseProvider


class MockProvider(BaseProvider):
    """A simple in‑memory mock provider used for development and tests.

    It returns deterministic canned responses for chat, embeddings and health
    checks.  No external network calls are made.
    """

    def __init__(self):
        self.call_count = 0

    def chat(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        self.call_count += 1
        # Echo back the last user message with a *mock* prefix.
        user_msg = messages[-1]["content"] if messages else ""
        return {
            "id": f"mock-chat-{self.call_count}",
            "model": "mock-chat-model",
            "choices": [{"message": {"role": "assistant", "content": f"Mock response to: {user_msg}"}}],
            "usage": {"prompt_tokens": len(user_msg.split()), "completion_tokens": 5, "total_tokens": len(user_msg.split()) + 5},
        }

    def embed(self, texts: List[str], **kwargs) -> List[List[float]]:
        # Return a simple deterministic vector (e.g., length 3) for each text.
        vectors = []
        for idx, txt in enumerate(texts, start=1):
            vectors.append([float(idx), float(len(txt)), 0.1])
        return vectors

    def stream(self, messages: List[Dict[str, Any]], **kwargs):
        # Simulate a streaming generator yielding partial responses.
        user_msg = messages[-1]["content"] if messages else ""
        response = f"Mock streaming response to: {user_msg}"
        for token in response.split():
            yield token + " "

    def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "provider": "mock", "latency_ms": 1}
