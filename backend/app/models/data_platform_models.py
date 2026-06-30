from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from app.db.session import Base


class DPDataset(Base):
    __tablename__ = "dp_datasets"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    format = Column(String, nullable=False)  # parquet, csv, json


class DPDatasetVersion(Base):
    __tablename__ = "dp_dataset_versions"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("dp_datasets.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class DPDatasetSchema(Base):
    __tablename__ = "dp_dataset_schemas"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("dp_datasets.id", ondelete="CASCADE"), nullable=False)
    columns_json = Column(Text, nullable=False)


class DPDatasetPartition(Base):
    __tablename__ = "dp_dataset_partitions"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("dp_datasets.id", ondelete="CASCADE"), nullable=False)
    partition_key = Column(String, nullable=False)


class DPDatasetSnapshot(Base):
    __tablename__ = "dp_dataset_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("dp_datasets.id", ondelete="CASCADE"), nullable=False)
    snapshot_time = Column(DateTime, default=func.now(), nullable=False)


class DPFeatureGroup(Base):
    __tablename__ = "dp_feature_groups"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class DPFeature(Base):
    __tablename__ = "dp_features"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("dp_feature_groups.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    data_type = Column(String, nullable=False)


class DPFeatureVersion(Base):
    __tablename__ = "dp_feature_versions"
    id = Column(Integer, primary_key=True, index=True)
    feature_id = Column(Integer, ForeignKey("dp_features.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, default=1, nullable=False)


class DPFeatureView(Base):
    __tablename__ = "dp_feature_views"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class DPFeatureServingEndpoint(Base):
    __tablename__ = "dp_feature_serving_endpoints"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    url = Column(String, nullable=False)


class DPLakehouse(Base):
    __tablename__ = "dp_lakehouses"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    storage_path = Column(String, nullable=False)


class DPDataCatalog(Base):
    __tablename__ = "dp_data_catalogs"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    catalog_name = Column(String, nullable=False)


class DPMetadataEntry(Base):
    __tablename__ = "dp_metadata_entries"
    id = Column(Integer, primary_key=True, index=True)
    catalog_id = Column(Integer, ForeignKey("dp_data_catalogs.id", ondelete="CASCADE"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)


class DPDataLineage(Base):
    __tablename__ = "dp_data_lineage"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    source_table = Column(String, nullable=False)
    target_table = Column(String, nullable=False)


class DPDataSource(Base):
    __tablename__ = "dp_data_sources"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    source_type = Column(String, nullable=False)  # s3, postgres


class DPDataSink(Base):
    __tablename__ = "dp_data_sinks"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    sink_type = Column(String, nullable=False)


class DPETLPipeline(Base):
    __tablename__ = "dp_etl_pipelines"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class DPETLExecution(Base):
    __tablename__ = "dp_etl_executions"
    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("dp_etl_pipelines.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="completed", nullable=False)


class DPStreamingPipeline(Base):
    __tablename__ = "dp_streaming_pipelines"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class DPStreamingTopic(Base):
    __tablename__ = "dp_streaming_topics"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    topic_name = Column(String, nullable=False)


class DPStreamingConsumer(Base):
    __tablename__ = "dp_streaming_consumers"
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("dp_streaming_topics.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)


class DPDataQualityRule(Base):
    __tablename__ = "dp_data_quality_rules"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("dp_datasets.id", ondelete="CASCADE"), nullable=False)
    column_name = Column(String, nullable=False)
    rule_type = Column(String, nullable=False)  # not_null, range


class DPDataQualityReport(Base):
    __tablename__ = "dp_data_quality_reports"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("dp_datasets.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float, nullable=False)


class DPDataValidation(Base):
    __tablename__ = "dp_data_validations"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("dp_datasets.id", ondelete="CASCADE"), nullable=False)
    passed = Column(Boolean, default=True, nullable=False)


class DPVectorDataset(Base):
    __tablename__ = "dp_vector_datasets"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class DPEmbeddingIndex(Base):
    __tablename__ = "dp_embedding_indexes"
    id = Column(Integer, primary_key=True, index=True)
    vector_dataset_id = Column(Integer, ForeignKey("dp_vector_datasets.id", ondelete="CASCADE"), nullable=False)
    dimension = Column(Integer, nullable=False)


class DPMetadataTag(Base):
    __tablename__ = "dp_metadata_tags"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("dp_datasets.id", ondelete="CASCADE"), nullable=False)
    tag_name = Column(String, nullable=False)


class DPDataRetentionPolicy(Base):
    __tablename__ = "dp_retention_policies"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    retention_days = Column(Integer, nullable=False)


class DPDataAccessPolicy(Base):
    __tablename__ = "dp_data_access_policies"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    role_required = Column(String, nullable=False)
