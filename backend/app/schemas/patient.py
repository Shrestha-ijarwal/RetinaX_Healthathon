from typing import Optional, List, Dict, Any
from pydantic import ConfigDict, BaseModel, Field

class DiabetesProfileSchema(BaseModel):
    type: Optional[str] = "Type 2 Diabetes Mellitus"
    duration_recorded: Optional[str] = "Unknown"
    last_hba1c: Optional[str] = "Not Recorded"
    hba1c_date: Optional[str] = None
    current_medications: Optional[str] = ""
    last_retinal_screening: Optional[str] = None
    next_planned_screening: Optional[str] = None

class PatientCreate(BaseModel):
    id: Optional[str] = None  # auto-generated if omitted
    name: str = Field(..., min_length=2, max_length=128)
    age: int = Field(..., ge=0, le=125)
    sex: str = Field(..., pattern="^(Male|Female|Other)$")
    contact: Optional[str] = ""
    facility: Optional[str] = "Primary Health Centre"
    clinician: Optional[str] = "Staff Nurse / Coordinator"
    diabetes_profile: Optional[Dict[str, Any]] = None

class TimelineEventOut(BaseModel):
    id: str
    patient_id: str
    stage: str
    timestamp: str
    source: Optional[str] = ""
    actor: Optional[str] = ""
    status: Optional[str] = ""
    note: Optional[str] = ""

    model_config = ConfigDict(from_attributes=True)

class CareJourneySummaryOut(BaseModel):
    overall_stage: Optional[str] = ""
    screening_workflow: Optional[str] = "Not Started"
    screening_appointment_date: Optional[str] = None
    document_status: Optional[str] = "No Documents"
    specialist_review: Optional[str] = "Not Started"
    followup_status: Optional[str] = "Pending"
    care_loop_completed: Optional[bool] = False
    next_workflow_action: Optional[str] = ""
    assigned_to: Optional[str] = ""
    due_date: Optional[str] = None
    last_contact_date: Optional[str] = None
    last_contact_method: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SpecialistReviewSummaryOut(BaseModel):
    review_status: str = "awaiting_specialist_review"
    completed: bool = False
    assigned_specialist: Optional[str] = None
    clinician_title: Optional[str] = "Dr."
    clinician_specialty: Optional[str] = "Ophthalmology"
    clinician_facility: Optional[str] = "District Eye Hospital"
    registration_number: Optional[str] = None
    review_scheduled_date: Optional[str] = None
    review_completed_at: Optional[str] = None
    report_available: bool = True
    operational_notes: Optional[str] = ""
    clinician_instruction: Optional[str] = ""
    task_owner: Optional[str] = "Care Coordinator"
    operational_task_status: Optional[str] = "Pending"
    reconciliation_status: Optional[str] = "Reconciled"
    last_updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class FollowupSummaryOut(BaseModel):
    status: str = "Pending"
    planned_date: Optional[str] = None
    responsible_staff: Optional[str] = ""
    completion_timestamp: Optional[str] = None
    notes: Optional[str] = ""
    contact_attempts: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)

class DocumentSummaryOut(BaseModel):
    id: str
    title: str
    doc_type: str
    upload_date: str
    source: Optional[str] = ""
    review_status: Optional[str] = ""
    file_name: str
    size_kb: Optional[int] = 0
    storage_key: Optional[str] = ""

    model_config = ConfigDict(from_attributes=True)

class OperationalTaskSummaryOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    source: Optional[str] = ""
    entered_by: Optional[str] = ""
    clinician_specialty: Optional[str] = ""
    clinician_facility: Optional[str] = ""
    assigned_to: Optional[str] = ""
    due_date: Optional[str] = None
    status: str = "Open"
    priority: str = "Medium"
    created_at: Optional[str] = ""
    completed_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ReminderSummaryOut(BaseModel):
    id: str
    type: str
    language: str
    text: Optional[str] = ""
    text_hi: Optional[str] = ""
    sent_status: str
    scheduled_for: Optional[str] = ""
    channel: Optional[str] = ""

    model_config = ConfigDict(from_attributes=True)

class PatientOut(BaseModel):
    id: str
    name: str
    age: int
    sex: str
    contact: Optional[str] = ""
    facility: Optional[str] = ""
    clinician: Optional[str] = ""
    registration_date: Optional[str] = ""
    diabetes_profile: Optional[Dict[str, Any]] = {}
    workflow_status: Optional[CareJourneySummaryOut] = None
    completeness_score: Optional[int] = 0
    version: int = 1

    model_config = ConfigDict(from_attributes=True)

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    contact: Optional[str] = None
    facility: Optional[str] = None
    clinician: Optional[str] = None
    diabetes_profile: Optional[Dict[str, Any]] = None
    expected_version: Optional[int] = Field(None, description="Expected patient version for OCC")

class PatientDetailOut(PatientOut):
    timeline: List[TimelineEventOut] = []
    documents: List[DocumentSummaryOut] = []
    specialist_review: Optional[SpecialistReviewSummaryOut] = None
    pending_tasks: List[OperationalTaskSummaryOut] = []
    followup: Optional[FollowupSummaryOut] = None
    reminders: List[ReminderSummaryOut] = []

class CompletenessCheckOut(BaseModel):
    score_percentage: int
    percentage: Optional[int] = None
    completed_count: int
    total_checks: int
    missing_items: List[str]
    checklist: Optional[List[str]] = None
    is_complete: bool
    checks: Dict[str, bool]
