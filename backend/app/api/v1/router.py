from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    agents,
    api_keys,
    auth,
    automation,
    conversations,
    documents,
    health,
    memory,
    monitoring,
    organizations,
    projects,
    rag,
    search,
    secrets,
    service_accounts,
    teams,
    tools,
    usage,
    users,
    workflows,
    workspaces,
    studio,
    mcp,
    multimodal,
    model_management,
    observability,
    infrastructure,
    devops,
    data_platform,
    identity,
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
v1_router.include_router(organizations.router)
v1_router.include_router(workspaces.router)
v1_router.include_router(teams.router)
v1_router.include_router(projects.router)
v1_router.include_router(api_keys.router)
v1_router.include_router(service_accounts.router)
v1_router.include_router(usage.router)
v1_router.include_router(secrets.router)
v1_router.include_router(studio.router)
v1_router.include_router(mcp.router)
v1_router.include_router(multimodal.router)
v1_router.include_router(model_management.router)
v1_router.include_router(observability.router)
v1_router.include_router(infrastructure.router)
v1_router.include_router(devops.router)
v1_router.include_router(data_platform.router)
v1_router.include_router(identity.router)


