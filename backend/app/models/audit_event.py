from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from backend.app.core.database import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), nullable=True, index=True)
    user_name = Column(String(128), default="System")
    user_role = Column(String(64), default="System")
    action = Column(String(128), nullable=False, index=True)  # LOGIN, LOGOUT, REVIEW_SUBMITTED, PATIENT_UPDATE, etc.
    resource_type = Column(String(64), default="")  # Patient, SpecialistReview, Followup, Document, Task
    resource_id = Column(String(64), default="")
    details = Column(JSON, default=dict)
    ip_address = Column(String(64), default="")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self):
        return f"<AuditEvent {self.action} by {self.user_name} on {self.resource_type}:{self.resource_id}>"
