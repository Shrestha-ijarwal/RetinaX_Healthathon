from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.audit_event import AuditEvent

def log_audit_event(
    db: Session,
    action: str,
    user_name: str = "System",
    user_role: str = "System",
    user_id: Optional[str] = None,
    resource_type: str = "",
    resource_id: str = "",
    details: Optional[Dict[str, Any]] = None,
    ip_address: str = ""
) -> AuditEvent:
    event = AuditEvent(
        user_id=str(user_id) if user_id else None,
        user_name=user_name,
        user_role=user_role,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        details=details or {},
        ip_address=ip_address,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(event)
    db.commit()
    return event
