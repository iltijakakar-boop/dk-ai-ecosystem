from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.mcp import (
    MCPServerCreate,
    MCPServerResponse,
    ToolDefinitionCreate,
    ToolDefinitionResponse,
    ConnectorCreate,
    ConnectorResponse,
    ConnectorCredentialCreate,
    WebhookEndpointCreate,
    WebhookEndpointResponse,
    ToolUsageStatisticsResponse,
)
from app.services.mcp_service import mcp_service
from app.services.tool_registry_service import tool_registry_service
from app.services.connector_service import connector_service
from app.services.credential_service import credential_service
from app.services.webhook_service import webhook_service
from app.services.tool_execution_service import tool_execution_service
from app.services.analytics_service import analytics_service


router = APIRouter(prefix="/mcp", tags=["mcp"])


# --- Request Payloads ---
class ExecuteToolPayload(BaseModel):
    arguments: Dict[str, Any]


# --- MCP Servers ---
@router.post("/servers", response_model=APIResponse[MCPServerResponse])
def register_mcp_server(
    payload: MCPServerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    server = mcp_service.register_server(
        db, workspace_id=payload.workspace_id, name=payload.name, url=payload.url
    )
    return APIResponse(success=True, message="MCP Server registered successfully.", data=MCPServerResponse.model_validate(server))


@router.get("/servers", response_model=APIResponse[List[MCPServerResponse]])
def list_mcp_servers(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    servers = mcp_service.get_servers(db, workspace_id)
    res = [MCPServerResponse.model_validate(s) for s in servers]
    return APIResponse(success=True, data=res)


@router.post("/servers/{id}/connect", response_model=APIResponse)
def connect_mcp_server(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    conn = mcp_service.establish_connection(db, server_id=id)
    return APIResponse(
        success=True,
        message="Connection handshake initiated.",
        data={"connection_id": conn.id, "status": conn.status, "type": conn.connection_type},
    )


@router.post("/servers/{id}/ping", response_model=APIResponse)
def ping_mcp_server_heartbeat(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    online = mcp_service.ping_heartbeat(db, server_id=id)
    return APIResponse(
        success=True,
        message="Heartbeat verification completed.",
        data={"online": online},
    )


# --- Tool Registry ---
@router.post("/tools", response_model=APIResponse[ToolDefinitionResponse])
def register_tool_definition(
    payload: ToolDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    tool = tool_registry_service.register_tool(
        db,
        workspace_id=payload.workspace_id,
        name=payload.name,
        description=payload.description,
        input_schema=payload.input_schema,
        execution_type=payload.execution_type,
        endpoint_url=payload.endpoint_url,
    )
    return APIResponse(success=True, message="Tool registered successfully.", data=ToolDefinitionResponse.model_validate(tool))


@router.get("/tools", response_model=APIResponse[List[ToolDefinitionResponse]])
def list_tool_registry_tools(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    tools = tool_registry_service.get_tools(db, workspace_id)
    res = [ToolDefinitionResponse.model_validate(t) for t in tools]
    return APIResponse(success=True, data=res)


@router.post("/tools/{id}/execute", response_model=APIResponse)
def execute_registry_tool(
    id: int,
    payload: ExecuteToolPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Verify strict scoping
    tool = tool_registry_service.get_tool(db, id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found.")

    res = tool_execution_service.execute_tool(
        db, workspace_id=tool.workspace_id, tool_id=id, arguments=payload.arguments
    )
    return APIResponse(success=True, message="Tool execution finished.", data=res)


# --- Connectors ---
@router.post("/connectors", response_model=APIResponse[ConnectorResponse])
def create_connector(
    payload: ConnectorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    conn = connector_service.create_connector(
        db, workspace_id=payload.workspace_id, name=payload.name, connector_type=payload.type, enabled=payload.enabled
    )
    return APIResponse(success=True, message="Connector created successfully.", data=ConnectorResponse.model_validate(conn))


@router.get("/connectors", response_model=APIResponse[List[ConnectorResponse]])
def list_connectors(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    conns = connector_service.get_connectors(db, workspace_id)
    res = [ConnectorResponse.model_validate(c) for c in conns]
    return APIResponse(success=True, data=res)


@router.post("/connectors/{id}/credentials", response_model=APIResponse)
def save_connector_credentials(
    id: int,
    payload: ConnectorCredentialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    cred = credential_service.save_credential(
        db, workspace_id=payload.workspace_id, connector_id=id, credential_data=payload.credential_data
    )
    return APIResponse(success=True, message="Connector credentials saved and encrypted successfully.")


# --- Webhooks ---
@router.post("/webhooks", response_model=APIResponse[WebhookEndpointResponse])
def create_webhook_endpoint(
    payload: WebhookEndpointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    end = webhook_service.create_endpoint(
        db,
        workspace_id=payload.workspace_id,
        url=payload.url,
        secret_token=payload.secret_token,
        event_types=payload.event_types,
    )
    return APIResponse(success=True, message="Webhook endpoint created successfully.", data=WebhookEndpointResponse.model_validate(end))


# --- Analytics ---
@router.get("/analytics", response_model=APIResponse[List[ToolUsageStatisticsResponse]])
def get_workspace_tool_analytics(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    stats = analytics_service.get_tool_statistics(db, workspace_id=workspace_id)
    res = [ToolUsageStatisticsResponse.model_validate(s) for s in stats]
    return APIResponse(success=True, data=res)
