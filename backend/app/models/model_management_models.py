from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from app.db.session import Base


class ModelRegistry(Base):
    __tablename__ = "model_registries"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False)


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("model_registries.id", ondelete="CASCADE"), nullable=False)
    version = Column(String, nullable=False)
    configuration = Column(Text, nullable=True)


class ModelArtifact(Base):
    __tablename__ = "model_artifacts"
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    artifact_url = Column(String, nullable=False)


class ModelDeployment(Base):
    __tablename__ = "model_deployments"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    model_name = Column(String, nullable=False)
    environment = Column(String, nullable=False)  # Development, Testing, Staging, Production
    status = Column(String, default="active", nullable=False)


class DeploymentHistory(Base):
    __tablename__ = "model_deployment_history"
    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("model_deployments.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)


class Dataset(Base):
    __tablename__ = "model_datasets"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)


class DatasetVersion(Base):
    __tablename__ = "model_dataset_versions"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("model_datasets.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    file_url = Column(String, nullable=False)


class TrainingJob(Base):
    __tablename__ = "model_training_jobs"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    status = Column(String, default="pending", nullable=False)
    dataset_id = Column(Integer, ForeignKey("model_datasets.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class FineTuningJob(Base):
    __tablename__ = "model_fine_tuning_jobs"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    model_id = Column(Integer, ForeignKey("model_registries.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending", nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class EvaluationJob(Base):
    __tablename__ = "model_evaluation_jobs"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    model_version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending", nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class Experiment(Base):
    __tablename__ = "model_experiments"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class ExperimentRun(Base):
    __tablename__ = "model_experiment_runs"
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("model_experiments.id", ondelete="CASCADE"), nullable=False)
    metrics_json = Column(Text, nullable=True)


class Checkpoint(Base):
    __tablename__ = "model_checkpoints"
    id = Column(Integer, primary_key=True, index=True)
    tuning_job_id = Column(Integer, ForeignKey("model_fine_tuning_jobs.id", ondelete="CASCADE"), nullable=False)
    step = Column(Integer, nullable=False)
    checkpoint_url = Column(String, nullable=False)


class HyperParameter(Base):
    __tablename__ = "model_hyperparameters"
    id = Column(Integer, primary_key=True, index=True)
    tuning_job_id = Column(Integer, ForeignKey("model_fine_tuning_jobs.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    value = Column(String, nullable=False)


class Benchmark(Base):
    __tablename__ = "model_benchmarks"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class BenchmarkResult(Base):
    __tablename__ = "model_benchmark_results"
    id = Column(Integer, primary_key=True, index=True)
    benchmark_id = Column(Integer, ForeignKey("model_benchmarks.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float, nullable=False)


class PromptBenchmark(Base):
    __tablename__ = "model_prompt_benchmarks"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    prompt = Column(Text, nullable=False)


class ModelRoute(Base):
    __tablename__ = "model_routes"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    pattern = Column(String, nullable=False)
    target_model = Column(String, nullable=False)


class ModelProvider(Base):
    __tablename__ = "model_providers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)


class ModelUsage(Base):
    __tablename__ = "model_usage_records"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    tokens = Column(Integer, nullable=False)


class ModelCost(Base):
    __tablename__ = "model_cost_records"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    cost = Column(Float, nullable=False)


class GPUWorker(Base):
    __tablename__ = "model_gpu_workers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    load_percent = Column(Float, default=0.0, nullable=False)


class TrainingQueue(Base):
    __tablename__ = "model_training_queue"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("model_training_jobs.id", ondelete="CASCADE"), nullable=False)
    priority = Column(Integer, default=0, nullable=False)


class EvaluationQueue(Base):
    __tablename__ = "model_evaluation_queue"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("model_evaluation_jobs.id", ondelete="CASCADE"), nullable=False)


class DeploymentQueue(Base):
    __tablename__ = "model_deployment_queue"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("model_deployments.id", ondelete="CASCADE"), nullable=False)


class InferenceEndpoint(Base):
    __tablename__ = "model_inference_endpoints"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    url = Column(String, nullable=False)


class ModelHealth(Base):
    __tablename__ = "model_health_status"
    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("model_inference_endpoints.id", ondelete="CASCADE"), nullable=False)
    healthy = Column(Boolean, default=True, nullable=False)


class ModelMetrics(Base):
    __tablename__ = "model_metrics_logs"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    model_name = Column(String, nullable=False)
    latency_ms = Column(Float, nullable=False)


class ModelApproval(Base):
    __tablename__ = "model_approvals"
    id = Column(Integer, primary_key=True, index=True)
    model_version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False)
    approved = Column(Boolean, default=False, nullable=False)


class ModelReview(Base):
    __tablename__ = "model_reviews"
    id = Column(Integer, primary_key=True, index=True)
    approval_id = Column(Integer, ForeignKey("model_approvals.id", ondelete="CASCADE"), nullable=False)
    notes = Column(Text, nullable=True)


class ModelTag(Base):
    __tablename__ = "model_tags"
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("model_registries.id", ondelete="CASCADE"), nullable=False)
    tag = Column(String, nullable=False)
