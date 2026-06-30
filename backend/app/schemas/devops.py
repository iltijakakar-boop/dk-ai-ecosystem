from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DevOpsPipelineCreate(BaseModel):
    workspace_id: int
    name: str


class DevOpsPipelineResponse(BaseModel):
    id: int
    workspace_id: int
    name: str

    class Config:
        from_attributes = True


class DevOpsPipelineRunResponse(BaseModel):
    id: int
    pipeline_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DevOpsReleaseCreate(BaseModel):
    workspace_id: int
    version: str


class DevOpsReleaseResponse(BaseModel):
    id: int
    workspace_id: int
    version: str
    status: str

    class Config:
        from_attributes = True


class DevOpsApprovalRequestResponse(BaseModel):
    id: int
    workspace_id: int
    deployment_id: int
    status: str

    class Config:
        from_attributes = True


class DevOpsContainerImageCreate(BaseModel):
    workspace_id: int
    name: str
    tag: str
    digest: str


class DevOpsContainerImageResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    tag: str
    digest: str

    class Config:
        from_attributes = True
