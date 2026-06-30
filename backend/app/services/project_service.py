from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.organization import Project


class ProjectService:
    def create_project(
        self,
        db: Session,
        *,
        workspace_id: int,
        name: str,
        description: Optional[str] = None,
        creator_id: Optional[int] = None,
    ) -> Project:
        proj = Project(
            workspace_id=workspace_id,
            name=name,
            description=description,
            status="Active",
            created_by=creator_id,
        )
        db.add(proj)
        db.commit()
        db.refresh(proj)
        return proj

    def get_projects(self, db: Session, *, workspace_id: int) -> List[Project]:
        return db.query(Project).filter(Project.workspace_id == workspace_id).all()

    def update_project_status(
        self, db: Session, *, project_id: int, status_str: str
    ) -> Project:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found."
            )
        proj.status = status_str
        db.commit()
        db.refresh(proj)
        return proj


project_service = ProjectService()
