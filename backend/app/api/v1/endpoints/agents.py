from typing import Any, Dict, List, Optional

from ai.core.agent_manager import agent_manager
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.schemas.response import APIResponse

router = APIRouter()


# Request schemas
class AgentChatRequest(BaseModel):
    message: str = Field(..., description="The input message for the agent.")
    session_id: Optional[str] = Field(
        None, description="Optional conversation session ID."
    )


class AgentToolRequest(BaseModel):
    tool_name: str = Field(..., description="The name of the tool/plugin to execute.")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Parameters for the tool execution."
    )


# Endpoints
@router.get("", response_model=APIResponse[List[Dict[str, Any]]])
def get_agents():
    """
    Retrieves all registered and enabled agents.
    """
    try:
        # Dynamically rediscover to catch new manifest modifications at runtime
        agent_manager.discover_agents()
        agents = agent_manager.list_agents()
        return APIResponse(
            success=True,
            data=agents,
            message="Successfully retrieved registered agents.",
        )
    except Exception as e:
        return APIResponse(
            success=False, error=str(e), message="Failed to list agents."
        )


@router.get("/{agent_name}", response_model=APIResponse[Dict[str, Any]])
def get_agent_by_name(agent_name: str):
    """
    Retrieves configuration and manifest details of a specific agent.
    """
    # Ensure discover is up to date
    agent_manager.discover_agents()
    agent = agent_manager.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found.")

    manifest = agent_manager.manifests.get(agent_name, {})
    # Build complete details
    details = {
        "id": agent.agent_id,
        "name": agent.name,
        "description": agent.description,
        "provider": agent.provider.__class__.__name__ if agent.provider else None,
        "model": manifest.get("model", "default"),
        "version": manifest.get("version", "1.0.0"),
        "tools": [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in agent.available_tools
        ],
    }
    return APIResponse(success=True, data=details)


@router.post("/{agent_name}/chat", response_model=APIResponse[Dict[str, Any]])
def chat_with_agent(agent_name: str, payload: AgentChatRequest):
    """
    Sends a message to the agent and returns the text response.
    """
    # Ensure discover is up to date
    agent_manager.discover_agents()
    agent = agent_manager.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found.")

    session_id = payload.session_id or "default_session"
    context = {"session_id": session_id}

    agent_res = agent_manager.execute_agent(
        agent_id=agent_name, input_text=payload.message, context=context
    )

    if not agent_res.success:
        return APIResponse(
            success=False,
            error=agent_res.error or "Unknown execution error.",
            message="Agent execution failed.",
        )

    return APIResponse(
        success=True,
        data={
            "output": agent_res.output,
            "session_id": session_id,
            "metadata": agent_res.metadata,
        },
        message="Agent response generated successfully.",
    )


@router.post("/{agent_name}/tools", response_model=APIResponse[Dict[str, Any]])
def run_agent_tool(agent_name: str, payload: AgentToolRequest):
    """
    Executes a specific tool loaded for the agent.
    """
    # Ensure discover is up to date
    agent_manager.discover_agents()
    agent = agent_manager.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found.")

    # Find tool
    target_tool = None
    for tool in agent.available_tools:
        if tool.name == payload.tool_name:
            target_tool = tool
            break

    if not target_tool:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{payload.tool_name}' not registered for Agent '{agent_name}'.",
        )

    try:
        result = target_tool.execute(**payload.arguments)
        return APIResponse(
            success=True,
            data={"result": result},
            message=f"Tool '{payload.tool_name}' executed successfully.",
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e),
            message=f"Failed to execute tool '{payload.tool_name}'.",
        )
