import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.patient import Patient
from backend.app.models.reminder import Reminder
from backend.app.models.timeline_event import TimelineEvent
from backend.app.schemas.reminder import ReminderCreate
from backend.app.services.audit_service import log_audit_event

REMINDER_TEMPLATES = {
    "Follow-Up Attendance": {
        "en": "Dear {patient_name}, this is a reminder from your care team at {facility} regarding your diabetic eye follow-up on {date}. Please bring your previous records. Call {contact} for rescheduling.",
        "hi": "प्रिय {patient_name}, {facility} में आपकी देखभाल टीम द्वारा {date} को आपकी डायबिटिक नेत्र अनुवर्ती जांच के संबंध में यह अनुस्मारक है। कृपया अपने पिछले रिकॉर्ड साथ लाएं।"
    },
    "Screening Scheduled": {
        "en": "Dear {patient_name}, your diabetic retinal screening appointment is scheduled at {facility} on {date}. Early regular screening protects your vision. Contact: {contact}.",
        "hi": "प्रिय {patient_name}, {facility} में {date} को आपकी डायबिटिक रेटिना जांच निर्धारित है। नियमित जांच आपकी दृष्टि की सुरक्षा करती है।"
    },
    "Document Request": {
        "en": "Dear {patient_name}, please provide your previous eye hospital summary or lab report to the care coordinator at {facility} to complete your care record.",
        "hi": "प्रिय {patient_name}, कृपया अपना पुराना नेत्र अस्पताल सारांश या लैब रिपोर्ट {facility} में केयर कोऑर्डिनेटर को उपलब्ध कराएं।"
    }
}

def generate_and_queue_reminder(
    db: Session,
    patient_id: str,
    data: ReminderCreate,
    current_user_name: str,
    current_user_role: str,
    ip_address: str = ""
) -> Reminder:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient {patient_id} not found.")

    tmpl = REMINDER_TEMPLATES.get(data.type, REMINDER_TEMPLATES["Follow-Up Attendance"])
    date_str = (
        (patient.followup and patient.followup.planned_date) or 
        (patient.journey and patient.journey.screening_appointment_date) or 
        "your upcoming scheduled date"
    )

    text_en = tmpl["en"].format(
        patient_name=patient.name,
        facility=patient.facility or "Primary Health Centre",
        date=date_str,
        contact=patient.facility or "clinic desk"
    )
    text_hi = tmpl["hi"].format(
        patient_name=patient.name,
        facility=patient.facility or "प्राथमिक स्वास्थ्य केंद्र",
        date=date_str
    )

    if data.custom_note:
        text_en += f" Note: {data.custom_note}"
        text_hi += f" विशेष सूचना: {data.custom_note}"

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    rem_id = f"rem-{uuid.uuid4().hex[:6]}"

    # State machine: starts as 'queued', then marked 'simulated' / 'sent'
    reminder = Reminder(
        id=rem_id,
        patient_id=patient_id,
        type=data.type,
        language=data.language,
        text_en=text_en,
        text_hi=text_hi,
        sent_status="Simulated Sent (Demo notification - not actually sent)",
        scheduled_for=now_str,
        channel=data.channel or "SMS / WhatsApp (Simulated Preview)",
        delivered_at=now_str
    )
    db.add(reminder)

    # Timeline event
    te = TimelineEvent(
        id=f"evt-{uuid.uuid4().hex[:8]}",
        patient_id=patient_id,
        stage="Patient Reminder Sent",
        timestamp=now_str,
        source="Communication Engine",
        actor=current_user_name,
        status="Delivered",
        note=f"Simulated {data.type} reminder sent ({data.language.upper()}). Demo notification - not actually sent."
    )
    db.add(te)

    # Audit log
    log_audit_event(
        db=db,
        action="REMINDER_SIMULATED_DISPATCH",
        user_name=current_user_name,
        user_role=current_user_role,
        resource_type="Reminder",
        resource_id=rem_id,
        details={
            "type": data.type,
            "language": data.language,
            "patient_id": patient_id,
            "channel": reminder.channel
        },
        ip_address=ip_address
    )

    db.commit()
    db.refresh(reminder)
    return reminder
