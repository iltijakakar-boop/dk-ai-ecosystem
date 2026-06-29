from ai.core.base_agent import BaseAgent, AgentResponse
from typing import Dict, Any, Optional

class ChatAgent(BaseAgent):
    """
    General conversational agent.
    """
    def execute(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        session_id = (context or {}).get("session_id", "default_session")
        
        # Retrieve conversation history
        history = self.memory.get_history(session_id)
        history_str = ""
        for msg in history:
            history_str += f"{msg['role'].capitalize()}: {msg['content']}\n"
            
        # Format final prompt
        final_prompt = f"Conversation History:\n{history_str}\nUser: {input_text}\nAssistant:"
        
        try:
            output = self.provider.generate(final_prompt, system_prompt=self.system_prompt)
            # Save to conversation memory
            self.memory.add_message(session_id, "user", input_text)
            self.memory.add_message(session_id, "assistant", output)
            return AgentResponse(success=True, output=output)
        except Exception as e:
            return AgentResponse(success=False, output="", error=str(e))
