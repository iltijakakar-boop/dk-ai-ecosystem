from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from app.db.session import Base


class VisionJob(Base):
    __tablename__ = "multimodal_vision_jobs"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    image_url = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending, running, completed, failed
    result_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class ImageGenerationJob(Base):
    __tablename__ = "multimodal_image_gen_jobs"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    prompt = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)
    generated_image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class ImageAnalysis(Base):
    __tablename__ = "multimodal_image_analyses"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    job_id = Column(Integer, ForeignKey("multimodal_vision_jobs.id", ondelete="CASCADE"), nullable=False)
    caption = Column(Text, nullable=True)
    tags = Column(String, nullable=True)


class OCRDocument(Base):
    __tablename__ = "multimodal_ocr_documents"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    document_url = Column(String, nullable=False)
    extracted_text = Column(Text, nullable=True)


class DocumentExtraction(Base):
    __tablename__ = "multimodal_doc_extractions"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    document_id = Column(Integer, ForeignKey("multimodal_ocr_documents.id", ondelete="CASCADE"), nullable=False)
    extracted_data = Column(Text, nullable=True)  # JSON keys & values


class SpeechRecognitionJob(Base):
    __tablename__ = "multimodal_speech_rec_jobs"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    audio_url = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)
    transcription = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class SpeechSynthesisJob(Base):
    __tablename__ = "multimodal_speech_syn_jobs"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    text = Column(Text, nullable=False)
    status = Column(String, default="pending", nullable=False)
    audio_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class AudioAnalysisJob(Base):
    __tablename__ = "multimodal_audio_analysis_jobs"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    audio_url = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)
    emotion = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class VideoAnalysisJob(Base):
    __tablename__ = "multimodal_video_analysis_jobs"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    video_url = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class VideoFrame(Base):
    __tablename__ = "multimodal_video_frames"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("multimodal_video_analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    timestamp_ms = Column(Integer, nullable=False)
    frame_url = Column(String, nullable=False)


class MediaAsset(Base):
    __tablename__ = "multimodal_media_assets"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # image, audio, video
    size_bytes = Column(Integer, nullable=False)


class MediaFolder(Base):
    __tablename__ = "multimodal_media_folders"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class MediaVersion(Base):
    __tablename__ = "multimodal_media_versions"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("multimodal_media_assets.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    url = Column(String, nullable=False)


class MediaMetadata(Base):
    __tablename__ = "multimodal_media_metadata"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("multimodal_media_assets.id", ondelete="CASCADE"), nullable=False)
    dimensions = Column(String, nullable=True)  # e.g. "1920x1080"
    duration_sec = Column(Float, nullable=True)


class MediaEmbedding(Base):
    __tablename__ = "multimodal_media_embeddings"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("multimodal_media_assets.id", ondelete="CASCADE"), nullable=False)
    embedding_vector = Column(Text, nullable=False)  # string representation


class MediaAnnotation(Base):
    __tablename__ = "multimodal_media_annotations"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("multimodal_media_assets.id", ondelete="CASCADE"), nullable=False)
    label = Column(String, nullable=False)
    bounding_box = Column(String, nullable=True)  # e.g. "x,y,w,h"


class MediaTranscript(Base):
    __tablename__ = "multimodal_media_transcripts"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("multimodal_media_assets.id", ondelete="CASCADE"), nullable=False)
    transcript_text = Column(Text, nullable=False)


class MediaTranslation(Base):
    __tablename__ = "multimodal_media_translations"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("multimodal_media_assets.id", ondelete="CASCADE"), nullable=False)
    language = Column(String, nullable=False)
    translated_text = Column(Text, nullable=False)


class MediaSummary(Base):
    __tablename__ = "multimodal_media_summaries"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("multimodal_media_assets.id", ondelete="CASCADE"), nullable=False)
    summary_text = Column(Text, nullable=False)


class MediaPipeline(Base):
    __tablename__ = "multimodal_media_pipelines"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class MediaExecution(Base):
    __tablename__ = "multimodal_media_executions"
    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("multimodal_media_pipelines.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending", nullable=False)


class MediaProvider(Base):
    __tablename__ = "multimodal_media_providers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)


class MediaUsage(Base):
    __tablename__ = "multimodal_media_usage"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    resource_type = Column(String, nullable=False)  # vision, audio, speech
    tokens_or_seconds = Column(Integer, nullable=False)
