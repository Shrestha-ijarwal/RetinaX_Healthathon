# RetinaX Care — Health-a-thon 2026 Live Demonstration Guide

**Product Positioning:** Closing the Loop in Diabetic Eye Care  
**Track:** Diabetes Care & RSSDI Track  
**Objective:** Demonstrate operational care continuity, specialist queue coordination, and loop closure without diagnostic AI.  

---

## 1. Demonstration Narrative Overview

Diabetic retinopathy screening programs in low- and middle-income regions face a critical operational breakdown: patients attend community screening camps or primary health centres, but their reports remain unreviewed, specialist referrals are lost, and coordinators lack systematic tracking to prevent dropout.

RetinaX Care demonstrates how an operational platform closes this loop through 12 structured operational steps.

---

## 2. Step-by-Step 12-Stage Demonstration Script

### Step 1: Open the Patient Directory
1. Navigate to `http://localhost:3000/patients` (or click **Patients** in the top navigation bar).
2. Note the directory of 12 synthetic patients.
3. Filter by **Needs Attention** or **Awaiting Review** to immediately observe prioritized patients.
4. Point out the **Completeness Score** column, showing rules-based demographic and documentation readiness (e.g. contact phone, baseline HbA1c recorded, screening report uploaded).

### Step 2: Select a Synthetic Patient (e.g., Manjula Shankaran, `RX-1011`)
1. Click **View Details** on patient `RX-1011`.
2. Review the patient drawer:
   - Primary Health Facility: `Anekal Eye Unit`
   - Diabetes Duration: Documented
   - Attached documents: 4 records (Screening photos, prescription, lab report, previous discharge summary).
3. Close the drawer.

### Step 3: Open the Care Journey Digital Twin
1. Navigate to **Care Journeys** (`/journeys`).
2. Point out that the directory displays operational progress across all patients rather than auto-selecting someone.
3. Click on patient `RX-1011` to open the interactive **Care Journey Digital Twin**.
4. Show the 5-phase operational pathway:
   - Phase 1 (Cohort Intake): Completed
   - Phase 2 (Retinal Screening): Completed (2026-09-29)
   - Phase 3 (Report Dossier): 4 Documents Attached
   - Phase 4 (Specialist Review): Pending Review
   - Phase 5 (Loop Closure): In Progress

### Step 4: Review Screening Workflow Status
1. Observe that while bilateral screening photos were taken on 2026-09-29 and uploaded to the repository, specialist review has not yet occurred.
2. Note the **Next Operational Action**: *"Ophthalmologist to review multi-record dossier (4 documents)"*.

### Step 5: Log In as Specialist & Open Review Queue
1. Navigate to `/login` (or click **Switch Account / Logout** from the top-right user menu).
2. Click the quick judging evaluation button **Specialist (Dr. Suresh Chandran)** to auto-fill credentials, then click **Sign In**.
3. Navigate to **Specialist Reviews** (`/reviews`).
4. Notice that the tele-ophthalmology reading queue lists `RX-1011` as *"Awaiting Review"* with 4 attached screening documents.
5. Click **Open Review Workspace →** on `RX-1011`.

### Step 6: Review Attached Dossier & Record Attributed Operational Directives
1. On the left pane, view the attached documents and click **View Verified PDF** to open the genuine standard PDF report.
2. On the right pane, complete the attributed operational review form:
   - Clinician Name: `Dr. Suresh Chandran, MS`
   - Medical Specialty: `Ophthalmology`
   - Medical Registration: `MCI-2016-849201`
   - Operational Review Status: `Completed`
   - Attributed Clinician Directive: *"Screening dossier reviewed. Follow-up eye examination recommended at District Eye Hospital within 6 months. Assist with transportation if needed."*
   - Operational Task Instructions: *"Coordinate hospital visit scheduling and transport assistance with patient family."*
3. Click **Submit Operational Review Directive**.
4. The review is recorded and attributed to the clinician. The care journey advances to *"Specialist Review Completed"*.

### Step 7: Verify RBAC Protection (Coordinator Cannot Review)
1. Switch roles to **Ananya Sharma (Care Coordinator)** from `/login` or the topbar user menu.
2. Attempt to submit a specialist review on any pending patient.
3. Observe that the submission buttons and forms are blocked in the UI, and any direct API call returns `HTTP 403 Forbidden`.

### Step 8: Manage Operational Follow-Up Worklist
1. Navigate to **Follow-Ups** (`/followups`).
2. Find patient `RX-1011` in the worklist. Note the updated directive and scheduled task.
3. Click **Log Contact**.
4. Record a contact attempt:
   - Method: `Phone Call`
   - Call Result: *"Spoke with patient daughter; confirmed transport arranged for hospital follow-up."*
   - Status: `Scheduled`
   - Planned Date: Select upcoming date (e.g., `2027-04-01`).
5. Click **Record Contact & Update**.

### Step 9: Simulate Bilingual Patient Reminder
1. In the follow-up worklist, click **Simulate Reminder** on `RX-1011`.
2. Select Language: **Hindi (हिंदी)** (or English).
3. Reminder Type: **Follow-Up Attendance**.
4. Click **Dispatch Simulated Reminder**.
5. View the rendered message preview in Hindi:
   > *"प्रिय Manjula Shankaran, Anekal Eye Unit में आपकी देखभाल टीम द्वारा आपकी डायबिटिक नेत्र अनुवर्ती जांच के संबंध में यह अनुस्मारक है..."*
6. Point out the clear banner: **"DEMO — NOT SENT TO PATIENT"**.

### Step 10: Inspect Live Continuity Analytics & Care Gap Radar
1. Navigate to **Insights** (`/analytics`).
2. Point out that all numbers are computed from actual database records (no hardcoded counters).
3. Switch to the **Care Gap Radar** tab:
   - Highlights patients lost to contact, missing reports, or delayed specialist reviews.
4. Switch to the **Reconciliation Queue** tab:
   - Shows records with missing contact details or date mismatches.
   - Click **Mark Reconciled ✓** to resolve an issue in real time.

### Step 11: Inspect the Immutable Audit Trail
1. Switch role to **Rajiv Menon (Administrator)**.
2. Check the system audit log (via `/api/v1/audit`).
3. Show the audit event:
   - Action: `SPECIALIST_REVIEW_COMPLETED`
   - Actor: `Dr. Suresh Chandran, MS (Specialist)`
   - Resource: `Patient RX-1011`
   - Timestamp and metadata accurately logged.

### Step 12: Demonstrate Offline Operation & PWA Synchronization
1. Disconnect network or toggle offline mode in browser DevTools (Network tab -> Offline).
2. The UI immediately displays the banner: *"⚠️ Offline Mode Active — Updates are saved locally to IndexedDB"*.
3. Log a contact attempt while offline. The change is persisted in IndexedDB and queued.
4. Toggle network back online (Network tab -> No throttling).
5. The banner changes to *"📶 Online — 1 offline update(s) ready to synchronize"*.
6. Click **Sync Now**. The pending mutation is processed and verified against the backend without conflict!
