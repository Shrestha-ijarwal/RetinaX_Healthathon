from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class OperationalCounts(BaseModel):
    total_patients: int
    screening_not_started: int
    screening_scheduled: int
    screening_completed: int
    report_missing: int
    awaiting_specialist_review: int
    review_completed: int
    followup_pending: int
    followup_scheduled: int
    followup_completed: int
    unable_to_contact: int
    care_loops_closed: int
    loop_closure_rate_pct: float

class GapRadarOut(BaseModel):
    report_missing_count: int
    review_overdue_count: int
    followup_overdue_count: int
    unable_to_contact_count: int
    unreconciled_count: int
    flagged_patients: List[Dict[str, Any]]

class ReconciliationItem(BaseModel):
    patient_id: str
    patient_name: str
    issue_type: str
    description: str
    detected_at: str
    assigned_to: str
    suggested_action: str

class AnalyticsOut(BaseModel):
    counts: OperationalCounts
    facility_breakdown: Dict[str, int]
    stage_breakdown: Dict[str, int]
    avg_turnaround_days: Dict[str, float]
    denominator_explanation: str
    generated_at: str
    disclaimer: str
