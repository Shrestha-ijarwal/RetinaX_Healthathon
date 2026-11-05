import os
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status

from backend.app.core.config import settings
from backend.app.models.patient import Patient
from backend.app.models.document import Document
from backend.app.models.timeline_event import TimelineEvent
from backend.app.storage import get_storage_provider
from backend.app.services.audit_service import log_audit_event

MAGIC_SIGNATURES = {
    b"%PDF-": ("application/pdf", "pdf"),
    b"\xff\xd8\xff": ("image/jpeg", "jpg"),
    b"\x89PNG\r\n\x1a\n": ("image/png", "png"),
}

def validate_magic_bytes(file_bytes: bytes) -> Tuple[str, str]:
    """
    Validates file binary magic bytes.
    Returns (detected_mime, detected_ext) or raises HTTPException.
    """
    for signature, (mime, ext) in MAGIC_SIGNATURES.items():
        if file_bytes.startswith(signature):
            return mime, ext
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported or corrupt file format. Document must be a valid PDF, JPEG, or PNG binary file."
    )

def simulate_malware_scan(file_bytes: bytes, filename: str) -> bool:
    """
    Documented security integration point for antivirus / malware scanning (e.g., ClamAV).
    Returns True if clean, raises HTTPException if malicious signature detected.
    """
    # Heuristic checks: check for embedded executable markers
    suspicious_signatures = [b"MZ", b"\x7fELF", b"<?php", b"<script", b"powershell"]
    for sig in suspicious_signatures:
        if sig in file_bytes[:512]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Security alert: File '{filename}' rejected due to forbidden executable signature."
            )
    return True

async def process_and_save_document(
    db: Session,
    patient_id: str,
    upload_file: UploadFile,
    title: str,
    doc_type: str,
    source: str,
    current_user_name: str,
    current_user_role: str,
    ip_address: str = ""
) -> Document:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient {patient_id} not found.")

    # 1. Read file content and check size limit
    content = await upload_file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB."
        )

    # 2. File extension check
    filename = upload_file.filename or "uploaded_document.pdf"
    clean_filename = os.path.basename(filename)
    ext = clean_filename.rsplit(".", 1)[-1].lower() if "." in clean_filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Forbidden extension '.{ext}'. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 3. Magic bytes / Signature validation
    detected_mime, detected_ext = validate_magic_bytes(content)

    # 4. Antivirus / Malware scanning gate
    simulate_malware_scan(content, clean_filename)

    # 5. Compute SHA256 integrity hash
    sha256_hash = hashlib.sha256(content).hexdigest()

    # 6. Save via storage provider (Local or S3/MinIO)
    storage = get_storage_provider()
    storage_key = storage.save_file(content, clean_filename, detected_mime)

    # 7. Record Document entity in database
    doc_id = f"doc-{uuid.uuid4().hex[:8]}"
    today_str = datetime.now().strftime("%Y-%m-%d")

    document = Document(
        id=doc_id,
        patient_id=patient_id,
        title=title or clean_filename,
        doc_type=doc_type or "Retinal Screening Report",
        upload_date=today_str,
        source=source or "Care Coordination Portal",
        review_status="Awaiting Specialist Review" if doc_type == "Retinal Screening Report" else "Document Archived",
        file_name=clean_filename,
        storage_key=storage_key,
        size_bytes=len(content),
        mime_type=detected_mime,
        sha256_hash=sha256_hash,
        uploaded_by=current_user_name
    )
    db.add(document)

    # Update patient care journey document status
    if patient.journey:
        count = len(patient.documents) + 1
        patient.journey.document_status = f"{count} Document(s) Uploaded"
        if doc_type == "Retinal Screening Report" and not (patient.specialist_review and patient.specialist_review.completed):
            patient.journey.specialist_review = "Pending Review"
            patient.journey.overall_stage = "Awaiting Specialist Review"
            patient.journey.next_workflow_action = f"Specialist to review {doc_type}"

    # Timeline event
    te = TimelineEvent(
        id=f"evt-{uuid.uuid4().hex[:8]}",
        patient_id=patient_id,
        stage="Document Uploaded",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        source="Document Intake",
        actor=current_user_name,
        status="Completed",
        note=f"Verified {detected_mime} document '{clean_filename}' ({len(content)} bytes) uploaded and encrypted."
    )
    db.add(te)

    # Audit log
    log_audit_event(
        db=db,
        action="DOCUMENT_UPLOADED",
        user_name=current_user_name,
        user_role=current_user_role,
        resource_type="Document",
        resource_id=doc_id,
        details={
            "patient_id": patient_id,
            "filename": clean_filename,
            "size_bytes": len(content),
            "mime": detected_mime,
            "sha256": sha256_hash[:16]
        },
        ip_address=ip_address
    )

    db.commit()
    db.refresh(document)
    return document
