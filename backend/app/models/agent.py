from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from app.db.session import Base


class AgentRegistry(Base):
    """
    SQLAlchemy database model for tracking and persisting registered agents.
    """

    __tablename__ = "agent_registry"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    status = Column(String, default="active", nullable=False)
    provider = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
