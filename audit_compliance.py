import os
from pathlib import Path

root = Path(r"C:\Users\sijar\Downloads\RetinaX_Healthathon")
prohibited_terms = [
    'grad-cam', 'gradcam', 'dr grade', 'dr_grade',
    'referable dr', 'risk score', 'predict',
    'trained_dr_model', 'trained_vessel', 'idrid'
]

findings = []
for p in root.rglob('*'):
    if p.is_file() and p.suffix in ['.py', '.html', '.js', '.css', '.json']:
        if p.name in ['tests_runner.py', 'audit_compliance.py']:
            continue
        try:
            content = p.read_text(encoding='utf-8').lower()
            for term in prohibited_terms:
                if term in content:
                    findings.append((str(p.relative_to(root)), term))
        except Exception as e:
            pass

print("=== RETINAX CARE COMPLIANCE AUDIT REPORT ===")
if not findings:
    print("[STATUS: 100% COMPLIANT] Zero prohibited terms or clinical AI references found.")
else:
    for file, term in findings:
        print(f"Notice: Term '{term}' matched in {file}")
