from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Followup(Base):
    __tablename__ = "followups"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(32), ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    status = Column(String(64), default="Pending")  # Pending, Scheduled, Completed, Unable to Contact
    planned_date = Column(String(32), nullable=True)
    responsible_staff = Column(String(128), default="")
    completion_timestamp = Column(String(32), nullable=True)
    version = Column(Integer, default=1, nullable=False)
    notes = Column(Text, default="")

    patient = relationship("Patient", back_populates="followup")
    contact_attempts = relationship("ContactAttempt", back_populates="followup", cascade="all, delete-orphan", order_by="desc(ContactAttempt.date)")

    def __repr__(self):
        return f"<Followup patient={self.patient_id} status={self.status}>"

class ContactAttempt(Base):
    __tablename__ = "contact_attempts"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(32), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    followup_id = Column(Integer, ForeignKey("followups.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String(32), nullable=False)
    method = Column(String(64), default="Phone Call")  # Phone Call, SMS, WhatsApp, Home Visit (ASHA)
    result = Column(String(255), default="")
    staff = Column(String(128), default="")
    notes = Column(Text, default="")

    followup = relationship("Followup", back_populates="contact_attempts")

    def __repr__(self):
        return f"<ContactAttempt {self.id} patient={self.patient_id} result={self.result}>"
