from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.organization import Team, TeamMember


class TeamService:
    ROLE_WEIGHTS = {
        "SUPER_ADMIN": 8,
        "ORGANIZATION_OWNER": 7,
        "ORGANIZATION_ADMIN": 6,
        "WORKSPACE_ADMIN": 5,
        "TEAM_MANAGER": 4,
        "DEVELOPER": 3,
        "MEMBER": 2,
        "VIEWER": 1,
    }

    def check_hierarchy(self, actor_role: str, target_role: str) -> None:
        actor_weight = self.ROLE_WEIGHTS.get(actor_role.upper(), 0)
        target_weight = self.ROLE_WEIGHTS.get(target_role.upper(), 0)
        if actor_weight <= target_weight:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify a user with equal or higher privileges.",
            )

    def create_team(
        self,
        db: Session,
        *,
        workspace_id: int,
        name: str,
        description: Optional[str] = None
    ) -> Team:
        team = Team(workspace_id=workspace_id, name=name, description=description)
        db.add(team)
        db.commit()
        db.refresh(team)
        return team

    def add_member(
        self, db: Session, *, team_id: int, user_id: int, role: str, inviter_id: int
    ) -> TeamMember:
        existing = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this team.",
            )

        member = TeamMember(
            team_id=team_id, user_id=user_id, role=role, invited_by=inviter_id
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    def remove_member(
        self, db: Session, *, team_id: int, user_id: int, actor_role: str
    ) -> None:
        member = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            .first()
        )
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in team.",
            )

        self.check_hierarchy(actor_role, member.role)

        db.delete(member)
        db.commit()

    def change_role(
        self, db: Session, *, team_id: int, user_id: int, new_role: str, actor_role: str
    ) -> TeamMember:
        member = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            .first()
        )
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in team.",
            )

        self.check_hierarchy(actor_role, member.role)

        member.role = new_role
        db.commit()
        db.refresh(member)
        return member


team_service = TeamService()
