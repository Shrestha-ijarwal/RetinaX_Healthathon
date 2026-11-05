from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.patient import Patient
from backend.app.models.operational_task import OperationalTask
from backend.app.models.document import Document
from backend.app.models.user import User
from backend.app.services.auth_service import get_current_user
from backend.app.services.fhir_adapter import (
    to_fhir_patient,
    to_fhir_task,
    to_fhir_document_reference
)

router = APIRouter()

@router.get("/Patient/{patient_id}", response_model=Dict[str, Any])
def get_fhir_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"FHIR Patient {patient_id} not found.")
    return to_fhir_patient(patient)

@router.get("/Task", response_model=Dict[str, Any])
def list_fhir_tasks(
    patient_id: Optional[str] = Query(None, alias="patient"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(OperationalTask)
    if patient_id:
        query = query.filter(OperationalTask.patient_id == patient_id)
    tasks = query.all()

    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(tasks),
        "entry": [
            {
                "fullUrl": f"https://retinax.care/fhir/Task/{t.id}",
                "resource": to_fhir_task(t)
            } for t in tasks
        ]
    }

@router.get("/DocumentReference", response_model=Dict[str, Any])
def list_fhir_documents(
    patient_id: Optional[str] = Query(None, alias="subject"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Document)
    if patient_id:
        query = query.filter(Document.patient_id == patient_id)
    docs = query.all()

    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(docs),
        "entry": [
            {
                "fullUrl": f"https://retinax.care/fhir/DocumentReference/{d.id}",
                "resource": to_fhir_document_reference(d)
            } for d in docs
        ]
    }
