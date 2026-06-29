# Backend - DK AI Ecosystem

This directory houses the backend server application for the DK AI Ecosystem, built with **FastAPI**, **SQLAlchemy 2.x**, **Pydantic v2**, **PostgreSQL**, and **Redis**.

## Directory Layout

```
backend/
├── app/
│   ├── api/                  # API routing layer
│   │   ├── router.py         # Main API router (aggregates versions)
│   │   └── v1/               # API version 1 routers
│   │       ├── router.py     # Version 1 router
│   │       └── endpoints/    # Route handlers/controllers
│   │               ├── admin.py  # Dashboard statistics and audit logs endpoints
│   │               ├── auth.py   # Registration, Login, Token Refresh, Logout endpoints
│   │               ├── health.py # Health status checker endpoint
│   │               └── users.py  # User profile and admin CRUD management endpoints
│   ├── core/                 # Core utilities
│   │   ├── exceptions.py     # Custom application exceptions
│   │   ├── lifespan.py       # Startup and shutdown resource setup
│   │   ├── logging.py        # Structured logging configuration
│   │   └── security.py       # Password hashing & token controls
│   ├── config/               # Settings management
│   │   ├── settings.py       # Base settings configuration
│   │   ├── development.py    # Dev settings overrides
│   │   ├── production.py     # Prod settings overrides
│   │   └── testing.py        # Test settings overrides
│   ├── db/                   # Database files
│   │   ├── base.py           # Model auto-discovery
│   │   ├── init_db.py        # Db initialization / seeding
│   │   ├── migrations.py     # Programmatic migration triggers
│   │   └── session.py        # SQLAlchemy connections
│   ├── middleware/           # Custom middlewares
│   ├── models/               # SQLAlchemy Database models
│   │   ├── user.py           # User model and UserRole enums definition
│   │   └── audit_log.py      # Database AuditLog model definition
│   ├── repositories/         # Repository patterns for queries
│   │   ├── user.py           # User CRUD repository definitions
│   │   └── audit_log.py      # Audit log CRUD repository definitions
│   ├── schemas/              # Pydantic schemas
│   │   ├── response.py       # Standard APIResponse schemas
│   │   ├── token.py          # Token payload and refresh schemas
│   │   ├── user.py           # User creation, update, and response validation schemas
│   │   └── audit_log.py      # Audit log response validation schemas
│   ├── services/             # Business logic services
│   │   └── user_service.py   # User management and authorization logic
│   ├── utils/                # Helper utilities
│   └── dependencies/         # FastAPI Dependency Injection
│       ├── auth.py           # User auth and Role checks dependencies
│       ├── db.py             # Database session dependency
│       ├── rate_limit.py     # Redis login rate limiting dependency
│       └── redis.py          # Redis connection dependency
│
├── tests/                    # Pytest test cases and conftest setup
│   ├── test_auth.py          # Auth validation, login, and RBAC tests
│   ├── test_main.py          # Startup and health check tests
│   └── test_user_admin.py    # User CRUD, role hierarchy, and soft delete tests
├── migrations/               # Alembic database schema migrations
├── requirements/             # Partitioned Python requirements (base, dev, prod)
├── Dockerfile                # Multi-stage Docker packaging configuration
├── docker-compose.yml        # Development environment runner (app + postgres + redis)
├── pyproject.toml            # Python tool configurations (black, ruff, pytest)
├── .env.example              # Sample environment configuration template
└── README.md                 # Project developer notes
```

## Security & User Management Features

1. **Standard Response Wrapper**:
   All endpoints and global exception handlers conform to the standard API response structure:
   ```json
   {
     "success": true,
     "data": { ... } or null,
     "message": "message string" or null,
     "error": "error description" or null
   }
   ```
2. **User management CRUD & RBAC**:
   - Soft Deletes: Flagging target records using `is_deleted`, `deleted_at`, and `deleted_by` attributes.
   - Role Hierarchy Checks: Validating that higher role accounts cannot be deactivated, deleted, or updated by users with lower permissions (order: `SUPER_ADMIN` > `ADMIN` > `USER`).
