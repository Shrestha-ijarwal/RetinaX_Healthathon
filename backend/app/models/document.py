from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(32), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    doc_type = Column(String(128), nullable=False)  # Retinal Screening Report, Prescription Record, Lab Summary, Referral Form
    upload_date = Column(String(32), nullable=False)
    source = Column(String(128), default="")
    review_status = Column(String(64), default="Awaiting Specialist Review")
    file_name = Column(String(255), nullable=False)
    storage_key = Column(String(255), nullable=False)  # Sanitized safe key on disk / S3
    size_bytes = Column(Integer, default=0)
    mime_type = Column(String(64), default="application/pdf")
    sha256_hash = Column(String(64), default="")
    uploaded_by = Column(String(128), default="")

    patient = relationship("Patient", back_populates="documents")

    def __repr__(self):
        return f"<Document {self.id} patient={self.patient_id} type={self.doc_type}>"
