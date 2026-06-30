from sqlalchemy.orm import Session
from app.services.agent_builder_service import agent_builder_service


def test_agent_builder_lifecycle_and_compilation(db: Session):
    # 1. Create agent template
    template = agent_builder_service.create_template(
        db,
        workspace_id=1,
        name="Linter Assistant",
        description="Lints backend Python files",
        system_prompt="You are a senior python code reviewer.",
        model="gpt-4o",
        temperature=0.2,
        config_data={"memory_enabled": True, "tools": ["python_linter"]}
    )
    assert template.name == "Linter Assistant"
    assert template.temperature == 0.2

    # 2. Update agent template config (creates a new version)
    updated = agent_builder_service.update_template(
        db,
        template_id=template.id,
        system_prompt="Updated system prompt.",
        config_data={"memory_enabled": True, "tools": ["python_linter", "ruff"]}
    )
    assert updated.system_prompt == "Updated system prompt."

    # 3. Compile and register agent to core AgentRegistry
    registry_agent = agent_builder_service.compile_and_register_agent(db, template_id=template.id)
    assert registry_agent is not None
    assert registry_agent.name == "Linter Assistant"
    assert registry_agent.version == "1.2"  # Version 2 snapshot
