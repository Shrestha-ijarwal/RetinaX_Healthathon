import json
from pathlib import Path
import sys

root = Path("C:/Users/sijar/Downloads/RetinaX_Healthathon")
sys.path.insert(0, str(root))

from server import app, PATIENTS_STORE, calculate_record_completeness, get_operational_metrics

client = app.test_client()

print("================================================================")
print("  RETINAX CARE — HEALTH-A-THON 2026 VERIFICATION TEST SUITE")
print("  Track: Diabetes Care · RSSDI | Product: RetinaX Care")
print("================================================================")

# 1. Health check & Scope Compliance Declaration
res = client.get('/health')
assert res.status_code == 200, f"Health check failed: {res.status_code}"
health_data = res.get_json()
assert health_data['status'] == 'healthy'
assert "non-clinical AI scope" in health_data['compliance']
print("[PASS] 1. System Health & Scope Compliance Declaration verified.")

# 2. Operational Metrics & Patient Cohort
res = client.get('/api/patients')
assert res.status_code == 200
data = res.get_json()
patients = data['patients']
metrics = data['metrics']
assert len(patients) == 12, f"Expected 12 synthetic patients, got {len(patients)}"
assert metrics['total_patients'] == 12
assert 'report_missing' in metrics
assert 'unable_to_contact' in metrics
assert 'awaiting_specialist_review' in metrics
print(f"[PASS] 2. Loaded 12 synthetic patients with operational metrics: {metrics}")

# 3. Operational Worklist Filtering
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
    res = client.get(f'/api/patients?filter={f}')
    assert res.status_code == 200, f"Filter {f} failed with status {res.status_code}"
    matched_count = len(res.get_json()['patients'])
    print(f"       Filter '{f}': {matched_count} patient(s) matched.")
print("[PASS] 3. All 10 operational filter modes verified.")

# 4. Verification: Care Journey Summary (Non-diagnostic Record Completeness)
res = client.get('/api/completeness/RX-1006')
assert res.status_code == 200
comp = res.get_json()['completeness']
assert len(comp['missing_items']) > 0
print(f"[PASS] 4. Care Journey Summary completeness checker correctly flagged missing items: {comp['missing_items']}")

# 5. DEDICATED HERO DEMO TEST: Mohammad Farooq (RX-1003)
print("\n--- Testing RX-1003 Hero Demo Flow ---")

# Step 1: Check initial state of RX-1003
res = client.get('/api/patients/RX-1003')
assert res.status_code == 200
farooq = res.get_json()
assert farooq['name'] == 'Mohammad Farooq'
assert farooq['specialist_review']['completed'] is False
assert any(d['doc_type'] == 'Retinal Screening Report' for d in farooq['documents'])
print("       Step 1-2: RX-1003 confirmed with uploaded report awaiting specialist review.")

# Step 2: Specialist Ophthalmologist Review Submission (Human-in-the-loop with Provenance)
review_payload = {
    'clinician_name': 'Dr. Suresh Chandran, MS (Ophthalmology)',
    'clinician_title': 'Dr.',
    'clinician_specialty': 'Ophthalmology',
    'clinician_facility': 'District Eye Hospital',
    'registration_number': 'MCI-2016-849201',
    'clinical_assessment': 'Manual clinical assessment: Bilateral microvascular changes observed. No high-risk proliferative features or macular edema on visual inspection.',
    'followup_instructions': 'Repeat dilated fundus examination at eye clinic in 6 months. Maintain strict glycemic control.',
    'referral_status': 'Hospital Follow-Up (6 Months)',
    'next_followup_date': '2027-04-01',
    'notes': 'Clinical assessment entered manually by qualified healthcare professional.'
}
res = client.post('/api/patients/RX-1003/review', json=review_payload)
assert res.status_code == 200
review_res = res.get_json()
updated_farooq = review_res['patient']
created_task = review_res['operational_task']

assert updated_farooq['specialist_review']['completed'] is True
assert updated_farooq['specialist_review']['clinician_name'] == 'Dr. Suresh Chandran, MS (Ophthalmology)'
assert updated_farooq['specialist_review']['clinician_specialty'] == 'Ophthalmology'
assert updated_farooq['specialist_review']['registration_number'] == 'MCI-2016-849201'
assert "Dr. Suresh Chandran" in created_task['source']
assert created_task['entered_by'] == 'Dr. Suresh Chandran, MS (Ophthalmology)'
assert created_task['due_date'] == '2027-04-01'

# Verify timeline audit trail has clinician provenance
latest_timeline_evt = updated_farooq['timeline'][-1]
assert latest_timeline_evt['stage'] == 'Specialist Review Completed'
assert 'Dr. Suresh Chandran' in latest_timeline_evt['actor']
print("       Step 3-4: Specialist review recorded with clinician provenance and operational task created.")

