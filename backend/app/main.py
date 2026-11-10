from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.idempotency import IdempotencyMiddleware
from backend.app.core.csrf import CSRFMiddleware
from backend.app.api.v1.api import api_router
from backend.app.db.seed import seed_demo_users
from backend.app.api.v1.endpoints.health import health_check

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Demo users are seeded ONLY in non-production environments (development/testing/demo)
        if settings.ENVIRONMENT.lower() != "production":
            seed_demo_users(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        f"**{settings.TAGLINE}**\n\n"
        f"{settings.SUBTITLE}\n\n"
        f"> **Safety & Non-Clinical Scope Notice:** {settings.DISCLAIMER}"
    ),
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# 1. Restrictive CORS Allowlist
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Total-Count", "X-Idempotency-Key"],
)

# 2. Idempotency Middleware for Safe Retries & Offline Sync
app.add_middleware(IdempotencyMiddleware)

# 3. CSRF Protection Middleware for Cookie-based Sessions
app.add_middleware(CSRFMiddleware)

# 4. Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["X-RetinaX-Scope"] = "Operational-Care-Continuity-Only"
    return response

# 5. Validation Exception Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Input validation failed. Please check submitted fields.",
            "details": exc.errors()
        }
    )

# 6. Top-level Health Endpoint (for container orchestrator / ECS / health checks)
@app.get("/health", tags=["Health"])
def top_health():
    db = SessionLocal()
    try:
        return health_check(db)
    finally:
        db.close()

# 7. API V1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# 8. Backward compatibility mount for /api routes (maps /api/* to /api/v1/*)
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
