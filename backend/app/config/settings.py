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

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
