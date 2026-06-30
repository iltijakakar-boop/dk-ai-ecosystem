from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.organization import APIKey
from app.models.user import User
from app.schemas.response import APIResponse
from app.services.api_key_service import api_key_service

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class APIKeyCreate(BaseModel):
    workspace_id: int
    name: str
    permissions: List[str] = []
    expires_in_days: Optional[int] = 30


@router.post("", response_model=APIResponse)
def create_api_key(
    payload: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    clear_key, key_obj = api_key_service.generate_key(
        db,
        workspace_id=payload.workspace_id,
        name=payload.name,
        permissions=payload.permissions,
        expires_in_days=payload.expires_in_days,
    )
    return APIResponse(
        success=True,
        message="API Key generated successfully. Save it now as it will not be displayed again.",
        data={
            "id": key_obj.id,
            "name": key_obj.name,
            "api_key": clear_key,
            "permissions": key_obj.permissions,
            "expires_at": (
                key_obj.expires_at.isoformat() if key_obj.expires_at else None
            ),
        },
    )


@router.get("", response_model=APIResponse)
def list_api_keys(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    keys = db.query(APIKey).filter(APIKey.workspace_id == workspace_id).all()
    data = [
        {
            "id": k.id,
            "name": k.name,
            "permissions": k.permissions,
            "expires_at": k.expires_at.isoformat() if k.expires_at else None,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
        }
        for k in keys
    ]
    return APIResponse(success=True, data=data)


@router.post("/{id}/rotate", response_model=APIResponse)
def rotate_api_key(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Fetch old key
    old_key = db.query(APIKey).filter(APIKey.id == id).first()
    if not old_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found."
        )

    # Save details
    workspace_id = old_key.workspace_id
    name = old_key.name
    perms = [p.strip() for p in (old_key.permissions or "").split(",") if p.strip()]

    # Delete old
    db.delete(old_key)
    db.commit()

    # Generate new
    clear_key, key_obj = api_key_service.generate_key(
        db, workspace_id=workspace_id, name=name, permissions=perms
    )
    return APIResponse(
        success=True,
        message="API Key rotated successfully.",
        data={
            "id": key_obj.id,
            "name": key_obj.name,
            "api_key": clear_key,
            "permissions": key_obj.permissions,
        },
    )


@router.delete("/{id}", response_model=APIResponse)
def delete_api_key(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    key_obj = db.query(APIKey).filter(APIKey.id == id).first()
    if not key_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found."
        )
    db.delete(key_obj)
    db.commit()
    return APIResponse(success=True, message="API Key revoked successfully.")
