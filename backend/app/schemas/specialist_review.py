from typing import Optional
from pydantic import ConfigDict, BaseModel, Field

class SpecialistReviewCreate(BaseModel):
    assigned_specialist: str = Field(..., min_length=2, description="Attributed specialist name")
    clinician_title: Optional[str] = "Dr."
    clinician_specialty: Optional[str] = "Ophthalmology"
    clinician_facility: Optional[str] = "District Eye Hospital"
    registration_number: Optional[str] = ""
    review_status: str = Field("review_completed", description="Operational review status")
    operational_notes: str = Field(..., min_length=2, description="Logistics, document legibility and operational notes")
    clinician_instruction: str = Field(..., min_length=2, description="Attributed clinician operational follow-up directive")
    task_owner: Optional[str] = "Care Coordinator"
    operational_task_status: Optional[str] = "In Progress"
    reconciliation_status: Optional[str] = "Reconciled"
    expected_version: Optional[int] = Field(None, description="Expected resource version for optimistic concurrency control (OCC)")

class SpecialistReviewOut(BaseModel):
    id: int
    patient_id: str
    review_status: str
    completed: bool
    assigned_specialist: Optional[str]
    clinician_title: Optional[str]
    clinician_specialty: Optional[str]
    clinician_facility: Optional[str]
    registration_number: Optional[str]
    review_scheduled_date: Optional[str]
    review_completed_at: Optional[str]
    report_available: bool
    operational_notes: Optional[str]
    clinician_instruction: Optional[str]
    task_owner: Optional[str]
    operational_task_status: Optional[str]
    reconciliation_status: Optional[str]
    last_updated_at: Optional[str]
    version: int = 1

    model_config = ConfigDict(from_attributes=True)
