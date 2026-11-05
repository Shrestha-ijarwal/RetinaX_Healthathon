from fastapi import APIRouter

from backend.app.api.v1.endpoints import (
    auth,
    patients,
    journeys,
    reviews,
    followups,
    tasks,
    documents,
    reminders,
    analytics,
    audit,
    fhir,
    health
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
api_router.include_router(journeys.router, prefix="/journeys", tags=["Care Journeys"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Specialist Reviews"])
api_router.include_router(followups.router, prefix="/followups", tags=["Follow-Ups"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Operational Tasks"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["Reminders"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Continuity Analytics"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Trail"])
api_router.include_router(fhir.router, prefix="/fhir", tags=["FHIR Interoperability"])
