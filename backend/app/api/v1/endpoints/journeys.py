from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.patient import Patient
from backend.app.models.care_journey import CareJourney
from backend.app.models.user import User
from backend.app.schemas.care_journey import CareJourneyOut, CareJourneyUpdate
from backend.app.services.auth_service import get_current_user, require_coordinator

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
def list_care_journeys(
    search: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    completed: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(CareJourney).join(Patient)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Patient.name.ilike(s)) | (Patient.id.ilike(s)))

    if stage and stage != "All":
        query = query.filter(CareJourney.overall_stage.ilike(f"%{stage}%"))

    if completed is not None:
        query = query.filter(CareJourney.care_loop_completed == completed)

    journeys = query.all()
    results = []
    for j in journeys:
        p = j.patient
        # calculate journey progress percentage (out of 4 core phases: Screening, Report, Specialist Review, Followup)
        steps_done = 0
        if j.screening_workflow == "Completed":
            steps_done += 1
        if any(d.doc_type == "Retinal Screening Report" for d in p.documents):
            steps_done += 1
        if p.specialist_review and p.specialist_review.completed:
            steps_done += 1
        if j.care_loop_completed or (p.followup and p.followup.status == "Completed"):
            steps_done += 1
        progress_pct = int((steps_done / 4) * 100)

        results.append({
            "id": j.id,
            "patient_id": p.id,
            "patient_name": p.name,
            "patient_age": p.age,
            "patient_sex": p.sex,
            "facility": p.facility,
            "overall_stage": j.overall_stage,
            "screening_workflow": j.screening_workflow,
            "screening_appointment_date": j.screening_appointment_date,
            "document_status": j.document_status,
            "specialist_review": j.specialist_review,
            "followup_status": j.followup_status,
            "care_loop_completed": j.care_loop_completed,
            "next_workflow_action": j.next_workflow_action,
            "assigned_to": j.assigned_to,
            "due_date": j.due_date,
            "progress_percentage": progress_pct
        })
    return results

@router.get("/{patient_id}", response_model=Dict[str, Any])
def get_patient_journey(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient or not patient.journey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Journey not found for patient {patient_id}")
    
    j = patient.journey
    steps_done = 0
    if j.screening_workflow == "Completed":
        steps_done += 1
    if any(d.doc_type == "Retinal Screening Report" for d in patient.documents):
        steps_done += 1
    if patient.specialist_review and patient.specialist_review.completed:
        steps_done += 1
    if j.care_loop_completed or (patient.followup and patient.followup.status == "Completed"):
        steps_done += 1
    progress_pct = int((steps_done / 4) * 100)

    return {
        "id": j.id,
        "patient_id": patient.id,
        "patient_name": patient.name,
        "facility": patient.facility,
        "overall_stage": j.overall_stage,
        "screening_workflow": j.screening_workflow,
        "screening_appointment_date": j.screening_appointment_date,
        "document_status": j.document_status,
        "specialist_review": j.specialist_review,
        "followup_status": j.followup_status,
        "care_loop_completed": j.care_loop_completed,
        "next_workflow_action": j.next_workflow_action,
        "assigned_to": j.assigned_to,
        "due_date": j.due_date,
        "progress_percentage": progress_pct,
        "timeline_count": len(patient.timeline_events),
        "document_count": len(patient.documents)
    }

@router.patch("/{patient_id}", response_model=Dict[str, Any])
def update_patient_journey(
    patient_id: str,
    data: CareJourneyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient or not patient.journey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Journey not found for patient {patient_id}")

    j = patient.journey
    if data.overall_stage is not None:
        j.overall_stage = data.overall_stage
    if data.screening_workflow is not None:
        j.screening_workflow = data.screening_workflow
    if data.screening_appointment_date is not None:
        j.screening_appointment_date = data.screening_appointment_date
    if data.followup_status is not None:
        j.followup_status = data.followup_status
    if data.care_loop_completed is not None:
        j.care_loop_completed = data.care_loop_completed
    if data.next_workflow_action is not None:
        j.next_workflow_action = data.next_workflow_action
    if data.assigned_to is not None:
        j.assigned_to = data.assigned_to
    if data.due_date is not None:
        j.due_date = data.due_date

    db.commit()
    db.refresh(j)
    return {"message": "Care journey updated successfully."}
