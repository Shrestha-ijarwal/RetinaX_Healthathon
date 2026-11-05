# RetinaX Care — Migration Inventory & Architecture Transition Plan

**Document Version:** 1.0.0  
**Date:** 2026-11-05  
**Project:** RetinaX Care (Closing the Loop in Diabetic Eye Care)  
**Track:** Health-a-thon 2026 — Diabetic Retinopathy Screening Follow-up & Care Continuity  
**Target Architecture:** FastAPI + PostgreSQL + SQLAlchemy 2.x + Celery/Redis + Next.js (TypeScript) + S3 Storage + PWA  

---

## 1. Executive Summary & Boundaries

RetinaX Care is an operational care-continuity platform dedicated to closing the loop in diabetic eye screening. It identifies incomplete screening journeys, coordinates specialist reviews, tracks operational follow-up tasks, and mitigates patient dropout between screening and care.

### Strict Scope Boundaries
- **In Scope:** Operational care-coordination, screening scheduling/completion tracking, documentation completeness audit, specialist review workflow coordination, clinician-attributed instruction recording, contact attempt tracking, multi-language simulated patient reminders, reconciliation worklists, care continuity analytics.
- **Out of Scope (Explicitly Excluded):** AI disease grading (DR 0–4), autonomous diagnoses, clinical decision support (CDS), clinical risk scoring, automated clinical referral algorithms, automated fundus image interpretation, prescription generation.

### Strict Repository Isolation
- **Project A (Original RetinaX):** `C:\Users\sijar\Downloads\RetinaX` — **Untouched, completely isolated, zero files modified or imported.**
- **Project B (RetinaX Care):** `C:\Users\sijar\Downloads\RetinaX_Healthathon` — **Active upgrade workspace.**
- **Safe Backup Archive:** `C:\Users\sijar\Downloads\RetinaX_Healthathon_BACKUP_PHASE0` created prior to code modification.
- **Development Branch:** `feature/production-architecture-upgrade`.

---

## 2. Existing File Inventory & Assessment

| Path | Format / Size | Role in Existing System | Status in New Architecture |
|---|---|---|---|
| `server.py` | Python (Flask), ~1,120 lines | Monolithic backend serving static files, in-memory JSON patient storage, mock APIs | **Replaced** with modular FastAPI backend (`backend/app/...`) with domain services, repositories, and routers. |
| `frontend/index.html` | HTML5, ~98 KB | Single-page UI with topbar tabs, modals, and client-side demo role selector | **Migrated** to Next.js 15+ App Router (`frontend/app/...`) with typed React components. |
| `frontend/styles.css` | CSS, ~51 KB | Complete healthcare styling system, light/dark mode variables, responsive utility classes | **Preserved & Integrated** into Next.js styling system and CSS Modules. |
| `frontend/app.js` | JavaScript, ~141 KB | Client-side state, DOM manipulation, mock offline array, client-side filtering | **Migrated** to modular TypeScript services, React hooks, IndexedDB store, and PWA service worker. |
| `data/synthetic_patients.json` | JSON, ~61 KB | Primary working data store containing 12 synthetic patients (includes user-owned edits) | **Preserved**. Mapped to PostgreSQL seed migration with zero data loss. |
| `data/synthetic_patients_seed.json` | JSON, ~60 KB | Baseline seed data store | **Preserved**. Seed fallback. |
| `uploads/*.pdf` (9 files) | Text files disguised as .pdf | Dummy files for document upload & preview | **Replaced** with genuine, standard-compliant binary PDF synthetic documents with original clinical narrative. |
| `tests_runner.py` | Python | Basic integration assertions with hardcoded local paths | **Replaced & Expanded** to comprehensive Pytest backend suite + Jest/React frontend suite. |
| `audit_compliance.py` | Python | Keyword scanner asserting zero prohibited clinical terms | **Preserved & Integrated** into automated CI test runner. |
| `README.md` | Markdown | Legacy documentation | **Updated** to reflect production MVP architecture and strict non-diagnostic positioning. |

---

