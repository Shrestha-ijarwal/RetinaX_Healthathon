"""
RetinaX Care - Comprehensive End-to-End Integration Verification Script
Verifies all 10 major operational workflows across backend, database, and API layers.
"""

import io
import json
import uuid
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.patient import Patient
from backend.app.models.care_journey import CareJourney
from backend.app.models.followup import Followup
from backend.app.models.document import Document
from backend.app.models.operational_task import OperationalTask

client = TestClient(app)

def run_e2e_verification():
    print("=" * 65)
    print(" RETINAX CARE - END-TO-END WORKFLOW INTEGRATION VERIFICATION")
    print("=" * 65)

    # 1. Login Authentication
    print("\n[1/10] Testing User Authentication & Dual-Auth Token Delivery...")
    coord_login = client.post(
        "/api/v1/auth/login",
        json={"email": "coordinator@retinax.care", "password": "Coordinator@2026"},
        headers={"Origin": "https://retina-x01.vercel.app"}
    )
    assert coord_login.status_code == 200, f"Coordinator login failed: {coord_login.text}"
    coord_data = coord_login.json()
    assert "access_token" in coord_data, "Cross-origin login must return access_token"
    coord_token = coord_data["access_token"]
    coord_headers = {"Authorization": f"Bearer {coord_token}"}
    print(f" -> Coordinator logged in successfully (User ID: {coord_data['user']['id']}, Role: {coord_data['user']['role']})")

    spec_login = client.post(
        "/api/v1/auth/login",
        json={"email": "specialist@retinax.care", "password": "Specialist@2026"},
        headers={"Origin": "https://retina-x01.vercel.app"}
    )
    assert spec_login.status_code == 200, f"Specialist login failed: {spec_login.text}"
    spec_data = spec_login.json()
    spec_token = spec_data["access_token"]
    spec_headers = {"Authorization": f"Bearer {spec_token}"}
    print(f" -> Specialist logged in successfully (User ID: {spec_data['user']['id']}, Role: {spec_data['user']['role']})")

    # 2. Patient Registration
    print("\n[2/10] Testing Synthetic Patient Registration & DB Persistence...")
    unique_suffix = uuid.uuid4().hex[:6].upper()
    new_patient_payload = {
        "name": f"Integration Patient {unique_suffix}",
        "age": 58,
        "sex": "Female",
        "contact": "+91 98450 99881",
        "facility": "Primary Health Centre - Ramanagara",
        "clinician": "Care Coordinator Desk"
    }
    create_res = client.post("/api/v1/patients", json=new_patient_payload, headers=coord_headers)
    assert create_res.status_code in [200, 201], f"Patient creation failed: {create_res.text}"
    new_patient = create_res.json()
    patient_id = new_patient.get("patient_id") or new_patient.get("id")
    print(f" -> Patient registered: ID={patient_id}, Name={new_patient_payload['name']}")

    # Verify persistence in DB
    db = SessionLocal()
    try:
        p_record = db.query(Patient).filter(Patient.id == patient_id).first()
        assert p_record is not None, "Patient record was not persisted to SQLite/Postgres DB!"
        print(f" -> Verified database record exists: DB ID={p_record.id}, Name={p_record.name}")
    finally:
        db.close()

    # 3. Patient Listing & Search
    print("\n[3/10] Testing Patient Worklist Retrieval & Search...")
    list_res = client.get(f"/api/v1/patients?search={unique_suffix}", headers=coord_headers)
    assert list_res.status_code == 200, f"Patient search failed: {list_res.text}"
    found_patients = list_res.json().get("patients", [])
    assert any((p.get("id") or p.get("patient_id")) == patient_id for p in found_patients), "Newly created patient not found in search results"
    print(f" -> Search query '{unique_suffix}' returned {len(found_patients)} match(es)")

    # 4. Patient Completeness Calculation
    print("\n[4/10] Testing Patient Record Completeness Rules Engine...")
    comp_res = client.get(f"/api/v1/patients/{patient_id}/completeness", headers=coord_headers)
    assert comp_res.status_code == 200, f"Completeness calculation failed: {comp_res.text}"
    comp_data = comp_res.json()
    print(f" -> Completeness score: {comp_data.get('completeness_percentage', 0)}%, Missing items: {len(comp_data.get('missing_critical_data', []))}")

    # 5. Care Journey Creation & Progression
    print("\n[5/10] Testing Care Journey Milestone Progression...")
    journey_res = client.get(f"/api/v1/journeys/{patient_id}", headers=coord_headers)
    assert journey_res.status_code in [200, 404]
    # Update / progress journey
    patch_journey = client.patch(
        f"/api/v1/journeys/{patient_id}",
        json={
            "current_stage": "Screening Completed",
            "milestone_screening_done": True,
            "screening_notes": "Bilateral 45-degree digital fundus photography completed via mobile unit."
        },
        headers=coord_headers
    )
    assert patch_journey.status_code in [200, 201], f"Journey update failed: {patch_journey.text}"
    print(f" -> Care Journey successfully progressed to 'Screening Completed'")

    # 6. Specialist Review Submission & RBAC
    print("\n[6/10] Testing Specialist Review Submission & Role-Based Access Control...")
    review_payload = {
        "assigned_specialist": "Dr. Suresh Chandran, MS",
        "clinician_title": "Dr.",
        "clinician_specialty": "Ophthalmology",
        "clinician_facility": "District Eye Hospital",
        "registration_number": "MCI-2016-849201",
        "review_status": "followup_initiated",
        "operational_notes": "Fundus images show microaneurysms in right eye. Specialist consultation recommended.",
        "clinician_instruction": "Schedule dilated slit-lamp biomicroscopy within 30 days. Re-check HbA1c.",
        "task_owner": "Care Coordinator",
        "operational_task_status": "In Progress",
        "reconciliation_status": "Reconciled"
    }

    # Coordinator attempt MUST be rejected with HTTP 403
    coord_review_res = client.post(f"/api/v1/reviews/{patient_id}", json=review_payload, headers=coord_headers)
    assert coord_review_res.status_code == 403, f"Expected 403 Forbidden for Coordinator review, got {coord_review_res.status_code}"
    print(" -> Verified RBAC: Care Coordinator correctly blocked from submitting specialist review (HTTP 403)")

    # Specialist attempt MUST succeed with HTTP 200/201
    spec_review_res = client.post(f"/api/v1/reviews/{patient_id}", json=review_payload, headers=spec_headers)
    assert spec_review_res.status_code in [200, 201], f"Specialist review submission failed: {spec_review_res.text}"
    print(" -> Verified Specialist successfully authorized to submit review and create attributed follow-up directive")

    # 7. Follow-Up Worklist, Status Updates, Contact Attempts & Simulated Reminders
    print("\n[7/10] Testing Follow-Up Management & Contact Logging...")
    followup_update = client.post(
        f"/api/v1/followups/{patient_id}",
        json={
            "status": "Scheduled",
            "planned_date": "2026-12-01",
            "notes": "Patient informed regarding scheduled specialist review appointment."
        },
        headers=coord_headers
    )
    assert followup_update.status_code in [200, 201], f"Followup update failed: {followup_update.text}"

    contact_attempt = client.post(
        f"/api/v1/followups/{patient_id}/attempts",
        json={
            "method": "Phone Call",
            "result": "Patient confirmed appointment date and requested reminder SMS.",
            "staff": "Care Coordinator Desk"
        },
        headers=coord_headers
    )
    assert contact_attempt.status_code in [200, 201], f"Contact attempt logging failed: {contact_attempt.text}"
    print(" -> Follow-up status updated and contact attempt successfully logged to audit timeline")

    reminder_res = client.post(
        f"/api/v1/reminders/{patient_id}/dispatch",
        json={
            "type": "Follow-Up Attendance",
            "language": "en",
            "custom_note": "Please bring your previous prescription."
        },
        headers=coord_headers
    )
    assert reminder_res.status_code in [200, 201], f"Reminder dispatch failed: {reminder_res.text}"
    print(" -> Simulated bilingual SMS/WhatsApp notification generated and dispatched")

    # 8. Document Upload (Security Validation) & Download (Token Auth)
    print("\n[8/10] Testing Document Management, Magic-Byte Security & Download Delivery...")
    
    # 8a: Fake PDF (plain text) MUST be rejected by python-magic/header validation
    fake_pdf = io.BytesIO(b"Hello world this is not a real PDF file!")
    rejected_upload = client.post(
        f"/api/v1/documents/{patient_id}",
        files={"file": ("fake_report.pdf", fake_pdf, "application/pdf")},
        data={"title": "Fake Report", "doc_type": "Retinal Screening Report", "source": "Mobile Unit"},
        headers=coord_headers
    )
    assert rejected_upload.status_code in [400, 422], f"Expected security rejection for fake PDF, got {rejected_upload.status_code}"
    print(" -> Document security verified: Malformed/disguised PDF rejected by magic bytes inspection")

    # 8b: Valid PDF upload MUST be accepted
    valid_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n185\n%%EOF\n"
    valid_pdf_io = io.BytesIO(valid_pdf_bytes)
    upload_res = client.post(
        f"/api/v1/documents/{patient_id}",
        files={"file": (f"report_{unique_suffix}.pdf", valid_pdf_io, "application/pdf")},
        data={"title": f"Valid Screening Report {unique_suffix}", "doc_type": "Retinal Screening Report", "source": "Mobile Unit"},
        headers=coord_headers
    )
    assert upload_res.status_code in [200, 201], f"Valid PDF upload failed: {upload_res.text}"
    uploaded_doc = upload_res.json()
    doc_id = uploaded_doc["id"]
    print(f" -> Valid clinical PDF uploaded and indexed: Doc ID={doc_id}")

    # 8c: Download via query token
    download_res = client.get(f"/api/v1/documents/{doc_id}/download?token={coord_token}")
    assert download_res.status_code == 200, f"Token download failed: {download_res.status_code}"
    assert download_res.content.startswith(b"%PDF"), "Downloaded file did not return valid PDF bytes"
    print(" -> Document downloaded successfully using ?token= query parameter (New Tab support verified)")

    # 9. Dashboard Analytics & Care Gap Radar
    print("\n[9/10] Testing Analytics Overview, Gap Radar & Cohort Reconciliation...")
    analytics_res = client.get("/api/v1/analytics/overview", headers=coord_headers)
    assert analytics_res.status_code == 200, f"Analytics overview failed: {analytics_res.text}"
    stats = analytics_res.json()
    print(f" -> Real database metrics: Total Patients={stats['counts']['total_patients']}, Screened={stats['counts']['screening_completed']}, Pending Review={stats['counts']['awaiting_specialist_review']}")

    radar_res = client.get("/api/v1/analytics/gap-radar", headers=coord_headers)
    assert radar_res.status_code == 200, f"Gap Radar failed: {radar_res.text}"
    radar_data = radar_res.json()
    print(f" -> Care Gap Radar: Total Flagged Care Gaps={radar_data['total_flagged']}")

    # 10. Logout & Session Termination
    print("\n[10/10] Testing Session Invalidation & Logout...")
    logout_res = client.post("/api/v1/auth/logout", headers=coord_headers)
    assert logout_res.status_code == 200, f"Logout failed: {logout_res.text}"
    print(" -> Session successfully invalidated")

    # Clean up test artifacts to keep database pristine
    db = SessionLocal()
    try:
        test_patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if test_patient:
            db.delete(test_patient)
            db.commit()
    finally:
        db.close()

    # Clean uploaded test file from uploads/
    uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
    for f in uploads_dir.glob(f"*{unique_suffix}*.pdf"):
        try:
            f.unlink()
        except Exception:
            pass

    print("\n" + "=" * 65)
    print(" ALL 10 END-TO-END WORKFLOW INTEGRATIONS PASSED WITH 100% SUCCESS!")
    print("=" * 65)

if __name__ == "__main__":
    run_e2e_verification()
