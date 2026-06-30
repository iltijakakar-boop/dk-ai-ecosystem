import json
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.studio_models import AgentStudioProject, WorkflowCanvas, CanvasLayout
from app.schemas.studio import AgentStudioProjectCreate, AgentStudioProjectUpdate, WorkflowCanvasCreate, WorkflowCanvasUpdate


class StudioService:
    def create_project(self, db: Session, payload: AgentStudioProjectCreate) -> AgentStudioProject:
        proj = AgentStudioProject(
            workspace_id=payload.workspace_id,
            name=payload.name,
            description=payload.description
        )
        db.add(proj)
        db.commit()
        db.refresh(proj)
        return proj

    def get_projects(self, db: Session, workspace_id: int) -> List[AgentStudioProject]:
        return db.query(AgentStudioProject).filter(AgentStudioProject.workspace_id == workspace_id).all()

    def get_project(self, db: Session, project_id: int) -> Optional[AgentStudioProject]:
        return db.query(AgentStudioProject).filter(AgentStudioProject.id == project_id).first()

    def update_project(self, db: Session, project_id: int, payload: AgentStudioProjectUpdate) -> AgentStudioProject:
        proj = self.get_project(db, project_id)
        if not proj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        if payload.name is not None:
            proj.name = payload.name
        if payload.description is not None:
            proj.description = payload.description
        db.commit()
        db.refresh(proj)
        return proj

    def delete_project(self, db: Session, project_id: int) -> bool:
        proj = self.get_project(db, project_id)
        if not proj:
            return False
        db.delete(proj)
        db.commit()
        return True

    def create_canvas(self, db: Session, payload: WorkflowCanvasCreate) -> WorkflowCanvas:
        canvas = WorkflowCanvas(
            workspace_id=payload.workspace_id,
            project_id=payload.project_id,
            name=payload.name,
            description=payload.description,
            definition=json.dumps(payload.definition or {})
        )
        db.add(canvas)
        db.commit()
        db.refresh(canvas)

        # Initialize default layout
        layout = CanvasLayout(canvas_id=canvas.id)
        db.add(layout)
        db.commit()

        return canvas

    def get_canvases(self, db: Session, workspace_id: int) -> List[WorkflowCanvas]:
        return db.query(WorkflowCanvas).filter(
            WorkflowCanvas.workspace_id == workspace_id,
            WorkflowCanvas.is_active == True
        ).all()

    def get_canvas(self, db: Session, canvas_id: int) -> Optional[WorkflowCanvas]:
        return db.query(WorkflowCanvas).filter(
            WorkflowCanvas.id == canvas_id,
            WorkflowCanvas.is_active == True
        ).first()

    def update_canvas(self, db: Session, canvas_id: int, payload: WorkflowCanvasUpdate) -> WorkflowCanvas:
        canvas = self.get_canvas(db, canvas_id)
        if not canvas:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canvas not found.")
        if payload.name is not None:
            canvas.name = payload.name
        if payload.description is not None:
            canvas.description = payload.description
        if payload.definition is not None:
            canvas.definition = json.dumps(payload.definition)
        db.commit()
        db.refresh(canvas)
        return canvas

    def delete_canvas(self, db: Session, canvas_id: int) -> bool:
        canvas = self.get_canvas(db, canvas_id)
        if not canvas:
            return False
        canvas.is_active = False
        db.commit()
        return True


studio_service = StudioService()
