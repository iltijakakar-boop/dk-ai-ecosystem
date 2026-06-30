from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from app.db.session import Base


class ObsSystemMetric(Base):
    __tablename__ = "obs_system_metrics"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    cpu_percent = Column(Float, nullable=False)
    memory_percent = Column(Float, nullable=False)
    gpu_percent = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)


class ObsApplicationMetric(Base):
    __tablename__ = "obs_application_metrics"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)


class ObsTrace(Base):
    __tablename__ = "obs_traces"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    trace_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    duration_ms = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class ObsTraceSpan(Base):
    __tablename__ = "obs_trace_spans"
    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, ForeignKey("obs_traces.trace_id", ondelete="CASCADE"), nullable=False)
    span_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    duration_ms = Column(Float, nullable=False)


class ObsLogEntry(Base):
    __tablename__ = "obs_log_entries"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    log_level = Column(String, default="INFO", nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)


class ObsAuditEvent(Base):
    __tablename__ = "obs_audit_events"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    target = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)


class ObsAlertRule(Base):
    __tablename__ = "obs_alert_rules"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    metric_name = Column(String, nullable=False)
    threshold = Column(Float, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)


class ObsAlert(Base):
    __tablename__ = "obs_alerts"
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("obs_alert_rules.id", ondelete="CASCADE"), nullable=False)
    message = Column(String, nullable=False)
    resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class ObsIncident(Base):
    __tablename__ = "obs_incidents"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # minor, major, critical
    status = Column(String, default="open", nullable=False)  # open, closed


class ObsIncidentTimeline(Base):
    __tablename__ = "obs_incident_timeline"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("obs_incidents.id", ondelete="CASCADE"), nullable=False)
    event_description = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)


class ObsIncidentComment(Base):
    __tablename__ = "obs_incident_comments"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("obs_incidents.id", ondelete="CASCADE"), nullable=False)
    comment = Column(Text, nullable=False)


class ObsSecurityEvent(Base):
    __tablename__ = "obs_security_events"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    event_type = Column(String, nullable=False)  # suspicious_login, rate_limit_violation
    severity = Column(String, nullable=False)


class ObsThreatDetection(Base):
    __tablename__ = "obs_threat_detections"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    description = Column(String, nullable=False)
    resolved = Column(Boolean, default=False, nullable=False)


class ObsCompliancePolicy(Base):
    __tablename__ = "obs_compliance_policies"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    policy_name = Column(String, nullable=False)  # GDPR, SOC2
    passed = Column(Boolean, default=True, nullable=False)


class ObsComplianceReport(Base):
    __tablename__ = "obs_compliance_reports"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    report_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class ObsRiskAssessment(Base):
    __tablename__ = "obs_risk_assessments"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    assessed_risk_level = Column(String, nullable=False)


class ObsGovernancePolicy(Base):
    __tablename__ = "obs_governance_policies"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    policy_text = Column(Text, nullable=False)


class ObsAIUsagePolicy(Base):
    __tablename__ = "obs_ai_usage_policies"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    max_tokens_per_request = Column(Integer, nullable=False)


class ObsModelAudit(Base):
    __tablename__ = "obs_model_audits"
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False)
    action = Column(String, nullable=False)


class ObsWorkflowAudit(Base):
    __tablename__ = "obs_workflow_audits"
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String, nullable=False)
    action = Column(String, nullable=False)


class ObsAgentAudit(Base):
    __tablename__ = "obs_agent_audits"
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, nullable=False)
    action = Column(String, nullable=False)


class ObsMCPAudit(Base):
    __tablename__ = "obs_mcp_audits"
    id = Column(Integer, primary_key=True, index=True)
    mcp_server_name = Column(String, nullable=False)
    action = Column(String, nullable=False)


class ObsAPIAudit(Base):
    __tablename__ = "obs_api_audits"
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False)


class ObsSystemHealth(Base):
    __tablename__ = "obs_system_health"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="healthy", nullable=False)


class ObsNodeHealth(Base):
    __tablename__ = "obs_node_health"
    id = Column(Integer, primary_key=True, index=True)
    node_name = Column(String, nullable=False)
    status = Column(String, default="healthy", nullable=False)


class ObsServiceHealth(Base):
    __tablename__ = "obs_service_health"
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, nullable=False)
    status = Column(String, default="healthy", nullable=False)


class ObsDashboard(Base):
    __tablename__ = "obs_dashboards"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    layout_json = Column(Text, nullable=False)


class ObsNotificationRule(Base):
    __tablename__ = "obs_notification_rules"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    channel = Column(String, nullable=False)  # email, slack


class ObsNotificationHistory(Base):
    __tablename__ = "obs_notification_history"
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("obs_notification_rules.id", ondelete="CASCADE"), nullable=False)
    sent_at = Column(DateTime, default=func.now(), nullable=False)
