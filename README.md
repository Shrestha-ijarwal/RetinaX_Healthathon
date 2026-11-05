# RetinaX Care

## Closing the Loop in Diabetic Eye Care
**Diabetic Retinopathy Screening Follow-up & Continuity of Care Platform**  
*Health-a-thon 2026 Production MVP — Diabetes Care & RSSDI Track*

---

> [!IMPORTANT]
> **ABSOLUTE PROJECT SEPARATION & RESEARCH ISOLATION:**  
> This repository (**RetinaX Care**, `RetinaX_Healthathon`) is an **operational care-continuity platform**.  
> It is completely separate from **Project A (Original RetinaX)**, which was an exploratory retinal AI research project.  
> RetinaX Care strictly excludes automated diagnostic AI, disease grading (DR 0–4), AI risk scores, and clinical decision support. All clinical evaluations remain with qualified medical professionals.

---

## 1. Product Identity & Purpose

Diabetic retinopathy (DR) is a leading cause of preventable blindness among adults. Although clinical guidelines advocate annual retinal examinations for all individuals with diabetes, screening initiatives frequently suffer from catastrophic follow-up dropout:
- **Screening records remain unindexed** across primary health centres and outreach camps.
- **Ophthalmologists face unorganized review queues** without clear triage visibility.
- **Patients fall through care gaps** because clinician-ordered follow-up actions lack tracking and engagement.

**RetinaX Care** closes this operational loop by providing a full-stack, secure, offline-capable platform that tracks every patient from initial diabetes intake to confirmed follow-up and annual cycle completion.

---

## 2. Upgraded Target Architecture

RetinaX Care has been upgraded from a legacy single-file prototype into an enterprise full-stack micro-monorepo:

| Layer | Upgraded Technology | Key Implementations |
|---|---|---|
| **Frontend** | Next.js 15+ / React 19 / TypeScript 5.7 | Next.js App Router, responsive design (320px–1440px), accessible healthcare components. |
| **Offline Layer** | W3C IndexedDB + Service Worker PWA | Offline mutation queue, background sync, conflict resolution ledger, online/offline status bar. |
| **Backend API** | Python FastAPI / Pydantic V2 | Asynchronous REST endpoints (`/api/v1`), centralized error handling, OpenAPI docs. |
| **Database** | PostgreSQL 16 / SQLAlchemy 2.0 | Normalized relational schema, cascading deletes, foreign keys, Alembic migrations. |
| **Authentication** | Argon2id + JWT + HttpOnly Cookies | Cryptographic password hashing, secure session management, backend RBAC dependencies. |
| **Authorization** | Strict Backend RBAC | `Specialist`, `Care Coordinator`, `Administrator` roles enforced by FastAPI guards. |
| **Document Storage**| Storage Provider Abstraction | Binary magic-byte validation (`%PDF-`, `\xff\xd8\xff`, `\x89PNG`), authenticated streaming, S3/MinIO. |
| **Background Jobs** | Celery 5.4 + Redis 7 | Simulated bilingual reminder delivery (English & Hindi), automated milestone reconciliation. |
| **Containers** | Docker & Docker Compose | Multi-stage Dockerfiles with non-root security users, health checks, persistent volumes. |
| **Interoperability**| HL7 FHIR R4 Adapter | Mappings for `Patient`, `Task`, and `DocumentReference` operational resources. |

---

## 3. The Six Primary Modules

1. **Patients Directory (`/patients`):** Master registry with search, 10 operational filter modes (`needs_attention`, `report_missing`, `unable_to_contact`, etc.), and 6-point record completeness scorecard.
2. **Care Journeys (`/journeys`):** Overview directory displaying progression percentage (0–100%) and current step; opens the interactive **Care Journey Digital Twin** upon selecting a patient.
3. **Specialist Reviews (`/reviews`):** Dedicated tele-ophthalmology reading queue with review workspace; strictly requires `Specialist` role and records clinician-attributed directives.
4. **Follow-Ups Hub (`/followups`):** Real-time worklist tracking pending, scheduled, completed, and unreachable patients; logs contact attempts (phone, SMS, WhatsApp, ASHA visit); dispatches bilingual simulated reminders.
5. **Clinical Documents (`/documents`):** Secured document archive with binary signature validation, sanitized storage keys, and authenticated download endpoints.
6. **Continuity Insights (`/analytics`):** Real-time metrics computed dynamically from database records (closure rate, turnaround days, facility distribution), Care Gap Radar, and Data Reconciliation Queue.

