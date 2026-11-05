import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.patient import Patient
from backend.app.models.followup import Followup, ContactAttempt
from backend.app.models.timeline_event import TimelineEvent
from backend.app.schemas.followup import FollowupUpdate
from backend.app.services.audit_service import log_audit_event

def update_followup_status(
    db: Session,
    patient_id: str,
    data: FollowupUpdate,
    current_user_name: str,
    current_user_role: str,
    ip_address: str = ""
) -> Followup:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient {patient_id} not found.")

    fu = db.query(Followup).filter(Followup.patient_id == patient_id).first()
    if not fu:
        fu = Followup(patient_id=patient_id)
        db.add(fu)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    today_str = datetime.now().strftime("%Y-%m-%d")

    fu.status = data.status
    if data.planned_date is not None:
        fu.planned_date = data.planned_date
    if data.responsible_staff:
        fu.responsible_staff = data.responsible_staff
    if data.notes:
        fu.notes = data.notes

    if data.status == "Completed":
        fu.completion_timestamp = now_str
        if patient.journey:
            patient.journey.care_loop_completed = True
            patient.journey.overall_stage = "Care Loop Successfully Closed"
            patient.journey.next_workflow_action = "Annual routine screening due next cycle"

    # Contact attempt logging
    if data.contact_attempt:
        ca = ContactAttempt(
            patient_id=patient_id,
            followup_id=fu.id,
            date=today_str,
            method=data.contact_attempt.method,
            result=data.contact_attempt.result,
            staff=data.contact_attempt.staff or current_user_name,
            notes=data.contact_attempt.notes or ""
        )
        db.add(ca)

        if patient.journey:
            patient.journey.last_contact_date = today_str
            patient.journey.last_contact_method = data.contact_attempt.method

    # Update care journey followup status
    if patient.journey:
        patient.journey.followup_status = data.status
        if data.status == "Unable to Contact":
            patient.journey.next_workflow_action = "Re-engage patient via ASHA worker home visit"

    # Timeline event
    te = TimelineEvent(
        id=f"evt-{uuid.uuid4().hex[:8]}",
        patient_id=patient_id,
        stage=f"Follow-Up Status: {data.status}",
        timestamp=now_str,
        source="Care Coordination Desk",
        actor=current_user_name,
        status="Updated",
        note=data.notes or f"Follow-up status transitioned to {data.status}."
    )
    db.add(te)

    # Audit log
    log_audit_event(
        db=db,
        action="FOLLOWUP_STATUS_UPDATE",
        user_name=current_user_name,
        user_role=current_user_role,
        resource_type="Followup",
        resource_id=patient_id,
        details={"status": data.status, "planned_date": data.planned_date},
        ip_address=ip_address
    )

    db.commit()
    db.refresh(fu)
    return fu
