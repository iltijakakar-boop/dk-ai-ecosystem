from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.dependencies.db import get_db
from app.schemas.response import APIResponse
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowExecutionResponse,
    TaskResponse,
    DeadLetterQueueResponse,
    OrchestratorStatusResponse
)
from app.models.workflow_model import (
    Workflow,
    WorkflowExecution,
    Task,
    DeadLetterQueue
)
from app.services.workflow_service import workflow_service
from app.services.approval_service import approval_service
from ai.orchestrator.workflow_engine import workflow_engine
from app.core.logging.logger import logger

router = APIRouter(prefix="/workflows", tags=["workflows"])

@router.post("", response_model=APIResponse[WorkflowResponse])
def create_or_update_workflow_template(
    payload: WorkflowCreate,
    db: Session = Depends(get_db)
):
    """
    Creates a new workflow template, or registers a new version of an existing template
    under a logical workflow_id without overwriting old runs.
    """
    wf = workflow_service.create_or_update_workflow(db, payload)
    return APIResponse(success=True, data=WorkflowResponse.model_validate(wf))


@router.get("", response_model=APIResponse[List[WorkflowResponse]])
def list_active_workflows(
    include_templates: bool = Query(True, description="Whether to include seeded system templates"),
    db: Session = Depends(get_db)
):
    """
    Lists active workflow templates and user-defined workflow groups.
    """
    query = db.query(Workflow).filter(Workflow.is_active == True)
    if not include_templates:
        query = query.filter(Workflow.is_template == False)
        
    wfs = query.all()
    res = [WorkflowResponse.model_validate(w) for w in wfs]
    return APIResponse(success=True, data=res)


@router.get("/dead-letter", response_model=APIResponse[List[DeadLetterQueueResponse]])
def list_dead_letter_queue_records(db: Session = Depends(get_db)):
    """
    Lists all diagnostic logs in the Dead Letter Queue (DLQ) for analysis.
    """
    records = db.query(DeadLetterQueue).all()
    res = [DeadLetterQueueResponse.model_validate(r) for r in records]
    return APIResponse(success=True, data=res)


@router.get("/{id}", response_model=APIResponse[WorkflowResponse])
def get_workflow_template_details(id: int, db: Session = Depends(get_db)):
    """
    Retrieves full details of a specific workflow template version.
    """
    wf = db.query(Workflow).filter(Workflow.id == id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    return APIResponse(success=True, data=WorkflowResponse.model_validate(wf))


@router.post("/{id}/execute", response_model=APIResponse[WorkflowExecutionResponse])
def execute_workflow_run(
    id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Creates a new WorkflowExecution run and starts executing steps asynchronously.
    """
    wf = db.query(Workflow).filter(Workflow.id == id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    # Create run instance
    execution = WorkflowExecution(
        workflow_id=wf.id,
        status="pending"
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    # Dispatch to background task runner
    background_tasks.add_task(
        workflow_engine.execute_workflow,
        execution_id=execution.id
    )

    return APIResponse(success=True, data=WorkflowExecutionResponse.model_validate(execution))


@router.post("/{id}/pause", response_model=APIResponse[WorkflowExecutionResponse])
def pause_workflow_execution(id: int, db: Session = Depends(get_db)):
    """
    Pauses a currently running execution run.
    """
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found.")
    
    if execution.status == "running":
        execution.status = "waiting"
        db.commit()
        db.refresh(execution)
        
    return APIResponse(success=True, data=WorkflowExecutionResponse.model_validate(execution))


@router.post("/{id}/resume", response_model=APIResponse[WorkflowExecutionResponse])
def resume_workflow_execution(
    id: int,
    background_tasks: BackgroundTasks,
    task_id: Optional[int] = Query(None, description="Approve specific paused approval task ID"),
    db: Session = Depends(get_db)
):
    """
    Resumes a paused execution run. Approves human task nodes if task_id is specified.
    """
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found.")

    # If approving a specific human task
    if task_id is not None:
        approved = approval_service.approve_task(db, task_id)
        if not approved:
            raise HTTPException(status_code=400, detail="Failed to approve task. Must be in 'waiting' status.")
    else:
        # Standard resume
        if execution.status == "waiting":
            execution.status = "running"
            db.commit()

    # Re-dispatch loop to background tasks queue
    background_tasks.add_task(
        workflow_engine.execute_workflow,
        execution_id=execution.id
    )

    db.refresh(execution)
    return APIResponse(success=True, data=WorkflowExecutionResponse.model_validate(execution))


@router.post("/{id}/cancel", response_model=APIResponse[WorkflowExecutionResponse])
def cancel_workflow_execution(id: int, db: Session = Depends(get_db)):
    """
    Terminates a workflow execution.
    """
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found.")

    execution.status = "cancelled"
    execution.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(execution)
    return APIResponse(success=True, data=WorkflowExecutionResponse.model_validate(execution))


@router.get("/{id}/status", response_model=APIResponse[WorkflowExecutionResponse])
def get_execution_status(id: int, db: Session = Depends(get_db)):
    """
    Returns the execution status, current step, and context variables.
    """
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found.")
    return APIResponse(success=True, data=WorkflowExecutionResponse.model_validate(execution))


@router.get("/tasks", response_model=APIResponse[List[TaskResponse]], tags=["tasks"])
def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    Lists tasks across all executions.
    """
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    tasks = query.all()
    res = [TaskResponse.model_validate(t) for t in tasks]
    return APIResponse(success=True, data=res)


@router.get("/tasks/{id}", response_model=APIResponse[TaskResponse], tags=["tasks"])
def get_task_details(id: int, db: Session = Depends(get_db)):
    """
    Retrieves full details of a specific task.
    """
    task = db.query(Task).filter(Task.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return APIResponse(success=True, data=TaskResponse.model_validate(task))


@router.get("/orchestrator/status", response_model=APIResponse[OrchestratorStatusResponse], tags=["orchestrator"])
def get_orchestrator_summary_status(db: Session = Depends(get_db)):
    """
    Returns metrics tracking active workflows, failures, queues, and average run times.
    """
    active_wf = db.query(WorkflowExecution).filter(WorkflowExecution.status == "running").count()
    failed_wf = db.query(WorkflowExecution).filter(WorkflowExecution.status == "failed").count()
    dlq_count = db.query(DeadLetterQueue).count()

    # Seeded mocks representing running agents and execution times
    summary = OrchestratorStatusResponse(
        active_workflows=active_wf,
        running_agents=2 if active_wf > 0 else 0,
        queue_length=0,
        average_execution_time_ms=1250.0,
        failed_workflows=failed_wf,
        retry_count=dlq_count
    )
    return APIResponse(success=True, data=summary)
