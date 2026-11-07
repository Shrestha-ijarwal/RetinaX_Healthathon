import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.app.core.database import Base

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    endpoint = Column(String(255), nullable=False)
    request_hash = Column(String(64), nullable=False)
    status = Column(String(32), default="PENDING", nullable=False)  # PENDING, COMPLETED, FAILED
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    expires_at = Column(DateTime, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("key", name="uq_idempotency_key"),
    )

    def __repr__(self):
        return f"<IdempotencyRecord key={self.key} user={self.user_id} status={self.status} code={self.response_code}>"


def compute_request_hash(method: str, endpoint: str, body_bytes: bytes) -> str:
    hasher = hashlib.sha256()
    hasher.update(method.upper().encode("utf-8"))
    hasher.update(b"|")
    hasher.update(endpoint.encode("utf-8"))
    hasher.update(b"|")
    hasher.update(body_bytes)
    return hasher.hexdigest()


def claim_or_get_idempotency_record(
    db: Session,
    key: str,
    user_id: Optional[int],
    endpoint: str,
    request_hash: str,
    ttl_hours: int = 24
) -> Tuple[str, Optional[IdempotencyRecord]]:
    """
    Atomically claims the idempotency key using DB uniqueness constraint.
    Guarantees that unauthenticated and authenticated duplicate keys cannot create multiple reservations.
    Returns a tuple (status, record):
    - ("CLAIMED", record): New record created in PENDING state; caller holds execution lock.
    - ("REPLAY", record): Previous execution COMPLETED with matching hash; caller should return cached response.
    - ("HASH_MISMATCH", record): Key was previously used with DIFFERENT request parameters/body; reject with 422.
    - ("IN_FLIGHT", record): Concurrent request is currently executing; reject with 409 Conflict.
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=ttl_hours)

    # Clean up expired records for this key if any
    db.query(IdempotencyRecord).filter(
        IdempotencyRecord.key == key,
        IdempotencyRecord.expires_at <= now
    ).delete(synchronize_session=False)

    new_record = IdempotencyRecord(
        key=key,
        user_id=user_id,
        endpoint=endpoint,
        request_hash=request_hash,
        status="PENDING",
        created_at=now,
        expires_at=expires_at
    )

    try:
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return ("CLAIMED", new_record)
    except IntegrityError:
        db.rollback()
        # Key already claimed by another request; inspect existing record
        existing = db.query(IdempotencyRecord).filter(
            IdempotencyRecord.key == key
        ).first()

        if not existing:
            # Race condition on delete/re-insert, retry once
            return ("IN_FLIGHT", None)

        if existing.request_hash != request_hash:
            return ("HASH_MISMATCH", existing)

        if existing.status == "PENDING":
            return ("IN_FLIGHT", existing)

        if existing.status == "COMPLETED":
            return ("REPLAY", existing)

        # Atomic reclamation of FAILED record: only one concurrent worker can succeed
        rows = db.query(IdempotencyRecord).filter(
            IdempotencyRecord.id == existing.id,
            IdempotencyRecord.status == "FAILED"
        ).update({
            "status": "PENDING",
            "request_hash": request_hash,
            "endpoint": endpoint,
            "user_id": user_id,
            "expires_at": expires_at
        }, synchronize_session=False)
        db.commit()

        if rows == 1:
            db.refresh(existing)
            return ("CLAIMED", existing)
        else:
            return ("IN_FLIGHT", existing)


def complete_idempotency_record(
    db: Session,
    record_id: int,
    response_code: int,
    response_body: str
) -> None:
    db.query(IdempotencyRecord).filter(
        IdempotencyRecord.id == record_id
    ).update({
        "status": "COMPLETED",
        "response_code": response_code,
        "response_body": response_body
    }, synchronize_session=False)
    db.commit()


def release_failed_idempotency_record(
    db: Session,
    record_id: int
) -> None:
    db.query(IdempotencyRecord).filter(
        IdempotencyRecord.id == record_id,
        IdempotencyRecord.status == "PENDING"
    ).update({"status": "FAILED"}, synchronize_session=False)
    db.commit()
