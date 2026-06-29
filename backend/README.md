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



