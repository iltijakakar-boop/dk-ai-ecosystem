from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.data_platform_models import (
    DPDataset,
    DPDatasetVersion,
    DPDatasetSchema,
    DPFeatureGroup,
    DPFeature,
    DPVectorDataset,
    DPEmbeddingIndex,
    DPDataQualityReport,
)


class DatasetService:
    def create_dataset(self, db: Session, *, workspace_id: int, name: str, format: str) -> DPDataset:
        ds = DPDataset(workspace_id=workspace_id, name=name, format=format)
        db.add(ds)
        db.commit()
        db.refresh(ds)

        # Create schema placeholder
        schema = DPDatasetSchema(dataset_id=ds.id, columns_json='{"columns": ["id", "feature_a", "feature_b"]}')
        db.add(schema)
        db.commit()
        return ds

    def get_datasets(self, db: Session, workspace_id: int) -> List[DPDataset]:
        return db.query(DPDataset).filter(DPDataset.workspace_id == workspace_id).all()


class FeatureStoreService:
    def create_feature_group(self, db: Session, *, workspace_id: int, name: str) -> DPFeatureGroup:
        group = DPFeatureGroup(workspace_id=workspace_id, name=name)
        db.add(group)
        db.commit()
        db.refresh(group)

        # Seed default features
        feat = DPFeature(group_id=group.id, name="user_click_ratio", data_type="float")
        db.add(feat)
        db.commit()
        return group

    def get_feature_groups(self, db: Session, workspace_id: int) -> List[DPFeatureGroup]:
        return db.query(DPFeatureGroup).filter(DPFeatureGroup.workspace_id == workspace_id).all()


class VectorDatasetService:
    def create_vector_dataset(self, db: Session, *, workspace_id: int, name: str) -> DPVectorDataset:
        vec = DPVectorDataset(workspace_id=workspace_id, name=name)
        db.add(vec)
        db.commit()
        db.refresh(vec)

        # Create index mapping
        idx = DPEmbeddingIndex(vector_dataset_id=vec.id, dimension=1536)
        db.add(idx)
        db.commit()
        return vec

    def get_vector_datasets(self, db: Session, workspace_id: int) -> List[DPVectorDataset]:
        return db.query(DPVectorDataset).filter(DPVectorDataset.workspace_id == workspace_id).all()

    def query_similarity_search(self, db: Session, vector_dataset_id: int, query_vector: List[float]) -> List[Dict[str, Any]]:
        # Simulate similarity match records
        return [
            {"id": "doc_101", "score": 0.942, "text": "DK Ecosystem modular microservice description"},
            {"id": "doc_205", "score": 0.815, "text": "Distributed infrastructure cluster configuration"},
        ]


class DataQualityService:
    def execute_quality_checks(self, db: Session, dataset_id: int) -> DPDataQualityReport:
        report = DPDataQualityReport(dataset_id=dataset_id, score=98.5)
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    def get_quality_reports(self, db: Session, dataset_id: int) -> List[DPDataQualityReport]:
        return db.query(DPDataQualityReport).filter(DPDataQualityReport.dataset_id == dataset_id).all()


dataset_service = DatasetService()
feature_store_service = FeatureStoreService()
vector_dataset_service = VectorDatasetService()
data_quality_service = DataQualityService()
