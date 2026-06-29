import abc
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from ai.tools.base_tool import BaseTool


class AgentResponse(BaseModel):
    """
    Standardized response structure returned by all agents.
    """

    success: bool
    output: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAgent(abc.ABC):
    """
    Abstract Base Class for all cognitive AI agents in the ecosystem.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        system_prompt: str,
        available_tools: Optional[List[BaseTool]] = None,
        provider: Optional[Any] = None,
        memory: Optional[Any] = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.available_tools = available_tools or []
        self.provider = provider
        self.memory = memory

    @abc.abstractmethod
    def execute(
        self, input_text: str, context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Executes the agent's cognitive loops, calling LLM provider and tools.
        """
        pass

    def validate(self) -> bool:
        """
        Validates the configuration and status of the agent.
        """
        return bool(self.agent_id and self.name and self.system_prompt)

    def before_run(self, *args, **kwargs):
        """
        Lifecycle hook executed immediately before running the execution loop.
        """
        pass

    def after_run(self, response: AgentResponse) -> AgentResponse:
        """
        Lifecycle hook executed immediately after the execution loop for post-processing.
        """
        return response
