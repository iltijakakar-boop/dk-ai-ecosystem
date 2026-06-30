from typing import List
from sqlalchemy.orm import Session
from app.models.mcp_models import ToolPermission


class ToolPermissionService:
    def grant_permission(self, db: Session, *, workspace_id: int, tool_name: str, allowed_scopes: List[str]) -> ToolPermission:
        perm = (
            db.query(ToolPermission)
            .filter(
                ToolPermission.workspace_id == workspace_id,
                ToolPermission.tool_name == tool_name,
            )
            .first()
        )
        scopes_str = ",".join(allowed_scopes)
        if perm:
            perm.allowed_scopes = scopes_str
        else:
            perm = ToolPermission(
                workspace_id=workspace_id,
                tool_name=tool_name,
                allowed_scopes=scopes_str
            )
            db.add(perm)
        db.commit()
        db.refresh(perm)
        return perm

    def verify_tool_permission(self, db: Session, *, workspace_id: int, tool_name: str, required_scope: str) -> bool:
        perm = (
            db.query(ToolPermission)
            .filter(
                ToolPermission.workspace_id == workspace_id,
                ToolPermission.tool_name == tool_name,
            )
            .first()
        )
        if not perm:
            return False
        
        allowed = [s.strip() for s in perm.allowed_scopes.split(",") if s.strip()]
        return required_scope in allowed


tool_permission_service = ToolPermissionService()
