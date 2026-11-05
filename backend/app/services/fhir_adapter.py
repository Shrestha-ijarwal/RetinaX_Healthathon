"""
HL7 / FHIR R4-compatible Operational Adapter for RetinaX Care.
Translates internal care continuity records to standardized FHIR resources.
Non-clinical, operational only.
"""

from typing import Dict, Any, Optional
from backend.app.models.patient import Patient
from backend.app.models.document import Document
from backend.app.models.operational_task import OperationalTask

def to_fhir_patient(patient: Patient) -> Dict[str, Any]:
    name_parts = patient.name.split(" ", 1)
    given = [name_parts[0]]
    family = name_parts[1] if len(name_parts) > 1 else ""

    gender = "other"
    if patient.sex.lower() == "male":
        gender = "male"
    elif patient.sex.lower() == "female":
        gender = "female"

    return {
        "resourceType": "Patient",
        "id": patient.id,
        "identifier": [
            {
                "use": "official",
                "system": "https://retinax.care/patient-identifier",
                "value": patient.id
            }
        ],
        "active": True,
        "name": [
            {
                "use": "usual",
                "text": patient.name,
                "family": family,
                "given": given
            }
        ],
        "telecom": [
            {
                "system": "phone",
                "value": patient.contact or "",
                "use": "mobile"
            }
        ],
        "gender": gender,
        "managingOrganization": {
            "display": patient.facility or "Primary Health Centre"
        }
    }

def to_fhir_task(task: OperationalTask) -> Dict[str, Any]:
    fhir_status = "requested"
    if task.status == "Completed":
        fhir_status = "completed"
    elif task.status == "In Progress":
        fhir_status = "in-progress"

    return {
        "resourceType": "Task",
        "id": task.id,
        "status": fhir_status,
        "intent": "order",
        "priority": "routine" if task.priority == "Medium" else task.priority.lower(),
        "code": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/CodeSystem/task-code",
                    "code": "fulfill",
                    "display": "Fulfill the focal request"
                }
            ],
            "text": task.title
        },
        "description": task.description or task.title,
        "for": {
            "reference": f"Patient/{task.patient_id}",
            "display": f"Patient {task.patient_id}"
        },
        "authoredOn": task.created_at or "",
        "owner": {
            "display": task.assigned_to or "Care Coordinator"
        }
    }

def to_fhir_document_reference(doc: Document) -> Dict[str, Any]:
    return {
        "resourceType": "DocumentReference",
        "id": doc.id,
        "status": "current",
        "type": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "11502-2",
                    "display": doc.doc_type
                }
            ],
            "text": doc.doc_type
        },
        "subject": {
            "reference": f"Patient/{doc.patient_id}"
        },
        "date": f"{doc.upload_date}T00:00:00Z" if doc.upload_date else "",
        "description": doc.title,
        "content": [
            {
                "attachment": {
                    "contentType": doc.mime_type,
                    "url": f"/api/v1/documents/{doc.id}/download",
                    "size": doc.size_bytes,
                    "title": doc.file_name
                }
            }
        ]
    }
