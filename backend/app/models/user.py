from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from backend.app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(64), nullable=False)  # "Specialist", "Care Coordinator", "Administrator"
    full_name = Column(String(128), nullable=False)
    title = Column(String(64), default="")
    facility = Column(String(128), default="")
    registration_number = Column(String(64), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
