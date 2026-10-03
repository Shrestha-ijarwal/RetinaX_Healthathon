"""
RetinaX Care - Diabetic Eye-Screening Coordination & Follow-Up Platform
Enterprise Care Continuity Edition
Tagline: "Closing the Loop in Diabetic Eye Care"
Subtext: "Care coordination • Follow-up • Patient engagement"

CORE POSITIONING:
"RetinaX Care helps diabetes-care teams identify incomplete retinal-screening
journeys, coordinate specialist review and track clinician-directed follow-up
before patients are lost to care."

SAFETY & SCOPE NOTICE:
RetinaX Care is strictly an assistive workflow coordination platform.
It does NOT provide diagnosis, treatment recommendations, clinical decision support,
clinical risk scoring, or automated clinical interpretation of retinal images.
All clinical interpretations and medical decisions remain with qualified healthcare professionals.
"""

import os
import sys
import json
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Paths
ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"
DATA_DIR = ROOT / "data"
UPLOADS_DIR = ROOT / "uploads"
DATA_FILE = DATA_DIR / "synthetic_patients.json"
SEED_FILE = DATA_DIR / "synthetic_patients_seed.json"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [RetinaX Care] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("retinax_care.server")

app = Flask(__name__, static_folder=None)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 MB limit

PATIENTS_STORE = []

def load_initial_data(from_seed=False):
    global PATIENTS_STORE
    try:
        source_path = SEED_FILE if from_seed or not DATA_FILE.exists() else DATA_FILE
        if source_path.exists():
            with open(source_path, "r", encoding="utf-8") as f:
                PATIENTS_STORE = json.load(f)
            if from_seed:
                save_data()
            logger.info(f"Successfully loaded {len(PATIENTS_STORE)} synthetic patient records from {source_path.name}.")
        else:
            PATIENTS_STORE = []
            logger.warning(f"Data file {source_path} not found. Starting with empty store.")
    except Exception as e:
        logger.error(f"Error loading initial data: {e}")
        PATIENTS_STORE = []

