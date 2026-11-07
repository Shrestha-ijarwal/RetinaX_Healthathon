import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from collections import Counter
from sqlalchemy.orm import Session

from backend.app.models.patient import Patient
from backend.app.models.care_journey import CareJourney
from backend.app.models.document import Document
from backend.app.models.specialist_review import SpecialistReview
from backend.app.models.followup import Followup, ContactAttempt
from backend.app.models.operational_task import OperationalTask
from backend.app.models.timeline_event import TimelineEvent

def _parse_date_safe(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    # Support various standard date formats in synthetic data
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d-%b-%Y"):
        try:
            return datetime.strptime(date_str.strip()[:16], fmt[:len(date_str.strip()[:16])])
        except Exception:
            pass
    # Regex fallback for YYYY-MM-DD
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", date_str)
    if match:
        try:
            return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except Exception:
            pass
    return None

def calculate_operational_analytics(db: Session) -> Dict[str, Any]:
    """
    Computes genuine database-derived care continuity metrics.
    Specifies numerator, denominator, and time-range for all turnaround times.
    Excludes incomplete records and handles empty datasets without division-by-zero.
    Never calculates clinical risk scores or clinical predictive grades.
    """
    patients = db.query(Patient).all()
    total = len(patients)

    if total == 0:
        return {
            "counts": {
                "total_patients": 0,
                "care_loops_closed": 0,
                "loop_closure_rate_pct": 0.0
            },
            "facility_breakdown": {},
            "stage_breakdown": {},
            "avg_turnaround_days": {
                "screening_to_report": {"value": None, "display": "Insufficient data (N=0 records)", "denominator": 0},
                "report_to_specialist_review": {"value": None, "display": "Insufficient data (N=0 records)", "denominator": 0},
                "review_to_first_contact": {"value": None, "display": "Insufficient data (N=0 records)", "denominator": 0},
                "overall_journey_cycle": {"value": None, "display": "Insufficient data (N=0 records)", "denominator": 0}
            },
            "denominator_explanation": "Total synthetic cohort size (N=0)",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "disclaimer": "RetinaX Care supports operational care continuity only. Non-diagnostic."
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

    # Calculate actual database-derived turnaround intervals from timestamps
    diffs_screen_to_report = []
    diffs_report_to_review = []
    diffs_review_to_contact = []
    diffs_overall_cycle = []

    for p in patients:
        j = p.journey
        sr = p.specialist_review
        fu = p.followup
        docs = [d for d in p.documents if d.doc_type == "Retinal Screening Report"]

        # 1. Screening appointment to Report upload
        if j and j.screening_appointment_date and docs:
            screen_dt = _parse_date_safe(j.screening_appointment_date)
            report_dt = _parse_date_safe(docs[0].upload_date)
            if screen_dt and report_dt and report_dt >= screen_dt:
                diffs_screen_to_report.append((report_dt - screen_dt).total_seconds() / 86400.0)

        # 2. Report upload to Specialist review completion
        if docs and sr and sr.completed and sr.review_completed_at:
            report_dt = _parse_date_safe(docs[0].upload_date)
            review_dt = _parse_date_safe(sr.review_completed_at)
            if report_dt and review_dt and review_dt >= report_dt:
                diffs_report_to_review.append((review_dt - report_dt).total_seconds() / 86400.0)

        # 3. Specialist review to First contact attempt
        if sr and sr.completed and sr.review_completed_at and fu and fu.contact_attempts:
            review_dt = _parse_date_safe(sr.review_completed_at)
            # Find earliest contact attempt
            att_dts = [_parse_date_safe(ca.date) for ca in fu.contact_attempts]
            valid_att = [d for d in att_dts if d]
            if review_dt and valid_att:
                earliest_att = min(valid_att)
                if earliest_att >= review_dt:
                    diffs_review_to_contact.append((earliest_att - review_dt).total_seconds() / 86400.0)

        # 4. Overall closed loop cycle duration
        if j and j.care_loop_completed and p.timeline_events:
            event_dts = [_parse_date_safe(e.timestamp) for e in p.timeline_events]
            valid_events = [d for d in event_dts if d]
            if len(valid_events) >= 2:
                total_cycle = (max(valid_events) - min(valid_events)).total_seconds() / 86400.0
                if total_cycle > 0:
                    diffs_overall_cycle.append(total_cycle)

    def _summarize_metric(diffs: List[float], label: str) -> Dict[str, Any]:
        count = len(diffs)
        if count == 0:
            return {
                "value": None,
                "display": "Insufficient data (N=0 records)",
                "numerator_days": 0.0,
                "denominator_records": 0,
                "unit": "days",
                "label": label
            }
        avg_val = round(sum(diffs) / count, 1)
        return {
            "value": avg_val,
            "display": f"{avg_val} days (N={count} records)",
            "numerator_days": round(sum(diffs), 1),
            "denominator_records": count,
            "unit": "days",
            "label": label
        }

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
            "screening_to_report": _summarize_metric(diffs_screen_to_report, "Screening to Report Upload"),
            "report_to_specialist_review": _summarize_metric(diffs_report_to_review, "Report Upload to Specialist Review"),
            "review_to_first_contact": _summarize_metric(diffs_review_to_contact, "Specialist Review to First Outreach"),
            "overall_journey_cycle": _summarize_metric(diffs_overall_cycle, "Overall Journey Cycle Duration")
        },
        "time_range": "Cohort inception to latest snapshot",
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
