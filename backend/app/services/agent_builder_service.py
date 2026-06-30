import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.studio_models import AgentTemplate, AgentVersion
from app.models.agent import AgentRegistry
from app.services.workspace_service import workspace_service


class AgentBuilderService:
    def create_template(
        self, db: Session, *, workspace_id: int, name: str, description: Optional[str] = None, system_prompt: Optional[str] = None, model: str, temperature: float = 0.7, config_data: Optional[Dict[str, Any]] = None
    ) -> AgentTemplate:
        template = AgentTemplate(
            workspace_id=workspace_id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            config_data=json.dumps(config_data or {}),
        )
        db.add(template)
        db.commit()
        db.refresh(template)

        # Save version 1
        ver = AgentVersion(
            agent_template_id=template.id,
            version=1,
            system_prompt=system_prompt,
            config_data=template.config_data,
        )
        db.add(ver)
        db.commit()

        return template

    def get_templates(self, db: Session, workspace_id: int) -> List[AgentTemplate]:
        return db.query(AgentTemplate).filter(AgentTemplate.workspace_id == workspace_id).all()

    def get_template(self, db: Session, template_id: int) -> Optional[AgentTemplate]:
        return db.query(AgentTemplate).filter(AgentTemplate.id == template_id).first()

    def update_template(
        self, db: Session, template_id: int, system_prompt: Optional[str] = None, config_data: Optional[Dict[str, Any]] = None
    ) -> AgentTemplate:
        template = self.get_template(db, template_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent template not found.")

        if system_prompt is not None:
            template.system_prompt = system_prompt
        if config_data is not None:
            template.config_data = json.dumps(config_data)

        db.commit()

        # Create new version snapshot
        latest_version = (
            db.query(AgentVersion)
            .filter(AgentVersion.agent_template_id == template_id)
            .order_by(AgentVersion.version.desc())
            .first()
        )
        next_ver = (latest_version.version + 1) if latest_version else 1

        ver = AgentVersion(
            agent_template_id=template_id,
            version=next_ver,
            system_prompt=template.system_prompt,
            config_data=template.config_data,
        )
        db.add(ver)
        db.commit()

        db.refresh(template)
        return template

    def compile_and_register_agent(self, db: Session, *, template_id: int) -> AgentRegistry:
        template = self.get_template(db, template_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent template not found.")

        # Check quota limits
        workspace_service.check_quota(db, workspace_id=template.workspace_id, resource_type="agents")

        # Compile and save to active AgentRegistry
        latest_ver = (
            db.query(AgentVersion)
            .filter(AgentVersion.agent_template_id == template_id)
            .order_by(AgentVersion.version.desc())
            .first()
        )
        ver_str = f"1.{latest_ver.version}" if latest_ver else "1.0"

        agent = AgentRegistry(
            id=f"studio_ws_{template.workspace_id}_agent_{template.id}",
            name=template.name,
            version=ver_str,
            status="active",
            provider="mock-llm-studio",
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent


agent_builder_service = AgentBuilderService()
