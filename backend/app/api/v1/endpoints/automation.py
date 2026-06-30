import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.dependencies.auth import RoleChecker, get_current_active_user
from app.dependencies.db import get_db
from app.models.automation import AutomationJob, JobExecution
from app.models.user import User, UserRole
from app.schemas.response import APIResponse
from app.services.automation_metrics import automation_metrics
from app.services.automation_service import automation_service
from app.services.event_listener import event_listener
from app.services.execution_history import execution_history
from app.services.scheduler_service import scheduler_service
from app.services.task_queue import task_queue

router = APIRouter(prefix="/automation", tags=["automation"])
admin_checker = RoleChecker([UserRole.ADMIN, UserRole.SUPER_ADMIN])

# --- Pydantic Schemas ---


class AutomationJobCreate(BaseModel):
    name: str = Field(
        ..., description="Job name", json_schema_extra={"example": "Workflow Seeder"}
    )
    description: Optional[str] = Field(None, description="Job description")
    trigger_type: str = Field(
        ...,
        description="cron, interval, event, manual, webhook",
        json_schema_extra={"example": "interval"},
    )
    cron_expression: Optional[str] = Field(
        None,
        description="Standard cron tab string (for cron jobs) or Event ID (for event jobs)",
        json_schema_extra={"example": "*/5 * * * *"},
    )
    interval_seconds: Optional[int] = Field(
        None,
        description="Frequency in seconds (for interval jobs)",
        json_schema_extra={"example": 60},
    )
    workflow_id: Optional[str] = Field(
        None,
        description="Logical workflow identifier target",
        json_schema_extra={"example": "multi_agent_review_workflow"},
    )
    agent_id: Optional[str] = Field(
        None,
        description="Logical agent identifier target",
        json_schema_extra={"example": "coding_agent"},
    )
    variables: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Variables accessible inside execution runs",
    )
    priority: str = Field("NORMAL", description="LOW, NORMAL, HIGH, CRITICAL")
    depends_on_job_id: Optional[int] = Field(
        None, description="Dependency parent job ID"
    )
    dependency_status: str = Field(
        "completed", description="Dependency status threshold trigger (e.g. completed)"
    )
    enabled: bool = Field(True, description="Enable scheduling and event matching")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "Ecosystem Sync Job",
                "trigger_type": "interval",
                "interval_seconds": 300,
                "workflow_id": "seeder_workflow",
                "priority": "HIGH",
                "enabled": True,
            }
        },
    )


class AutomationJobResponse(BaseModel):
    id: int
    uuid: str
    name: str
    description: Optional[str] = None
    trigger_type: str
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    workflow_id: Optional[str] = None
    agent_id: Optional[str] = None
    variables: str
    priority: str
    depends_on_job_id: Optional[int] = None
    dependency_status: Optional[str] = None
    enabled: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobExecutionResponse(BaseModel):
    id: int
    job_id: int
    execution_uuid: str
    status: str
    trigger_source: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    retry_count: int
    result: Optional[str] = None
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JobExecutionLogResponse(BaseModel):
    id: int
    execution_uuid: str
    timestamp: datetime
    level: str
    message: str
    duration_ms: Optional[int] = None
    correlation_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JobProgressResponse(BaseModel):
    status: str
    percentage: int
    current_step: str
    elapsed_seconds: float
    estimated_remaining_seconds: float
    last_updated: float


class WebhookTriggerPayload(BaseModel):
    event_type: str = Field(
        ...,
        description="System or webhook event identifier",
        json_schema_extra={"example": "github_push"},
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata and variables associated with the event",
    )


# --- REST Endpoints ---


