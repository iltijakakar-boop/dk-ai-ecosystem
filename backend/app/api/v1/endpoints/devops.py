from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.devops import (
    DevOpsPipelineCreate,
    DevOpsPipelineResponse,
    DevOpsPipelineRunResponse,
    DevOpsReleaseCreate,
    DevOpsReleaseResponse,
    DevOpsApprovalRequestResponse,
    DevOpsContainerImageCreate,
    DevOpsContainerImageResponse,
)
from app.services.devops_service import (
    pipeline_service,
    release_service,
    approval_service,
    container_registry_service,
)


router = APIRouter(prefix="/devops", tags=["devops"])


@router.post("/pipelines", response_model=APIResponse[DevOpsPipelineResponse])
def create_build_pipeline(
    payload: DevOpsPipelineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    pipe = pipeline_service.create_pipeline(db, workspace_id=payload.workspace_id, name=payload.name)
    return APIResponse(success=True, message="CI/CD Pipeline created successfully.", data=DevOpsPipelineResponse.model_validate(pipe))


@router.get("/pipelines", response_model=APIResponse[List[DevOpsPipelineResponse]])
def get_pipelines_list(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    pipes = pipeline_service.get_pipelines(db, workspace_id)
    res = [DevOpsPipelineResponse.model_validate(p) for p in pipes]
    return APIResponse(success=True, data=res)


@router.post("/pipelines/{id}/run", response_model=APIResponse[DevOpsPipelineRunResponse])
def trigger_pipeline_run(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    run = pipeline_service.run_pipeline(db, pipeline_id=id)
    return APIResponse(success=True, message="Pipeline run initiated.", data=DevOpsPipelineRunResponse.model_validate(run))


@router.post("/releases", response_model=APIResponse[DevOpsReleaseResponse])
def create_new_release_tag(
    payload: DevOpsReleaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    rel = release_service.create_release(db, workspace_id=payload.workspace_id, version=payload.version)
    return APIResponse(success=True, message="Release registered successfully.", data=DevOpsReleaseResponse.model_validate(rel))


@router.post("/rollback")
def execute_release_rollback(
    workspace_id: int,
    current_release_id: int,
    target_release_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    rollback = release_service.trigger_rollback(
        db,
        workspace_id=workspace_id,
        current_rel_id=current_release_id,
        target_rel_id=target_release_id,
    )
    return APIResponse(success=True, message="Rollback executed successfully.")


@router.post("/approvals", response_model=APIResponse[DevOpsApprovalRequestResponse])
def create_change_approval_request(
    workspace_id: int,
    release_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    req = approval_service.request_approval(db, workspace_id=workspace_id, release_id=release_id)
    return APIResponse(success=True, message="Approval ticket created.", data=DevOpsApprovalRequestResponse.model_validate(req))


@router.get("/approvals", response_model=APIResponse[List[DevOpsApprovalRequestResponse]])
def get_pending_approvals_list(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    reqs = approval_service.get_pending_approvals(db, workspace_id)
    res = [DevOpsApprovalRequestResponse.model_validate(r) for r in reqs]
    return APIResponse(success=True, data=res)


@router.post("/approvals/{id}/action", response_model=APIResponse[DevOpsApprovalRequestResponse])
def process_approval_gate(
    id: int,
    approve: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    req = approval_service.process_approval(db, request_id=id, approve=approve)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    return APIResponse(success=True, message="Gate action processed successfully.", data=DevOpsApprovalRequestResponse.model_validate(req))


@router.post("/registry/images", response_model=APIResponse[DevOpsContainerImageResponse])
def register_container_image(
    payload: DevOpsContainerImageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    img = container_registry_service.register_image(
        db,
        workspace_id=payload.workspace_id,
        name=payload.name,
        tag=payload.tag,
        digest=payload.digest,
    )
    return APIResponse(success=True, message="Docker container image registered.", data=DevOpsContainerImageResponse.model_validate(img))


@router.get("/registry/images", response_model=APIResponse[List[DevOpsContainerImageResponse]])
def get_registry_images_list(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    imgs = container_registry_service.get_images(db, workspace_id)
    res = [DevOpsContainerImageResponse.model_validate(i) for i in imgs]
    return APIResponse(success=True, data=res)
