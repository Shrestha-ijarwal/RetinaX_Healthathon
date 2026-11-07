import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.models.patient import Patient
from backend.app.models.care_journey import CareJourney
from backend.app.models.timeline_event import TimelineEvent
from backend.app.models.specialist_review import SpecialistReview
from backend.app.models.operational_task import OperationalTask
from backend.app.models.followup import Followup
from backend.app.models.document import Document
from backend.app.models.reminder import Reminder
from backend.app.schemas.patient import PatientCreate

def calculate_record_completeness(patient: Patient) -> Dict[str, Any]:
    """
    Rules-based record completeness checker (Non-diagnostic / Operational only).
    Checks whether operational and demographic records are present.
    """
    p_dict = {
        "contact": patient.contact,
        "diabetes_profile": patient.diabetes_profile or {},
        "documents": patient.documents or [],
        "specialist_review": patient.specialist_review,
        "followup": patient.followup
    }

    checks = {
        "contact_number": bool(p_dict["contact"] and p_dict["contact"].strip()),
        "baseline_diabetes_duration": bool(
            p_dict["diabetes_profile"].get("duration_recorded") and 
            p_dict["diabetes_profile"].get("duration_recorded") != "Unknown"
        ),
        "baseline_hba1c": bool(
            p_dict["diabetes_profile"].get("last_hba1c") and 
            p_dict["diabetes_profile"].get("last_hba1c") != "Not Recorded"
        ),
        "screening_report_uploaded": any(d.doc_type == "Retinal Screening Report" for d in patient.documents),
        "specialist_review_recorded": bool(patient.specialist_review and patient.specialist_review.completed),
        "followup_plan_defined": bool(
            (patient.followup and patient.followup.planned_date) or 
            p_dict["diabetes_profile"].get("next_planned_screening")
        )
    }

    missing_items = []
    if not checks["contact_number"]:
        missing_items.append("Primary contact telephone number not on file")
    if not checks["baseline_diabetes_duration"]:
        missing_items.append("Diabetes duration not documented in source record")
    if not checks["baseline_hba1c"]:
        missing_items.append("Baseline HbA1c lab result not documented")
    if not checks["screening_report_uploaded"]:
        missing_items.append("Retinal screening report/images not uploaded")
    if not checks["specialist_review_recorded"]:
        missing_items.append("Specialist ophthalmologist review not recorded")
    if not checks["followup_plan_defined"]:
        missing_items.append("Next follow-up / screening date not scheduled")

    total_checks = len(checks)
    completed_checks = sum(1 for v in checks.values() if v)
    score_pct = int((completed_checks / total_checks) * 100)

    return {
        "score_percentage": score_pct,
        "percentage": score_pct,
        "completed_count": completed_checks,
        "total_checks": total_checks,
        "missing_items": missing_items,
        "checklist": missing_items,
        "is_complete": len(missing_items) == 0,
        "checks": checks
    }

