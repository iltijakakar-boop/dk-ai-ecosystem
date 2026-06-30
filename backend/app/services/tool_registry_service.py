import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.mcp_models import ToolDefinition, ToolVersion, ToolDependency


class ToolRegistryService:
    def register_tool(
        self,
        db: Session,
        *,
        workspace_id: int,
        name: str,
        description: Optional[str] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        execution_type: str,
        endpoint_url: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
    ) -> ToolDefinition:
        # Prevent duplicate active definition in same workspace
        tool = (
            db.query(ToolDefinition)
            .filter(ToolDefinition.workspace_id == workspace_id, ToolDefinition.name == name)
            .first()
        )
        schema_str = json.dumps(input_schema or {})

        if tool:
            tool.description = description
            tool.input_schema = schema_str
            tool.execution_type = execution_type
            tool.endpoint_url = endpoint_url
            db.commit()
        else:
            tool = ToolDefinition(
                workspace_id=workspace_id,
                name=name,
                description=description,
                input_schema=schema_str,
                execution_type=execution_type,
                endpoint_url=endpoint_url,
            )
            db.add(tool)
            db.commit()
            db.refresh(tool)

        # Track historical version
        latest = (
            db.query(ToolVersion)
            .filter(ToolVersion.tool_id == tool.id)
            .order_by(ToolVersion.version.desc())
            .first()
        )
        next_ver = (latest.version + 1) if latest else 1

        ver = ToolVersion(
            tool_id=tool.id,
            version=next_ver,
            input_schema=schema_str,
        )
        db.add(ver)

        # Save dependencies
        db.query(ToolDependency).filter(ToolDependency.tool_id == tool.id).delete()
        if dependencies:
            for dep in dependencies:
                db_dep = ToolDependency(tool_id=tool.id, dependency_tool_name=dep)
                db.add(db_dep)

        db.commit()
        db.refresh(tool)
        return tool

    def get_tools(self, db: Session, workspace_id: int) -> List[ToolDefinition]:
        return db.query(ToolDefinition).filter(ToolDefinition.workspace_id == workspace_id).all()

    def get_tool(self, db: Session, tool_id: int) -> Optional[ToolDefinition]:
        return db.query(ToolDefinition).filter(ToolDefinition.id == tool_id).first()


tool_registry_service = ToolRegistryService()
