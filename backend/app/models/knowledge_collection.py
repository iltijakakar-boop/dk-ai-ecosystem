from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.db.session import Base


class KnowledgeCollection(Base):
    """
    SQLAlchemy model representing a collection of document chunks with access control permissions.
    """

    __tablename__ = "knowledge_collections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    owner_id = Column(Integer, nullable=True)  # Owner User.id
    collection_type = Column(
        String, default="public", nullable=False
    )  # personal, team, public
    created_at = Column(DateTime, default=func.now(), nullable=False)
