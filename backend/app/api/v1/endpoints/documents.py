import io
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.patient import Patient
from backend.app.models.document import Document
from backend.app.models.user import User
from backend.app.schemas.document import DocumentOut, DocumentUploadResponse
from backend.app.services.auth_service import get_current_user, require_coordinator
from backend.app.services.document_service import process_and_save_document
from backend.app.storage import get_storage_provider
from backend.app.services.audit_service import log_audit_event

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
def list_documents(
    doc_type: Optional[str] = Query(None),
    patient_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Document).join(Patient)

    if patient_id:
        query = query.filter(Document.patient_id == patient_id)

    if doc_type and doc_type != "All":
        query = query.filter(Document.doc_type.ilike(f"%{doc_type}%"))

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (Document.title.ilike(s)) | 
            (Document.file_name.ilike(s)) | 
            (Patient.name.ilike(s)) | 
            (Patient.id.ilike(s))
        )

    docs = query.order_by(Document.upload_date.desc()).all()
    results = []
    for d in docs:
        p = d.patient
        results.append({
            "id": d.id,
            "patient_id": d.patient_id,
            "patient_name": p.name if p else "Unknown",
            "facility": p.facility if p else "",
            "title": d.title,
            "doc_type": d.doc_type,
            "upload_date": d.upload_date,
            "source": d.source,
            "review_status": d.review_status,
            "file_name": d.file_name,
            "storage_key": d.storage_key,
            "size_kb": d.size_bytes // 1024,
            "mime_type": d.mime_type,
            "uploaded_by": d.uploaded_by,
            "download_url": f"/api/v1/documents/{d.id}/download"
        })
    return results

@router.post("/{patient_id}", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    patient_id: str,
    request: Request,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    doc_type: Optional[str] = Form("Retinal Screening Report"),
    source: Optional[str] = Form("Tele-Ophthalmology Intake"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coordinator)
):
    doc = await process_and_save_document(
        db=db,
        patient_id=patient_id,
        upload_file=file,
        title=title or (file.filename or "Uploaded Document"),
        doc_type=doc_type or "Retinal Screening Report",
        source=source or "Care Coordination Portal",
        current_user_name=current_user.full_name,
        current_user_role=current_user.role,
        ip_address=request.client.host if request.client else ""
    )
    return {
        "id": doc.id,
        "patient_id": doc.patient_id,
        "title": doc.title,
        "doc_type": doc.doc_type,
        "file_name": doc.file_name,
        "storage_key": doc.storage_key,
        "size_bytes": doc.size_bytes,
        "mime_type": doc.mime_type,
        "message": "Document successfully validated with magic-byte verification and securely archived."
    }

@router.get("/{document_id}/download")
def download_document_by_id(
    document_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Strict Backend Auth required!
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        # Check by storage key directly
        doc = db.query(Document).filter(Document.storage_key == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document record not found.")

    storage = get_storage_provider()
    try:
        content = storage.get_file_bytes(doc.storage_key)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File content not available: {e}")

    log_audit_event(
        db=db,
        action="DOCUMENT_DOWNLOADED",
        user_name=current_user.full_name,
        user_role=current_user.role,
        user_id=str(current_user.id),
        resource_type="Document",
        resource_id=doc.id,
        details={"file_name": doc.file_name, "patient_id": doc.patient_id},
        ip_address=request.client.host if request.client else ""
    )

    return Response(
        content=content,
        media_type=doc.mime_type or "application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{doc.file_name}"',
            "Cache-Control": "private, no-cache, no-store, must-revalidate"
        }
    )

@router.get("/download/{storage_key}")
def download_by_storage_key(
    storage_key: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return download_document_by_id(storage_key, request, db, current_user)
