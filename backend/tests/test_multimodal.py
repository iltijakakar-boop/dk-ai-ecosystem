from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services.multimodal_service import vision_service, media_storage_service


def get_admin_headers(client: TestClient) -> dict:
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    res = client.post("/api/v1/auth/login", data=payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 1. Vision Processing
def test_vision_processing_endpoint(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/multimodal/vision",
        json={"workspace_id": 1, "image_url": "https://images.local/mountain.jpg"},
        headers=headers,
    )
    assert res.status_code == 200
    assert "labels" in res.json()["data"]["result_data"]


# 2. Image Generation
def test_image_generation_endpoint(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/multimodal/image-gen",
        json={"workspace_id": 1, "prompt": "A modern coding workstation workspace"},
        headers=headers,
    )
    assert res.status_code == 200
    assert "generated_image_url" in res.json()["data"]


# 3. OCR Document Intelligence
def test_ocr_extraction_endpoint(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/multimodal/ocr",
        json={"workspace_id": 1, "name": "invoice_receipt.pdf", "document_url": "https://storage.local/invoice.pdf"},
        headers=headers,
    )
    assert res.status_code == 200
    assert "Gemini Cloud Services" in res.json()["data"]["extracted_text"]


# 4. Speech Recognition (Speech-to-Text)
def test_speech_to_text_endpoint(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/multimodal/speech-to-text",
        json={"workspace_id": 1, "audio_url": "https://storage.local/greeting.wav"},
        headers=headers,
    )
    assert res.status_code == 200
    assert "transcription" in res.json()["data"]


# 5. Speech Synthesis (Text-to-Speech)
def test_text_to_speech_endpoint(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/multimodal/text-to-speech",
        json={"workspace_id": 1, "text": "Testing speech rendering engine"},
        headers=headers,
    )
    assert res.status_code == 200
    assert "audio_url" in res.json()["data"]


# 6. Audio Intelligence & Video Analysis
def test_audio_and_video_analysis(client: TestClient, db: Session):
    from app.services.multimodal_service import audio_analysis_service, video_analysis_service
    # Test services directly
    aud = audio_analysis_service.analyze_audio(db, workspace_id=1, audio_url="https://audio.local")
    assert aud.emotion == "happy"

    vid = video_analysis_service.analyze_video(db, workspace_id=1, video_url="https://video.local")
    assert "software agent" in vid.summary


# 7. Media Library & Storage
def test_media_library_endpoint(client: TestClient, db: Session):
    from tests.conftest import TestingSessionLocal
    headers = get_admin_headers(client)
    
    session = TestingSessionLocal()
    try:
        media_storage_service.upload_asset(
            session, workspace_id=1, name="diagram.png", url="https://assets.local/diagram.png", file_type="image", size_bytes=2048
        )
        session.commit()
    finally:
        session.close()

    res = client.get("/api/v1/multimodal/media?workspace_id=1", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) > 0


# 8. Multi-Modal Agent Abstractions
def test_multimodal_agent_routing():
    # Verify modular, provider-independent adapter interfaces return mock values
    from app.services.multimodal_service import vision_service
    assert vision_service is not None
