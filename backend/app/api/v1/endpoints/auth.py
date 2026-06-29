import time
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import redis.asyncio as aioredis
from typing import Optional

from app.dependencies.db import get_db
from app.dependencies.redis import get_redis
from app.dependencies.rate_limit import login_rate_limiter
from app.dependencies.auth import reusable_oauth2
from app.repositories.user import user_repository
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token, TokenRefresh, TokenPayload
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.config.settings import settings

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user = user_repository.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    return user_repository.create(db, obj_in=user_in)

@router.post("/login", response_model=Token, dependencies=[Depends(login_rate_limiter)])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = user_repository.get_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user."
        )
        
    access_token = create_access_token(
        subject=user.id, email=user.email, role=user.role.value
    )
    refresh_token = create_refresh_token(
        subject=user.id, email=user.email, role=user.role.value
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
def refresh_token(token_refresh: TokenRefresh):
    try:
        payload = jwt.decode(
            token_refresh.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        if token_data.type != "refresh" or token_data.sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token."
            )
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token."
        )
        
    access_token = create_access_token(
        subject=token_data.sub, email=token_data.email, role=token_data.role
    )
    new_refresh_token = create_refresh_token(
        subject=token_data.sub, email=token_data.email, role=token_data.role
    )
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(
    token: str = Depends(reusable_oauth2),
    redis_client: Optional[aioredis.Redis] = Depends(get_redis)
):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        exp = payload.get("exp")
        if exp:
            now = time.time()
            ttl = int(exp - now)
            if ttl > 0 and redis_client:
                await redis_client.setex(f"blacklist:{token}", ttl, "true")
    except JWTError:
        pass
        
    return {"detail": "Successfully logged out."}
