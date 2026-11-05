import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.patient import Patient
from backend.app.models.specialist_review import SpecialistReview
from backend.app.models.care_journey import CareJourney
from backend.app.models.timeline_event import TimelineEvent
from backend.app.models.operational_task import OperationalTask
from backend.app.models.followup import Followup
from backend.app.schemas.specialist_review import SpecialistReviewCreate
from backend.app.services.audit_service import log_audit_event

def record_specialist_review(
    db: Session,
    patient_id: str,
    data: SpecialistReviewCreate,
    current_user_name: str,
    current_user_role: str,
    ip_address: str = ""
) -> SpecialistReview:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found."
        )

    review = db.query(SpecialistReview).filter(SpecialistReview.patient_id == patient_id).first()
    if not review:
        review = SpecialistReview(patient_id=patient_id)
        db.add(review)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Update review with mandatory clinician attribution
    review.completed = True
    review.clinician_name = data.clinician_name
    review.clinician_title = data.clinician_title or "Dr."
    review.clinician_specialty = data.clinician_specialty or "Ophthalmology"
    review.clinician_facility = data.clinician_facility or "District Eye Hospital"
    review.registration_number = data.registration_number or ""
    review.review_timestamp = now_str
    review.clinical_assessment = data.clinical_assessment
    review.followup_instructions = data.followup_instructions
    review.referral_status = data.referral_status
    review.notes = data.notes or f"Clinical review entered manually by {data.clinician_name} ({review.clinician_specialty})."

    # Advance Care Journey
    journey = patient.journey
    if journey:
        journey.specialist_review = "Completed"
        journey.overall_stage = "Specialist Review Completed"
        journey.next_workflow_action = f"Coordinate follow-up ({data.referral_status})"

        # Check if referral is annual routine and care loop can be marked completed
        if "routine annual" in data.referral_status.lower() or "annual routine" in data.referral_status.lower():
            journey.care_loop_completed = True
            journey.overall_stage = "Care Loop Successfully Closed (Annual)"
            journey.followup_status = "Completed"
        else:
            journey.followup_status = "Pending"

    # Update Document review status
    for doc in patient.documents:
        if doc.doc_type == "Retinal Screening Report":
            doc.review_status = "Reviewed by Specialist"

    # Complete any existing specialist review task
    for tsk in patient.tasks:
        if "review" in tsk.title.lower() and tsk.status == "Open":
            tsk.status = "Completed"
            tsk.completed_at = now_str

    # Create operational follow-up task based on clinician directive
    if data.followup_instructions:
        task_id = f"tsk-{patient_id}-{int(datetime.now().timestamp())}"
        followup_task = OperationalTask(
            id=task_id,
            patient_id=patient_id,
            title=f"Follow-Up Coordination ({data.referral_status})",
            description=f"Coordinate patient follow-up per clinician instructions: {data.followup_instructions}",
            source=f"Clinician Instruction ({data.clinician_name})",
            entered_by=data.clinician_name,
            clinician_specialty=review.clinician_specialty,
            clinician_facility=review.clinician_facility,
            assigned_to="Care Coordinator",
            due_date=None,
            status="Open",
            priority="High",
            created_at=datetime.now().strftime("%Y-%m-%d")
        )
        db.add(followup_task)

    # Log attributed timeline event
    te = TimelineEvent(
        id=f"evt-{uuid.uuid4().hex[:8]}",
        patient_id=patient_id,
        stage="Specialist Review Completed",
        timestamp=now_str,
        source="Specialist Review Portal",
        actor=f"{data.clinician_name} ({review.clinician_specialty})",
        status="Completed",
        note=f"Specialist review recorded by {data.clinician_name}. Directive: {data.referral_status}."
    )
    db.add(te)

    # Audit Trail
    log_audit_event(
        db=db,
        action="SPECIALIST_REVIEW_COMPLETED",
        user_name=current_user_name,
        user_role=current_user_role,
        resource_type="SpecialistReview",
        resource_id=patient_id,
        details={
            "clinician": data.clinician_name,
            "referral_status": data.referral_status,
            "registration": data.registration_number
        },
        ip_address=ip_address
    )

    db.commit()
    db.refresh(review)
    return review
