import math
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.dependencies.db import get_db
from app.dependencies.auth import RoleChecker
from app.models.user import User, UserRole
from app.repositories.audit_log import audit_log_repository
from app.schemas.response import APIResponse
from app.schemas.audit_log import AuditLogResponse

router = APIRouter()

admin_checker = RoleChecker([UserRole.ADMIN, UserRole.SUPER_ADMIN])

@router.get("/dashboard", response_model=APIResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(admin_checker)
):
    # Statistics queries
    total_users = db.query(User).filter(User.is_deleted == False).count()
    active_users = db.query(User).filter(User.is_active == True, User.is_deleted == False).count()
    inactive_users = total_users - active_users

    super_admins = db.query(User).filter(User.role == UserRole.SUPER_ADMIN, User.is_deleted == False).count()
    admins = db.query(User).filter(User.role == UserRole.ADMIN, User.is_deleted == False).count()
    users = db.query(User).filter(User.role == UserRole.USER, User.is_deleted == False).count()

    stats = {
        "users_stats": {
            "total": total_users,
            "active": active_users,
            "inactive": inactive_users,
        },
        "roles_distribution": {
            "super_admins": super_admins,
            "admins": admins,
            "users": users
        }
    }
    return {"success": True, "data": stats}

@router.get("/audit-logs", response_model=APIResponse)
def get_audit_logs(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_admin: User = Depends(admin_checker)
):
    total_logs = db.query(audit_log_repository.model).count()
    logs = audit_log_repository.get_multi(db, skip=skip, limit=limit)
    
    pages = math.ceil(total_logs / limit) if limit > 0 else 1
    page = (skip // limit) + 1 if limit > 0 else 1

    paginated_data = {
        "items": [AuditLogResponse.model_validate(log) for log in logs],
        "total": total_logs,
        "page": page,
        "size": limit,
        "pages": pages
    }
    return {"success": True, "data": paginated_data}
