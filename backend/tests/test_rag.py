import pytest
import os
import json
from fastapi.testclient import TestClient
from app.db.session import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.vector_embedding import VectorEmbedding
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.memory_entry import MemoryEntry
from app.models.knowledge_collection import KnowledgeCollection
from app.services.memory_service import memory_service
from app.services.conversation_service import conversation_service
from app.services.indexing_service import indexing_service
from app.services.rag_engine import rag_engine

@pytest.fixture(autouse=True)
def clean_rag_database_and_files():
    """
    Purges all test entries before and after each RAG test case.
    """
    db = SessionLocal()
    try:
        db.query(VectorEmbedding).delete()
        db.query(DocumentChunk).delete()
        db.query(Document).delete()
        db.query(Message).delete()
        db.query(Conversation).delete()
        db.query(MemoryEntry).delete()
        db.query(KnowledgeCollection).delete()
        db.commit()
    finally:
        db.close()

    # Clear JSON files
    for f in ["database/long_term_memory.json"]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass
    yield


def test_conversations_api(client: TestClient):
    """
    Tests conversation creation, message log turns, and deletion.
    """
    # 1. Create Conversation
    payload = {"session_id": "test_conv_session", "title": "Framework Test"}
    res = client.post("/api/v1/conversations", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["session_id"] == "test_conv_session"
    assert data["title"] == "Framework Test"
    conv_id = data["id"]

    # 2. Add Message Turn
    db = SessionLocal()
    try:
        msg = conversation_service.add_message(db, "test_conv_session", "user", "Hello framework!")
        assert msg.content == "Hello framework!"
    finally:
        db.close()

    # 3. Retrieve Messages Log
    history_res = client.get(f"/api/v1/conversations/{conv_id}/messages")
    assert history_res.status_code == 200
    history_data = history_res.json()["data"]
    assert len(history_data) == 1
    assert history_data[0]["content"] == "Hello framework!"

    # 4. Delete Thread
    del_res = client.delete(f"/api/v1/conversations/{conv_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True


def test_memory_providers_storage(client: TestClient):
    """
    Tests long term key-value storages using SQLite, Redis, and File providers.
    """
    # 1. SQLite Store
    store = memory_service.get_store()
    store.set("sqlite_key", "sqlite_val", memory_type="long_term")
    assert store.get("sqlite_key", memory_type="long_term") == "sqlite_val"
    store.delete("sqlite_key", memory_type="long_term")
    assert store.get("sqlite_key", memory_type="long_term") is None

    # 2. File Store
    from app.services.memory_service import FileMemoryStore
    file_store = FileMemoryStore("database/long_term_memory_test.json")
    file_store.set("file_key", {"data": "file_val"}, memory_type="long_term")
    assert file_store.get("file_key", memory_type="long_term") == {"data": "file_val"}
    
    # Cleanup file
    if os.path.exists("database/long_term_memory_test.json"):
        os.remove("database/long_term_memory_test.json")


def test_memory_compression_summarization(client: TestClient):
    """
    Verifies that dialog turns are summarized and history is reduced
    once thresholds are exceeded.
    """
    db = SessionLocal()
    try:
        # Create conversation thread
        conv = conversation_service.create_conversation(db, "session_compress", "Compression thread")
        
        # Log 12 message turns (limit is MEMORY_SUMMARY_TRIGGER_MESSAGES = 10)
        # We append alternating user/assistant rounds
        for i in range(12):
            role = "user" if i % 2 == 0 else "assistant"
            conversation_service.add_message(db, "session_compress", role, f"Turn statement number {i}")

        db.refresh(conv)
        # Verify summary column populated
        assert conv.summary is not None
        assert "[Conversation Summary]" in conv.summary

        # Confirm message turns were pruned, leaving the last 2 rounds + 1 extra
        msg_count = db.query(Message).filter(Message.conversation_id == conv.id).count()
        assert msg_count == 3
        
        # Check prepended summary history rebuilds
        history = conversation_service.get_history(db, "session_compress")
        assert len(history) == 4 # 1 Prepend Summary + 3 Active Messages
        assert history[0]["role"] == "system"
        assert "summary of the older conversation" in history[0]["content"]

    finally:
        db.close()


def test_collection_access_control(client: TestClient):
    """
    Enforces collection visibility check. Personal collections are only visible to the owner.
    """
    db = SessionLocal()
    try:
        # Create two knowledge collections
        col_owner = KnowledgeCollection(name="personal_owner", collection_type="personal", owner_id=10)
        col_other = KnowledgeCollection(name="personal_other", collection_type="personal", owner_id=20)
        db.add(col_owner)
        db.add(col_other)
        db.commit()

        # Ingest document for owner collection
        doc_owner = Document(
            uuid="uuid-owner-col",
            filename="owner.txt",
            original_filename="owner.txt",
            mime_type="text/plain",
            file_size=10,
            sha256="sha-owner-123",
            collection_id=col_owner.id,
            processing_status="indexed",
            chunk_count=1
        )
        db.add(doc_owner)
        db.flush()

        chunk_owner = DocumentChunk(
            document_id=doc_owner.id,
            chunk_index=0,
            text="Owner proprietary guidelines content text block.",
            token_count=6
        )
        db.add(chunk_owner)
        db.flush()

        # Mock vector embedding
        emb = VectorEmbedding(
            chunk_id=chunk_owner.id,
            embedding_provider="mock",
            embedding_model="text-embedding-004",
            vector_dimension=1536,
            embedding_data=pickle.dumps([0.1]*1536)
        )
        db.add(emb)
        db.commit()

        # 1. Search as owner (user_id = 10): returns chunk
        res_owner = client.post("/api/v1/rag/search?user_id=10", json={
            "session_id": "sess_owner",
            "query": "proprietary",
            "collection_id": col_owner.id
        })
        assert res_owner.status_code == 200
        assert len(res_owner.json()["data"]) == 1

        # 2. Search as different user (user_id = 20): gets empty results
        res_other = client.post("/api/v1/rag/search?user_id=20", json={
            "session_id": "sess_other",
            "query": "proprietary",
            "collection_id": col_owner.id
        })
        assert res_other.status_code == 200
        assert len(res_other.json()["data"]) == 0

    finally:
        db.close()


def test_retrieval_explainability_and_chat_pipeline(client: TestClient):
    """
    Validates hybrid RAG responses and retrieval explainability diagnostics (/explain).
    """
    db = SessionLocal()
    try:
        # Ingest public document
        doc = Document(
            uuid="uuid-rag-doc",
            filename="rag.txt",
            original_filename="rag.txt",
            mime_type="text/plain",
            file_size=15,
            sha256="sha-rag-123",
            processing_status="indexed",
            chunk_count=1
        )
        db.add(doc)
        db.flush()

        chunk = DocumentChunk(
            document_id=doc.id,
            chunk_index=0,
            text="Ecosystem modularity and pluggable drivers are core principles.",
            token_count=10
        )
        db.add(chunk)
        db.flush()

        emb = VectorEmbedding(
            chunk_id=chunk.id,
            embedding_provider="mock",
            embedding_model="text-embedding-004",
            vector_dimension=1536,
            embedding_data=pickle.dumps([0.5]*1536)
        )
        db.add(emb)
        db.commit()

        # 1. Explain retrieval endpoint
        explain_res = client.get("/api/v1/rag/explain?query=modularity&search_type=hybrid")
        assert explain_res.status_code == 200
        explain_data = explain_res.json()["data"]
        
        assert explain_data["query"] == "modularity"
        assert len(explain_data["retrieved_chunk_ids"]) > 0
        assert explain_data["context_size_chars"] > 0
        assert explain_data["final_prompt_token_count_estimate"] > 0

        # 2. Chat RAG query endpoint
        chat_res = client.post("/api/v1/rag/chat", json={
            "session_id": "sess_rag_chat",
            "query": "DK AI Ecosystem details modularity",
            "search_type": "hybrid"
        })
        assert chat_res.status_code == 200
        chat_data = chat_res.json()["data"]
        
        assert "Ecosystem" in chat_data["answer"] or "modularity" in chat_data["answer"]
        assert len(chat_data["sources"]) > 0

    finally:
        db.close()

import pickle
