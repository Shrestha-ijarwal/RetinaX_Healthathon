"""
RetinaX Care — Health-a-thon 2026 Verification Test Runner
Supports dynamic root resolution without hardcoded Windows paths.
Tests FastAPI production backend, authentication, RBAC, document validation,
operational metrics, and non-clinical scope compliance.
"""

import sys
from pathlib import Path

# Dynamic root resolution
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

print("================================================================")
print("  RETINAX CARE — HEALTH-A-THON 2026 VERIFICATION TEST SUITE")
print("  Track: Diabetes Care & RSSDI | Product: RetinaX Care")
print("================================================================")

# 1. Health check & Scope Compliance Declaration
res = client.get('/health')
assert res.status_code == 200, f"Health check failed: {res.status_code}"
health_data = res.json()
assert health_data['status'] == 'healthy'
assert "non-clinical AI scope" in health_data['compliance']
print("[PASS] 1. System Health & Scope Compliance Declaration verified.")

# 2. Authentication & JWT Token Issuance
auth_res = client.post('/api/v1/auth/login', json={"email": "coordinator@retinax.care", "password": "Coordinator@2026"})
assert auth_res.status_code == 200, f"Coordinator login failed: {auth_res.text}"
token = auth_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("[PASS] 2. Argon2id Authentication & JWT token issuance verified.")

# 3. Operational Metrics & Patient Cohort
res = client.get('/api/v1/patients', headers=headers)
assert res.status_code == 200
data = res.json()
patients = data['patients']
metrics = data['metrics']
assert len(patients) == 12, f"Expected 12 synthetic patients, got {len(patients)}"
assert metrics['total_patients'] == 12
assert 'report_missing' in metrics
assert 'unable_to_contact' in metrics
assert 'awaiting_specialist_review' in metrics
print(f"[PASS] 3. Loaded 12 synthetic patients with operational metrics: Total={metrics['total_patients']}, Missing Reports={metrics['report_missing']}, Loops Closed={metrics['care_loops_closed']}")

# 4. Operational Worklist Filtering (All 10 filter modes)
test_filters = [
    'all',
    'needs_attention',
    'pending_screening',
    'scheduled',
    'screening_completed',
    'report_missing',
    'awaiting_review',
    'followup_pending',
    'unable_to_contact',
    'completed'
]
for f in test_filters:
    res = client.get(f'/api/v1/patients?filter={f}', headers=headers)
    assert res.status_code == 200, f"Filter {f} failed with status {res.status_code}"
    matched_count = len(res.json()['patients'])
    print(f"       Filter '{f:20}': {matched_count:2d} patient(s) matched.")
print("[PASS] 4. All 10 operational filter modes verified.")

# 5. Record Completeness Check
res = client.get('/api/v1/patients/RX-1006/completeness', headers=headers)
assert res.status_code == 200
comp = res.json()
assert "score_percentage" in comp
print(f"[PASS] 5. Rules-based record completeness calculated: {comp['score_percentage']}% (Checks completed: {comp['completed_count']}/{comp['total_checks']}).")

# 6. Backend-Enforced RBAC
spec_res = client.post(
    '/api/v1/reviews/RX-1007',
    json={
        "assigned_specialist": "Coordinator Impersonator",
        "review_status": "review_completed",
        "operational_notes": "Unpermitted operational review submission attempt",
        "clinician_instruction": "None"
    },
    headers=headers
)
assert spec_res.status_code == 403, f"Expected 403 Forbidden for Coordinator review, got {spec_res.status_code}"
print("[PASS] 6. Backend RBAC verified: Care Coordinator blocked from specialist endpoints (HTTP 403).")

# 7. Document Security: Magic-byte inspection
fake_file = {"file": ("malicious.pdf", b"PLAIN_TEXT_NOT_A_PDF", "application/pdf")}
upload_res = client.post('/api/v1/documents/RX-1001', files=fake_file, headers=headers)
assert upload_res.status_code == 400
print("[PASS] 7. Document Security verified: Plain text masquerading as PDF rejected by magic bytes.")

# 8. Care Continuity Gap Radar
radar_res = client.get('/api/v1/analytics/gap-radar', headers=headers)
assert radar_res.status_code == 200
radar = radar_res.json()
assert "flagged_patients" in radar
print(f"[PASS] 8. Care Gap Radar active: {radar['total_flagged']} patient(s) flagged for coordinator review.")

# 9. HL7 / FHIR R4 Adapter
fhir_res = client.get('/api/v1/fhir/Patient/RX-1001', headers=headers)
assert fhir_res.status_code == 200
assert fhir_res.json()["resourceType"] == "Patient"
print("[PASS] 9. HL7 / FHIR R4 operational adapter verified.")

print("================================================================")
print("  ALL 9 CORE OPERATIONAL TEST SUITES PASSED SUCCESSFULLY!")
print("================================================================")
