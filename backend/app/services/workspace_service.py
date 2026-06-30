import json
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.agent import AgentRegistry
from app.models.automation import AutomationJob
from app.models.document import Document
from app.models.organization import Project, Team, TeamMember, Workspace
from app.models.workflow_model import Workflow


class WorkspaceService:
    def create_workspace(
        self,
        db: Session,
        *,
        organization_id: int,
        name: str,
        description: Optional[str] = None,
    ) -> Workspace:
        # Check defaults settings and quotas
        default_settings = {
            "timezone": "UTC",
            "language": "en",
            "theme": "dark",
            "default_model": "mock-chat-model",
            "embedding_provider": "mock",
            "vector_db_provider": "sqlite",
        }
        # Resolve organization plan
        from app.models.organization import Organization

        org = db.query(Organization).filter(Organization.id == organization_id).first()
        plan = org.plan if org else "Free"

        plan_quotas = {
            "Free": {
                "agents": 3,
                "workflows": 3,
                "automations": 3,
                "storage_mb": 50,
                "members": 3,
                "projects": 2,
            },
            "Starter": {
                "agents": 5,
                "workflows": 5,
                "automations": 5,
                "storage_mb": 100,
                "members": 5,
                "projects": 3,
            },
            "Pro": {
                "agents": 15,
                "workflows": 15,
                "automations": 15,
                "storage_mb": 500,
                "members": 15,
                "projects": 10,
            },
            "Business": {
                "agents": 50,
                "workflows": 50,
                "automations": 50,
                "storage_mb": 2000,
                "members": 50,
                "projects": 30,
            },
            "Enterprise": {
                "agents": 1000,
                "workflows": 1000,
                "automations": 1000,
                "storage_mb": 50000,
                "members": 1000,
                "projects": 1000,
            },
            "Custom": {
                "agents": 9999,
                "workflows": 9999,
                "automations": 9999,
                "storage_mb": 99999,
                "members": 9999,
                "projects": 9999,
            },
        }
        default_quotas = plan_quotas.get(plan, plan_quotas["Free"])

        ws = Workspace(
            organization_id=organization_id,
            name=name,
            description=description,
            settings=json.dumps(default_settings),
            quotas=json.dumps(default_quotas),
        )
        db.add(ws)
        db.commit()
        db.refresh(ws)
        return ws

    def update_settings(
        self, db: Session, *, workspace_id: int, settings_dict: Dict[str, Any]
    ) -> Workspace:
        ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not ws:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found."
            )

        current = json.loads(ws.settings or "{}")
        current.update(settings_dict)
        ws.settings = json.dumps(current)
        db.commit()
        db.refresh(ws)
        return ws

    def update_quotas(
        self, db: Session, *, workspace_id: int, quotas_dict: Dict[str, Any]
    ) -> Workspace:
        ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not ws:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found."
            )

        current = json.loads(ws.quotas or "{}")
        current.update(quotas_dict)
        ws.quotas = json.dumps(current)
        db.commit()
        db.refresh(ws)
        return ws

    def check_quota(
        self, db: Session, *, workspace_id: int, resource_type: str, amount: int = 1
    ) -> None:
        ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not ws:
            return

        quotas = json.loads(ws.quotas or "{}")
        limit = quotas.get(resource_type)
        if limit is None:
            return  # Unlimited

        current_count = 0
        if resource_type == "agents":
            current_count = (
                db.query(AgentRegistry)
                .filter(
                    hasattr(AgentRegistry, "workspace_id")
                    and AgentRegistry.workspace_id == workspace_id
                )
                .count()
            )
        elif resource_type == "workflows":
            current_count = (
                db.query(Workflow)
                .filter(
                    hasattr(Workflow, "workspace_id")
                    and Workflow.workspace_id == workspace_id
                )
                .count()
            )
        elif resource_type == "documents":
            current_count = (
                db.query(Document)
                .filter(
                    hasattr(Document, "workspace_id")
                    and Document.workspace_id == workspace_id
                )
                .count()
            )
        elif resource_type == "automations":
            current_count = (
                db.query(AutomationJob)
                .filter(
                    hasattr(AutomationJob, "workspace_id")
                    and AutomationJob.workspace_id == workspace_id
                )
                .count()
            )
        elif resource_type == "members":
            # Count members of teams in this workspace
            team_ids = [
                t.id
                for t in db.query(Team).filter(Team.workspace_id == workspace_id).all()
            ]
            if team_ids:
                current_count = (
                    db.query(TeamMember)
                    .filter(TeamMember.team_id.in_(team_ids))
                    .distinct(TeamMember.user_id)
                    .count()
                )
        elif resource_type == "projects":
            current_count = (
                db.query(Project).filter(Project.workspace_id == workspace_id).count()
            )

        if current_count + amount > limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Resource limit reached for {resource_type} (Limit: {limit}, Current: {current_count}).",
            )


workspace_service = WorkspaceService()
