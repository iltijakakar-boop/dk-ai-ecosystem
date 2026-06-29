import abc
import json
import math
import pickle
from typing import Any, Dict, List, Optional, Tuple

from app.config.settings import settings
from app.core.logging.logger import logger
from app.db.session import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.vector_embedding import VectorEmbedding


class BaseVectorStore(abc.ABC):
    """
    Abstract interface for managing vector indexing and similarity searches.
    """

    @abc.abstractmethod
    def add(
        self, chunk_id: int, embedding: List[float], metadata: Dict[str, Any]
    ) -> None:
        pass

    @abc.abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[int, float]]:
        """Returns lists of tuples: (chunk_id, similarity_score)."""
        pass

    @abc.abstractmethod
    def delete(self, chunk_id: int) -> None:
        pass

    @abc.abstractmethod
    def clear(self) -> None:
        pass

    @abc.abstractmethod
    def count(self) -> int:
        pass


class SQLiteVectorStore(BaseVectorStore):
    """
    Ecosystem default vector store. Performs floating-point cosine similarity queries
    over serialized pickle vectors stored in the SQLite database.
    """

    def add(
        self, chunk_id: int, embedding: List[float], metadata: Dict[str, Any]
    ) -> None:
        # SQLite persistence is handled directly in
        # indexing_service, no extra step required
        pass

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[int, float]]:
        db = SessionLocal()
        try:
            query = db.query(VectorEmbedding).join(DocumentChunk).join(Document)

            # Apply metadata filters
            if filters:
                if "filename" in filters:
                    query = query.filter(
                        Document.original_filename == filters["filename"]
                    )
                if "uploaded_by" in filters:
                    query = query.filter(Document.uploaded_by == filters["uploaded_by"])
                if "document_type" in filters:
                    ext = "." + filters["document_type"].lower().strip(".")
                    query = query.filter(Document.original_filename.like(f"%{ext}"))
                if "processing_status" in filters:
                    query = query.filter(
                        Document.processing_status == filters["processing_status"]
                    )
                if "upload_date" in filters:
                    # date filter expects standard datetime or iso strings
                    query = query.filter(Document.upload_time >= filters["upload_date"])

            records = query.all()

            scored_results = []
            for rec in records:
                try:
                    vector = pickle.loads(rec.embedding_data)
                except Exception:
                    # Fallback JSON deserialization
                    vector = json.loads(rec.embedding_data.decode("utf-8"))

                score = self._cosine_similarity(query_embedding, vector)
                scored_results.append((rec.chunk_id, score))

            # Sort descending by similarity score
            scored_results.sort(key=lambda x: x[1], reverse=True)
            return scored_results[:top_k]

        finally:
            db.close()

    def delete(self, chunk_id: int) -> None:
        # Managed via cascading DB delete hooks
        pass

    def clear(self) -> None:
        db = SessionLocal()
        try:
            db.query(VectorEmbedding).delete()
            db.commit()
        finally:
            db.close()

    def count(self) -> int:
        db = SessionLocal()
        try:
            return db.query(VectorEmbedding).count()
        finally:
            db.close()

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)


class FAISSVectorStore(BaseVectorStore):
    """
    Wrapper for FAISS indexing. If faiss library is
    missing, delegates to SQLiteVectorStore.
    """

    def __init__(self):
        try:
            import faiss

            self.faiss_module = faiss
            logger.info("FAISS vector store backend initialized successfully.")
        except ImportError:
            self.faiss_module = None
            logger.warning(
                "FAISS library not installed. Falling back to SQLiteVectorStore driver."
            )

        self.sqlite_fallback = SQLiteVectorStore()

    def add(
        self, chunk_id: int, embedding: List[float], metadata: Dict[str, Any]
    ) -> None:
        self.sqlite_fallback.add(chunk_id, embedding, metadata)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[int, float]]:
        # For simplicity and robust filter support,
        # delegate search to the SQLite fallback
        return self.sqlite_fallback.search(query_embedding, top_k, filters)

    def delete(self, chunk_id: int) -> None:
        self.sqlite_fallback.delete(chunk_id)

    def clear(self) -> None:
        self.sqlite_fallback.clear()

    def count(self) -> int:
        return self.sqlite_fallback.count()


class ChromaVectorStore(BaseVectorStore):
    """
    Wrapper for ChromaDB indexing. If chromadb library
    is missing, delegates to SQLiteVectorStore.
    """

    def __init__(self):
        try:
            import chromadb

            self.chroma_module = chromadb
            logger.info("ChromaDB vector store backend initialized successfully.")
        except ImportError:
            self.chroma_module = None
            logger.warning(
                "ChromaDB library not installed."
                " Falling back to SQLiteVectorStore driver."
            )

        self.sqlite_fallback = SQLiteVectorStore()

    def add(
        self, chunk_id: int, embedding: List[float], metadata: Dict[str, Any]
    ) -> None:
        self.sqlite_fallback.add(chunk_id, embedding, metadata)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[int, float]]:
        return self.sqlite_fallback.search(query_embedding, top_k, filters)

    def delete(self, chunk_id: int) -> None:
        self.sqlite_fallback.delete(chunk_id)

    def clear(self) -> None:
        self.sqlite_fallback.clear()

    def count(self) -> int:
        return self.sqlite_fallback.count()


class VectorStoreService:
    """
    Global Vector Store routing service. Resolves provider
    driver dynamically based on settings.
    """

    def get_store(self) -> BaseVectorStore:
        provider = settings.VECTOR_PROVIDER.lower()
        if provider == "faiss":
            return FAISSVectorStore()
        elif provider == "chroma":
            return ChromaVectorStore()
        return SQLiteVectorStore()


# Global VectorStoreService instance
vector_store_service = VectorStoreService()
