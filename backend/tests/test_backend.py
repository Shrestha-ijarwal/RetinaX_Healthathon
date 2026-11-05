import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

# Helper: Get auth headers for a role
def get_auth_headers(email: str, password: str) -> dict:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# =========================================================================
# 1. Health & Scope Compliance Declarations
# =========================================================================
def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "Strict non-clinical AI scope" in data["compliance"]
    assert "RetinaX Care" in data["service"]

def test_api_v1_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

# =========================================================================
# 2. Authentication & Session Management
# =========================================================================
def test_auth_login_all_three_roles():
    # Specialist
    res_spec = client.post("/api/v1/auth/login", json={"email": "specialist@retinax.care", "password": "Specialist@2026"})
    assert res_spec.status_code == 200
    assert res_spec.json()["user"]["role"] == "Specialist"

    # Coordinator
    res_coord = client.post("/api/v1/auth/login", json={"email": "coordinator@retinax.care", "password": "Coordinator@2026"})
    assert res_coord.status_code == 200
    assert res_coord.json()["user"]["role"] == "Care Coordinator"

    # Admin
    res_admin = client.post("/api/v1/auth/login", json={"email": "admin@retinax.care", "password": "Admin@2026"})
    assert res_admin.status_code == 200
    assert res_admin.json()["user"]["role"] == "Administrator"

def test_auth_login_invalid_password():
    res = client.post("/api/v1/auth/login", json={"email": "specialist@retinax.care", "password": "WrongPassword"})
    assert res.status_code == 401

def test_auth_get_me():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == "coordinator@retinax.care"

def test_unauthenticated_access_blocked():
    anon_client = TestClient(app)
    res = anon_client.get("/api/v1/patients")
    assert res.status_code == 401

# =========================================================================
# 3. RBAC Enforcement Tests
# =========================================================================
def test_coordinator_cannot_submit_specialist_review():
    coord_headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    payload = {
        "clinician_name": "Coordinator Fake Specialist",
        "clinical_assessment": "Unpermitted attempt",
        "followup_instructions": "None",
        "referral_status": "Hospital Follow-Up"
    }
    # Attempt review as coordinator
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
        "clinician_name": "Dr. Suresh Chandran, MS",
        "clinician_title": "Dr.",
        "clinician_specialty": "Ophthalmology",
        "clinician_facility": "District Eye Hospital",
        "registration_number": "MCI-2016-849201",
        "clinical_assessment": "Bilateral mild non-proliferative changes verified in color fundus photos.",
        "followup_instructions": "Review in 6 months at hospital retina clinic. Strict glycemic control advised.",
        "referral_status": "Hospital Follow-Up (6 Months)",
        "notes": "Reviewed in tele-ophthalmology reading queue."
    }
    res = client.post("/api/v1/reviews/RX-1007", json=payload, headers=spec_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "success"

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
        "all",
        "needs_attention",
        "pending_screening",
        "scheduled",
        "screening_completed",
        "report_missing",
        "awaiting_review",
        "followup_pending",
        "unable_to_contact",
        "completed"
    ]
    for f in filters:
        res = client.get(f"/api/v1/patients?filter={f}", headers=headers)
        assert res.status_code == 200
        assert "patients" in res.json()

def test_patient_detail():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    res = client.get("/api/v1/patients/RX-1001", headers=headers)
    assert res.status_code == 200
    p = res.json()
    assert p["id"] == "RX-1001"
    assert p["name"] == "Ramesh Kumar"
    assert "timeline" in p
    assert "documents" in p
    assert "specialist_review" in p
    assert "followup" in p

