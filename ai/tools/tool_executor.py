import time
import concurrent.futures
import json
from typing import Dict, Any, Optional
from app.config.settings import settings
from app.core.logging import logger
from ai.tools.tool_registry import tool_registry
from ai.tools.base_tool import BaseTool


class ToolExecutor:
    """
    Executes tools safely, verifying permissions and schemas,
    enforcing timeouts, and logging execution statistics to the database.
    """

    def check_permissions(
        self, tool: BaseTool, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Validates execution permissions and allow/deny lists.
        """
        # Allow/Deny List checks from configurations
        tool_allow_list = getattr(settings, "TOOL_ALLOW_LIST", [])
        tool_deny_list = getattr(settings, "TOOL_DENY_LIST", [])

        if tool_deny_list and tool.tool_id in tool_deny_list:
            return False
        if tool_allow_list and tool.tool_id not in tool_allow_list:
            return False

        # Validate context permissions
        if not tool.permissions:
            return True

        allowed_permissions = (context or {}).get("permissions", [])
        for perm in tool.permissions:
            if perm not in allowed_permissions:
                logger.warning(
                    f"Permission denied: Tool '{tool.tool_id}' requires '{perm}'."
                )
                return False

        return True

    def execute_tool(
        self,
        tool_id: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes a registered tool with timeout and logs execution.
        """
        tool = tool_registry.get_tool(tool_id)
        if not tool:
            return {
                "success": False,
                "result": None,
                "error": f"Tool '{tool_id}' not found or is disabled.",
            }

        # 1. Permission checks
        if not self.check_permissions(tool, context):
            return {
                "success": False,
                "result": None,
                "error": f"Permission denied for tool '{tool_id}'.",
            }

        # 2. Schema Parameter validation
        try:
            tool.validate(arguments)
        except (ValueError, TypeError) as ve:
            return {
                "success": False,
                "result": None,
                "error": f"Parameter validation error: {str(ve)}",
            }

        # Lifecycle hooks and Execution with Timeout
        success = False
        error_msg = None
        result = None
        start_time = time.perf_counter()

        try:
            # Hooks
            tool.before_execute(arguments, context=context)

            # Execute with timeout wrapper
            timeout_limit = tool.timeout or getattr(settings, "MAX_TOOL_TIMEOUT", 5)

            # Use ThreadPoolExecutor to enforce timeouts
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(tool.execute, **arguments)
                try:
                    result = future.result(timeout=timeout_limit)
                    result = tool.after_execute(result)
                    success = True
                except concurrent.futures.TimeoutError:
                    raise TimeoutError(
                        f"Tool execution exceeded timeout of {timeout_limit} seconds."
                    )

        except Exception as ex:
            error_msg = f"{ex.__class__.__name__}: {str(ex)}"
            logger.exception(f"Error during execution of tool {tool_id}:")
        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000.0

        # 3. Log to database
        self._write_execution_log(
            tool_id=tool_id,
            arguments=arguments,
            context=context,
            duration_ms=duration_ms,
            success=success,
            result=result,
            error_msg=error_msg,
        )

        if not success:
            return {
                "success": False,
                "result": None,
                "error": error_msg or "Unknown execution failure.",
            }

        return {"success": True, "result": result, "error": None}

    def _write_execution_log(
        self,
        tool_id: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        duration_ms: float,
        success: bool,
        result: Any,
        error_msg: Optional[str],
    ) -> None:
        """
        Commits execution results and timing to database logs.
        """
        try:
            from app.db.session import SessionLocal
            from app.models.tool_model import ToolExecutionLog

            db = SessionLocal()
            try:
                log_entry = ToolExecutionLog(
                    session_id=(context or {}).get("session_id"),
                    user_id=(context or {}).get("user_id"),
                    agent_id=(context or {}).get("agent_id"),
                    tool_id=tool_id,
                    duration_ms=duration_ms,
                    status="success" if success else "error",
                    input=json.dumps(arguments),
                    output=json.dumps(result) if success else None,
                    error=error_msg,
                )
                db.add(log_entry)
                db.commit()
            except Exception as e:
                logger.error(f"Failed to record ToolExecutionLog in database: {e}")
                db.rollback()
            finally:
                db.close()
        except Exception as e:
            logger.error(
                f"Database session not available for ToolExecutor logging: {e}"
            )


# Global Executor instance
tool_executor = ToolExecutor()
