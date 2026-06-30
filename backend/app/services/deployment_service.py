from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.studio_models import Deployment, DeploymentHistory


class DeploymentService:
    def create_deployment(
        self,
        db: Session,
        *,
        workspace_id: int,
        canvas_id: Optional[int] = None,
        agent_template_id: Optional[int] = None,
        pipeline_id: Optional[int] = None,
        version: int,
        environment: str = "Testing",
        user_id: Optional[int] = None,
    ) -> Deployment:
        # Create deployment record
        dep = Deployment(
            workspace_id=workspace_id,
            canvas_id=canvas_id,
            agent_template_id=agent_template_id,
            pipeline_id=pipeline_id,
            version=version,
            environment=environment,
            status="Active",
        )
        db.add(dep)
        db.commit()
        db.refresh(dep)

        # Audit History Log
        history = DeploymentHistory(
            deployment_id=dep.id,
            action="deploy",
            details=f"Deployed version {version} to environment: {environment}",
            performed_by=user_id,
        )
        db.add(history)
        db.commit()

        return dep

    def get_deployments(self, db: Session, workspace_id: int) -> List[Deployment]:
        return db.query(Deployment).filter(Deployment.workspace_id == workspace_id).all()

    def get_deployment(self, db: Session, deployment_id: int) -> Optional[Deployment]:
        return db.query(Deployment).filter(Deployment.id == deployment_id).first()

    def rollback_deployment(self, db: Session, *, deployment_id: int, user_id: Optional[int] = None) -> Deployment:
        dep = self.get_deployment(db, deployment_id)
        if not dep:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found.")

        # Find previous active version or rollback by setting status
        dep.status = "RolledBack"
        db.commit()

        # Audit rollback action
        history = DeploymentHistory(
            deployment_id=dep.id,
            action="rollback",
            details=f"Rolled back deployment to inactive status",
            performed_by=user_id,
        )
        db.add(history)
        db.commit()

        db.refresh(dep)
        return dep


deployment_service = DeploymentService()
