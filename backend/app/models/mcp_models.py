import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from app.db.session import Base


class MCPServer(Base):
    """
    Model Context Protocol (MCP) Server configurations scoped to workspaces.
    """
    __tablename__ = "mcp_servers"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)  # Endpoint URL (SSE or HTTP)
    status = Column(String, default="offline", nullable=False)  # online, offline
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class MCPClient(Base):
    """
    Model Context Protocol (MCP) Client configuration bindings.
    """
    __tablename__ = "mcp_clients"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    client_name = Column(String, nullable=False)
    status = Column(String, default="active", nullable=False)


class MCPConnection(Base):
    """
    Connection logging tracking protocol connection details.
    """
    __tablename__ = "mcp_connections"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    server_id = Column(Integer, ForeignKey("mcp_servers.id", ondelete="CASCADE"), nullable=False)
    connection_type = Column(String, default="sse", nullable=False)  # sse, http
    status = Column(String, default="connected", nullable=False)
    connected_at = Column(DateTime, default=func.now(), nullable=False)


class ToolRegistry(Base):
    """
    Universal Tool Registry root node.
    """
    __tablename__ = "mcp_tool_registries"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class ToolDefinition(Base):
    """
    Definition schema representing specific registry tools (e.g. OpenAI call or custom REST).
    """
    __tablename__ = "mcp_tool_definitions"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    input_schema = Column(Text, nullable=True, default="{}")  # JSON schema representation
    execution_type = Column(String, nullable=False)  # native, python, mcp, rest
    endpoint_url = Column(String, nullable=True)


class ToolCategory(Base):
    """
    Categorizes tools in the registry.
    """
    __tablename__ = "mcp_tool_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)


class ToolPermission(Base):
    """
    Permissions mappings checking agent scopes before executing specific tools.
    """
    __tablename__ = "mcp_tool_permissions"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    tool_name = Column(String, nullable=False)
    allowed_scopes = Column(String, nullable=False)  # Comma-separated allowed scopes


class ToolExecution(Base):
    """
    Active execution session tracking tool invoke tasks.
    """
    __tablename__ = "mcp_tool_executions"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    tool_name = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending, completed, failed


class MCPToolExecutionLog(Base):
    """
    Auditing log capturing visual tool execution variables, performance, and values.
    """
    __tablename__ = "mcp_tool_execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    tool_name = Column(String, nullable=False)
    input_params = Column(Text, nullable=True)
    output_result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=False)
    executed_at = Column(DateTime, default=func.now(), nullable=False)


class Connector(Base):
    """
    Integration configuration matching external services (GitHub, Slack, Databases).
    """
    __tablename__ = "mcp_connectors"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # slack, gemini, github, postgres
    enabled = Column(Boolean, default=True, nullable=False)


class ConnectorCredential(Base):
    """
    Encrypted access tokens or API keys matching an integration connector.
    """
    __tablename__ = "mcp_connector_credentials"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    connector_id = Column(Integer, ForeignKey("mcp_connectors.id", ondelete="CASCADE"), nullable=False)
    encrypted_credential = Column(Text, nullable=False)


class ConnectorSecret(Base):
    """
    Encrypted secrets associated with connectors.
    """
    __tablename__ = "mcp_connector_secrets"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    connector_id = Column(Integer, ForeignKey("mcp_connectors.id", ondelete="CASCADE"), nullable=False)
    encrypted_secret = Column(Text, nullable=False)


class WebhookEndpoint(Base):
    """
    Central dispatch target webhook configurations.
    """
    __tablename__ = "mcp_webhook_endpoints"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    url = Column(String, nullable=False)
    secret_token = Column(String, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)


class WebhookEvent(Base):
    """
    Events mapping webhook subscriptions.
    """
    __tablename__ = "mcp_webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("mcp_webhook_endpoints.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String, nullable=False)  # e.g. agent_finished, workflow_completed


class WebhookDelivery(Base):
    """
    Log of webhook execution deliver tasks.
    """
    __tablename__ = "mcp_webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("mcp_webhook_endpoints.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String, nullable=False)
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    delivered_at = Column(DateTime, default=func.now(), nullable=False)


class RemoteEndpoint(Base):
    """
    Endpoint parameters scoping visual remote tool servers.
    """
    __tablename__ = "mcp_remote_endpoints"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    url = Column(String, nullable=False)
    auth_header = Column(String, nullable=True)


class RemoteSession(Base):
    """
    Active execution session tracking remote integrations auth keys.
    """
    __tablename__ = "mcp_remote_sessions"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class ToolVersion(Base):
    """
    Immutable tool definitions version history.
    """
    __tablename__ = "mcp_tool_versions"

    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(Integer, ForeignKey("mcp_tool_definitions.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    input_schema = Column(Text, nullable=False)


class ToolDependency(Base):
    """
    Declares visual tools integration dependencies.
    """
    __tablename__ = "mcp_tool_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(Integer, ForeignKey("mcp_tool_definitions.id", ondelete="CASCADE"), nullable=False)
    dependency_tool_name = Column(String, nullable=False)


class ToolUsageStatistics(Base):
    """
    Aggregated usage metrics tracking tool execution metrics.
    """
    __tablename__ = "mcp_tool_usage_statistics"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    tool_name = Column(String, nullable=False)
    calls_count = Column(Integer, default=0, nullable=False)
    errors_count = Column(Integer, default=0, nullable=False)
    total_duration_ms = Column(Float, default=0.0, nullable=False)
