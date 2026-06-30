from typing import Any, Dict, List

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.agent import AgentRegistry
from app.models.document import Document
from app.models.organization import APIKey, Project, Secret, Team
from app.models.workflow_model import Workflow


class EnterpriseSearchService:
    def global_search(
        self, db: Session, *, workspace_id: int, query: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        results: Dict[str, List[Dict[str, Any]]] = {
            "projects": [],
            "teams": [],
            "agents": [],
            "workflows": [],
            "documents": [],
            "secrets": [],
            "api_keys": [],
        }
        if not query:
            return results

        pattern = f"%{query}%"

        # Search Projects
        projects = (
            db.query(Project)
            .filter(
                Project.workspace_id == workspace_id,
                or_(Project.name.like(pattern), Project.description.like(pattern)),
            )
            .all()
        )
        results["projects"] = [
            {"id": p.id, "name": p.name, "description": p.description} for p in projects
        ]

        # Search Teams
        teams = (
            db.query(Team)
            .filter(
                Team.workspace_id == workspace_id,
                or_(Team.name.like(pattern), Team.description.like(pattern)),
            )
            .all()
        )
        results["teams"] = [
            {"id": t.id, "name": t.name, "description": t.description} for t in teams
        ]

        # Search Agents
        agents = (
            db.query(AgentRegistry)
            .filter(
                hasattr(AgentRegistry, "workspace_id")
                and AgentRegistry.workspace_id == workspace_id,
                AgentRegistry.name.like(pattern),
            )
            .all()
        )
        results["agents"] = [
            {"id": a.id, "name": a.name, "provider": a.provider} for a in agents
        ]

        # Search Workflows
        workflows = (
            db.query(Workflow)
            .filter(
                hasattr(Workflow, "workspace_id")
                and Workflow.workspace_id == workspace_id,
                or_(Workflow.name.like(pattern), Workflow.description.like(pattern)),
            )
            .all()
        )
        results["workflows"] = [
            {"id": w.id, "name": w.name, "description": w.description}
            for w in workflows
        ]

        # Search Documents
        documents = (
            db.query(Document)
            .filter(
                hasattr(Document, "workspace_id")
                and Document.workspace_id == workspace_id,
                or_(
                    Document.original_filename.like(pattern),
                    Document.mime_type.like(pattern),
                ),
            )
            .all()
        )
        results["documents"] = [
            {"id": d.id, "filename": d.original_filename, "size": d.file_size}
            for d in documents
        ]

        # Search Secrets
        secrets = (
            db.query(Secret)
            .filter(
                Secret.workspace_id == workspace_id,
                or_(Secret.name.like(pattern), Secret.category.like(pattern)),
            )
            .all()
        )
        results["secrets"] = [
            {"id": s.id, "name": s.name, "category": s.category} for s in secrets
        ]

        # Search API Keys
        keys = (
            db.query(APIKey)
            .filter(APIKey.workspace_id == workspace_id, APIKey.name.like(pattern))
            .all()
        )
        results["api_keys"] = [
            {"id": k.id, "name": k.name, "created_at": k.created_at.isoformat()}
            for k in keys
        ]

        return results


enterprise_search_service = EnterpriseSearchService()
