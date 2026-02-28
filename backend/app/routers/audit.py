"""Audit log viewer endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog
from app.schemas import AuditLogRead

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("/logs", response_model=list[AuditLogRead])
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    action: str | None = None,
    transaction_id: int | None = None,
    db: Session = Depends(get_db),
):
    """View the audit trail with optional filters."""
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action)
    if transaction_id is not None:
        query = query.filter(AuditLog.transaction_id == transaction_id)

    return query.order_by(AuditLog.id.desc()).offset(skip).limit(limit).all()
