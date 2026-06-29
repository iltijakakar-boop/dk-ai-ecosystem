import sys
from pathlib import Path

# Add project root workspace directory to sys.path to allow imports of ai and agents packages
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.config.settings import settings
# Force database URL to test.db to isolate test runs
settings.DATABASE_URL = "sqlite:///./test.db"

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.dependencies.db import get_db
from app.dependencies.redis import get_redis

# Use local test SQLite database URL for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Mock Redis client helper for unit tests
class MockRedis:
    async def ping(self) -> bool:
        return True
    
    async def aclose(self) -> None:
        pass

async def mock_get_redis() -> MockRedis:
    return MockRedis()

@pytest.fixture(scope="session", autouse=True)
def db_setup() -> Generator:
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db() -> Generator:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="module")
def client() -> Generator:
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = mock_get_redis
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
