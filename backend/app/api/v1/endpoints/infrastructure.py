from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.infrastructure import (
    InfraClusterCreate,
    InfraClusterResponse,
    InfraDeploymentCreate,
    InfraDeploymentResponse,
    InfraPodResponse,
    InfraEdgeNodeCreate,
    InfraEdgeNodeResponse,
    InfraBackupPolicyCreate,
    InfraBackupPolicyResponse,
)
from app.services.infrastructure_service import (
    cluster_service,
    autoscaling_service,
    edge_ai_service,
    backup_service,
)


router = APIRouter(prefix="/infrastructure", tags=["infrastructure"])


@router.post("/clusters", response_model=APIResponse[InfraClusterResponse])
def create_kubernetes_cluster(
    payload: InfraClusterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    cluster = cluster_service.create_cluster(db, workspace_id=payload.workspace_id, name=payload.name, api_endpoint=payload.api_endpoint)
    return APIResponse(success=True, message="Kubernetes cluster registered.", data=InfraClusterResponse.model_validate(cluster))


@router.get("/clusters", response_model=APIResponse[List[InfraClusterResponse]])
def get_registered_clusters(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    clusters = cluster_service.get_clusters(db, workspace_id)
    res = [InfraClusterResponse.model_validate(c) for c in clusters]
    return APIResponse(success=True, data=res)


@router.post("/deployments", response_model=APIResponse[InfraDeploymentResponse])
def create_cluster_deployment(
    payload: InfraDeploymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    dep = autoscaling_service.create_deployment(
        db,
        workspace_id=payload.workspace_id,
        cluster_id=payload.cluster_id,
        name=payload.name,
        replicas=payload.replicas,
    )
    return APIResponse(success=True, message="Deployment created.", data=InfraDeploymentResponse.model_validate(dep))


@router.get("/deployments", response_model=APIResponse[List[InfraDeploymentResponse]])
def get_deployments_list(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    deps = autoscaling_service.get_deployments(db, workspace_id)
    res = [InfraDeploymentResponse.model_validate(d) for d in deps]
    return APIResponse(success=True, data=res)


@router.get("/pods", response_model=APIResponse[List[InfraPodResponse]])
def get_deployment_pods(
    deployment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    pods = autoscaling_service.get_pods(db, deployment_id=deployment_id)
    res = [InfraPodResponse.model_validate(p) for p in pods]
    return APIResponse(success=True, data=res)


@router.post("/scale", response_model=APIResponse[InfraDeploymentResponse])
def scale_deployment_replicas(
    deployment_id: int,
    replicas: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    dep = autoscaling_service.scale_deployment(db, deployment_id=deployment_id, replicas=replicas)
    if not dep:
        raise HTTPException(status_code=404, detail="Deployment not found.")
    return APIResponse(success=True, message="Scale action executed successfully.", data=InfraDeploymentResponse.model_validate(dep))


@router.post("/edge/nodes", response_model=APIResponse[InfraEdgeNodeResponse])
def register_remote_edge_node(
    payload: InfraEdgeNodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    node = edge_ai_service.register_edge_node(db, workspace_id=payload.workspace_id, name=payload.name)
    return APIResponse(success=True, message="Edge node registered successfully.", data=InfraEdgeNodeResponse.model_validate(node))


@router.get("/edge/nodes", response_model=APIResponse[List[InfraEdgeNodeResponse]])
def get_edge_nodes_list(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    nodes = edge_ai_service.get_edge_nodes(db, workspace_id)
    res = [InfraEdgeNodeResponse.model_validate(n) for n in nodes]
    return APIResponse(success=True, data=res)


@router.post("/backups/policy", response_model=APIResponse[InfraBackupPolicyResponse])
def configure_backup_policy(
    payload: InfraBackupPolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    policy = backup_service.create_policy(db, workspace_id=payload.workspace_id, frequency=payload.frequency)
    return APIResponse(success=True, message="Backup policy configured.", data=InfraBackupPolicyResponse.model_validate(policy))


@router.post("/backups/restore")
def trigger_restore_job(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    job = backup_service.trigger_restore(db, workspace_id)
    return APIResponse(success=True, message="Disaster recovery restore job triggered successfully.")