def test_patient_completeness_check():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    res = client.get("/api/v1/patients/RX-1006/completeness", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "score_percentage" in data
    assert "missing_items" in data
    assert "checks" in data

# =========================================================================
# 5. Document Ingestion, Magic-Byte Validation, and Secure Download
# =========================================================================
def test_document_magic_byte_rejection():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    # Attempt uploading fake executable or plain text masquerading as PDF
    fake_pdf = b"NOT_A_REAL_PDF_FILE_JUST_PLAIN_TEXT"
    files = {"file": ("fake_doc.pdf", fake_pdf, "application/pdf")}
    res = client.post(
        "/api/v1/documents/RX-1001",
        files=files,
        data={"title": "Fake PDF", "doc_type": "Retinal Screening Report"},
        headers=headers
    )
    assert res.status_code == 400
    assert "unsupported or corrupt" in res.json()["detail"].lower()

def test_document_valid_pdf_upload_and_download():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    # Minimal valid PDF binary
    valid_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\nxref\n0 3\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \ntrailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n115\n%%EOF"
    files = {"file": ("screening_test.pdf", valid_pdf, "application/pdf")}
    res = client.post(
        "/api/v1/documents/RX-1001",
        files=files,
        data={"title": "Test Screening PDF", "doc_type": "Retinal Screening Report"},
        headers=headers
    )
    assert res.status_code == 201
    doc_id = res.json()["id"]

    # Now test authenticated download
    res_down = client.get(f"/api/v1/documents/{doc_id}/download", headers=headers)
    assert res_down.status_code == 200
    assert res_down.headers["content-type"] == "application/pdf"
    assert res_down.content.startswith(b"%PDF-1.4")

# =========================================================================
# 6. Follow-Up Workflows & Contact Attempts
# =========================================================================
def test_followup_worklist_and_update():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    res = client.get("/api/v1/followups", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) > 0

    # Update follow-up with contact attempt
    update_payload = {
        "status": "Scheduled",
        "planned_date": "2026-11-20",
        "notes": "Patient confirmed clinic visit.",
        "contact_attempt": {
            "method": "Phone Call",
            "result": "Patient agreed to hospital appointment on Nov 20",
            "staff": "Ananya Sharma"
        }
    }
    res_up = client.post("/api/v1/followups/RX-1001", json=update_payload, headers=headers)
    assert res_up.status_code == 200
    assert res_up.json()["status"] == "success"

# =========================================================================
# 7. Operational Tasks
# =========================================================================
def test_operational_task_lifecycle():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    create_payload = {
        "title": "Coordinate Transport Escort",
        "description": "Arrange village vehicle for patient hospital visit.",
        "priority": "High"
    }
    res_create = client.post("/api/v1/tasks/RX-1002", json=create_payload, headers=headers)
    assert res_create.status_code == 201
    task_id = res_create.json()["id"]

    res_comp = client.post(
        f"/api/v1/tasks/RX-1002/tasks/{task_id}/complete",
        json={"completion_note": "Transport arranged with ASHA worker."},
        headers=headers
    )
    assert res_comp.status_code == 200
    assert res_comp.json()["status"] == "Completed"

# =========================================================================
# 8. Simulated Bilingual Reminders
# =========================================================================
def test_simulated_reminder_dispatch():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    payload = {
        "type": "Follow-Up Attendance",
        "language": "hi",
        "custom_note": "समय पर आएं"
    }
    res = client.post("/api/v1/reminders/RX-1001", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert "DEMO - NOT SENT TO PATIENT" in data["disclaimer"]
    assert "अनुस्मारक" in data["text_hi"]

# =========================================================================
# 9. Continuity Analytics & Care Gap Radar
# =========================================================================
def test_analytics_and_gap_radar():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    res_an = client.get("/api/v1/analytics", headers=headers)
    assert res_an.status_code == 200
    assert "loop_closure_rate_pct" in res_an.json()["counts"]
    assert "denominator_explanation" in res_an.json()

    res_gap = client.get("/api/v1/analytics/gap-radar", headers=headers)
    assert res_gap.status_code == 200
    assert "flagged_patients" in res_gap.json()

# =========================================================================
# 10. FHIR R4 Interoperability Endpoints
# =========================================================================
def test_fhir_endpoints():
    headers = get_auth_headers("coordinator@retinax.care", "Coordinator@2026")
    res_p = client.get("/api/v1/fhir/Patient/RX-1001", headers=headers)
    assert res_p.status_code == 200
    assert res_p.json()["resourceType"] == "Patient"
    assert res_p.json()["id"] == "RX-1001"

    res_t = client.get("/api/v1/fhir/Task", headers=headers)
    assert res_t.status_code == 200
    assert res_t.json()["resourceType"] == "Bundle"

# =========================================================================
# 11. Strict Non-Clinical Scope Compliance Verification
# =========================================================================
def test_zero_prohibited_clinical_terms():
    import os
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    prohibited_terms = [
        "grad-cam", "gradcam", "dr grade", "dr_grade",
        "referable dr", "risk score", "trained_dr_model", "trained_vessel", "idrid"
    ]
    findings = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in [".py"]:
            if "test" in p.name:
                continue
            content = p.read_text(encoding="utf-8", errors="ignore").lower()
            for term in prohibited_terms:
                if term in content:
                    findings.append((str(p.name), term))
    assert len(findings) == 0, f"Prohibited clinical terms found: {findings}"
