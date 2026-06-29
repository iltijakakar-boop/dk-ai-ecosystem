import os
import json
import importlib
import sys
from typing import Dict, Any, List, Optional
from app.config.settings import settings
from app.core.logging import logger
from ai.core.base_agent import BaseAgent, AgentResponse
from ai.core.provider_manager import provider_manager
from ai.core.memory_manager import ConversationMemory
from ai.tools.base_tool import BaseTool

class AgentManager:
    """
    Registry and lifecycle orchestrator for dynamically scanning, loading,
    and executing cognitive agents.
    """
    def __init__(self, agents_dir: Optional[str] = None):
        if agents_dir is None:
            # Locate agent folder in project root workspace
            # project root is 3 levels up from this file or absolute path
            # c:\Projects\dk-ai-ecosystem\agents
            self.agents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "agents"))
        else:
            self.agents_dir = os.path.abspath(agents_dir)
            
        self.agents: Dict[str, BaseAgent] = {}
        self.manifests: Dict[str, dict] = {}

    def discover_agents(self) -> None:
        """
        Scans agents directory, reads manifests, loads python classes, and initializes instances.
        """
        logger.info(f"Scanning for agents in: {self.agents_dir}")
        if not os.path.exists(self.agents_dir):
            logger.warning(f"Agents directory {self.agents_dir} does not exist.")
            return

        # Ensure the agents folder parent directory is in sys.path
        parent_dir = os.path.dirname(self.agents_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        for entry in os.scandir(self.agents_dir):
            if entry.is_dir() and not entry.name.startswith((".", "__")):
                manifest_path = os.path.join(entry.path, "manifest.json")
                agent_file = os.path.join(entry.path, "agent.py")
                
                if os.path.exists(manifest_path) and os.path.exists(agent_file):
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            manifest = json.load(f)
                            
                        agent_id = manifest.get("id")
                        if not agent_id:
                            logger.error(f"Manifest in {entry.name} missing 'id' key.")
                            continue
                            
                        if not manifest.get("enabled", True):
                            logger.info(f"Agent {agent_id} is disabled in manifest.")
                            continue
                        
                        # Dynamically load the agent's python module
                        module_name = f"agents.{entry.name}.agent"
                        # Reload or import module
                        if module_name in sys.modules:
                            module = importlib.reload(sys.modules[module_name])
                        else:
                            module = importlib.import_module(module_name)
                        
                        # Search for a class inheriting from BaseAgent
                        agent_class = None
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if (
                                isinstance(attr, type)
                                and issubclass(attr, BaseAgent)
                                and attr is not BaseAgent
                            ):
                                agent_class = attr
                                break
                                
                        if not agent_class:
                            logger.error(f"No BaseAgent subclass found in {agent_file}")
                            continue

                        # Load system prompt
                        prompt_path = os.path.join(entry.path, "prompt.md")
                        system_prompt = ""
                        if os.path.exists(prompt_path):
                            with open(prompt_path, "r", encoding="utf-8") as pf:
                                system_prompt = pf.read()
                        
                        # Load provider
                        provider_name = manifest.get("provider") or settings.AI_PROVIDER
                        provider_model = manifest.get("model") or settings.DEFAULT_MODEL
                        provider = provider_manager.get_provider(provider_name, model_name=provider_model)
                        
                        # Load tools if tools.py exists
                        tools_file = os.path.join(entry.path, "tools.py")
                        available_tools = []
                        if os.path.exists(tools_file):
                            tools_module_name = f"agents.{entry.name}.tools"
                            try:
                                if tools_module_name in sys.modules:
                                    tools_module = importlib.reload(sys.modules[tools_module_name])
                                else:
                                    tools_module = importlib.import_module(tools_module_name)
                                    
                                for t_attr_name in dir(tools_module):
                                    t_attr = getattr(tools_module, t_attr_name)
                                    if (
                                        isinstance(t_attr, type)
                                        and issubclass(t_attr, BaseTool)
                                        and t_attr is not BaseTool
                                    ):
                                        available_tools.append(t_attr())
                            except Exception as te:
                                logger.exception(f"Failed to load tools module for {agent_id}:")
                        
                        # Create unique conversation memory instance
                        memory = ConversationMemory()
                        
                        # Initialize agent
                        agent_instance = agent_class(
                            agent_id=agent_id,
                            name=manifest.get("name", agent_id),
                            description=manifest.get("description", ""),
                            system_prompt=system_prompt,
                            available_tools=available_tools,
                            provider=provider,
                            memory=memory
                        )
                        
                        # Validate agent
                        if agent_instance.validate():
                            self.agents[agent_id] = agent_instance
                            self.manifests[agent_id] = manifest
                            logger.info(f"Agent {agent_id} loaded successfully.")
                        else:
                            logger.error(f"Agent {agent_id} failed validation checks.")
                            
                    except Exception as ex:
                        logger.exception(f"Error loading agent from directory {entry.name}:")

        # Sync discovered agents with AgentRegistry database table
        try:
            from app.db.session import SessionLocal
            from app.models.agent import AgentRegistry
            from sqlalchemy.sql import func
            
            db = SessionLocal()
            try:
                for agent_id, agent_instance in self.agents.items():
                    manifest = self.manifests.get(agent_id, {})
                    db_agent = db.query(AgentRegistry).filter(AgentRegistry.id == agent_id).first()
                    if db_agent:
                        db_agent.name = agent_instance.name
                        db_agent.version = manifest.get("version", "1.0.0")
                        db_agent.provider = manifest.get("provider") or settings.AI_PROVIDER
                        db_agent.status = "active" if manifest.get("enabled", True) else "disabled"
                        db_agent.updated_at = func.now()
                    else:
                        db_agent = AgentRegistry(
                            id=agent_id,
                            name=agent_instance.name,
                            version=manifest.get("version", "1.0.0"),
                            status="active" if manifest.get("enabled", True) else "disabled",
                            provider=manifest.get("provider") or settings.AI_PROVIDER
                        )
                        db.add(db_agent)
                db.commit()
                logger.info("Synchronized dynamic agents with the AgentRegistry database table.")
            except Exception as dbe:
                logger.warning(f"Could not sync agents with AgentRegistry: {dbe}")
                db.rollback()
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Database session not available for AgentRegistry sync: {e}")

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Gets a loaded agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        """Returns metadata for all registered and active agents."""
        return [
            {
                "id": agent.agent_id,
                "name": agent.name,
                "description": agent.description,
                "provider": agent.provider.__class__.__name__ if agent.provider else None,
                "tools": [t.name for t in agent.available_tools],
                "version": self.manifests.get(agent.agent_id, {}).get("version", "1.0.0")
            }
            for agent in self.agents.values()
        ]

    def execute_agent(
        self, agent_id: str, input_text: str, context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Executes the requested agent with lifecycle hooks.
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return AgentResponse(
                success=False,
                output="",
                error=f"Agent '{agent_id}' is not loaded or does not exist."
            )
            
        try:
            agent.before_run()
            response = agent.execute(input_text, context=context)
            response = agent.after_run(response)
            return response
        except Exception as e:
            logger.exception(f"Exception during execution of agent {agent_id}:")
            return AgentResponse(
                success=False,
                output="",
                error=f"Execution error: {str(e)}"
            )

# Global Agent Manager instance
agent_manager = AgentManager()
