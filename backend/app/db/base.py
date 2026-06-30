# Import all the models so that Base has them registered before migrating
from app.db.session import Base  # noqa
from app.models.user import User, UserRole  # noqa
from app.models.audit_log import AuditLog  # noqa
from app.models.agent import AgentRegistry  # noqa
from app.models.tool_model import Tool, Plugin, ToolExecutionLog  # noqa
from app.models.monitoring_model import SystemMetric, ExecutionMetric  # noqa
from app.models.document import Document  # noqa
from app.models.document_chunk import DocumentChunk  # noqa
from app.models.vector_embedding import VectorEmbedding  # noqa
from app.models.conversation import Conversation  # noqa
from app.models.message import Message  # noqa
from app.models.memory_entry import MemoryEntry  # noqa
from app.models.knowledge_collection import KnowledgeCollection  # noqa
from app.models.automation import AutomationJob, JobExecution, JobExecutionLog, Notification  # fmt: skip # noqa
