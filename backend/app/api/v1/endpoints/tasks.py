from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.patient import Patient
from backend.app.models.operational_task import OperationalTask
from backend.app.models.user import User
from backend.app.schemas.operational_task import OperationalTaskCreate, TaskCompleteRequest, OperationalTaskOut
from backend.app.services.auth_service import get_current_user, require_coordinator
from backend.app.services.task_service import create_task, complete_task

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
def list_tasks(
    status_filter: Optional[str] = Query(None, description="Open, Completed"),
    patient_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(OperationalTask).join(Patient)

    if patient_id:
        query = query.filter(OperationalTask.patient_id == patient_id)

    if status_filter and status_filter != "All":
        query = query.filter(OperationalTask.status.ilike(status_filter))

    tasks = query.order_by(OperationalTask.status.desc(), OperationalTask.created_at.desc()).all()
    results = []
    for t in tasks:
        p = t.patient
        results.append({
            "id": t.id,
            "patient_id": t.patient_id,
            "patient_name": p.name if p else "Unknown",
            "facility": p.facility if p else "",
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
        })
    return results

@router.post("/{patient_id}", response_model=OperationalTaskOut, status_code=status.HTTP_201_CREATED)
def add_patient_task(
    patient_id: str,
    data: OperationalTaskCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    return create_task(
        db=db,
        patient_id=patient_id,
        data=data,
        current_user_name=current_user.full_name,
        current_user_role=current_user.role,
        ip_address=request.client.host if request.client else ""
    )

@router.post("/{patient_id}/tasks/{task_id}/complete", response_model=OperationalTaskOut)
def finish_patient_task(
    patient_id: str,
    task_id: str,
    body: TaskCompleteRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    return complete_task(
        db=db,
        patient_id=patient_id,
        task_id=task_id,
        completion_note=body.completion_note or "Task resolved by care coordinator.",
        current_user_name=current_user.full_name,
        current_user_role=current_user.role,
        ip_address=request.client.host if request.client else ""
    )