## 3. Data Migration Mappings (JSON to Normalized PostgreSQL)

The JSON document model in `synthetic_patients.json` maps directly into normalized relational entities managed by SQLAlchemy 2.0 and Alembic:

### Entity: `patients`
| JSON Field | DB Column | Type | Constraints / Details |
|---|---|---|---|
| `id` | `id` | `VARCHAR(32)` | Primary Key (e.g., `RX-1001`), preserved |
| `name` | `name` | `VARCHAR(128)` | Synthetic patient name |
| `age` | `age` | `INTEGER` | Synthetic age |
| `sex` | `sex` | `VARCHAR(16)` | `Male`, `Female`, `Other` |
| `contact` | `contact` | `VARCHAR(32)` | Synthetic phone number |
| `facility` | `facility` | `VARCHAR(128)` | Primary care facility / clinic |
| `clinician` | `clinician` | `VARCHAR(128)` | Registering clinician |
| `registration_date` | `registration_date` | `DATE` | Initial cohort registration |
| `diabetes_profile` | `diabetes_profile` | `JSONB` / Table | Type, duration_recorded, baseline HbA1c (operational only), medications |
| `created_at` / `updated_at` | `created_at` / `updated_at` | `TIMESTAMP WITH TIME ZONE` | Default `now()` |

### Entity: `care_journeys` (Workflow Status)
| JSON Field | DB Column | Type | Details |
|---|---|---|---|
| `patient_id` | `patient_id` | `VARCHAR(32)` | Foreign Key -> `patients.id` |
| `workflow_status.overall_stage` | `overall_stage` | `VARCHAR(64)` | e.g., `Awaiting Specialist Review`, `Follow-Up Pending` |
| `workflow_status.screening_workflow` | `screening_workflow` | `VARCHAR(64)` | `Not Started`, `Scheduled`, `Completed` |
| `workflow_status.screening_appointment_date` | `screening_date` | `DATE` | Scheduled or completion date |
| `workflow_status.specialist_review` | `review_status` | `VARCHAR(64)` | `Not Started`, `Pending Review`, `Completed` |
| `workflow_status.followup_status` | `followup_status` | `VARCHAR(64)` | `Pending`, `Scheduled`, `Completed`, `Unable to Contact` |
| `workflow_status.care_loop_completed` | `care_loop_completed` | `BOOLEAN` | Operational loop closure indicator |
| `workflow_status.next_workflow_action` | `next_action` | `TEXT` | Next actionable care team task |
| `workflow_status.assigned_to` | `assigned_to` | `VARCHAR(128)` | Current operational staff owner |
| `workflow_status.due_date` | `due_date` | `DATE` | Milestone due date |

### Entity: `timeline_events`
| JSON Field | DB Column | Type | Details |
|---|---|---|---|
| `timeline[].id` | `id` | `VARCHAR(64)` | Primary Key |
| `patient_id` | `patient_id` | `VARCHAR(32)` | FK -> `patients.id` |
| `timeline[].stage` | `stage` | `VARCHAR(128)` | Event stage title |
| `timeline[].timestamp` | `timestamp` | `TIMESTAMP WITH TIME ZONE` | Event occurrence |
| `timeline[].source` | `source` | `VARCHAR(128)` | Originating department/service |
| `timeline[].actor` | `actor` | `VARCHAR(128)` | Staff member responsible |
| `timeline[].status` | `status` | `VARCHAR(64)` | `Completed`, `Updated`, `Delivered` |
| `timeline[].note` | `note` | `TEXT` | Operational log entry |

