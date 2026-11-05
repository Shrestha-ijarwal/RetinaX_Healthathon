from typing import Optional
from pydantic import ConfigDict, BaseModel

class CareJourneyUpdate(BaseModel):
    overall_stage: Optional[str] = None
    screening_workflow: Optional[str] = None
    screening_appointment_date: Optional[str] = None
    document_status: Optional[str] = None
    specialist_review: Optional[str] = None
    followup_status: Optional[str] = None
    care_loop_completed: Optional[bool] = None
    next_workflow_action: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None

class CareJourneyOut(BaseModel):
    id: int
    patient_id: str
    overall_stage: str
    screening_workflow: str
    screening_appointment_date: Optional[str]
    document_status: str
    specialist_review: str
    followup_status: str
    care_loop_completed: bool
    next_workflow_action: str
    assigned_to: str
    due_date: Optional[str]
    last_contact_date: Optional[str]
    last_contact_method: Optional[str]

    model_config = ConfigDict(from_attributes=True)
