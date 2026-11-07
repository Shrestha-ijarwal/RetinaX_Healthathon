"""
RetinaX Care - Database Seed & Synthetic Patient Migration Script
Health-a-thon 2026 Edition

Safely imports synthetic patient records from data/synthetic_patients.json
(or data/synthetic_patients_seed.json fallback) and seeds demonstration user accounts.
Strictly idempotent: can be rerun safely without creating duplicates.
"""

import json
import logging
import os
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import datetime, timezone

# Ensure project root is in path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.security import get_password_hash
from backend.app.models.user import User
from backend.app.models.patient import Patient
from backend.app.models.care_journey import CareJourney
from backend.app.models.timeline_event import TimelineEvent
from backend.app.models.specialist_review import SpecialistReview
from backend.app.models.operational_task import OperationalTask
from backend.app.models.followup import Followup, ContactAttempt
from backend.app.models.document import Document
from backend.app.models.reminder import Reminder
from backend.app.models.audit_event import AuditEvent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("retinax.seed")

DEMO_USERS = [
    {
        "email": "specialist@retinax.care",
        "username": "dr_chandran",
        "password": "Specialist@2026",
        "role": "Specialist",
        "full_name": "Dr. Suresh Chandran, MS",
        "title": "Senior Consultant Ophthalmologist",
        "facility": "District Eye Hospital",
        "registration_number": "MCI-2016-849201",
    },
    {
        "email": "coordinator@retinax.care",
        "username": "coord_ananya",
        "password": "Coordinator@2026",
        "role": "Care Coordinator",
        "full_name": "Ananya Sharma",
        "title": "Lead Care Coordinator",
        "facility": "District Health Office - Ramanagara",
        "registration_number": "",
    },
    {
        "email": "admin@retinax.care",
        "username": "admin_sys",
        "password": "Admin@2026",
        "role": "Administrator",
        "full_name": "Rajiv Menon",
        "title": "Platform Operations Administrator",
        "facility": "State Tele-Ophthalmology Cell",
        "registration_number": "",
    }
]