3. **Audit Log Trail**:
   - Administrative changes (activations, role edits, soft deletions, password changes) are recorded inside the database under the `AuditLog` table, capturing `resource`, `ip_address`, and `user_agent`.
4. **Pagination formats**:
   - Standard paginated list return structure:
     ```json
     {
       "items": [...],
       "total": 100,
       "page": 1,
       "size": 10,
       "pages": 10
     }
     ```

## Setup & Running locally

### 1. Configure Environment
Copy `.env.example` to `.env` and fill out your local variables:
```bash
cp .env.example .env
```

### 2. Local Virtual Environment
Install dependencies locally (Python 3.13+ required):
```bash
python -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows
pip install -r requirements/dev.txt
```

Run the application:
```bash
uvicorn app.main:app --reload
```

## Running Tests
Run tests locally using pytest:
```bash
pytest tests/
```

## AI Core Agent Framework

This ecosystem includes a dynamic, pluggable cognitive agent orchestration engine.

### 1. Agent Architecture
Agents are dynamically discovered and instantiated from the `agents/` root directory at startup. Each agent resides in its own folder and contains:
- `manifest.json`: Configuration specifications (enabled, provider name, required tools).
- `prompt.md`: Base system prompt guidelines.
- `tools.py`: Declarations of agent-specific plugin tools.
- `agent.py`: Agent execution module extending the abstract `BaseAgent` class.
- `README.md`: Local documentation.

The abstract `BaseAgent` defines:
- Lifecycle hooks (`before_run` / `after_run`) to post-process instructions.
- Standard execution loop entry point (`execute()`).
- Configuration validation checker (`validate()`).

### 2. Provider Architecture
Providers represent LLM model hosts and are abstracted under the `BaseProvider` class. Concrete implementations support:
- **Gemini**: Dynamic API triggers or fallback mocks.
- **OpenAI**: Chat completions support.
- **Anthropic**: Messages API support.
- **Ollama**: Local containerized inference.
- **OpenRouter**: Unified API routing.

The system switches providers globally or per-agent by modifying settings (`AI_PROVIDER` / `DEFAULT_MODEL` / manifests) without modifying application code.

### 3. Memory System
Agents maintain session context, conversation history, and data indexing using the pluggable memory layer:
- `SessionMemory`: Scoped short-term session state.
- `ConversationMemory`: Message thread (roles and text contents) retention.
- `LongTermMemory`: File-backed database persistent storage.
- `VectorMemory`: Stub semantic search engine with mock embeddings lookup.

### 4. Tool & Plugin System (Sprint 007)

The ecosystem includes a secure, production-ready Tool Calling Framework and Plugin Runtime.

#### Tool Architecture
- **BaseTool**: Abstract base class (`ai/tools/base_tool.py`) defining standard metadata (`tool_id`, `version`, `author`, `license`, `tags`, `permissions`, `timeout`), JSON schema `parameters`, validation hooks, and execution entries.
- **ToolRegistry**: Manages in-memory tool instances, dynamic registration, built-in discoveries (`ai/tools/builtin/`), conflict resolution, and metadata validation on load.
- **ToolExecutor**: Manages argument schema validation, permission checks, execution timeout enforcement (via ThreadPoolExecutor), exception standardizing, and DB logging.

#### Plugin Architecture
- **plugin.json Manifest**: Each external plugin under `/plugins` folder declares its properties: `id`, `name`, `version`, `author`, `description`, `permissions`, `dependencies`, `enabled`, and `entry_point`.
- **Plugin Loader**: Scans directories, prevents duplicate IDs, and dynamically imports plugins' `tools.py` modules.
- **Plugin Manager**: Provides interfaces to install (directory setup), uninstall, toggle statuses (updating memory & DB states), and verify health.

