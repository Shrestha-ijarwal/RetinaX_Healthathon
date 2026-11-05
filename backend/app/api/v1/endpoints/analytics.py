from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.patient import Patient
from backend.app.models.timeline_event import TimelineEvent
from backend.app.schemas.analytics import AnalyticsOut, GapRadarOut
from backend.app.services.auth_service import get_current_user, require_coordinator
from backend.app.services.analytics_service import (
    calculate_operational_analytics,
    get_gap_radar_analysis,
    get_reconciliation_queue
)
from backend.app.services.audit_service import log_audit_event

router = APIRouter()

@router.get("", response_model=Dict[str, Any])
def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return calculate_operational_analytics(db)

@router.get("/gap-radar", response_model=Dict[str, Any])
def get_gap_radar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_gap_radar_analysis(db)

@router.get("/reconciliation", response_model=List[Dict[str, Any]])
def get_reconciliation_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_reconciliation_queue(db)

@router.post("/reconciliation/{patient_id}/resolve", response_model=Dict[str, Any])
def resolve_reconciliation_item(
    patient_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return {"status": "error", "message": f"Patient {patient_id} not found"}

    te = TimelineEvent(
        id=f"evt-{patient_id}-reconcile",
        patient_id=patient_id,
        stage="Record Reconciled",
        timestamp=request.headers.get("date", "2026-11-05 18:00"),
        source="Reconciliation Desk",
        actor=current_user.full_name,
        status="Resolved",
        note="Care discrepancy audited and marked resolved by coordinator."
    )
    db.add(te)

    log_audit_event(
        db=db,
        action="RECONCILIATION_RESOLVED",
        user_name=current_user.full_name,
        user_role=current_user.role,
        user_id=str(current_user.id),
        resource_type="Patient",
        resource_id=patient_id,
        details={"reconciliation_status": "Resolved"},
        ip_address=request.client.host if request.client else ""
    )

    db.commit()
    return {
        "status": "success",
        "message": f"Operational record for patient {patient_id} marked as reconciled."
    }
