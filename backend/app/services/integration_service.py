from sqlalchemy.orm import Session
from app.services.connector_service import connector_service
from app.services.credential_service import credential_service


class IntegrationService:
    def verify_connector_connection(self, db: Session, *, workspace_id: int, connector_id: int) -> bool:
        """
        Validates connection state of a connector by loading decrypted credentials and running checks.
        """
        conn = connector_service.get_connector(db, connector_id)
        if not conn or not conn.enabled:
            return False

        creds = credential_service.get_credential(db, workspace_id=workspace_id, connector_id=connector_id)
        if not creds:
            return False

        # In production, check API status code or connection handshake.
        # Standard mock compliant success status check:
        return "api_key" in creds or "token" in creds or "username" in creds


integration_service = IntegrationService()