#### Built-in Tools
- **Web Search**: Simulates search query returns.
- **File Management**: Secure path IO operations restricted strictly inside the workspace boundary.
- **Python Code Executor**: Clean sandbox interface (`BasePythonSandbox`) implementing process-level isolation (`SubprocessPythonSandbox`) for security.
- **Math Calculator**: Safe expression evaluation using Python's `ast` (Abstract Syntax Tree) to block raw code execution.
- **DateTime Utility**: Handles formatted timestamps and timezone conversions.
- **Memory Manager**: Short-term state save/retrieve operations scoped to session keys.

#### Security Model
- **Process Isolation**: Untrusted script execution is isolated within subprocess runtimes, avoiding main process freeze or modifications.
- **Directory Bounds**: Path checks enforce that all filesystem read/write/deletes remain within the workspace root.
- **Log Auditing**: Every tool execution is recorded in the `tool_execution_logs` DB table (capturing timing, outputs, errors, session/user context).

#### MCP Compatibility
The framework exposes structures under `ai/mcp/` supporting future Model Context Protocol integrations:
- `mcp_schema.py`: Models matching standard MCP JSON-RPC protocol shapes.
- `mcp_adapter.py`: Adapter translating BaseTool instances to standard MCP tool schemas.

---

### 5. Observability & Monitoring (Sprint 007.5)

The ecosystem features a production-ready logging, tracing, and metric collection framework.

#### Logging Architecture
- **Thread-safe Correlation Context**: Correlation IDs are propagated across ASGI calls using Python's standard `contextvars`.
- **Dual Formatters**: Supports structured `JSONFormatter` output (optimized for production log aggregators) and standard colorized `ConsoleFormatter` formats.
- **Log Rotation**: Built-in `RotatingFileHandler` writing logs to `logs/app.log` up to 10MB sizes before rotating (holding 5 historical backup files).

#### Request Correlation IDs
- **Middleware Extraction/Generation**: Intercepts requests to check for incoming `X-Correlation-ID` or `X-Request-ID` headers, generating a fallback UUID if missing.
- **Header Returns**: Appends the same correlation ID back to the user response headers.

#### Metrics Registry & System Stats
- **Global Metrics Registry**: Tracks in-memory aggregates including request totals, latencies, DB query calls, and Redis key commands.
- **OpenTelemetry Abstraction Layer**: Includes abstract class structures (`BaseMetricsExporter`, `OTelMetricsExporterPlaceholder`) to enable zero-refactor OpenTelemetry migrations later.
- **Hardware Telemetry**: Collects active CPU, virtual memory, disk storage capacity percentages, process uptimes, active thread counts, and connection counts.

#### Telemetry Databases
- **System Metrics**: Persists hardware states (`system_metrics` table).
- **Execution Metrics**: Persists component latency and success rate diagnostics (`execution_metrics` table).

#### Retention Policy & Purges
- **Cleanup Service**: Provides the retention service `cleanup_expired_metrics_and_logs()` that purges DB system metric records and execution logs exceeding configured settings (`METRICS_RETENTION_DAYS`, `LOG_RETENTION_DAYS`).

#### Monitoring API Endpoints
Exposed routes under `/api/v1/monitoring/`:
- `GET /health`: Dependency connectivity indicators (DB and Redis status).
- `GET /system`: Hardware state telemetry.
- `GET /metrics`: In-memory HTTP request/DB counters.
- `GET /agents`: Agent latencies and successes analysis.
- `GET /tools`: Tool calling audits.
- `GET /plugins`: Active plugins summary.
- `GET /logs`: Real-time log tail retriever (retrieves last 100 log lines).
- `POST /cleanup`: Manual retention policy database purge.

---

### 6. Document Management & Vector Storage (Sprint 008A)

The ecosystem includes a production-ready Document Ingestion, chunking, and Vector Database layer.

