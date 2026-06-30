from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelRegistryCreate(BaseModel):
    workspace_id: int
    name: str
    description: Optional[str] = None


class ModelRegistryResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str]
    is_archived: bool

    class Config:
        from_attributes = True


class ModelVersionCreate(BaseModel):
    model_id: int
    version: str
    configuration: Optional[str] = None


class ModelVersionResponse(BaseModel):
    id: int
    model_id: int
    version: str
    configuration: Optional[str]

    class Config:
        from_attributes = True


class DatasetCreate(BaseModel):
    workspace_id: int
    name: str
    description: Optional[str] = None


class DatasetResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


class TrainingJobCreate(BaseModel):
    workspace_id: int
    dataset_id: int


class TrainingJobResponse(BaseModel):
    id: int
    workspace_id: int
    status: str
    dataset_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FineTuningJobCreate(BaseModel):
    workspace_id: int
    model_id: int


class FineTuningJobResponse(BaseModel):
    id: int
    workspace_id: int
    model_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class GPUWorkerResponse(BaseModel):
    id: int
    name: str
    load_percent: float

    class Config:
        from_attributes = True
