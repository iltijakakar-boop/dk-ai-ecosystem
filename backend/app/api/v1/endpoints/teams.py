from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.db import get_db
from app.models.organization import Team
from app.models.user import User
from app.schemas.response import APIResponse
from app.services.team_service import team_service

router = APIRouter(prefix="/teams", tags=["teams"])


class TeamCreate(BaseModel):
    workspace_id: int
    name: str
    description: Optional[str] = None


class MemberInvite(BaseModel):
    user_id: int
    role: str = "Member"


class MemberRoleUpdate(BaseModel):
    role: str


@router.post("", response_model=APIResponse)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    team = team_service.create_team(
        db,
        workspace_id=payload.workspace_id,
        name=payload.name,
        description=payload.description,
    )
    return APIResponse(
        success=True,
        message="Team created successfully.",
        data={
            "id": team.id,
            "workspace_id": team.workspace_id,
            "name": team.name,
            "description": team.description,
        },
    )


@router.get("", response_model=APIResponse)
def list_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    teams = db.query(Team).all()
    data = [
        {
            "id": t.id,
            "workspace_id": t.workspace_id,
            "name": t.name,
            "description": t.description,
        }
        for t in teams
    ]
    return APIResponse(success=True, data=data)


@router.post("/{id}/invite", response_model=APIResponse)
def invite_to_team(
    id: int,
    payload: MemberInvite,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    member = team_service.add_member(
        db,
        team_id=id,
        user_id=payload.user_id,
        role=payload.role,
        inviter_id=current_user.id,
    )
    return APIResponse(
        success=True,
        message="Member added to team successfully.",
        data={
            "id": member.id,
            "team_id": member.team_id,
            "user_id": member.user_id,
            "role": member.role,
        },
    )


@router.post("/{id}/remove-member", response_model=APIResponse)
def remove_from_team(
    id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    team_service.remove_member(
        db, team_id=id, user_id=user_id, actor_role=current_user.role
    )
    return APIResponse(success=True, message="Member removed from team successfully.")


@router.put("/{id}/members/{user_id}", response_model=APIResponse)
def update_member_role(
    id: int,
    user_id: int,
    payload: MemberRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    member = team_service.change_role(
        db,
        team_id=id,
        user_id=user_id,
        new_role=payload.role,
        actor_role=current_user.role,
    )
    return APIResponse(
        success=True,
        message="Member role updated successfully.",
        data={"id": member.id, "role": member.role},
    )
