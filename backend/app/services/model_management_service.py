import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.model_management_models import (
    ModelRegistry,
    ModelVersion,
    Dataset,
    TrainingJob,
    FineTuningJob,
    GPUWorker,
)


class ModelRegistryService:
    def register_model(self, db: Session, *, workspace_id: int, name: str, description: Optional[str] = None) -> ModelRegistry:
        model = ModelRegistry(
            workspace_id=workspace_id,
            name=name,
            description=description,
            is_archived=False
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    def create_version(self, db: Session, *, model_id: int, version: str, configuration: Optional[str] = None) -> ModelVersion:
        ver = ModelVersion(
            model_id=model_id,
            version=version,
            configuration=configuration
        )
        db.add(ver)
        db.commit()
        db.refresh(ver)
        return ver

    def get_models(self, db: Session, workspace_id: int) -> List[ModelRegistry]:
        return db.query(ModelRegistry).filter(ModelRegistry.workspace_id == workspace_id).all()

    def get_model(self, db: Session, model_id: int) -> Optional[ModelRegistry]:
        return db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()


class DatasetService:
    def create_dataset(self, db: Session, *, workspace_id: int, name: str, description: Optional[str] = None) -> Dataset:
        ds = Dataset(
            workspace_id=workspace_id,
            name=name,
            description=description
        )
        db.add(ds)
        db.commit()
        db.refresh(ds)
        return ds

    def get_datasets(self, db: Session, workspace_id: int) -> List[Dataset]:
        return db.query(Dataset).filter(Dataset.workspace_id == workspace_id).all()


class TrainingService:
    def start_training(self, db: Session, *, workspace_id: int, dataset_id: int) -> TrainingJob:
        job = TrainingJob(
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            status="completed"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def get_jobs(self, db: Session, workspace_id: int) -> List[TrainingJob]:
        return db.query(TrainingJob).filter(TrainingJob.workspace_id == workspace_id).all()


class FineTuningService:
    def start_fine_tuning(self, db: Session, *, workspace_id: int, model_id: int) -> FineTuningJob:
        job = FineTuningJob(
            workspace_id=workspace_id,
            model_id=model_id,
            status="completed"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job


class GPUSchedulerService:
    def get_workers(self, db: Session) -> List[GPUWorker]:
        workers = db.query(GPUWorker).all()
        if not workers:
            # Seed GPU workers
            worker1 = GPUWorker(name="GPU-Worker-Node01-A100", load_percent=42.5)
            worker2 = GPUWorker(name="GPU-Worker-Node02-H100", load_percent=12.0)
            db.add(worker1)
            db.add(worker2)
            db.commit()
            workers = [worker1, worker2]
        return workers


model_registry_service = ModelRegistryService()
dataset_service = DatasetService()
training_service = TrainingService()
fine_tuning_service = FineTuningService()
gpu_scheduler_service = GPUSchedulerService()
