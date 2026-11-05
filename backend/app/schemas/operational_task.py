from typing import Optional
from pydantic import ConfigDict, BaseModel, Field

class OperationalTaskCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = ""
    assigned_to: Optional[str] = "Care Coordinator"
    due_date: Optional[str] = None
    priority: Optional[str] = "Medium"
    source: Optional[str] = "Operational Coordinator"

class TaskCompleteRequest(BaseModel):
    completion_note: Optional[str] = "Task completed by care team."

class OperationalTaskOut(BaseModel):
    id: str
    patient_id: str
    title: str
    description: Optional[str] = ""
    source: Optional[str] = ""
    entered_by: Optional[str] = ""
    clinician_specialty: Optional[str] = ""
    clinician_facility: Optional[str] = ""
    assigned_to: str
    due_date: Optional[str]
    status: str
    priority: str
    created_at: str
    completed_at: Optional[str]

    model_config = ConfigDict(from_attributes=True)
