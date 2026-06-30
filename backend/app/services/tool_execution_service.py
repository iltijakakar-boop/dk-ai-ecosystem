import json
import time
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.mcp_models import ToolDefinition, MCPToolExecutionLog, ToolExecution
from app.services.analytics_service import analytics_service


class ToolExecutionService:
    def execute_tool(
        self, db: Session, *, workspace_id: int, tool_id: int, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        tool = db.query(ToolDefinition).filter(ToolDefinition.id == tool_id, ToolDefinition.workspace_id == workspace_id).first()
        if not tool:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found.")

        start_time = time.time()
        status_flag = "completed"
        error_msg = None
        result = {}

        try:
            # Simulate execution depending on type
            if tool.execution_type == "native":
                result = {"output": f"Executed native tool {tool.name}", "args": arguments}
            elif tool.execution_type == "mcp":
                result = {"output": f"Executed remote MCP tool {tool.name}", "args": arguments}
            else:
                result = {"output": f"Executed API tool {tool.name}", "args": arguments}
        except Exception as e:
            status_flag = "failed"
            error_msg = str(e)
            result = {"error": error_msg}

        duration = (time.time() - start_time) * 1000.0

        # Create ToolExecution log
        log_entry = MCPToolExecutionLog(
            workspace_id=workspace_id,
            tool_name=tool.name,
            input_params=json.dumps(arguments),
            output_result=json.dumps(result) if status_flag == "completed" else None,
            error_message=error_msg,
            duration_ms=duration,
        )
        db.add(log_entry)
        db.commit()

        # Update aggregated analytics metrics
        analytics_service.record_tool_call(
            db,
            workspace_id=workspace_id,
            tool_name=tool.name,
            duration_ms=duration,
            is_error=(status_flag == "failed")
        )

        return result


tool_execution_service = ToolExecutionService()
