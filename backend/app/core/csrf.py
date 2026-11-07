import secrets
from typing import Callable
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from backend.app.core.config import settings

def generate_csrf_token() -> str:
    return secrets.token_hex(32)

class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware for Cookie-based Sessions.
    Verifies that state-changing requests (POST, PUT, PATCH, DELETE) authenticated
    via the 'retinax_session' cookie include a matching 'X-CSRF-Token' header
    matching the 'retinax_csrf_token' cookie.
    Requests using 'Authorization: Bearer' headers or public auth endpoints are exempt.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        is_mutation = request.method in ("POST", "PUT", "PATCH", "DELETE")
        path = request.url.path

        # Exempt paths
        exempt_paths = (
            "/api/v1/auth/login",
            "/api/auth/login",
            "/api/v1/fhir/validate",
            "/health",
            "/docs",
            "/openapi.json"
        )
        is_exempt = any(path.startswith(p) for p in exempt_paths)

        has_bearer = "authorization" in request.headers and request.headers["authorization"].startswith("Bearer ")
        has_session_cookie = "retinax_session" in request.cookies

        # If mutating using session cookie and not exempt, enforce CSRF
        if is_mutation and not is_exempt and has_session_cookie and not has_bearer:
            csrf_cookie = request.cookies.get("retinax_csrf_token")
            csrf_header = request.headers.get("X-CSRF-Token")

            if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_cookie, csrf_header):
                return Response(
                    content='{"detail": "CSRF validation failed. Missing or invalid X-CSRF-Token header."}',
                    status_code=status.HTTP_403_FORBIDDEN,
                    media_type="application/json"
                )

        response = await call_next(request)

        # Automatically ensure a CSRF cookie is present for the client
        if "retinax_csrf_token" not in request.cookies:
            token = generate_csrf_token()
            is_prod = (settings.ENVIRONMENT.lower() == "production")
            response.set_cookie(
                key="retinax_csrf_token",
                value=token,
                httponly=False,  # Must be readable by frontend JS to set header
                samesite="lax",
                secure=is_prod,
                path="/"
            )

        return response
