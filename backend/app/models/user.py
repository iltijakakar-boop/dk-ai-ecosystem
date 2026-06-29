import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String

from app.db.session import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    USER = "USER"


class User(Base):
    __tablename__ = "users"

    id: Column = Column(Integer, primary_key=True, index=True)
    email: Column = Column(String, unique=True, index=True, nullable=False)
    hashed_password: Column = Column(String, nullable=False)
    is_active: Column = Column(Boolean, default=True, nullable=False)
    role: Column = Column(Enum(UserRole), default=UserRole.USER, nullable=False)

    # Soft delete tracking
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
