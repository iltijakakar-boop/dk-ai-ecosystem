from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.infrastructure_models import (
    InfraCluster,
    InfraNode,
    InfraDeployment,
    InfraPod,
    InfraEdgeNode,
    InfraBackupPolicy,
    InfraRestoreJob,
)


class ClusterService:
    def create_cluster(self, db: Session, *, workspace_id: int, name: str, api_endpoint: str) -> InfraCluster:
        cluster = InfraCluster(
            workspace_id=workspace_id,
            name=name,
            api_endpoint=api_endpoint,
            status="healthy"
        )
        db.add(cluster)
        db.commit()
        db.refresh(cluster)

        # Seed default node
        node = InfraNode(cluster_id=cluster.id, name=f"{name}-master-0", role="master", status="ready")
        db.add(node)
        db.commit()
        return cluster

    def get_clusters(self, db: Session, workspace_id: int) -> List[InfraCluster]:
        return db.query(InfraCluster).filter(InfraCluster.workspace_id == workspace_id).all()


class AutoScalingService:
    def create_deployment(self, db: Session, *, workspace_id: int, cluster_id: int, name: str, replicas: int) -> InfraDeployment:
        dep = InfraDeployment(
            workspace_id=workspace_id,
            cluster_id=cluster_id,
            name=name,
            replicas=replicas
        )
        db.add(dep)
        db.commit()
        db.refresh(dep)

        # Seed pods based on replicas
        for i in range(replicas):
            pod = InfraPod(
                deployment_id=dep.id,
                name=f"{name}-pod-{i}",
                status="running",
                cpu_cores=0.5
            )
            db.add(pod)
        db.commit()
        return dep

    def get_deployments(self, db: Session, workspace_id: int) -> List[InfraDeployment]:
        return db.query(InfraDeployment).filter(InfraDeployment.workspace_id == workspace_id).all()

    def get_pods(self, db: Session, deployment_id: int) -> List[InfraPod]:
        return db.query(InfraPod).filter(InfraPod.deployment_id == deployment_id).all()

    def scale_deployment(self, db: Session, deployment_id: int, replicas: int) -> InfraDeployment:
        dep = db.query(InfraDeployment).filter(InfraDeployment.id == deployment_id).first()
        if not dep:
            return None
        
        # Clean current pods
        db.query(InfraPod).filter(InfraPod.deployment_id == dep.id).delete()

        dep.replicas = replicas
        db.add(dep)

        # Add new pods
        for i in range(replicas):
            pod = InfraPod(
                deployment_id=dep.id,
                name=f"{dep.name}-pod-{i}",
                status="running",
                cpu_cores=0.5
            )
            db.add(pod)
        db.commit()
        db.refresh(dep)
        return dep


class EdgeAIService:
    def register_edge_node(self, db: Session, *, workspace_id: int, name: str) -> InfraEdgeNode:
        node = InfraEdgeNode(
            workspace_id=workspace_id,
            name=name,
            status="online",
            sync_status="synced"
        )
        db.add(node)
        db.commit()
        db.refresh(node)
        return node

    def get_edge_nodes(self, db: Session, workspace_id: int) -> List[InfraEdgeNode]:
        return db.query(InfraEdgeNode).filter(InfraEdgeNode.workspace_id == workspace_id).all()


class BackupService:
    def create_policy(self, db: Session, *, workspace_id: int, frequency: str) -> InfraBackupPolicy:
        policy = InfraBackupPolicy(
            workspace_id=workspace_id,
            frequency=frequency
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        return policy

    def trigger_restore(self, db: Session, workspace_id: int) -> InfraRestoreJob:
        job = InfraRestoreJob(
            workspace_id=workspace_id,
            status="completed"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job


cluster_service = ClusterService()
autoscaling_service = AutoScalingService()
edge_ai_service = EdgeAIService()
backup_service = BackupService()
