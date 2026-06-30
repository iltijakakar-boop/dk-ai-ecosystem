from sqlalchemy.orm import Session
from app.models.studio_models import WorkflowCanvas, PromptVersion, AgentVersion, PipelineVersion


class VersioningService:
    def create_canvas_snapshot(self, db: Session, *, canvas_id: int) -> int:
        canvas = db.query(WorkflowCanvas).filter(WorkflowCanvas.id == canvas_id).first()
        if not canvas:
            return 1
        canvas.version += 1
        db.commit()
        return canvas.version

    def get_prompt_version_history(self, db: Session, *, prompt_id: int) -> list:
        return db.query(PromptVersion).filter(PromptVersion.prompt_id == prompt_id).order_by(PromptVersion.version.desc()).all()

    def get_agent_version_history(self, db: Session, *, agent_template_id: int) -> list:
        return db.query(AgentVersion).filter(AgentVersion.agent_template_id == agent_template_id).order_by(AgentVersion.version.desc()).all()


versioning_service = VersioningService()
