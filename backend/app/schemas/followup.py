from typing import Optional, List
from pydantic import ConfigDict, BaseModel, Field

class ContactAttemptCreate(BaseModel):
    method: str = Field(..., pattern=r"^(Phone Call|SMS|WhatsApp|Home Visit \(ASHA\)|In-Clinic Counseling)$")
    result: str = Field(..., min_length=2, max_length=255)
    staff: Optional[str] = "Care Coordinator"
    notes: Optional[str] = ""

class ContactAttemptOut(BaseModel):
    id: int
    patient_id: str
    date: str
    method: str
    result: str
    staff: str
    notes: Optional[str] = ""

    model_config = ConfigDict(from_attributes=True)

class FollowupUpdate(BaseModel):
    status: str = Field(..., pattern="^(Pending|Scheduled|Completed|Unable to Contact)$")
    planned_date: Optional[str] = None
    responsible_staff: Optional[str] = None
    notes: Optional[str] = None
    expected_version: Optional[int] = Field(None, description="Expected resource version for optimistic concurrency control (OCC)")
    contact_attempt: Optional[ContactAttemptCreate] = None

class FollowupOut(BaseModel):
    id: int
    patient_id: str
    status: str
    planned_date: Optional[str]
    responsible_staff: Optional[str]
    completion_timestamp: Optional[str]
    notes: Optional[str]
    version: int = 1
    contact_attempts: List[ContactAttemptOut] = []

    model_config = ConfigDict(from_attributes=True)
