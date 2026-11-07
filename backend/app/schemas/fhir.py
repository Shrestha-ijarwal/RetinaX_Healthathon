"""
FHIR R4 Operational Interoperability Adapter for RetinaX Care.
Strictly non-clinical / operational care coordination exchange.

Supported Resources:
- Patient: Demographic & administrative continuity identifier
- Task: Operational care follow-up assignment and scheduling
- DocumentReference: Indexing of uploaded screening reports and dossiers
- Bundle: Collection, transaction, or searchset containing supported resources

Unsupported / Deliberately Excluded Resources:
- DiagnosticReport, Observation, Condition, Specimen (excluded to maintain strict non-clinical boundary)
- Full terminology server binding (SNOMED-CT / LOINC runtime expansion)
- Dynamic search parameters beyond operational identifiers
"""

import re
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator, Extra

VALID_FHIR_GENDERS = {"male", "female", "other", "unknown"}
VALID_TASK_STATUSES = {
    "draft", "requested", "received", "accepted", "rejected",
    "ready", "cancelled", "in-progress", "on-hold", "failed",
    "completed", "entered-in-error"
}
VALID_TASK_INTENTS = {
    "proposal", "plan", "order", "original-order", "reflex-order",
    "filler-order", "instance-order", "option"
}
VALID_DOCREF_STATUSES = {"current", "superseded", "entered-in-error"}
VALID_BUNDLE_TYPES = {
    "document", "message", "transaction", "transaction-response",
    "batch", "batch-response", "history", "searchset", "collection"
}

FHIR_REFERENCE_REGEX = re.compile(r"^(Patient|Task|DocumentReference|Practitioner|Organization)/[A-Za-z0-9\-_.]+$")

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

class FHIRReference(BaseModel):
    reference: str
    display: Optional[str] = None

    @field_validator("reference")
    @classmethod
    def validate_reference_format(cls, v: str) -> str:
        if not FHIR_REFERENCE_REGEX.match(v):
            raise ValueError(
                f"Invalid FHIR reference '{v}'. Must be formatted as ResourceType/id (e.g. Patient/RX-1001, Task/tsk-101)."
            )
        return v

class FHIRPatientResource(BaseModel):
    resourceType: str = "Patient"
    id: str = Field(..., min_length=1, description="Logical resource identifier")
    identifier: List[FHIRIdentifier] = []
    active: bool = True
    name: List[FHIRHumanName] = []
    telecom: List[FHIRContactPoint] = []
    gender: Optional[str] = "unknown"
    managingOrganization: Optional[Dict[str, str]] = None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> str:
        val = (v or "unknown").lower()
        if val not in VALID_FHIR_GENDERS:
            raise ValueError(f"Invalid FHIR R4 gender '{v}'. Must be one of: {sorted(VALID_FHIR_GENDERS)}")
        return val

class FHIRTaskResource(BaseModel):
    resourceType: str = "Task"
    id: str = Field(..., min_length=1)
    status: str = "requested"
    intent: str = "order"
    priority: str = "routine"
    code: Optional[FHIRCodeableConcept] = None
    description: str = Field(..., min_length=1)
    focus: Optional[FHIRReference] = None
    for_patient: Optional[FHIRReference] = Field(None, alias="for")
    authoredOn: Optional[str] = None
    owner: Optional[Dict[str, str]] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        val = v.lower()
        if val not in VALID_TASK_STATUSES:
            raise ValueError(f"Invalid FHIR R4 Task status '{v}'. Must be one of: {sorted(VALID_TASK_STATUSES)}")
        return val

    @field_validator("intent")
    @classmethod
    def validate_intent(cls, v: str) -> str:
        val = v.lower()
        if val not in VALID_TASK_INTENTS:
            raise ValueError(f"Invalid FHIR R4 Task intent '{v}'. Must be one of: {sorted(VALID_TASK_INTENTS)}")
        return val

class FHIRDocumentReference(BaseModel):
    resourceType: str = "DocumentReference"
    id: str = Field(..., min_length=1)
    status: str = "current"
    type: Optional[FHIRCodeableConcept] = None
    subject: Optional[FHIRReference] = None
    date: Optional[str] = None
    description: Optional[str] = ""
    content: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("status")
    @classmethod
    def validate_doc_status(cls, v: str) -> str:
        val = v.lower()
        if val not in VALID_DOCREF_STATUSES:
            raise ValueError(f"Invalid FHIR R4 DocumentReference status '{v}'. Must be one of: {sorted(VALID_DOCREF_STATUSES)}")
        return val

class FHIRBundleEntry(BaseModel):
    fullUrl: Optional[str] = None
    resource: Dict[str, Any]

class FHIRBundleResource(BaseModel):
    resourceType: str = "Bundle"
    type: str = "searchset"
    total: int = 0
    entry: List[FHIRBundleEntry] = []

    @field_validator("type")
    @classmethod
    def validate_bundle_type(cls, v: str) -> str:
        val = v.lower()
        if val not in VALID_BUNDLE_TYPES:
            raise ValueError(f"Invalid FHIR R4 Bundle type '{v}'. Must be one of: {sorted(VALID_BUNDLE_TYPES)}")
        return val

    @model_validator(mode="after")
    def validate_bundle_entries(self):
        for idx, item in enumerate(self.entry):
            sub_res = item.resource
            if not isinstance(sub_res, dict) or "resourceType" not in sub_res:
                raise ValueError(f"Bundle entry[{idx}] must contain a valid FHIR resource with 'resourceType'.")
            sub_type = sub_res.get("resourceType")
            if sub_type == "Patient":
                FHIRPatientResource(**sub_res)
            elif sub_type == "Task":
                FHIRTaskResource(**sub_res)
            elif sub_type == "DocumentReference":
                FHIRDocumentReference(**sub_res)
            else:
                raise ValueError(
                    f"Bundle entry[{idx}] resourceType '{sub_type}' is unsupported in operational adapter. Supported: Patient, Task, DocumentReference."
                )
        return self

def validate_fhir_resource(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates an arbitrary dictionary against FHIR R4 schemas.
    Raises ValueError with actionable path details if non-conformant.
    """
    if not isinstance(data, dict):
        raise ValueError("Invalid FHIR payload: expected JSON object.")

    res_type = data.get("resourceType")
    if not res_type:
        raise ValueError("Missing mandatory 'resourceType' field in FHIR payload.")

    if res_type == "Patient":
        return FHIRPatientResource(**data).model_dump()
    elif res_type == "Task":
        return FHIRTaskResource(**data).model_dump(by_alias=True)
    elif res_type == "DocumentReference":
        return FHIRDocumentReference(**data).model_dump()
    elif res_type == "Bundle":
        return FHIRBundleResource(**data).model_dump()
    else:
        raise ValueError(
            f"Unsupported FHIR R4 resourceType '{res_type}'. This operational adapter strictly validates: Patient, Task, DocumentReference, Bundle."
        )
