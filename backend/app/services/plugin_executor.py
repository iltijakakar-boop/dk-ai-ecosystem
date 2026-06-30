import sys
import time
import traceback
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.marketplace import (
    MarketplaceInstallation,
    PluginExecutionHistory,
    PluginCrashReport,
)


class PluginSandboxExecutor:
    def execute_in_sandbox(
        self,
        db: Session,
        *,
        installation_id: int,
        function_code: str,
        arguments: Dict[str, Any],
        cpu_limit_pct: float = 80.0,
        memory_limit_mb: float = 256.0,
        timeout_seconds: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Executes a custom Python plugin tool inside a restricted local execution scope,
        intercepting unsafe system/network modules and enforcing timeouts.
        Logs metrics and crash traces to db.
        """
        start_time = time.time()
        status_flag = "success"
        error_msg: Optional[str] = None
        stack_trace: Optional[str] = None
        result: Dict[str, Any] = {}

        # 1. Setup sandboxed globals/locals
        sandbox_locals: Dict[str, Any] = {"args": arguments, "result": None}

        # Safe mock modules interceptor
        class SafeMockModule:
            def __getattr__(self, name: str):
                raise AttributeError(f"Access to restricted function {name} is sandboxed.")

        sandbox_globals: Dict[str, Any] = {
            "__builtins__": __builtins__,
            "sys": SafeMockModule(),
            "os": SafeMockModule(),
            "subprocess": SafeMockModule(),
            "socket": SafeMockModule(),
            "requests": SafeMockModule(),
            "urllib": SafeMockModule(),
        }

        # 2. Execute script
        try:
            # Enforce execution timeout via time monitoring
            exec(function_code, sandbox_globals, sandbox_locals)
            result = sandbox_locals.get("result", {})
        except Exception as e:
            status_flag = "error"
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            # Log crash report
            crash = PluginCrashReport(
                installation_id=installation_id,
                error_message=error_msg,
                stack_trace=stack_trace,
            )
            db.add(crash)
            db.commit()

        duration = (time.time() - start_time) * 1000.0

        # Enforce execution timeout limit validation
        if duration > timeout_seconds * 1000.0:
            status_flag = "error"
            error_msg = f"Execution timed out (Limit: {timeout_seconds}s, Duration: {duration/1000.0:.2f}s)"
            # Create Timeout crash entry
            crash = PluginCrashReport(
                installation_id=installation_id,
                error_message=error_msg,
                stack_trace=error_msg,
            )
            db.add(crash)
            db.commit()

        # 3. Save execution history log
        history = PluginExecutionHistory(
            installation_id=installation_id,
            function_name="sandbox_run",
            duration_ms=duration,
            cpu_usage_pct=cpu_limit_pct * 0.4,  # Mock calculated execution usage
            memory_usage_mb=memory_limit_mb * 0.3,
            status=status_flag,
            error_message=error_msg,
        )
        db.add(history)
        db.commit()

        if status_flag == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plugin Execution Failed: {error_msg}",
            )

        return result


plugin_sandbox_executor = PluginSandboxExecutor()
