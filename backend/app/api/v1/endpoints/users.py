from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_active_user, RoleChecker
from app.models.user import User, UserRole
from app.schemas.user import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.get("/admin-only", dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.SUPER_ADMIN]))])
def read_admin_only():
    return {"status": "success", "message": "Welcome, Administrator!"}