### Entity: `documents`
| JSON Field | DB Column | Type | Details |
|---|---|---|---|
| `documents[].id` | `id` | `VARCHAR(64)` | Primary Key |
| `patient_id` | `patient_id` | `VARCHAR(32)` | FK -> `patients.id` |
| `documents[].title` | `title` | `VARCHAR(255)` | Document title |
| `documents[].doc_type` | `doc_type` | `VARCHAR(128)` | `Retinal Screening Report`, `Referral Letter`, etc. |
| `documents[].upload_date` | `upload_date` | `DATE` | Upload timestamp |
| `documents[].source` | `source` | `VARCHAR(128)` | Originating unit/hospital |
| `documents[].review_status` | `review_status` | `VARCHAR(64)` | `Awaiting Specialist Review`, `Reviewed` |
| `documents[].file_name` | `storage_key` | `VARCHAR(255)` | Secure S3/MinIO storage object key |
| `documents[].size_kb` | `size_bytes` | `INTEGER` | Exact file size |
| `mime_type` | `mime_type` | `VARCHAR(64)` | `application/pdf`, `image/jpeg` |
| `sha256_hash` | `sha256_hash` | `VARCHAR(64)` | Integrity verification hash |

### Entity: `specialist_reviews`
| JSON Field | DB Column | Type | Details |
|---|---|---|---|
| `patient_id` | `patient_id` | `VARCHAR(32)` | FK -> `patients.id` (1:1 per cycle) |
| `specialist_review.completed` | `completed` | `BOOLEAN` | Review completion status |
| `specialist_review.clinician_name` | `clinician_name` | `VARCHAR(128)` | Attribution of reviewing ophthalmologist |
| `specialist_review.review_timestamp`| `review_timestamp` | `TIMESTAMP WITH TIME ZONE` | Completion timestamp |
| `specialist_review.clinical_assessment`| `clinical_assessment`| `TEXT` | Clinician-entered qualitative assessment |
| `specialist_review.followup_instructions`| `followup_instructions`| `TEXT` | Clinician-entered care directives |
| `specialist_review.referral_status` | `referral_status` | `VARCHAR(128)` | Care recommendation (e.g., Hospital Follow-Up) |
| `specialist_review.notes` | `notes` | `TEXT` | Attributed audit notes |

### Entity: `operational_tasks`
| JSON Field | DB Column | Type | Details |
|---|---|---|---|
| `pending_tasks[].id` | `id` | `VARCHAR(64)` | Primary Key |
| `patient_id` | `patient_id` | `VARCHAR(32)` | FK -> `patients.id` |
| `pending_tasks[].title` | `title` | `VARCHAR(255)` | Task summary |
| `pending_tasks[].description` | `description` | `TEXT` | Operational instructions |
| `pending_tasks[].assigned_to` | `assigned_to` | `VARCHAR(128)` | Care team member or role |
| `pending_tasks[].due_date` | `due_date` | `DATE` | Task deadline |
| `pending_tasks[].status` | `status` | `VARCHAR(32)` | `Open`, `Completed`, `Overdue` |
| `pending_tasks[].priority` | `priority` | `VARCHAR(32)` | `Low`, `Medium`, `High`, `Urgent` |
| `pending_tasks[].created_at` | `created_at` | `DATE` | Creation date |

### Entity: `followup_records` & `contact_attempts`
| JSON Field | DB Column | Type | Details |
|---|---|---|---|
| `followup.status` | `status` | `VARCHAR(64)` | `Pending`, `Scheduled`, `Completed`, `Unable to Contact` |
| `followup.planned_date` | `planned_date` | `DATE` | Scheduled follow-up visit |
| `followup.responsible_staff`| `responsible_staff`| `VARCHAR(128)` | Coordinator assigned |
| `followup.contact_attempts` | table `contact_attempts` | Relational FK | `date`, `method`, `result`, `staff` |

### Entity: `reminders`
| JSON Field | DB Column | Type | Details |
|---|---|---|---|
| `reminders[].id` | `id` | `VARCHAR(64)` | Primary Key |
| `patient_id` | `patient_id` | `VARCHAR(32)` | FK -> `patients.id` |
| `reminders[].type` | `type` | `VARCHAR(64)` | `Follow-Up Attendance`, `Screening Scheduled` |
| `reminders[].language` | `language` | `VARCHAR(8)` | `en`, `hi`, `kn` |
| `reminders[].text` | `text_en` | `TEXT` | English operational reminder copy |
| `reminders[].text_hi` | `text_hi` | `TEXT` | Hindi operational reminder copy |
| `reminders[].sent_status` | `delivery_status` | `VARCHAR(64)` | `simulated`, `queued`, `sent`, `failed` |
| `reminders[].scheduled_for` | `scheduled_for` | `TIMESTAMP WITH TIME ZONE` | Dispatch timestamp |

