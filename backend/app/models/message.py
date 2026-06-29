from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Message(Base):
    """
    SQLAlchemy model representing individual messages in a conversation thread.
    """

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(String, nullable=False)  # system, user, assistant
    content = Column(String, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)

    # Relationship to Conversation
    conversation = relationship(
        "Conversation",
        backref=backref("messages", cascade="all, delete-orphan", passive_deletes=True),
    )
