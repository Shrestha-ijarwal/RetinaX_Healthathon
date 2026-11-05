from typing import Optional
from pydantic import ConfigDict, BaseModel, Field

class SpecialistReviewCreate(BaseModel):
    clinician_name: str = Field(..., min_length=2)
    clinician_title: Optional[str] = "Dr."
    clinician_specialty: Optional[str] = "Ophthalmology"
    clinician_facility: Optional[str] = "District Eye Hospital"
    registration_number: Optional[str] = ""
    clinical_assessment: str = Field(..., min_length=2, description="Manual qualitative assessment entered by qualified specialist")
    followup_instructions: str = Field(..., min_length=2, description="Clinician directed care directive")
    referral_status: str = Field(..., description="Operational referral category e.g. Hospital Follow-Up (6 Months), Routine Annual, etc.")
    notes: Optional[str] = ""

class SpecialistReviewOut(BaseModel):
    id: int
    patient_id: str
    completed: bool
    clinician_name: Optional[str]
    clinician_title: Optional[str]
    clinician_specialty: Optional[str]
    clinician_facility: Optional[str]
    registration_number: Optional[str]
    review_timestamp: Optional[str]
    clinical_assessment: Optional[str]
    followup_instructions: Optional[str]
    referral_status: Optional[str]
    notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)
