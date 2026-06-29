from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class SystemMetric(Base):
    """
    SQLAlchemy database model for persisting host resource metrics.
    """
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    cpu = Column(Float, nullable=False)
    memory = Column(Float, nullable=False)
    disk = Column(Float, nullable=False)
    uptime = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)


class ExecutionMetric(Base):
    """
    SQLAlchemy database model for tracking latency and success of agents, APIs, and services.
    """
    __tablename__ = "execution_metrics"

    id = Column(Integer, primary_key=True, index=True)
    component = Column(String, index=True, nullable=False)  # e.g., 'agent:chat_agent', 'api:health'
    execution_time = Column(Float, nullable=False)          # Duration in milliseconds
    success = Column(Boolean, nullable=False)
    error = Column(String, nullable=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
