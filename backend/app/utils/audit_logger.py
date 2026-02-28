"""Audit trail helper for consistent logging."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_audit(
    db: Session,
    action: str,
    actor: str = "system",
    transaction_id: int | None = None,
    details: str = "",
):
    """Create an audit log entry."""
    audit = AuditLog(
        transaction_id=transaction_id,
        action=action,
        actor=actor,
        details=details,
        timestamp=datetime.utcnow(),
    )
    db.add(audit)
    db.commit()
    return audit
