from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.mcp_models import Connector


class ConnectorService:
    def create_connector(
        self, db: Session, *, workspace_id: int, name: str, connector_type: str, enabled: bool = True
    ) -> Connector:
        conn = Connector(
            workspace_id=workspace_id,
            name=name,
            type=connector_type,
            enabled=enabled
        )
        db.add(conn)
        db.commit()
        db.refresh(conn)
        return conn

    def get_connectors(self, db: Session, workspace_id: int) -> List[Connector]:
        return db.query(Connector).filter(Connector.workspace_id == workspace_id).all()

    def get_connector(self, db: Session, connector_id: int) -> Optional[Connector]:
        return db.query(Connector).filter(Connector.id == connector_id).first()

    def toggle_connector(self, db: Session, *, connector_id: int, enabled: bool) -> Connector:
        conn = self.get_connector(db, connector_id)
        if not conn:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found.")
        conn.enabled = enabled
        db.commit()
        db.refresh(conn)
        return conn


connector_service = ConnectorService()
