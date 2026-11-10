import io
import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_auth_headers(email: str, password: str) -> dict:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = res.json().get("access_token") or res.cookies.get("retinax_session")
    return {"Authorization": f"Bearer {token}"}

# =========================================================================
# 1. Health and Scope Compliance Endpoints
# =========================================================================
def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "compliance" in data
    assert "disclaimer" in data

def test_api_v1_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_production_configuration_rejects_insecure_secrets():
    from backend.app.core.config import Settings

    # 1. Blank or weak secrets in production must raise ValueError
    with pytest.raises(ValueError, match="CRITICAL SECURITY CONFIGURATION ERROR"):
        Settings(ENVIRONMENT="production", SECRET_KEY="")

    with pytest.raises(ValueError, match="CRITICAL SECURITY CONFIGURATION ERROR"):
        Settings(ENVIRONMENT="production", SECRET_KEY="short-key")

    with pytest.raises(ValueError, match="CRITICAL SECURITY CONFIGURATION ERROR"):
        Settings(ENVIRONMENT="production", SECRET_KEY="retinax-care-super-secret-key-healthathon-2026-prod-grade")

    # 2. Strong 32+ character external key in production must succeed
    strong_key = "a_cryptographically_strong_prod_secret_key_exceeding_32_characters"
    prod_cfg = Settings(ENVIRONMENT="production", SECRET_KEY=strong_key)
    assert prod_cfg.SECRET_KEY == strong_key

    # 3. Development mode provides distinct demo fallback
    dev_cfg = Settings(ENVIRONMENT="development", SECRET_KEY="")
    assert "development-only" in dev_cfg.SECRET_KEY

# =========================================================================
# 2. Authentication, Cookie & CSRF Security Tests
# =========================================================================
def test_auth_login_all_three_roles():
    roles = [
        ("coordinator@retinax.care", "Coordinator@2026", "Care Coordinator"),
        ("specialist@retinax.care", "Specialist@2026", "Specialist"),
        ("admin@retinax.care", "Admin@2026", "Administrator")
    ]
    for email, password, expected_role in roles:
        res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["user"]["role"] == expected_role
        assert "retinax_session" in res.cookies
        assert "retinax_csrf_token" in res.cookies

def test_auth_login_invalid_password():
    res = client.post("/api/v1/auth/login", json={"email": "coordinator@retinax.care", "password": "WrongPassword!"})
    assert res.status_code == 401

def test_auth_get_me():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["role"] == "Care Coordinator"

def test_unauthenticated_access_blocked():
    anon_client = TestClient(app)
    res = anon_client.get("/api/v1/patients")
    assert res.status_code == 401

def test_auth_logout():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    res = client.post("/api/v1/auth/logout", headers=headers)
    assert res.status_code == 200
    assert "Successfully logged out" in res.json()["message"]

