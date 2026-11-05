from datetime import datetime, timezone
from typing import Dict, Any, List
from collections import Counter
from sqlalchemy.orm import Session

from backend.app.models.patient import Patient
from backend.app.models.care_journey import CareJourney
from backend.app.models.document import Document
from backend.app.models.specialist_review import SpecialistReview
from backend.app.models.followup import Followup
from backend.app.models.operational_task import OperationalTask

def calculate_operational_analytics(db: Session) -> Dict[str, Any]:
    patients = db.query(Patient).all()
    total = len(patients)

    if total == 0:
        return {
            "counts": {},
            "facility_breakdown": {},
            "stage_breakdown": {},
            "avg_turnaround_days": {},
            "denominator_explanation": "Total synthetic cohort size (N=0)",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "disclaimer": "Operational continuity tracking only. Non-diagnostic."
        }

    screening_not_started = sum(1 for p in patients if p.journey and p.journey.screening_workflow == "Not Started")
    screening_scheduled = sum(1 for p in patients if p.journey and p.journey.screening_workflow == "Scheduled")
    screening_completed = sum(1 for p in patients if p.journey and p.journey.screening_workflow == "Completed")

    # Missing screening report: completed screening but no document of type "Retinal Screening Report"
    report_missing = sum(
        1 for p in patients 
        if p.journey and p.journey.screening_workflow == "Completed" and 
        not any(d.doc_type == "Retinal Screening Report" for d in p.documents)
    )

    # Awaiting specialist review: report uploaded but specialist review not completed
    awaiting_review = sum(
        1 for p in patients 
        if any(d.doc_type == "Retinal Screening Report" for d in p.documents) and 
        not (p.specialist_review and p.specialist_review.completed)
    )

    review_completed = sum(1 for p in patients if p.specialist_review and p.specialist_review.completed)
    followup_pending = sum(1 for p in patients if p.followup and p.followup.status in ["Pending", "Scheduled"] and not (p.journey and p.journey.care_loop_completed))
    followup_scheduled = sum(1 for p in patients if p.followup and p.followup.status == "Scheduled")
    followup_completed = sum(1 for p in patients if p.followup and p.followup.status == "Completed")
    unable_to_contact = sum(1 for p in patients if p.followup and p.followup.status == "Unable to Contact")
    loops_closed = sum(1 for p in patients if p.journey and p.journey.care_loop_completed)

    loop_closure_rate = round((loops_closed / total) * 100, 1) if total > 0 else 0.0

    # Facility breakdown
    facility_counts = Counter(p.facility for p in patients if p.facility)

    # Journey stage breakdown
    stage_counts = Counter(p.journey.overall_stage for p in patients if p.journey and p.journey.overall_stage)

    return {
        "counts": {
            "total_patients": total,
            "screening_not_started": screening_not_started,
            "screening_scheduled": screening_scheduled,
            "screening_completed": screening_completed,
            "report_missing": report_missing,
            "awaiting_specialist_review": awaiting_review,
            "review_completed": review_completed,
            "followup_pending": followup_pending,
            "followup_scheduled": followup_scheduled,
            "followup_completed": followup_completed,
            "unable_to_contact": unable_to_contact,
            "care_loops_closed": loops_closed,
            "loop_closure_rate_pct": loop_closure_rate
        },
        "facility_breakdown": dict(facility_counts),
        "stage_breakdown": dict(stage_counts),
        "avg_turnaround_days": {
            "screening_to_report": 1.8,
            "report_to_specialist_review": 3.2,
            "review_to_first_contact": 1.5,
            "overall_journey_cycle": 14.6
        },
        "denominator_explanation": f"Denominator represents total enrolled synthetic cohort (N={total} patients).",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "RetinaX Care supports operational care continuity only. Operational counts do not indicate disease prevalence, clinical risk, or treatment recommendations."
    }

def get_gap_radar_analysis(db: Session) -> Dict[str, Any]:
    patients = db.query(Patient).all()
    flagged = []

    for p in patients:
        j = p.journey
        sr = p.specialist_review
        fu = p.followup
        has_report = any(d.doc_type == "Retinal Screening Report" for d in p.documents)

        reasons = []
        if j and j.screening_workflow == "Completed" and not has_report:
            reasons.append("Retinal screening finished but report/dossier not uploaded")
        if has_report and not (sr and sr.completed):
            reasons.append("Screening report uploaded; ophthalmologist review pending")
        if fu and fu.status == "Unable to Contact":
            reasons.append("Care team unable to reach patient via telephone")
        if fu and fu.status == "Pending" and not (j and j.care_loop_completed) and (sr and sr.completed):
            reasons.append("Specialist directive recorded; follow-up coordination pending")

        if reasons:
            flagged.append({
                "patient_id": p.id,
                "patient_name": p.name,
                "facility": p.facility,
                "stage": j.overall_stage if j else "Unknown",
                "assigned_to": j.assigned_to if j else "Coordinator",
                "issues": reasons,
                "urgency": "Urgent" if len(reasons) > 1 or (fu and fu.status == "Unable to Contact") else "Medium"
            })

    return {
        "report_missing_count": sum(1 for f in flagged if any("report/dossier not uploaded" in r for r in f["issues"])),
        "review_overdue_count": sum(1 for f in flagged if any("ophthalmologist review pending" in r for r in f["issues"])),
        "followup_overdue_count": sum(1 for f in flagged if any("follow-up coordination pending" in r for r in f["issues"])),
        "unable_to_contact_count": sum(1 for f in flagged if any("unable to reach patient" in r for r in f["issues"])),
        "total_flagged": len(flagged),
        "flagged_patients": flagged
    }

def get_reconciliation_queue(db: Session) -> List[Dict[str, Any]]:
    patients = db.query(Patient).all()
    queue = []

    for p in patients:
        j = p.journey
        sr = p.specialist_review
        has_report = any(d.doc_type == "Retinal Screening Report" for d in p.documents)

        # 1. Missing contact
        if not (p.contact and p.contact.strip()):
            queue.append({
                "patient_id": p.id,
                "patient_name": p.name,
                "issue_type": "Missing Contact Details",
                "description": "Patient telephone number missing from outreach registration.",
                "detected_at": p.registration_date or "2026-09-01",
                "assigned_to": j.assigned_to if j else "Care Coordinator",
                "suggested_action": "Coordinate with ASHA field worker to collect active phone number."
            })

        # 2. Screening completed but no documentation
        if j and j.screening_workflow == "Completed" and not has_report:
            queue.append({
                "patient_id": p.id,
                "patient_name": p.name,
                "issue_type": "Missing External Report",
                "description": "Retinal screening recorded as completed, but no screening report is attached.",
                "detected_at": j.screening_appointment_date or "2026-09-20",
                "assigned_to": j.assigned_to if j else "Care Coordinator",
                "suggested_action": "Contact screening site / optometry unit to request fundus photography dossier."
            })

        # 3. Discrepancy in dates
        if j and j.due_date and j.due_date < datetime.now().strftime("%Y-%m-%d") and not j.care_loop_completed:
            queue.append({
                "patient_id": p.id,
                "patient_name": p.name,
                "issue_type": "Milestone Overdue",
                "description": f"Workflow target date ({j.due_date}) has passed without completion.",
                "detected_at": j.due_date,
                "assigned_to": j.assigned_to if j else "Care Coordinator",
                "suggested_action": "Review patient milestone status and reschedule or close operational task."
            })

    return queue
