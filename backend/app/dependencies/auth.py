from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
import redis.asyncio as aioredis
from typing import List, Optional

from app.dependencies.db import get_db
from app.dependencies.redis import get_redis
from app.config.settings import settings
from app.core.exceptions import UnauthorizedException
from app.repositories.user import user_repository
from app.models.user import User, UserRole
from app.schemas.token import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2),
    redis_client: Optional[aioredis.Redis] = Depends(get_redis)
) -> User:
    # Check if the token is blacklisted in Redis
    if redis_client:
        try:
            is_blacklisted = await redis_client.get(f"blacklist:{token}")
            if is_blacklisted:
                raise UnauthorizedException("Token is blacklisted")
        except Exception:
            pass

    # Decode and validate JWT
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        if token_data.type != "access":
            raise UnauthorizedException("Invalid token type")
            
        if token_data.sub is None:
            raise UnauthorizedException("Could not validate credentials")
    except (JWTError, ValueError):
        raise UnauthorizedException("Could not validate credentials")

    # Fetch corresponding user from DB
    user = user_repository.get(db, id=int(token_data.sub))
    if not user:
        raise UnauthorizedException("User not found")
        
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

class RoleChecker:
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user does not have enough privileges"
            )
        return current_user
