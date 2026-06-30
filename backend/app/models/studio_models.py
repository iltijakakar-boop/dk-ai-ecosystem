import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class AgentStudioProject(Base):
    """
    Groups visual canvases, templates, and deployments within a workspace.
    """
    __tablename__ = "agent_studio_projects"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class WorkflowCanvas(Base):
    """
    The root visual graph design schema for visual builders.
    """
    __tablename__ = "workflow_canvases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("agent_studio_projects.id"), nullable=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    definition = Column(Text, nullable=True, default="{}")  # Visual canvas JSON representation
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class WorkflowNode(Base):
    """
    Represents individual node elements on the visual canvas.
    """
    __tablename__ = "workflow_nodes"

    id = Column(Integer, primary_key=True, index=True)
    canvas_id = Column(Integer, ForeignKey("workflow_canvases.id", ondelete="CASCADE"), nullable=False)
    node_id = Column(String, nullable=False)  # React Flow node ID
    type = Column(String, nullable=False)  # agent, llm, prompt, tool, condition, loop, rag, etc.
    label = Column(String, nullable=False)
    config_data = Column(Text, nullable=True, default="{}")  # Node parameters JSON config
    pos_x = Column(Float, default=0.0, nullable=False)
    pos_y = Column(Float, default=0.0, nullable=False)


class WorkflowEdge(Base):
    """
    Represents directed links between visual node ports.
    """
    __tablename__ = "workflow_edges"

    id = Column(Integer, primary_key=True, index=True)
    canvas_id = Column(Integer, ForeignKey("workflow_canvases.id", ondelete="CASCADE"), nullable=False)
    edge_id = Column(String, nullable=False)
    source_node = Column(String, nullable=False)
    target_node = Column(String, nullable=False)
    source_handle = Column(String, nullable=True)
    target_handle = Column(String, nullable=True)


class PromptTemplate(Base):
    """
    Visual prompt builder metadata template.
    """
    __tablename__ = "studio_prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    template_text = Column(Text, nullable=False)
    variables = Column(String, nullable=True, default="[]")  # JSON string of variable names