def seed_demo_users(db: Session, force: bool = False) -> dict:
    env = (os.getenv("ENVIRONMENT") or getattr(settings, "ENVIRONMENT", "development")).lower()
    if env == "production" and not force:
        logger.warning("DEMO SEEDING REFUSED: Demo user seeding is strictly prohibited in production mode.")
        raise RuntimeError(
            "CRITICAL SECURITY CONFIGURATION: Demo user account seeding is strictly disabled in production mode."
        )

    created = 0
    existing = 0
    for udata in DEMO_USERS:
        user = db.query(User).filter(User.email == udata["email"]).first()
        if not user:
            new_user = User(
                email=udata["email"],
                username=udata["username"],
                hashed_password=get_password_hash(udata["password"]),
                role=udata["role"],
                full_name=udata["full_name"],
                title=udata["title"],
                facility=udata["facility"],
                registration_number=udata["registration_number"],
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(new_user)
            created += 1
            logger.info(f"Created demo user: {udata['email']} ({udata['role']})")
        else:
            existing += 1
    db.commit()
    return {"users_created": created, "users_existing": existing}

def seed_synthetic_patients(db: Session, force_reset: bool = False, force: bool = False) -> dict:
    env = (os.getenv("ENVIRONMENT") or getattr(settings, "ENVIRONMENT", "development")).lower()
    if env == "production" and not force:
        logger.warning("DEMO SEEDING REFUSED: Synthetic patient seeding is strictly prohibited in production mode.")
        raise RuntimeError(
            "CRITICAL SECURITY CONFIGURATION: Synthetic patient seeding is strictly disabled in production mode."
        )

    data_file = ROOT_DIR / "data" / "synthetic_patients.json"
    seed_file = ROOT_DIR / "data" / "synthetic_patients_seed.json"

    source_path = data_file if data_file.exists() else seed_file
    if not source_path.exists():
        logger.error(f"Cannot find synthetic patient file at {data_file} or {seed_file}")
        return {"error": "Source file not found"}

    with open(source_path, "r", encoding="utf-8") as f:
        patients_raw = json.load(f)

    logger.info(f"Loaded {len(patients_raw)} raw synthetic patient records from {source_path.name}")

    imported = 0
    updated = 0
    skipped = 0
    failed = 0

    for raw in patients_raw:
        pid = raw.get("id")
        if not pid or not raw.get("name"):
            logger.warning(f"Skipping invalid record missing id or name: {raw}")
            failed += 1
            continue

        existing_patient = db.query(Patient).filter(Patient.id == pid).first()
        if existing_patient and not force_reset:
            skipped += 1
            continue

        if existing_patient and force_reset:
            db.delete(existing_patient)
            db.flush()

        # 1. Create Patient
        patient = Patient(
            id=pid,
            name=raw.get("name"),
            age=raw.get("age", 0),
            sex=raw.get("sex", "Unknown"),
            contact=raw.get("contact", ""),
            facility=raw.get("facility", ""),
            clinician=raw.get("clinician", ""),
            registration_date=raw.get("registration_date", ""),
            diabetes_profile=raw.get("diabetes_profile", {}),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(patient)
        db.flush()

        # 2. Care Journey
        wf = raw.get("workflow_status", {})
        journey = CareJourney(
            patient_id=pid,
            overall_stage=wf.get("overall_stage", "Initial Cohort Enrollment"),
            screening_workflow=wf.get("screening_workflow", "Not Started"),
            screening_appointment_date=wf.get("screening_appointment_date"),
            document_status=wf.get("document_status", "No Documents"),
            specialist_review=wf.get("specialist_review", "Not Started"),
            followup_status=wf.get("followup_status", "Pending"),
            care_loop_completed=bool(wf.get("care_loop_completed", False)),
            next_workflow_action=wf.get("next_workflow_action", ""),
            assigned_to=wf.get("assigned_to", ""),
            due_date=wf.get("due_date"),
            last_contact_date=wf.get("last_contact_date"),
            last_contact_method=wf.get("last_contact_method")
        )
        db.add(journey)

        # 3. Timeline Events
        for evt in raw.get("timeline", []):
            te = TimelineEvent(
                id=evt.get("id") or f"evt-{pid}-{int(datetime.now().timestamp()*1000)}",
                patient_id=pid,
                stage=evt.get("stage", "Timeline Event"),
                timestamp=evt.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M")),
                source=evt.get("source", ""),
                actor=evt.get("actor", ""),
                status=evt.get("status", "Logged"),
                note=evt.get("note", "")
            )
            db.add(te)

        # 4. Documents
        for doc in raw.get("documents", []):
            d = Document(
                id=doc.get("id") or f"doc-{pid}-{len(patient.documents)+1}",
                patient_id=pid,
                title=doc.get("title", "Clinical Document"),
                doc_type=doc.get("doc_type", "Retinal Screening Report"),
                upload_date=doc.get("upload_date", datetime.now().strftime("%Y-%m-%d")),
                source=doc.get("source", ""),
                review_status=doc.get("review_status", "Awaiting Specialist Review"),
                file_name=doc.get("file_name", f"{pid}_doc.pdf"),
                storage_key=doc.get("file_name", f"{pid}_doc.pdf"),
                size_bytes=int(doc.get("size_kb", 50) * 1024),
                mime_type="application/pdf",
                uploaded_by=raw.get("clinician", "Care Coordinator")
            )
            db.add(d)

        # 5. Specialist Review (Operational)
        sr_raw = raw.get("specialist_review", {})
        sr = SpecialistReview(
            patient_id=pid,
            completed=bool(sr_raw.get("completed", False)),
            review_status=sr_raw.get("review_status", ("review_completed" if sr_raw.get("completed") else "awaiting_specialist_review")),
            assigned_specialist=sr_raw.get("assigned_specialist") or sr_raw.get("clinician_name"),
            clinician_title=sr_raw.get("clinician_title", "Dr."),
            clinician_specialty=sr_raw.get("clinician_specialty", "Ophthalmology"),
            clinician_facility=sr_raw.get("clinician_facility", "District Eye Hospital"),
            registration_number=sr_raw.get("registration_number", ""),
            review_scheduled_date=sr_raw.get("review_scheduled_date"),
            review_completed_at=sr_raw.get("review_completed_at") or sr_raw.get("review_timestamp"),
            report_available=bool(sr_raw.get("report_available", True)),
            operational_notes=sr_raw.get("operational_notes", ""),
            clinician_instruction=sr_raw.get("clinician_instruction", ""),
            task_owner=sr_raw.get("task_owner", "Care Coordinator"),
            operational_task_status=sr_raw.get("operational_task_status", "Pending"),
            reconciliation_status=sr_raw.get("reconciliation_status", "Reconciled"),
            last_updated_at=sr_raw.get("last_updated_at") or sr_raw.get("review_timestamp")
        )
        db.add(sr)

        # 6. Operational Tasks
        for tsk in raw.get("pending_tasks", []):
            ot = OperationalTask(
                id=tsk.get("id") or f"tsk-{pid}-{int(datetime.now().timestamp())}",
                patient_id=pid,
                title=tsk.get("title", "Follow-up Action"),
                description=tsk.get("description", ""),
                source=tsk.get("source", "Operational Rule"),
                entered_by=tsk.get("entered_by", ""),
                clinician_specialty=tsk.get("clinician_specialty", ""),
                clinician_facility=tsk.get("clinician_facility", ""),
                assigned_to=tsk.get("assigned_to", "Care Coordinator"),
                due_date=tsk.get("due_date"),
                status=tsk.get("status", "Open"),
                priority=tsk.get("priority", "Medium"),
                created_at=tsk.get("created_at", datetime.now().strftime("%Y-%m-%d")),
                completed_at=tsk.get("completed_at")
            )
            db.add(ot)

        # 7. Followup & Contact Attempts
        fu_raw = raw.get("followup", {})
        fu = Followup(
            patient_id=pid,
            status=fu_raw.get("status", "Pending"),
            planned_date=fu_raw.get("planned_date"),
            responsible_staff=fu_raw.get("responsible_staff", ""),
            completion_timestamp=fu_raw.get("completion_timestamp"),
            notes=fu_raw.get("notes", "")
        )
        db.add(fu)
        db.flush()

        for ca in fu_raw.get("contact_attempts", []):
            c_att = ContactAttempt(
                patient_id=pid,
                followup_id=fu.id,
                date=ca.get("date", datetime.now().strftime("%Y-%m-%d")),
                method=ca.get("method", "Phone Call"),
                result=ca.get("result", ""),
                staff=ca.get("staff", ""),
                notes=ca.get("notes", "")
            )
            db.add(c_att)

        # 8. Reminders
        for rem in raw.get("reminders", []):
            rm = Reminder(
                id=rem.get("id") or f"rem-{pid}-{int(datetime.now().timestamp())}",
                patient_id=pid,
                type=rem.get("type", "Follow-Up Attendance"),
                language=rem.get("language", "en"),
                text_en=rem.get("text", ""),
                text_hi=rem.get("text_hi", ""),
                sent_status=rem.get("sent_status", "simulated"),
                scheduled_for=rem.get("scheduled_for", ""),
                channel=rem.get("channel", "SMS / WhatsApp (Simulated Preview)")
            )
            db.add(rm)

        imported += 1

    # Log initial seed audit event
    audit = AuditEvent(
        user_name="Seed Script",
        user_role="System",
        action="DATABASE_SEED",
        resource_type="Cohort",
        resource_id="synthetic_patients",
        details={"imported": imported, "skipped": skipped, "failed": failed},
        timestamp=datetime.now(timezone.utc)
    )
    db.add(audit)
    db.commit()

    logger.info(f"Seed complete: {imported} imported, {skipped} skipped, {failed} failed.")
    return {
        "imported": imported,
        "skipped": skipped,
        "failed": failed,
        "total_source": len(patients_raw)
    }

def run_seed():
    env = (os.getenv("ENVIRONMENT") or getattr(settings, "ENVIRONMENT", "development")).lower()
    if env == "production":
        logger.error("SEED EXECUTION REFUSED: Direct execution of seed.py is blocked in production mode.")
        print("\n[SECURITY ERROR] Demo seed execution is strictly blocked in production mode (ENVIRONMENT=production).\n")
        sys.exit(1)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user_res = seed_demo_users(db)
        patient_res = seed_synthetic_patients(db, force_reset=False)
        print("\n=======================================================")
        print("  RETINAX CARE DATABASE SEED REPORT")
        print("=======================================================")
        print(f"Users Created: {user_res['users_created']}, Existing: {user_res['users_existing']}")
        print(f"Patients Imported: {patient_res['imported']}")
        print(f"Patients Skipped (Already Present): {patient_res['skipped']}")
        print(f"Patients Failed: {patient_res['failed']}")
        print("=======================================================\n")
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
