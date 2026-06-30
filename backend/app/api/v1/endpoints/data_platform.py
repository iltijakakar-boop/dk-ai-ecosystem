from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.data_platform import (
    DPDatasetCreate,
    DPDatasetResponse,
    DPFeatureGroupCreate,
    DPFeatureGroupResponse,
    DPVectorDatasetCreate,
    DPVectorDatasetResponse,
    DPDataQualityReportResponse,
)
from app.services.data_platform_service import (
    dataset_service,
    feature_store_service,
    vector_dataset_service,
    data_quality_service,
)


router = APIRouter(prefix="/data-platform", tags=["data-platform"])


@router.post("/datasets", response_model=APIResponse[DPDatasetResponse])
def register_lakehouse_dataset(
    payload: DPDatasetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ds = dataset_service.create_dataset(db, workspace_id=payload.workspace_id, name=payload.name, format=payload.format)
    return APIResponse(success=True, message="Lakehouse dataset registered.", data=DPDatasetResponse.model_validate(ds))


@router.get("/datasets", response_model=APIResponse[List[DPDatasetResponse]])
def get_datasets_list(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    datasets = dataset_service.get_datasets(db, workspace_id)
    res = [DPDatasetResponse.model_validate(d) for d in datasets]
    return APIResponse(success=True, data=res)


@router.post("/feature-groups", response_model=APIResponse[DPFeatureGroupResponse])
def create_feature_group_store(
    payload: DPFeatureGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    group = feature_store_service.create_feature_group(db, workspace_id=payload.workspace_id, name=payload.name)
    return APIResponse(success=True, message="Feature group created.", data=DPFeatureGroupResponse.model_validate(group))


@router.get("/feature-groups", response_model=APIResponse[List[DPFeatureGroupResponse]])
def get_feature_groups_list(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    groups = feature_store_service.get_feature_groups(db, workspace_id)
    res = [DPFeatureGroupResponse.model_validate(g) for g in groups]
    return APIResponse(success=True, data=res)


@router.post("/vector-datasets", response_model=APIResponse[DPVectorDatasetResponse])
def create_vector_embedding_index(
    payload: DPVectorDatasetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    vec = vector_dataset_service.create_vector_dataset(db, workspace_id=payload.workspace_id, name=payload.name)
    return APIResponse(success=True, message="Vector dataset embedding index created.", data=DPVectorDatasetResponse.model_validate(vec))


@router.get("/vector-datasets", response_model=APIResponse[List[DPVectorDatasetResponse]])
def get_vector_datasets_list(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    datasets = vector_dataset_service.get_vector_datasets(db, workspace_id)
    res = [DPVectorDatasetResponse.model_validate(v) for v in datasets]
    return APIResponse(success=True, data=res)


@router.post("/vector-datasets/search")
def search_similar_embeddings(
    vector_dataset_id: int,
    query_vector: List[float],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    matches = vector_dataset_service.query_similarity_search(db, vector_dataset_id=vector_dataset_id, query_vector=query_vector)
    return APIResponse(success=True, data=matches)


@router.post("/datasets/{id}/quality-check", response_model=APIResponse[DPDataQualityReportResponse])
def run_dataset_quality_evaluation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    report = data_quality_service.execute_quality_checks(db, dataset_id=id)
    return APIResponse(success=True, message="Data quality evaluation checks completed.", data=DPDataQualityReportResponse.model_validate(report))
