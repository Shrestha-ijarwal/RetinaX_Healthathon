import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.patient import Patient
from backend.app.models.operational_task import OperationalTask
from backend.app.models.timeline_event import TimelineEvent
from backend.app.schemas.operational_task import OperationalTaskCreate
from backend.app.services.audit_service import log_audit_event

def create_task(
    db: Session,
    patient_id: str,
    data: OperationalTaskCreate,
    current_user_name: str,
    current_user_role: str,
    ip_address: str = ""
) -> OperationalTask:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient {patient_id} not found.")

    task_id = f"tsk-{uuid.uuid4().hex[:6]}"
    task = OperationalTask(
        id=task_id,
        patient_id=patient_id,
        title=data.title,
        description=data.description or "",
        source=data.source or "Care Coordinator",
        entered_by=current_user_name,
        assigned_to=data.assigned_to or "Care Coordinator",
        due_date=data.due_date,
        status="Open",
        priority=data.priority or "Medium",
        created_at=datetime.now().strftime("%Y-%m-%d")
    )
    db.add(task)

    te = TimelineEvent(
        id=f"evt-{uuid.uuid4().hex[:8]}",
        patient_id=patient_id,
        stage="Task Created",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        source="Care Coordination Desk",
        actor=current_user_name,
        status="Open",
        note=f"Operational task '{data.title}' assigned to {task.assigned_to}."
    )
    db.add(te)

    log_audit_event(
        db=db,
        action="TASK_CREATED",
        user_name=current_user_name,
        user_role=current_user_role,
        resource_type="OperationalTask",
        resource_id=task_id,
        details={"title": data.title, "patient_id": patient_id},
        ip_address=ip_address
    )

    db.commit()
    db.refresh(task)
    return task

def complete_task(
    db: Session,
    patient_id: str,
    task_id: str,
    completion_note: str,
    current_user_name: str,
    current_user_role: str,
    ip_address: str = ""
) -> OperationalTask:
    task = db.query(OperationalTask).filter(
        OperationalTask.id == task_id,
        OperationalTask.patient_id == patient_id
    ).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found for patient {patient_id}.")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    task.status = "Completed"
    task.completed_at = now_str

    te = TimelineEvent(
        id=f"evt-{uuid.uuid4().hex[:8]}",
        patient_id=patient_id,
        stage="Task Completed",
        timestamp=now_str,
        source="Care Coordination Desk",
        actor=current_user_name,
        status="Completed",
        note=f"Task '{task.title}' completed. Note: {completion_note}"
    )
    db.add(te)

    log_audit_event(
        db=db,
        action="TASK_COMPLETED",
        user_name=current_user_name,
        user_role=current_user_role,
        resource_type="OperationalTask",
        resource_id=task_id,
        details={"title": task.title, "note": completion_note},
        ip_address=ip_address
    )

    db.commit()
    db.refresh(task)
    return task
