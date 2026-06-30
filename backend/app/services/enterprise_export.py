import json
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.agent import AgentRegistry
from app.models.organization import APIKey, Project, Team, Workspace
from app.models.workflow_model import Workflow


class EnterpriseExportService:
    def export_workspace(self, db: Session, *, workspace_id: int) -> str:
        ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not ws:
            return "{}"

        # Compile workspace resources
        data: Dict[str, Any] = {
            "workspace": {
                "name": ws.name,
                "description": ws.description,
                "settings": json.loads(ws.settings or "{}"),
                "quotas": json.loads(ws.quotas or "{}"),
            },
            "projects": [],
            "teams": [],
            "agents": [],
            "workflows": [],
            "api_keys": [],
        }

        # Projects
        projects = db.query(Project).filter(Project.workspace_id == workspace_id).all()
        data["projects"] = [
            {"name": p.name, "description": p.description, "status": p.status}
            for p in projects
        ]

        # Teams
        teams = db.query(Team).filter(Team.workspace_id == workspace_id).all()
        data["teams"] = [{"name": t.name, "description": t.description} for t in teams]

        # Agents
        agents = (
            db.query(AgentRegistry)
            .filter(
                hasattr(AgentRegistry, "workspace_id")
                and AgentRegistry.workspace_id == workspace_id
            )
            .all()
        )
        data["agents"] = [
            {"name": a.name, "version": a.version, "provider": a.provider}
            for a in agents
        ]

        # Workflows
        workflows = (
            db.query(Workflow)
            .filter(
                hasattr(Workflow, "workspace_id")
                and Workflow.workspace_id == workspace_id
            )
            .all()
        )
        data["workflows"] = [
            {"name": w.name, "description": w.description, "definition": w.definition}
            for w in workflows
        ]

        # API Keys
        keys = db.query(APIKey).filter(APIKey.workspace_id == workspace_id).all()
        data["api_keys"] = [
            {"name": k.name, "permissions": k.permissions} for k in keys
        ]

        return json.dumps(data, indent=2)


enterprise_export_service = EnterpriseExportService()
