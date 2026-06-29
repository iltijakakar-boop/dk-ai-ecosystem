from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.repositories.base import CRUDBase


class AuditLogRepository(CRUDBase[AuditLog]):
    def create_log(
        self,
        db: Session,
        *,
        user_id: int = None,
        target_id: int = None,
        resource: str = None,
        action: str,
        ip_address: str = None,
        user_agent: str = None,
        details: str = None
    ) -> AuditLog:
        db_obj = AuditLog(
            user_id=user_id,
            target_id=target_id,
            resource=resource,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


audit_log_repository = AuditLogRepository(AuditLog)