---

## 4. Quick Start: Local Docker Compose (Recommended)

Run the entire full-stack application with a single command:

```bash
# 1. Clone repository
git clone https://github.com/Shrestha-ijarwal/RetinaX_Healthathon.git
cd RetinaX_Healthathon

# 2. Configure environment
cp .env.example .env

# 3. Start all services
docker compose build
docker compose up -d

# 4. Verify running health
docker compose ps
```

- **Frontend Application:** `http://localhost:3000`
- **FastAPI Backend & Health:** `http://localhost:8000/health`
- **Interactive OpenAPI Documentation:** `http://localhost:8000/api/v1/docs`
- **MinIO Storage Console:** `http://localhost:9001`

---

## 5. Native Local Development (Without Docker)

### 5.1 Backend
```powershell
Set-Location "C:\Users\sijar\Downloads\RetinaX_Healthathon"
$env:PYTHONPATH="C:\Users\sijar\Downloads\RetinaX_Healthathon"

# Install backend packages
pip install -r backend/requirements.txt

# Run migrations
python -m alembic upgrade head

# Seed synthetic cohort & demonstration accounts
python backend/app/db/seed.py

# Start FastAPI server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5.2 Frontend
```powershell
Set-Location "C:\Users\sijar\Downloads\RetinaX_Healthathon\frontend"
npm.cmd install
npm.cmd run dev
```

---

## 6. Demonstration Accounts & Roles

Switch between roles anytime via the top-right profile popover menu:

| Role | Email | Password | Full Name | Permitted Capabilities |
|---|---|---|---|---|
| **Specialist** | `specialist@retinax.care` | `Specialist@2026` | Dr. Suresh Chandran, MS | Access specialist review queue, record qualitative clinical assessments, submit attributed follow-up directives. |
| **Care Coordinator** | `coordinator@retinax.care` | `Coordinator@2026` | Ananya Sharma | View cohort, register synthetic patients, log contact attempts, dispatch simulated bilingual reminders. *(Blocked from submitting specialist reviews)* |
| **Administrator** | `admin@retinax.care` | `Admin@2026` | Rajiv Menon | Inspect immutable audit logs, reset demonstration cohort, manage platform configuration. |

---

## 7. Automated Test Suite & Compliance Audit

Execute the complete 22-test automated verification suite:

```powershell
Set-Location "C:\Users\sijar\Downloads\RetinaX_Healthathon"
$env:PYTHONPATH="C:\Users\sijar\Downloads\RetinaX_Healthathon"
python -m pytest backend/tests/test_backend.py -v
```

**Results:** `22 passed, 0 failed (100% pass rate)`  
- Authenticated login & session invalidation verified.
- RBAC authorization barriers verified (Care Coordinator blocked with HTTP 403 on specialist endpoints).
- File upload magic-byte rejection verified.
- Zero prohibited clinical AI terms confirmed.

---

## 8. Documentation Index

- [Architecture & Tech Stack](docs/ARCHITECTURE.md)
- [Migration Inventory & Safety Plan](docs/MIGRATION_INVENTORY.md)
- [Relational Data Model & ERD](docs/DATA_MODEL.md)
- [REST API & OpenAPI Specification](docs/API.md)
- [Security Hardening & Threat Model](docs/SECURITY.md)
- [Deployment & AWS Guide](docs/DEPLOYMENT.md)
- [12-Step Demonstration Script](docs/DEMO_GUIDE.md)
- [Test Suite & QA Report](docs/TESTING.md)
- [Known Limitations & Disclosures](docs/KNOWN_LIMITATIONS.md)

---

## 9. Non-Clinical Scope & Compliance Notice

> **DISCLAIMER:** RetinaX Care supports operational care coordination and continuity tracking. It does not provide diagnosis, clinical risk assessment, treatment recommendations, or autonomous clinical decision-making. Clinical decisions remain the responsibility of qualified healthcare professionals. All demonstration records are synthetic and fictional.
