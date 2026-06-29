import uuid
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.dependencies.db import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.vector_embedding import VectorEmbedding
from app.schemas.document import (
    DocumentChunkResponse,
    DocumentResponse,
    DocumentStatusResponse,
)
from app.schemas.response import APIResponse
from app.services.document_service import document_service
from app.services.indexing_service import indexing_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=APIResponse[List[Dict[str, Any]]])
async def upload_multiple_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """
    Ingests one or many files, checks file size/type constraints, hashes contents for duplicate checking,
    writes them safely to workspace storage, and schedules indexing on a background task queue.
    """
    responses = []

    for upload_file in files:
        try:
            # 1. Read raw file bytes to validate and compute hash
            content = await upload_file.read()
            original_filename = upload_file.filename or "unnamed_file"
            file_size = len(content)

            # 2. Size and Extension Validation
            is_valid, err_msg = document_service.validate_file(
                original_filename, file_size
            )
            if not is_valid:
                responses.append(
                    {
                        "success": False,
                        "filename": original_filename,
                        "error": err_msg,
                        "status": "failed",
                    }
                )
                continue

            # 3. SHA-256 Hashing for Duplicate Document checks
            file_hash = document_service.calculate_sha256(content)
            existing_doc = (
                db.query(Document).filter(Document.sha256 == file_hash).first()
            )
            if existing_doc:
                responses.append(
                    {
                        "success": True,
                        "filename": original_filename,
                        "document_id": existing_doc.id,
                        "status": existing_doc.processing_status,
                        "message": "Document already ingested. Returned existing document ID.",
                    }
                )
                continue

            # 4. Save unique file on disk
            saved_name = document_service.save_file(content, original_filename)

            # 5. Create Database metadata record
            doc_record = Document(
                uuid=str(uuid.uuid4()),
                filename=saved_name,
                original_filename=original_filename,
                mime_type=upload_file.content_type or "application/octet-stream",
                file_size=file_size,
                sha256=file_hash,
                processing_status="pending",
            )
            db.add(doc_record)
            db.commit()
            db.refresh(doc_record)

            # 6. Queue background processing task
            background_tasks.add_task(
                indexing_service.index_document_in_background, document_id=doc_record.id
            )

            responses.append(
                {
                    "success": True,
                    "filename": original_filename,
                    "document_id": doc_record.id,
                    "status": "processing",
                    "message": "File uploaded successfully. Indexing started in background.",
                }
            )

        except Exception as e:
            logger.exception(f"Error handling upload for file {upload_file.filename}:")
            responses.append(
                {
                    "success": False,
                    "filename": upload_file.filename or "unknown",
                    "error": str(e),
                    "status": "failed",
                }
            )

    return APIResponse(
        success=True,
        data=responses,
        message=f"Processed upload request for {len(files)} files.",
    )


@router.get("", response_model=APIResponse[List[DocumentResponse]])
def list_documents(
    filename: Optional[str] = Query(None, description="Filter by original filename"),
    status: Optional[str] = Query(None, description="Filter by processing status"),
    mime_type: Optional[str] = Query(None, description="Filter by MIME type"),
    db: Session = Depends(get_db),
):
    """
    Lists metadata and processing states for all ingested documents, with options to filter.
    """
    query = db.query(Document)
    if filename:
        query = query.filter(Document.original_filename.like(f"%{filename}%"))
    if status:
        query = query.filter(Document.processing_status == status)
    if mime_type:
        query = query.filter(Document.mime_type == mime_type)

    documents = query.all()
    # Map SQLAlchemy objects to Pydantic schemas
    res_list = [DocumentResponse.model_validate(doc) for doc in documents]
    return APIResponse(success=True, data=res_list)


@router.get("/{document_id}", response_model=APIResponse[DocumentResponse])
def get_document_details(document_id: int, db: Session = Depends(get_db)):
    """
    Retrieves full metadata details for a specific document.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return APIResponse(success=True, data=DocumentResponse.model_validate(doc))


@router.get("/{document_id}/status", response_model=APIResponse[DocumentStatusResponse])
def get_document_status(document_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the current processing state of a document.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    msg = (
        "Indexing finished successfully."
        if doc.processing_status == "indexed"
        else None
    )
    if doc.processing_status == "failed":
        msg = "Indexing failed during processing pipeline."
    elif doc.processing_status == "processing":
        msg = "File is currently being parsed and chunked."

    status_data = DocumentStatusResponse(
        document_id=doc.id,
        status=doc.processing_status,
        chunk_count=doc.chunk_count,
        message=msg,
    )
    return APIResponse(success=True, data=status_data)


@router.delete("/{document_id}", response_model=APIResponse[Dict[str, Any]])
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    Removes a document from disk storage, deletes all its DB records, and cleans up vector store vectors.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # 1. Delete file from storage
    document_service.delete_file(doc.filename)

    # 2. Database cascading cleanups manually
    chunks = (
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
    )
    for chunk in chunks:
        db.query(VectorEmbedding).filter(VectorEmbedding.chunk_id == chunk.id).delete()
        db.delete(chunk)

    db.delete(doc)
    db.commit()

    return APIResponse(
        success=True,
        data={"document_id": document_id},
        message="Document, associated chunks, vector embeddings, and cache purged successfully.",
    )


@router.post("/{document_id}/reindex", response_model=APIResponse[Dict[str, Any]])
def trigger_document_reindexing(
    document_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """
    Triggers incremental reindexing asynchronously. Reuses unchanged chunks and adds new chunks.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    background_tasks.add_task(indexing_service.reindex_document, document_id=doc.id)

    return APIResponse(
        success=True,
        data={"document_id": document_id, "status": "processing"},
        message="Incremental reindexing started in background.",
    )


@router.get(
    "/{document_id}/chunks", response_model=APIResponse[List[DocumentChunkResponse]]
)
def get_document_chunks_list(document_id: int, db: Session = Depends(get_db)):
    """
    Returns the parsed text chunk details associated with a document.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )
    res = [DocumentChunkResponse.model_validate(c) for c in chunks]
    return APIResponse(success=True, data=res)
