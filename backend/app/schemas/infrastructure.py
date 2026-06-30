from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class InfraClusterCreate(BaseModel):
    workspace_id: int
    name: str
    api_endpoint: str


class InfraClusterResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    api_endpoint: str
    status: str

    class Config:
        from_attributes = True


class InfraDeploymentCreate(BaseModel):
    workspace_id: int
    cluster_id: int
    name: str
    replicas: int


class InfraDeploymentResponse(BaseModel):
    id: int
    workspace_id: int
    cluster_id: int
    name: str
    replicas: int

    class Config:
        from_attributes = True


class InfraPodResponse(BaseModel):
    id: int
    deployment_id: int
    name: str
    status: str
    cpu_cores: float

    class Config:
        from_attributes = True


class InfraEdgeNodeCreate(BaseModel):
    workspace_id: int
    name: str


class InfraEdgeNodeResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    status: str
    sync_status: str

    class Config:
        from_attributes = True


class InfraBackupPolicyCreate(BaseModel):
    workspace_id: int
    frequency: str


class InfraBackupPolicyResponse(BaseModel):
    id: int
    workspace_id: int
    frequency: str

    class Config:
        from_attributes = True