@router.get("/jobs", response_model=APIResponse[List[AutomationJobResponse]])
def list_jobs(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """
    List all registered automation jobs.
    SuperAdmins and Admins can see all jobs, while normal users can only view jobs they created.
    """
    if current_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        jobs = db.query(AutomationJob).all()
    else:
        jobs = (
            db.query(AutomationJob)
            .filter(AutomationJob.created_by == current_user.id)
            .all()
        )
    return APIResponse(
        success=True, data=[AutomationJobResponse.model_validate(j) for j in jobs]
    )


@router.post(
    "/jobs",
    response_model=APIResponse[AutomationJobResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_job(
    payload: AutomationJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_checker),
):
    """
    Registers a new AI Automation Job. (Admins/SuperAdmins only)
    """
    job_data = payload.model_dump()
    job_data["created_by"] = current_user.id
    job = automation_service.register_job(db, job_data)
    return APIResponse(success=True, data=AutomationJobResponse.model_validate(job))


@router.get("/jobs/{id}", response_model=APIResponse[AutomationJobResponse])
def get_job(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve specific job definition.
    """
    job = db.query(AutomationJob).filter(AutomationJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Check permissions
    if (
        current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]
        and job.created_by != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Not authorized to view this job.")

    return APIResponse(success=True, data=AutomationJobResponse.model_validate(job))


@router.put("/jobs/{id}", response_model=APIResponse[AutomationJobResponse])
def update_job(
    id: int,
    payload: AutomationJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_checker),
):
    """
    Modify an existing job definition. (Admins/SuperAdmins only)
    """
    job = db.query(AutomationJob).filter(AutomationJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Remove from scheduler first to rebuild it
    scheduler_service.remove_scheduled_job(job.id)

    job.name = payload.name
    job.description = payload.description
    job.trigger_type = payload.trigger_type
    job.cron_expression = payload.cron_expression
    job.interval_seconds = payload.interval_seconds
    job.workflow_id = payload.workflow_id
    job.agent_id = payload.agent_id
    job.variables = json.dumps(payload.variables)
    job.priority = payload.priority.upper()
    job.depends_on_job_id = payload.depends_on_job_id
    job.dependency_status = payload.dependency_status
    job.enabled = payload.enabled
    job.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(job)

    # Re-register if enabled
    if job.enabled and job.trigger_type in ["cron", "interval"]:
        scheduler_service.add_scheduled_job(
            job_id=job.id,
            trigger_type=job.trigger_type,
            cron_expr=job.cron_expression,
            interval_secs=job.interval_seconds,
            execute_callback=automation_service.enqueue_scheduled_job,
        )

    return APIResponse(success=True, data=AutomationJobResponse.model_validate(job))


@router.delete("/jobs/{id}", response_model=APIResponse[Dict[str, str]])
def delete_job(
    id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_checker)
):
    """
    Delete a job definition and all related execution logs. (Admins/SuperAdmins only)
    """
    success = automation_service.delete_job(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found.")
    return APIResponse(success=True, message="Job deleted successfully.")


@router.post("/jobs/{id}/run", response_model=APIResponse[JobExecutionResponse])
def run_job(
    id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_checker)
):
    """
    Trigger manual execution of a job immediately. (Admins/SuperAdmins only)
    """
    execution = automation_service.trigger_job(db, job_id=id, trigger_source="manual")
    if not execution:
        raise HTTPException(status_code=404, detail="Unable to execute. Job not found.")
    return APIResponse(
        success=True, data=JobExecutionResponse.model_validate(execution)
    )


@router.post("/jobs/{id}/pause", response_model=APIResponse[AutomationJobResponse])
def pause_job(
    id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_checker)
):
    """
    Pause a scheduled job. (Admins/SuperAdmins only)
    """
    job = automation_service.pause_job(db, id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return APIResponse(success=True, data=AutomationJobResponse.model_validate(job))


@router.post("/jobs/{id}/resume", response_model=APIResponse[AutomationJobResponse])
def resume_job(
    id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_checker)
):
    """
    Resume a paused job. (Admins/SuperAdmins only)
    """
    job = automation_service.resume_job(db, id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return APIResponse(success=True, data=AutomationJobResponse.model_validate(job))


@router.post("/jobs/{id}/cancel", response_model=APIResponse[Dict[str, str]])
def cancel_job(
    id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_checker)
):
    """
    Aborts the active running execution of a job. (Admins/SuperAdmins only)
    """
    # Fetch latest execution
    last_exec = (
        db.query(JobExecution)
        .filter(JobExecution.job_id == id)
        .order_by(JobExecution.started_at.desc())
        .first()
    )
    if not last_exec or last_exec.status not in [
        "Pending",
        "Queued",
        "Running",
        "Waiting",
        "Retrying",
    ]:
        raise HTTPException(status_code=400, detail="Job is not actively executing.")

    success = automation_service.cancel_job_execution(db, last_exec.execution_uuid)
    if not success:
        raise HTTPException(
            status_code=500, detail="Failed to cancel active execution."
        )

    return APIResponse(success=True, message="Active execution cancelled successfully.")


@router.get(
    "/jobs/{id}/executions", response_model=APIResponse[List[JobExecutionResponse]]
)
def get_job_executions(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Fetch history of executions for a specific job.
    """
    job = db.query(AutomationJob).filter(AutomationJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    is_admin = current_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    if not is_admin and job.created_by != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to view these executions."
        )

    execs = execution_history.get_job_executions(db, job_id=id)
    return APIResponse(
        success=True, data=[JobExecutionResponse.model_validate(e) for e in execs]
    )


@router.get(
    "/jobs/{id}/logs", response_model=APIResponse[List[JobExecutionLogResponse]]
)
def get_job_execution_logs(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get detailed transition logs for the latest run of a specific job.
    """
    job = db.query(AutomationJob).filter(AutomationJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    is_admin = current_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    if not is_admin and job.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view logs.")

    last_exec = (
        db.query(JobExecution)
        .filter(JobExecution.job_id == id)
        .order_by(JobExecution.started_at.desc())
        .first()
    )
    if not last_exec:
        return APIResponse(success=True, data=[])

    logs = execution_history.get_logs(db, execution_uuid=last_exec.execution_uuid)
    return APIResponse(
        success=True, data=[JobExecutionLogResponse.model_validate(log) for log in logs]
    )


@router.get("/jobs/{id}/progress", response_model=APIResponse[JobProgressResponse])
def get_job_progress(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Query the live percentage and current step progress of an executing job.
    """
    job = db.query(AutomationJob).filter(AutomationJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    is_admin = current_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    if not is_admin and job.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized.")

    last_exec = (
        db.query(JobExecution)
        .filter(JobExecution.job_id == id)
        .order_by(JobExecution.started_at.desc())
        .first()
    )
    if not last_exec:
        raise HTTPException(status_code=404, detail="No executions found for this job.")

    prog = task_queue.get_progress(last_exec.execution_uuid)
    if not prog:
        # Construct fallback progress based on database record
        prog = {
            "status": last_exec.status,
            "percentage": 100 if last_exec.status == "Completed" else 0,
            "current_step": (
                "Completed" if last_exec.status == "Completed" else last_exec.status
            ),
            "elapsed_seconds": 0.0,
            "estimated_remaining_seconds": 0.0,
            "last_updated": datetime.utcnow().timestamp(),
        }

    return APIResponse(success=True, data=JobProgressResponse(**prog))


@router.get("/history", response_model=APIResponse[List[JobExecutionResponse]])
def get_global_history(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve global execution history records.
    """
    if current_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        execs = (
            db.query(JobExecution)
            .order_by(JobExecution.started_at.desc())
            .limit(limit)
            .all()
        )
    else:
        execs = (
            db.query(JobExecution)
            .join(AutomationJob)
            .filter(AutomationJob.created_by == current_user.id)
            .order_by(JobExecution.started_at.desc())
            .limit(limit)
            .all()
        )
    return APIResponse(
        success=True, data=[JobExecutionResponse.model_validate(e) for e in execs]
    )


@router.get("/statistics", response_model=APIResponse[Dict[str, Any]])
def get_statistics(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """
    Get core performance metrics, retry statistics, and duration averages.
    """
    stats = automation_metrics.get_dashboard_stats(db)
    return APIResponse(success=True, data=stats)


@router.get("/dashboard", response_model=APIResponse[Dict[str, Any]])
def get_dashboard(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a comprehensive dashboard statistics overview.
    """
    stats = automation_metrics.get_dashboard_stats(db)
    return APIResponse(success=True, data=stats)


@router.get("/scheduler", response_model=APIResponse[Dict[str, Any]])
def get_scheduler_status(current_user: User = Depends(get_current_active_user)):
    """
    Get live scheduler status, active providers, and configured cron tasks count.
    """
    jobs = len(scheduler_service.scheduler.get_jobs())
    return APIResponse(
        success=True,
        data={
            "running": scheduler_service.scheduler.running,
            "jobs_count": jobs,
            "provider": "apscheduler",
            "timezone": str(scheduler_service.scheduler.timezone),
        },
    )


@router.post("/webhook", response_model=APIResponse[Dict[str, str]])
def incoming_webhook(payload: WebhookTriggerPayload, db: Session = Depends(get_db)):
    """
    Public webhook receiver. Processes incoming POST payload and triggers matching event-based automation rules.
    """
    event_listener.notify_event(event_type=payload.event_type, payload=payload.payload)
    return APIResponse(success=True, message="Webhook payload received and queued.")
