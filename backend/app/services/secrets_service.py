import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.organization import Secret, SecretVersion

# Generate a valid Fernet key from the settings string
key_bytes = settings.SECRETS_ENCRYPTION_KEY.encode()
fernet_key = base64.urlsafe_b64encode(hashlib.sha256(key_bytes).digest())
cipher = Fernet(fernet_key)


class SecretsService:
    def encrypt_value(self, value: str) -> str:
        return cipher.encrypt(value.encode()).decode()

    def decrypt_value(self, encrypted_val: str) -> str:
        try:
            return cipher.decrypt(encrypted_val.encode()).decode()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to decrypt secret value. Key may have changed.",
            )

    def create_secret(
        self,
        db: Session,
        *,
        workspace_id: int,
        name: str,
        value: str,
        category: Optional[str] = None,
    ) -> Secret:
        # Check uniqueness in workspace
        existing = (
            db.query(Secret)
            .filter(Secret.workspace_id == workspace_id, Secret.name == name)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Secret with this name already exists in this workspace.",
            )

        encrypted = self.encrypt_value(value)
        secret_obj = Secret(
            workspace_id=workspace_id,
            name=name,
            encrypted_value=encrypted,
            version=1,
            category=category,
        )
        db.add(secret_obj)
        db.commit()
        db.refresh(secret_obj)

        # Log initial version history
        ver_obj = SecretVersion(
            secret_id=secret_obj.id, encrypted_value=encrypted, version=1
        )
        db.add(ver_obj)
        db.commit()

        return secret_obj

    def update_secret(self, db: Session, *, secret_id: int, value: str) -> Secret:
        secret_obj = db.query(Secret).filter(Secret.id == secret_id).first()
        if not secret_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Secret not found."
            )

        new_version = secret_obj.version + 1
        encrypted = self.encrypt_value(value)

        secret_obj.encrypted_value = encrypted
        secret_obj.version = new_version
        db.commit()

        # Log new version history
        ver_obj = SecretVersion(
            secret_id=secret_obj.id, encrypted_value=encrypted, version=new_version
        )
        db.add(ver_obj)
        db.commit()
        db.refresh(secret_obj)

        return secret_obj

    def rollback_secret(
        self, db: Session, *, secret_id: int, target_version: int
    ) -> Secret:
        secret_obj = db.query(Secret).filter(Secret.id == secret_id).first()
        if not secret_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Secret not found."
            )

        ver_obj = (
            db.query(SecretVersion)
            .filter(
                SecretVersion.secret_id == secret_id,
                SecretVersion.version == target_version,
            )
            .first()
        )
        if not ver_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Secret version {target_version} not found in history.",
            )

        new_version = secret_obj.version + 1
        secret_obj.encrypted_value = ver_obj.encrypted_value
        secret_obj.version = new_version
        db.commit()

        # Log new version history representing the rollback
        new_ver_obj = SecretVersion(
            secret_id=secret_obj.id,
            encrypted_value=ver_obj.encrypted_value,
            version=new_version,
        )
        db.add(new_ver_obj)
        db.commit()
        db.refresh(secret_obj)

        return secret_obj


# Initialize key mapping on load
secrets_service = SecretsService()
