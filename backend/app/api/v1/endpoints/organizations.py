from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.response import APIResponse
from app.services.organization_service import organization_service

router = APIRouter(prefix="/organizations", tags=["organizations"])


class OrganizationCreate(BaseModel):
    name: str
    slug: str


class BrandingUpdate(BaseModel):
    logo: Optional[str] = None
    colors: Optional[str] = None
    custom_domain: Optional[str] = None
    support_email: Optional[EmailStr] = None


class InvitationCreate(BaseModel):
    email: EmailStr
    role: str = "Member"


class InvitationAccept(BaseModel):
    token: str


@router.post("", response_model=APIResponse)
def create_organization(
    payload: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    org = organization_service.create_organization(
        db, name=payload.name, slug=payload.slug, owner_id=current_user.id
    )
    return APIResponse(
        success=True,
        message="Organization created successfully.",
        data={
            "id": org.id,
            "uuid": org.uuid,
            "name": org.name,
            "slug": org.slug,
            "plan": org.plan,
        },
    )


@router.get("", response_model=APIResponse)
def list_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    orgs = db.query(Organization).all()
    data = [
        {
            "id": o.id,
            "uuid": o.uuid,
            "name": o.name,
            "slug": o.slug,
            "plan": o.plan,
            "status": o.status,
        }
        for o in orgs
    ]
    return APIResponse(success=True, data=data)


@router.get("/{id}", response_model=APIResponse)
def get_organization(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    org = db.query(Organization).filter(Organization.id == id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found."
        )
    return APIResponse(
        success=True,
        data={
            "id": org.id,
            "uuid": org.uuid,
            "name": org.name,
            "slug": org.slug,
            "plan": org.plan,
            "status": org.status,
            "logo": org.logo,
            "colors": org.colors,
            "custom_domain": org.custom_domain,
            "support_email": org.support_email,
        },
    )


@router.put("/{id}/branding", response_model=APIResponse)
def update_branding(
    id: int,
    payload: BrandingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    org = organization_service.update_branding(
        db,
        org_id=id,
        logo=payload.logo,
        colors=payload.colors,
        custom_domain=payload.custom_domain,
        support_email=payload.support_email,
    )
    return APIResponse(
        success=True, message="Branding updated successfully.", data={"id": org.id}
    )


@router.post("/{id}/invitations", response_model=APIResponse)
def invite_user(
    id: int,
    payload: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    invite = organization_service.create_invitation(
        db,
        org_id=id,
        email=payload.email,
        role=payload.role,
        inviter_id=current_user.id,
    )
    return APIResponse(
        success=True,
        message="Invitation sent successfully.",
        data={
            "id": invite.id,
            "email": invite.email,
            "token": invite.token,
            "role": invite.role,
            "status": invite.status,
        },
    )


@router.post("/invitations/accept", response_model=APIResponse)
def accept_invitation(
    payload: InvitationAccept,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    organization_service.accept_invitation(
        db, token=payload.token, user_id=current_user.id
    )
    return APIResponse(success=True, message="Invitation accepted successfully.")


@router.post("/invitations/reject", response_model=APIResponse)
def reject_invitation(
    payload: InvitationAccept,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    organization_service.reject_invitation(db, token=payload.token)
    return APIResponse(success=True, message="Invitation rejected successfully.")
