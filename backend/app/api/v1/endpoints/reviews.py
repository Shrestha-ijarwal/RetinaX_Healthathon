from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.patient import Patient
from backend.app.models.specialist_review import SpecialistReview
from backend.app.models.user import User
from backend.app.schemas.specialist_review import SpecialistReviewCreate, SpecialistReviewOut
from backend.app.services.auth_service import get_current_user, require_specialist
from backend.app.services.review_service import record_specialist_review

router = APIRouter()

@router.get("/queue", response_model=List[Dict[str, Any]])
def get_specialist_review_queue(
    status_filter: Optional[str] = Query("all", description="all, pending, completed"),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Patient)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Patient.name.ilike(s)) | (Patient.id.ilike(s)))

    patients = query.all()
    queue = []
    for p in patients:
        sr = p.specialist_review
        j = p.journey
        docs = [d for d in p.documents if d.doc_type == "Retinal Screening Report"]
        has_report = len(docs) > 0
        is_completed = bool(sr and sr.completed)

        state = "awaiting_specialist_review"
        if is_completed:
            state = sr.review_status if sr else "review_completed"
        elif has_report:
            state = "awaiting_specialist_review"
        elif j and j.screening_workflow == "Completed":
            state = "record_reconciliation_required"
        else:
            state = "awaiting_screening"

        if status_filter == "pending" and is_completed:
            continue
        if status_filter == "completed" and not is_completed:
            continue

        queue.append({
            "patient_id": p.id,
            "patient_name": p.name,
            "patient_age": p.age,
            "patient_sex": p.sex,
            "facility": p.facility,
            "review_state": state,
            "screening_report_available": has_report,
            "report_document_count": len(docs),
            "assigned_specialist": (sr.assigned_specialist if sr and sr.assigned_specialist else (j.assigned_to if j else "Unassigned")),
            "completed": is_completed,
            "review_status": sr.review_status if sr else state,
            "reconciliation_status": sr.reconciliation_status if sr else "Reconciled",
            "review_timestamp": sr.review_completed_at if sr else None
        })

    return queue

@router.get("/{patient_id}", response_model=Dict[str, Any])
def get_patient_review(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient {patient_id} not found.")

    sr = patient.specialist_review
    reports = [
        {
            "id": d.id,
            "title": d.title,
            "upload_date": d.upload_date,
            "source": d.source,
            "file_name": d.file_name,
            "storage_key": d.storage_key,
            "mime_type": d.mime_type
        } for d in patient.documents if d.doc_type == "Retinal Screening Report"
    ]

    return {
        "patient_id": patient.id,
        "patient_name": patient.name,
        "patient_age": patient.age,
        "patient_sex": patient.sex,
        "facility": patient.facility,
        "diabetes_profile": patient.diabetes_profile,
        "screening_reports": reports,
        "review": {
            "completed": sr.completed if sr else False,
            "review_status": sr.review_status if sr else "awaiting_specialist_review",
            "assigned_specialist": sr.assigned_specialist if sr else None,
            "clinician_title": sr.clinician_title if sr else "Dr.",
            "clinician_specialty": sr.clinician_specialty if sr else "Ophthalmology",
            "clinician_facility": sr.clinician_facility if sr else "District Eye Hospital",
            "registration_number": sr.registration_number if sr else "",
            "review_scheduled_date": sr.review_scheduled_date if sr else None,
            "review_completed_at": sr.review_completed_at if sr else None,
            "report_available": sr.report_available if sr else len(reports) > 0,
            "operational_notes": sr.operational_notes if sr else "",
            "clinician_instruction": sr.clinician_instruction if sr else "",
            "task_owner": sr.task_owner if sr else "Care Coordinator",
            "operational_task_status": sr.operational_task_status if sr else "Pending",
            "reconciliation_status": sr.reconciliation_status if sr else "Reconciled",
            "last_updated_at": sr.last_updated_at if sr else None
        } if sr else None
    }

@router.post("/{patient_id}", response_model=Dict[str, Any])
def submit_specialist_review(
    patient_id: str,
    review_data: SpecialistReviewCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_specialist)  # Backend-enforced Specialist RBAC!
):
    expected_version = review_data.expected_version
    if expected_version is None:
        hdr_ver = request.headers.get("X-Expected-Version")
        if hdr_ver is not None:
            try:
                expected_version = int(hdr_ver)
            except ValueError:
                pass

    review = record_specialist_review(
        db=db,
        patient_id=patient_id,
        data=review_data,
        current_user_name=current_user.full_name,
        current_user_role=current_user.role,
        expected_version=expected_version,
        ip_address=request.client.host if request.client else ""
    )
    return {
        "status": "success",
        "message": f"Specialist operational review successfully recorded and attributed to {review.assigned_specialist}.",
        "review_id": review.id,
        "patient_id": patient_id,
        "review_status": review.review_status
    }
