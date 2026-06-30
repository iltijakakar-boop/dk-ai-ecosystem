import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.organization import APIKey


class APIKeyService:
    def generate_key(
        self,
        db: Session,
        *,
        workspace_id: int,
        name: str,
        permissions: Optional[List[str]] = None,
        expires_in_days: Optional[int] = 30,
    ) -> tuple[str, APIKey]:
        # Generate random key string
        secret_part = secrets.token_hex(16)
        clear_key = f"dk_api_{secret_part}"

        # Hash key for storage
        key_hash = hashlib.sha256(clear_key.encode()).hexdigest()

        # Permissions list to string
        perms_str = ",".join(permissions) if permissions else ""

        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        key_obj = APIKey(
            workspace_id=workspace_id,
            name=name,
            key_hash=key_hash,
            permissions=perms_str,
            expires_at=expires_at,
        )
        db.add(key_obj)
        db.commit()
        db.refresh(key_obj)

        return clear_key, key_obj

    def verify_key(self, db: Session, *, clear_key: str) -> APIKey:
        if not clear_key.startswith("dk_api_"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key format.",
            )

        key_hash = hashlib.sha256(clear_key.encode()).hexdigest()
        key_obj = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()

        if not key_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key."
            )

        if key_obj.expires_at and key_obj.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key has expired."
            )

        # Update last used
        key_obj.last_used_at = datetime.utcnow()
        db.commit()
        db.refresh(key_obj)

        return key_obj

    def check_scope(self, key_obj: APIKey, required_scope: str) -> None:
        scopes = [
            s.strip() for s in (key_obj.permissions or "").split(",") if s.strip()
        ]
        # admin.full has override for all scopes
        if "admin.full" in scopes or required_scope in scopes:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required API key permission scope: {required_scope}",
        )


api_key_service = APIKeyService()
