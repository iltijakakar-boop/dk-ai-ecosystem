import hashlib
import secrets
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.organization import ServiceAccount


class ServiceAccountService:
    def create_service_account(
        self,
        db: Session,
        *,
        workspace_id: int,
        name: str,
        description: Optional[str] = None,
        permissions: Optional[List[str]] = None,
    ) -> tuple[str, ServiceAccount]:
        secret_part = secrets.token_hex(16)
        clear_token = f"dk_sa_{secret_part}"

        token_hash = hashlib.sha256(clear_token.encode()).hexdigest()
        perms_str = ",".join(permissions) if permissions else ""

        sa_obj = ServiceAccount(
            workspace_id=workspace_id,
            name=name,
            description=description,
            token_hash=token_hash,
            permissions=perms_str,
            status="Active",
        )
        db.add(sa_obj)
        db.commit()
        db.refresh(sa_obj)

        return clear_token, sa_obj

    def verify_token(self, db: Session, *, clear_token: str) -> ServiceAccount:
        if not clear_token.startswith("dk_sa_"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Service Account token format.",
            )

        token_hash = hashlib.sha256(clear_token.encode()).hexdigest()
        sa_obj = (
            db.query(ServiceAccount)
            .filter(
                ServiceAccount.token_hash == token_hash,
                ServiceAccount.status == "Active",
            )
            .first()
        )

        if not sa_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive Service Account token.",
            )

        return sa_obj

    def check_scope(self, sa_obj: ServiceAccount, required_scope: str) -> None:
        scopes = [s.strip() for s in (sa_obj.permissions or "").split(",") if s.strip()]
        if "admin.full" in scopes or required_scope in scopes:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required service account scope: {required_scope}",
        )


service_account_service = ServiceAccountService()