class PromptVersion(Base):
    """
    Immutable snapshots of visual prompts history.
    """
    __tablename__ = "studio_prompt_versions"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("studio_prompt_templates.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    template_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class AgentTemplate(Base):
    """
    Saved custom blueprints representing visual agent definitions.
    """
    __tablename__ = "studio_agent_templates"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    model = Column(String, nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    config_data = Column(Text, nullable=True, default="{}")  # Memory, tools configuration


class AgentVersion(Base):
    """
    Visual agent specifications version history snapshots.
    """
    __tablename__ = "studio_agent_versions"

    id = Column(Integer, primary_key=True, index=True)
    agent_template_id = Column(Integer, ForeignKey("studio_agent_templates.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    system_prompt = Column(Text, nullable=True)
    config_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class Pipeline(Base):
    """
    RAG, ETL, or Data visual processing flow pipelines.
    """
    __tablename__ = "studio_pipelines"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String, nullable=False)  # RAG, Data Processing, ETL, etc.
    definition = Column(Text, nullable=True, default="{}")  # visual pipeline graph definition


class PipelineVersion(Base):
    """
    Visual pipeline layout blueprints versions.
    """
    __tablename__ = "studio_pipeline_versions"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("studio_pipelines.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    definition = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class Deployment(Base):
    """
    Visual builds deployed to staging or production runtime servers.
    """
    __tablename__ = "studio_deployments"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    canvas_id = Column(Integer, ForeignKey("workflow_canvases.id", ondelete="SET NULL"), nullable=True)
    agent_template_id = Column(Integer, ForeignKey("studio_agent_templates.id", ondelete="SET NULL"), nullable=True)
    pipeline_id = Column(Integer, ForeignKey("studio_pipelines.id", ondelete="SET NULL"), nullable=True)
    version = Column(Integer, nullable=False)
    environment = Column(String, default="Testing", nullable=False)  # Draft, Testing, Staging, Production
    status = Column(String, default="Active", nullable=False)  # Active, RolledBack, Archived
    created_at = Column(DateTime, default=func.now(), nullable=False)


class DeploymentHistory(Base):
    """
    Visual deployments audit log.
    """
    __tablename__ = "studio_deployment_history"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("studio_deployments.id", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False)  # deploy, rollback, deactivate
    details = Column(Text, nullable=True)
    performed_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class ExecutionSession(Base):
    """
    Execution run reference tracking general studio run lifecycle.
    """
    __tablename__ = "studio_execution_sessions"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    entity_type = Column(String, nullable=False)  # workflow, agent, pipeline
    entity_id = Column(Integer, nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending, running, completed, failed
    inputs = Column(Text, nullable=True, default="{}")
    outputs = Column(Text, nullable=True, default="{}")
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)


class DebugSession(Base):
    """
    Debug context session tracing variable snapshots and execution logs node by node.
    """
    __tablename__ = "studio_debug_sessions"

    id = Column(Integer, primary_key=True, index=True)
    execution_session_id = Column(Integer, ForeignKey("studio_execution_sessions.id", ondelete="CASCADE"), nullable=True)
    workspace_id = Column(Integer, index=True, nullable=False)
    status = Column(String, default="running", nullable=False)  # running, completed, failed
    current_step = Column(String, nullable=True)
    logs = Column(Text, nullable=True, default="[]")  # JSON array of steps debug messages
    variables_state = Column(Text, nullable=True, default="{}")  # JSON snapshot of visual variables
    created_at = Column(DateTime, default=func.now(), nullable=False)


class CanvasLayout(Base):
    """
    Canvas options, workspace configs, zoom, and theme settings.
    """
    __tablename__ = "studio_canvas_layouts"

    id = Column(Integer, primary_key=True, index=True)
    canvas_id = Column(Integer, ForeignKey("workflow_canvases.id", ondelete="CASCADE"), nullable=False)
    grid_size = Column(Integer, default=15, nullable=False)
    zoom = Column(Float, default=1.0, nullable=False)
    pan_x = Column(Float, default=0.0, nullable=False)
    pan_y = Column(Float, default=0.0, nullable=False)
    theme = Column(String, default="dark", nullable=False)


class WorkflowVariable(Base):
    """
    User variables defined global in visual canvas scope.
    """
    __tablename__ = "studio_workflow_variables"

    id = Column(Integer, primary_key=True, index=True)
    canvas_id = Column(Integer, ForeignKey("workflow_canvases.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, default="string", nullable=False)  # string, integer, float, boolean, json
    default_value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)


class WorkflowParameter(Base):
    """
    Trigger arguments accepted at workflow execution entrance.
    """
    __tablename__ = "studio_workflow_parameters"

    id = Column(Integer, primary_key=True, index=True)
    canvas_id = Column(Integer, ForeignKey("workflow_canvases.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    required = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)


class WorkflowOutput(Base):
    """
    Variables or Node outputs mapping to final workflow results.
    """
    __tablename__ = "studio_workflow_outputs"

    id = Column(Integer, primary_key=True, index=True)
    canvas_id = Column(Integer, ForeignKey("workflow_canvases.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    source_node = Column(String, nullable=False)
    source_property = Column(String, nullable=False)


class WorkflowTrigger(Base):
    """
    Visual flow trigger definitions mapping to external webhooks, etc.
    """
    __tablename__ = "studio_workflow_triggers"

    id = Column(Integer, primary_key=True, index=True)
    canvas_id = Column(Integer, ForeignKey("workflow_canvases.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # webhook, schedule, event_signal
    config_data = Column(Text, nullable=True, default="{}")


class WorkflowSchedule(Base):
    """
    Scheduler configuration for time-based triggers.
    """
    __tablename__ = "studio_workflow_schedules"

    id = Column(Integer, primary_key=True, index=True)
    canvas_id = Column(Integer, ForeignKey("workflow_canvases.id", ondelete="CASCADE"), nullable=False)
    cron_expression = Column(String, nullable=True)
    interval_seconds = Column(Integer, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)


class StudioWorkflowExecution(Base):
    """
    Reference of a specific execution run of a visual canvas.
    """
    __tablename__ = "studio_workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    canvas_id = Column(Integer, ForeignKey("workflow_canvases.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending, running, completed, failed
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)


class StudioWorkflowLog(Base):
    """
    Step-by-step logs tracking task execution per visual node.
    """
    __tablename__ = "studio_workflow_logs"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("studio_workflow_executions.id", ondelete="CASCADE"), nullable=False)
    node_id = Column(String, nullable=True)
    log_level = Column(String, default="INFO", nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
