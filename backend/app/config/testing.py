from app.config.settings import Settings


class TestingSettings(Settings):
    DEBUG: bool = True
    ENVIRONMENT: str = "testing"
    DATABASE_URL: str = "sqlite:///./test.db"
    REDIS_URL: str = "redis://localhost:6379/1"


test_settings = TestingSettings()
