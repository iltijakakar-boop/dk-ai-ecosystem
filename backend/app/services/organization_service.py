import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.organization import (
    Organization,
    OrganizationInvitation,
    Team,
    TeamMember,
    Workspace,
)


class OrganizationService:
    def create_organization(
        self, db: Session, *, name: str, slug: str, owner_id: int
    ) -> Organization:
        # Check slug uniqueness
        existing = db.query(Organization).filter(Organization.slug == slug).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization slug is already taken.",
            )

        org = Organization(name=name, slug=slug, owner_id=owner_id)
        db.add(org)
        db.commit()
        db.refresh(org)

        # Automatically create default workspace and team
        from app.services.workspace_service import workspace_service

        workspace = workspace_service.create_workspace(
            db,
            organization_id=org.id,
            name="Default Workspace",
            description="Default workspace created for organization.",
        )

        default_team = Team(
            workspace_id=workspace.id,
            name="General Team",
            description="General organization-wide team.",
        )
        db.add(default_team)
        db.commit()
        db.refresh(default_team)

        # Add owner to team membership
        membership = TeamMember(
            team_id=default_team.id,
            user_id=owner_id,
            role="Owner",
            invited_by=owner_id,
        )
        db.add(membership)
        db.commit()

        return org

    def update_branding(
        self,
        db: Session,
        *,
        org_id: int,
        logo: Optional[str] = None,
        colors: Optional[str] = None,
        custom_domain: Optional[str] = None,
        support_email: Optional[str] = None,
    ) -> Organization:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found."
            )

        if logo is not None:
            org.logo = logo
        if colors is not None:
            org.colors = colors
        if custom_domain is not None:
            org.custom_domain = custom_domain
        if support_email is not None:
            org.support_email = support_email

        db.commit()
        db.refresh(org)
        return org

    def create_invitation(
        self, db: Session, *, org_id: int, email: str, role: str, inviter_id: int
    ) -> OrganizationInvitation:
        # Check active invite
        existing = (
            db.query(OrganizationInvitation)
            .filter(
                OrganizationInvitation.organization_id == org_id,
                OrganizationInvitation.email == email,
                OrganizationInvitation.status == "Pending",
            )
            .first()
        )
        if existing:
            # Check expiration
            if existing.expires_at > datetime.utcnow():
                return existing
            existing.status = "Expired"
            db.commit()

        token = secrets.token_hex(32)
        invite = OrganizationInvitation(
            organization_id=org_id,
            email=email,
            token=token,
            role=role,
            status="Pending",
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db.add(invite)
        db.commit()
        db.refresh(invite)
        return invite

    def accept_invitation(self, db: Session, *, token: str, user_id: int) -> bool:
        invite = (
            db.query(OrganizationInvitation)
            .filter(
                OrganizationInvitation.token == token,
                OrganizationInvitation.status == "Pending",
            )
            .first()
        )
        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or already processed invitation token.",
            )

        if invite.expires_at < datetime.utcnow():
            invite.status = "Expired"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation token has expired.",
            )

        # Get default workspace and default team for this org
        workspace = (
            db.query(Workspace)
            .filter(Workspace.organization_id == invite.organization_id)
            .first()
        )
        if workspace:
            team = db.query(Team).filter(Team.workspace_id == workspace.id).first()
            if team:
                # Add to team members
                existing_member = (
                    db.query(TeamMember)
                    .filter(
                        TeamMember.team_id == team.id, TeamMember.user_id == user_id
                    )
                    .first()
                )
                if not existing_member:
                    membership = TeamMember(
                        team_id=team.id,
                        user_id=user_id,
                        role=invite.role,
                        invited_by=invite.organization_id,  # Org ID system inviter
                    )
                    db.add(membership)

        invite.status = "Accepted"
        db.commit()
        return True

    def reject_invitation(self, db: Session, *, token: str) -> bool:
        invite = (
            db.query(OrganizationInvitation)
            .filter(
                OrganizationInvitation.token == token,
                OrganizationInvitation.status == "Pending",
            )
            .first()
        )
        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or already processed invitation token.",
            )

        invite.status = "Rejected"
        db.commit()
        return True


organization_service = OrganizationService()
