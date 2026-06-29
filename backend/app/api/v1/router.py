from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, users

v1_router = APIRouter()

v1_router.include_router(health.router, prefix="/health", tags=["health"])
v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
v1_router.include_router(users.router, prefix="/users", tags=["users"])
