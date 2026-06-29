from sqlalchemy.orm import Session
from app.repositories.base import CRUDBase
from app.models.user import User, UserRole
from app.schemas.user import UserCreate

class UserRepository(CRUDBase[User]):
    def get_by_email(self, db: Session, email: str) -> User:
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        from app.core.security import get_password_hash
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            role=UserRole.USER,
            is_active=True
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

user_repository = UserRepository(User)
