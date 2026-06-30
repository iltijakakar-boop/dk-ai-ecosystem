import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.db.session import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    plan = Column(String, default="Free", nullable=False)
    status = Column(String, default="Active", nullable=False)
    logo = Column(String, nullable=True)
    colors = Column(String, nullable=True)
    custom_domain = Column(String, nullable=True)
    support_email = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    settings = Column(String, nullable=True, default="{}")
    quotas = Column(String, nullable=True, default="{}")
    created_at = Column(DateTime, default=func.now(), nullable=False)


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, default="Member", nullable=False)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    joined_at = Column(DateTime, default=func.now(), nullable=False)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="Active", nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String, nullable=False)
    key_hash = Column(String, unique=True, index=True, nullable=False)
    permissions = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class ServiceAccount(Base):
    __tablename__ = "service_accounts"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    permissions = Column(String, nullable=True)
    status = Column(String, default="Active", nullable=False)


class Secret(Base):
    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    encrypted_value = Column(String, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    category = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class SecretVersion(Base):
    __tablename__ = "secret_versions"

    id = Column(Integer, primary_key=True, index=True)
    secret_id = Column(Integer, ForeignKey("secrets.id"), nullable=False)
    encrypted_value = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class OrganizationInvitation(Base):
    __tablename__ = "organization_invitations"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    email = Column(String, index=True, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default="Member", nullable=False)
    status = Column(String, default="Pending", nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    tokens = Column(Integer, default=0, nullable=False)
    requests = Column(Integer, default=0, nullable=False)
    storage_used = Column(Integer, default=0, nullable=False)
    vector_usage = Column(Integer, default=0, nullable=False)
    automation_usage = Column(Integer, default=0, nullable=False)
    workflow_usage = Column(Integer, default=0, nullable=False)
    bandwidth = Column(Integer, default=0, nullable=False)
    cpu_usage = Column(Integer, default=0, nullable=False)
    gpu_usage = Column(Integer, default=0, nullable=False)
    memory_usage = Column(Integer, default=0, nullable=False)
    response_latency_ms = Column(Integer, default=0, nullable=False)
    error_rate = Column(Integer, default=0, nullable=False)
    estimated_cost = Column(Integer, default=0, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)


class EnterpriseAuditLog(Base):
    __tablename__ = "enterprise_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, index=True, nullable=False)
    resource_id = Column(String, index=True, nullable=True)
    details = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
