from ai.tools.base_tool import BaseTool
from ai.mcp.mcp_schema import MCPTool


class MCPAdapter:
    """
    Translates standard ecosystem BaseTool models into MCP tool definitions.
    """

    @staticmethod
    def to_mcp_tool(tool: BaseTool) -> MCPTool:
        """
        Adapts a BaseTool instance to the MCPTool model definition.
        """
        return MCPTool(
            name=tool.tool_id, description=tool.description, inputSchema=tool.parameters
        )
