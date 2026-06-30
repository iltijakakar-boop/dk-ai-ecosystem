import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.studio_models import Pipeline, PipelineVersion


class PipelineService:
    def create_pipeline(
        self, db: Session, *, workspace_id: int, name: str, description: Optional[str] = None, type: str, definition: Optional[Dict[str, Any]] = None
    ) -> Pipeline:
        pipe = Pipeline(
            workspace_id=workspace_id,
            name=name,
            description=description,
            type=type,
            definition=json.dumps(definition or {}),
        )
        db.add(pipe)
        db.commit()
        db.refresh(pipe)

        # Version 1 snapshot
        ver = PipelineVersion(
            pipeline_id=pipe.id,
            version=1,
            definition=pipe.definition,
        )
        db.add(ver)
        db.commit()

        return pipe

    def get_pipelines(self, db: Session, workspace_id: int) -> List[Pipeline]:
        return db.query(Pipeline).filter(Pipeline.workspace_id == workspace_id).all()

    def get_pipeline(self, db: Session, pipeline_id: int) -> Optional[Pipeline]:
        return db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()

    def update_pipeline(self, db: Session, *, pipeline_id: int, definition: Dict[str, Any]) -> Pipeline:
        pipe = self.get_pipeline(db, pipeline_id)
        if not pipe:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found.")

        pipe.definition = json.dumps(definition)
        db.commit()

        # Save version
        latest = (
            db.query(PipelineVersion)
            .filter(PipelineVersion.pipeline_id == pipeline_id)
            .order_by(PipelineVersion.version.desc())
            .first()
        )
        next_ver = (latest.version + 1) if latest else 1

        ver = PipelineVersion(
            pipeline_id=pipeline_id,
            version=next_ver,
            definition=pipe.definition,
        )
        db.add(ver)
        db.commit()

        db.refresh(pipe)
        return pipe


pipeline_service = PipelineService()
