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

        state = "Not Ready (Awaiting Screening)"
        if is_completed:
            state = "Completed"
        elif has_report:
            state = "Pending Review"
        elif j and j.screening_workflow == "Completed":
            state = "Awaiting Report Dossier"

        if status_filter == "pending" and state != "Pending Review":
            continue
        if status_filter == "completed" and state != "Completed":
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
            "assigned_specialist": (sr.clinician_name if sr and sr.clinician_name else (j.assigned_to if j else "Unassigned")),
            "completed": is_completed,
            "referral_status": sr.referral_status if sr else "Awaiting Review",
            "review_timestamp": sr.review_timestamp if sr else None
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
            "clinician_name": sr.clinician_name if sr else None,
            "clinician_title": sr.clinician_title if sr else "Dr.",
            "clinician_specialty": sr.clinician_specialty if sr else "Ophthalmology",
            "clinician_facility": sr.clinician_facility if sr else "District Eye Hospital",
            "registration_number": sr.registration_number if sr else "",
            "review_timestamp": sr.review_timestamp if sr else None,
            "clinical_assessment": sr.clinical_assessment if sr else "",
            "followup_instructions": sr.followup_instructions if sr else "",
            "referral_status": sr.referral_status if sr else "Awaiting Review",
            "notes": sr.notes if sr else ""
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
    review = record_specialist_review(
        db=db,
        patient_id=patient_id,
        data=review_data,
        current_user_name=current_user.full_name,
        current_user_role=current_user.role,
        ip_address=request.client.host if request.client else ""
    )
    return {
        "status": "success",
        "message": f"Specialist review successfully recorded and attributed to {review.clinician_name}.",
        "review_id": review.id,
        "patient_id": patient_id,
        "referral_status": review.referral_status
    }
