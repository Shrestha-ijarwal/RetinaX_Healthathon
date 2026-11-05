from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class SpecialistReview(Base):
    __tablename__ = "specialist_reviews"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(32), ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    completed = Column(Boolean, default=False)
    clinician_name = Column(String(128), nullable=True)
    clinician_title = Column(String(64), nullable=True)
    clinician_specialty = Column(String(128), nullable=True)
    clinician_facility = Column(String(128), nullable=True)
    registration_number = Column(String(64), nullable=True)
    review_timestamp = Column(String(32), nullable=True)
    clinical_assessment = Column(Text, default="")
    followup_instructions = Column(Text, default="")
    referral_status = Column(String(128), default="Awaiting Review")
    notes = Column(Text, default="")

    patient = relationship("Patient", back_populates="specialist_review")

    def __repr__(self):
        return f"<SpecialistReview patient={self.patient_id} completed={self.completed}>"
