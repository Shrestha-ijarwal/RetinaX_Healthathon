from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(32), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String(128), nullable=False)
    timestamp = Column(String(32), nullable=False)
    source = Column(String(128), default="")
    actor = Column(String(128), default="")
    status = Column(String(64), default="")
    note = Column(Text, default="")

    patient = relationship("Patient", back_populates="timeline_events")

    def __repr__(self):
        return f"<TimelineEvent {self.id} patient={self.patient_id} stage={self.stage}>"
