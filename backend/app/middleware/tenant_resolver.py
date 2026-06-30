import contextvars
from typing import Optional

# Thread-safe context variables for active tenant scope
active_org_id = contextvars.ContextVar("active_org_id", default=None)
active_workspace_id = contextvars.ContextVar("active_workspace_id", default=None)
active_project_id = contextvars.ContextVar("active_project_id", default=None)


class TenantContext:
    """
    Context manager to easily set/reset tenant boundaries in synchronous/asynchronous code block scopes.
    """

    def __init__(
        self,
        org_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ):
        self.org_id = org_id
        self.workspace_id = workspace_id
        self.project_id = project_id
        self.tokens: list = []

    def __enter__(self):
        if self.org_id is not None:
            self.tokens.append((active_org_id, active_org_id.set(self.org_id)))
        if self.workspace_id is not None:
            self.tokens.append(
                (active_workspace_id, active_workspace_id.set(self.workspace_id))
            )
        if self.project_id is not None:
            self.tokens.append(
                (active_project_id, active_project_id.set(self.project_id))
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for var, token in reversed(self.tokens):
            var.reset(token)


def get_tenant_context():
    """
    Retrieve active tenant boundaries from thread-local context variables.
    """
    return {
        "org_id": active_org_id.get(),
        "workspace_id": active_workspace_id.get(),
        "project_id": active_project_id.get(),
    }
