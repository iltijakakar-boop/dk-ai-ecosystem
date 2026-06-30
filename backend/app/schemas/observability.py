from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ObsSystemMetricCreate(BaseModel):
    workspace_id: int
    cpu_percent: float
    memory_percent: float
    gpu_percent: Optional[float] = None


class ObsSystemMetricResponse(BaseModel):
    id: int
    workspace_id: int
    cpu_percent: float
    memory_percent: float
    gpu_percent: Optional[float]
    timestamp: datetime

    class Config:
        from_attributes = True


class ObsLogEntryCreate(BaseModel):
    workspace_id: int
    log_level: str
    message: str


class ObsLogEntryResponse(BaseModel):
    id: int
    workspace_id: int
    log_level: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True


class ObsTraceResponse(BaseModel):
    id: int
    workspace_id: int
    trace_id: str
    name: str
    duration_ms: float
    created_at: datetime

    class Config:
        from_attributes = True


class ObsAlertRuleCreate(BaseModel):
    workspace_id: int
    metric_name: str
    threshold: float


class ObsAlertRuleResponse(BaseModel):
    id: int
    workspace_id: int
    metric_name: str
    threshold: float
    enabled: bool

    class Config:
        from_attributes = True


class ObsAlertResponse(BaseModel):
    id: int
    rule_id: int
    message: str
    resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ObsIncidentCreate(BaseModel):
    workspace_id: int
    title: str
    severity: str


class ObsIncidentResponse(BaseModel):
    id: int
    workspace_id: int
    title: str
    severity: str
    status: str

    class Config:
        from_attributes = True
