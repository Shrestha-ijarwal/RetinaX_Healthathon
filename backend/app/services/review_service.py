import uuid
from datetime import datetime
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
    expected_version: Optional[int] = None,
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
        review = SpecialistReview(patient_id=patient_id, version=1)
        db.add(review)
        db.flush()

    eff_version = expected_version if expected_version is not None else data.expected_version
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    update_dict = {
        "completed": True,
        "review_status": data.review_status or "review_completed",
        "assigned_specialist": data.assigned_specialist,
        "clinician_title": data.clinician_title or "Dr.",
        "clinician_specialty": data.clinician_specialty or "Ophthalmology",
        "clinician_facility": data.clinician_facility or "District Eye Hospital",
        "registration_number": data.registration_number or "",
        "review_completed_at": now_str,
        "report_available": True,
        "operational_notes": data.operational_notes,
        "clinician_instruction": data.clinician_instruction,
        "task_owner": data.task_owner or "Care Coordinator",
        "operational_task_status": data.operational_task_status or "In Progress",
        "reconciliation_status": data.reconciliation_status or "Reconciled",
        "last_updated_at": now_str,
        "version": (eff_version + 1) if eff_version is not None else SpecialistReview.version + 1
    }

    # Atomic conditional update at DB engine level
    query = db.query(SpecialistReview).filter(SpecialistReview.patient_id == patient_id)
    if eff_version is not None:
        query = query.filter(SpecialistReview.version == eff_version)

    rows_affected = query.update(update_dict, synchronize_session=False)
    if rows_affected == 0:
        db.rollback()
        existing_rev = db.query(SpecialistReview).filter(SpecialistReview.patient_id == patient_id).first()
        current_v = existing_rev.version if existing_rev else 1
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "VERSION_CONFLICT",
                "message": f"Specialist review record for patient {patient_id} has been modified concurrently.",
                "current_version": current_v,
                "expected_version": eff_version,
                "review_status": existing_rev.review_status if existing_rev else None,
                "last_updated_at": existing_rev.last_updated_at if existing_rev else None
            }
        )

    review = db.query(SpecialistReview).filter(SpecialistReview.patient_id == patient_id).first()

    # Advance Care Journey operationally
    journey = patient.journey
    if journey:
        journey.specialist_review = "Completed"
        journey.overall_stage = "Specialist Review Completed"
        journey.next_workflow_action = "Coordinate operational follow-up per clinician directive"

        if data.review_status == "followup_completed":
            journey.care_loop_completed = True
            journey.overall_stage = "Care Loop Successfully Closed"
            journey.followup_status = "Completed"
        else:
            journey.followup_status = "Pending"

    # Update document review state
    for doc in patient.documents:
        if doc.doc_type == "Retinal Screening Report":
            doc.review_status = "Reviewed by Specialist"

    # Complete existing specialist review operational tasks
    for tsk in patient.tasks:
        if "review" in tsk.title.lower() and tsk.status == "Open":
            tsk.status = "Completed"
            tsk.completed_at = now_str

    # Create operational follow-up task based on attributed clinician directive
    if data.clinician_instruction:
        task_id = f"tsk-{patient_id}-{uuid.uuid4().hex[:6]}"
        followup_task = OperationalTask(
            id=task_id,
            patient_id=patient_id,
            title=f"Follow-Up Coordination ({patient_id})",
            description=f"Coordinate patient follow-up per clinician directive: {data.clinician_instruction}",
            source=f"Clinician Directive ({data.assigned_specialist})",
            entered_by=data.assigned_specialist,
            clinician_specialty=review.clinician_specialty,
            clinician_facility=review.clinician_facility,
            assigned_to=review.task_owner or "Care Coordinator",
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
        actor=f"{data.assigned_specialist} ({review.clinician_specialty})",
        status="Completed",
        note=f"Specialist operational review signed off by {data.assigned_specialist}. Directive logged."
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
            "specialist": data.assigned_specialist,
            "review_status": review.review_status,
            "registration": data.registration_number,
            "reconciliation": review.reconciliation_status,
            "version": review.version
        },
        ip_address=ip_address
    )

    db.commit()
    db.refresh(review)
    return review
