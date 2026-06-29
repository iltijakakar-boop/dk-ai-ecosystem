# Import all the models so that Base has them registered before migrating
from app.db.session import Base
from app.models.user import User, UserRole  # noqa
from app.models.audit_log import AuditLog  # noqa
from app.models.agent import AgentRegistry  # noqa
from app.models.tool_model import Tool, Plugin, ToolExecutionLog  # noqa
from app.models.monitoring_model import SystemMetric, ExecutionMetric  # noqa



