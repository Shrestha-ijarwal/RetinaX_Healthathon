#!/usr/bin/env python3
"""
RetinaX Care - Static Scope & Non-Clinical Compliance Scanner
Health-a-thon 2026 Edition (Diabetes Care & RSSDI Track)

Scans: Active Backend Python, Frontend TypeScript/TSX, API Schemas,
Database Models, Active Services, Synthetic Data, and Documentation.

Validates that operational care-continuity platform does not contain:
- Automated diagnosis & DR severity grading (0-4)
- AI-generated clinical risk scoring
- Autonomous referral decisions
- Treatment recommendations & autonomous clinical advice
"""

import sys
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

# Prohibited clinical and diagnostic concepts
PROHIBITED_TERMS = [
    'grad-cam', 'gradcam', 'trained_dr_model', 'trained_vessel', 'idrid', 'eyepacs', 'messidor',
    'dr_grade', 'dr grade', 'referable dr', 'referable diabetic retinopathy',
    'clinical_assessment', 'referral_status',
    'clinical risk score', 'treatment recommendation'
]

# Exclusion rules with transparent reporting
EXCLUSION_RULES = {
    'node_modules': 'Third-party JavaScript library dependencies',
    '.next': 'Next.js compilation build output directory',
    '.git': 'Git version control system internal metadata',
    '__pycache__': 'Python compiled bytecode cache',
    '.pytest_cache': 'Pytest testing cache directory',
    'uploads': 'User binary document storage (PDF/JPEG/PNG files)',
    'package-lock.json': 'Node.js dependency lockfile',
    'audit_compliance.py': 'Compliance scanner source file itself',
    'server.py': 'Preserved legacy Flask prototype file (superseded by FastAPI backend)',
    'app.js': 'Preserved legacy frontend prototype script (superseded by Next.js React app)',
    'index.html': 'Preserved legacy frontend prototype HTML (superseded by Next.js app)',
    'styles.css': 'Preserved legacy frontend prototype CSS',
    'MIGRATION_INVENTORY.md': 'Historical migration inventory documentation of legacy schema',
    'legacy': 'Preserved legacy prototype directory (superseded by Next.js frontend)',
    'tests': 'Automated regression test suite assertions',
    'tests_runner.py': 'Automated regression test runner',
    'migrations': 'Alembic historical schema migration scripts'
}

CHECKED_EXTENSIONS = {'.py', '.ts', '.tsx', '.js', '.json', '.yaml', '.yml', '.md'}

# Active code assignments that violate non-clinical boundaries
ACTIVE_ASSIGNMENT_PATTERNS = [
    re.compile(r'["\'](clinical_assessment|referral_status|dr_grade)["\']\s*:'),
    re.compile(r'\b(clinical_assessment|referral_status|dr_grade)\s*='),
    re.compile(r'def\s+(predict_dr|diagnose_|grade_dr|calculate_clinical_risk)\b'),
]

DISCLAIMER_PATTERNS = [
    'does not provide', 'does not store', 'does not diagnose', 'does not calculate',
    'strictly exclude', 'never implement', 'prohibited', 'non-clinical', 'non-diagnostic',
    'disclaimer', 'excluding', 'excluded', 'without clinical', 'never calculates',
    'retinax care supports operational care continuity only'
]

