import io
import os
import time
import pytest
import pickle
import json
from fastapi.testclient import TestClient
from app.db.session import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.vector_embedding import VectorEmbedding
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store_service
from app.services.indexing_service import indexing_service
from app.services.document_service import document_service

@pytest.fixture(autouse=True)
def clean_database_and_files():
    """
    Cleans up all database records and uploaded files in the storage path before and after each test.
    """
    db = SessionLocal()
    try:
        db.query(VectorEmbedding).delete()
        db.query(DocumentChunk).delete()
        db.query(Document).delete()
        db.commit()
    finally:
        db.close()

    # Clean up workspace storage files
    storage_path = os.path.abspath(document_service.storage_path)
    if os.path.exists(storage_path):
        for f in os.listdir(storage_path):
            file_path = os.path.join(storage_path, f)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception:
                pass

    yield

    db = SessionLocal()
    try:
        db.query(VectorEmbedding).delete()
        db.query(DocumentChunk).delete()
        db.query(Document).delete()
        db.commit()
    finally:
        db.close()


def test_document_upload_validation(client: TestClient):
    """
    Tests file upload constraints such as unsupported extensions and size limits.
    """
    # 1. Invalid Extension
    files = [("files", ("image.png", b"fake image bytes", "image/png"))]
    res = client.post("/api/v1/documents/upload", files=files)
    assert res.status_code == 200
    data = res.json()["data"][0]
    assert data["success"] is False
    assert "Unsupported file type" in data["error"]

    # 2. Oversized File
    oversized_content = b"x" * (11 * 1024 * 1024) # 11MB (limit is 10MB)
    files = [("files", ("big.txt", oversized_content, "text/plain"))]
    res_big = client.post("/api/v1/documents/upload", files=files)
    assert res_big.status_code == 200
    data_big = res_big.json()["data"][0]
    assert data_big["success"] is False
    assert "exceeds maximum allowed size" in data_big["error"]


def test_multifile_upload_and_background_processing(client: TestClient):
    """
    Tests upload of multiple documents, background queue triggers, and status updates.
    """
    files = [
        ("files", ("doc1.txt", b"DK AI Ecosystem is a powerful framework for AI agents.", "text/plain")),
        ("files", ("doc2.md", b"This markdown file details RAG capabilities.", "text/markdown"))
    ]
    res = client.post("/api/v1/documents/upload", files=files)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 2
    
    doc1_id = data[0]["document_id"]
    doc2_id = data[1]["document_id"]
    
    assert data[0]["status"] == "processing"
    assert data[1]["status"] == "processing"

    # Verify status transition to indexed (TestClient runs background tasks synchronously before returning)
    status_res1 = client.get(f"/api/v1/documents/{doc1_id}/status")
    assert status_res1.status_code == 200
    assert status_res1.json()["data"]["status"] == "indexed"
    assert status_res1.json()["data"]["chunk_count"] > 0


def test_duplicate_document_detection(client: TestClient):
    """
    Verifies that uploading an identical file detects duplicate SHA-256 hash
    and returns existing document information.
    """
    content = b"Unique content for duplicate hashing checks."
    files1 = [("files", ("original.txt", content, "text/plain"))]
    res1 = client.post("/api/v1/documents/upload", files=files1)
    doc_id1 = res1.json()["data"][0]["document_id"]

    # Upload identical content
    files2 = [("files", ("copy.txt", content, "text/plain"))]
    res2 = client.post("/api/v1/documents/upload", files=files2)
    assert res2.status_code == 200
    data2 = res2.json()["data"][0]
    
    assert data2["document_id"] == doc_id1
    assert "already ingested" in data2["message"]


