# RetinaX Care — System Architecture & Component Design

**Version:** 2.0.0 (Health-a-thon 2026 Production MVP)  
**Positioning:** Closing the Loop in Diabetic Eye Care  
**Subtitle:** Diabetic Retinopathy Screening Follow-up & Continuity of Care  

---

## 1. Architectural Overview

RetinaX Care is engineered as a secure, distributed, micro-monorepo designed to eliminate dropouts between primary diabetic eye screening and subsequent ophthalmologist-directed care.

```
                                  +-------------------------------------------------+
                                  |            CLIENT APPLICATION LAYER             |
                                  |  Next.js 15+ (App Router) / React 19 / TS       |
                                  |  IndexedDB Offline Storage / Service Worker PWA |
                                  +-----------------------+-------------------------+
                                                          |
                                      HTTPS / TLS 1.3     | REST API & JWT Bearer
                                                          v
                                  +-------------------------------------------------+
                                  |               API GATEWAY / INGRESS             |
                                  |  Reverse Proxy / CORS Whitelist / Secure Headers|
                                  +-----------------------+-------------------------+
                                                          |
                                                          v
                                  +-------------------------------------------------+
                                  |           FASTAPI APPLICATION CORE              |
                                  |  - Role-Based Access Control (Specialist/Coord) |
                                  |  - Magic-Byte Binary Document Validation        |
                                  |  - Non-Clinical Operational State Engines       |
                                  |  - HL7 / FHIR R4 Interoperability Adapter       |
                                  +--------+------------------+----------------+----+
                                           |                  |                |
                          SQLAlchemy 2.0   |     Celery Tasks |   boto3 Client |
                                           v                  v                v
                        +----------------------+    +-----------------+  +-------------------+
                        |   POSTGRESQL 16      |    |  REDIS 7 BROKER |  | S3 / MINIO OBJECT |
                        | Normalized Models,   |    | Message Queue & |  | Encrypted Storage |
                        | Foreign Keys & Index |    | Rate Limiting   |  | Signed URL Store  |
                        +----------------------+    +-----------------+  +-------------------+
```

---

## 2. Technology Stack & Pinned Component Versions

| Tier | Component | Selection & Rationale |
|---|---|---|
| **Frontend** | Next.js 15+ / React 19 / TypeScript 5.7 | High-performance App Router with server-side rendering, strict typed contracts, and zero layout shift. |
| **Styling** | Custom Healthcare Design System | Native CSS variables, restrained palette, tested responsive grid (320px–1440px), dark/light modes. |
| **Offline Layer** | W3C IndexedDB + Service Worker | Client-side mutation queue with conflict detection, ensuring rural field continuity without data loss. |
| **Backend API** | FastAPI 0.115+ / Python 3.12–3.14 | High-throughput asynchronous framework with automatic OpenAPI documentation and Pydantic validation. |
| **Persistence** | PostgreSQL 16 + SQLAlchemy 2.0 | Normalized schemas, ACID compliance, cascading deletes, and Alembic database versioning. |
| **Auth & RBAC** | Argon2id + JWT + HttpOnly Cookies | Password hashing resistant to GPU/ASIC attacks, backend dependency guards (`require_specialist`, `require_coordinator`, `require_admin`). |
| **Document Security**| Python Magic Bytes + SHA256 Hash | File signature validation (`%PDF-`, `\xff\xd8\xff`, `\x89PNG`), private object storage, authenticated downloads. |
| **Task Queue** | Celery 5.4+ + Redis 7 | Asynchronous simulation of bilingual SMS/WhatsApp reminders and periodic care milestone reconciliation. |
| **Storage Abstraction**| Local Filesystem & AWS S3 / MinIO | Pluggable `BaseStorageProvider` enabling zero-cloud local development with production AWS S3 readiness. |
| **Containers** | Docker & Docker Compose | Multi-stage Dockerfiles with unprivileged service users (`retinax:retinax` and `nextjs:nodejs`). |
| **Interoperability**| HL7 FHIR R4 Adapter | Bidirectional mapping for `Patient`, `Task`, and `DocumentReference` operational resources. |

---

## 3. Core Modules & Operational Workflows

### 3.1 Patients Directory
- Master registry of diabetic cohort participants.
- Operational search and 10 multi-criteria filter modes (`needs_attention`, `report_missing`, `unable_to_contact`, etc.).
- Rules-based 6-point record completeness scorecard (contact details, diabetes duration, baseline HbA1c recorded, screening report uploaded, specialist review recorded, follow-up scheduled).
- Zero clinical risk scoring or automated inferences.

### 3.2 Care Journey Digital Twin
- Dedicated directory before deep-dive inspection.
- 5-phase visual pathway tracking:
  1. Cohort Intake & Profiling
  2. Retinal Screening Appointment
  3. Screening Report Dossier Ingestion
  4. Specialist Review & Directives
  5. Follow-Up Coordination & Loop Closure
- Interactive step-by-step audit showing timestamps, responsible staff, and next actionable operational milestone.

### 3.3 Specialist Reviews (Tele-Ophthalmology Queue)
- Dedicated triage worklist sorting patients awaiting specialist reading.
- Review workspace presents uploaded bilateral screening images and patient operational parameters.
- Review submission is strictly protected by backend RBAC (`require_specialist`).
- Requires attributed clinician metadata (name, specialty, registration number, qualitative note, follow-up instruction).
- Clinician directive automatically triggers an operational task assigned to the care coordinator.

### 3.4 Follow-Ups & Communication Hub
- Real-time worklist of pending, scheduled, completed, and unreachable patients.
- Contact attempt logger capturing date, method (Phone, SMS, WhatsApp, ASHA Home Visit), result, and notes.
- Simulated bilingual reminder dispatcher generating neutral, non-diagnostic appointment notifications in English and Hindi.
- Explicit notice: "DEMO — NOT SENT TO PATIENT".

### 3.5 Document Repository
- Encrypted document storage for screening reports, laboratory summaries, and referral sheets.
- Binary magic-byte inspection rejecting executables, scripts, or disguised text files.
- Authenticated download endpoints verifying session authorization before streaming file bytes.

### 3.6 Continuity Insights & Care Gap Radar
- Telemetry computed dynamically from database queries (zero hardcoded numbers).
- Real-time Care Gap Radar flagging missing reports, overdue reviews, and communication breakdowns.
- Data Reconciliation Queue identifying discrepancies between outreach data and clinic records with one-click resolution.
