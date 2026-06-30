from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.devops_models import (
    DevOpsPipeline,
    DevOpsPipelineRun,
    DevOpsPipelineStage,
    DevOpsRelease,
    DevOpsDeployment,
    DevOpsApprovalRequest,
    DevOpsRollback,
    DevOpsContainerImage,
)


class PipelineService:
    def create_pipeline(self, db: Session, *, workspace_id: int, name: str) -> DevOpsPipeline:
        pipe = DevOpsPipeline(workspace_id=workspace_id, name=name)
        db.add(pipe)
        db.commit()
        db.refresh(pipe)
        return pipe

    def get_pipelines(self, db: Session, workspace_id: int) -> List[DevOpsPipeline]:
        return db.query(DevOpsPipeline).filter(DevOpsPipeline.workspace_id == workspace_id).all()

    def run_pipeline(self, db: Session, pipeline_id: int) -> DevOpsPipelineRun:
        run = DevOpsPipelineRun(pipeline_id=pipeline_id, status="running")
        db.add(run)
        db.commit()
        db.refresh(run)

        # Seed stages
        for stage_name in ["Build", "Test", "Security Scan", "Deploy Gate"]:
            stage = DevOpsPipelineStage(run_id=run.id, name=stage_name, status="completed")
            db.add(stage)
        db.commit()
        
        # Complete run
        run.status = "completed"
        db.add(run)
        db.commit()
        db.refresh(run)
        return run


class ReleaseService:
    def create_release(self, db: Session, *, workspace_id: int, version: str) -> DevOpsRelease:
        rel = DevOpsRelease(workspace_id=workspace_id, version=version, status="active")
        db.add(rel)
        db.commit()
        db.refresh(rel)
        return rel

    def trigger_rollback(self, db: Session, *, workspace_id: int, current_rel_id: int, target_rel_id: int) -> DevOpsRollback:
        # Create deployment record
        dep = DevOpsDeployment(workspace_id=workspace_id, release_id=target_rel_id, environment="production", status="completed")
        db.add(dep)
        db.commit()

        # Update historical release status
        old_rel = db.query(DevOpsRelease).filter(DevOpsRelease.id == current_rel_id).first()
        if old_rel:
            old_rel.status = "rolled_back"
            db.add(old_rel)

        rollback = DevOpsRollback(workspace_id=workspace_id, deployment_id=dep.id, target_release_id=target_rel_id)
        db.add(rollback)
        db.commit()
        db.refresh(rollback)
        return rollback


class ApprovalService:
    def request_approval(self, db: Session, *, workspace_id: int, release_id: int) -> DevOpsApprovalRequest:
        dep = DevOpsDeployment(workspace_id=workspace_id, release_id=release_id, environment="production", status="pending")
        db.add(dep)
        db.commit()

        req = DevOpsApprovalRequest(workspace_id=workspace_id, deployment_id=dep.id, status="pending")
        db.add(req)
        db.commit()
        db.refresh(req)
        return req

    def get_pending_approvals(self, db: Session, workspace_id: int) -> List[DevOpsApprovalRequest]:
        return db.query(DevOpsApprovalRequest).filter(
            DevOpsApprovalRequest.workspace_id == workspace_id,
            DevOpsApprovalRequest.status == "pending"
        ).all()

    def process_approval(self, db: Session, request_id: int, approve: bool) -> DevOpsApprovalRequest:
        req = db.query(DevOpsApprovalRequest).filter(DevOpsApprovalRequest.id == request_id).first()
        if not req:
            return None
        
        req.status = "approved" if approve else "rejected"
        db.add(req)

        # Update deployment status
        dep = db.query(DevOpsDeployment).filter(DevOpsDeployment.id == req.deployment_id).first()
        if dep:
            dep.status = "completed" if approve else "failed"
            db.add(dep)

        db.commit()
        db.refresh(req)
        return req


class ContainerRegistryService:
    def register_image(self, db: Session, *, workspace_id: int, name: str, tag: str, digest: str) -> DevOpsContainerImage:
        img = DevOpsContainerImage(
            workspace_id=workspace_id,
            name=name,
            tag=tag,
            digest=digest
        )
        db.add(img)
        db.commit()
        db.refresh(img)
        return img

    def get_images(self, db: Session, workspace_id: int) -> List[DevOpsContainerImage]:
        return db.query(DevOpsContainerImage).filter(DevOpsContainerImage.workspace_id == workspace_id).all()


pipeline_service = PipelineService()
release_service = ReleaseService()
approval_service = ApprovalService()
container_registry_service = ContainerRegistryService()
