from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from app.db.session import Base


class InfraCluster(Base):
    __tablename__ = "infra_clusters"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    api_endpoint = Column(String, nullable=False)
    status = Column(String, default="healthy", nullable=False)


class InfraNode(Base):
    __tablename__ = "infra_nodes"
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("infra_clusters.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # master, worker
    status = Column(String, default="ready", nullable=False)


class InfraDeployment(Base):
    __tablename__ = "infra_deployments"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    cluster_id = Column(Integer, ForeignKey("infra_clusters.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    replicas = Column(Integer, default=1, nullable=False)


class InfraPod(Base):
    __tablename__ = "infra_pods"
    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("infra_deployments.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="running", nullable=False)
    cpu_cores = Column(Float, default=0.5, nullable=False)


class InfraNamespace(Base):
    __tablename__ = "infra_namespaces"
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("infra_clusters.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)


class InfraServiceMesh(Base):
    __tablename__ = "infra_service_mesh"
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("infra_clusters.id", ondelete="CASCADE"), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)


class InfraIngress(Base):
    __tablename__ = "infra_ingress"
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("infra_clusters.id", ondelete="CASCADE"), nullable=False)
    host = Column(String, nullable=False)


class InfraGateway(Base):
    __tablename__ = "infra_gateways"
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("infra_clusters.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)


class InfraLoadBalancer(Base):
    __tablename__ = "infra_load_balancers"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    ip_address = Column(String, nullable=False)


class InfraAutoScaler(Base):
    __tablename__ = "infra_autoscalers"
    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("infra_deployments.id", ondelete="CASCADE"), nullable=False)
    min_replicas = Column(Integer, default=1, nullable=False)
    max_replicas = Column(Integer, default=10, nullable=False)


class InfraPersistentVolume(Base):
    __tablename__ = "infra_persistent_volumes"
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("infra_clusters.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    capacity_gb = Column(Integer, nullable=False)


class InfraStorageClass(Base):
    __tablename__ = "infra_storage_classes"
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("infra_clusters.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)


class InfraSecretManager(Base):
    __tablename__ = "infra_secret_managers"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    provider = Column(String, nullable=False)  # vault, aws, gcp


class InfraConfigManager(Base):
    __tablename__ = "infra_config_managers"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    key = Column(String, nullable=False)


class InfraClusterPolicy(Base):
    __tablename__ = "infra_cluster_policies"
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("infra_clusters.id", ondelete="CASCADE"), nullable=False)
    policy_name = Column(String, nullable=False)


class InfraEdgeNode(Base):
    __tablename__ = "infra_edge_nodes"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="online", nullable=False)  # online, offline
    sync_status = Column(String, default="synced", nullable=False)  # synced, syncing


class InfraEdgeDeployment(Base):
    __tablename__ = "infra_edge_deployments"
    id = Column(Integer, primary_key=True, index=True)
    edge_node_id = Column(Integer, ForeignKey("infra_edge_nodes.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String, nullable=False)


class InfraDisasterRecoveryPlan(Base):
    __tablename__ = "infra_dr_plans"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)


class InfraBackupPolicy(Base):
    __tablename__ = "infra_backup_policies"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    frequency = Column(String, nullable=False)  # hourly, daily


class InfraRestoreJob(Base):
    __tablename__ = "infra_restore_jobs"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    status = Column(String, default="pending", nullable=False)


class InfraInfrastructureAudit(Base):
    __tablename__ = "infra_audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
