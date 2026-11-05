from typing import Optional
from pydantic import ConfigDict, BaseModel

class DocumentOut(BaseModel):
    id: str
    patient_id: str
    title: str
    doc_type: str
    upload_date: str
    source: str
    review_status: str
    file_name: str
    storage_key: str
    size_bytes: int
    mime_type: str
    download_url: Optional[str] = None
    uploaded_by: Optional[str] = ""

    model_config = ConfigDict(from_attributes=True)

class DocumentUploadResponse(BaseModel):
    id: str
    patient_id: str
    title: str
    doc_type: str
    file_name: str
    storage_key: str
    size_bytes: int
    mime_type: str
    message: str = "Document successfully validated and securely stored."
