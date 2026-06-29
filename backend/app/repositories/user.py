from typing import List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.repositories.base import CRUDBase
from app.models.user import User, UserRole
from app.schemas.user import UserCreate

class UserRepository(CRUDBase[User]):
    def get(self, db: Session, id: Any) -> Optional[User]:
        return db.query(User).filter(User.id == id, User.is_deleted == False).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).filter(User.is_deleted == False).offset(skip).limit(limit).all()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email, User.is_deleted == False).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        from app.core.security import get_password_hash
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            role=UserRole.USER,
            is_active=True,
            is_deleted=False
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def search_and_filter(
        self,
        db: Session,
        *,
        query: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[User], int]:
        q = db.query(User).filter(User.is_deleted == False)
        
        if query:
            # Support search by email and id
            if query.isdigit():
                q = q.filter((User.id == int(query)) | (User.email.contains(query)))
            else:
                q = q.filter(User.email.contains(query))
        
        if role:
            q = q.filter(User.role == role)
            
        if is_active is not None:
            q = q.filter(User.is_active == is_active)
            
        total = q.count()
        items = q.offset(skip).limit(limit).all()
        return items, total

    def soft_delete(self, db: Session, *, user_id: int, deleted_by_id: int) -> Optional[User]:
        user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
        if user:
            user.is_deleted = True
            user.deleted_at = datetime.now(timezone.utc)
            user.deleted_by = deleted_by_id
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

user_repository = UserRepository(User)
