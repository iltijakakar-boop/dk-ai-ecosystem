from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.db.session import Base


class Conversation(Base):
    """
    SQLAlchemy model tracking conversation sessions and compressed context summaries.
    """

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=True)
    title = Column(String, nullable=False)
    summary = Column(String, nullable=True)  # Compressed summaries of old messages
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
