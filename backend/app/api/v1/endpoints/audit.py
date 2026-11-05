from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.audit_event import AuditEvent
from backend.app.models.user import User
from backend.app.schemas.audit import AuditEventOut
from backend.app.services.auth_service import require_admin

router = APIRouter()

@router.get("", response_model=List[AuditEventOut])
def list_audit_events(
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)  # Strictly restricted to Administrator!
):
    query = db.query(AuditEvent)

    if action:
        query = query.filter(AuditEvent.action.ilike(f"%{action}%"))

    if resource_type:
        query = query.filter(AuditEvent.resource_type == resource_type)

    events = query.order_by(AuditEvent.timestamp.desc()).limit(limit).all()
    return events
