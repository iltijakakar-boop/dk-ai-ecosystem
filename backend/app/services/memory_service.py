import abc
import os
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.config.settings import settings
from app.db.session import SessionLocal
from app.models.memory_entry import MemoryEntry
from app.models.conversation import Conversation
from app.models.message import Message
from app.core.logging.logger import logger

class BaseMemoryStore(abc.ABC):
    @abc.abstractmethod
    def get(self, key: str, memory_type: str = "long_term") -> Optional[Any]:
        pass

    @abc.abstractmethod
    def set(self, key: str, value: Any, memory_type: str = "long_term", expires_in_seconds: Optional[int] = None) -> None:
        pass

    @abc.abstractmethod
    def delete(self, key: str, memory_type: str = "long_term") -> None:
        pass

    @abc.abstractmethod
    def clear(self, memory_type: str = "long_term") -> None:
        pass


class SQLiteMemoryStore(BaseMemoryStore):
    """
    Database-backed memory entry store.
    """
    def get(self, key: str, memory_type: str = "long_term") -> Optional[Any]:
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            entry = db.query(MemoryEntry).filter(
                MemoryEntry.key == key,
                MemoryEntry.memory_type == memory_type
            ).first()
            
            if entry:
                # Check expiration
                if entry.expires_at and entry.expires_at.replace(tzinfo=timezone.utc) < now:
                    db.delete(entry)
                    db.commit()
                    return None
                return json.loads(entry.value)
            return None
        finally:
            db.close()

    def set(self, key: str, value: Any, memory_type: str = "long_term", expires_in_seconds: Optional[int] = None) -> None:
        db = SessionLocal()
        try:
            expires_at = None
            if expires_in_seconds:
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)

            # Check if exists
            entry = db.query(MemoryEntry).filter(
                MemoryEntry.key == key,
                MemoryEntry.memory_type == memory_type
            ).first()

            serialized_val = json.dumps(value)
            if entry:
                entry.value = serialized_val
                entry.expires_at = expires_at
                entry.created_at = datetime.now(timezone.utc)
            else:
                entry = MemoryEntry(
                    key=key,
                    value=serialized_val,
                    memory_type=memory_type,
                    expires_at=expires_at
                )
                db.add(entry)
            db.commit()
        finally:
            db.close()

    def delete(self, key: str, memory_type: str = "long_term") -> None:
        db = SessionLocal()
        try:
            db.query(MemoryEntry).filter(
                MemoryEntry.key == key,
                MemoryEntry.memory_type == memory_type
            ).delete()
            db.commit()
        finally:
            db.close()

    def clear(self, memory_type: str = "long_term") -> None:
        db = SessionLocal()
        try:
            db.query(MemoryEntry).filter(MemoryEntry.memory_type == memory_type).delete()
            db.commit()
        finally:
            db.close()


class RedisMemoryStore(BaseMemoryStore):
    """
    Redis-backed memory store. Falls back to SQLite if Redis is unavailable.
    """
    def __init__(self):
        self.sqlite_fallback = SQLiteMemoryStore()
        try:
            import redis
            # Simple connection check
            self.client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.client.ping()
            self.active = True
        except Exception:
            logger.warning("Redis is not available. RedisMemoryStore falling back to SQLite.")
            self.active = False

    def get(self, key: str, memory_type: str = "long_term") -> Optional[Any]:
        if not self.active:
            return self.sqlite_fallback.get(key, memory_type)
        rkey = f"mem:{memory_type}:{key}"
        val = self.client.get(rkey)
        return json.loads(val) if val else None

    def set(self, key: str, value: Any, memory_type: str = "long_term", expires_in_seconds: Optional[int] = None) -> None:
        if not self.active:
            return self.sqlite_fallback.set(key, value, memory_type, expires_in_seconds)
        rkey = f"mem:{memory_type}:{key}"
        serialized = json.dumps(value)
        if expires_in_seconds:
            self.client.setex(rkey, expires_in_seconds, serialized)
        else:
            self.client.set(rkey, serialized)

    def delete(self, key: str, memory_type: str = "long_term") -> None:
        if not self.active:
            return self.sqlite_fallback.delete(key, memory_type)
        rkey = f"mem:{memory_type}:{key}"
        self.client.delete(rkey)

    def clear(self, memory_type: str = "long_term") -> None:
        if not self.active:
            return self.sqlite_fallback.clear(memory_type)
        keys = self.client.keys(f"mem:{memory_type}:*")
        if keys:
            self.client.delete(*keys)


