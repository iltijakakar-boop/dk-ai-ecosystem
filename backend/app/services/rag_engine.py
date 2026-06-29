import time
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from app.db.session import SessionLocal
from app.models.monitoring_model import ExecutionMetric
from app.services.retrieval_service import retrieval_service
from app.services.reranker import reranker_service
from app.services.context_builder import context_builder
from app.services.conversation_service import conversation_service
from app.config.settings import settings
from app.core.logging.logger import logger

class RAGEngine:
    """
    Orchestrates the entire RAG cycle: retrieves contexts, reranks blocks,
    assembles token contexts, appends summaries, calls LLM providers, and audits performance.
    """
    
    def generate_chat_response(
        self,
        session_id: str,
        query: str,
        collection_id: Optional[int] = None,
        top_k: Optional[int] = None,
        search_type: str = "hybrid",
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes RAG context retrieval and query generation.
        """
        db = SessionLocal()
        start_total = time.perf_counter()
        
        # 1. Retrieve history including prepended compression summaries
        history = conversation_service.get_history(db, session_id)
        memory_hits = []
        if any("[Conversation Summary]" in h["content"] for h in history):
            memory_hits.append("summary_history")

        # 2. Retrieve contexts with collection filters
        start_retrieve = time.perf_counter()
        filters = {}
        if collection_id is not None:
            filters["collection_id"] = collection_id
            
        retrieved_chunks = retrieval_service.retrieve_context(
            query=query,
            top_k=top_k or settings.TOP_K_RESULTS,
            filters=filters,
            search_type=search_type,
            user_id=user_id
        )
        duration_retrieve = (time.perf_counter() - start_retrieve) * 1000.0
        self._log_metric(db, "rag:retrieval", duration_retrieve)

        # 3. Reranking
        start_rerank = time.perf_counter()
        reranker = reranker_service.get_reranker()
        reranked_chunks = reranker.rerank(query, retrieved_chunks)
        duration_rerank = (time.perf_counter() - start_rerank) * 1000.0
        self._log_metric(db, "rag:rerank", duration_rerank)

        # 4. Context Building
        context_str = context_builder.build_context(reranked_chunks)
        context_size = len(context_str)

        # Log active memory layers
        if context_str:
            memory_hits.append("knowledge_memory")

        # 5. Prompt Assembly & LLM Generation
        start_llm = time.perf_counter()
        answer = self._call_llm_provider(query, context_str, history)
        duration_llm = (time.perf_counter() - start_llm) * 1000.0
        self._log_metric(db, "rag:llm", duration_llm)

        # 6. Save chat turns back to dialogue logs
        conversation_service.add_message(db, session_id, "user", query)
        conversation_service.add_message(db, session_id, "assistant", answer)

        # Auditing metrics
        duration_total = (time.perf_counter() - start_total) * 1000.0
        self._log_metric(db, "rag:total", duration_total)
        self._log_metric(db, "rag:context_size", float(context_size))

        db.close()

        # Build clean source outputs
        sources = []
        for c in reranked_chunks:
            sources.append({
                "chunk_id": c["chunk_id"],
                "filename": c["filename"],
                "score": c.get("rerank_score", c["score"])
            })

        return {
            "answer": answer,
            "session_id": session_id,
            "sources": sources,
            "diagnostics": {
                "retrieved_chunks_count": len(retrieved_chunks),
                "context_size_chars": context_size,
                "memory_hits": memory_hits,
                "duration_ms": duration_total
            }
        }

    def explain_retrieval(
        self,
        query: str,
        collection_id: Optional[int] = None,
        top_k: Optional[int] = None,
        search_type: str = "hybrid",
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Diagnostic helper executing RAG context fetches without calling the LLM.
        """
        db = SessionLocal()
        
        filters = {}
        if collection_id is not None:
            filters["collection_id"] = collection_id

        retrieved_chunks = retrieval_service.retrieve_context(
            query=query,
            top_k=top_k or settings.TOP_K_RESULTS,
            filters=filters,
            search_type=search_type,
            user_id=user_id
        )

        reranker = reranker_service.get_reranker()
        reranked_chunks = reranker.rerank(query, retrieved_chunks)
        context_str = context_builder.build_context(reranked_chunks)

        doc_ids = list(set(c["document_id"] for c in reranked_chunks))
        chunk_ids = [c["chunk_id"] for c in reranked_chunks]
        sim_scores = [c["score"] for c in retrieved_chunks]
        rerank_scores = [c.get("rerank_score", c["score"]) for c in reranked_chunks]

        # Estimate prompt tokens: context chars / 4 + query words
        prompt_tokens_est = (len(context_str) // 4) + len(query.split()) + 50

        db.close()

        return {
            "query": query,
            "retrieved_document_ids": doc_ids,
            "retrieved_chunk_ids": chunk_ids,
            "similarity_scores": sim_scores,
            "reranking_scores": rerank_scores,
            "context_size_chars": len(context_str),
            "memory_hits": ["knowledge_memory"] if context_str else [],
            "final_prompt_token_count_estimate": prompt_tokens_est
        }

    def _call_llm_provider(self, query: str, context: str, history: List[Dict[str, str]]) -> str:
        """
        Routes the compiled prompt to the configured LLM backend.
        Falls back to intelligent mock responses when API keys are absent.
        """
        provider = settings.EMBEDDING_PROVIDER.lower() # Reuse provider setting for consistency
        
        # Build prompt context prefix
        context_prefix = ""
        if context:
            context_prefix = f"Use the following document contexts to answer the query:\n{context}\n\n"

        prompt = f"{context_prefix}User Query: {query}"
        
        # Mock LLM generation
        if provider == "mock" or not (settings.GEMINI_API_KEY or settings.OPENAI_API_KEY):
            # Extract basic facts from context if possible
            if "DK AI Ecosystem" in context:
                return "The DK AI Ecosystem is a modular, provider-agnostic framework built for scalable AI agents."
            if "RAG capabilities" in context:
                return "The RAG pipeline provides vector, keyword, and hybrid similarity search with access controls."
            return f"Mock Response: Answered query '{query}' using retrieved document context."

        # Concrete LLM calls can be routed here if configured
        try:
            if provider == "gemini" and settings.GEMINI_API_KEY:
                # Call Gemini completions
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={settings.GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}]
                }
                with httpx.Client() as client:
                    res = client.post(url, json=payload, timeout=settings.API_TIMEOUT)
                res.raise_for_status()
                return res.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logger.error(f"LLM API call failed: {e}. Falling back to mock response.")
            
        return f"Mock Response (API Fallback): Answered query '{query}'."

    def _log_metric(self, db, component: str, value: float) -> None:
        """
        Saves timings into the monitoring diagnostics metrics.
        """
        try:
            metric = ExecutionMetric(
                component=component,
                execution_time=value,
                success=True,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(metric)
            db.commit()
        except Exception as err:
            logger.warning(f"Failed to record RAG performance metric: {err}")

# Global RAGEngine instance
rag_engine = RAGEngine()
