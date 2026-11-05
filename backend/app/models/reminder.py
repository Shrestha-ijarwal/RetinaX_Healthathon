from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(32), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(64), default="Follow-Up Attendance")  # Follow-Up Attendance, Screening Scheduled, Document Request
    language = Column(String(8), default="en")  # en, hi, kn
    text_en = Column(Text, default="")
    text_hi = Column(Text, default="")
    sent_status = Column(String(64), default="simulated")  # simulated, queued, sent, failed, cancelled
    scheduled_for = Column(String(32), default="")
    channel = Column(String(64), default="SMS / WhatsApp (Simulated Preview)")
    delivered_at = Column(String(32), nullable=True)

    patient = relationship("Patient", back_populates="reminders")

    def __repr__(self):
        return f"<Reminder {self.id} patient={self.patient_id} status={self.sent_status}>"
