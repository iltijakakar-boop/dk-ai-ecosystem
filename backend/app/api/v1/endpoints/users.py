import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.dependencies.auth import RoleChecker, get_current_active_user
from app.dependencies.db import get_db
from app.models.user import User, UserRole
from app.repositories.user import user_repository
from app.schemas.response import APIResponse
from app.schemas.user import (
    UserChangePassword,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
    UserUpdateRole,
)
from app.services.user_service import user_service

router = APIRouter()

admin_checker = RoleChecker([UserRole.ADMIN, UserRole.SUPER_ADMIN])


@router.get("", response_model=APIResponse)
def read_users(
    skip: int = 0,
    limit: int = 10,
    q: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(admin_checker),
):
    items, total = user_repository.search_and_filter(
        db, query=q, role=role, is_active=is_active, skip=skip, limit=limit
    )
    pages = math.ceil(total / limit) if limit > 0 else 1
    page = (skip // limit) + 1 if limit > 0 else 1

    paginated_data = {
        "items": [UserResponse.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "size": limit,
        "pages": pages,
    }
    return {"success": True, "data": paginated_data}


@router.get("/me", response_model=APIResponse)
def read_user_me(current_user: User = Depends(get_current_active_user)):
    user_data = UserResponse.model_validate(current_user)
    return {"success": True, "data": user_data}


@router.get("/admin-only", response_model=APIResponse)
def read_admin_only(current_admin: User = Depends(admin_checker)):
    return {"success": True, "message": "Welcome, Administrator!"}


@router.get("/{id}", response_model=APIResponse)
def read_user_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if (
        current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
        and current_user.id != id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this profile.",
        )

    user = user_repository.get(db, id=id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    return {"success": True, "data": UserResponse.model_validate(user)}


@router.put("/me", response_model=APIResponse)
def update_profile(
    request: Request,
    obj_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    updated_user = user_service.update_user_profile(
        db, user_id=current_user.id, email=obj_in.email, ip=ip, ua=ua
    )
    return {
        "success": True,
        "data": UserResponse.model_validate(updated_user),
        "message": "Profile updated successfully.",
    }


@router.post("/me/change-password", response_model=APIResponse)
def change_password(
    request: Request,
    pass_in: UserChangePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    user_service.change_user_password(
        db,
        user_id=current_user.id,
        old_password=pass_in.old_password,
        new_password=pass_in.new_password,
        ip=ip,
        ua=ua,
    )
    return {"success": True, "message": "Password changed successfully."}


@router.patch("/{id}/role", response_model=APIResponse)
def change_user_role(
    id: int,
    role_in: UserUpdateRole,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(admin_checker),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    updated_user = user_service.update_user_role(
        db, actor=current_admin, target_id=id, new_role=role_in.role, ip=ip, ua=ua
    )
    return {
        "success": True,
        "data": UserResponse.model_validate(updated_user),
        "message": "User role updated successfully.",
    }


@router.patch("/{id}/status", response_model=APIResponse)
def change_user_status(
    id: int,
    status_in: UserStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(admin_checker),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    updated_user = user_service.update_user_status(
        db,
        actor=current_admin,
        target_id=id,
        is_active=status_in.is_active,
        ip=ip,
        ua=ua,
    )
    return {
        "success": True,
        "data": UserResponse.model_validate(updated_user),
        "message": "User status updated successfully.",
    }


@router.delete("/{id}", response_model=APIResponse)
def delete_user(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(admin_checker),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    user_service.delete_user(db, actor=current_admin, target_id=id, ip=ip, ua=ua)
    return {"success": True, "message": "User deleted successfully."}
