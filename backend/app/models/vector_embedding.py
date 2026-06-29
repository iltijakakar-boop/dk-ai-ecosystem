from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref
from app.db.session import Base

class VectorEmbedding(Base):
    """
    SQLAlchemy model representing the vectorized embedding data generated for a document chunk.
    """
    __tablename__ = "vector_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False, unique=True)
    embedding_provider = Column(String, nullable=False)
    embedding_model = Column(String, nullable=False)
    vector_dimension = Column(Integer, nullable=False)
    embedding_data = Column(LargeBinary, nullable=False) # Serialized float list (JSON/pickle/numpy bytes)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationship to DocumentChunk
    chunk = relationship("DocumentChunk", backref=backref("embedding", uselist=False, cascade="all, delete-orphan", passive_deletes=True))
