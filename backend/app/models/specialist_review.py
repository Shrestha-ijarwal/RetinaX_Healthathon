from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class SpecialistReview(Base):
    """
    Operational specialist review record.
    Tracks review workflow status, document availability, and attributed clinician instructions.
    Does NOT store automated diagnosis, disease grading, or clinical risk scores.
    """
    __tablename__ = "specialist_reviews"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(32), ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    review_status = Column(String(64), nullable=False, default="awaiting_specialist_review")
    completed = Column(Boolean, default=False)
    assigned_specialist = Column(String(128), nullable=True)
    clinician_title = Column(String(64), nullable=True, default="Dr.")
    clinician_specialty = Column(String(128), nullable=True, default="Ophthalmology")
    clinician_facility = Column(String(128), nullable=True, default="District Eye Hospital")
    registration_number = Column(String(64), nullable=True)
    review_scheduled_date = Column(String(32), nullable=True)
    review_completed_at = Column(String(32), nullable=True)
    report_available = Column(Boolean, default=True)
    operational_notes = Column(Text, default="")
    clinician_instruction = Column(Text, default="")
    task_owner = Column(String(128), default="Care Coordinator")
    operational_task_status = Column(String(64), default="Pending")
    reconciliation_status = Column(String(64), default="Reconciled")
    version = Column(Integer, default=1, nullable=False)
    last_updated_at = Column(String(32), nullable=True)

    patient = relationship("Patient", back_populates="specialist_review")

    def __repr__(self):
        return f"<SpecialistReview patient={self.patient_id} status={self.review_status} completed={self.completed}>"
