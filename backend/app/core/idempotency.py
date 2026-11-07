import json
import re
from datetime import datetime, timezone
from typing import Optional, Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal
from backend.app.models.idempotency import (
    IdempotencyRecord,
    compute_request_hash,
    claim_or_get_idempotency_record,
    complete_idempotency_record,
    release_failed_idempotency_record
)

UUID_OR_SAFE_KEY_PATTERN = re.compile(r"^[0-9a-zA-Z\-_]{8,64}$")

class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Idempotency only applies to mutating methods
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return await call_next(request)

        idempotency_key = request.headers.get("X-Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        # 1. Validate idempotency key format
        if not UUID_OR_SAFE_KEY_PATTERN.match(idempotency_key):
            return Response(
                content=json.dumps({"detail": "Invalid X-Idempotency-Key format. Must be an 8-64 character UUID or token."}),
                status_code=status.HTTP_400_BAD_REQUEST,
                media_type="application/json"
            )

        # 2. Read request body & compute deterministic hash
        body_bytes = await request.body()
        endpoint = request.url.path
        req_hash = compute_request_hash(request.method, endpoint, body_bytes)

        # 3. Extract authenticated user ID if session or bearer token exists
        user_id = None
        auth_header = request.headers.get("Authorization", "")
        cookie_token = request.cookies.get("retinax_session", "")
        token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else cookie_token

        if token:
            try:
                from backend.app.core.security import decode_access_token
                payload = decode_access_token(token)
                if payload and "sub" in payload:
                    user_id = int(payload["sub"])
            except Exception:
                pass

        # 4. Atomically claim key or check existing execution
        db: Session = SessionLocal()
        record_id = None
        try:
            claim_status, record = claim_or_get_idempotency_record(
                db=db,
                key=idempotency_key,
                user_id=user_id,
                endpoint=endpoint,
                request_hash=req_hash,
                ttl_hours=24
            )

            if claim_status == "HASH_MISMATCH":
                return Response(
                    content=json.dumps({
                        "error": "IDEMPOTENCY_KEY_REUSE_MISMATCH",
                        "detail": "Idempotency key conflict: This key was previously used with different request parameters or payload."
                    }),
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    media_type="application/json"
                )

            if claim_status == "IN_FLIGHT":
                return Response(
                    content=json.dumps({
                        "error": "CONCURRENT_REQUEST_IN_FLIGHT",
                        "detail": "A concurrent request with this idempotency key is currently being processed. Please retry shortly."
                    }),
                    status_code=status.HTTP_409_CONFLICT,
                    media_type="application/json"
                )

            if claim_status == "REPLAY" and record:
                headers = {
                    "X-Cache-Lookup": "HIT-IDEMPOTENT",
                    "X-Original-Timestamp": record.created_at.isoformat() if record.created_at else ""
                }
                return Response(
                    content=record.response_body or "",
                    status_code=record.response_code or 200,
                    media_type="application/json",
                    headers=headers
                )

            # claim_status == "CLAIMED": we hold the atomic reservation lock!
            if record:
                record_id = record.id

        finally:
            db.close()

        # 5. Execute downstream operation
        try:
            response = await call_next(request)
        except Exception as exc:
            # If downstream unhandled crash occurs, release the reservation so client can retry
            if record_id:
                cleanup_db = SessionLocal()
                try:
                    release_failed_idempotency_record(cleanup_db, record_id)
                finally:
                    cleanup_db.close()
            raise exc

        # 6. If request completed (even client error 4xx), persist completed response
        if response.status_code < 500 and record_id:
            response_body_sections = [section async for section in response.body_iterator]
            full_body = b"".join(response_body_sections)

            save_db = SessionLocal()
            try:
                complete_idempotency_record(
                    db=save_db,
                    record_id=record_id,
                    response_code=response.status_code,
                    response_body=full_body.decode("utf-8", errors="replace")
                )
            finally:
                save_db.close()

            return Response(
                content=full_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        elif response.status_code >= 500 and record_id:
            # On transient server error, release the reservation to allow subsequent retry
            save_db = SessionLocal()
            try:
                release_failed_idempotency_record(save_db, record_id)
            finally:
                save_db.close()

        return response
