from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VisionJobCreate(BaseModel):
    workspace_id: int
    image_url: str


class VisionJobResponse(BaseModel):
    id: int
    workspace_id: int
    image_url: str
    status: str
    result_data: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ImageGenerationCreate(BaseModel):
    workspace_id: int
    prompt: str


class ImageGenerationResponse(BaseModel):
    id: int
    workspace_id: int
    prompt: str
    status: str
    generated_image_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class OCRDocumentCreate(BaseModel):
    workspace_id: int
    name: str
    document_url: str


class OCRDocumentResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    document_url: str
    extracted_text: Optional[str]

    class Config:
        from_attributes = True


class SpeechRecognitionCreate(BaseModel):
    workspace_id: int
    audio_url: str


class SpeechRecognitionResponse(BaseModel):
    id: int
    workspace_id: int
    audio_url: str
    status: str
    transcription: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SpeechSynthesisCreate(BaseModel):
    workspace_id: int
    text: str


class SpeechSynthesisResponse(BaseModel):
    id: int
    workspace_id: int
    text: str
    status: str
    audio_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MediaAssetResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    url: str
    file_type: str
    size_bytes: int

    class Config:
        from_attributes = True