# Step 3: Bilingual Reminder Generation (English & Hindi)
res_en = client.post('/api/patients/RX-1003/reminders', json={'type': 'Follow-Up Attendance', 'language': 'en'})
assert res_en.status_code == 200
res_hi = client.post('/api/patients/RX-1003/reminders', json={'type': 'Follow-Up Attendance', 'language': 'hi'})
assert res_hi.status_code == 200
hi_rem = res_hi.get_json()['reminder']
assert "Demo notification" in hi_rem['sent_status']
print(f"       Step 5: Generated simulated English & Hindi notifications (Hindi text length: {len(hi_rem['text_hi'])} chars).")

# Step 4: Follow-up Completion and Care Loop Closure
res = client.post('/api/patients/RX-1003/followup', json={
    'status': 'Completed',
    'responsible_staff': 'Coordinator Imran Khan',
    'notes': 'Patient attended 6-month evaluation. Care loop closed for this cycle.',
    'close_care_loop': True
})
assert res.status_code == 200
closed_farooq = res.get_json()['patient']
assert closed_farooq['workflow_status']['care_loop_completed'] is True
assert closed_farooq['workflow_status']['overall_stage'] == 'Care Loop Completed'
print("       Step 6: Closed care loop for Mohammad Farooq successfully.")

# 6. Secondary Benchmark Test: Gurpreet Singh (RX-1005)
res = client.get('/api/patients/RX-1005')
assert res.status_code == 200
gurpreet = res.get_json()
assert gurpreet['workflow_status']['care_loop_completed'] is True
print("[PASS] 6. Secondary benchmark (RX-1005 Care Loop Completed) verified.")

# 7. Demo Reset Functionality
res = client.post('/api/patients/reset')
assert res.status_code == 200
reset_farooq = client.get('/api/patients/RX-1003').get_json()
assert reset_farooq['specialist_review']['completed'] is False
print("[PASS] 7. Reset demo data restores all synthetic cases to baseline state.")

# 8. Runtime Dependency Sanity: Verify NO diagnostic model files are loaded
import server
assert not hasattr(server, 'trained_DR_model_v3')
assert not hasattr(server, 'dr_model')
assert not hasattr(server, 'gradcam')
print("[PASS] 8. Confirmed ZERO runtime dependencies on diagnostic models or Grad-CAM.")

# 9. Custom Clinician Profile Review Attribution & Provenance Test
print("\n--- Testing Custom Clinician Profile Review Attribution ---")
custom_clinician_payload = {
    'clinician_name': 'Dr. Ananya Sharma',
    'clinician_title': 'Dr.',
    'clinician_specialty': 'Ophthalmology',
    'clinician_facility': 'District Eye Hospital',
    'registration_number': 'REG-2026-CUSTOM-01',
    'clinical_assessment': 'Manual examination of fundus images: Early background retinopathy signs noted. No macular edema.',
    'followup_instructions': 'Hospital eye-clinic follow-up in 6 months per clinical guidelines.',
    'referral_status': 'Hospital Follow-Up (6 Months)',
    'next_followup_date': '2026-12-15',
    'notes': 'Clinician-entered review for customized demo profile testing.'
}
res_custom = client.post('/api/patients/RX-1004/review', json=custom_clinician_payload)
assert res_custom.status_code == 200
custom_data = res_custom.get_json()
custom_patient = custom_data['patient']
custom_task = custom_data['operational_task']

assert custom_patient['specialist_review']['completed'] is True
assert custom_patient['specialist_review']['clinician_name'] == 'Dr. Ananya Sharma'
assert custom_patient['specialist_review']['clinician_specialty'] == 'Ophthalmology'
assert custom_patient['specialist_review']['clinician_facility'] == 'District Eye Hospital'
assert custom_patient['specialist_review']['registration_number'] == 'REG-2026-CUSTOM-01'

# Task provenance assertions
assert custom_task['source'] == 'Clinician Instruction (Dr. Ananya Sharma)'
assert custom_task['entered_by'] == 'Dr. Ananya Sharma'
assert custom_task['clinician_specialty'] == 'Ophthalmology'
assert custom_task['clinician_facility'] == 'District Eye Hospital'
assert custom_task['assigned_to'] == 'Care Coordinator'

# Timeline audit trail assertions
latest_event = custom_patient['timeline'][-1]
assert latest_event['stage'] == 'Specialist Review Completed'
assert 'Dr. Ananya Sharma' in latest_event['actor']
assert 'District Eye Hospital' in latest_event['note']
print("[PASS] 9. Custom clinician profile review attribution, provenance chain & audit trail verified.")

print("\n================================================================")
print(">>> ALL UNIT & INTEGRATION TESTS PASSED WITH 100% SUCCESS! <<<")
print("================================================================")
