from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Dict, Any, Optional
from app.schemas.response import APIResponse
from app.schemas.rag import RAGChatRequest, RAGChatResponse, RAGExplainResponse
from app.services.rag_engine import rag_engine
from app.services.retrieval_service import retrieval_service
from app.services.context_builder import context_builder
from app.config.settings import settings

router = APIRouter(prefix="/rag", tags=["rag"])

class RAGSearchRequest(RAGChatRequest):
    pass


@router.post("/chat", response_model=APIResponse[RAGChatResponse])
def rag_chat_generation(payload: RAGChatRequest, user_id: Optional[int] = Query(None, description="Requesting User.id")):
    """
    Executes a context-aware chat turn, checking collection permissions and logging turns in the session.
    """
    try:
        res = rag_engine.generate_chat_response(
            session_id=payload.session_id,
            query=payload.query,
            collection_id=payload.collection_id,
            top_k=payload.top_k,
            search_type=payload.search_type,
            user_id=user_id
        )
        data = RAGChatResponse(
            answer=res["answer"],
            session_id=res["session_id"],
            sources=res["sources"]
        )
        return APIResponse(success=True, data=data, message="Chat response generated successfully.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=APIResponse[List[Dict[str, Any]]])
def rag_search_ranked(payload: RAGSearchRequest, user_id: Optional[int] = Query(None, description="Requesting User.id")):
    """
    Ingests a query and retrieves sorted document chunk contexts without calling the LLM.
    """
    try:
        retrieved = retrieval_service.retrieve_context(
            query=payload.query,
            top_k=payload.top_k or settings.TOP_K_RESULTS,
            filters={"collection_id": payload.collection_id} if payload.collection_id is not None else None,
            search_type=payload.search_type,
            user_id=user_id
        )
        return APIResponse(success=True, data=retrieved, message="RAG retrieval search completed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context", response_model=APIResponse[str])
def preview_formatted_context(payload: RAGSearchRequest, user_id: Optional[int] = Query(None, description="Requesting User.id")):
    """
    Retrieves and assembles the formatted context string, respecting size boundaries.
    """
    try:
        retrieved = retrieval_service.retrieve_context(
            query=payload.query,
            top_k=payload.top_k or settings.TOP_K_RESULTS,
            filters={"collection_id": payload.collection_id} if payload.collection_id is not None else None,
            search_type=payload.search_type,
            user_id=user_id
        )
        context_str = context_builder.build_context(retrieved)
        return APIResponse(success=True, data=context_str, message="Formatted context preview assembled.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explain", response_model=APIResponse[RAGExplainResponse])
def explain_retrieval_diagnostics(
    query: str = Query(..., example="Ecosystem framework modularity check"),
    collection_id: Optional[int] = Query(None, description="Specific collection filter ID"),
    top_k: Optional[int] = Query(None, description="Number of results to retrieve"),
    search_type: str = Query("hybrid", description="vector, keyword, hybrid"),
    user_id: Optional[int] = Query(None, description="Requesting User.id")
):
    """
    Explainability endpoint: returns retrieved documents, chunk IDs, similarity and reranking scores,
    and prompt token diagnostic parameters.
    """
    try:
        explanation = rag_engine.explain_retrieval(
            query=query,
            collection_id=collection_id,
            top_k=top_k,
            search_type=search_type,
            user_id=user_id
        )
        data = RAGExplainResponse(
            query=explanation["query"],
            retrieved_document_ids=explanation["retrieved_document_ids"],
            retrieved_chunk_ids=explanation["retrieved_chunk_ids"],
            similarity_scores=explanation["similarity_scores"],
            reranking_scores=explanation["reranking_scores"],
            context_size_chars=explanation["context_size_chars"],
            memory_hits=explanation["memory_hits"],
            final_prompt_token_count_estimate=explanation["final_prompt_token_count_estimate"]
        )
        return APIResponse(success=True, data=data, message="Retrieval diagnostics explained successfully.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers", response_model=APIResponse[Dict[str, Any]])
def list_rag_providers():
    """
    Lists the configured active providers for vector, embedding, and memory backends.
    """
    providers = {
        "memory_provider": settings.MEMORY_PROVIDER,
        "rag_provider": settings.RAG_PROVIDER,
        "reranking_provider": settings.RERANKING_PROVIDER,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "vector_provider": settings.VECTOR_PROVIDER
    }
    return APIResponse(success=True, data=providers, message="Active RAG providers listed.")
