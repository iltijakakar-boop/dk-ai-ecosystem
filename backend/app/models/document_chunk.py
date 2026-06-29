from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship

from app.db.session import Base


class DocumentChunk(Base):
    """
    SQLAlchemy model representing a chunk of parsed text extracted from a document.
    """

    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    token_count = Column(Integer, nullable=False)

    # Relationship to Document
    document = relationship(
        "Document",
        backref=backref("chunks", cascade="all, delete-orphan", passive_deletes=True),
    )