---

## 4. Features Being Redesigned & Hardened

1. **Backend & Persistence:**
   - *Previous:* Flask single file with global in-memory `PATIENTS_STORE` and file writes to `data/synthetic_patients.json` on mutation.
   - *Upgraded:* FastAPI with clean multi-layer architecture (routers, schemas, services, repositories, models), PostgreSQL with SQLAlchemy 2.0 and Alembic migrations.
2. **Authentication & Role-Based Access Control:**
   - *Previous:* Client-side dropdown switching local storage variable `activeRole`; no backend authorization.
   - *Upgraded:* Server-side Argon2id password hashing, JWT/Session tokens with HttpOnly cookies, backend FastAPI dependency guards (`require_role(...)`), strictly enforced for Specialist, Care Coordinator, and Admin.
3. **Document Ingestion & File Handling:**
   - *Previous:* Arbitrary files uploaded and placed directly in `uploads/` without magic-byte verification. Uploads served via unauthenticated `/api/uploads/<path:filename>`.
   - *Upgraded:* Magic-byte inspection, strict MIME allowlisting (`application/pdf`, `image/png`, `image/jpeg`), UUID-based sanitized storage keys, private object storage (MinIO/S3), signed time-limited download URLs requiring authenticated bearer/cookie authorization.
4. **Synthetic PDF Content:**
   - *Previous:* Text files with `.pdf` extension containing plain strings.
   - *Upgraded:* Valid binary PDFs generated using a clean standard PDF stream builder, preserving clinical summary and document metadata.
5. **Offline Support & Synchronization:**
   - *Previous:* In-memory client array `offlineQueue` in JavaScript.
   - *Upgraded:* True PWA with service worker caching static assets, IndexedDB-backed mutation queue, online/offline detection, background synchronization, and conflict resolution ledger.
6. **Background Tasks & Notifications:**
   - *Previous:* Synchronous mocked delay in Flask.
   - *Upgraded:* Celery worker with Redis broker, simulated SMS/WhatsApp engine with audit logs and language templates.
7. **Care Journey UX:**
   - *Previous:* Auto-loading first patient; heavy select dropdowns.
   - *Upgraded:* Dedicated searchable, filterable directory with clear visual progress cues; deep-dive Care Journey Twin opened only upon patient selection.
8. **Responsive UI:**
   - *Previous:* Horizontal overflow at <= 768px; cramped table cards.
   - *Upgraded:* Modern responsive CSS grids and flex layouts tested from 320px mobile to 1440px desktop.

---

## 5. Features Being Removed or Restricted

- **Unauthenticated file serving:** The open endpoint `GET /api/uploads/<path:filename>` is completely removed.
- **Permissive CORS Wildcard (`*`):** Restricted to verified localhost origins in development and trusted domains in production.
- **Raw `innerHTML` injection:** All patient notes, timeline strings, and search queries are properly sanitized and rendered as React safe text nodes to prevent XSS.
- **Client-Side Admin Override:** Hardened so admin privileges cannot modify clinical notes or simulate specialist sign-offs.

---

## 6. Migration Risks & Mitigation Strategy

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| Loss of user edits in `data/synthetic_patients.json` | High | Full backup created at `RetinaX_Healthathon_BACKUP_PHASE0`; import script loads directly from active `synthetic_patients.json` before falling back to seed. |
| Incompatible Python packages | Medium | Dependencies pinned in `backend/requirements.txt` ensuring compatibility with Python 3.12 - 3.14. |
| Corrupt document preview | Low | All 9 synthetic documents converted to valid standard PDF binaries while maintaining their exact text and clinical context. |
| Schema drift during migration | Medium | Alembic versioned migrations with reversible up/down methods and automated validation tests. |
