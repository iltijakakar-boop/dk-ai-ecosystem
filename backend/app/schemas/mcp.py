import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class MCPServerCreate(BaseModel):
    workspace_id: int
    name: str
    url: str


class MCPServerResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    url: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MCPClientResponse(BaseModel):
    id: int
    workspace_id: int
    client_name: str
    status: str

    class Config:
        from_attributes = True


class ToolDefinitionCreate(BaseModel):
    workspace_id: int
    name: str
    description: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    execution_type: str  # native, python, mcp, rest
    endpoint_url: Optional[str] = None


class ToolDefinitionResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str]
    input_schema: Dict[str, Any]
    execution_type: str
    endpoint_url: Optional[str]

    @field_validator("input_schema", mode="before")
    @classmethod
    def parse_schema(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v or {}

    class Config:
        from_attributes = True


class ToolPermissionCreate(BaseModel):
    workspace_id: int
    tool_name: str
    allowed_scopes: List[str]


class ToolPermissionResponse(BaseModel):
    id: int
    workspace_id: int
    tool_name: str
    allowed_scopes: List[str]

    @field_validator("allowed_scopes", mode="before")
    @classmethod
    def parse_scopes(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v or []

    class Config:
        from_attributes = True


class ConnectorCreate(BaseModel):
    workspace_id: int
    name: str
    type: str  # slack, gemini, github, postgres
    enabled: bool = True


class ConnectorResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    type: str
    enabled: bool

    class Config:
        from_attributes = True


class ConnectorCredentialCreate(BaseModel):
    workspace_id: int
    connector_id: int
    credential_data: Dict[str, Any]


class ConnectorCredentialResponse(BaseModel):
    id: int
    workspace_id: int
    connector_id: int
    encrypted_credential: str

    class Config:
        from_attributes = True


class WebhookEndpointCreate(BaseModel):
    workspace_id: int
    url: str
    secret_token: str
    enabled: bool = True
    event_types: List[str]


class WebhookEndpointResponse(BaseModel):
    id: int
    workspace_id: int
    url: str
    enabled: bool

    class Config:
        from_attributes = True


class WebhookDeliveryResponse(BaseModel):
    id: int
    endpoint_id: int
    event_type: str
    status_code: Optional[int]
    response_body: Optional[str]
    delivered_at: datetime

    class Config:
        from_attributes = True


class ToolUsageStatisticsResponse(BaseModel):
    id: int
    workspace_id: int
    tool_name: str
    calls_count: int
    errors_count: int
    total_duration_ms: float

    class Config:
        from_attributes = True
