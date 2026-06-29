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
│   │           ├── auth.py   # Registration, Login, Token Refresh, Logout endpoints
│   │           ├── health.py # Health status checker endpoint
│   │           └── users.py  # User profile and admin test route endpoints
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
│   │   └── user.py           # User model and UserRole enums definition
│   ├── repositories/         # Repository patterns for queries
│   │   └── user.py           # User CRUD repository definitions
│   ├── schemas/              # Pydantic schemas
│   │   ├── token.py          # Token payload and refresh schemas
│   │   └── user.py           # User creation, update, and response validation schemas
│   ├── services/             # Business logic services
│   ├── utils/                # Helper utilities
│   └── dependencies/         # FastAPI Dependency Injection
│       ├── auth.py           # User auth and Role checks dependencies
│       ├── db.py             # Database session dependency
│       ├── rate_limit.py     # Redis login rate limiting dependency
│       └── redis.py          # Redis connection dependency
│
├── tests/                    # Pytest test cases and conftest setup
│   ├── test_auth.py          # Auth validation, login, and RBAC tests
│   └── test_main.py          # Startup and health check tests
├── migrations/               # Alembic database schema migrations
├── requirements/             # Partitioned Python requirements (base, dev, prod)
├── Dockerfile                # Multi-stage Docker packaging configuration
├── docker-compose.yml        # Development environment runner (app + postgres + redis)
├── pyproject.toml            # Python tool configurations (black, ruff, pytest)
├── .env.example              # Sample environment configuration template
└── README.md                 # Project developer notes
```

## Security Features

1. **Authentication (JWT & Refresh)**:
   - Registers users via `/auth/register` with active schema checks.
   - Logs users in via `/auth/login` to obtain access and refresh tokens.
   - Access tokens contain claims for subject (`sub`), `email`, `role`, `type`, `iat`, and `exp`.
   - Refreshes expired access tokens via `/auth/refresh`.
   - Logs users out via `/auth/logout`, storing the token signature inside the Redis blacklist.
2. **Role-Based Access Control (RBAC)**:
   - Roles are strictly defined as `UserRole` enum values: `SUPER_ADMIN`, `ADMIN`, `USER`.
   - Endpoints are protected by injecting the `RoleChecker([Role...])` class-based dependency.
3. **Password Policy**:
   - Minimum of 8 characters.
   - Must contain at least one uppercase letter, one lowercase letter, one number, and one special character.
4. **Rate Limiting**:
   - Enforces a rate limit of 5 login attempts per 5 minutes per client IP using Redis.

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
The server will start at `http://localhost:8000`. You can access interactive API documentation at `http://localhost:8000/docs`.

### 3. Local Docker environment (Recommended)
You can spin up the application along with PostgreSQL and Redis (configured with restart policies and health checks) using:
```bash
docker compose up --build
```

## Running Tests
Run tests locally using pytest:
```bash
pytest tests/
```
Tests automatically mock the Redis connection and use an in-memory SQLite database configuration to run cleanly without external dependencies.
