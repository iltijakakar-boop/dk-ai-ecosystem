import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.sql import func
from app.db.session import Base

class Tool(Base):
    """
    Persisted metadata for both built-in and plugin tools.
    """
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    category = Column(String, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class Plugin(Base):
    """
    Registered external plugin configurations.
    """
    __tablename__ = "plugins"

    id = Column(Integer, primary_key=True, index=True)
    plugin_id = Column(String, unique=True, index=True, nullable=False)
    version = Column(String, nullable=False)
    status = Column(String, default="active", nullable=False)  # active, disabled, error
    installed_at = Column(DateTime, default=func.now(), nullable=False)


class ToolExecutionLog(Base):
    """
    Auditing table for capturing execution details, timeouts, and errors.
    """
    __tablename__ = "tool_execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()), nullable=False)
    session_id = Column(String, index=True, nullable=True)
    user_id = Column(Integer, index=True, nullable=True)
    agent_id = Column(String, index=True, nullable=True)
    tool_id = Column(String, index=True, nullable=False)
    duration_ms = Column(Float, nullable=False)
    status = Column(String, nullable=False)  # success, error
    input = Column(Text, nullable=True)
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
