from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(32), primary_key=True, index=True)  # e.g., RX-1001
    name = Column(String(128), nullable=False, index=True)
    age = Column(Integer, nullable=False)
    sex = Column(String(16), nullable=False)
    contact = Column(String(32), default="")
    facility = Column(String(128), default="")
    clinician = Column(String(128), default="")
    registration_date = Column(String(32), default="")
    diabetes_profile = Column(JSON, default=dict)  # type, duration, last_hba1c, hba1c_date, current_meds, etc.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    journey = relationship("CareJourney", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEvent", back_populates="patient", cascade="all, delete-orphan", order_by="desc(TimelineEvent.timestamp)")
    documents = relationship("Document", back_populates="patient", cascade="all, delete-orphan", order_by="desc(Document.upload_date)")
    specialist_review = relationship("SpecialistReview", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    tasks = relationship("OperationalTask", back_populates="patient", cascade="all, delete-orphan")
    followup = relationship("Followup", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="patient", cascade="all, delete-orphan", order_by="desc(Reminder.scheduled_for)")

    def __repr__(self):
        return f"<Patient {self.id}: {self.name}>"
