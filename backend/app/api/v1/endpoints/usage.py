from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.dependencies.tenant import get_tenant_context_dependency
from app.schemas.response import APIResponse
from app.services.enterprise_export import enterprise_export_service
from app.services.enterprise_search import enterprise_search_service
from app.services.usage_service import usage_service

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/statistics", response_model=APIResponse)
def get_usage_statistics(
    workspace_id: int,
    db: Session = Depends(get_db),
    tenant_ctx: dict = Depends(get_tenant_context_dependency),
):
    stats = usage_service.aggregate_workspace_usage(db, workspace_id=workspace_id)
    return APIResponse(success=True, data=stats)


@router.get("/search", response_model=APIResponse)
def global_search(
    workspace_id: int,
    query: str,
    db: Session = Depends(get_db),
    tenant_ctx: dict = Depends(get_tenant_context_dependency),
):
    results = enterprise_search_service.global_search(
        db, workspace_id=workspace_id, query=query
    )
    return APIResponse(success=True, data=results)


@router.get("/export", response_model=APIResponse)
def export_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    tenant_ctx: dict = Depends(get_tenant_context_dependency),
):
    export_data = enterprise_export_service.export_workspace(
        db, workspace_id=workspace_id
    )
    return APIResponse(
        success=True,
        message="Workspace configuration exported successfully.",
        data={"export_json": export_data},
    )