#### File Ingestion & Security
- **Multi-File Ingestion**: Supports uploading multiple files in a single REST request, assigning unique UUID filenames under `data/documents/` while preserving metadata in SQL databases.
- **SHA-256 Duplicate Check**: Generates a cryptographic hash of uploaded files. Rejects duplicate uploads or returns existing document records to avoid storage waste.
- **Security Protections**: File validation checks MIME-types, size limits (up to 10MB), and prevents path traversals.

#### Background Ingestion Queue
- **FastAPI Background Tasks**: Triggers background parsing and chunking, immediately returning a `{"status": "processing"}` status payload. Clients can poll the status endpoint to monitor progression.

#### Pluggable Embedding & Vector Stores
- **Pluggable Vector Databases**: Built behind the `BaseVectorStore` interface supporting dynamic switches:
  - **SQLiteVectorStore**: Ecosystem default. Stores vector floats in binary BLOBs and computes cosine similarity directly in Python with zero external requirements.
  - **FAISSVectorStore / ChromaVectorStore**: Integrates native FAISS or ChromaDB indexing when packages are installed, falling back gracefully to SQLite if missing.
- **Pluggable Embedding Providers**: Supports Mock (1536 dim deterministic seed vectors), Google Gemini, and OpenAI API endpoints.
- **Batching & Exponential Backoff Retries**: Generates embeddings in batches (`BATCH_SIZE = 32`) and automatically applies retries with exponential backoffs.

#### Optimization Caching & Incremental Reindexing
- **Embedding Cache**: Checks for matching chunk text contents in the database. Reuses existing vectors and skips redundant provider calls.
- **Incremental Reindexing**: When reindexing, the pipeline compares new chunks to old chunks, keeping matching vectors and only requesting embeddings for changed/modified sections.

#### API Route Summary
Routes under `/api/v1/documents/` and `/api/v1/search/`:
- `POST /api/v1/documents/upload`: Multi-file background uploading.
- `GET /api/v1/documents`: List/filter documents.
- `GET /api/v1/documents/{id}/status`: Ingestion status (`pending`, `processing`, `indexed`, `failed`).
- `DELETE /api/v1/documents/{id}`: Cascadely purges files, DB chunks, embeddings, and caches.
- `POST /api/v1/documents/{id}/reindex`: Triggers incremental document reindexing.
- `POST /api/v1/search/similarity`: Similarity search using metadata filters.
- `POST /api/v1/search/vector`: Similarity search returning raw float coordinates.
- `GET /api/v1/search/statistics`: Ingestion statistics summary.
- `GET /api/v1/search/providers/health`: Status checks for vector store and embedding provider connections.

---

### 7. RAG Engine & Memory System (Sprint 008B)

The ecosystem includes a production-ready RAG Engine and Enterprise Memory System.

#### Four-Layer Memory System
- **Session Memory**: Key-value data mapped to active agent session scopes.
- **Conversation Memory**: Dialogue history threads stored in the `conversations` and `messages` tables.
- **Long-Term Memory**: Persistent key-value facts mapped to specific keys.
- **Knowledge Memory**: Semantic collections indexed via document chunks.
- **Memory Providers**: Configurable memory stores supporting SQLite (database entries), Redis (in-memory expirations), and File (JSON database backups) backends.

#### Conversation summarization & Pruning
- **Compression Summarizer**: Automatically compiles old dialogue rounds into a single fact sheet stored in `Conversation.summary` when messages exceed `MEMORY_SUMMARY_TRIGGER_MESSAGES` (default 10) or `MEMORY_SUMMARY_TRIGGER_TOKENS` (default 2000). Prunes older detail logs, leaving the last 2 local chat rounds to maintain conversational flow.

#### Knowledge Collections & Access Control
- **Collection Permissions**: Groups documents into Knowledge Collections of type:
  - `public`: Accessible to everyone.
  - `personal`: Accessible only to the creator (`owner_id == user_id`).
  - `team`: Shared within owner group scopes.
- **Access Filters**: Checks user permissions during the retrieval step, excluding unauthorized documents from prompt contexts.

