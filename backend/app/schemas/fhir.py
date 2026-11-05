"""
FHIR R4-compatible operational schemas for RetinaX Care.
Strictly non-clinical / operational care coordination exchange.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class FHIRCoding(BaseModel):
    system: Optional[str] = "http://hl7.org/fhir"
    code: Optional[str] = ""
    display: Optional[str] = ""

class FHIRCodeableConcept(BaseModel):
    coding: List[FHIRCoding] = []
    text: Optional[str] = ""

class FHIRIdentifier(BaseModel):
    use: Optional[str] = "official"
    system: Optional[str] = "https://retinax.care/patient-id"
    value: str

class FHIRHumanName(BaseModel):
    use: Optional[str] = "usual"
    text: str
    family: Optional[str] = ""
    given: List[str] = []

class FHIRContactPoint(BaseModel):
    system: str = "phone"
    value: str
    use: Optional[str] = "mobile"

class FHIRPatientResource(BaseModel):
    resourceType: str = "Patient"
    id: str
    identifier: List[FHIRIdentifier] = []
    active: bool = True
    name: List[FHIRHumanName] = []
    telecom: List[FHIRContactPoint] = []
    gender: Optional[str] = "unknown"
    managingOrganization: Optional[Dict[str, str]] = None

class FHIRTaskResource(BaseModel):
    resourceType: str = "Task"
    id: str
    status: str = "requested"  # requested, in-progress, completed, cancelled
    intent: str = "order"
    priority: str = "routine"
    code: Optional[FHIRCodeableConcept] = None
    description: str
    focus: Optional[Dict[str, str]] = None  # reference to Patient
    for_patient: Optional[Dict[str, str]] = Field(None, alias="for")
    authoredOn: Optional[str] = None
    owner: Optional[Dict[str, str]] = None

class FHIRDocumentReference(BaseModel):
    resourceType: str = "DocumentReference"
    id: str
    status: str = "current"
    type: Optional[FHIRCodeableConcept] = None
    subject: Optional[Dict[str, str]] = None
    date: Optional[str] = None
    description: Optional[str] = ""
    content: List[Dict[str, Any]] = []
