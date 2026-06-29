from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class KnowledgeCollectionResponse(BaseModel):
    id: int = Field(..., example=1)
    name: str = Field(..., example="finance_q1_reports")
    description: Optional[str] = Field(None, example="Financial earnings for Q1")
    owner_id: Optional[int] = Field(None, example=2)
    collection_type: str = Field(..., example="public")  # personal, team, public
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeCollectionCreate(BaseModel):
    name: str = Field(..., example="finance_q1_reports")
    description: Optional[str] = Field(None, example="Financial earnings for Q1")
    collection_type: str = Field("public", example="public")  # personal, team, public


class ConversationResponse(BaseModel):
    id: int = Field(..., example=1)
    session_id: str = Field(..., example="session_abc_123")
    user_id: Optional[int] = Field(None, example=2)
    title: str = Field(..., example="DK AI Framework Discussion")
    summary: Optional[str] = Field(
        None, example="Summarized overview of RAG details..."
    )
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    session_id: str = Field(..., example="session_abc_123")
    title: str = Field("New Conversation", example="DK AI Framework Discussion")
    user_id: Optional[int] = Field(None, example=2)


class MessageResponse(BaseModel):
    id: int = Field(..., example=42)
    conversation_id: int = Field(..., example=1)
    role: str = Field(..., example="user")
    content: str = Field(..., example="How does vector memory work?")
    token_count: int = Field(..., example=7)
    timestamp: datetime

    class Config:
        from_attributes = True


class RAGChatRequest(BaseModel):
    session_id: str = Field(..., example="session_abc_123")
    query: str = Field(..., example="What are the main goals of the framework?")
    collection_id: Optional[int] = Field(None, example=1)
    top_k: Optional[int] = Field(None, example=5)
    search_type: Optional[str] = Field(
        "hybrid", example="hybrid", description="vector, keyword, hybrid"
    )


class RAGChatResponse(BaseModel):
    answer: str = Field(
        ...,
        example="The main goals of the framework are modularity and pluggable drivers.",
    )
    session_id: str = Field(..., example="session_abc_123")
    sources: List[Dict[str, Any]] = Field(
        ..., example=[{"chunk_id": 12, "filename": "doc1.txt", "score": 0.89}]
    )


class RAGExplainResponse(BaseModel):
    query: str = Field(..., example="RAG explainability check")
    retrieved_document_ids: List[int] = Field(..., example=[1, 2])
    retrieved_chunk_ids: List[int] = Field(..., example=[12, 14])
    similarity_scores: List[float] = Field(..., example=[0.89, 0.74])
    reranking_scores: List[float] = Field(..., example=[0.95, 0.81])
    context_size_chars: int = Field(..., example=1500)
    memory_hits: List[str] = Field(..., example=["summary_history", "long_term_fact"])
    final_prompt_token_count_estimate: int = Field(..., example=425)


class MemorySearchRequest(BaseModel):
    key: str = Field(..., example="user_role")
    memory_type: str = Field("long_term", example="long_term")


class MemoryEntryResponse(BaseModel):
    id: int = Field(..., example=1)
    memory_type: str = Field(..., example="long_term")
    key: str = Field(..., example="user_role")
    value: str = Field(..., example="admin")
    metadata_json: Optional[str] = Field(None, example='{"uploader": "system"}')
    created_at: datetime
    expires_at: Optional[datetime] = Field(None)

    class Config:
        from_attributes = True
