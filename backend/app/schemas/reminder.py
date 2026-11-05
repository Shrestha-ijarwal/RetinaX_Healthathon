from typing import Optional
from pydantic import ConfigDict, BaseModel, Field

class ReminderCreate(BaseModel):
    type: str = Field(..., pattern="^(Follow-Up Attendance|Screening Scheduled|Document Request)$")
    language: str = Field("en", pattern="^(en|hi|kn)$")
    custom_note: Optional[str] = None
    channel: Optional[str] = "SMS / WhatsApp (Simulated Preview)"

class ReminderOut(BaseModel):
    id: str
    patient_id: str
    type: str
    language: str
    text_en: str
    text_hi: str
    sent_status: str
    scheduled_for: str
    channel: str
    delivered_at: Optional[str]
    disclaimer: str = "DEMO - NOT SENT TO PATIENT"

    model_config = ConfigDict(from_attributes=True)