#### Hybrid Retrieval & Explainability
- **Hybrid Retrieval**: Combines Vector similarity and Keyword term overlaps using reciprocal linear weights.
- **Reranker Service**: Contexts are ranked using a word-overlap MockReranker, or forwarded to Gemini/OpenAI API prompts.
- **Retrieval Explainability**: Endpoint `/api/v1/rag/explain` details retrieved documents, chunk IDs, similarity and reranking scores, memory hits, and estimated final prompt tokens.

#### API Route Summary
Routes under `/api/v1/memory/`, `/api/v1/conversations/`, and `/api/v1/rag/`:
- `GET /api/v1/memory`: List memory items by type.
- `DELETE /api/v1/memory`: Clear memory items by type.
- `POST /api/v1/memory/search`: Search specific memory key.
- `POST /api/v1/conversations`: Start conversation session.
- `GET /api/v1/conversations`: List active threads.
- `DELETE /api/v1/conversations/{id}`: Purge thread and cascade messages.
- `GET /api/v1/conversations/{id}/messages`: View history turns.
- `POST /api/v1/rag/chat`: Context-aware conversational generation.
- `POST /api/v1/rag/search`: Retrieve ranked contexts.
- `POST /api/v1/rag/context`: View formatted context text.
- `GET /api/v1/rag/explain`: Diagnostic queries metrics.
- `GET /api/v1/rag/providers`: Active provider configurations list.

---

### 8. Multi-Agent Collaboration & Workflow Orchestration (Sprint 009)

The ecosystem includes a production-grade Multi-Agent Collaboration Engine and Workflow Orchestrator.

#### Workflow Versioning & Templates
- **Versioning Control**: Modifying a workflow definition creates a new record with an incremented version, setting the older version `is_active = False` to preserve historical integrity.
- **Reusable Templates**: Seeds standard system templates (Research, Coding, Document Analysis, Multi-Agent Review) to run pipelines directly.

#### Agent Capability Registry & Orchestration
- **Capability Routing**: Agents register capability tags (e.g. `chat`, `coding`, `research`, `document`, `planning`, `analysis`). The central `AgentOrchestrator` resolves agent assignments at runtime based on task needs rather than hardcoding agent IDs.
- **Orchestrated Communication**: Prevents direct communication between agents. All message exchanges pass through the orchestrator transit hub.

#### Dead Letter Queue (DLQ)
- **DLQ Model & API**: When a task exhausts all retries, the orchestrator writes the failure reason, retry attempts, and stack traces to `DeadLetterQueue` tables. Accessible via `GET /api/v1/workflows/dead-letter`.

#### Human-in-the-Loop & State Manager
- **Suspension Pauses**: Steps requesting human approval suspend workflow executions. Resuming is triggered via API overrides which mark tasks as approved or rejected.
- **Event Bus & State Sync**: An in-memory broker logs lifecycle events (`WorkflowStarted`, `TaskCompleted`, `AgentFinished`) and saves contexts directly into the database.

#### API Route Summary
Routes under `/api/v1/workflows/`:
- `POST /api/v1/workflows`: Create/update workflow (registers new version).
- `GET /api/v1/workflows`: List active workflows and templates.
- `GET /api/v1/workflows/dead-letter`: View DLQ failure records.
- `GET /api/v1/workflows/{id}`: Fetch template version details.
- `POST /api/v1/workflows/{id}/execute`: Trigger execution asynchronously.
- `POST /api/v1/workflows/{id}/pause`: Pause running execution.
- `POST /api/v1/workflows/{id}/resume`: Resume execution and approve human overrides.
- `POST /api/v1/workflows/{id}/cancel`: Cancel execution.
- `GET /api/v1/workflows/{id}/status`: Progress tracking.
- `GET /api/v1/tasks`: List all tasks.
- `GET /api/v1/tasks/{id}`: Fetch task details.
- `GET /api/v1/orchestrator/status`: System counts (latencies, running agents, queue length).






