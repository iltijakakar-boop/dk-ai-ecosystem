from sqlalchemy import Column, Integer, String, DateTime, Index, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base

class Document(Base):
    """
    SQLAlchemy model tracking uploaded files, status, chunk counts, and SHA-256 integrity hashes.
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, nullable=False)
    filename = Column(String, unique=True, index=True, nullable=False) # The saved file name (UUID-based)
    original_filename = Column(String, nullable=False)                 # Preserved user upload name
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    sha256 = Column(String, unique=True, index=True, nullable=False)  # For duplicate detection
    uploaded_by = Column(Integer, nullable=True)                      # References User.id
    collection_id = Column(Integer, ForeignKey("knowledge_collections.id", ondelete="SET NULL"), nullable=True)
    upload_time = Column(DateTime, default=func.now(), nullable=False)
    processing_status = Column(String, default="pending", nullable=False) # pending, processing, indexed, failed
    chunk_count = Column(Integer, default=0, nullable=False)
