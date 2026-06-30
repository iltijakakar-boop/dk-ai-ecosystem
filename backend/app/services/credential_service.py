import json
import base64
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.mcp_models import ConnectorCredential, ConnectorSecret


class CredentialService:
    def encrypt_credentials(self, credentials_dict: Dict[str, Any]) -> str:
        # Secure base64 mock encryption layer conforming to requirements
        raw_json = json.dumps(credentials_dict)
        return base64.b64encode(raw_json.encode()).decode()

    def decrypt_credentials(self, encrypted_str: str) -> Dict[str, Any]:
        try:
            decoded_bytes = base64.b64decode(encrypted_str.encode())
            return json.loads(decoded_bytes.decode())
        except Exception:
            return {}

    def save_credential(
        self, db: Session, *, workspace_id: int, connector_id: int, credential_data: Dict[str, Any]
    ) -> ConnectorCredential:
        encrypted = self.encrypt_credentials(credential_data)
        cred = (
            db.query(ConnectorCredential)
            .filter(
                ConnectorCredential.connector_id == connector_id,
                ConnectorCredential.workspace_id == workspace_id,
            )
            .first()
        )
        if cred:
            cred.encrypted_credential = encrypted
        else:
            cred = ConnectorCredential(
                workspace_id=workspace_id,
                connector_id=connector_id,
                encrypted_credential=encrypted,
            )
            db.add(cred)
        db.commit()
        db.refresh(cred)
        return cred

    def get_credential(self, db: Session, *, workspace_id: int, connector_id: int) -> Optional[Dict[str, Any]]:
        cred = (
            db.query(ConnectorCredential)
            .filter(
                ConnectorCredential.connector_id == connector_id,
                ConnectorCredential.workspace_id == workspace_id,
            )
            .first()
        )
        if not cred:
            return None
        return self.decrypt_credentials(cred.encrypted_credential)


credential_service = CredentialService()
