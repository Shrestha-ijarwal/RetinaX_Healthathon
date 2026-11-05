from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class CareJourney(Base):
    __tablename__ = "care_journeys"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(32), ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    overall_stage = Column(String(64), default="Initial Cohort Enrollment")
    screening_workflow = Column(String(64), default="Not Started")  # Not Started, Scheduled, Completed
    screening_appointment_date = Column(String(32), nullable=True)
    document_status = Column(String(64), default="No Documents")
    specialist_review = Column(String(64), default="Not Started")  # Not Started, Pending Review, Completed
    followup_status = Column(String(64), default="Pending")  # Pending, Scheduled, Completed, Unable to Contact
    care_loop_completed = Column(Boolean, default=False)
    next_workflow_action = Column(String(255), default="")
    assigned_to = Column(String(128), default="")
    due_date = Column(String(32), nullable=True)
    last_contact_date = Column(String(32), nullable=True)
    last_contact_method = Column(String(64), nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    patient = relationship("Patient", back_populates="journey")

    def __repr__(self):
        return f"<CareJourney patient={self.patient_id} stage={self.overall_stage}>"
