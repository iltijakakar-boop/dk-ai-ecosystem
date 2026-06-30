import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.observability_models import (
    ObsSystemMetric,
    ObsLogEntry,
    ObsTrace,
    ObsTraceSpan,
    ObsAlertRule,
    ObsAlert,
    ObsIncident,
)


class MetricsService:
    def record_system_metrics(
        self, db: Session, *, workspace_id: int, cpu_percent: float, memory_percent: float, gpu_percent: Optional[float] = None
    ) -> ObsSystemMetric:
        metric = ObsSystemMetric(
            workspace_id=workspace_id,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            gpu_percent=gpu_percent
        )
        db.add(metric)
        db.commit()
        db.refresh(metric)

        # Alert evaluation check
        alert_rules = db.query(ObsAlertRule).filter(ObsAlertRule.workspace_id == workspace_id, ObsAlertRule.enabled == True).all()
        for rule in alert_rules:
            val = cpu_percent if rule.metric_name == "cpu" else memory_percent
            if val > rule.threshold:
                alert = ObsAlert(
                    rule_id=rule.id,
                    message=f"Alert! Metric '{rule.metric_name}' value {val}% breached threshold of {rule.threshold}%",
                    resolved=False
                )
                db.add(alert)
        db.commit()
        return metric

    def get_metrics(self, db: Session, workspace_id: int) -> List[ObsSystemMetric]:
        return db.query(ObsSystemMetric).filter(ObsSystemMetric.workspace_id == workspace_id).order_by(ObsSystemMetric.timestamp.desc()).all()


class LoggingService:
    def create_log_entry(self, db: Session, *, workspace_id: int, log_level: str, message: str) -> ObsLogEntry:
        log = ObsLogEntry(
            workspace_id=workspace_id,
            log_level=log_level,
            message=message
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def get_logs(self, db: Session, workspace_id: int) -> List[ObsLogEntry]:
        return db.query(ObsLogEntry).filter(ObsLogEntry.workspace_id == workspace_id).order_by(ObsLogEntry.timestamp.desc()).all()


class TracingService:
    def create_trace(self, db: Session, *, workspace_id: int, name: str, duration_ms: float) -> ObsTrace:
        trace_id = str(uuid.uuid4())
        trace = ObsTrace(
            workspace_id=workspace_id,
            trace_id=trace_id,
            name=name,
            duration_ms=duration_ms
        )
        db.add(trace)
        db.commit()
        db.refresh(trace)
        return trace

    def get_traces(self, db: Session, workspace_id: int) -> List[ObsTrace]:
        return db.query(ObsTrace).filter(ObsTrace.workspace_id == workspace_id).all()


class AlertService:
    def create_rule(self, db: Session, *, workspace_id: int, metric_name: str, threshold: float) -> ObsAlertRule:
        rule = ObsAlertRule(
            workspace_id=workspace_id,
            metric_name=metric_name,
            threshold=threshold,
            enabled=True
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    def get_alerts(self, db: Session, workspace_id: int) -> List[ObsAlert]:
        return (
            db.query(ObsAlert)
            .join(ObsAlertRule)
            .filter(ObsAlertRule.workspace_id == workspace_id)
            .all()
        )


class IncidentService:
    def create_incident(self, db: Session, *, workspace_id: int, title: str, severity: str) -> ObsIncident:
        incident = ObsIncident(
            workspace_id=workspace_id,
            title=title,
            severity=severity,
            status="open"
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident

    def get_incidents(self, db: Session, workspace_id: int) -> List[ObsIncident]:
        return db.query(ObsIncident).filter(ObsIncident.workspace_id == workspace_id).all()


metrics_service = MetricsService()
logging_service = LoggingService()
tracing_service = TracingService()
alert_service = AlertService()
incident_service = IncidentService()
