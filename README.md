# RetinaX Care

## Closing the Loop in Diabetic Eye Care

**Problem Area:** Diabetic Retinopathy Screening Follow-up & Continuity of Care  
**Care Area:** Diabetes Care · RSSDI  
**Platform Scope:** Assistive diabetic eye-screening coordination, record consolidation, and follow-up tracking platform.

---

## 📌 Core Positioning

> "RetinaX Care helps diabetes-care teams identify incomplete retinal-screening journeys, coordinate specialist review and track clinician-directed follow-up before patients are lost to care."

RetinaX Care is **NOT a diagnostic AI tool**. It is an operational care-coordination platform engineered to eliminate dropouts and bridge communication gaps across the diabetes care continuum.

---

## 🔍 The Problem & Current Care Gap

Diabetic retinopathy (DR) is a leading cause of preventable blindness among working-age adults. While clinical guidelines recommend annual retinal examinations for all patients with diabetes, in practice:

1. **Fragmented Workflows:** Patients get screened at community camps or primary health centres (PHCs), but fundus images and reports are rarely linked back to their ongoing diabetes health record.
2. **Specialist Bottlenecks:** Fundus photographs sit in unindexed folders awaiting specialist review with zero workflow visibility into pending cases.
3. **Lost to Follow-Up:** Clinician-recommended follow-up actions (e.g. 6-month revisit, tertiary retina clinic referral) frequently fail because no operational tracking or patient engagement mechanism exists.
4. **Care Loop Breakdown:** Care teams lack a unified answer to the basic question: *"Which patients currently have an incomplete diabetic eye-care journey?"*

---

## 💡 The Solution: RetinaX Care

RetinaX Care provides an operational backbone that tracks every patient from initial diabetes intake to care loop completion:

```
IDENTIFY WORKFLOW GAP
        ↓
ASSIGN ACTION
        ↓
COORDINATE REVIEW (Human-In-The-Loop)
        ↓
ENGAGE PATIENT (Bilingual Reminders)
        ↓
TRACK FOLLOW-UP
        ↓
CLOSE CARE LOOP
```

---

## 👥 Who Uses RetinaX Care?

- **Diabetes Care Coordinators & Primary Health Staff:** Identify patients due for screening, schedule camp appointments, upload reports, and track follow-ups.
- **Consulting Ophthalmologists:** Review organized fundus photography reports and manually document clinical assessments and management instructions.
- **ASHA & Community Health Workers:** Receive alerts to re-engage patients with failed phone contacts or missing baseline records.

---

## 🛡️ Health-a-thon Scope & Non-Clinical AI Alignment

> **EXPLICIT SCOPE ALIGNMENT:**  
> Designed to align with Health-a-thon's non-clinical AI scope. Automated diagnostic and clinical decision-support functionality from the original RetinaX system is excluded from RetinaX Care.

- ❌ **No automated DR diagnosis:** Does not classify Grade 0–4 severity or predict diabetic retinopathy.
- ❌ **No autonomous clinical decision support:** Does not recommend clinical treatments or medical interventions.
- ❌ **No clinical risk scoring:** Does not calculate disease risk percentages or progression predictions.
- ❌ **No automated image interpretation:** Fundus images are cataloged for physician review, never interpreted by autonomous algorithms.
- ❌ **No automated referral triggers:** All referrals and re-examination intervals are manually determined and signed off by ophthalmologists.
- ❌ **Zero dependency on diagnostic models:** `trained_DR_model_v3.mat`, `trained_vessel_segmentation_v4_1.mat`, `dr_model.pth`, and Grad-CAM are completely excluded.

---

## 🚀 Key Features

### 1. Care Continuity Dashboard (Hero View)
- Real-time operational metrics answering: *"Which patients currently have an incomplete diabetic eye-care journey?"*
- Interactive metric cards for instant filtering:
  - **Total Cohort**
  - **Screening Not Started**
  - **Screening Scheduled**
  - **Screening Completed**
  - **Report Missing**
  - **Awaiting Specialist Review**
  - **Follow-Up Pending**
  - **Unable to Contact**
  - **Care Loop Completed**

### 2. Operational Patient Worklist
- Practical multi-column coordination table: Patient Details, ID, Screening Status, Report Status, Specialist Review, Follow-Up Status, Next Workflow Action, Assigned Staff, Due Date, and Last Contact.
- One-click filters including **Needs Workflow Attention** (prioritizing operational bottlenecks without clinical risk scoring).

