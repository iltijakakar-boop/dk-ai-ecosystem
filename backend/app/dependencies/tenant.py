from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.middleware.tenant_resolver import TenantContext
from app.models.organization import Team, TeamMember, Workspace
from app.services.api_key_service import api_key_service
from app.services.service_account_service import service_account_service

security = HTTPBearer(auto_error=False)


async def get_tenant_context_dependency(
    request: Request,
    db: Session = Depends(get_db),
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_workspace_id: Optional[int] = Header(None, alias="X-Workspace-Id"),
):
    token = None
    if auth:
        token = auth.credentials

    # Support header overrides if Authorization is not present
    if not token:
        token = request.headers.get("x-api-key") or request.headers.get(
            "x-service-account-token"
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials missing.",
        )

    resolved_org_id = None
    resolved_workspace_id = None
    resolved_user = None
    resolved_api_key = None
    resolved_sa = None
    resolved_role = None

    if token.startswith("dk_api_"):
        # API Key authentication
        key_obj = api_key_service.verify_key(db, clear_key=token)
        resolved_workspace_id = key_obj.workspace_id
        resolved_api_key = key_obj
        resolved_role = "SERVICE_ACCOUNT"
        ws = db.query(Workspace).filter(Workspace.id == resolved_workspace_id).first()
        if ws:
            resolved_org_id = ws.organization_id
    elif token.startswith("dk_sa_"):
        # Service Account authentication
        sa_obj = service_account_service.verify_token(db, clear_token=token)
        resolved_workspace_id = sa_obj.workspace_id
        resolved_sa = sa_obj
        resolved_role = "SERVICE_ACCOUNT"
        ws = db.query(Workspace).filter(Workspace.id == resolved_workspace_id).first()
        if ws:
            resolved_org_id = ws.organization_id
    else:
        # Standard JWT User authentication
        try:
            user = await get_current_user(db=db, token=token)
            resolved_user = user
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials or token.",
            )

        # Resolve active workspace
        if x_workspace_id:
            # Check user access
            membership = (
                db.query(TeamMember)
                .join(Team, Team.id == TeamMember.team_id)
                .filter(
                    Team.workspace_id == x_workspace_id,
                    TeamMember.user_id == user.id,
                )
                .first()
            )
            # Support super admins accessing any workspace
            is_admin = user.role in ["admin", "super_admin"]
            if not membership and not is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have access to this workspace.",
                )
            resolved_workspace_id = x_workspace_id
            resolved_role = membership.role if membership else user.role
            ws = (
                db.query(Workspace)
                .filter(Workspace.id == resolved_workspace_id)
                .first()
            )
            if ws:
                resolved_org_id = ws.organization_id
        else:
            # Get first workspace membership fallback
            membership = (
                db.query(TeamMember)
                .join(Team, Team.id == TeamMember.team_id)
                .filter(TeamMember.user_id == user.id)
                .first()
            )
            if membership:
                team = db.query(Team).filter(Team.id == membership.team_id).first()
                if team:
                    resolved_workspace_id = team.workspace_id
                    resolved_role = membership.role
                    ws = (
                        db.query(Workspace)
                        .filter(Workspace.id == resolved_workspace_id)
                        .first()
                    )
                    if ws:
                        resolved_org_id = ws.organization_id
            else:
                # If no membership, fallback to first workspace for admins
                if user.role in ["admin", "super_admin"]:
                    ws = db.query(Workspace).first()
                    if ws:
                        resolved_workspace_id = ws.id
                        resolved_org_id = ws.organization_id
                        resolved_role = "SUPER_ADMIN"

        if not resolved_workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not associated with any active workspace.",
            )

    # Instantiate context manager to set thread-local boundaries
    context = TenantContext(org_id=resolved_org_id, workspace_id=resolved_workspace_id)
    context.__enter__()

    request.state.tenant_context = {
        "org_id": resolved_org_id,
        "workspace_id": resolved_workspace_id,
        "user": resolved_user,
        "api_key": resolved_api_key,
        "service_account": resolved_sa,
        "role": resolved_role,
        "context_manager": context,
    }

    return request.state.tenant_context


class ScopeChecker:
    """
    FastAPI dependency checker verifying scope authorization permissions.
    """

    def __init__(self, required_scope: str):
        self.required_scope = required_scope

    def __call__(
        self, tenant_ctx: dict = Depends(get_tenant_context_dependency)
    ) -> dict:
        api_key = tenant_ctx.get("api_key")
        sa = tenant_ctx.get("service_account")
        user = tenant_ctx.get("user")
        role = tenant_ctx.get("role")

        # 1. Assert scopes for API Keys
        if api_key:
            api_key_service.check_scope(api_key, self.required_scope)
        # 2. Assert scopes for Service Accounts
        elif sa:
            service_account_service.check_scope(sa, self.required_scope)
        # 3. Assert roles for User
        elif user:
            # Map scopes to minimum allowed roles
            all_roles = [
                "VIEWER",
                "MEMBER",
                "DEVELOPER",
                "TEAM_MANAGER",
                "WORKSPACE_ADMIN",
                "ORGANIZATION_ADMIN",
                "ORGANIZATION_OWNER",
                "SUPER_ADMIN",
                "admin",
                "super_admin",
            ]
            member_up = [
                "MEMBER",
                "DEVELOPER",
                "TEAM_MANAGER",
                "WORKSPACE_ADMIN",
                "ORGANIZATION_ADMIN",
                "ORGANIZATION_OWNER",
                "SUPER_ADMIN",
                "admin",
                "super_admin",
            ]
            dev_up = [
                "DEVELOPER",
                "TEAM_MANAGER",
                "WORKSPACE_ADMIN",
                "ORGANIZATION_ADMIN",
                "ORGANIZATION_OWNER",
                "SUPER_ADMIN",
                "admin",
                "super_admin",
            ]
            admin_up = [
                "WORKSPACE_ADMIN",
                "ORGANIZATION_ADMIN",
                "ORGANIZATION_OWNER",
                "SUPER_ADMIN",
                "admin",
                "super_admin",
            ]
            org_admin_up = [
                "ORGANIZATION_ADMIN",
                "ORGANIZATION_OWNER",
                "SUPER_ADMIN",
                "admin",
                "super_admin",
            ]

            role_requirements = {
                "agent.read": all_roles,
                "agent.write": member_up,
                "workflow.read": all_roles,
                "workflow.write": dev_up,
                "rag.read": all_roles,
                "rag.write": dev_up,
                "vector.read": all_roles,
                "vector.write": dev_up,
                "storage.read": all_roles,
                "storage.write": member_up,
                "secret.read": dev_up,
                "secret.write": admin_up,
                "billing.read": org_admin_up,
                "billing.write": [
                    "ORGANIZATION_OWNER",
                    "SUPER_ADMIN",
                    "admin",
                    "super_admin",
                ],
                "admin.full": ["SUPER_ADMIN", "super_admin"],
            }
            req_roles = role_requirements.get(
                self.required_scope, ["SUPER_ADMIN", "super_admin"]
            )
            # Normalize role string
            norm_role = str(role).upper()
            if norm_role not in [r.upper() for r in req_roles]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User role {role} not authorized for required scope: {self.required_scope}",
                )

        return tenant_ctx
