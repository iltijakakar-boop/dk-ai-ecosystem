from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.organization import ServiceAccount
from app.models.user import User
from app.schemas.response import APIResponse
from app.services.service_account_service import service_account_service

router = APIRouter(prefix="/service-accounts", tags=["service-accounts"])


class ServiceAccountCreate(BaseModel):
    workspace_id: int
    name: str
    description: Optional[str] = None
    permissions: List[str] = []


@router.post("", response_model=APIResponse)
def create_service_account(
    payload: ServiceAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    clear_token, sa_obj = service_account_service.create_service_account(
        db,
        workspace_id=payload.workspace_id,
        name=payload.name,
        description=payload.description,
        permissions=payload.permissions,
    )
    return APIResponse(
        success=True,
        message="Service Account bot created successfully.",
        data={
            "id": sa_obj.id,
            "name": sa_obj.name,
            "token": clear_token,
            "permissions": sa_obj.permissions,
        },
    )


@router.get("", response_model=APIResponse)
def list_service_accounts(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sas = (
        db.query(ServiceAccount)
        .filter(ServiceAccount.workspace_id == workspace_id)
        .all()
    )
    data = [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "permissions": s.permissions,
            "status": s.status,
        }
        for s in sas
    ]
    return APIResponse(success=True, data=data)


@router.delete("/{id}", response_model=APIResponse)
def delete_service_account(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sa_obj = db.query(ServiceAccount).filter(ServiceAccount.id == id).first()
    if not sa_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service Account not found."
        )
    db.delete(sa_obj)
    db.commit()
    return APIResponse(success=True, message="Service Account deleted successfully.")
