from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    agents,
    auth,
    automation,
    conversations,
    documents,
    health,
    memory,
    monitoring,
    rag,
    search,
    tools,
    users,
    workflows,
)

v1_router = APIRouter()

v1_router.include_router(health.router, prefix="/health", tags=["health"])
v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
v1_router.include_router(users.router, prefix="/users", tags=["users"])
v1_router.include_router(admin.router, prefix="/admin", tags=["admin"])
v1_router.include_router(agents.router, prefix="/agents", tags=["agents"])
v1_router.include_router(tools.router)
v1_router.include_router(monitoring.router)
v1_router.include_router(documents.router)
v1_router.include_router(search.router)
v1_router.include_router(memory.router)
v1_router.include_router(conversations.router)
v1_router.include_router(rag.router)
v1_router.include_router(workflows.router)
v1_router.include_router(automation.router)