def test_csrf_protection_with_cookie_session():
    # 1. Login to obtain session cookie & CSRF cookie
    login_res = client.post("/api/v1/auth/login", json={"email": "coordinator@retinax.care", "password": "Coordinator@2026"})
    assert login_res.status_code == 200
    session_cookie = login_res.cookies.get("retinax_session")
    csrf_cookie = login_res.cookies.get("retinax_csrf_token")

    # 2. State-changing request WITH cookie BUT WITHOUT X-CSRF-Token header -> must be rejected (HTTP 403)
    c_client = TestClient(app, cookies={"retinax_session": session_cookie, "retinax_csrf_token": csrf_cookie})
    reject_res = c_client.post(
        "/api/v1/followups/RX-1001",
        json={"status": "Scheduled", "planned_date": "2027-01-15"}
    )
    assert reject_res.status_code == 403
    assert "CSRF validation failed" in reject_res.json()["detail"]

    # 3. State-changing request WITH matching X-CSRF-Token header -> accepted (HTTP 200)
    accept_res = c_client.post(
        "/api/v1/followups/RX-1001",
        json={"status": "Scheduled", "planned_date": "2027-01-15"},
        headers={"X-CSRF-Token": csrf_cookie}
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "success"

# =========================================================================
# 3. RBAC Enforcement Tests
# =========================================================================
def test_coordinator_cannot_submit_specialist_review():
    coord_headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    payload = {
        "assigned_specialist": "Coordinator Impersonator",
        "review_status": "review_completed",
        "operational_notes": "Unpermitted operational review submission attempt",
        "clinician_instruction": "None"
    }
    res = client.post("/api/v1/reviews/RX-1007", json=payload, headers=coord_headers)
    assert res.status_code == 403
    assert "not authorized" in res.json()["detail"].lower()

def test_coordinator_cannot_access_audit_logs():
    coord_headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    res = client.get("/api/v1/audit", headers=coord_headers)
    assert res.status_code == 403

def test_admin_can_access_audit_logs():
    admin_headers = get_auth_headers("admin@retinax.care", "Admin@2026")
    res = client.get("/api/v1/audit", headers=admin_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_specialist_can_submit_specialist_review():
    spec_headers = get_auth_headers("specialist@retinax.care", "Specialist@2026")
    payload = {
        "assigned_specialist": "Dr. Suresh Chandran, MS",
        "clinician_title": "Dr.",
        "clinician_specialty": "Ophthalmology",
        "clinician_facility": "District Eye Hospital",
        "registration_number": "MCI-2016-849201",
        "review_status": "followup_initiated",
        "operational_notes": "Screening report legibility verified. Color photographs adequate for tele-triage.",
        "clinician_instruction": "Attributed directive: Coordinate follow-up at district hospital within 6 months.",
        "task_owner": "Care Coordinator",
        "operational_task_status": "In Progress",
        "reconciliation_status": "Reconciled"
    }
    res = client.post("/api/v1/reviews/RX-1007", json=payload, headers=spec_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert res.json()["review_status"] == "followup_initiated"

# =========================================================================
# 4. Patient Module & Operational Filters
# =========================================================================
def test_patient_list_and_metrics():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    res = client.get("/api/v1/patients", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["patients"]) == 12
    assert data["metrics"]["total_patients"] == 12
    assert "report_missing" in data["metrics"]
    assert "awaiting_specialist_review" in data["metrics"]
    assert "care_loops_closed" in data["metrics"]

def test_patient_filters():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    filters = [
        "all", "needs_attention", "pending_screening", "scheduled",
        "screening_completed", "report_missing", "awaiting_review",
        "followup_pending", "unable_to_contact", "completed"
    ]
    for f in filters:
        res = client.get(f"/api/v1/patients?filter={f}", headers=headers)
        assert res.status_code == 200
        assert isinstance(res.json()["patients"], list)

def test_patient_detail():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    res = client.get("/api/v1/patients/RX-1001", headers=headers)
    assert res.status_code == 200
    p = res.json()
    assert p["id"] == "RX-1001"
    assert "timeline" in p
    assert "documents" in p
    assert "workflow_status" in p

def test_patient_completeness_check():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    res = client.get("/api/v1/patients/RX-1006/completeness", headers=headers)
    assert res.status_code == 200
    comp = res.json()
    assert "score_percentage" in comp or "percentage" in comp
    assert "checks" in comp or "checklist" in comp

# =========================================================================
# 5. Document Security & Binary Magic-Byte Inspection
# =========================================================================
def test_document_magic_byte_rejection():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    fake_file = {"file": ("malicious.pdf", b"This is plain text pretending to be a PDF", "application/pdf")}
    res = client.post("/api/v1/documents/RX-1001", files=fake_file, data={"title": "Fake PDF", "doc_type": "Retinal Screening Report", "source": "Outreach"}, headers=headers)
    assert res.status_code == 400
    assert "unsupported" in res.json()["detail"].lower() or "corrupt" in res.json()["detail"].lower()

def test_document_valid_pdf_upload_and_download():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    valid_pdf_bytes = (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n185\n%%EOF"
    )
    valid_file = {"file": ("screening_test.pdf", valid_pdf_bytes, "application/pdf")}
    upload_res = client.post(
        "/api/v1/documents/RX-1001",
        files=valid_file,
        data={"title": "Test Screening Upload", "doc_type": "Retinal Screening Report", "source": "District Camp"},
        headers=headers
    )
    assert upload_res.status_code in [200, 201]
    doc_id = upload_res.json()["id"]

    # Verify download
    down_res = client.get(f"/api/v1/documents/download/{doc_id}", headers=headers)
    assert down_res.status_code == 200
    assert down_res.headers["content-type"] == "application/pdf"
    assert down_res.content.startswith(b"%PDF-1.4")

    # Clean up test artifact so test runs do not pollute document directories
    from backend.app.core.database import SessionLocal
    from backend.app.models.document import Document
    from backend.app.core.config import settings
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            if doc.storage_key:
                p = settings.STORAGE_DIR / doc.storage_key
                if p.exists():
                    p.unlink()
            db.delete(doc)
            db.commit()
    finally:
        db.close()

# =========================================================================
# 6. Follow-up and Contact Attempt Worklist
# =========================================================================
def test_followup_worklist_and_update():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    res = client.get("/api/v1/followups", headers=headers)
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 12

    # Add contact attempt
    att_res = client.post(
        "/api/v1/followups/RX-1001/attempts",
        json={"method": "Phone Call", "result": "Patient unreachable", "notes": "Phone rang with no answer."},
        headers=headers
    )
    assert att_res.status_code == 200
    assert att_res.json()["status"] == "success"

# =========================================================================
# 7. Operational Tasks Lifecycle
# =========================================================================
def test_operational_task_lifecycle():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    c_res = client.post(
        "/api/v1/tasks/RX-1001",
        json={"title": "Verify Contact Number", "description": "Call local ASHA to confirm contact", "priority": "High"},
        headers=headers
    )
    assert c_res.status_code in [200, 201]
    task_id = c_res.json()["id"]

    # Complete task
    comp_res = client.post(
        f"/api/v1/tasks/RX-1001/tasks/{task_id}/complete",
        json={"completion_note": "Number confirmed with local health worker"},
        headers=headers
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "Completed"

# =========================================================================
# 8. Idempotency Support & Safe Duplicate Replay
# =========================================================================
def test_idempotent_duplicate_request_replay():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    idempotency_key = str(uuid.uuid4())
    headers["X-Idempotency-Key"] = idempotency_key

    payload = {
        "title": f"Idempotent Task {idempotency_key[:8]}",
        "description": "Ensures duplicate offline sync mutations do not create duplicate database records",
        "priority": "Medium"
    }

    # First request -> executed and recorded
    res1 = client.post("/api/v1/tasks/RX-1002", json=payload, headers=headers)
    assert res1.status_code in [200, 201]
    task_id_1 = res1.json()["id"]

    # Second request with SAME idempotency key -> cached replay, same ID
    res2 = client.post("/api/v1/tasks/RX-1002", json=payload, headers=headers)
    assert res2.status_code == res1.status_code
    assert res2.headers.get("X-Cache-Lookup") == "HIT-IDEMPOTENT"
    assert res2.json()["id"] == task_id_1

def test_invalid_idempotency_key_format_rejected():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    headers["X-Idempotency-Key"] = "bad key with spaces!@#"
    res = client.post("/api/v1/tasks/RX-1002", json={"title": "Bad Key Test"}, headers=headers)
    assert res.status_code == 400
    assert "Invalid X-Idempotency-Key" in res.json()["detail"]

def test_idempotency_key_reuse_different_payload_rejected():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    idempotency_key = str(uuid.uuid4())
    headers["X-Idempotency-Key"] = idempotency_key

    # First request
    res1 = client.post(
        "/api/v1/tasks/RX-1002",
        json={"title": f"Initial Task {idempotency_key[:6]}", "priority": "Low"},
        headers=headers
    )
    assert res1.status_code in [200, 201]

    # Second request with SAME key but DIFFERENT payload -> rejected with HTTP 422
    res2 = client.post(
        "/api/v1/tasks/RX-1002",
        json={"title": f"TAMPERED TASK {idempotency_key[:6]}", "priority": "High"},
        headers=headers
    )
    assert res2.status_code == 422
    assert res2.json()["error"] == "IDEMPOTENCY_KEY_REUSE_MISMATCH"

def test_idempotency_concurrent_in_flight_rejected():
    from backend.app.core.database import SessionLocal
    from backend.app.models.idempotency import IdempotencyRecord, compute_request_hash
    from datetime import datetime, timezone, timedelta
    import json

    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    idempotency_key = str(uuid.uuid4())
    headers["X-Idempotency-Key"] = idempotency_key

    endpoint = "/api/v1/tasks/RX-1002"
    payload = {"title": "Concurrent In-Flight Test", "priority": "Medium"}
    body_bytes = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    req_hash = compute_request_hash("POST", endpoint, body_bytes)
    headers["Content-Type"] = "application/json"

    # Pre-insert a PENDING reservation in the database for this user with matching hash
    from backend.app.models.user import User
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "coordinator@retinax.care").first()
        user_id = user.id if user else None
        rec = IdempotencyRecord(
            key=idempotency_key,
            user_id=user_id,
            endpoint=endpoint,
            request_hash=req_hash,
            status="PENDING",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        db.add(rec)
        db.commit()
    finally:
        db.close()

    # Concurrent request attempting to use this in-flight reservation must receive HTTP 409
    res = client.post(
        endpoint,
        content=body_bytes,
        headers=headers
    )
    assert res.status_code == 409
    assert res.json()["error"] == "CONCURRENT_REQUEST_IN_FLIGHT"

# =========================================================================
# 9. Optimistic Concurrency Control (OCC) Tests
# =========================================================================
def test_optimistic_concurrency_stale_version_rejected():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")

    # 1. First update setting known status
    u1 = client.post(
        "/api/v1/followups/RX-1003",
        json={"status": "Scheduled", "planned_date": "2027-02-01"},
        headers=headers
    )
    assert u1.status_code == 200

    # 2. Simulate concurrent update attempting to overwrite with a stale expected_version
    stale_payload = {
        "status": "Completed",
        "planned_date": "2027-02-01",
        "expected_version": 99999  # Deliberately stale version
    }
    conflict_res = client.post("/api/v1/followups/RX-1003", json=stale_payload, headers=headers)
    assert conflict_res.status_code == 409
    data = conflict_res.json()["detail"]
    assert data["error"] == "VERSION_CONFLICT"
    assert "current_version" in data
    assert data["expected_version"] == 99999

def test_patient_optimistic_concurrency_stale_version_rejected():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    p_res = client.get("/api/v1/patients/RX-1001", headers=headers)
    assert p_res.status_code == 200
    current_ver = p_res.json().get("version", 1)

    # Attempt update with stale version
    stale_res = client.patch(
        "/api/v1/patients/RX-1001",
        json={"facility": "Stale Facility Test", "expected_version": 99999},
        headers=headers
    )
    assert stale_res.status_code == 409
    assert stale_res.json()["detail"]["error"] == "VERSION_CONFLICT"

    # Update with correct version
    ok_res = client.patch(
        "/api/v1/patients/RX-1001",
        json={"facility": "Primary Health Centre Alpha", "expected_version": current_ver},
        headers=headers
    )
    assert ok_res.status_code == 200
    assert ok_res.json()["version"] == current_ver + 1

def test_task_completion_optimistic_concurrency_stale_version_rejected():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    # Create task
    c_res = client.post(
        "/api/v1/tasks/RX-1001",
        json={"title": "OCC Task Test", "priority": "High"},
        headers=headers
    )
    assert c_res.status_code in [200, 201]
    task = c_res.json()
    task_id = task["id"]
    task_ver = task.get("version", 1)

    # Attempt completion with stale version
    stale_res = client.post(
        f"/api/v1/tasks/RX-1001/tasks/{task_id}/complete",
        json={"completion_note": "Stale note", "expected_version": 99999},
        headers=headers
    )
    assert stale_res.status_code == 409
    assert stale_res.json()["detail"]["error"] == "VERSION_CONFLICT"

    # Complete with correct version
    ok_res = client.post(
        f"/api/v1/tasks/RX-1001/tasks/{task_id}/complete",
        json={"completion_note": "Valid OCC note", "expected_version": task_ver},
        headers=headers
    )
    assert ok_res.status_code == 200
    assert ok_res.json()["status"] == "Completed"
    assert ok_res.json()["version"] == task_ver + 1

# =========================================================================
# 10. Reminder Simulation & Celery Tasks
# =========================================================================
def test_simulated_reminder_dispatch():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    res = client.post(
        "/api/v1/reminders/RX-1001/dispatch",
        json={"type": "Follow-Up Attendance", "language": "en", "channel": "SMS"},
        headers=headers
    )
    assert res.status_code in [200, 201]
    rem = res.json()
    assert "[DEMO — NOT SENT TO PATIENT]" in rem["text_en"]
    assert "Simulated" in rem["sent_status"]

# =========================================================================
# 11. Analytics & Operational Care Gap Radar
# =========================================================================
def test_analytics_and_gap_radar():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    res = client.get("/api/v1/analytics/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "counts" in data
    assert "avg_turnaround_days" in data
    assert "disclaimer" in data

    radar_res = client.get("/api/v1/analytics/gap-radar", headers=headers)
    assert radar_res.status_code == 200
    assert "flagged_patients" in radar_res.json()

# =========================================================================
# 12. HL7 / FHIR R4 Operational Schemas & Validation
# =========================================================================
def test_fhir_endpoints_and_validation():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    res_p = client.get("/api/v1/fhir/Patient/RX-1001", headers=headers)
    assert res_p.status_code == 200
    assert res_p.json()["resourceType"] == "Patient"
    assert res_p.json()["id"] == "RX-1001"

    res_t = client.get("/api/v1/fhir/Task", headers=headers)
    assert res_t.status_code == 200
    assert res_t.json()["resourceType"] == "Bundle"

    # Test valid Bundle validation
    valid_bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "total": 1,
        "entry": [
            {
                "fullUrl": "https://retinax.care/fhir/Patient/RX-TEST",
                "resource": {
                    "resourceType": "Patient",
                    "id": "RX-TEST",
                    "gender": "female"
                }
            }
        ]
    }
    b_res = client.post("/api/v1/fhir/validate", json=valid_bundle, headers=headers)
    assert b_res.status_code == 200
    assert b_res.json()["status"] == "valid"

    # Test invalid FHIR resource rejection
    invalid_task = {
        "resourceType": "Task",
        "id": "bad-task",
        "status": "ILLEGAL_STATUS_NOT_IN_FHIR_R4",
        "description": "Invalid test task"
    }
    val_res = client.post("/api/v1/fhir/validate", json=invalid_task, headers=headers)
    assert val_res.status_code == 422
    assert "validation failure" in val_res.json()["detail"].lower()

# =========================================================================
# 13. Strict Non-Clinical Scope Compliance Verification
# =========================================================================
def test_zero_prohibited_clinical_terms():
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    prohibited_terms = [
        "grad-cam", "gradcam", "dr grade", "dr_grade",
        "referable dr", "trained_dr_model", "trained_vessel", "idrid"
    ]
    findings = []
    for p in root.rglob("*.py"):
        if "test" in p.name:
            continue
        content = p.read_text(encoding="utf-8", errors="ignore").lower()
        for term in prohibited_terms:
            if term in content:
                findings.append((p.name, term))
    assert len(findings) == 0, f"Prohibited clinical terms found: {findings}"

# =========================================================================
# 14. Production Hardening & Demo Seeding Protection Tests
# =========================================================================
def test_demo_seeding_strictly_blocked_in_production(monkeypatch):
    from backend.app.core.database import SessionLocal
    from backend.app.db.seed import seed_demo_users, seed_synthetic_patients

    monkeypatch.setenv("ENVIRONMENT", "production")
    db = SessionLocal()
    try:
        with pytest.raises(RuntimeError, match="CRITICAL SECURITY CONFIGURATION: Demo user account seeding is strictly disabled"):
            seed_demo_users(db)

        with pytest.raises(RuntimeError, match="CRITICAL SECURITY CONFIGURATION: Synthetic patient seeding is strictly disabled"):
            seed_synthetic_patients(db)
    finally:
        db.close()

def test_production_login_cookie_only_no_bearer_in_json(monkeypatch):
    from backend.app.core.config import settings
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    res = client.post("/api/v1/auth/login", json={"email": "coordinator@retinax.care", "password": "Coordinator@2026"})
    assert res.status_code == 200
    body = res.json()
    # In production mode, access_token in JSON is None (cookie-only auth)
    assert body.get("access_token") is None
    assert body.get("token_type") == "cookie"
    assert "retinax_session" in res.cookies
    assert "retinax_csrf_token" in res.cookies

# =========================================================================
# 15. Concurrent Idempotency & Unauthenticated Reservation Tests
# =========================================================================
def test_unauthenticated_idempotency_key_uniqueness_enforced():
    from backend.app.core.database import SessionLocal
    from backend.app.models.idempotency import IdempotencyRecord, claim_or_get_idempotency_record

    key = f"unauth-{uuid.uuid4().hex[:16]}"
    db = SessionLocal()
    try:
        status1, rec1 = claim_or_get_idempotency_record(
            db=db, key=key, user_id=None, endpoint="/api/v1/test", request_hash="hash123"
        )
        assert status1 == "CLAIMED"
        assert rec1 is not None

        # Second attempt with same key and user_id=None must NOT create multiple reservations
        status2, rec2 = claim_or_get_idempotency_record(
            db=db, key=key, user_id=None, endpoint="/api/v1/test", request_hash="hash123"
        )
        assert status2 == "IN_FLIGHT"
    finally:
        db.query(IdempotencyRecord).filter(IdempotencyRecord.key == key).delete()
        db.commit()
        db.close()

def test_concurrent_idempotent_requests_execute_only_once():
    import concurrent.futures
    import json
    from backend.app.core.database import SessionLocal
    from backend.app.models.operational_task import OperationalTask

    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    unique_suffix = uuid.uuid4().hex[:12]
    idempotency_key = f"conc-idemp-{unique_suffix}"
    headers["X-Idempotency-Key"] = idempotency_key
    headers["Content-Type"] = "application/json"

    task_title = f"Concurrent Idempotent Task {unique_suffix}"
    payload = {"title": task_title, "priority": "High"}
    body_bytes = json.dumps(payload, separators=(',', ':')).encode("utf-8")

    def make_request():
        c = TestClient(app)
        return c.post("/api/v1/tasks/RX-1002", content=body_bytes, headers=headers)

    # Fire 5 concurrent requests with the exact same idempotency key
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(5)]
        responses = [f.result() for f in futures]

    status_codes = [r.status_code for r in responses]
    # At least one succeeded with 201/200; any others are either cached replays (200/201) or in-flight (409)
    assert any(s in [200, 201] for s in status_codes)

    # Critical check: verify EXACTLY ONE record was created in the database for this task title
    db = SessionLocal()
    try:
        tasks = db.query(OperationalTask).filter(OperationalTask.title == task_title).all()
        assert len(tasks) == 1, f"Expected exactly 1 task created, but found {len(tasks)}"
    finally:
        db.close()

# =========================================================================
# 16. Concurrent Optimistic Concurrency Control (OCC) Tests
# =========================================================================
def test_concurrent_optimistic_concurrency_race_condition_rejected():
    import concurrent.futures

    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    # Fetch initial patient version
    p_res = client.get("/api/v1/patients/RX-1001", headers=headers)
    assert p_res.status_code == 200
    base_version = p_res.json()["version"]

    def attempt_concurrent_update(i):
        c = TestClient(app)
        payload = {
            "facility": f"Concurrent PHC Center Attempt {i}",
            "expected_version": base_version
        }
        return c.patch("/api/v1/patients/RX-1001", json=payload, headers=headers)

    # 5 concurrent threads attempt to update RX-1001 based on the SAME initial version
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(attempt_concurrent_update, i) for i in range(5)]
        results = [f.result() for f in futures]

    successes = [r for r in results if r.status_code == 200]
    conflicts = [r for r in results if r.status_code == 409]

    # Exactly ONE simultaneous update can win; all other simultaneous updates MUST receive HTTP 409
    assert len(successes) == 1, f"Expected exactly 1 winning update, but got {len(successes)}"
    assert len(conflicts) == 4, f"Expected 4 version conflicts, but got {len(conflicts)}"

    for c_res in conflicts:
        err = c_res.json()["detail"]
        assert err["error"] == "VERSION_CONFLICT"
        assert err["expected_version"] == base_version

    # Verify that database version incremented by exactly 1
    p_final = client.get("/api/v1/patients/RX-1001", headers=headers)
    assert p_final.json()["version"] == base_version + 1

# =========================================================================
# 17. Offline Service Worker & Foreground Sync Contract Verification
# =========================================================================
def test_offline_sync_payload_and_csrf_contract():
    # Verify that header X-Expected-Version is accepted by endpoints when body expected_version is omitted
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    p_res = client.get("/api/v1/patients/RX-1002", headers=headers)
    curr_v = p_res.json()["version"]

    # Test that stale version passed via X-Expected-Version header triggers HTTP 409
    hdr_stale = dict(headers)
    hdr_stale["X-Expected-Version"] = str(curr_v - 1)
    stale_res = client.patch(
        "/api/v1/patients/RX-1002",
        json={"facility": "Header Version Test"},
        headers=hdr_stale
    )
    assert stale_res.status_code == 409
    assert stale_res.json()["detail"]["error"] == "VERSION_CONFLICT"

    # Test that matching version passed via X-Expected-Version header succeeds (HTTP 200)
    hdr_ok = dict(headers)
    hdr_ok["X-Expected-Version"] = str(curr_v)
    ok_res = client.patch(
        "/api/v1/patients/RX-1002",
        json={"facility": "Header Version Verified"},
        headers=hdr_ok
    )
    assert ok_res.status_code == 200
    assert ok_res.json()["version"] == curr_v + 1
