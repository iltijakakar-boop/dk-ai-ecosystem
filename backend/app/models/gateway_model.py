from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from app.db.session import Base


class ProviderUsage(Base):
    """
    SQLAlchemy model tracking LLM completions usage, cost, and latency metrics.
    """

    __tablename__ = "provider_usages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    provider = Column(String, index=True, nullable=False)
    model = Column(String, index=True, nullable=False)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost = Column(Float, default=0.0, nullable=False)
    latency_ms = Column(Float, default=0.0, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)


class ProviderHealth(Base):
    """
    SQLAlchemy model monitoring active provider statuses, latency metrics, and circuit states.
    """

    __tablename__ = "provider_healths"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, unique=True, index=True, nullable=False)
    status = Column(
        String, default="healthy", nullable=False
    )  # healthy, degraded, down
    latency = Column(Float, default=0.0, nullable=False)
    last_check = Column(DateTime, default=func.now(), nullable=False)


class ModelRegistry(Base):
    """
    SQLAlchemy model holding model specifications, deprecations, active controls, and capability tags.
    """

    __tablename__ = "registered_models"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, index=True, nullable=False)
    model_name = Column(String, index=True, nullable=False)
    model_version = Column(String, nullable=False)
    release_date = Column(String, nullable=True)
    deprecated = Column(Boolean, default=False, nullable=False)
    recommended = Column(Boolean, default=True, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    capabilities = Column(
        String, default="[]", nullable=False
    )  # JSON-serialized list of capability strings
    max_context_tokens = Column(Integer, default=8192, nullable=False)
    max_output_tokens = Column(Integer, default=2048, nullable=False)
