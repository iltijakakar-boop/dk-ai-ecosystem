from typing import List, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "DK AI Ecosystem"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "DK AI Ecosystem core backend services."
    ENVIRONMENT: str = "development"

    # CORS Origins
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        return []

    # Database Settings
    DATABASE_URL: str = "sqlite:///./sql_app.db"

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security Settings
    SECRET_KEY: str = "your-super-secret-key-change-it-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Initial Admin Seeding Credentials
    FIRST_SUPERUSER: str = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "Admin@123"  # Conforms to password policies

    # AI Core settings
    AI_PROVIDER: str = "gemini"
    DEFAULT_MODEL: str = "gemini-2.5-flash"
    API_TIMEOUT: int = 30
    MAX_CONTEXT_LENGTH: int = 8192
    MAX_OUTPUT_TOKENS: int = 2048

    # Provider API keys and endpoints
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Observability & Monitoring settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "TEXT"  # TEXT or JSON
    ENABLE_FILE_LOGGING: bool = False
    ENABLE_JSON_LOGGING: bool = False
    METRICS_ENABLED: bool = True
    TRACE_ENABLED: bool = False
    REQUEST_ID_ENABLED: bool = True
    METRICS_RETENTION_DAYS: int = 30
    LOG_RETENTION_DAYS: int = 7

    # Document & Vector settings
    DOCUMENT_STORAGE_PATH: str = "data/documents"
    MAX_DOCUMENT_SIZE_MB: int = 10
    ALLOWED_DOCUMENT_TYPES: list = ["pdf", "docx", "txt", "md"]
    EMBEDDING_PROVIDER: str = "mock"
    EMBEDDING_MODEL: str = "text-embedding-004"
    VECTOR_PROVIDER: str = "sqlite"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 5
    BATCH_SIZE: int = 32

    # RAG & Memory settings
    MEMORY_PROVIDER: str = "sqlite"
    RAG_PROVIDER: str = "sqlite"
    MAX_CONTEXT_CHUNKS: int = 5
    MAX_CONTEXT_TOKENS: int = 4096
    ENABLE_HYBRID_SEARCH: bool = True
    ENABLE_RERANKING: bool = True
    MEMORY_EXPIRATION_DAYS: int = 30
    RERANKING_PROVIDER: str = "mock"
    MEMORY_SUMMARY_TRIGGER_MESSAGES: int = 10
    MEMORY_SUMMARY_TRIGGER_TOKENS: int = 2000

    # Orchestrator & Workflows settings
    DEFAULT_TASK_TIMEOUT_SECONDS: int = 60
    MAX_WORKFLOW_RETRIES: int = 3

    # Gateway settings
    DEFAULT_PROVIDER: str = "mock"
    DEFAULT_CHAT_MODEL: str = "mock-chat-model"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-004"
    DEFAULT_RERANK_MODEL: str = "mock-rerank"
    ENABLE_STREAMING: bool = True
    ENABLE_FAILOVER: bool = True
    MAX_PROVIDER_RETRIES: int = 3
    REQUEST_TIMEOUT_SECONDS: int = 30
    RATE_LIMIT_PER_PROVIDER: int = 60
    COST_TRACKING_ENABLED: bool = True

    # Automation and Task Execution settings
    ENABLE_AUTOMATION: bool = True
    ENABLE_SCHEDULER: bool = True
    DEFAULT_TIMEZONE: str = "UTC"
    MAX_JOB_RETRIES: int = 3
    JOB_TIMEOUT_SECONDS: int = 300
    MAX_PARALLEL_JOBS: int = 10
    JOB_HISTORY_DAYS: int = 30
    TASK_QUEUE_PROVIDER: str = "in_memory"
    SCHEDULER_PROVIDER: str = "apscheduler"
    ENABLE_EMAIL_NOTIFICATIONS: bool = False
    ENABLE_WEBHOOK_NOTIFICATIONS: bool = False

    # Enterprise Multi-Tenant settings
    ENABLE_MULTI_TENANT: bool = True
    ENABLE_API_KEYS: bool = True
    ENABLE_SERVICE_ACCOUNTS: bool = True
    ENABLE_USAGE_TRACKING: bool = True
    ENABLE_BILLING: bool = True
    ENABLE_SECRETS_MANAGER: bool = True
    DEFAULT_WORKSPACE_NAME: str = "Default Workspace"
    DEFAULT_ORGANIZATION_PLAN: str = "Free"
    MAX_API_KEYS_PER_WORKSPACE: int = 10
    MAX_TEAM_MEMBERS: int = 50
    MAX_PROJECTS_PER_WORKSPACE: int = 20
    SECRETS_ENCRYPTION_KEY: str = "dk-ai-ecosystem-default-dev-secrets-key-32bytes="

    # Enterprise AI Marketplace & Plugin Settings
    ENABLE_MARKETPLACE: bool = True
    ENABLE_PLUGIN_SYSTEM: bool = True
    ENABLE_PLUGIN_SANDBOX: bool = True
    ENABLE_PLUGIN_SIGNATURES: bool = True
    ENABLE_PLUGIN_AUTO_UPDATE: bool = True
    ENABLE_MARKETPLACE_PAYMENTS: bool = True
    ENABLE_PLUGIN_ANALYTICS: bool = True
    ENABLE_PROMPT_MARKETPLACE: bool = True
    ENABLE_TEMPLATE_MARKETPLACE: bool = True
    ENABLE_KNOWLEDGE_PACKS: bool = True
    MAX_PLUGIN_SIZE_MB: int = 100
    MAX_PLUGIN_DEPENDENCIES: int = 25

    # Enterprise AI Studio Settings (Sprint 014)
    ENABLE_AI_STUDIO: bool = True
    ENABLE_VISUAL_WORKFLOW_BUILDER: bool = True
    ENABLE_AGENT_BUILDER: bool = True
    ENABLE_PROMPT_STUDIO: bool = True
    ENABLE_PIPELINE_DESIGNER: bool = True
    ENABLE_DEBUGGER: bool = True
    ENABLE_DEPLOYMENTS: bool = True
    ENABLE_VISUAL_VERSIONING: bool = True
    ENABLE_COLLABORATION: bool = True

    # Enterprise MCP Server & Client Ecosystem (Sprint 015)
    ENABLE_MCP: bool = True
    ENABLE_MCP_SERVER: bool = True
    ENABLE_MCP_CLIENT: bool = True
    ENABLE_TOOL_REGISTRY: bool = True
    ENABLE_CONNECTORS: bool = True
    ENABLE_REMOTE_EXECUTION: bool = True
    ENABLE_TOOL_ANALYTICS: bool = True
    ENABLE_MCP_MARKETPLACE: bool = True

    # Enterprise Multi-Modal AI (Sprint 016)
    ENABLE_MULTIMODAL_AI: bool = True
    ENABLE_VISION_AI: bool = True
    ENABLE_SPEECH_AI: bool = True
    ENABLE_AUDIO_AI: bool = True
    ENABLE_VIDEO_AI: bool = True
    ENABLE_OCR: bool = True
    ENABLE_DOCUMENT_AI: bool = True
    ENABLE_IMAGE_GENERATION: bool = True
    ENABLE_TEXT_TO_SPEECH: bool = True
    ENABLE_SPEECH_TO_TEXT: bool = True
    ENABLE_MEDIA_PIPELINES: bool = True
    ENABLE_MEDIA_STREAMING: bool = True

    # Enterprise AI Model Management & Fine-Tuning (Sprint 017)
    ENABLE_MODEL_REGISTRY: bool = True
    ENABLE_FINE_TUNING: bool = True
    ENABLE_DATASET_MANAGER: bool = True
    ENABLE_MODEL_EVALUATION: bool = True
    ENABLE_EXPERIMENT_TRACKING: bool = True
    ENABLE_LLM_GATEWAY: bool = True
    ENABLE_GPU_SCHEDULER: bool = True
    ENABLE_MODEL_DEPLOYMENTS: bool = True
    ENABLE_MODEL_MONITORING: bool = True
    ENABLE_MODEL_VERSIONING: bool = True
    ENABLE_MODEL_ROUTING: bool = True
    ENABLE_HYPERPARAMETERS: bool = True
    ENABLE_LORA: bool = True
    ENABLE_QLORA: bool = True
    ENABLE_PEFT: bool = True

    # Enterprise Observability Settings (Sprint 018)
    ENABLE_OBSERVABILITY: bool = True
    ENABLE_METRICS: bool = True
    ENABLE_LOGGING: bool = True
    ENABLE_TRACING: bool = True
    ENABLE_ALERTING: bool = True
    ENABLE_SECURITY_CENTER: bool = True
    ENABLE_COMPLIANCE: bool = True
    ENABLE_AI_GOVERNANCE: bool = True
    ENABLE_INCIDENT_MANAGEMENT: bool = True
    ENABLE_ANOMALY_DETECTION: bool = True
    ENABLE_OPEN_TELEMETRY: bool = True
    ENABLE_PROMETHEUS: bool = True
    ENABLE_GRAFANA_EXPORT: bool = True

    # Enterprise Distributed Infrastructure (Sprint 019)
    ENABLE_KUBERNETES: bool = True
    ENABLE_DOCKER: bool = True
    ENABLE_SERVICE_MESH: bool = True
    ENABLE_AUTO_SCALING: bool = True
    ENABLE_LOAD_BALANCING: bool = True
    ENABLE_MULTI_REGION: bool = True
    ENABLE_EDGE_AI: bool = True
    ENABLE_DISASTER_RECOVERY: bool = True
    ENABLE_INFRASTRUCTURE_MONITORING: bool = True
    ENABLE_SERVICE_DISCOVERY: bool = True
    ENABLE_DISTRIBUTED_CACHE: bool = True
    ENABLE_MESSAGE_BROKER: bool = True

    # Enterprise DevOps Settings (Sprint 020)
    ENABLE_CICD: bool = True
    ENABLE_GITOPS: bool = True
    ENABLE_RELEASE_MANAGEMENT: bool = True
    ENABLE_ENVIRONMENTS: bool = True
    ENABLE_IAC: bool = True
    ENABLE_ARTIFACT_REGISTRY: bool = True
    ENABLE_DEPLOYMENT_AUTOMATION: bool = True
    ENABLE_PRODUCTION_APPROVALS: bool = True
    ENABLE_CHANGE_MANAGEMENT: bool = True
    ENABLE_RELEASE_NOTES: bool = True

    # Enterprise Data Platform Settings (Sprint 021)
    ENABLE_DATA_PLATFORM: bool = True
    ENABLE_LAKEHOUSE: bool = True
    ENABLE_FEATURE_STORE: bool = True
    ENABLE_DATA_CATALOG: bool = True
    ENABLE_DATA_GOVERNANCE: bool = True
    ENABLE_DATA_LINEAGE: bool = True
    ENABLE_DATA_QUALITY: bool = True
    ENABLE_ETL_PIPELINES: bool = True
    ENABLE_STREAMING: bool = True
    ENABLE_VECTOR_DATASETS: bool = True
    ENABLE_DATA_VERSIONING: bool = True
    ENABLE_METADATA_INDEXING: bool = True

    # Enterprise IAM Settings (Sprint 022)
    ENABLE_ENTERPRISE_IAM: bool = True
    ENABLE_SSO: bool = True
    ENABLE_OAUTH2: bool = True
    ENABLE_OPENID_CONNECT: bool = True
    ENABLE_SAML: bool = True
    ENABLE_MFA: bool = True
    ENABLE_PASSKEYS: bool = True
    ENABLE_ZERO_TRUST: bool = True
    ENABLE_POLICY_ENGINE: bool = True
    ENABLE_DEVICE_TRUST: bool = True
    ENABLE_SESSION_MANAGEMENT: bool = True
    ENABLE_API_SECURITY: bool = True
    ENABLE_FEDERATION: bool = True
    ENABLE_RISK_BASED_AUTH: bool = True
    ENABLE_ADAPTIVE_AUTH: bool = True

    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
