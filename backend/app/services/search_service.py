import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.db.session import SessionLocal
from app.models.document_chunk import DocumentChunk
from app.models.document import Document
from app.models.monitoring_model import ExecutionMetric
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store_service
from app.config.settings import settings
from app.core.logging.logger import logger

class SearchService:
    """
    Coordinates vector queries: generates query embeddings, applies filters,
    invokes vector store drivers, maps results to document chunks, and audits performance.
    """
    
    def search_similarity(
        self, 
        query_text: str, 
        top_k: int = 5, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes a similarity search, returning matching text blocks with scoring metrics.
        """
        db = SessionLocal()
        start_time = time.perf_counter()
        
        try:
            # 1. Generate Query Vector (utilizing Mock or standard Embedding provider)
            query_vectors = embedding_service.get_embeddings_with_retry([query_text])
            if not query_vectors:
                return []
            query_vector = query_vectors[0]

            # 2. Query Selected Vector Store Driver
            store = vector_store_service.get_store()
            scored_matches = store.search(
                query_embedding=query_vector, 
                top_k=top_k, 
                filters=filters
            )

            # 3. Resolve Chunk details from Database
            results = []
            for chunk_id, score in scored_matches:
                chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
                if chunk:
                    doc = db.query(Document).filter(Document.id == chunk.document_id).first()
                    results.append({
                        "chunk_id": chunk.id,
                        "text": chunk.text,
                        "score": score,
                        "token_count": chunk.token_count,
                        "document_id": chunk.document_id,
                        "filename": doc.original_filename if doc else "unknown",
                        "mime_type": doc.mime_type if doc else "unknown"
                    })

            # Record search latency metrics
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            self._log_search_metric(db, duration_ms)

            return results

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise e
        finally:
            db.close()

    def _log_search_metric(self, db, duration_ms: float) -> None:
        """
        Saves query execution latencies in the monitoring registry.
        """
        try:
            metric = ExecutionMetric(
                component="search:similarity",
                execution_time=duration_ms,
                success=True,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(metric)
            db.commit()
        except Exception as err:
            logger.warning(f"Failed to record search performance telemetry: {err}")

# Global SearchService instance
search_service = SearchService()
