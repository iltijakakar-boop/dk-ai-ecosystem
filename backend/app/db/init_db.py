from sqlalchemy.orm import Session
from app.db.session import engine, Base
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.config.settings import settings

def init_db(db: Session) -> None:
    # Ensure all tables are created
    Base.metadata.create_all(bind=engine)
    
    # Seed the initial superuser if not already present
    superuser = db.query(User).filter(User.email == settings.FIRST_SUPERUSER).first()
    if not superuser:
        superuser_db = User(
            email=settings.FIRST_SUPERUSER,
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        db.add(superuser_db)
        db.commit()
        db.refresh(superuser_db)
