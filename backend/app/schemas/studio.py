import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# --- Projects ---
class AgentStudioProjectCreate(BaseModel):
    workspace_id: int = Field(..., example=1)
    name: str = Field(..., example="Customer Support System")
    description: Optional[str] = Field(None, example="Automated customer ticket processing multi-agent project.")


class AgentStudioProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Updated Project Name")
    description: Optional[str] = Field(None, example="Updated description.")


class AgentStudioProjectResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Canvases ---
class WorkflowCanvasCreate(BaseModel):
    workspace_id: int
    project_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None


class WorkflowCanvasUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None


class WorkflowCanvasResponse(BaseModel):
    id: int
    project_id: Optional[int]
    workspace_id: int
    name: str
    description: Optional[str]
    definition: Dict[str, Any]
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("definition", mode="before")
    @classmethod
    def parse_definition(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v or {}

    class Config:
        from_attributes = True


# --- Nodes & Edges ---
class WorkflowNodeCreate(BaseModel):
    node_id: str
    type: str
    label: str
    config_data: Optional[Dict[str, Any]] = None
    pos_x: float = 0.0
    pos_y: float = 0.0


class WorkflowNodeResponse(BaseModel):
    id: int
    canvas_id: int
    node_id: str
    type: str
    label: str
    config_data: Dict[str, Any]
    pos_x: float
    pos_y: float

    @field_validator("config_data", mode="before")
    @classmethod
    def parse_config(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v or {}

    class Config:
        from_attributes = True


class WorkflowEdgeCreate(BaseModel):
    edge_id: str
    source_node: str
    target_node: str
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None


class WorkflowEdgeResponse(BaseModel):
    id: int
    canvas_id: int
    edge_id: str
    source_node: str
    target_node: str
    source_handle: Optional[str]
    target_handle: Optional[str]

    class Config:
        from_attributes = True


# --- Canvas Layout ---
class CanvasLayoutUpdate(BaseModel):
    grid_size: Optional[int] = None
    zoom: Optional[float] = None
    pan_x: Optional[float] = None
    pan_y: Optional[float] = None
    theme: Optional[str] = None


class CanvasLayoutResponse(BaseModel):
    id: int
    canvas_id: int
    grid_size: int
    zoom: float
    pan_x: float
    pan_y: float
    theme: str

    class Config:
        from_attributes = True


# --- Prompts ---
class PromptTemplateCreate(BaseModel):
    workspace_id: int
    name: str
    description: Optional[str] = None
    template_text: str
    variables: Optional[List[str]] = None


class PromptTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    template_text: Optional[str] = None
    variables: Optional[List[str]] = None


class PromptTemplateResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str]
    template_text: str
    variables: List[str]

    @field_validator("variables", mode="before")
    @classmethod
    def parse_variables(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v or []

    class Config:
        from_attributes = True


class PromptVersionResponse(BaseModel):
    id: int
    prompt_id: int
    version: int
    template_text: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Agent Templates ---
class AgentTemplateCreate(BaseModel):
    workspace_id: int
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: str
    temperature: float = 0.7
    config_data: Optional[Dict[str, Any]] = None


class AgentTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    config_data: Optional[Dict[str, Any]] = None


class AgentTemplateResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str]
    system_prompt: Optional[str]
    model: str
    temperature: float
    config_data: Dict[str, Any]

    @field_validator("config_data", mode="before")
    @classmethod
    def parse_config(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v or {}

    class Config:
        from_attributes = True


class AgentVersionResponse(BaseModel):
    id: int
    agent_template_id: int
    version: int
    system_prompt: Optional[str]
    config_data: Dict[str, Any]
    created_at: datetime

    @field_validator("config_data", mode="before")
    @classmethod
    def parse_config(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v or {}

    class Config:
        from_attributes = True


# --- Pipelines ---
class PipelineCreate(BaseModel):
    workspace_id: int
    name: str
    description: Optional[str] = None
    type: str
    definition: Optional[Dict[str, Any]] = None


class PipelineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None


class PipelineResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str]
    type: str
    definition: Dict[str, Any]

    @field_validator("definition", mode="before")
    @classmethod
    def parse_definition(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v or {}

    class Config:
        from_attributes = True


class PipelineVersionResponse(BaseModel):
    id: int
    pipeline_id: int
    version: int
    definition: Dict[str, Any]
    created_at: datetime

    @field_validator("definition", mode="before")
    @classmethod
    def parse_definition(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v or {}

    class Config:
        from_attributes = True


# --- Deployments ---
class DeploymentCreate(BaseModel):
    workspace_id: int
    canvas_id: Optional[int] = None
    agent_template_id: Optional[int] = None
    pipeline_id: Optional[int] = None
    version: int
    environment: str = "Testing"  # Testing, Staging, Production


class DeploymentResponse(BaseModel):
    id: int
    workspace_id: int
    canvas_id: Optional[int]
    agent_template_id: Optional[int]
    pipeline_id: Optional[int]
    version: int
    environment: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DeploymentHistoryResponse(BaseModel):
    id: int
    deployment_id: int
    action: str
    details: Optional[str]
    performed_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Executions & Debugging ---
class ExecutionSessionCreate(BaseModel):
    workspace_id: int
    entity_type: str
    entity_id: int
    inputs: Optional[Dict[str, Any]] = None


class ExecutionSessionResponse(BaseModel):
    id: int
    workspace_id: int
    entity_type: str
    entity_id: int
    status: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime]

    @field_validator("inputs", "outputs", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v or {}

    class Config:
        from_attributes = True


class DebugSessionResponse(BaseModel):
    id: int
    execution_session_id: Optional[int]
    workspace_id: int
    status: str
    current_step: Optional[str]
    logs: List[Dict[str, Any]]
    variables_state: Dict[str, Any]
    created_at: datetime

    @field_validator("logs", mode="before")
    @classmethod
    def parse_logs(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v or []

    @field_validator("variables_state", mode="before")
    @classmethod
    def parse_vars(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v or {}

    class Config:
        from_attributes = True


# --- Workflow Variables & Triggers ---
class WorkflowVariableCreate(BaseModel):
    name: str
    type: str = "string"
    default_value: Optional[str] = None
    description: Optional[str] = None


class WorkflowVariableResponse(BaseModel):
    id: int
    canvas_id: int
    name: str
    type: str
    default_value: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True


class WorkflowParameterResponse(BaseModel):
    id: int
    canvas_id: int
    name: str
    required: bool
    description: Optional[str]

    class Config:
        from_attributes = True


class WorkflowOutputResponse(BaseModel):
    id: int
    canvas_id: int
    name: str
    source_node: str
    source_property: str

    class Config:
        from_attributes = True


class WorkflowTriggerResponse(BaseModel):
    id: int
    canvas_id: int
    name: str
    type: str
    config_data: Dict[str, Any]

    @field_validator("config_data", mode="before")
    @classmethod
    def parse_config(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v or {}

    class Config:
        from_attributes = True


class WorkflowScheduleResponse(BaseModel):
    id: int
    canvas_id: int
    cron_expression: Optional[str]
    interval_seconds: Optional[int]
    enabled: bool

    class Config:
        from_attributes = True


class WorkflowExecutionResponse(BaseModel):
    id: int
    canvas_id: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class WorkflowLogResponse(BaseModel):
    id: int
    execution_id: int
    node_id: Optional[str]
    log_level: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True
