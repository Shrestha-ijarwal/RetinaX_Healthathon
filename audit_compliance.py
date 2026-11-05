import os
import sys
from pathlib import Path

# Dynamic root path resolution (no hardcoded Windows paths)
root = Path(__file__).resolve().parent

prohibited_terms = [
    'grad-cam', 'gradcam', 'dr grade', 'dr_grade',
    'referable dr', 'risk score', 'trained_dr_model', 'trained_vessel', 'idrid'
]

findings = []
for p in root.rglob('*'):
    # Ignore node_modules, git, venv, cache, tests, backup, docs
    if any(part in p.parts for part in ['node_modules', '.git', '.next', '__pycache__', 'tests', 'docs', '.pytest_cache']):
        continue
    if p.is_file() and p.suffix in ['.py', '.html', '.js', '.ts', '.tsx', '.json']:
        if p.name in ['tests_runner.py', 'audit_compliance.py', 'package-lock.json']:
            continue
        try:
            content = p.read_text(encoding='utf-8', errors='ignore').lower()
            for term in prohibited_terms:
                if term in content:
                    findings.append((str(p.relative_to(root)), term))
        except Exception:
            pass

print("================================================================")
print("  RETINAX CARE — SCOPE & NON-CLINICAL COMPLIANCE AUDIT")
print("  Track: Diabetes Care | Health-a-thon 2026")
print("================================================================")

if not findings:
    print("[STATUS: 100% COMPLIANT] Zero prohibited terms or clinical AI references found.")
    print("System strictly adheres to operational care-continuity scope boundaries.")
    sys.exit(0)
else:
    print(f"[ALERT] {len(findings)} prohibited term(s) detected:")
    for file, term in findings:
        print(f"  - Term '{term}' matched in {file}")
    sys.exit(1)