def save_data():
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(PATIENTS_STORE, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save synthetic data: {e}")

load_initial_data(from_seed=True)

# Helper: Rules-based record completeness checker (Non-diagnostic / Operational only)
def calculate_record_completeness(patient):
    missing_items = []
    checks = {
        "contact_number": bool(patient.get("contact") and patient.get("contact").strip()),
        "baseline_diabetes_duration": bool(patient.get("diabetes_profile", {}).get("duration_recorded") and patient.get("diabetes_profile", {}).get("duration_recorded") != "Unknown"),
        "baseline_hba1c": bool(patient.get("diabetes_profile", {}).get("last_hba1c") and patient.get("diabetes_profile", {}).get("last_hba1c") != "Not Recorded"),
        "screening_report_uploaded": any(d.get("doc_type") == "Retinal Screening Report" for d in patient.get("documents", [])),
        "specialist_review_recorded": patient.get("specialist_review", {}).get("completed", False),
        "followup_plan_defined": bool(patient.get("followup", {}).get("planned_date") or patient.get("diabetes_profile", {}).get("next_planned_screening"))
    }
    
    if not checks["contact_number"]:
        missing_items.append("Primary contact telephone number not on file")
    if not checks["baseline_diabetes_duration"]:
        missing_items.append("Diabetes duration not documented in source record")
    if not checks["baseline_hba1c"]:
        missing_items.append("Baseline HbA1c lab result not documented")
    if not checks["screening_report_uploaded"]:
        missing_items.append("Retinal screening report/images not uploaded")
    if not checks["specialist_review_recorded"]:
        missing_items.append("Specialist ophthalmologist review not recorded")
    if not checks["followup_plan_defined"]:
        missing_items.append("Next follow-up / screening date not scheduled")

    total_checks = len(checks)
    completed_checks = sum(1 for v in checks.values() if v)
    score_pct = int((completed_checks / total_checks) * 100)

    return {
        "score_percentage": score_pct,
        "completed_count": completed_checks,
        "total_checks": total_checks,
        "missing_items": missing_items,
        "is_complete": len(missing_items) == 0,
        "checks": checks
    }

# Helper: Calculate operational metrics
def get_operational_metrics():
    total = len(PATIENTS_STORE)
    not_started = sum(1 for p in PATIENTS_STORE if p.get("workflow_status", {}).get("screening_workflow") == "Not Started")
    scheduled = sum(1 for p in PATIENTS_STORE if p.get("workflow_status", {}).get("screening_workflow") == "Scheduled")
    screening_completed = sum(1 for p in PATIENTS_STORE if p.get("workflow_status", {}).get("screening_workflow") == "Completed")
    
    # Report missing: Screening done, but no retinal screening report doc
    report_missing = sum(1 for p in PATIENTS_STORE if p.get("workflow_status", {}).get("screening_workflow") == "Completed" and not any(d.get("doc_type") == "Retinal Screening Report" for d in p.get("documents", [])))
    
    # Awaiting review: Report uploaded, but review not completed
    awaiting_review = sum(1 for p in PATIENTS_STORE if not p.get("specialist_review", {}).get("completed") and any(d.get("doc_type") == "Retinal Screening Report" for d in p.get("documents", [])))
    
    # Follow-up pending
    followup_pending = sum(1 for p in PATIENTS_STORE if p.get("followup", {}).get("status") in ["Pending", "Scheduled"] and not p.get("workflow_status", {}).get("care_loop_completed"))
    
    # Unable to contact
    unable_to_contact = sum(1 for p in PATIENTS_STORE if p.get("followup", {}).get("status") == "Unable to Contact" or p.get("workflow_status", {}).get("overall_stage") == "Unable to Contact")
    
    # Care loop completed
    care_loop_completed = sum(1 for p in PATIENTS_STORE if p.get("workflow_status", {}).get("care_loop_completed", False))

    return {
        "total_patients": total,
        "not_started": not_started,
        "screening_scheduled": scheduled,
        "screening_completed": screening_completed,
        "report_missing": report_missing,
        "awaiting_specialist_review": awaiting_review,
        "followup_pending": followup_pending,
        "unable_to_contact": unable_to_contact,
        "care_loop_completed": care_loop_completed
    }

# CORS Header Injection
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = "*"
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
    response.headers['Access-Control-Allow-Headers'] = '*'
    return response

# Static frontend serving
@app.get("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.get("/<path:path>")
def serve_static(path):
    file_path = FRONTEND_DIR / path
    if file_path.exists() and file_path.is_file():
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")

# Documents download/serving
@app.get("/api/uploads/<path:filename>")
def get_uploaded_file(filename):
    safe_name = secure_filename(Path(filename).name)
    file_path = UPLOADS_DIR / safe_name
    if not file_path.exists():
        return jsonify(error="Document not found on disk"), 404
    return send_from_directory(UPLOADS_DIR, safe_name)

# API: Health Check
@app.get("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "RetinaX Care Backend",
        "version": "2.4.0-enterprise",
        "timestamp": datetime.now().isoformat(),
        "total_patients": len(PATIENTS_STORE),
        "compliance": "Designed for non-clinical AI scope. Assistive care coordination, specialist review workflow, and follow-up continuity platform. Zero automated diagnostic inference."
    })

# API: Patient Worklist with Operational Filtering
@app.get("/api/patients")
def list_patients():
    filter_type = request.args.get("filter", "all").lower()
    search = request.args.get("search", "").strip().lower()

    filtered = []
    for p in PATIENTS_STORE:
        # Search match (ID, Name, Clinician, Facility, Next Action)
        if search:
            match_str = f"{p.get('id', '')} {p.get('name', '')} {p.get('clinician', '')} {p.get('facility', '')} {p.get('workflow_status', {}).get('next_workflow_action', '')}".lower()
            if search not in match_str:
                continue

        stage = p.get("workflow_status", {}).get("overall_stage", "")
        wf_screen = p.get("workflow_status", {}).get("screening_workflow", "")
        has_report = any(d.get("doc_type") == "Retinal Screening Report" for d in p.get("documents", []))
        spec_rev = p.get("specialist_review", {}).get("completed", False)
        f_status = p.get("followup", {}).get("status", "")
        loop_done = p.get("workflow_status", {}).get("care_loop_completed", False)
        comp = calculate_record_completeness(p)

        include = False
        if filter_type == "all":
            include = True
        elif filter_type == "needs_attention":
            # Any incomplete workflow step
            include = not loop_done and (wf_screen == "Not Started" or (wf_screen == "Completed" and not has_report) or (has_report and not spec_rev) or f_status in ["Pending", "Unable to Contact"] or len(comp["missing_items"]) > 0)
        elif filter_type == "pending_screening" and wf_screen == "Not Started":
            include = True
        elif filter_type == "scheduled" and wf_screen == "Scheduled":
            include = True
        elif filter_type == "screening_completed" and wf_screen == "Completed":
            include = True
        elif filter_type == "report_missing" and wf_screen == "Completed" and not has_report:
            include = True
        elif filter_type == "awaiting_review" and (has_report and not spec_rev):
            include = True
        elif filter_type == "followup_pending" and f_status in ["Pending", "Scheduled"] and not loop_done:
            include = True
        elif filter_type == "unable_to_contact" and (f_status == "Unable to Contact" or stage == "Unable to Contact"):
            include = True
        elif filter_type == "completed" and loop_done:
            include = True

        if include:
            p_summary = dict(p)
            p_summary["completeness"] = comp
            # Ensure next_workflow_action and assigned_to are populated
            if not p_summary.get("workflow_status", {}).get("next_workflow_action"):
                if wf_screen == "Not Started":
                    p_summary["workflow_status"]["next_workflow_action"] = "Initiate screening workflow"
                elif wf_screen == "Scheduled":
                    p_summary["workflow_status"]["next_workflow_action"] = "Confirm camp appointment"
                elif wf_screen == "Completed" and not has_report:
                    p_summary["workflow_status"]["next_workflow_action"] = "Upload screening report"
                elif has_report and not spec_rev:
                    p_summary["workflow_status"]["next_workflow_action"] = "Specialist review required"
                elif loop_done:
                    p_summary["workflow_status"]["next_workflow_action"] = "Care loop completed for 2026"
                else:
                    p_summary["workflow_status"]["next_workflow_action"] = "Coordinate follow-up revisit"

            filtered.append(p_summary)

    # Operational sorting (Workflow attention: items needing review/upload/contact first)
    def operational_sort_key(patient):
        if patient.get("workflow_status", {}).get("care_loop_completed"):
            return 9
        f_status = patient.get("followup", {}).get("status")
        if f_status == "Unable to Contact":
            return 1
        has_report = any(d.get("doc_type") == "Retinal Screening Report" for d in patient.get("documents", []))
        spec_rev = patient.get("specialist_review", {}).get("completed", False)
        wf_screen = patient.get("workflow_status", {}).get("screening_workflow")
        if wf_screen == "Completed" and not has_report:
            return 2
        if has_report and not spec_rev:
            return 3
        if f_status == "Pending":
            return 4
        if wf_screen == "Scheduled":
            return 5
        return 6

    filtered.sort(key=operational_sort_key)

    metrics = get_operational_metrics()
    return jsonify({
        "metrics": metrics,
        "patients": filtered,
        "count": len(filtered)
    })

# API: Single Patient Detail
@app.get("/api/patients/<patient_id>")
def get_patient(patient_id):
    patient = next((p for p in PATIENTS_STORE if p.get("id") == patient_id), None)
    if not patient:
        return jsonify(error="Patient not found"), 404
    
    completeness = calculate_record_completeness(patient)
    res = dict(patient)
    res["completeness"] = completeness
    return jsonify(res)

# API: Add New Patient (Registration)
@app.post("/api/patients")
def register_patient():
    data = request.json or {}
    new_id = f"RX-{1000 + len(PATIENTS_STORE) + 1}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    today_str = datetime.now().strftime("%Y-%m-%d")

    patient = {
        "id": new_id,
        "name": data.get("name", "Unknown Patient"),
        "age": int(data.get("age", 50)),
        "sex": data.get("sex", "Other"),
        "contact": data.get("contact", ""),
        "facility": data.get("facility", "Primary Health Centre"),
        "clinician": data.get("clinician", "Attending Physician"),
        "registration_date": today_str,
        "diabetes_profile": {
            "type": data.get("diabetes_type", "Type 2 Diabetes Mellitus"),
            "duration_recorded": data.get("duration", "Not Specified"),
            "last_hba1c": data.get("hba1c", "Not Recorded"),
            "hba1c_date": today_str if data.get("hba1c") else None,
            "current_medications": data.get("medications", "None documented"),
            "last_retinal_screening": "None documented",
            "next_planned_screening": None
        },
        "workflow_status": {
            "overall_stage": "Screening Not Started",
            "screening_workflow": "Not Started",
            "screening_appointment_date": None,
            "document_status": "No Documents",
            "specialist_review": "Not Started",
            "followup_status": "Pending",
            "care_loop_completed": False,
            "next_workflow_action": "Initiate screening workflow & schedule baseline appointment",
            "assigned_to": data.get("registered_by", "Care Coordinator"),
            "due_date": today_str,
            "last_contact_date": today_str,
            "last_contact_method": "In-Person Registration"
        },
        "timeline": [
            {
                "id": str(uuid.uuid4())[:8],
                "stage": "Patient Registered",
                "timestamp": now_str,
                "source": "Outpatient Desk",
                "actor": data.get("registered_by", "Care Coordinator"),
                "status": "Completed",
                "note": "Patient enrolled in RetinaX Care diabetic eye screening tracker."
            }
        ],
        "documents": [],
        "specialist_review": {
            "completed": False,
            "clinician_name": None,
            "review_timestamp": None,
            "clinical_assessment": "",
            "followup_instructions": "",
            "referral_status": "Not Started",
            "notes": ""
        },
        "pending_tasks": [
            {
                "id": f"tsk-{uuid.uuid4().hex[:6]}",
                "title": "Initiate Retinal Screening Workflow",
                "description": "Schedule initial fundus photography screening appointment for newly registered patient.",
                "assigned_to": data.get("registered_by", "Care Coordinator"),
                "due_date": today_str,
                "status": "Open",
                "priority": "Medium",
                "created_at": today_str
            }
        ],
        "followup": {
            "status": "Pending",
            "planned_date": None,
            "responsible_staff": data.get("registered_by", "Care Coordinator"),
            "contact_attempts": [],
            "completion_timestamp": None,
            "notes": "Initial follow-up pending screening workflow."
        },
        "reminders": []
    }

    PATIENTS_STORE.insert(0, patient)
    save_data()
    return jsonify({"message": "Patient registered successfully", "patient": patient}), 201

# API: Add Timeline Event
@app.post("/api/patients/<patient_id>/timeline")
def add_timeline_event(patient_id):
    patient = next((p for p in PATIENTS_STORE if p.get("id") == patient_id), None)
    if not patient:
        return jsonify(error="Patient not found"), 404

    data = request.json or {}
    event = {
        "id": f"evt-{uuid.uuid4().hex[:6]}",
        "stage": data.get("stage", "Workflow Update"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": data.get("source", "Coordination Portal"),
        "actor": data.get("actor", "Care Coordinator"),
        "status": data.get("status", "Completed"),
        "note": data.get("note", "")
    }
    patient["timeline"].append(event)
    save_data()
    return jsonify({"message": "Timeline updated", "event": event, "patient": patient})

# API: Upload Document / Record Attachment
@app.post("/api/patients/<patient_id>/documents")
def upload_patient_document(patient_id):
    patient = next((p for p in PATIENTS_STORE if p.get("id") == patient_id), None)
    if not patient:
        return jsonify(error="Patient not found"), 404

    title = request.form.get("title") or (request.json and request.json.get("title")) or "Medical Record Attachment"
    doc_type = request.form.get("doc_type") or (request.json and request.json.get("doc_type")) or "Retinal Screening Report"
    source = request.form.get("source") or (request.json and request.json.get("source")) or "Clinical Unit"
    
    file_name = f"doc_{patient_id}_{uuid.uuid4().hex[:6]}.pdf"
    size_kb = 450

    if 'file' in request.files:
        file = request.files['file']
        if file.filename:
            file_name = secure_filename(f"{patient_id}_{file.filename}")
            UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
            save_path = UPLOADS_DIR / file_name
            file.save(save_path)
            size_kb = round(os.path.getsize(save_path) / 1024, 1)

    new_doc = {
        "id": f"doc-{uuid.uuid4().hex[:6]}",
        "title": title,
        "doc_type": doc_type,
        "upload_date": datetime.now().strftime("%Y-%m-%d"),
        "source": source,
        "review_status": "Awaiting Specialist Review" if doc_type == "Retinal Screening Report" else "Filed",
        "file_name": file_name,
        "size_kb": size_kb
    }

    patient["documents"].append(new_doc)

    if doc_type == "Retinal Screening Report":
        patient["workflow_status"]["document_status"] = "Report Available"
        patient["workflow_status"]["screening_workflow"] = "Completed"
        if not patient["specialist_review"]["completed"]:
            patient["workflow_status"]["overall_stage"] = "Awaiting Specialist Review"
            patient["workflow_status"]["specialist_review"] = "Pending Review"
            patient["workflow_status"]["next_workflow_action"] = "Ophthalmologist review of uploaded fundus report required"

        patient["timeline"].append({
            "id": f"evt-{uuid.uuid4().hex[:6]}",
            "stage": "Report Uploaded",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source": "Document Hub",
            "actor": "Care Coordinator",
            "status": "Completed",
            "note": f"Retinal screening document '{title}' attached to patient record."
        })

        patient["pending_tasks"].append({
            "id": f"tsk-{uuid.uuid4().hex[:6]}",
            "title": "Specialist Ophthalmologist Review",
            "description": f"Ophthalmologist review required for newly uploaded report '{title}'.",
            "assigned_to": "Attending Ophthalmologist",
            "due_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "Open",
            "priority": "High",
            "created_at": datetime.now().strftime("%Y-%m-%d")
        })

    save_data()
    return jsonify({"message": "Document uploaded and indexed", "document": new_doc, "patient": patient}), 201

# API: Human-In-The-Loop Specialist Clinical Review (Manually Entered by Clinician)
@app.post("/api/patients/<patient_id>/review")
def submit_specialist_review(patient_id):
    patient = next((p for p in PATIENTS_STORE if p.get("id") == patient_id), None)
    if not patient:
        return jsonify(error="Patient not found"), 404

    data = request.json or {}
    clinician_name = data.get("clinician_name", "Attending Ophthalmologist").strip()
    clinician_title = data.get("clinician_title", "Dr.").strip()
    clinician_specialty = data.get("clinician_specialty", "Ophthalmology").strip()
    clinician_facility = data.get("clinician_facility", "District Eye Hospital").strip()
    registration_number = data.get("registration_number", "").strip()
    clinical_assessment = data.get("clinical_assessment", "").strip()
    followup_instructions = data.get("followup_instructions", "").strip()
    referral_status = data.get("referral_status", "Routine Follow-Up").strip()
    notes = data.get("notes", "").strip()
    next_followup_date = data.get("next_followup_date", "")

    if not clinical_assessment:
        return jsonify(error="Clinical assessment text must be entered by healthcare professional"), 400

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Update patient review record with clinician provenance
    patient["specialist_review"] = {
        "completed": True,
        "clinician_name": clinician_name,
        "clinician_title": clinician_title,
        "clinician_specialty": clinician_specialty,
        "clinician_facility": clinician_facility,
        "registration_number": registration_number,
        "review_timestamp": now_str,
        "clinical_assessment": clinical_assessment,
        "followup_instructions": followup_instructions,
        "referral_status": referral_status,
        "notes": notes or "Clinical assessment entered manually by qualified healthcare professional."
    }

    # Update workflow state
    patient["workflow_status"]["specialist_review"] = "Completed"
    patient["workflow_status"]["overall_stage"] = "Follow-Up Pending"
    patient["workflow_status"]["followup_status"] = "Pending"
    patient["workflow_status"]["next_workflow_action"] = f"Coordinate follow-up ({referral_status})"
    
    if next_followup_date:
        patient["followup"]["planned_date"] = next_followup_date
        patient["diabetes_profile"]["next_planned_screening"] = next_followup_date

    # Close any open specialist review tasks
    for task in patient.get("pending_tasks", []):
        if "Specialist" in task.get("title", "") and task.get("status") == "Open":
            task["status"] = "Completed"
            task["completed_at"] = now_str

    # Mark document review status
    for doc in patient.get("documents", []):
        if doc.get("doc_type") == "Retinal Screening Report":
            doc["review_status"] = "Reviewed by Specialist"

    # Add timeline event with explicit clinician provenance
    clinician_actor = f"{clinician_name} • {clinician_specialty}" if clinician_specialty else clinician_name
    patient["timeline"].append({
        "id": f"evt-{uuid.uuid4().hex[:6]}",
        "stage": "Specialist Review Completed",
        "timestamp": now_str,
        "source": "Specialist Review Portal",
        "actor": clinician_actor,
        "status": "Completed",
        "note": f"Specialist review recorded by {clinician_name} ({clinician_specialty}, {clinician_facility}). Directive: {referral_status}."
    })

    # AUTOMATED OPERATIONAL TASK CREATION BASED ON CLINICIAN-ENTERED INSTRUCTION
    task_due = next_followup_date or (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    operational_task = {
        "id": f"tsk-{uuid.uuid4().hex[:6]}",
        "title": f"Follow-Up Coordination ({referral_status})",
        "description": f"Coordinate patient follow-up per clinician instructions: {followup_instructions or 'Per clinician management plan'}.",
        "source": f"Clinician Instruction ({clinician_name})",
        "entered_by": clinician_name,
        "clinician_specialty": clinician_specialty,
        "clinician_facility": clinician_facility,
        "assigned_to": "Care Coordinator",
        "due_date": task_due,
        "status": "Open",
        "priority": "High" if ("Hospital" in referral_status or "Clinic" in referral_status or "Urgent" in referral_status) else "Medium",
        "created_at": today_str
    }
    patient.setdefault("pending_tasks", []).append(operational_task)

    save_data()
    return jsonify({
        "message": "Specialist review submitted and operational follow-up task created",
        "specialist_review": patient["specialist_review"],
        "operational_task": operational_task,
        "patient": patient
    })

# API: Workflow Task Management
@app.post("/api/patients/<patient_id>/tasks")
def manage_tasks(patient_id):
    patient = next((p for p in PATIENTS_STORE if p.get("id") == patient_id), None)
    if not patient:
        return jsonify(error="Patient not found"), 404

    data = request.json or {}
    new_task = {
        "id": f"tsk-{uuid.uuid4().hex[:6]}",
        "title": data.get("title", "Workflow Task"),
        "description": data.get("description", ""),
        "assigned_to": data.get("assigned_to", "Care Coordinator"),
        "due_date": data.get("due_date", datetime.now().strftime("%Y-%m-%d")),
        "status": "Open",
        "priority": data.get("priority", "Medium"),
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }
    patient.setdefault("pending_tasks", []).append(new_task)
    save_data()
    return jsonify({"message": "Task created", "task": new_task, "patient": patient}), 201

@app.post("/api/patients/<patient_id>/tasks/<task_id>/complete")
def complete_task(patient_id, task_id):
    patient = next((p for p in PATIENTS_STORE if p.get("id") == patient_id), None)
    if not patient:
        return jsonify(error="Patient not found"), 404

    target_task = next((t for t in patient.get("pending_tasks", []) if t.get("id") == task_id), None)
    if not target_task:
        return jsonify(error="Task not found"), 404

    target_task["status"] = "Completed"
    target_task["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    patient["timeline"].append({
        "id": f"evt-{uuid.uuid4().hex[:6]}",
        "stage": "Task Completed",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "Task Engine",
        "actor": target_task.get("assigned_to", "Staff"),
        "status": "Completed",
        "note": f"Completed task: {target_task.get('title')}"
    })

    save_data()
    return jsonify({"message": "Task marked completed", "task": target_task, "patient": patient})

# API: Follow-Up Status & Care Loop Completion
@app.post("/api/patients/<patient_id>/followup")
def update_followup(patient_id):
    patient = next((p for p in PATIENTS_STORE if p.get("id") == patient_id), None)
    if not patient:
        return jsonify(error="Patient not found"), 404

    data = request.json or {}
    new_status = data.get("status", patient.get("followup", {}).get("status", "Pending"))
    planned_date = data.get("planned_date", patient.get("followup", {}).get("planned_date"))
    staff = data.get("responsible_staff", patient.get("followup", {}).get("responsible_staff", "Care Coordinator"))
    notes = data.get("notes", "")
    new_contact_attempt = data.get("contact_attempt")
    close_loop = data.get("close_care_loop", False)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    patient["followup"]["status"] = new_status
    if planned_date:
        patient["followup"]["planned_date"] = planned_date
        patient["diabetes_profile"]["next_planned_screening"] = planned_date
    if staff:
        patient["followup"]["responsible_staff"] = staff
    if notes:
        patient["followup"]["notes"] = notes

    if new_contact_attempt:
        new_contact_attempt["date"] = datetime.now().strftime("%Y-%m-%d")
        patient["followup"].setdefault("contact_attempts", []).append(new_contact_attempt)
        patient["workflow_status"]["last_contact_date"] = datetime.now().strftime("%Y-%m-%d")
        patient["workflow_status"]["last_contact_method"] = f"{new_contact_attempt.get('method')} ({new_contact_attempt.get('result', '')[:20]})"

    if new_status == "Completed" or close_loop:
        patient["followup"]["status"] = "Completed"
        patient["followup"]["completion_timestamp"] = now_str
        patient["workflow_status"]["care_loop_completed"] = True
        patient["workflow_status"]["overall_stage"] = "Care Loop Completed"
        patient["workflow_status"]["followup_status"] = "Completed"
        patient["workflow_status"]["next_workflow_action"] = "Care cycle completed for 2026"

        for t in patient.get("pending_tasks", []):
            if t.get("status") == "Open":
                t["status"] = "Completed"
                t["completed_at"] = now_str

        patient["timeline"].append({
            "id": f"evt-{uuid.uuid4().hex[:6]}",
            "stage": "Care Loop Completed",
            "timestamp": now_str,
            "source": "Care Loop Engine",
            "actor": staff,
            "status": "Completed",
            "note": f"Diabetic eye care loop successfully completed for this cycle. {notes}"
        })
    else:
        patient["workflow_status"]["followup_status"] = new_status
        if new_status == "Scheduled":
            patient["workflow_status"]["overall_stage"] = "Follow-Up Scheduled"
        elif new_status == "Unable to Contact":
            patient["workflow_status"]["overall_stage"] = "Unable to Contact"
            patient["workflow_status"]["next_workflow_action"] = "Re-engage patient via ASHA worker home visit"

        patient["timeline"].append({
            "id": f"evt-{uuid.uuid4().hex[:6]}",
            "stage": f"Follow-Up Status: {new_status}",
            "timestamp": now_str,
            "source": "Care Coordination Desk",
            "actor": staff,
            "status": "Updated",
            "note": notes or f"Follow-up workflow state updated to {new_status}."
        })

    save_data()
    return jsonify({
        "message": "Follow-up workflow updated",
        "followup": patient["followup"],
        "workflow_status": patient["workflow_status"],
        "patient": patient
    })

# API: Simulated Patient Reminders (English & Hindi)
@app.post("/api/patients/<patient_id>/reminders")
def send_simulated_reminder(patient_id):
    patient = next((p for p in PATIENTS_STORE if p.get("id") == patient_id), None)
    if not patient:
        return jsonify(error="Patient not found"), 404

    data = request.json or {}
    rem_type = data.get("type", "General Follow-Up")
    custom_text = data.get("text")
    custom_text_hi = data.get("text_hi")
    lang = data.get("language", "en")

    name = patient.get("name", "Patient")
    date_str = patient.get("followup", {}).get("planned_date") or patient.get("workflow_status", {}).get("screening_appointment_date") or "your scheduled date"
    facility = patient.get("facility", "your local health centre")

    if rem_type == "Screening Appointment":
        text_en = custom_text or f"Dear {name}, your retinal screening appointment is scheduled for {date_str} at {facility}. Please arrive on time."
        text_hi = custom_text_hi or f"प्रिय {name}, आपकी रेटिनल स्क्रीनिंग {date_str} को {facility} में निर्धारित है। कृपया समय पर पहुंचें।"
    elif rem_type == "Bring Previous Records":
        text_en = custom_text or f"Dear {name}, please remember to bring your previous retinal screening and lab reports to your upcoming appointment."
        text_hi = custom_text_hi or f"प्रिय {name}, कृपया अपने आगामी परामर्श के लिए अपनी पिछली रेटिनल स्क्रीनिंग और लैब रिपोर्ट साथ लाएं।"
    elif rem_type == "Follow-Up Attendance":
        text_en = custom_text or f"Dear {name}, your care team has requested you to attend your scheduled follow-up on {date_str}."
        text_hi = custom_text_hi or f"प्रिय {name}, आपकी केयर टीम ने आपसे {date_str} को फॉलो-अप जांच में उपस्थित होने का अनुरोध किया है।"
    elif rem_type == "Contact Attempt Notice":
        text_en = custom_text or f"Dear {name}, your care team is trying to contact you regarding a scheduled follow-up. Please contact {facility}."
        text_hi = custom_text_hi or f"प्रिय {name}, आपकी देखभाल टीम निर्धारित फॉलो-अप के संबंध में आपसे संपर्क करने का प्रयास कर रही है। कृपया {facility} से संपर्क करें।"
    else:
        text_en = custom_text or f"Dear {name}, this is a reminder from your RetinaX Care team regarding your diabetic eye care."
        text_hi = custom_text_hi or f"प्रिय {name}, यह आपकी डायबिटिक नेत्र देखभाल के संबंध में आपकी रेटिनाएक्स केयर टीम का अनुस्मारक है।"

    reminder_record = {
        "id": f"rem-{uuid.uuid4().hex[:6]}",
        "type": rem_type,
        "language": lang,
        "text": text_en,
        "text_hi": text_hi,
        "sent_status": "Simulated Sent (Demo notification — not actually sent)",
        "scheduled_for": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "channel": "SMS / WhatsApp (Simulated Preview)"
    }

    patient.setdefault("reminders", []).append(reminder_record)
    
    patient["timeline"].append({
        "id": f"evt-{uuid.uuid4().hex[:6]}",
        "stage": "Patient Reminder Sent",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "Communication Engine",
        "actor": "Automated Care Coordinator",
        "status": "Delivered",
        "note": f"Simulated {rem_type} reminder sent ({lang.upper()}). Demo notification — not actually sent."
    })

    save_data()
    return jsonify({
        "message": "Simulated reminder generated and logged successfully",
        "reminder": reminder_record,
        "patient": patient
    })

# API: Record Completeness Checker
@app.get("/api/completeness/<patient_id>")
def check_completeness(patient_id):
    patient = next((p for p in PATIENTS_STORE if p.get("id") == patient_id), None)
    if not patient:
        return jsonify(error="Patient not found"), 404

    comp = calculate_record_completeness(patient)
    return jsonify({
        "patient_id": patient_id,
        "patient_name": patient.get("name"),
        "completeness": comp
    })

# API: Continuity Analytics (Funnel, Bottlenecks, Turnaround & Ownership)
@app.get("/api/analytics")
def get_analytics():
    total = len(PATIENTS_STORE)
    
    # 6-stage drop-off funnel
    stage_registered = total
    stage_scheduled = sum(1 for p in PATIENTS_STORE if p.get("workflow_status", {}).get("screening_workflow") in ["Scheduled", "Completed"])
    stage_screened = sum(1 for p in PATIENTS_STORE if p.get("workflow_status", {}).get("screening_workflow") == "Completed")
    stage_report_available = sum(1 for p in PATIENTS_STORE if any(d.get("doc_type") == "Retinal Screening Report" for d in p.get("documents", [])))
    stage_review_done = sum(1 for p in PATIENTS_STORE if p.get("specialist_review", {}).get("completed", False))
    stage_followup_active = sum(1 for p in PATIENTS_STORE if p.get("followup", {}).get("status") in ["Scheduled", "Completed"] or p.get("workflow_status", {}).get("care_loop_completed"))
    stage_loop_closed = sum(1 for p in PATIENTS_STORE if p.get("workflow_status", {}).get("care_loop_completed", False))

    funnel = [
        {"stage": "1. Patient Registered", "count": stage_registered, "pct": 100, "drop_pct": 0},
        {"stage": "2. Screening Scheduled", "count": stage_scheduled, "pct": round((stage_scheduled / max(1, total)) * 100, 1), "drop_pct": round(((total - stage_scheduled) / max(1, total)) * 100, 1)},
        {"stage": "3. Fundus Scans Acquired", "count": stage_screened, "pct": round((stage_screened / max(1, total)) * 100, 1), "drop_pct": round(((stage_scheduled - stage_screened) / max(1, stage_scheduled or 1)) * 100, 1)},
        {"stage": "4. Report Uploaded & Indexed", "count": stage_report_available, "pct": round((stage_report_available / max(1, total)) * 100, 1), "drop_pct": round(((stage_screened - stage_report_available) / max(1, stage_screened or 1)) * 100, 1)},
        {"stage": "5. Specialist Review Completed", "count": stage_review_done, "pct": round((stage_review_done / max(1, total)) * 100, 1), "drop_pct": round(((stage_report_available - stage_review_done) / max(1, stage_report_available or 1)) * 100, 1)},
        {"stage": "6. Care Loop Closed", "count": stage_loop_closed, "pct": round((stage_loop_closed / max(1, total)) * 100, 1), "drop_pct": round(((stage_review_done - stage_loop_closed) / max(1, stage_review_done or 1)) * 100, 1)}
    ]

    # Bottlenecks analysis
    awaiting_review_count = sum(1 for p in PATIENTS_STORE if not p.get("specialist_review", {}).get("completed") and any(d.get("doc_type") == "Retinal Screening Report" for d in p.get("documents", [])))
    uncontacted_count = sum(1 for p in PATIENTS_STORE if p.get("followup", {}).get("status") == "Unable to Contact" or p.get("workflow_status", {}).get("overall_stage") == "Unable to Contact")
    report_missing_count = sum(1 for p in PATIENTS_STORE if p.get("workflow_status", {}).get("screening_workflow") == "Completed" and not any(d.get("doc_type") == "Retinal Screening Report" for d in p.get("documents", [])))

    bottlenecks = [
        {
            "category": "Specialist Review Backlog",
            "count": awaiting_review_count,
            "status": "Warning" if awaiting_review_count > 0 else "Optimal",
            "impact": "Uploaded fundus reports awaiting clinician assessment and follow-up plan.",
            "primary_owner": "Attending Ophthalmologist",
            "median_days_waiting": 3.5
        },
        {
            "category": "Unable to Contact / At Risk of Drop-off",
            "count": uncontacted_count,
            "status": "Critical" if uncontacted_count > 0 else "Optimal",
            "impact": "Multiple failed telephone contact attempts. Requires field ASHA home visit.",
            "primary_owner": "Community Health / ASHA Outreach",
            "median_days_waiting": 8.0
        },
        {
            "category": "External Report Reconciliation",
            "count": report_missing_count,
            "status": "Notice" if report_missing_count > 0 else "Optimal",
            "impact": "Screening completed at mobile camp; digital report awaiting hospital EMR indexing.",
            "primary_owner": "Care Coordinator / Health Informatics",
            "median_days_waiting": 4.2
        }
    ]

    # Team Ownership Workload Breakdown
    ownership = {
        "Care Coordinator": sum(1 for p in PATIENTS_STORE if "Coordinator" in p.get("workflow_status", {}).get("assigned_to", "Care Coordinator")),
        "Attending Ophthalmologist": sum(1 for p in PATIENTS_STORE if "Ophthalmologist" in p.get("workflow_status", {}).get("assigned_to", "") or (any(d.get("doc_type") == "Retinal Screening Report" for d in p.get("documents", [])) and not p.get("specialist_review", {}).get("completed"))),
        "Community Outreach / ASHA": sum(1 for p in PATIENTS_STORE if "ASHA" in p.get("workflow_status", {}).get("assigned_to", "") or p.get("followup", {}).get("status") == "Unable to Contact"),
        "Primary Physician": sum(1 for p in PATIENTS_STORE if "Physician" in p.get("workflow_status", {}).get("assigned_to", ""))
    }

    # Turnaround Benchmarks (Simulated operational statistics)
    turnaround = {
        "avg_days_registration_to_screening": 5.4,
        "avg_days_screening_to_report": 1.8,
        "avg_days_report_to_specialist_review": 3.2,
        "avg_days_review_to_followup_closure": 11.5,
        "care_loop_resolution_rate_pct": round((stage_loop_closed / max(1, total)) * 100, 1),
        "overall_contact_success_rate_pct": 82.5
    }

    return jsonify({
        "total_cohort": total,
        "funnel": funnel,
        "bottlenecks": bottlenecks,
        "ownership": ownership,
        "turnaround": turnaround
    })

# API: Care Gap Radar (Patients requiring workflow attention)
@app.get("/api/gap-radar")
def get_gap_radar():
    radar_items = []
    
    for p in PATIENTS_STORE:
        p_id = p.get("id")
        name = p.get("name")
        stage = p.get("workflow_status", {}).get("overall_stage")
        wf_screen = p.get("workflow_status", {}).get("screening_workflow")
        has_report = any(d.get("doc_type") == "Retinal Screening Report" for d in p.get("documents", []))
        spec_rev = p.get("specialist_review", {}).get("completed", False)
        f_status = p.get("followup", {}).get("status")
        loop_done = p.get("workflow_status", {}).get("care_loop_completed", False)
        owner = p.get("workflow_status", {}).get("assigned_to", "Care Coordinator")
        due = p.get("workflow_status", {}).get("due_date", "Today")

        gap_type = None
        urgency = "Medium"
        description = ""
        action = ""

        if loop_done:
            continue
        elif f_status == "Unable to Contact" or stage == "Unable to Contact":
            gap_type = "Patient Unreachable (Drop-off Risk)"
            urgency = "High"
            description = f"Patient reached maximum phone contact attempts. Requires physical home visit verification."
            action = "Dispatch ASHA worker for community re-engagement"
            owner = "Community Outreach / ASHA"
        elif wf_screen == "Completed" and not has_report:
            gap_type = "Report Reconciliation Exception"
            urgency = "Medium"
            description = f"Fundus photography completed at camp. Screening report not yet reconciled or uploaded."
            action = "Retrieve and index mobile camp report into hub"
            owner = "Care Coordinator"
        elif has_report and not spec_rev:
            gap_type = "Specialist Review Pending"
            urgency = "High"
            description = f"Retinal report available on disk. Specialist ophthalmologist clinical review pending."
            action = "Submit ophthalmologist clinical assessment and follow-up plan"
            owner = "Attending Ophthalmologist"
        elif f_status == "Pending" and spec_rev:
            gap_type = "Clinician Follow-Up Pending"
            urgency = "Medium"
            description = f"Specialist instructed follow-up. Patient appointment or revisit coordination pending."
            action = "Confirm follow-up attendance date with patient"
            owner = "Care Coordinator"
        elif wf_screen == "Not Started":
            gap_type = "Screening Unscheduled"
            urgency = "Low"
            description = f"Newly registered diabetic patient without baseline screening schedule."
            action = "Book retinal screening slot at local clinic/camp"
            owner = "Care Coordinator"

        if gap_type:
            radar_items.append({
                "patient_id": p_id,
                "patient_name": name,
                "gap_type": gap_type,
                "urgency": urgency,
                "description": description,
                "recommended_action": action,
                "assigned_owner": owner,
                "due_date": due,
                "facility": p.get("facility", "Primary Health Centre")
            })

    # Sort High urgency first
    urgency_map = {"High": 1, "Medium": 2, "Low": 3}
    radar_items.sort(key=lambda x: urgency_map.get(x["urgency"], 4))

    return jsonify({
        "total_gaps": len(radar_items),
        "gap_items": radar_items
    })

# API: Categorized Follow-Up Command Center
@app.get("/api/followups")
def get_followups():
    due_today = []
    upcoming = []
    overdue = []
    unable_to_contact = []
    completed = []

    today_date = datetime.now().date()

    for p in PATIENTS_STORE:
        p_info = {
            "id": p.get("id"),
            "name": p.get("name"),
            "age": p.get("age"),
            "sex": p.get("sex"),
            "contact": p.get("contact"),
            "facility": p.get("facility"),
            "status": p.get("followup", {}).get("status", "Pending"),
            "planned_date": p.get("followup", {}).get("planned_date") or p.get("diabetes_profile", {}).get("next_planned_screening") or "Not scheduled",
            "responsible_staff": p.get("followup", {}).get("responsible_staff", "Care Coordinator"),
            "contact_attempts_count": len(p.get("followup", {}).get("contact_attempts", [])),
            "care_loop_completed": p.get("workflow_status", {}).get("care_loop_completed", False),
            "referral_status": p.get("specialist_review", {}).get("referral_status", "Routine"),
            "notes": p.get("followup", {}).get("notes", "")
        }

        if p_info["care_loop_completed"] or p_info["status"] == "Completed":
            completed.append(p_info)
        elif p_info["status"] == "Unable to Contact":
            unable_to_contact.append(p_info)
        else:
            # Check date status
            planned_str = p.get("followup", {}).get("planned_date")
            if not planned_str:
                upcoming.append(p_info)
            else:
                try:
                    p_date = datetime.strptime(planned_str, "%Y-%m-%d").date()
                    if p_date < today_date:
                        overdue.append(p_info)
                    elif p_date == today_date:
                        due_today.append(p_info)
                    else:
                        upcoming.append(p_info)
                except Exception:
                    upcoming.append(p_info)

    return jsonify({
        "counts": {
            "due_today": len(due_today),
            "upcoming": len(upcoming),
            "overdue": len(overdue),
            "unable_to_contact": len(unable_to_contact),
            "completed": len(completed)
        },
        "due_today": due_today,
        "upcoming": upcoming,
        "overdue": overdue,
        "unable_to_contact": unable_to_contact,
        "completed": completed
    })

# API: Record Reconciliation Exceptions
@app.get("/api/reconciliation")
def get_reconciliation_items():
    exceptions = []
    for p in PATIENTS_STORE:
        has_report = any(d.get("doc_type") == "Retinal Screening Report" for d in p.get("documents", []))
        wf_screen = p.get("workflow_status", {}).get("screening_workflow")
        if wf_screen == "Completed" and not has_report:
            exceptions.append({
                "patient_id": p.get("id"),
                "patient_name": p.get("name"),
                "facility": p.get("facility"),
                "screening_date": p.get("timeline", [{}])[0].get("timestamp", "Recent"),
                "exception_reason": "Mobile camp screening completed but report PDF not linked to patient record.",
                "action_needed": "Attach / Link external retinal screening report"
            })
    return jsonify({
        "total_exceptions": len(exceptions),
        "exceptions": exceptions
    })

@app.post("/api/reconciliation/<patient_id>/resolve")
def resolve_reconciliation(patient_id):
    patient = next((p for p in PATIENTS_STORE if p.get("id") == patient_id), None)
    if not patient:
        return jsonify(error="Patient not found"), 404

    data = request.json or {}
    report_title = data.get("title", f"Reconciled Retinal Screening Report - {patient_id}")
    source = data.get("source", "Reconciled Mobile Camp EMR")

    doc = {
        "id": f"doc-{uuid.uuid4().hex[:6]}",
        "title": report_title,
        "doc_type": "Retinal Screening Report",
        "upload_date": datetime.now().strftime("%Y-%m-%d"),
        "source": source,
        "review_status": "Awaiting Specialist Review",
        "file_name": f"report_{patient_id}_reconciled.pdf",
        "size_kb": 420.0
    }
    patient["documents"].append(doc)
    patient["workflow_status"]["document_status"] = "Report Available"
    patient["workflow_status"]["overall_stage"] = "Awaiting Specialist Review"
    patient["workflow_status"]["specialist_review"] = "Pending Review"
    patient["workflow_status"]["next_workflow_action"] = "Specialist review required for newly reconciled report"

    patient["timeline"].append({
        "id": f"evt-{uuid.uuid4().hex[:6]}",
        "stage": "Record Reconciled",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "Record Reconciliation Desk",
        "actor": "Care Coordinator",
        "status": "Completed",
        "note": f"External retinal screening report successfully reconciled and linked from {source}."
    })

    save_data()
    return jsonify({"message": "Record reconciled successfully", "patient": patient, "document": doc})

# API: Notifications Feed
@app.get("/api/notifications")
def get_notifications():
    notifications = []
    
    # Check for unreviewed reports
    unreviewed = [p for p in PATIENTS_STORE if any(d.get("doc_type") == "Retinal Screening Report" for d in p.get("documents", [])) and not p.get("specialist_review", {}).get("completed")]
    for p in unreviewed:
        notifications.append({
            "id": f"notif-{p['id']}-rev",
            "patient_id": p['id'],
            "patient_name": p['name'],
            "type": "Specialist Review Required",
            "level": "warning",
            "message": f"Fundus report for {p['name']} ({p['id']}) is awaiting specialist ophthalmologist review.",
            "timestamp": "Today"
        })

    # Check for unable to contact
    uncontacted = [p for p in PATIENTS_STORE if p.get("followup", {}).get("status") == "Unable to Contact"]
    for p in uncontacted:
        notifications.append({
            "id": f"notif-{p['id']}-contact",
            "patient_id": p['id'],
            "patient_name": p['name'],
            "type": "Patient Unreachable",
            "level": "critical",
            "message": f"{p['name']} ({p['id']}) unreachable after multiple contact attempts. ASHA home visit escalation required.",
            "timestamp": "Today"
        })

    # Check for missing reports
    missing = [p for p in PATIENTS_STORE if p.get("workflow_status", {}).get("screening_workflow") == "Completed" and not any(d.get("doc_type") == "Retinal Screening Report" for d in p.get("documents", []))]
    for p in missing:
        notifications.append({
            "id": f"notif-{p['id']}-miss",
            "patient_id": p['id'],
            "patient_name": p['name'],
            "type": "Report Reconciliation",
            "level": "info",
            "message": f"Screening completed for {p['name']} ({p['id']}). Mobile camp report requires reconciliation.",
            "timestamp": "Recent"
        })

    return jsonify({
        "count": len(notifications),
        "notifications": notifications
    })

# API: Reset Synthetic Data for Demo Runs
@app.post("/api/patients/reset")
def reset_data():
    load_initial_data(from_seed=True)
    return jsonify({
        "message": "Synthetic demo dataset reloaded to initial state",
        "total_patients": len(PATIENTS_STORE)
    })

if __name__ == "__main__":
    logger.info("Starting RetinaX Care Platform (Enterprise Care Continuity Edition)...")
    logger.info("Operating Mode: Non-diagnostic Care Coordination & Follow-up Tracking.")
    logger.info("Listening on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
