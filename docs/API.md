# RetinaX Care — REST API Reference & Specification

**Base URL:** `/api/v1` (with backward compatibility mount at `/api`)  
**Format:** JSON (UTF-8)  
**Authentication:** HTTP Bearer JWT or secure HttpOnly Cookie (`retinax_session`)  
**Interactive OpenAPI UI:** `http://localhost:8000/api/v1/docs`  
**ReDoc Reference:** `http://localhost:8000/api/v1/redoc`  

---

## 1. Authentication Endpoints

### `POST /api/v1/auth/login`
Authenticates user credentials and issues a JWT session token. Sets secure HttpOnly cookie.
- **Request Body:**
  ```json
  {
    "email": "specialist@retinax.care",
    "password": "Specialist@2026"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "specialist@retinax.care",
      "username": "dr_chandran",
      "role": "Specialist",
      "full_name": "Dr. Suresh Chandran, MS"
    }
  }
  ```

### `POST /api/v1/auth/logout`
Terminates session and clears `retinax_session` cookie.

### `GET /api/v1/auth/me`
Returns current authenticated user profile and permissions.

---

## 2. Patients & Screening Cohort

### `GET /api/v1/patients`
Returns paginated list of synthetic patients with real-time operational filters and cohort metrics.
- **Query Parameters:**
  - `search` (string): Search across name, ID, phone, or clinic.
  - `filter` (string): `all`, `needs_attention`, `pending_screening`, `scheduled`, `screening_completed`, `report_missing`, `awaiting_review`, `followup_pending`, `unable_to_contact`, `completed`.
  - `facility` (string): Filter by healthcare facility.
  - `skip` (int), `limit` (int): Pagination controls.

### `GET /api/v1/patients/{patient_id}`
Returns full detailed patient record, including care journey stage, chronological timeline events, attached documents, specialist review, tasks, and follow-up records.

### `POST /api/v1/patients`
Registers a new synthetic patient into the care cohort. Requires `Care Coordinator` role.

### `GET /api/v1/patients/{patient_id}/completeness`
Calculates non-clinical record completeness score (0-100%) against the 6-point operational criteria checklist.

### `POST /api/v1/patients/reset`
Idempotently resets the synthetic demonstration cohort back to baseline seed data.

---

## 3. Care Journeys

### `GET /api/v1/journeys`
Retrieves directory of active patient care journeys with progression percentage, current step, and next operational action.

### `GET /api/v1/journeys/{patient_id}`
Returns Care Journey Digital Twin data for the selected patient.

### `PATCH /api/v1/journeys/{patient_id}`
Updates journey stage parameters (screening date, follow-up status, next action).

---

## 4. Specialist Reviews (RBAC Protected)

### `GET /api/v1/reviews/queue`
Retrieves tele-ophthalmology reading worklist sorted by report availability and waiting duration.

### `GET /api/v1/reviews/{patient_id}`
Returns patient screening dossier, attached retinal fundus photography reports, and previous review status.

### `POST /api/v1/reviews/{patient_id}`
Submits formal ophthalmologist review.  
**Security Enforcement:** Restricted exclusively to users with the `Specialist` role (HTTP 403 Forbidden for Care Coordinators).  
- **Request Body:**
  ```json
  {
    "assigned_specialist": "Dr. Suresh Chandran, MS",
    "clinician_title": "Dr.",
    "clinician_specialty": "Ophthalmology",
    "clinician_facility": "District Eye Hospital",
    "registration_number": "MCI-2016-849201",
    "review_status": "followup_initiated",
    "operational_notes": "Screening report legibility verified. Color photographs adequate for tele-triage.",
    "clinician_instruction": "Attributed directive: Review in 6 months at hospital retina clinic.",
    "task_owner": "Care Coordinator",
    "operational_task_status": "In Progress",
    "reconciliation_status": "Reconciled"
  }
  ```

---

## 5. Follow-Ups & Reminders

### `GET /api/v1/followups`
Worklist of patients requiring follow-up coordination, sorted by urgency and status.

### `POST /api/v1/followups/{patient_id}`
Updates follow-up status (`Pending`, `Scheduled`, `Completed`, `Unable to Contact`) and logs a contact attempt.

### `POST /api/v1/reminders/{patient_id}`
Queues a bilingual appointment reminder in simulation mode (`DEMO — NOT SENT TO PATIENT`).  
- **Supported Languages:** `en` (English), `hi` (Hindi).

---

## 6. Document Ingestion & Download

### `GET /api/v1/documents`
List of verified clinical attachments, screening photography dossiers, and notes.

### `POST /api/v1/documents/{patient_id}`
Multipart upload of clinical documents.  
- **Security Validation:** Binary magic bytes verified (`%PDF-`, `\xff\xd8\xff`, `\x89PNG`). Max size: 32 MB.

### `GET /api/v1/documents/{document_id}/download`
Secure streaming download of document file bytes. Requires valid authenticated session.

---

## 7. Continuity Analytics & Radar

### `GET /api/v1/analytics`
Dynamically computed operational continuity metrics: loop closure rate (%), screening completion, turnaround times, and facility distribution.

### `GET /api/v1/analytics/gap-radar`
Care continuity gap radar flagging missing reports, review bottlenecks, and communication failures.

### `GET /api/v1/analytics/reconciliation`
Data reconciliation worklist of records requiring field verification or documentation correction.

### `POST /api/v1/analytics/reconciliation/{patient_id}/resolve`
Marks a reconciliation item as audited and resolved.

---

## 8. HL7 / FHIR R4 Interoperability

- `GET /api/v1/fhir/Patient/{id}` — Returns FHIR R4 `Patient` resource.
- `GET /api/v1/fhir/Task` — Returns FHIR R4 `Bundle` of operational care coordination tasks.
- `GET /api/v1/fhir/DocumentReference` — Returns FHIR R4 `DocumentReference` searchset.
