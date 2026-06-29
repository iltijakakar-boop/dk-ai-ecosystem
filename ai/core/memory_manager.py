import abc
import os
import json
from typing import Any, Dict, List, Optional
from app.core.logging import logger

class BaseMemory(abc.ABC):
    """
    Base memory interface for AI agents.
    """
    @abc.abstractmethod
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieves conversation history as a list of role/content dictionaries."""
        pass

    @abc.abstractmethod
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Adds a message to the conversation history."""
        pass

    @abc.abstractmethod
    def clear(self, session_id: str) -> None:
        """Clears memory for the given session."""
        pass


class SessionMemory:
    """
    Short-term key-value storage scoped to active agent sessions.
    """
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def set(self, session_id: str, key: str, value: Any) -> None:
        if session_id not in self._store:
            self._store[session_id] = {}
        self._store[session_id][key] = value

    def get(self, session_id: str, key: str, default: Any = None) -> Any:
        return self._store.get(session_id, {}).get(key, default)

    def clear(self, session_id: str) -> None:
        if session_id in self._store:
            self._store[session_id].clear()


class ConversationMemory(BaseMemory):
    """
    Dialogue history tracker that retains system, assistant, and user rounds.
    """
    def __init__(self):
        self._history: Dict[str, List[Dict[str, str]]] = {}

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        return self._history.get(session_id, [])

    def add_message(self, session_id: str, role: str, content: str) -> None:
        if session_id not in self._history:
            self._history[session_id] = []
        self._history[session_id].append({"role": role, "content": content})

    def clear(self, session_id: str) -> None:
        if session_id in self._history:
            self._history[session_id] = []


class LongTermMemory(BaseMemory):
    """
    Database-backed persistent memory system. Fallback to file-based JSON storage.
    """
    def __init__(self, storage_path: str = "database/long_term_memory.json"):
        self.storage_path = storage_path
        self._cache: Dict[str, List[Dict[str, str]]] = {}
        self._load_from_disk()

    def _load_from_disk(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load long term memory from {self.storage_path}: {e}")
                self._cache = {}

    def _save_to_disk(self):
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save long term memory to {self.storage_path}: {e}")

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        return self._cache.get(session_id, [])

    def add_message(self, session_id: str, role: str, content: str) -> None:
        if session_id not in self._cache:
            self._cache[session_id] = []
        self._cache[session_id].append({"role": role, "content": content})
        self._save_to_disk()

    def clear(self, session_id: str) -> None:
        if session_id in self._cache:
            self._cache[session_id] = []
            self._save_to_disk()


class VectorMemory:
    """
    Placeholder/stub for semantic search/vector memory stores.
    """
    def __init__(self):
        self._vector_store: Dict[str, List[Dict[str, Any]]] = {}

    def add_embedding(self, session_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if session_id not in self._vector_store:
            self._vector_store[session_id] = []
        self._vector_store[session_id].append({
            "text": text,
            "metadata": metadata or {},
            "vector_placeholder": [0.0] * 128  # Placeholder embedding
        })
        logger.info(f"Mock embedded and stored in VectorMemory: {text[:30]}...")

    def search(self, session_id: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Simulates vector search. Performs simple text search/substring check.
        """
        records = self._vector_store.get(session_id, [])
        if not records:
            return []
        
        # Simple fallback text search match
        matches = []
        for r in records:
            if query.lower() in r["text"].lower():
                matches.append(r)
        
        # If no text search matches, return first top_k
        if not matches:
            matches = records[:top_k]
            
        return matches[:top_k]
