from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.model_management import (
    ModelRegistryCreate,
    ModelRegistryResponse,
    ModelVersionCreate,
    ModelVersionResponse,
    DatasetCreate,
    DatasetResponse,
    TrainingJobResponse,
    FineTuningJobCreate,
    FineTuningJobResponse,
    GPUWorkerResponse,
)
from app.services.model_management_service import (
    model_registry_service,
    dataset_service,
    training_service,
    fine_tuning_service,
    gpu_scheduler_service,
)


router = APIRouter(prefix="/model-management", tags=["model-management"])


@router.post("/models", response_model=APIResponse[ModelRegistryResponse])
def register_model_in_registry(
    payload: ModelRegistryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    model = model_registry_service.register_model(db, workspace_id=payload.workspace_id, name=payload.name, description=payload.description)
    return APIResponse(success=True, message="Model registered successfully.", data=ModelRegistryResponse.model_validate(model))


@router.get("/models", response_model=APIResponse[List[ModelRegistryResponse]])
def list_registered_models(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    models = model_registry_service.get_models(db, workspace_id)
    res = [ModelRegistryResponse.model_validate(m) for m in models]
    return APIResponse(success=True, data=res)


@router.post("/models/{id}/versions", response_model=APIResponse[ModelVersionResponse])
def create_model_version(
    id: int,
    payload: ModelVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ver = model_registry_service.create_version(db, model_id=id, version=payload.version, configuration=payload.configuration)
    return APIResponse(success=True, message="Model version recorded.", data=ModelVersionResponse.model_validate(ver))


@router.post("/datasets", response_model=APIResponse[DatasetResponse])
def create_dataset_record(
    payload: DatasetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ds = dataset_service.create_dataset(db, workspace_id=payload.workspace_id, name=payload.name, description=payload.description)
    return APIResponse(success=True, message="Dataset recorded.", data=DatasetResponse.model_validate(ds))


@router.get("/datasets", response_model=APIResponse[List[DatasetResponse]])
def list_datasets(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ds = dataset_service.get_datasets(db, workspace_id)
    res = [DatasetResponse.model_validate(d) for d in ds]
    return APIResponse(success=True, data=res)


@router.post("/fine-tune", response_model=APIResponse[FineTuningJobResponse])
def start_model_fine_tuning(
    payload: FineTuningJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    job = fine_tuning_service.start_fine_tuning(db, workspace_id=payload.workspace_id, model_id=payload.model_id)
    return APIResponse(success=True, message="Fine-tuning job started.", data=FineTuningJobResponse.model_validate(job))


@router.get("/gpu-workers", response_model=APIResponse[List[GPUWorkerResponse]])
def list_gpu_workers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    workers = gpu_scheduler_service.get_workers(db)
    res = [GPUWorkerResponse.model_validate(w) for w in workers]
    return APIResponse(success=True, data=res)
