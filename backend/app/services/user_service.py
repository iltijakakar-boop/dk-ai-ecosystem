from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.user import user_repository
from app.repositories.audit_log import audit_log_repository
from app.models.user import User, UserRole
from app.core.security import get_password_hash, verify_password

class UserService:
    def check_role_hierarchy(self, actor_role: UserRole, target_role: UserRole) -> None:
        role_weights = {
            UserRole.SUPER_ADMIN: 3,
            UserRole.ADMIN: 2,
            UserRole.USER: 1
        }
        if role_weights[actor_role] <= role_weights[target_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify a user with equal or higher privileges."
            )

    def update_user_profile(
        self,
        db: Session,
        *,
        user_id: int,
        email: str,
        ip: str = None,
        ua: str = None
    ) -> User:
        user = user_repository.get(db, id=user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        if email != user.email:
            existing = user_repository.get_by_email(db, email=email)
            if existing:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
            user.email = email
            db.add(user)
            db.commit()
            db.refresh(user)
            audit_log_repository.create_log(
                db,
                user_id=user_id,
                target_id=user_id,
                resource="users",
                action="PROFILE_UPDATED",
                ip_address=ip,
                user_agent=ua,
                details=f"Email changed to {email}"
            )
        return user

    def change_user_password(
        self,
        db: Session,
        *,
        user_id: int,
        old_password: str,
        new_password: str,
        ip: str = None,
        ua: str = None
    ) -> None:
        user = user_repository.get(db, id=user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")
        
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        db.commit()
        audit_log_repository.create_log(
            db,
            user_id=user_id,
            target_id=user_id,
            resource="users",
            action="PASSWORD_CHANGED",
            ip_address=ip,
            user_agent=ua
        )

    def update_user_role(
        self,
        db: Session,
        *,
        actor: User,
        target_id: int,
        new_role: UserRole,
        ip: str = None,
        ua: str = None
    ) -> User:
        target = user_repository.get(db, id=target_id)
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        self.check_role_hierarchy(actor.role, target.role)
        
        role_weights = {
            UserRole.SUPER_ADMIN: 3,
            UserRole.ADMIN: 2,
            UserRole.USER: 1
        }
        if role_weights[actor.role] < role_weights[new_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot promote a user to a role higher than your own."
            )

        old_role = target.role
        target.role = new_role
        db.add(target)
        db.commit()
        db.refresh(target)
        
        audit_log_repository.create_log(
            db,
            user_id=actor.id,
            target_id=target_id,
            resource="users",
            action="ROLE_UPDATED",
            ip_address=ip,
            user_agent=ua,
            details=f"Role changed from {old_role} to {new_role}"
        )
        return target

    def update_user_status(
        self,
        db: Session,
        *,
        actor: User,
        target_id: int,
        is_active: bool,
        ip: str = None,
        ua: str = None
    ) -> User:
        target = user_repository.get(db, id=target_id)
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        self.check_role_hierarchy(actor.role, target.role)
        
        target.is_active = is_active
        db.add(target)
        db.commit()
        db.refresh(target)
        
        action_str = "USER_ACTIVATED" if is_active else "USER_DEACTIVATED"
        audit_log_repository.create_log(
            db,
            user_id=actor.id,
            target_id=target_id,
            resource="users",
            action=action_str,
            ip_address=ip,
            user_agent=ua
        )
        return target

    def delete_user(
        self,
        db: Session,
        *,
        actor: User,
        target_id: int,
        ip: str = None,
        ua: str = None
    ) -> User:
        target = user_repository.get(db, id=target_id)
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        self.check_role_hierarchy(actor.role, target.role)
        
        deleted = user_repository.soft_delete(db, user_id=target_id, deleted_by_id=actor.id)
        audit_log_repository.create_log(
            db,
            user_id=actor.id,
            target_id=target_id,
            resource="users",
            action="USER_DELETED",
            ip_address=ip,
            user_agent=ua
        )
        return deleted

user_service = UserService()
