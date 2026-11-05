# RetinaX Care — Security Hardening, Threat Model & Governance

**Document Version:** 2.0.0  
**Classification:** Healthcare Operational Security Specification  
**Standard:** OWASP Top 10 (2021) & Health-a-thon Compliance  

---

## 1. Security Architecture Summary

RetinaX Care applies defense-in-depth across the client, network, application, and database tiers.

```
+-------------------------------------------------------------------------+
| Layer 1: Ingress & Network Defense                                      |
| - Restrictive CORS allowlist (whitelisted origins only)                 |
| - Secure response headers (HSTS, X-Frame-Options, X-Content-Type-Options)|
| - Rate limiting on authentication & upload endpoints                     |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
| Layer 2: Authentication & Role-Based Access Control                     |
| - Argon2id cryptographic password hashing                               |
| - Server-side JWT session validation with HttpOnly cookies              |
| - Strict backend authorization dependencies (require_specialist, etc.)   |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
| Layer 3: Application Data & Storage Isolation                           |
| - Pydantic V2 strict type validation & input sanitization               |
| - Binary magic-byte inspection (rejection of disguised executables)     |
| - Sanitized UUID object storage keys (no path traversal, no PHI in keys)|
| - Authenticated document streaming (no unauthenticated file serving)     |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
| Layer 4: Audit & Accountability                                         |
| - Immutable audit event logging (actor, role, action, target, timestamp)|
| - Parameterized ORM queries (SQLAlchemy 2.0 SQL-injection prevention)   |
| - Offline IndexedDB storage with conflict resolution                    |
+-------------------------------------------------------------------------+
```

---

## 2. Authentication & Credential Protection

### Cryptographic Hashing: Argon2id
All user passwords are encrypted using **Argon2id** (`argon2-cffi`), the winner of the Password Hashing Competition. Argon2id provides superior resistance against side-channel and GPU/ASIC-based brute-force attacks compared to standard MD5, SHA-256, or plain bcrypt.
- Password hash structure: `$argon2id$v=19$m=65536,t=3,p=4$...`

### Session Tokens & Cookies
- Authentication tokens are signed using HMAC-SHA256 with a high-entropy secret key.
- Issued with an expiration window of 120 minutes.
- Delivered via `Authorization: Bearer <token>` or stored in `HttpOnly`, `SameSite=Lax` cookies, preventing token leakage via client-side JavaScript XSS.

---

## 3. Backend-Enforced Role-Based Access Control (RBAC)

The previous vulnerable client-side role toggle has been completely eliminated. Role authorization is strictly enforced by FastAPI dependency guards on every protected route:

| Role | Permitted Operational Capabilities | Prohibited Capabilities |
|---|---|---|
| **Specialist** | View assigned reading queue; submit ophthalmologist tele-review; enter qualitative clinical directives. | Cannot obtain autonomous AI grading; cannot access administrative system logs. |
| **Care Coordinator** | View patient records; update follow-up statuses; log contact attempts; upload screening dossiers; trigger simulated reminders. | **Strictly prohibited** from editing or submitting specialist reviews (HTTP 403 Forbidden). |
| **Administrator** | Manage user accounts; inspect immutable audit event log; reset demonstration cohort; manage system configuration. | Cannot bypass clinical review requirements or alter attributed ophthalmologist directives. |

**RBAC Test Verification:**
Automated test suite (`backend/tests/test_backend.py`) verifies that a Care Coordinator attempting to call `POST /api/v1/reviews/{patient_id}` receives `HTTP 403 Forbidden: Role 'Care Coordinator' is not authorized for this operational action`.

---

## 4. Document Ingestion Security & Magic-Byte Validation

To prevent malicious file execution or disguise attacks, the document ingestion pipeline implements multi-stage validation:

1. **Size Verification:** Rejects requests exceeding 32 MB (`HTTP 413 Entity Too Large`).
2. **Extension Whitelist:** Only `.pdf`, `.jpg`, `.jpeg`, and `.png` extensions permitted.
3. **Binary Magic-Byte Inspection:** Inspects initial bytes of uploaded file stream:
   - PDF: Must begin with `%PDF-` (`0x25 0x50 0x44 0x46 0x2D`)
   - JPEG: Must begin with `\xff\xd8\xff`
   - PNG: Must begin with `\x89PNG\r\n\x1a\n`
   - Files with plain text or executable headers (`MZ`, `\x7fELF`) masquerading as `.pdf` are rejected (`HTTP 400 Bad Request`).
4. **Malware Scanning Hook:** Documented integration point for Antivirus engines (e.g. ClamAV).
5. **Key Sanitization:** User filenames are stripped of non-alphanumeric characters, and stored using random UUID prefixes (e.g. `documents/3f82a1bc_fundus_scan.pdf`). Original patient identifiers are never placed in raw object keys.
6. **No Public Storage Access:** The open endpoint `GET /api/uploads/<filename>` has been removed. All document downloads require active authentication and are routed through `GET /api/v1/documents/{id}/download`.
7. **Genuine Synthetic PDF Replacement:** The previous dummy text files in `uploads/` have been replaced with standard, fully valid `%PDF-1.4` binary synthetic records generated with clean PDF streams.

---

## 5. Security Response Headers

All HTTP responses pass through the security headers middleware:

- `X-Content-Type-Options: nosniff` — Prevents MIME-type sniffing.
- `X-Frame-Options: DENY` — Prevents clickjacking attacks.
- `X-XSS-Protection: 1; mode=block` — Enables legacy browser XSS filters.
- `Referrer-Policy: strict-origin-when-cross-origin` — Protects token leakage in referrer headers.
- `Permissions-Policy: geolocation=(), microphone=(), camera=()` — Disables unneeded hardware APIs.
- `X-RetinaX-Scope: Operational-Care-Continuity-Only` — Explicit declaration of non-clinical scope.

---

## 6. Audit Trail & Accountability

All sensitive actions generate an immutable record in the `audit_events` table:

- `USER_LOGIN` / `USER_LOGOUT`
- `PATIENT_CREATED`
- `SPECIALIST_REVIEW_COMPLETED` (records clinician name, medical registration number, and timestamp)
- `FOLLOWUP_STATUS_UPDATE`
- `TASK_CREATED` / `TASK_COMPLETED`
- `DOCUMENT_UPLOADED` (logs SHA256 integrity hash and file size)
- `DOCUMENT_DOWNLOADED`
- `REMINDER_SIMULATED_DISPATCH`
- `SYNTHETIC_COHORT_RESET`

Audit events can only be queried by users with the `Administrator` role (`GET /api/v1/audit`).
