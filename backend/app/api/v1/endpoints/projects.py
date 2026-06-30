from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.services.project_service import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    workspace_id: int
    name: str
    description: Optional[str] = None


class ProjectStatusUpdate(BaseModel):
    status: str


@router.post("", response_model=APIResponse)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    proj = project_service.create_project(
        db,
        workspace_id=payload.workspace_id,
        name=payload.name,
        description=payload.description,
        creator_id=current_user.id,
    )
    return APIResponse(
        success=True,
        message="Project created successfully.",
        data={
            "id": proj.id,
            "workspace_id": proj.workspace_id,
            "name": proj.name,
            "description": proj.description,
            "status": proj.status,
        },
    )


@router.get("", response_model=APIResponse)
def list_projects(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    projects = project_service.get_projects(db, workspace_id=workspace_id)
    data = [
        {
            "id": p.id,
            "workspace_id": p.workspace_id,
            "name": p.name,
            "description": p.description,
            "status": p.status,
        }
        for p in projects
    ]
    return APIResponse(success=True, data=data)


@router.put("/{id}/status", response_model=APIResponse)
def update_project_status(
    id: int,
    payload: ProjectStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    proj = project_service.update_project_status(
        db, project_id=id, status_str=payload.status
    )
    return APIResponse(
        success=True,
        message="Project status updated successfully.",
        data={"id": proj.id, "status": proj.status},
    )
