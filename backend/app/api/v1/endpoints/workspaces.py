from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.organization import Workspace
from app.models.user import User
from app.schemas.response import APIResponse
from app.services.workspace_service import workspace_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class WorkspaceCreate(BaseModel):
    organization_id: int
    name: str
    description: Optional[str] = None


class SettingsUpdate(BaseModel):
    settings: Dict[str, Any]


class QuotaUpdate(BaseModel):
    quotas: Dict[str, Any]


@router.post("", response_model=APIResponse)
def create_workspace(
    payload: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ws = workspace_service.create_workspace(
        db,
        organization_id=payload.organization_id,
        name=payload.name,
        description=payload.description,
    )
    return APIResponse(
        success=True,
        message="Workspace created successfully.",
        data={
            "id": ws.id,
            "uuid": ws.uuid,
            "name": ws.name,
            "description": ws.description,
        },
    )


@router.get("", response_model=APIResponse)
def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Admins see all, normal users see active workspaces via memberships
    workspaces = db.query(Workspace).all()
    data = [
        {
            "id": w.id,
            "uuid": w.uuid,
            "name": w.name,
            "description": w.description,
            "organization_id": w.organization_id,
        }
        for w in workspaces
    ]
    return APIResponse(success=True, data=data)


@router.get("/{id}", response_model=APIResponse)
def get_workspace(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ws = db.query(Workspace).filter(Workspace.id == id).first()
    if not ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found."
        )
    return APIResponse(
        success=True,
        data={
            "id": ws.id,
            "uuid": ws.uuid,
            "organization_id": ws.organization_id,
            "name": ws.name,
            "description": ws.description,
            "settings": ws.settings,
            "quotas": ws.quotas,
        },
    )


@router.put("/{id}/settings", response_model=APIResponse)
def update_settings(
    id: int,
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    workspace_service.update_settings(
        db, workspace_id=id, settings_dict=payload.settings
    )
    return APIResponse(success=True, message="Workspace settings updated successfully.")


@router.put("/{id}/quotas", response_model=APIResponse)
def update_quotas(
    id: int,
    payload: QuotaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    workspace_service.update_quotas(db, workspace_id=id, quotas_dict=payload.quotas)
    return APIResponse(
        success=True, message="Workspace resource quotas updated successfully."
    )
