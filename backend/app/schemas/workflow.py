from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

class WorkflowCreate(BaseModel):
    workflow_id: Optional[str] = Field(None, example="research_and_code_workflow")
    name: str = Field(..., example="Research & Coding Workflow")
    description: Optional[str] = Field(None, example="Automated multi-agent workflow for researching and linting code.")
    definition: Dict[str, Any] = Field(..., example={
        "steps": [
            {
                "name": "research_step",
                "required_capability": "research",
                "input": {"query": "FastAPI best practices"}
            },
            {
                "name": "coding_step",
                "required_capability": "coding",
                "input": {"task": "Write basic API based on research_step.output"}
            }
        ]
    })
    is_template: Optional[bool] = Field(False, example=False)


class WorkflowResponse(BaseModel):
    id: int = Field(..., example=1)
    workflow_id: str = Field(..., example="research_and_code_workflow")
    version: int = Field(..., example=1)
    is_active: bool = Field(..., example=True)
    is_template: bool = Field(..., example=False)
    name: str = Field(..., example="Research & Coding Workflow")
    description: Optional[str] = Field(None, example="Automated multi-agent workflow...")
    definition: Dict[str, Any] = Field(..., example={"steps": []})
    created_at: datetime

    @field_validator("definition", mode="before")
    @classmethod
    def parse_definition_json(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        from_attributes = True


class WorkflowExecutionResponse(BaseModel):
    id: int = Field(..., example=42)
    workflow_id: int = Field(..., example=1)
    status: str = Field(..., example="running", description="pending, running, waiting, completed, failed, cancelled")
    current_step: Optional[str] = Field(None, example="coding_step")
    context: Dict[str, Any] = Field(..., example={"shared_var": "val"})
    started_at: datetime
    completed_at: Optional[datetime] = Field(None)

    @field_validator("context", mode="before")
    @classmethod
    def parse_context_json(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: int = Field(..., example=10)
    workflow_execution_id: int = Field(..., example=42)
    name: str = Field(..., example="coding_step")
    status: str = Field(..., example="completed", description="pending, running, waiting, completed, failed, cancelled")
    required_capability: Optional[str] = Field(None, example="coding")
    input_data: Dict[str, Any] = Field(..., example={})
    output_data: Optional[Dict[str, Any]] = Field(None, example={})
    error: Optional[str] = Field(None)
    retry_count: int = Field(..., example=0)
    max_retries: int = Field(..., example=3)
    timeout_seconds: int = Field(..., example=60)
    created_at: datetime
    updated_at: datetime

    @field_validator("input_data", "output_data", mode="before")
    @classmethod
    def parse_task_jsons(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return {}
            try:
                return json.loads(v)
            except Exception:
                return {}
        return v

    class Config:
        from_attributes = True


class DeadLetterQueueResponse(BaseModel):
    id: int = Field(..., example=1)
    task_id: int = Field(..., example=10)
    workflow_execution_id: int = Field(..., example=42)
    failure_reason: str = Field(..., example="Task timeout exceeded after 3 retries.")
    retry_count: int = Field(..., example=3)
    stack_trace: Optional[str] = Field(None, example="Traceback (most recent call): ...")
    timestamp: datetime

    class Config:
        from_attributes = True


class OrchestratorStatusResponse(BaseModel):
    active_workflows: int = Field(..., example=3)
    running_agents: int = Field(..., example=2)
    queue_length: int = Field(..., example=0)
    average_execution_time_ms: float = Field(..., example=1240.5)
    failed_workflows: int = Field(..., example=1)
    retry_count: int = Field(..., example=2)
