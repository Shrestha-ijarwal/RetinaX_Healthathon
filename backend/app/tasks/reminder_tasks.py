import logging
from datetime import datetime, timezone
from backend.app.tasks.celery_app import celery_app
from backend.app.core.database import SessionLocal
from backend.app.models.reminder import Reminder
from backend.app.models.care_journey import CareJourney
from backend.app.services.audit_service import log_audit_event

logger = logging.getLogger("retinax.celery_tasks")

@celery_app.task(name="tasks.dispatch_simulated_reminder")
def dispatch_simulated_reminder(reminder_id: str):
    db = SessionLocal()
    try:
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if not reminder:
            logger.warning(f"Reminder {reminder_id} not found.")
            return {"status": "not_found", "reminder_id": reminder_id}

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        reminder.sent_status = "Simulated Sent [DEMO — NOT SENT TO PATIENT]"
        reminder.delivered_at = now_str
        db.commit()

        log_audit_event(
            db=db,
            action="CELERY_REMINDER_DELIVERED",
            user_name="Celery Worker",
            user_role="System",
            resource_type="Reminder",
            resource_id=reminder_id,
            details={"dispatched_at": now_str, "language": reminder.language}
        )

        logger.info(f"Successfully simulated dispatch for reminder {reminder_id}")
        return {"status": "success", "reminder_id": reminder_id, "delivered_at": now_str}
    except Exception as e:
        logger.error(f"Error dispatching reminder {reminder_id}: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="tasks.reconcile_overdue_milestones")
def reconcile_overdue_milestones():
    db = SessionLocal()
    try:
        today_str = datetime.now().strftime("%Y-%m-%d")
        overdue_journeys = db.query(CareJourney).filter(
            CareJourney.due_date < today_str,
            CareJourney.care_loop_completed == False
        ).all()

        count = len(overdue_journeys)
        logger.info(f"Reconciliation task identified {count} overdue journeys.")
        return {"status": "completed", "overdue_count": count}
    finally:
        db.close()
