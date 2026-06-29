import json
import time
import traceback
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.workflow_model import (
    Workflow,
    WorkflowExecution,
    Task,
    TaskExecution,
    AgentAssignment,
    DeadLetterQueue
)
from ai.orchestrator.orchestrator import agent_orchestrator
from ai.orchestrator.event_bus import event_bus
from ai.orchestrator.state_manager import StateManager
from ai.shared_memory.shared_context import SharedContextMemory
from app.config.settings import settings
from app.core.logging.logger import logger

class WorkflowService:
    """
    Coordinates seeding templates, executing workflows in background loops,
    matching capabilities, handling retries, pausing on human approvals, and DLQ routing.
    """
    
    def seed_default_templates(self, db: Session) -> None:
        """
        Seeds standard multi-agent workflows into the workflows table if not present.
        """
        templates = [
            {
                "workflow_id": "research_workflow",
                "name": "Research Workflow",
                "description": "Multi-agent research analysis template",
                "definition": {
                    "steps": [
                        {"name": "research_step", "required_capability": "research", "input": {"query": "Ecosystem documentation trends"}},
                        {"name": "analysis_step", "required_capability": "analysis", "input": {"aspect": "modularity"}}
                    ]
                }
            },
            {
                "workflow_id": "coding_workflow",
                "name": "Coding Workflow",
                "description": "Automated code writing and linting pipeline",
                "definition": {
                    "steps": [
                        {"name": "coding_step", "required_capability": "coding", "input": {"task": "Write simple RAG context builder"}},
                        {"name": "analysis_step", "required_capability": "analysis", "input": {"rule": "Lint check code format"}}
                    ]
                }
            },
            {
                "workflow_id": "document_analysis_workflow",
                "name": "Document Analysis Workflow",
                "description": "Scans uploaded files and summarizes contents",
                "definition": {
                    "steps": [
                        {"name": "document_step", "required_capability": "document", "input": {"scope": "all"}},
                        {"name": "analysis_step", "required_capability": "analysis", "input": {"depth": "detailed"}}
                    ]
                }
            },
            {
                "workflow_id": "multi_agent_review_workflow",
                "name": "Multi-Agent Review Workflow",
                "description": "Pipeline requiring manual human confirmation to proceed",
                "definition": {
                    "steps": [
                        {"name": "planning_step", "required_capability": "planning", "input": {"strategy": "Q2 RAG expansions"}},
                        {"name": "human_approval_step", "required_capability": "human_approval", "requires_approval": True, "input": {}}
                    ]
                }
            }
        ]

        for temp in templates:
            existing = db.query(Workflow).filter(
                Workflow.workflow_id == temp["workflow_id"],
                Workflow.is_template == True
            ).first()
            
            if not existing:
                workflow_obj = Workflow(
                    workflow_id=temp["workflow_id"],
                    version=1,
                    is_active=True,
                    is_template=True,
                    name=temp["name"],
                    description=temp["description"],
                    definition=json.dumps(temp["definition"])
                )
                db.add(workflow_obj)
        db.commit()

    def create_or_update_workflow(self, db: Session, payload: Any) -> Workflow:
        """
        Workflow Versioning: Creates a new workflow record or increments version on update.
        """
        workflow_id = payload.workflow_id
        if not workflow_id:
            import uuid
            workflow_id = f"wf_{str(uuid.uuid4())[:8]}"

        # Resolve current active version
        active_wf = db.query(Workflow).filter(
            Workflow.workflow_id == workflow_id,
            Workflow.is_active == True
        ).first()

        new_version = 1
        if active_wf:
            new_version = active_wf.version + 1
            # Mark previous version inactive
            active_wf.is_active = False
            db.commit()

        new_wf = Workflow(
            workflow_id=workflow_id,
            version=new_version,
            is_active=True,
            is_template=payload.is_template or False,
            name=payload.name,
            description=payload.description,
            definition=json.dumps(payload.definition)
        )
        db.add(new_wf)
        db.commit()
        db.refresh(new_wf)
        return new_wf

    def run_workflow_pipeline(self, execution_id: int) -> None:
        """
        Orchestration execution loop. Runs sequence instructions, catches failures,
        pauses on human approvals, and routes to DeadLetterQueue.
        """
        db = SessionLocal()
        exec_obj = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
        if not exec_obj:
            db.close()
            return

        exec_obj.status = "running"
        db.commit()
        
        event_bus.publish(execution_id, None, "WorkflowStarted", f"Workflow execution {execution_id} started.")

        try:
            workflow = exec_obj.workflow
            definition = json.loads(workflow.definition)
            steps = definition.get("steps", [])
            shared_memory = SharedContextMemory(execution_id)

            # Loop through workflow definition steps
            for step in steps:
                step_name = step["name"]
                
                # Check if current execution status was cancelled
                db.refresh(exec_obj)
                if exec_obj.status in ["cancelled", "failed"]:
                    logger.info(f"Execution {execution_id} halted because status is {exec_obj.status}")
                    break

                # 1. Check if this step has already been completed in a previous paused run
                existing_task = db.query(Task).filter(
                    Task.workflow_execution_id == execution_id,
                    Task.name == step_name
                ).first()
                
                if existing_task and existing_task.status == "completed":
                    logger.info(f"Step '{step_name}' already completed in previous run. Skipping.")
                    continue

                # 2. Update execution current active step
                exec_obj.current_step = step_name
                db.commit()

                # 3. Create or resolve task node
                if not existing_task:
                    existing_task = Task(
                        workflow_execution_id=execution_id,
                        name=step_name,
                        status="pending",
                        required_capability=step.get("required_capability"),
                        input_data=json.dumps(step.get("input", {})),
                        max_retries=step.get("max_retries", settings.MAX_WORKFLOW_RETRIES),
                        timeout_seconds=step.get("timeout_seconds", settings.DEFAULT_TASK_TIMEOUT_SECONDS)
                    )
                    db.add(existing_task)
                    db.commit()
                    db.refresh(existing_task)

                task = existing_task
                event_bus.publish(execution_id, task.id, "TaskCreated", f"Task '{step_name}' registered.")

                # 4. Enforce Human-in-the-Loop Approval Check
                if step.get("requires_approval") or task.required_capability == "human_approval":
                    task.status = "waiting"
                    exec_obj.status = "waiting"
                    db.commit()
                    event_bus.publish(
                        execution_id, 
                        task.id, 
                        "TaskSuspended", 
                        f"Task '{step_name}' paused. Awaiting human approval."
                    )
                    # Pause loop. Resuming is handled via the approval services resume endpoint
                    break

                # 5. Resolve capability matching agent
                required_cap = task.required_capability or "chat"
                assigned_agent_id = agent_orchestrator.find_agent_by_capability(required_cap)
                
                if not assigned_agent_id:
                    # Move directly to DLQ
                    error_msg = f"No eligible agent found possessing capability: '{required_cap}'."
                    self._route_to_dlq(db, task, exec_obj, error_msg, "N/A")
                    break

                # Create assignments and audit run records
                task.status = "running"
                db.add(AgentAssignment(task_id=task.id, agent_id=assigned_agent_id))
                task_exec = TaskExecution(task_id=task.id, agent_id=assigned_agent_id, status="running")
                db.add(task_exec)
                db.commit()

                event_bus.publish(
                    execution_id, 
                    task.id, 
                    "AgentStarted", 
                    f"Agent '{assigned_agent_id}' started task '{step_name}'."
                )

                # 6. Task Execution Retry Policy Loop
                success = False
                last_error = None
                
                # Fetch inputs from shared context if referenced from a previous step's output
                inputs = json.loads(task.input_data)
                
                for attempt in range(1, task.max_retries + 1):
                    try:
                        task.retry_count = attempt - 1
                        db.commit()

                        # Simulate execution via Orchestrator message routing
                        agent_reply = agent_orchestrator.route_agent_message(
                            "orchestrator", 
                            assigned_agent_id, 
                            f"Process inputs: {inputs}"
                        )

                        # Success
                        success = True
                        task.status = "completed"
                        task.output_data = json.dumps({
                            "result": f"Step '{step_name}' successfully executed by {assigned_agent_id}.",
                            "agent_response": agent_reply
                        })
                        
                        task_exec.status = "completed"
                        task_exec.completed_at = datetime.now(timezone.utc)
                        db.commit()

                        # Save output to Shared Memory context variables
                        shared_memory.set_variable(f"{step_name}_output", json.loads(task.output_data))
                        
                        event_bus.publish(
                            execution_id, 
                            task.id, 
                            "TaskCompleted", 
                            f"Task '{step_name}' completed."
                        )
                        event_bus.publish(
                            execution_id, 
                            task.id, 
                            "AgentFinished", 
                            f"Agent '{assigned_agent_id}' finished task '{step_name}'."
                        )
                        break

                    except Exception as err:
                        last_error = err
                        logger.warning(f"Attempt {attempt} failed for task '{step_name}': {err}")
                        time.sleep(attempt * 0.1) # exponential backoff simulation

                if not success:
                    # 7. Dead Letter Queue Routing on exhaustion
                    error_reason = f"Task failed after {task.max_retries} attempts. Error: {last_error}"
                    trace_str = traceback.format_exc()
                    
                    self._route_to_dlq(db, task, exec_obj, error_reason, trace_str)
                    break

            # Check if all tasks completed successfully
            db.refresh(exec_obj)
            all_completed = True
            for t in exec_obj.tasks:
                if t.status != "completed":
                    all_completed = False
                    
            if all_completed and exec_obj.status == "running":
                exec_obj.status = "completed"
                exec_obj.completed_at = datetime.now(timezone.utc)
                db.commit()
                event_bus.publish(execution_id, None, "WorkflowCompleted", f"Workflow execution {execution_id} completed.")

        except Exception as e:
            logger.exception(f"Unhandled crash inside workflow execution {execution_id}:")
            exec_obj.status = "failed"
            db.commit()
            event_bus.publish(execution_id, None, "WorkflowFailed", f"Workflow execution failed: {e}")
        finally:
            db.close()

    def _route_to_dlq(
        self, 
        db: Session, 
        task: Task, 
        exec_obj: WorkflowExecution, 
        reason: str, 
        stack_trace: str
    ) -> None:
        """
        Updates task and execution statuses to failed, and registers diagnostics logs in the DLQ.
        """
        task.status = "failed"
        task.error = reason
        exec_obj.status = "failed"
        exec_obj.completed_at = datetime.now(timezone.utc)
        
        dlq_entry = DeadLetterQueue(
            task_id=task.id,
            workflow_execution_id=exec_obj.id,
            failure_reason=reason,
            retry_count=task.retry_count + 1,
            stack_trace=stack_trace,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(dlq_entry)
        db.commit()

        event_bus.publish(
            exec_obj.id, 
            task.id, 
            "WorkflowFailed", 
            f"Task '{task.name}' failed. Moved to Dead Letter Queue (DLQ)."
        )

# Global WorkflowService instance
workflow_service = WorkflowService()
