from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.patient import Patient
from backend.app.models.user import User
from backend.app.schemas.patient import PatientCreate, PatientOut, PatientDetailOut, CompletenessCheckOut
from backend.app.services.auth_service import get_current_user, require_coordinator
from backend.app.services.patient_service import (
    get_patients_list,
    get_patient_detail,
    create_patient_record,
    calculate_record_completeness
)
from backend.app.services.audit_service import log_audit_event
from backend.app.db.seed import seed_synthetic_patients

router = APIRouter()

def format_patient_dict(p: Patient) -> dict:
    comp = calculate_record_completeness(p)
    return {
        "id": p.id,
        "name": p.name,
        "age": p.age,
        "sex": p.sex,
        "contact": p.contact,
        "facility": p.facility,
        "clinician": p.clinician,
        "registration_date": p.registration_date,
        "diabetes_profile": p.diabetes_profile or {},
        "workflow_status": {
            "overall_stage": p.journey.overall_stage if p.journey else "",
            "screening_workflow": p.journey.screening_workflow if p.journey else "Not Started",
            "screening_appointment_date": p.journey.screening_appointment_date if p.journey else None,
            "document_status": p.journey.document_status if p.journey else "No Documents",
            "specialist_review": p.journey.specialist_review if p.journey else "Not Started",
            "followup_status": p.journey.followup_status if p.journey else "Pending",
            "care_loop_completed": p.journey.care_loop_completed if p.journey else False,
            "next_workflow_action": p.journey.next_workflow_action if p.journey else "",
            "assigned_to": p.journey.assigned_to if p.journey else "",
            "due_date": p.journey.due_date if p.journey else None,
            "last_contact_date": p.journey.last_contact_date if p.journey else None,
            "last_contact_method": p.journey.last_contact_method if p.journey else None,
        } if p.journey else None,
        "completeness_score": comp["score_percentage"]
    }

def format_patient_detail_dict(p: Patient) -> dict:
    base = format_patient_dict(p)
    base["timeline"] = [
        {
            "id": t.id,
            "stage": t.stage,
            "timestamp": t.timestamp,
            "source": t.source,
            "actor": t.actor,
            "status": t.status,
            "note": t.note
        } for t in p.timeline_events
    ]
    base["documents"] = [
        {
            "id": d.id,
            "title": d.title,
            "doc_type": d.doc_type,
            "upload_date": d.upload_date,
            "source": d.source,
            "review_status": d.review_status,
            "file_name": d.file_name,
            "size_kb": d.size_bytes // 1024,
            "storage_key": d.storage_key,
            "mime_type": d.mime_type
        } for d in p.documents
    ]
    base["specialist_review"] = {
        "completed": p.specialist_review.completed if p.specialist_review else False,
        "clinician_name": p.specialist_review.clinician_name if p.specialist_review else None,
        "clinician_title": p.specialist_review.clinician_title if p.specialist_review else None,
        "clinician_specialty": p.specialist_review.clinician_specialty if p.specialist_review else None,
        "clinician_facility": p.specialist_review.clinician_facility if p.specialist_review else None,
        "registration_number": p.specialist_review.registration_number if p.specialist_review else None,
        "review_timestamp": p.specialist_review.review_timestamp if p.specialist_review else None,
        "clinical_assessment": p.specialist_review.clinical_assessment if p.specialist_review else "",
        "followup_instructions": p.specialist_review.followup_instructions if p.specialist_review else "",
        "referral_status": p.specialist_review.referral_status if p.specialist_review else "Awaiting Review",
        "notes": p.specialist_review.notes if p.specialist_review else ""
    } if p.specialist_review else None

    base["pending_tasks"] = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "source": t.source,
            "entered_by": t.entered_by,
            "clinician_specialty": t.clinician_specialty,
            "clinician_facility": t.clinician_facility,
            "assigned_to": t.assigned_to,
            "due_date": t.due_date,
            "status": t.status,
            "priority": t.priority,
            "created_at": t.created_at,
            "completed_at": t.completed_at
        } for t in p.tasks
    ]

    base["followup"] = {
        "status": p.followup.status if p.followup else "Pending",
        "planned_date": p.followup.planned_date if p.followup else None,
        "responsible_staff": p.followup.responsible_staff if p.followup else "",
        "completion_timestamp": p.followup.completion_timestamp if p.followup else None,
        "notes": p.followup.notes if p.followup else "",
        "contact_attempts": [
            {
                "id": ca.id,
                "date": ca.date,
                "method": ca.method,
                "result": ca.result,
                "staff": ca.staff,
                "notes": ca.notes
            } for ca in (p.followup.contact_attempts if p.followup else [])
        ]
    } if p.followup else None

    base["reminders"] = [
        {
            "id": r.id,
            "type": r.type,
            "language": r.language,
            "text": r.text_en,
            "text_hi": r.text_hi,
            "sent_status": r.sent_status,
            "scheduled_for": r.scheduled_for,
            "channel": r.channel
        } for r in p.reminders
    ]
    return base

@router.get("", response_model=Dict[str, Any])
def list_patients(
    search: Optional[str] = Query(None, description="Search by name, ID, facility, contact"),
    filter: Optional[str] = Query("all", description="Operational filter e.g. needs_attention, report_missing, etc."),
    facility: Optional[str] = Query(None, description="Filter by healthcare facility"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patients, metrics, total = get_patients_list(
        db=db,
        search=search,
        filter_mode=filter,
        facility=facility,
        skip=skip,
        limit=limit
    )

    return {
        "patients": [format_patient_dict(p) for p in patients],
        "metrics": metrics,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/{patient_id}", response_model=Dict[str, Any])
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = get_patient_detail(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found."
        )
    return format_patient_detail_dict(patient)

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_patient(
    patient_data: PatientCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    patient = create_patient_record(db, patient_data, created_by=current_user.full_name)
    log_audit_event(
        db=db,
        action="PATIENT_CREATED",
        user_name=current_user.full_name,
        user_role=current_user.role,
        user_id=str(current_user.id),
        resource_type="Patient",
        resource_id=patient.id,
        details={"name": patient.name, "facility": patient.facility},
        ip_address=request.client.host if request.client else ""
    )
    return format_patient_detail_dict(patient)

@router.get("/{patient_id}/completeness", response_model=CompletenessCheckOut)
def get_completeness(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = get_patient_detail(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found."
        )
    return calculate_record_completeness(patient)

@router.post("/reset", response_model=Dict[str, Any])
def reset_synthetic_cohort(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = seed_synthetic_patients(db, force_reset=True)
    log_audit_event(
        db=db,
        action="SYNTHETIC_COHORT_RESET",
        user_name=current_user.full_name,
        user_role=current_user.role,
        user_id=str(current_user.id),
        resource_type="Cohort",
        resource_id="synthetic_patients",
        details=result,
        ip_address=request.client.host if request.client else ""
    )
    return {
        "status": "success",
        "message": "Synthetic demonstration cohort successfully reset to seed state.",
        "details": result
    }
