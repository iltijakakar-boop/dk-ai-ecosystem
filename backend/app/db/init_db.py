from sqlalchemy.orm import Session
from app.db.session import engine, Base

def init_db(db: Session) -> None:
    # Tables should be created with Alembic migrations in production,
    # but for local development, we can create them directly if needed:
    Base.metadata.create_all(bind=engine)
    
    # Add database seeding logic here (e.g. creating superuser)
    pass
