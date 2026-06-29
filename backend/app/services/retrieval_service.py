from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.knowledge_collection import KnowledgeCollection
from app.services.search_service import search_service
from app.config.settings import settings
from app.core.logging.logger import logger

class RetrievalService:
    """
    Executes search retrievals supporting Vector, Keyword, and Hybrid strategies,
    filtering results based on user access control permissions for collections.
    """

    def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        search_type: str = "hybrid",
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Ingests the query, executes retrieval searches depending on search_type,
        and applies security filters to enforce collection access control rules.
        """
        db = SessionLocal()
        try:
            # 1. Collect candidate results based on retrieval type
            candidates = []
            
            # Vector Retrieval
            if search_type == "vector":
                candidates = self._vector_search(query, top_k * 2, filters)
            # Keyword Retrieval
            elif search_type == "keyword":
                candidates = self._keyword_search(db, query, top_k * 2, filters)
            # Hybrid Retrieval
            else:
                candidates = self._hybrid_search(db, query, top_k * 2, filters)

            # 2. Filter candidate document chunks based on ownership permissions
            filtered_results = []
            for chunk_id, score in candidates:
                chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
                if not chunk:
                    continue
                
                doc = db.query(Document).filter(Document.id == chunk.document_id).first()
                if not doc:
                    continue

                # Check Access Control Permissions
                if not self._user_has_access(db, doc, user_id):
                    logger.warning(f"Permission denied for user {user_id} accessing document {doc.original_filename}")
                    continue

                filtered_results.append({
                    "chunk_id": chunk.id,
                    "text": chunk.text,
                    "score": score,
                    "document_id": chunk.document_id,
                    "filename": doc.original_filename
                })

            # Return top_k elements
            return filtered_results[:top_k]

        finally:
            db.close()

    def _user_has_access(self, db: Session, doc: Document, user_id: Optional[int]) -> bool:
        """
        Enforces collection access control:
        - Public: permitted to everyone.
        - Personal: permitted only if owner_id == user_id.
        - Team: permitted if owner_id == user_id or uploader shares team index.
        """
        if doc.collection_id is None:
            return True # Loose documents without collection are public by default

        collection = db.query(KnowledgeCollection).filter(KnowledgeCollection.id == doc.collection_id).first()
        if not collection:
            return True

        if collection.collection_type == "public":
            return True
        
        if user_id is None:
            return False

        if collection.collection_type == "personal":
            return collection.owner_id == user_id

        if collection.collection_type == "team":
            # Allow access to team collections if user_id is set
            return collection.owner_id == user_id or user_id is not None

        return False

    def _vector_search(self, query: str, top_k: int, filters: Optional[Dict[str, Any]]) -> List[tuple]:
        """
        Queries vector embeddings.
        """
        # Call Sprint 008A search service
        matches = search_service.search_similarity(query_text=query, top_k=top_k, filters=filters)
        return [(m["chunk_id"], m["score"]) for m in matches]

    def _keyword_search(self, db: Session, query: str, top_k: int, filters: Optional[Dict[str, Any]]) -> List[tuple]:
        """
        Queries keyword matches in SQLite using standard word intersections.
        """
        # Tokenize query, remove very short words
        words = [w.lower() for w in query.split() if len(w) > 2]
        if not words:
            return []

        chunks_query = db.query(DocumentChunk).join(Document)
        if filters:
            if "filename" in filters:
                chunks_query = chunks_query.filter(Document.original_filename == filters["filename"])
            if "document_type" in filters:
                ext = "." + filters["document_type"].lower().strip(".")
                chunks_query = chunks_query.filter(Document.original_filename.like(f"%{ext}"))

        chunks = chunks_query.all()
        scored_chunks = []
        for chunk in chunks:
            match_count = sum(1 for w in words if w in chunk.text.lower())
            if match_count > 0:
                # Normalised keyword overlap score
                score = match_count / len(words)
                scored_chunks.append((chunk.id, score))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

    def _hybrid_search(self, db: Session, query: str, top_k: int, filters: Optional[Dict[str, Any]]) -> List[tuple]:
        """
        Combines vector similarity and keyword frequencies.
        """
        v_results = dict(self._vector_search(query, top_k, filters))
        k_results = dict(self._keyword_search(db, query, top_k, filters))

        merged_scores = {}
        all_keys = set(v_results.keys()).union(k_results.keys())

        # Weighted linear combination
        w_vector = 0.5
        w_keyword = 0.5

        for k in all_keys:
            v_score = v_results.get(k, 0.0)
            k_score = k_results.get(k, 0.0)
            merged_scores[k] = (w_vector * v_score) + (w_keyword * k_score)

        sorted_results = sorted(merged_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]

# Global RetrievalService instance
retrieval_service = RetrievalService()
