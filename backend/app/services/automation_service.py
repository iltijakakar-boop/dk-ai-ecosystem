import asyncio
import json
from typing import Any, Dict, Optional

from ai.core.agent_manager import agent_manager
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.logging import logger
from app.db.session import SessionLocal
from app.models.automation import AutomationJob, JobExecution
from app.models.workflow_model import Workflow, WorkflowExecution
from app.services.execution_history import execution_history
from app.services.notification_service import notification_service
from app.services.retry_manager import retry_manager
from app.services.scheduler_service import scheduler_service
from app.services.task_queue import task_queue
from app.services.workflow_service import workflow_service


class AutomationService:
    """
    Core facade orchestrating the AI Automation & Autonomous Task Execution framework.
    """

    def __init__(self):
        # Register callback in task queue
        task_queue.set_executor_callback(self.execute_job_task)

    def register_job(self, db: Session, job_data: Dict[str, Any]) -> AutomationJob:
        # Deserialize JSON variables if passed as dict
        vars_str = "{}"
        if "variables" in job_data:
            if isinstance(job_data["variables"], dict):
                vars_str = json.dumps(job_data["variables"])
            elif isinstance(job_data["variables"], str):
                vars_str = job_data["variables"]

        job = AutomationJob(
            name=job_data["name"],
            description=job_data.get("description"),
            trigger_type=job_data["trigger_type"],
            cron_expression=job_data.get("cron_expression"),
            interval_seconds=job_data.get("interval_seconds"),
            workflow_id=job_data.get("workflow_id"),
            agent_id=job_data.get("agent_id"),
            variables=vars_str,
            priority=job_data.get("priority", "NORMAL").upper(),
            depends_on_job_id=job_data.get("depends_on_job_id"),
            dependency_status=job_data.get("dependency_status", "completed"),
            enabled=job_data.get("enabled", True),
            created_by=job_data.get("created_by"),
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Register in scheduler if enabled
        if job.enabled and job.trigger_type in ["cron", "interval"]:
            scheduler_service.add_scheduled_job(
                job_id=job.id,
                trigger_type=job.trigger_type,
                cron_expr=job.cron_expression,
                interval_secs=job.interval_seconds,
                execute_callback=self.enqueue_scheduled_job,
            )

        return job

    def enqueue_scheduled_job(self, job_id: int):
        """
        Callback from APScheduler to enqueue a job for running.
        """
        db = SessionLocal()
        try:
            self.trigger_job(db, job_id=job_id, trigger_source="scheduler")
        finally:
            db.close()

    def trigger_job(
        self,
        db: Session,
        job_id: int,
        trigger_source: str,
        override_variables: Optional[Dict[str, Any]] = None,
    ) -> Optional[JobExecution]:
        """
        Initializes job execution, checks dependencies, and enqueues to task queue.
        """
        job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
        if not job:
            logger.error(f"Cannot trigger Job {job_id}: Job not found.")
            return None

        # Generate a unique execution UUID
        import uuid

        exec_uuid = str(uuid.uuid4())

        # Check dependencies
        deps_satisfied = True
        waiting_reason = ""
        if job.depends_on_job_id:
            # Query last execution of dependent job
            last_exec = (
                db.query(JobExecution)
                .filter(JobExecution.job_id == job.depends_on_job_id)
                .order_by(JobExecution.started_at.desc())
                .first()
            )

            target_status = job.dependency_status or "Completed"
            if not last_exec or last_exec.status.lower() != target_status.lower():
                deps_satisfied = False
                waiting_reason = (
                    f"Waiting on Job {job.depends_on_job_id} to be "
                    f"'{target_status}' (current last status: {last_exec.status if last_exec else 'None'})"
                )

        status = "Queued" if deps_satisfied else "Waiting"

        # Create execution record
        exec_obj = execution_history.create_execution(
            db,
            job_id=job.id,
            execution_uuid=exec_uuid,
            trigger_source=trigger_source,
            status=status,
        )

        if not deps_satisfied:
            execution_history.log_step(
                db,
                exec_uuid,
                "WARNING",
                f"Execution suspended. Reason: {waiting_reason}",
            )
            # Keep execution in Waiting status, do not enqueue
            return exec_obj

        # Load execution variables
        vars_dict = {}
        if job.variables:
            try:
                vars_dict = json.loads(job.variables)
            except Exception:
                pass
        if override_variables:
            vars_dict.update(override_variables)

        # Enqueue task
        task_queue.enqueue(
            job_id=job.id,
            execution_uuid=exec_uuid,
            priority=job.priority,
            variables=vars_dict,
            trigger_source=trigger_source,
        )

        return exec_obj

    async def execute_job_task(
        self,
        execution_uuid: str,
        job_id: int,
        variables: Dict[str, Any],
        trigger_source: str,
    ):
        """
        Worker callback executing the actual task node.
        """
        db = SessionLocal()
        try:
            job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found during execution.")
                execution_history.update_execution(
                    db, execution_uuid, "Failed", error="Job not found."
                )
                return

            execution_history.update_execution(db, execution_uuid, "Running")
            execution_history.log_step(
                db, execution_uuid, "INFO", "Started job execution task."
            )

            # Execute variables evaluation
            task_queue.update_progress(execution_uuid, 20, "Evaluating rule conditions")

            # Simulate rule checks
            action = {"workflow_id": job.workflow_id, "agent_id": job.agent_id}

            # E.g. rules check placeholder if variables have conditions
            # If variables contain "rules", pass to rules engine

            task_queue.update_progress(execution_uuid, 40, "Executing action pipeline")
            execution_output = {}

            # 1. Run Workflow if defined
            if action.get("workflow_id"):
                wf_id_str = action["workflow_id"]
                execution_history.log_step(
                    db,
                    execution_uuid,
                    "INFO",
                    f"Triggering Workflow template: {wf_id_str}",
                )

                # Fetch Workflow
                wf = (
                    db.query(Workflow)
                    .filter(
                        (Workflow.id == wf_id_str) | (Workflow.workflow_id == wf_id_str)
                    )
                    .first()
                )
                if not wf:
                    raise ValueError(f"Workflow '{wf_id_str}' not found.")

                # Create WorkflowExecution
                wf_exec = WorkflowExecution(workflow_id=wf.id, status="running")
                db.add(wf_exec)
                db.commit()
                db.refresh(wf_exec)

                # Run pipeline synchronously in this thread worker
                workflow_service.run_workflow_pipeline(wf_exec.id)

                # Refresh status
                db.refresh(wf_exec)
                if wf_exec.status == "failed":
                    raise ValueError(f"Workflow execution {wf_exec.id} failed.")

                execution_output = {
                    "workflow_execution_id": wf_exec.id,
                    "status": wf_exec.status,
                }
                execution_history.log_step(
                    db,
                    execution_uuid,
                    "INFO",
                    f"Workflow execution {wf_exec.id} completed successfully.",
                )

            # 2. Run Agent if defined
            elif action.get("agent_id"):
                agent_id_str = action["agent_id"]
                execution_history.log_step(
                    db, execution_uuid, "INFO", f"Triggering Agent: {agent_id_str}"
                )

                agent_manager.discover_agents()
                agent = agent_manager.get_agent(agent_id_str)
                if not agent:
                    raise ValueError(f"Agent '{agent_id_str}' not found.")

                # Run agent chat/execution
                input_prompt = variables.get("prompt", "Ecosystem automation check")
                agent_res = agent_manager.execute_agent(
                    agent_id=agent_id_str,
                    input_text=input_prompt,
                    context={"session_id": f"auto_{execution_uuid}", **variables},
                )

                if not agent_res.success:
                    raise ValueError(f"Agent execution failed: {agent_res.error}")

                execution_output = {"agent_output": agent_res.output}
                execution_history.log_step(
                    db,
                    execution_uuid,
                    "INFO",
                    f"Agent execution completed successfully. Output length: {len(agent_res.output)} chars.",
                )

            else:
                # No target, run simple diagnostic test execution
                logger.info(f"Job {job_id} executed with variables: {variables}")
                execution_output = {
                    "message": "Diagnostic test run completed successfully."
                }
                execution_history.log_step(
                    db, execution_uuid, "INFO", "Simple diagnostic run executed."
                )

            task_queue.update_progress(execution_uuid, 80, "Wrapping up job logs")

            # Mark completion
            execution_history.update_execution(
                db,
                execution_uuid=execution_uuid,
                status="Completed",
                result=json.dumps(execution_output),
            )

            # Send completion notification if configured
            notification_service.send_notification(
                db,
                provider="email",
                recipient="admin@example.com",
                subject=f"Job Completed: {job.name}",
                message=f"Job {job.name} (Execution: {execution_uuid}) completed successfully.",
            )

            # Check for downstream jobs in Waiting state depending on this job
            self._resume_waiting_dependent_jobs(db, job.id)

        except Exception as e:
            # Handle Retry logic
            current_retry = 0
            exec_rec = (
                db.query(JobExecution)
                .filter(JobExecution.execution_uuid == execution_uuid)
                .first()
            )
            if exec_rec:
                current_retry = exec_rec.retry_count

            if retry_manager.should_retry(
                current_retry,
                (
                    job.max_retries
                    if hasattr(job, "max_retries")
                    else settings.MAX_JOB_RETRIES
                ),
            ):
                new_retry = current_retry + 1
                backoff = retry_manager.calculate_backoff(new_retry)

                execution_history.update_execution(
                    db,
                    execution_uuid=execution_uuid,
                    status="Retrying",
                    retry_count=new_retry,
                    error=str(e),
                )
                execution_history.log_step(
                    db,
                    execution_uuid,
                    "WARNING",
                    f"Execution failed: {e}. Retrying ({new_retry}) in {backoff}s...",
                )

                # Reschedule retry run in background
                asyncio.create_task(
                    self._schedule_retry(
                        execution_uuid, job_id, variables, trigger_source, backoff
                    )
                )
            else:
                execution_history.update_execution(
                    db, execution_uuid=execution_uuid, status="Failed", error=str(e)
                )
                execution_history.log_step(
                    db, execution_uuid, "ERROR", f"Job failed: {e}"
                )

                # Send failure notification
                notification_service.send_notification(
                    db,
                    provider="email",
                    recipient="admin@example.com",
                    subject=f"Job FAILED: {job.name}",
                    message=f"Job {job.name} (Execution: {execution_uuid}) failed. Error: {e}",
                )
        finally:
            db.close()

    async def _schedule_retry(
        self,
        execution_uuid: str,
        job_id: int,
        variables: Dict[str, Any],
        trigger_source: str,
        delay: float,
    ):
        await asyncio.sleep(delay)
        db = SessionLocal()
        try:
            job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
            if job:
                # Re-enqueue
                task_queue.enqueue(
                    job_id=job_id,
                    execution_uuid=execution_uuid,
                    priority=job.priority,
                    variables=variables,
                    trigger_source=trigger_source,
                )
        finally:
            db.close()

    def _resume_waiting_dependent_jobs(self, db: Session, completed_job_id: int):
        waiting_jobs = (
            db.query(AutomationJob)
            .filter(
                AutomationJob.enabled,
                AutomationJob.depends_on_job_id == completed_job_id,
                AutomationJob.dependency_status == "completed",
            )
            .all()
        )

        for w_job in waiting_jobs:
            # Find any execution of this job currently in "Waiting" state
            waiting_execs = (
                db.query(JobExecution)
                .filter(
                    JobExecution.job_id == w_job.id, JobExecution.status == "Waiting"
                )
                .all()
            )

            for exec_obj in waiting_execs:
                logger.info(
                    f"Dependency met for Job {w_job.id} (Execution {exec_obj.execution_uuid}). Queueing..."
                )

                # Update status to Queued
                exec_obj.status = "Queued"
                db.commit()

                # Enqueue in priority queue
                vars_dict = {}
                if w_job.variables:
                    try:
                        vars_dict = json.loads(w_job.variables)
                    except Exception:
                        pass

                task_queue.enqueue(
                    job_id=w_job.id,
                    execution_uuid=exec_obj.execution_uuid,
                    priority=w_job.priority,
                    variables=vars_dict,
                    trigger_source=exec_obj.trigger_source,
                )

    def pause_job(self, db: Session, job_id: int) -> Optional[AutomationJob]:
        job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
        if not job:
            return None
        job.enabled = False
        db.commit()
        db.refresh(job)

        # Remove from scheduler
        scheduler_service.remove_scheduled_job(job_id)
        return job

    def resume_job(self, db: Session, job_id: int) -> Optional[AutomationJob]:
        job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
        if not job:
            return None
        job.enabled = True
        db.commit()
        db.refresh(job)

        # Add back to scheduler if appropriate
        if job.trigger_type in ["cron", "interval"]:
            scheduler_service.add_scheduled_job(
                job_id=job.id,
                trigger_type=job.trigger_type,
                cron_expr=job.cron_expression,
                interval_secs=job.interval_seconds,
                execute_callback=self.enqueue_scheduled_job,
            )
        return job

    def cancel_job_execution(self, db: Session, execution_uuid: str) -> bool:
        # Try cancelling in task queue
        cancelled = task_queue.cancel_task(execution_uuid)
        if cancelled:
            execution_history.update_execution(db, execution_uuid, "Cancelled")
            execution_history.log_step(
                db, execution_uuid, "WARNING", "Execution cancelled by user request."
            )
            return True
        return False

    def delete_job(self, db: Session, job_id: int) -> bool:
        job = db.query(AutomationJob).filter(AutomationJob.id == job_id).first()
        if not job:
            return False

        # De-register scheduled
        scheduler_service.remove_scheduled_job(job_id)

        # Delete related executions
        db.query(JobExecution).filter(JobExecution.job_id == job_id).delete()
        db.delete(job)
        db.commit()
        return True


automation_service = AutomationService()
# Share with central event listener
from app.services.event_listener import event_listener

event_listener.set_automation_service(automation_service)