def get_patients_list(
    db: Session,
    search: Optional[str] = None,
    filter_mode: Optional[str] = "all",
    facility: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[Patient], Dict[str, int], int]:
    query = db.query(Patient)

    if facility and facility != "All Facilities":
        query = query.filter(Patient.facility == facility)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Patient.name.ilike(search_term),
                Patient.id.ilike(search_term),
                Patient.contact.ilike(search_term),
                Patient.facility.ilike(search_term)
            )
        )

    all_matching = query.all()

    # Apply operational filter modes
    filtered_patients = []
    for p in all_matching:
        j = p.journey
        sr = p.specialist_review
        fu = p.followup
        has_report = any(d.doc_type == "Retinal Screening Report" for d in p.documents)

        match = True
        if filter_mode == "needs_attention":
            match = not (j and j.care_loop_completed) and (
                (j and j.followup_status == "Unable to Contact") or
                (j and j.screening_workflow == "Completed" and not has_report) or
                (has_report and not (sr and sr.completed)) or
                (fu and fu.status in ["Pending", "Scheduled"])
            )
        elif filter_mode == "pending_screening":
            match = bool(j and j.screening_workflow in ["Not Started", "Pending"])
        elif filter_mode == "scheduled":
            match = bool(j and j.screening_workflow == "Scheduled")
        elif filter_mode == "screening_completed":
            match = bool(j and j.screening_workflow == "Completed")
        elif filter_mode == "report_missing":
            match = bool(j and j.screening_workflow == "Completed" and not has_report)
        elif filter_mode == "awaiting_review":
            match = bool(has_report and not (sr and sr.completed))
        elif filter_mode == "followup_pending":
            match = bool(fu and fu.status in ["Pending", "Scheduled"] and not (j and j.care_loop_completed))
        elif filter_mode == "unable_to_contact":
            match = bool(fu and fu.status == "Unable to Contact")
        elif filter_mode == "completed":
            match = bool(j and j.care_loop_completed)

        if match:
            filtered_patients.append(p)

    total_count = len(filtered_patients)
    paginated = filtered_patients[skip : skip + limit]

    # Calculate operational metrics across whole store
    all_all = db.query(Patient).all()
    metrics = {
        "total_patients": len(all_all),
        "screening_not_started": sum(1 for p in all_all if p.journey and p.journey.screening_workflow == "Not Started"),
        "screening_scheduled": sum(1 for p in all_all if p.journey and p.journey.screening_workflow == "Scheduled"),
        "screening_completed": sum(1 for p in all_all if p.journey and p.journey.screening_workflow == "Completed"),
        "report_missing": sum(1 for p in all_all if p.journey and p.journey.screening_workflow == "Completed" and not any(d.doc_type == "Retinal Screening Report" for d in p.documents)),
        "awaiting_specialist_review": sum(1 for p in all_all if any(d.doc_type == "Retinal Screening Report" for d in p.documents) and not (p.specialist_review and p.specialist_review.completed)),
        "followup_pending": sum(1 for p in all_all if p.followup and p.followup.status in ["Pending", "Scheduled"] and not (p.journey and p.journey.care_loop_completed)),
        "unable_to_contact": sum(1 for p in all_all if p.followup and p.followup.status == "Unable to Contact"),
        "care_loops_closed": sum(1 for p in all_all if p.journey and p.journey.care_loop_completed),
    }

    return paginated, metrics, total_count

def get_patient_detail(db: Session, patient_id: str) -> Optional[Patient]:
    return db.query(Patient).filter(Patient.id == patient_id).first()

def create_patient_record(db: Session, data: PatientCreate, created_by: str = "Coordinator") -> Patient:
    pid = data.id
    if not pid:
        # Generate next ID like RX-1013
        existing_ids = [p.id for p in db.query(Patient.id).all() if p.id.startswith("RX-")]
        nums = [int(i.split("-")[1]) for i in existing_ids if i.split("-")[1].isdigit()]
        next_num = max(nums, default=1000) + 1
        pid = f"RX-{next_num}"

    patient = Patient(
        id=pid,
        name=data.name,
        age=data.age,
        sex=data.sex,
        contact=data.contact or "",
        facility=data.facility or "Primary Health Centre",
        clinician=data.clinician or "Care Coordinator",
        registration_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        diabetes_profile=data.diabetes_profile or {
            "type": "Type 2 Diabetes Mellitus",
            "duration_recorded": "Unknown",
            "last_hba1c": "Not Recorded",
            "hba1c_date": None,
            "current_medications": "",
            "last_retinal_screening": None,
            "next_planned_screening": None
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(patient)
    db.flush()

    journey = CareJourney(
        patient_id=pid,
        overall_stage="Initial Cohort Enrollment",
        screening_workflow="Not Started",
        screening_appointment_date=None,
        document_status="No Documents",
        specialist_review="Not Started",
        followup_status="Pending",
        care_loop_completed=False,
        next_workflow_action="Schedule initial retinal screening appointment",
        assigned_to=created_by,
        due_date=None
    )
    db.add(journey)

    sr = SpecialistReview(
        patient_id=pid,
        completed=False,
        review_status="awaiting_specialist_review"
    )
    db.add(sr)

    fu = Followup(
        patient_id=pid,
        status="Pending",
        responsible_staff=created_by
    )
    db.add(fu)

    te = TimelineEvent(
        id=f"evt-{pid}-init",
        patient_id=pid,
        stage="Cohort Registration",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        source="Care Coordination Desk",
        actor=created_by,
        status="Completed",
        note=f"Synthetic patient registered into diabetic care continuity cohort at {patient.facility}."
    )
    db.add(te)

    db.commit()
    db.refresh(patient)
    return patient