### 3. Longitudinal Patient Journey Timeline
- Step-by-step visual tracker: Registered &rarr; Screening Ordered &rarr; Appointment Scheduled &rarr; Screening Completed &rarr; Report Uploaded &rarr; Specialist Review &rarr; Follow-Up Action &rarr; Loop Completed.
- Full audit log with timestamps, actors, departments, and coordination notes.

### 4. Care Journey Summary
- Factual single-view record summary that saves minutes of clinician search time across physical paper records.
- Organizes recorded vitals, document attachments, and missing workflow items with zero clinical deductions.

### 5. Document Hub
- Central repository for fundus images, optometry reports, laboratory panels (HbA1c/lipids), prescriptions, and historical consult slips.
- Document preview modal with metadata indexing and review status tagging.

### 6. Human-In-The-Loop Specialist Review Portal
- Interface where ophthalmologists manually enter clinical assessments, follow-up instructions, and referral decisions.
- **Deterministic Task Generator:** When a clinician enters an instruction (e.g. "Hospital follow-up in 6 months"), the system automatically creates an operational follow-up task assigned to the care coordinator.
- Prominently labeled: *"Clinical assessment entered by healthcare professional."*

### 7. Pending Action Engine & Follow-Up Tracker
- Deterministic rules identifying workflow gaps (e.g. uninitiated scheduling, missing uploads, pending specialist review, overdue follow-ups).
- Log contact attempts (Phone call, ASHA home visit, SMS) and close care cycles.

### 8. Bilingual Simulated Patient Reminders (English & Hindi)
- Operational reminder generator supporting English and **हिन्दी (Hindi)** templates for screening appointments, document requests, and follow-up notices.
- Prominently tagged: *"Demo notification — not actually sent"*.

---

## 🎬 Guided Demo Story — Mohammad Farooq (RX-1003 Hero)

RetinaX Care includes an interactive guided walkthrough built around **Mohammad Farooq (RX-1003)**:

1. **Step 1 (Identify Gap):** Care coordinator opens dashboard and sees **Awaiting Specialist Review: 3**. Clicks metric to filter worklist.
2. **Step 2 (Inspect Journey):** Opens RX-1003. Timeline shows: Screening completed ✓, Report uploaded ✓, Specialist review PENDING. System explains: *"Screening report is available, but specialist review has not yet been recorded."*
3. **Step 3 (Specialist Review):** Ophthalmologist reviews fundus report and manually enters clinical assessment and 6-month revisit instruction.
4. **Step 4 (Operational Task Creation):** RetinaX Care automatically generates a follow-up coordination task for the coordinator based on the clinician's instruction.
5. **Step 5 (Patient Engagement):** Coordinator previews and triggers a simulated SMS notification in Hindi.
6. **Step 6 (Close Care Loop):** Once follow-up is attended, coordinator completes the task and changes status to **Care Loop Completed**.

*Secondary benchmark:* **Gurpreet Singh (RX-1005)** is available to demonstrate an already closed annual care loop.

---

## 🏛️ System Architecture

```
RetinaX_Healthathon/
├── README.md                      # Comprehensive project documentation
├── requirements.txt               # Lightweight Python dependencies (Flask, Werkzeug)
├── server.py                      # Flask REST API backend & workflow rules engine
├── .gitignore                     # Safety exclusions (PHI, weights, datasets)
│
├── frontend/                      # Clean, responsive single-page application
│   ├── index.html                 # Semantic HTML structure & multi-view modals
│   ├── styles.css                 # Medical design tokens, dark/light themes, custom UI
│   └── app.js                     # State management, filtering, bilingual reminders
│
├── data/
│   └── synthetic_patients.json    # 12 diverse synthetic patients (100% de-identified)
│
├── uploads/                       # Document repository for mock PDF/image records
│
├── tests_runner.py                # Automated unit and integration test suite
└── audit_compliance.py            # Static code & UI compliance scanner
```

---

## ⚡ Quickstart Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start RetinaX Care
```bash
python server.py
```

### 3. Open in Browser
Navigate to:
```
http://127.0.0.1:5000
```

---

## 🔒 Synthetic Data & Privacy Safeguards

- **100% Synthetic Cohort:** All 12 demo patients are entirely fictional with synthetic clinical profiles.
- **Zero Protected Health Information (PHI):** No real clinical records or identifiable patient data are utilized.
- **Transparent Distinction:** The UI strictly separates `SYSTEM WORKFLOW STATUS` from `CLINICIAN-ENTERED INFORMATION`.

---

## 📜 Event Track Alignment
Built specifically for **Health-a-thon 2026** under the **Diabetes Care · RSSDI** track to address diabetic retinopathy screening dropouts and maintain care continuity.