class FileMemoryStore(BaseMemoryStore):
    """
    File-backed memory store saving entries in JSON format.
    """
    def __init__(self, file_path: str = "database/long_term_memory.json"):
        self.file_path = file_path
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def _read_file(self) -> Dict[str, Any]:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _write_file(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write file memory: {e}")

    def get(self, key: str, memory_type: str = "long_term") -> Optional[Any]:
        data = self._read_file()
        composite_key = f"{memory_type}:{key}"
        entry = data.get(composite_key)
        if entry:
            # Check expiry
            expires_at_str = entry.get("expires_at")
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str).replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > expires_at:
                    # Remove expired entry
                    del data[composite_key]
                    self._write_file(data)
                    return None
            return entry.get("value")
        return None

    def set(self, key: str, value: Any, memory_type: str = "long_term", expires_in_seconds: Optional[int] = None) -> None:
        data = self._read_file()
        composite_key = f"{memory_type}:{key}"
        expires_at = None
        if expires_in_seconds:
            expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)).isoformat()
        
        data[composite_key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self._write_file(data)

    def delete(self, key: str, memory_type: str = "long_term") -> None:
        data = self._read_file()
        composite_key = f"{memory_type}:{key}"
        if composite_key in data:
            del data[composite_key]
            self._write_file(data)

    def clear(self, memory_type: str = "long_term") -> None:
        data = self._read_file()
        filtered = {k: v for k, v in data.items() if not k.startswith(f"{memory_type}:")}
        self._write_file(filtered)


class MemoryService:
    def get_store(self) -> BaseMemoryStore:
        provider = settings.MEMORY_PROVIDER.lower()
        if provider == "redis":
            return RedisMemoryStore()
        elif provider == "file":
            return FileMemoryStore()
        return SQLiteMemoryStore()

    def compress_conversation_if_needed(self, db: Session, conversation_id: int) -> bool:
        """
        Memory Compression & Summarization:
        Checks messages count or token count thresholds. Compresses older conversation logs
        into the Conversation.summary field and deletes details of older rounds.
        """
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return False

        # Load message list ordered by timestamp
        messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.timestamp.asc()).all()
        total_messages = len(messages)
        total_tokens = sum(m.token_count for m in messages)

        trigger_msg = getattr(settings, "MEMORY_SUMMARY_TRIGGER_MESSAGES", 10)
        trigger_tokens = getattr(settings, "MEMORY_SUMMARY_TRIGGER_TOKENS", 2000)

        if total_messages <= trigger_msg and total_tokens <= trigger_tokens:
            return False

        logger.info(f"Summarizing conversation thread {conversation_id} (rounds: {total_messages}, tokens: {total_tokens})")

        # Keep the last 2 messages (1 user round and 1 assistant round) to preserve immediate conversation flow
        msgs_to_summarize = messages[:-2] if total_messages > 2 else messages
        if not msgs_to_summarize:
            return False

        # Build text description of historical logs
        summary_text_input = []
        for m in msgs_to_summarize:
            summary_text_input.append(f"{m.role.capitalize()}: {m.content}")
        
        input_history = "\n".join(summary_text_input)

        # Generate a structured summary
        summary_result = self._generate_mock_summary(input_history)

        # Update Conversation Summary
        if conv.summary:
            conv.summary = f"{conv.summary}\n\n[Previous Summary Update]: {summary_result}"
        else:
            conv.summary = f"[Conversation Summary]: {summary_result}"

        # Delete summarized messages from database
        summarized_ids = [m.id for m in msgs_to_summarize]
        db.query(Message).filter(Message.id.in_(summarized_ids)).delete(synchronize_session=False)
        db.commit()

        logger.info(f"Conversation {conversation_id} compressed successfully. Deleted {len(summarized_ids)} messages.")
        return True

    def _generate_mock_summary(self, text: str) -> str:
        """
        Deterministic mock summary generator to extract key facts from dialog context.
        """
        lines = text.split("\n")
        facts = []
        for line in lines:
            if "key" in line.lower() or "target" in line.lower() or "goals" in line.lower() or "RAG" in line or "vector" in line:
                facts.append(line.strip())
        
        extracted_facts = "; ".join(facts[:4]) if facts else "General topic discussions."
        return f"Compressed context: User and Assistant discussed development targets. Key elements: {extracted_facts}"

# Global MemoryService instance
memory_service = MemoryService()
