from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.patient import Patient
from backend.app.models.reminder import Reminder
from backend.app.models.user import User
from backend.app.schemas.reminder import ReminderCreate, ReminderOut
from backend.app.services.auth_service import get_current_user, require_coordinator
from backend.app.services.reminder_service import generate_and_queue_reminder

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
def list_reminders(
    patient_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Reminder).join(Patient)

    if patient_id:
        query = query.filter(Reminder.patient_id == patient_id)

    if status_filter and status_filter != "All":
        query = query.filter(Reminder.sent_status.ilike(f"%{status_filter}%"))

    reminders = query.order_by(Reminder.scheduled_for.desc()).all()
    results = []
    for r in reminders:
        p = r.patient
        results.append({
            "id": r.id,
            "patient_id": r.patient_id,
            "patient_name": p.name if p else "Unknown",
            "contact": p.contact if p else "",
            "facility": p.facility if p else "",
            "type": r.type,
            "language": r.language,
            "text": r.text_en,
            "text_hi": r.text_hi,
            "sent_status": r.sent_status,
            "scheduled_for": r.scheduled_for,
            "channel": r.channel,
            "delivered_at": r.delivered_at,
            "disclaimer": "DEMO - NOT SENT TO PATIENT"
        })
    return results

@router.post("/{patient_id}", response_model=ReminderOut, status_code=status.HTTP_201_CREATED)
def trigger_simulated_reminder(
    patient_id: str,
    data: ReminderCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    reminder = generate_and_queue_reminder(
        db=db,
        patient_id=patient_id,
        data=data,
        current_user_name=current_user.full_name,
        current_user_role=current_user.role,
        ip_address=request.client.host if request.client else ""
    )
    return reminder
