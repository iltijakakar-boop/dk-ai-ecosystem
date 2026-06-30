from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.observability import (
    ObsSystemMetricCreate,
    ObsSystemMetricResponse,
    ObsLogEntryCreate,
    ObsLogEntryResponse,
    ObsTraceResponse,
    ObsAlertRuleCreate,
    ObsAlertRuleResponse,
    ObsAlertResponse,
    ObsIncidentCreate,
    ObsIncidentResponse,
)
from app.services.observability_service import (
    metrics_service,
    logging_service,
    tracing_service,
    alert_service,
    incident_service,
)


router = APIRouter(prefix="/observability", tags=["observability"])


@router.post("/metrics", response_model=APIResponse[ObsSystemMetricResponse])
def log_system_metrics(
    payload: ObsSystemMetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    metric = metrics_service.record_system_metrics(
        db,
        workspace_id=payload.workspace_id,
        cpu_percent=payload.cpu_percent,
        memory_percent=payload.memory_percent,
        gpu_percent=payload.gpu_percent,
    )
    return APIResponse(success=True, message="System metrics recorded.", data=ObsSystemMetricResponse.model_validate(metric))


@router.get("/metrics", response_model=APIResponse[List[ObsSystemMetricResponse]])
def get_recorded_metrics(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    metrics = metrics_service.get_metrics(db, workspace_id)
    res = [ObsSystemMetricResponse.model_validate(m) for m in metrics]
    return APIResponse(success=True, data=res)


@router.post("/logs", response_model=APIResponse[ObsLogEntryResponse])
def create_structured_log(
    payload: ObsLogEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    log = logging_service.create_log_entry(db, workspace_id=payload.workspace_id, log_level=payload.log_level, message=payload.message)
    return APIResponse(success=True, message="Log entry recorded.", data=ObsLogEntryResponse.model_validate(log))


@router.get("/logs", response_model=APIResponse[List[ObsLogEntryResponse]])
def query_application_logs(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    logs = logging_service.get_logs(db, workspace_id)
    res = [ObsLogEntryResponse.model_validate(l) for l in logs]
    return APIResponse(success=True, data=res)


@router.get("/traces", response_model=APIResponse[List[ObsTraceResponse]])
def query_distributed_traces(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    traces = tracing_service.get_traces(db, workspace_id)
    res = [ObsTraceResponse.model_validate(t) for t in traces]
    return APIResponse(success=True, data=res)


@router.post("/alerts/rules", response_model=APIResponse[ObsAlertRuleResponse])
def create_threshold_alert_rule(
    payload: ObsAlertRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    rule = alert_service.create_rule(db, workspace_id=payload.workspace_id, metric_name=payload.metric_name, threshold=payload.threshold)
    return APIResponse(success=True, message="Alert rule established.", data=ObsAlertRuleResponse.model_validate(rule))


@router.get("/alerts", response_model=APIResponse[List[ObsAlertResponse]])
def list_triggered_alerts(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    alerts = alert_service.get_alerts(db, workspace_id)
    res = [ObsAlertResponse.model_validate(a) for a in alerts]
    return APIResponse(success=True, data=res)


@router.post("/incidents", response_model=APIResponse[ObsIncidentResponse])
def report_ops_incident(
    payload: ObsIncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    incident = incident_service.create_incident(db, workspace_id=payload.workspace_id, title=payload.title, severity=payload.severity)
    return APIResponse(success=True, message="Incident reported.", data=ObsIncidentResponse.model_validate(incident))


@router.get("/incidents", response_model=APIResponse[List[ObsIncidentResponse]])
def list_workspace_incidents(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    incidents = incident_service.get_incidents(db, workspace_id)
    res = [ObsIncidentResponse.model_validate(i) for i in incidents]
    return APIResponse(success=True, data=res)
