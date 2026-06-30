from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.multimodal import (
    VisionJobCreate,
    VisionJobResponse,
    ImageGenerationCreate,
    ImageGenerationResponse,
    OCRDocumentCreate,
    OCRDocumentResponse,
    SpeechRecognitionCreate,
    SpeechRecognitionResponse,
    SpeechSynthesisCreate,
    SpeechSynthesisResponse,
    MediaAssetResponse,
)
from app.services.multimodal_service import (
    vision_service,
    image_generation_service,
    ocr_service,
    speech_to_text_service,
    text_to_speech_service,
    media_storage_service,
)


router = APIRouter(prefix="/multimodal", tags=["multimodal"])


@router.post("/vision", response_model=APIResponse[VisionJobResponse])
def run_vision_analysis(
    payload: VisionJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    job = vision_service.create_vision_job(db, workspace_id=payload.workspace_id, image_url=payload.image_url)
    return APIResponse(success=True, message="Vision job processed successfully.", data=VisionJobResponse.model_validate(job))


@router.post("/image-gen", response_model=APIResponse[ImageGenerationResponse])
def generate_image_from_prompt(
    payload: ImageGenerationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    job = image_generation_service.create_generation_job(db, workspace_id=payload.workspace_id, prompt=payload.prompt)
    return APIResponse(success=True, message="Image generation completed.", data=ImageGenerationResponse.model_validate(job))


@router.post("/ocr", response_model=APIResponse[OCRDocumentResponse])
def run_ocr_document_extraction(
    payload: OCRDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    doc = ocr_service.execute_ocr(db, workspace_id=payload.workspace_id, name=payload.name, document_url=payload.document_url)
    return APIResponse(success=True, message="OCR extraction finished.", data=OCRDocumentResponse.model_validate(doc))


@router.post("/speech-to-text", response_model=APIResponse[SpeechRecognitionResponse])
def run_speech_recognition(
    payload: SpeechRecognitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    job = speech_to_text_service.transcribe_audio(db, workspace_id=payload.workspace_id, audio_url=payload.audio_url)
    return APIResponse(success=True, message="Transcription finished.", data=SpeechRecognitionResponse.model_validate(job))


@router.post("/text-to-speech", response_model=APIResponse[SpeechSynthesisResponse])
def run_speech_synthesis(
    payload: SpeechSynthesisCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    job = text_to_speech_service.synthesize_speech(db, workspace_id=payload.workspace_id, text=payload.text)
    return APIResponse(success=True, message="Speech synthesis completed.", data=SpeechSynthesisResponse.model_validate(job))


@router.get("/media", response_model=APIResponse[List[MediaAssetResponse]])
def list_media_assets(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    assets = media_storage_service.get_assets(db, workspace_id)
    res = [MediaAssetResponse.model_validate(a) for a in assets]
    return APIResponse(success=True, data=res)
