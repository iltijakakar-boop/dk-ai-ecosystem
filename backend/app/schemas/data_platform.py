from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DPDatasetCreate(BaseModel):
    workspace_id: int
    name: str
    format: str


class DPDatasetResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    format: str

    class Config:
        from_attributes = True


class DPFeatureGroupCreate(BaseModel):
    workspace_id: int
    name: str


class DPFeatureGroupResponse(BaseModel):
    id: int
    workspace_id: int
    name: str

    class Config:
        from_attributes = True


class DPVectorDatasetCreate(BaseModel):
    workspace_id: int
    name: str


class DPVectorDatasetResponse(BaseModel):
    id: int
    workspace_id: int
    name: str

    class Config:
        from_attributes = True


class DPDataQualityReportResponse(BaseModel):
    id: int
    dataset_id: int
    score: float

    class Config:
        from_attributes = True