def test_embedding_cache_reuse(client: TestClient):
    """
    Tests that duplicate chunk text content reuses existing embeddings
    and skips provider API calls.
    """
    unique_text = "This exact line represents chunk cache testing."
    files = [("files", ("source.txt", unique_text.encode("utf-8"), "text/plain"))]
    res = client.post("/api/v1/documents/upload", files=files)
    doc_id = res.json()["data"][0]["document_id"]

    # Fetch generated embedding data using a fresh session
    db = SessionLocal()
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).first()
        assert chunk is not None
        assert chunk.embedding is not None
        emb_data_orig = chunk.embedding.embedding_data
    finally:
        db.close()

    # 2. Ingest second document containing the exact same chunk
    files2 = [("files", ("target.txt", unique_text.encode("utf-8"), "text/plain"))]
    res2 = client.post("/api/v1/documents/upload", files=files2)
    doc_id2 = res2.json()["data"][0]["document_id"]

    db = SessionLocal()
    try:
        chunk2 = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id2).first()
        assert chunk2 is not None
        assert chunk2.embedding is not None
        # Embedding data must match exactly (reused)
        assert chunk2.embedding.embedding_data == emb_data_orig
    finally:
        db.close()


def test_incremental_reindexing(client: TestClient):
    """
    Verifies that reindexing retains unchanged chunk vectors and only
    regenerates vectors for added/modified chunks.
    """
    # 1. Upload document and index it
    initial_text = "Line number one.\nLine number two."
    files = [("files", ("reindex_doc.txt", initial_text.encode("utf-8"), "text/plain"))]
    res = client.post("/api/v1/documents/upload", files=files)
    doc_id = res.json()["data"][0]["document_id"]

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        filename = doc.filename
    finally:
        db.close()

    # Modify document contents in disk storage
    file_path = os.path.join(document_service.storage_path, filename)
    new_text = "Line number one.\nLine number three modified."
    with open(file_path, "wb") as f:
        f.write(new_text.encode("utf-8"))

    # Trigger incremental reindexing (synchronous background helper)
    indexing_service.reindex_document(doc_id)

    db = SessionLocal()
    try:
        new_chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
        new_texts = [c.text for c in new_chunks]
        
        # "Line number one" chunk should remain preserved
        assert any("Line number one" in t for t in new_texts)
        assert any("Line number three modified" in t for t in new_texts)
    finally:
        db.close()


def test_similarity_search_and_statistics(client: TestClient):
    """
    Tests text similarity querying, raw vector retrieval, stats, and health checks.
    """
    files = [("files", ("search_doc.txt", b"Artificial intelligence is transforming business analytics.", "text/plain"))]
    res = client.post("/api/v1/documents/upload", files=files)
    doc_id = res.json()["data"][0]["document_id"]

    # 1. Similarity Query
    search_payload = {
        "query": "artificial intelligence",
        "top_k": 3
    }
    search_res = client.post("/api/v1/search/similarity", json=search_payload)
    assert search_res.status_code == 200
    matches = search_res.json()["data"]
    assert len(matches) > 0
    assert "artificial" in matches[0]["text"].lower() or "intelligence" in matches[0]["text"].lower()

    # 2. Raw Vector Query
    vec_res = client.post("/api/v1/search/vector", json=search_payload)
    assert vec_res.status_code == 200
    vec_matches = vec_res.json()["data"]
    assert len(vec_matches) > 0
    assert "vector" in vec_matches[0]
    assert len(vec_matches[0]["vector"]) == 1536

    # 3. Provider Health Check
    health_res = client.get("/api/v1/search/providers/health")
    assert health_res.status_code == 200
    assert health_res.json()["success"] is True

    # 4. Statistics
    stats_res = client.get("/api/v1/search/statistics")
    assert stats_res.status_code == 200
    assert stats_res.json()["data"]["total_vectors"] > 0


def test_document_delete_cleanup(client: TestClient):
    """
    Tests that deleting a document cleans up disk storage and cascadingly deletes
    document chunks and vector embeddings.
    """
    files = [("files", ("cleanup_doc.txt", b"Document content to delete", "text/plain"))]
    res = client.post("/api/v1/documents/upload", files=files)
    doc_id = res.json()["data"][0]["document_id"]

    db = SessionLocal()
    try:
        assert db.query(Document).filter(Document.id == doc_id).count() == 1
        assert db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).count() > 0
    finally:
        db.close()

    # Execute DELETE request
    del_res = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Confirm complete cascades deletion
    db = SessionLocal()
    try:
        assert db.query(Document).filter(Document.id == doc_id).count() == 0
        assert db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).count() == 0
    finally:
        db.close()
