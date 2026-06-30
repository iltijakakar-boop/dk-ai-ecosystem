from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.organization import Secret
from app.models.user import User
from app.schemas.response import APIResponse
from app.services.secrets_service import secrets_service

router = APIRouter(prefix="/secrets", tags=["secrets"])


class SecretCreate(BaseModel):
    workspace_id: int
    name: str
    value: str
    category: Optional[str] = None


class SecretUpdate(BaseModel):
    value: str


@router.post("", response_model=APIResponse)
def create_secret(
    payload: SecretCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sec = secrets_service.create_secret(
        db,
        workspace_id=payload.workspace_id,
        name=payload.name,
        value=payload.value,
        category=payload.category,
    )
    return APIResponse(
        success=True,
        message="Secret created and encrypted successfully.",
        data={
            "id": sec.id,
            "workspace_id": sec.workspace_id,
            "name": sec.name,
            "version": sec.version,
            "category": sec.category,
        },
    )


@router.get("/{id}/decrypt", response_model=APIResponse)
def decrypt_secret(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sec = db.query(Secret).filter(Secret.id == id).first()
    if not sec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Secret not found."
        )

    decrypted = secrets_service.decrypt_value(sec.encrypted_value)
    return APIResponse(
        success=True,
        data={
            "id": sec.id,
            "name": sec.name,
            "value": decrypted,
            "version": sec.version,
        },
    )


@router.put("/{id}", response_model=APIResponse)
def update_secret(
    id: int,
    payload: SecretUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sec = secrets_service.update_secret(db, secret_id=id, value=payload.value)
    return APIResponse(
        success=True,
        message="Secret value updated and encrypted successfully.",
        data={"id": sec.id, "version": sec.version},
    )


@router.post("/{id}/rollback", response_model=APIResponse)
def rollback_secret(
    id: int,
    version: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sec = secrets_service.rollback_secret(db, secret_id=id, target_version=version)
    return APIResponse(
        success=True,
        message=f"Secret rolled back to version {version} successfully.",
        data={"id": sec.id, "version": sec.version},
    )


@router.delete("/{id}", response_model=APIResponse)
def delete_secret(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    sec = db.query(Secret).filter(Secret.id == id).first()
    if not sec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Secret not found."
        )
    db.delete(sec)
    db.commit()
    return APIResponse(success=True, message="Secret deleted successfully.")
