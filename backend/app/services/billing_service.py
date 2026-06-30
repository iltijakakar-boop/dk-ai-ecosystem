from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.organization import Organization, Workspace
from app.services.workspace_service import workspace_service


class BillingService:
    PLAN_QUOTAS = {
        "Free": {
            "agents": 3,
            "workflows": 3,
            "automations": 3,
            "storage_mb": 50,
            "members": 3,
            "projects": 2,
        },
        "Starter": {
            "agents": 5,
            "workflows": 5,
            "automations": 5,
            "storage_mb": 100,
            "members": 5,
            "projects": 3,
        },
        "Pro": {
            "agents": 15,
            "workflows": 15,
            "automations": 15,
            "storage_mb": 500,
            "members": 15,
            "projects": 10,
        },
        "Business": {
            "agents": 50,
            "workflows": 50,
            "automations": 50,
            "storage_mb": 2000,
            "members": 50,
            "projects": 30,
        },
        "Enterprise": {
            "agents": 1000,
            "workflows": 1000,
            "automations": 1000,
            "storage_mb": 50000,
            "members": 1000,
            "projects": 1000,
        },
        "Custom": {
            "agents": 9999,
            "workflows": 9999,
            "automations": 9999,
            "storage_mb": 99999,
            "members": 9999,
            "projects": 9999,
        },
    }

    def update_organization_plan(
        self, db: Session, *, org_id: int, plan_name: str
    ) -> Organization:
        if plan_name not in self.PLAN_QUOTAS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid billing plan selection: {plan_name}",
            )

        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found."
            )

        org.plan = plan_name
        db.commit()

        # Update quotas on all workspaces belonging to this organization
        workspaces = (
            db.query(Workspace).filter(Workspace.organization_id == org_id).all()
        )
        for ws in workspaces:
            workspace_service.update_quotas(
                db, workspace_id=ws.id, quotas_dict=self.PLAN_QUOTAS[plan_name]
            )

        return org


billing_service = BillingService()
