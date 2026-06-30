# Multi-Tenant Enterprise Platform Documentation

This document describes the design, architecture, and configuration of the multi-tenant enterprise system introduced in Sprint 012.

---

## 1. Core Architecture

The Multi-Tenant platform is structured using a clean domain division under `backend/app`:

- **Database Models (`app/models/organization.py`)**: 12 custom SQLAlchemy models representing organizations, workspaces, teams, team members, projects, api keys, service accounts, secrets, secret versions, invitations, usage records, and billing plans.
- **Tenant Context (`app/middleware/tenant_resolver.py`)**: Thread-safe active tenant scoping using `contextvars.ContextVar`. Allows background workers, service layers, and request-response threads to dynamically query the current tenant bounds.
- **Dependencies (`app/dependencies/tenant.py`)**: Automatically resolves organization, workspace, and project bounds from JWT authentication tokens, API keys (`dk_api_...`), or Service Account credentials (`dk_sa_...`).
- **Service Layers (`app/services/...`)**: Independent CRUD logic and business checks (e.g. workspace quotas, secret encryption, billing upgrades).

---

## 2. Authentication & Tenant Resolver

A centralized dependency (`get_tenant_context_dependency`) inspects every incoming HTTP request:

1. **API Keys**: Authenticated via `Authorization: Bearer dk_api_xxxx` or `x-api-key` header. Automatically resolved to the designated workspace.
2. **Service Accounts**: Authenticated via `Authorization: Bearer dk_sa_xxxx` or `x-service-account-token` header. Automatically resolved to the designated workspace.
3. **User Tokens**: Authenticated via JWT bearer tokens. Resolves active workspace from the `x-workspace-id` header or switches automatically to the user's default workspace.

Resolved tenant IDs are loaded into thread-local variables inside `TenantContext`:

```python
from app.middleware.tenant_resolver import TenantContext

with TenantContext(org_id=1, workspace_id=2):
    # Any query or operation inside this block is scoped to org 1, workspace 2
    pass
```

---

## 3. Enterprise RBAC Scopes

Fine-grained permissions are enforced per request via `ScopeChecker(required_scope)`. Standard scopes include:

- `agent.read` / `agent.write`
- `workflow.read` / `workflow.write`
- `rag.read` / `rag.write`
- `vector.read` / `vector.write`
- `storage.read` / `storage.write`
- `secret.read` / `secret.write`
- `billing.read` / `billing.write`
- `admin.full`

Each scope maps to a minimum allowed user role (e.g., `VIEWER`, `MEMBER`, `DEVELOPER`, `TEAM_MANAGER`, `WORKSPACE_ADMIN`, `ORGANIZATION_ADMIN`, `ORGANIZATION_OWNER`, `SUPER_ADMIN`).

---

## 4. Quotas & Billing Limits

Resource creation is regulated by workspace-specific quotas. The `workspace_service.check_quota` method is called inside service layers before adding resources:

```python
workspace_service.check_quota(db, workspace_id=ws_id, resource_type="projects", amount=1)
```

Quotas mapping per Billing Plan:

| Resource Type | Free | Starter | Pro | Business | Enterprise | Custom |
|---|---|---|---|---|---|---|
| **AI Agents** | 3 | 5 | 15 | 50 | 1000 | 9999 |
| **Workflows** | 3 | 5 | 15 | 50 | 1000 | 9999 |
| **Automations** | 3 | 5 | 15 | 50 | 1000 | 9999 |
| **Storage (MB)** | 50 | 100 | 500 | 2000 | 50000 | 99999 |
| **Team Members** | 3 | 5 | 15 | 50 | 1000 | 9999 |
| **Projects** | 2 | 3 | 10 | 30 | 1000 | 9999 |

---

## 5. Secrets Management & Encryption

All workspace credentials, API tokens, and connection strings are stored encrypted in the `secrets` table:

- **AES/Fernet Encryption**: Keys are derived Base64-safe using SHA-256 of the configuration secret key (`SECRETS_ENCRYPTION_KEY`).
- **Version History & Rollbacks**: Every update creates a new entry in `secret_versions`. Reverting to previous versions is supported via `/rollback` endpoint.

---

## 6. Global Search & Export

- **Enterprise Search**: Provides workspace-scoped global search matching text queries against projects, teams, agents, workflows, documents, and secrets.
- **Enterprise Export**: Generates a unified JSON file archiving workspace settings, projects list, team topologies, registered agents, and workflows.
