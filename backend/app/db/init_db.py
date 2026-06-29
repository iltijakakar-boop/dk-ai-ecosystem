from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import engine
from app.models.user import User, UserRole


def init_db(db: Session) -> None:
    # Ensure all tables are created
    Base.metadata.create_all(bind=engine)

    # Trigger database schema migrations
    from app.db.migrations import run_migrations

    run_migrations()

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
