from app.core.logging.logger import logger


class WorkflowEngine:
    """
    Core orchestrator delegate. Forwards workflow pipeline executions
    to the centralized workflow service.
    """

    def execute_workflow(self, execution_id: int) -> None:
        """
        Launches the workflow loop execution.
        """
        logger.info(f"[WorkflowEngine] Dispatching run for execution {execution_id}")
        from app.services.workflow_service import workflow_service

        workflow_service.run_workflow_pipeline(execution_id)


# Global WorkflowEngine instance
workflow_engine = WorkflowEngine()
