from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class MCPTool(BaseModel):
    """
    Standard MCP representation of a tool.
    """
    name: str = Field(..., description="Unique tool name.")
    description: str = Field(..., description="Details about tool functionality.")
    inputSchema: Dict[str, Any] = Field(..., description="JSON Schema for input parameters.")


class JSONRPCRequest(BaseModel):
    """
    JSON-RPC 2.0 Request wrapper.
    """
    jsonrpc: str = Field("2.0", pattern="^2.0$")
    method: str = Field(..., description="RPC method name (e.g. 'tools/list', 'tools/call').")
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None


class JSONRPCResponse(BaseModel):
    """
    JSON-RPC 2.0 Response wrapper.
    """
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None
