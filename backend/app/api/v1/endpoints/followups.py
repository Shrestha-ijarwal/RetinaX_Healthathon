from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.patient import Patient
from backend.app.models.followup import Followup
from backend.app.models.user import User
from backend.app.schemas.followup import FollowupUpdate, FollowupOut, ContactAttemptCreate
from backend.app.services.auth_service import get_current_user, require_coordinator
from backend.app.services.followup_service import update_followup_status, record_contact_attempt

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
def list_followups_worklist(
    status_filter: Optional[str] = Query(None, description="Pending, Scheduled, Completed, Unable to Contact"),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Patient)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Patient.name.ilike(s)) | (Patient.id.ilike(s)))

    patients = query.all()
    worklist = []

    for p in patients:
        fu = p.followup
        j = p.journey
        if not fu:
            continue

        if status_filter and status_filter != "All" and fu.status.lower() != status_filter.lower():
            continue

        worklist.append({
            "patient_id": p.id,
            "patient_name": p.name,
            "patient_age": p.age,
            "patient_sex": p.sex,
            "contact": p.contact,
            "facility": p.facility,
            "followup_status": fu.status,
            "planned_date": fu.planned_date,
            "responsible_staff": fu.responsible_staff or (j.assigned_to if j else "Coordinator"),
            "contact_attempts_count": len(fu.contact_attempts),
            "last_contact_attempt": (
                {
                    "date": fu.contact_attempts[0].date,
                    "method": fu.contact_attempts[0].method,
                    "result": fu.contact_attempts[0].result
                } if fu.contact_attempts else None
            ),
            "care_loop_completed": j.care_loop_completed if j else False,
            "specialist_directive": p.specialist_review.clinician_instruction if p.specialist_review else "Awaiting Directive",
            "review_status": p.specialist_review.review_status if p.specialist_review else "awaiting_specialist_review"
        })

    return worklist

@router.get("/{patient_id}", response_model=Dict[str, Any])
def get_patient_followup(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient or not patient.followup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Follow-up record for patient {patient_id} not found.")

    fu = patient.followup
    return {
        "patient_id": patient.id,
        "patient_name": patient.name,
        "contact": patient.contact,
        "facility": patient.facility,
        "status": fu.status,
        "planned_date": fu.planned_date,
        "responsible_staff": fu.responsible_staff,
        "completion_timestamp": fu.completion_timestamp,
        "notes": fu.notes,
        "contact_attempts": [
            {
                "id": ca.id,
                "date": ca.date,
                "method": ca.method,
                "result": ca.result,
                "staff": ca.staff,
                "notes": ca.notes
            } for ca in fu.contact_attempts
        ]
    }

@router.post("/{patient_id}", response_model=Dict[str, Any])
def update_patient_followup(
    patient_id: str,
    data: FollowupUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    expected_version = data.expected_version
    if expected_version is None:
        hdr_ver = request.headers.get("X-Expected-Version")
        if hdr_ver is not None:
            try:
                expected_version = int(hdr_ver)
            except ValueError:
                pass

    fu = update_followup_status(
        db=db,
        patient_id=patient_id,
        data=data,
        current_user_name=current_user.full_name,
        current_user_role=current_user.role,
        expected_version=expected_version,
        ip_address=request.client.host if request.client else ""
    )
    return {
        "status": "success",
        "message": f"Follow-up status successfully updated to {fu.status}.",
        "followup_status": fu.status,
        "planned_date": fu.planned_date
    }

@router.post("/{patient_id}/attempts", response_model=Dict[str, Any])
def add_patient_contact_attempt(
    patient_id: str,
    data: ContactAttemptCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    ca = record_contact_attempt(
        db=db,
        patient_id=patient_id,
        data=data,
        current_user_name=current_user.full_name,
        current_user_role=current_user.role,
        ip_address=request.client.host if request.client else ""
    )
    return {
        "status": "success",
        "message": f"Contact attempt logged successfully for patient {patient_id}.",
        "attempt_id": ca.id,
        "result": ca.result
    }