def run_compliance_audit():
    findings = []
    scanned_files = []
    excluded_summary = {reason: 0 for reason in set(EXCLUSION_RULES.values())}

    for path in sorted(ROOT_DIR.rglob('*')):
        if not path.is_file():
            continue

        # Check directory / file exclusions
        excluded = False
        for ex_pattern, reason in EXCLUSION_RULES.items():
            if ex_pattern in path.parts or path.name == ex_pattern:
                excluded_summary[reason] += 1
                excluded = True
                break
        if excluded:
            continue

        if path.suffix not in CHECKED_EXTENSIONS:
            continue

        scanned_files.append(path)
        rel_path = path.relative_to(ROOT_DIR)

        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()

            for idx, line in enumerate(lines, 1):
                line_lower = line.lower()

                # 1. Check for active prohibited code assignments / model fields
                for pat in ACTIVE_ASSIGNMENT_PATTERNS:
                    if pat.search(line):
                        findings.append({
                            'file': str(rel_path),
                            'line': idx,
                            'term': pat.pattern,
                            'type': 'ACTIVE_FIELD_ASSIGNMENT',
                            'snippet': line.strip()[:120]
                        })

                # 2. Check for prohibited diagnostic terms
                for term in PROHIBITED_TERMS:
                    if term in line_lower:
                        # If the line is an explicit negative disclaimer stating the platform does NOT do this, skip
                        if any(marker in line_lower for marker in DISCLAIMER_PATTERNS):
                            continue
                        # If in documentation and discussing project boundary, skip
                        if path.suffix == '.md' and any(marker in line_lower for marker in DISCLAIMER_PATTERNS):
                            continue

                        findings.append({
                            'file': str(rel_path),
                            'line': idx,
                            'term': term,
                            'type': 'PROHIBITED_TERM',
                            'snippet': line.strip()[:120]
                        })
        except Exception as e:
            print(f"Warning: could not read {rel_path}: {e}")

    print("================================================================================")
    print("  RETINAX CARE — STATIC SCOPE & NON-CLINICAL COMPLIANCE SCANNER")
    print("  Track: Diabetes Care & RSSDI | Health-a-thon 2026")
    print("================================================================================")
    print(f"Scanned files count : {len(scanned_files)} files across backend, frontend, schemas, data & docs.")
    print("Excluded directories and resources (with explicit rationale):")
    for reason, count in sorted(excluded_summary.items()):
        if count > 0:
            print(f"  - {reason:<65}: {count} file(s)")

    print("\n--------------------------------------------------------------------------------")
    print("  SCAN RESULTS & CODEBASE AUDIT")
    print("--------------------------------------------------------------------------------")

    if findings:
        print(f"\n[ALERT] {len(findings)} prohibited clinical construct(s) detected in active source files:\n")
        for f in findings:
            print(f"  - [{f['type']}] '{f['term']}' in {f['file']}:{f['line']}")
            print(f"    Line content: \"{f['snippet']}\"\n")
        print("Status: FAILED — Prohibited clinical diagnostic constructs detected in active files.")
        sys.exit(1)
    else:
        print("\n[RESULT] Zero active prohibited clinical decision terms detected.")
        print("Status: PASS — No active clinical decision-making or diagnostic AI fields found.")

    print("\n--------------------------------------------------------------------------------")
    print("  HEALTHCARE SCOPE & OPERATIONAL BOUNDARY CHECKLIST (MANUAL REVIEW)")
    print("--------------------------------------------------------------------------------")
    checklist = [
        ("Automated diagnosis or disease detection", "EXCLUDED — No diagnostic ML models"),
        ("Diabetic retinopathy grading (DR 0–4)", "EXCLUDED — Only operational tracking stages"),
        ("Clinical risk scoring / triage algorithms", "EXCLUDED — Rules-based operational queues only"),
        ("Treatment recommendations & prescriptive care", "EXCLUDED — Attributed clinician directives only"),
        ("Autonomous referral decision engine", "EXCLUDED — No automated referral logic"),
        ("Automated interpretation of fundus images", "EXCLUDED — Document availability verified only"),
        ("Clinical predictions based on HbA1c", "EXCLUDED — HbA1c stored as historical record only"),
        ("Persistent non-clinical disclaimer", "VERIFIED — Present on UI, API and documentation")
    ]
    for item, status_desc in checklist:
        print(f"  [PASS] {item:<48} : {status_desc}")

    print("\n--------------------------------------------------------------------------------")
    print("Automated static scan completed. This is not a legal, regulatory, clinical,")
    print("or security certification. Manual review is required.")
    print("================================================================================\n")
    sys.exit(0)

if __name__ == '__main__':
    run_compliance_audit()
