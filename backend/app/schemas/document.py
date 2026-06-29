from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional

class DocumentResponse(BaseModel):
    id: int = Field(..., example=1)
    uuid: str = Field(..., example="44ca1112-9c1c-43f1-a128-444bb222f601")
    original_filename: str = Field(..., example="quarterly_report.pdf")
    mime_type: str = Field(..., example="application/pdf")
    file_size: int = Field(..., example=1048576, description="Size in bytes")
    sha256: str = Field(..., example="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    uploaded_by: Optional[int] = Field(None, example=2)
    upload_time: datetime = Field(..., example="2026-06-29T23:01:00Z")
    processing_status: str = Field(..., example="indexed", description="pending, processing, indexed, failed")
    chunk_count: int = Field(..., example=12)

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    success: bool = Field(..., example=True)
    filename: str = Field(..., example="quarterly_report.pdf")
    document_id: int = Field(..., example=1)
    status: str = Field(..., example="processing", description="pending, processing, indexed, failed")
    message: str = Field(..., example="File uploaded successfully. Indexing started in background.")


class DocumentStatusResponse(BaseModel):
    document_id: int = Field(..., example=1)
    status: str = Field(..., example="indexed", description="pending, processing, indexed, failed")
    chunk_count: int = Field(..., example=12)
    message: Optional[str] = Field(None, example="Indexing finished successfully.")


class DocumentChunkResponse(BaseModel):
    id: int = Field(..., example=42)
    document_id: int = Field(..., example=1)
    chunk_index: int = Field(..., example=0)
    text: str = Field(..., example="DK AI Ecosystem quarterly performance text excerpt...")
    token_count: int = Field(..., example=85)

    class Config:
        from_attributes = True


class VectorStatisticsResponse(BaseModel):
    total_documents: int = Field(..., example=5)
    total_chunks: int = Field(..., example=128)
    total_vectors: int = Field(..., example=128)
    vector_dimension: int = Field(..., example=1536)
    embedding_provider: str = Field(..., example="mock")
    vector_provider: str = Field(..., example="sqlite")


class ProviderHealthResponse(BaseModel):
    embedding_provider: str = Field(..., example="mock")
    embedding_healthy: bool = Field(..., example=True)
    vector_provider: str = Field(..., example="sqlite")
    vector_healthy: bool = Field(..., example=True)
    details: Dict[str, Any] = Field(..., example={
        "embedding_model": "text-embedding-004",
        "vector_dimension": 1536,
        "sqlite_file": "test.db"
    })
