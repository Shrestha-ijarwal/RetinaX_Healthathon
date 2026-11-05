from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class OperationalTask(Base):
    __tablename__ = "operational_tasks"

    id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(32), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    source = Column(String(128), default="Operational Rule")
    entered_by = Column(String(128), default="")
    clinician_specialty = Column(String(128), default="")
    clinician_facility = Column(String(128), default="")
    assigned_to = Column(String(128), default="Care Coordinator")
    due_date = Column(String(32), nullable=True)
    status = Column(String(32), default="Open")  # Open, Completed
    priority = Column(String(32), default="Medium")  # Low, Medium, High, Urgent
    created_at = Column(String(32), default="")
    completed_at = Column(String(32), nullable=True)

    patient = relationship("Patient", back_populates="tasks")

    def __repr__(self):
        return f"<OperationalTask {self.id} patient={self.patient_id} status={self.status}>"
