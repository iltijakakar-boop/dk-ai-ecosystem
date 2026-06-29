from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.db.session import Base


class MemoryEntry(Base):
    """
    SQLAlchemy model representing long-term key-value memory records and general facts.
    """

    __tablename__ = "memory_entries"

    id = Column(Integer, primary_key=True, index=True)
    memory_type = Column(
        String, default="long_term", nullable=False
    )  # session, long_term
    key = Column(String, index=True, nullable=False)
    value = Column(String, nullable=False)  # JSON-serialized value
    metadata_json = Column(String, nullable=True)  # JSON-serialized metadata dictionary
    created_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)
