import pickle
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.dependencies.db import get_db
from app.schemas.response import APIResponse
from app.schemas.document import VectorStatisticsResponse, ProviderHealthResponse
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.vector_embedding import VectorEmbedding
from app.services.search_service import search_service
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store_service
from app.config.settings import settings

router = APIRouter(prefix="/search", tags=["search"])

class SearchRequest(BaseModel):
    query: str = Field(..., example="Ecosystem quarterly target report summaries")
    top_k: Optional[int] = Field(None, example=5)
    filters: Optional[Dict[str, Any]] = Field(None, example={
        "filename": "quarterly_report.pdf",
        "document_type": "pdf"
    })


@router.post("/similarity", response_model=APIResponse[List[Dict[str, Any]]])
def query_similarity_search(payload: SearchRequest):
    """
    Executes a vector search over all document chunk texts using the configured embedding and vector drivers.
    """
    top_k = payload.top_k or settings.TOP_K_RESULTS
    results = search_service.search_similarity(
        query_text=payload.query,
        top_k=top_k,
        filters=payload.filters
    )
    return APIResponse(success=True, data=results, message="Similarity query execution successful.")


@router.post("/vector", response_model=APIResponse[List[Dict[str, Any]]])
def query_vector_search(payload: SearchRequest, db: Session = Depends(get_db)):
    """
    Retrieves similarity results complete with raw float vector coordinates.
    """
    top_k = payload.top_k or settings.TOP_K_RESULTS
    matches = search_service.search_similarity(
        query_text=payload.query,
        top_k=top_k,
        filters=payload.filters
    )
    
    # Enrich results with float vectors
    results = []
    for match in matches:
        chunk_id = match["chunk_id"]
        embedding_rec = db.query(VectorEmbedding).filter(VectorEmbedding.chunk_id == chunk_id).first()
        
        vector = []
        if embedding_rec:
            try:
                vector = pickle.loads(embedding_rec.embedding_data)
            except Exception:
                vector = json.loads(embedding_rec.embedding_data.decode("utf-8"))

        match_copy = dict(match)
        match_copy["vector"] = vector
        match_copy["vector_dimension"] = len(vector)
        match_copy["embedding_provider"] = embedding_rec.embedding_provider if embedding_rec else "unknown"
        results.append(match_copy)

    return APIResponse(success=True, data=results, message="Vector query execution successful.")


@router.get("/statistics", response_model=APIResponse[VectorStatisticsResponse])
def get_vector_statistics(db: Session = Depends(get_db)):
    """
    Returns document and chunk totals alongside dimensions and configuration variables.
    """
    total_docs = db.query(Document).count()
    total_chunks = db.query(DocumentChunk).count()
    total_vectors = db.query(VectorEmbedding).count()
    
    # Resolve vector dimension from database or configuration
    dimension = 1536
    sample_embedding = db.query(VectorEmbedding).first()
    if sample_embedding:
        dimension = sample_embedding.vector_dimension

    stats = VectorStatisticsResponse(
        total_documents=total_docs,
        total_chunks=total_chunks,
        total_vectors=total_vectors,
        vector_dimension=dimension,
        embedding_provider=settings.EMBEDDING_PROVIDER,
        vector_provider=settings.VECTOR_PROVIDER
    )
    return APIResponse(success=True, data=stats)


@router.get("/providers/health", response_model=APIResponse[ProviderHealthResponse])
def check_providers_health():
    """
    Checks connection status and parameter limits for the configured embedding and vector drivers.
    """
    # Verify Embedding Provider Health
    emb_provider_name = settings.EMBEDDING_PROVIDER.lower()
    emb_healthy = True
    emb_error = None
    
    try:
        # Check standard mock or attempt connection
        provider = embedding_service.get_provider()
        provider.generate_embeddings(["health_check"])
    except Exception as e:
        emb_healthy = False
        emb_error = str(e)

    # Verify Vector Store Health
    vec_provider_name = settings.VECTOR_PROVIDER.lower()
    vec_healthy = True
    vec_error = None
    
    try:
        store = vector_store_service.get_store()
        store.count()
    except Exception as e:
        vec_healthy = False
        vec_error = str(e)

    details = {
        "embedding_model": settings.EMBEDDING_MODEL,
        "sqlite_db": "test.db",
        "embedding_error": emb_error,
        "vector_error": vec_error
    }

    health_data = ProviderHealthResponse(
        embedding_provider=emb_provider_name,
        embedding_healthy=emb_healthy,
        vector_provider=vec_provider_name,
        vector_healthy=vec_healthy,
        details=details
    )
    
    success = emb_healthy and vec_healthy
    return APIResponse(
        success=success,
        data=health_data,
        message="Search provider health checked."
    )
