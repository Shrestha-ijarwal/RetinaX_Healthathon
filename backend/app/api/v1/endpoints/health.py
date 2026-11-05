from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.core.database import get_db
from backend.app.core.config import settings

router = APIRouter()

@router.get("/health")
@router.get("")
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {e}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_status,
        "compliance": "Strict non-clinical AI scope. Assistive operational care continuity tracking only.",
        "disclaimer": settings.DISCLAIMER
    }
