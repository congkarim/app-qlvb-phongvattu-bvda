from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        actor_user_id: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user_id=actor_user_id,
            metadata_=metadata or {},
        )
        self.db.add(audit_log)
        self.db.flush()
        return audit_log

    def list_for_entity(self, *, entity_type: str, entity_id: str, limit: int = 50) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
                AuditLog.deleted_at.is_(None),
            )
            .options(selectinload(AuditLog.actor))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))
