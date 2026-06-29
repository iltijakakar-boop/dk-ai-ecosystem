from typing import List, Dict, Any, Optional
from app.core.logging.logger import logger

class AgentOrchestrator:
    """
    Central transit hub matching tasks to agents based on capability descriptors,
    routing messaging events, and preventing direct agent-to-agent talk.
    """
    
    def __init__(self):
        # Seeded capabilities mapping for built-in ecosystem agents
        self.agent_capabilities: Dict[str, List[str]] = {
            "chat_agent": ["chat", "planning"],
            "coding_agent": ["coding", "analysis"],
            "research_agent": ["research", "analysis"],
            "document_agent": ["document", "analysis"]
        }

    def register_agent_capabilities(self, agent_id: str, capabilities: List[str]) -> None:
        """
        Registers capability tags for a specific agent.
        """
        self.agent_capabilities[agent_id] = capabilities
        logger.info(f"Registered capabilities for agent {agent_id}: {capabilities}")

    def find_agent_by_capability(self, required_capability: str) -> Optional[str]:
        """
        Returns the first registered agent ID matching the required capability tag.
        """
        for agent_id, caps in self.agent_capabilities.items():
            if required_capability in caps:
                return agent_id
        return None

    def route_agent_message(
        self, 
        from_agent_id: str, 
        to_agent_id: str, 
        message_content: str
    ) -> str:
        """
        Routes messaging logs between collaborating agents. Enforces orchestration bounds.
        """
        logger.info(f"[Orchestrator Transit] Routing message from {from_agent_id} to {to_agent_id}")
        
        # In a real environment, we'd invoke the target agent's execute() method here.
        # For simulation, we return a mock response that acknowledges routing context.
        return f"Acknowledged message from {from_agent_id} via Orchestrator: '{message_content}'"

# Global AgentOrchestrator instance
agent_orchestrator = AgentOrchestrator()
