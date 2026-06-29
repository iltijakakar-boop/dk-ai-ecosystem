import os

from ai.core.agent_manager import agent_manager
from ai.core.memory_manager import (
    ConversationMemory,
    LongTermMemory,
    SessionMemory,
    VectorMemory,
)
from ai.core.provider_manager import provider_manager
from fastapi.testclient import TestClient


def test_agent_registration():
    """Tests dynamic discovery and listing of agents."""
    agent_manager.discover_agents()
    agents = agent_manager.list_agents()

    agent_ids = [a["id"] for a in agents]
    assert "chat_agent" in agent_ids
    assert "coding_agent" in agent_ids
    assert "research_agent" in agent_ids
    assert "document_agent" in agent_ids


def test_agent_execution_chat_agent():
    """Tests executing chat_agent logic."""
    agent_manager.discover_agents()

    res = agent_manager.execute_agent(
        "chat_agent", "Hello ecosystem!", context={"session_id": "test_session_chat"}
    )
    assert res.success is True
    assert len(res.output) > 0
    assert "Mock Response" in res.output or "ecosystem" in res.output


def test_provider_switching():
    """Tests resolving different providers dynamically."""
    p_gemini = provider_manager.get_provider("gemini")
    assert p_gemini.__class__.__name__ == "GeminiProvider"

    p_openai = provider_manager.get_provider("openai")
    assert p_openai.__class__.__name__ == "OpenAIProvider"

    p_anthropic = provider_manager.get_provider("anthropic")
    assert p_anthropic.__class__.__name__ == "AnthropicProvider"

    p_ollama = provider_manager.get_provider("ollama")
    assert p_ollama.__class__.__name__ == "OllamaProvider"

    p_openrouter = provider_manager.get_provider("openrouter")
    assert p_openrouter.__class__.__name__ == "OpenRouterProvider"


def test_tool_loading_and_execution():
    """Tests registration and execution of agent tools."""
    agent_manager.discover_agents()
    agent = agent_manager.get_agent("coding_agent")
    assert agent is not None

    # Check that code_linter tool is present
    tool_names = [t.name for t in agent.available_tools]
    assert "code_linter" in tool_names

    # Run the linter tool
    linter_tool = next(t for t in agent.available_tools if t.name == "code_linter")

    # Valid syntax
    val_res = linter_tool.execute(code="def add(a, b):\n    return a + b")
    assert val_res["valid"] is True

    # Invalid syntax
    inval_res = linter_tool.execute(code="def add(a, b)\n    return a + b")
    assert inval_res["valid"] is False
    assert "SyntaxError" in inval_res["error"]


def test_memory_systems():
    """Tests all four memory systems (Session, Conversation, LongTerm, Vector)."""
    # 1. Session Memory
    sess_mem = SessionMemory()
    sess_mem.set("session_1", "step", 2)
    assert sess_mem.get("session_1", "step") == 2
    sess_mem.clear("session_1")
    assert sess_mem.get("session_1", "step") is None

    # 2. Conversation Memory
    conv_mem = ConversationMemory()
    conv_mem.add_message("session_2", "user", "ping")
    conv_mem.add_message("session_2", "assistant", "pong")
    history = conv_mem.get_history("session_2")
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["content"] == "pong"

    # 3. Long Term Memory
    lt_mem = LongTermMemory(storage_path="database/test_long_term_memory.json")
    lt_mem.add_message("session_3", "user", "long-term fact")
    assert len(lt_mem.get_history("session_3")) == 1
    assert lt_mem.get_history("session_3")[0]["content"] == "long-term fact"

    # Clean up test database file
    lt_mem.clear("session_3")
    if os.path.exists("database/test_long_term_memory.json"):
        try:
            os.remove("database/test_long_term_memory.json")
        except Exception:
            pass

    # 4. Vector Memory (Placeholder mock testing)
    vec_mem = VectorMemory()
    vec_mem.add_embedding("session_4", "Important coding guidelines and patterns.")
    matches = vec_mem.search("session_4", "guidelines")
    assert len(matches) == 1
    assert "guidelines" in matches[0]["text"]


def test_api_endpoints(client: TestClient):
    """Tests GET and POST API endpoints of agents using the TestClient."""
    # 1. GET /api/v1/agents
    res_list = client.get("/api/v1/agents")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["success"] is True
    agent_ids = [a["id"] for a in list_data["data"]]
    assert "chat_agent" in agent_ids

    # 2. GET /api/v1/agents/{agent_name}
    res_detail = client.get("/api/v1/agents/chat_agent")
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert detail_data["success"] is True
    assert detail_data["data"]["id"] == "chat_agent"

    # 3. POST /api/v1/agents/{agent_name}/chat
    res_chat = client.post(
        "/api/v1/agents/chat_agent/chat",
        json={"message": "hello agent test", "session_id": "pytest_session"},
    )
    assert res_chat.status_code == 200
    chat_data = res_chat.json()
    assert chat_data["success"] is True
    assert "output" in chat_data["data"]

    # 4. POST /api/v1/agents/{agent_name}/tools
    res_tool = client.post(
        "/api/v1/agents/coding_agent/tools",
        json={
            "tool_name": "code_linter",
            "arguments": {"code": "print('lint testing')"},
        },
    )
    assert res_tool.status_code == 200
    tool_data = res_tool.json()
    assert tool_data["success"] is True
    assert tool_data["data"]["result"]["valid"] is True


def test_agent_registry_database_persistence(db):
    """Tests that AgentRegistry model persists dynamic agents in the database."""
    from app.models.agent import AgentRegistry

    # Trigger discover, which executes the synchronization query
    agent_manager.discover_agents()

    # Query database directly using the db session fixture
    db_agents = db.query(AgentRegistry).all()
    assert len(db_agents) >= 4

    chat_db_agent = (
        db.query(AgentRegistry).filter(AgentRegistry.id == "chat_agent").first()
    )
    assert chat_db_agent is not None
    assert chat_db_agent.name == "Chat Agent"
    assert chat_db_agent.status == "active"
    assert chat_db_agent.provider == "gemini"
    assert chat_db_agent.created_at is not None
    assert chat_db_agent.updated_at is not None
