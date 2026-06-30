from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.mcp_models import RemoteEndpoint


class RemoteExecutionService:
    def register_remote_endpoint(
        self, db: Session, *, workspace_id: int, url: str, auth_header: Optional[str] = None
    ) -> RemoteEndpoint:
        endpoint = (
            db.query(RemoteEndpoint)
            .filter(RemoteEndpoint.workspace_id == workspace_id, RemoteEndpoint.url == url)
            .first()
        )
        if endpoint:
            endpoint.auth_header = auth_header
        else:
            endpoint = RemoteEndpoint(
                workspace_id=workspace_id,
                url=url,
                auth_header=auth_header,
            )
            db.add(endpoint)
        db.commit()
        db.refresh(endpoint)
        return endpoint

    def execute_remote_tool(
        self, db: Session, *, workspace_id: int, endpoint_id: int, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        endpoint = (
            db.query(RemoteEndpoint)
            .filter(RemoteEndpoint.id == endpoint_id, RemoteEndpoint.workspace_id == workspace_id)
            .first()
        )
        if not endpoint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Remote endpoint configuration not found."
            )

        # In production, dispatch via httpx or other transports.
        # Simple mock compliant response for execution:
        return {
            "result": f"Remote tool {tool_name} executed successfully.",
            "echo_args": arguments,
            "origin": endpoint.url,
            "status": "success",
        }


remote_execution_service = RemoteExecutionService()
