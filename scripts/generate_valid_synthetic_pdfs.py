"""
Generate valid synthetic binary PDFs for RetinaX Care demonstration documents.
Replaces text-disguised .pdf files with standard %PDF-1.4 binary files
while preserving all original clinical narrative and synthetic metadata.
"""

from pathlib import Path
import hashlib

ROOT_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = ROOT_DIR / "uploads"
BACKUP_UPLOADS = Path(r"C:\Users\sijar\Downloads\RetinaX_Healthathon_BACKUP_PHASE0\uploads")

DOC_METADATA = {
    "fundus_khader_oct26.pdf": {
        "title": "Retinal Fundus Photography Report",
        "patient": "Syed Abdul Khader (RX-1012)",
        "facility": "Padarayanapura Urban Primary Health Centre",
        "date": "2026-10-02",
        "content": [
            "Clinical Record: Retinal Fundus Screening Photography",
            "Screening Modality: Non-mydriatic Bilateral 45-degree Fundus Camera",
            "Acquisition Status: Bilateral macula- and disc-centered fields captured",
            "Image Quality: Adequate for specialist telemedicine review",
            "Care Continuity Status: Awaiting Specialist Review",
            "Operational Next Step: Queue for District Eye Hospital review"
        ]
    },
    "lab_summary_rx1001.pdf": {
        "title": "Baseline Laboratory Summary",
        "patient": "Ramesh Kumar (RX-1001)",
        "facility": "Primary Health Centre - Ramanagara",
        "date": "2026-08-14",
        "content": [
            "Laboratory Investigation Record - Diabetic Profile",
            "HbA1c: 8.4% (Standardized HPLC)",
            "Fasting Blood Glucose: 162 mg/dL",
            "Post-Prandial Blood Glucose: 234 mg/dL",
            "Serum Creatinine: 1.0 mg/dL",
            "Note: Glycemic index documented for care-coordination scheduling only.",
            "Operational Care Status: Annual retinal screening completed; follow-up scheduled."
        ]
    },
    "referral_babulal.pdf": {
        "title": "Specialist Consultation & Hospital Referral Sheet",
        "patient": "Babu Lal Patel (RX-1008)",
        "facility": "Primary Health Centre - Nelamangala",
        "date": "2026-09-12",
        "content": [
            "Operational Directives: Hospital Eye Clinic Referral",
            "Attributed Specialist: Dr. Jayashree Nayak, MS (Ophthalmology)",
            "Referral Destination: District Hospital Retina Clinic (Scheduled: Oct 20, 2026)",
            "Transport / Coordinator Note: Patient requires family escort for dilation.",
            "Care Coordinator Action: Verify hospital appointment reminder delivery."
        ]
    },
    "retinal_babulal.pdf": {
        "title": "Screening Images & Technical Dossier",
        "patient": "Babu Lal Patel (RX-1008)",
        "facility": "Primary Health Centre - Nelamangala",
        "date": "2026-09-12",
        "content": [
            "Technical Screening Record: 2-field color fundus images",
            "Image Files: Left Eye (Macula), Right Eye (Disc/Macula)",
            "Acquisition Technician: ASHA Lead Coordinator Rekha",
            "Specialist Directive: Forwarded to District Hospital Retina Clinic."
        ]
    },
    "retinal_kavitha_sep26.pdf": {
        "title": "Retinal Screening Photography Dossier",
        "patient": "Kavitha Sundaram (RX-1004)",
        "facility": "Taluk Hospital - Channapatna",
        "date": "2026-09-22",
        "content": [
            "Retinal Screening Report & Tele-Ophthalmology Intake",
            "Bilateral digital retinal photography completed at Taluk unit.",
            "Status: Images transmitted to specialist review queue.",
            "Care Continuity: Specialist review logged by Dr. Manjunath Shenoy."
        ]
    },
    "retinal_manjula_sep26.pdf": {
        "title": "Multi-Record Screening Photography Dossier",
        "patient": "Manjula Shankaran (RX-1011)",
        "facility": "Anekal Eye Unit",
        "date": "2026-09-29",
        "content": [
            "Screening Photography Dossier (Bilateral Photos)",
            "Baseline comparison dataset from 2024 included in archive.",
            "Status: Awaiting Specialist Review",
            "Care Coordinator: Rajesh V (4 records organized for specialist queue)."
        ]
    },
    "retinal_report_farooq_oct26.pdf": {
        "title": "Fundus Screening Operational Report",
        "patient": "Mohammad Farooq (RX-1003)",
        "facility": "Padarayanapura UPHC",
        "date": "2026-10-01",
        "content": [
            "Screening Report - Tele-Retina Mobile Unit",
            "Optometrist: Deepa, B.Optom",
            "Field Coverage: Bilateral 45-degree color fundus images acquired.",
            "Workflow Status: Screening completed, uploaded to specialist review queue.",
            "Operational Priority: High (Overdue review queue tracking)."
        ]
    },
    "screening_gurpreet_2026.pdf": {
        "title": "Annual Retinal Screening Completion Certificate",
        "patient": "Gurpreet Singh (RX-1005)",
        "facility": "Community Health Centre - Magadi",
        "date": "2026-09-18",
        "content": [
            "Annual Screening Cycle Report (2026 Cycle)",
            "Reviewing Ophthalmologist: Dr. Rashmi Desai, DO, DNB",
            "Clinician Attributed Note: Normal bilateral retinal findings documented.",
            "Care Continuity Status: Care Loop Successfully Closed for 2026.",
            "Next Planned Operational Action: Schedule 2027 annual routine screening."
        ]
    },
    "specialist_note_kavitha.pdf": {
        "title": "Specialist Consultation & Follow-Up Directive Note",
        "patient": "Kavitha Sundaram (RX-1004)",
        "facility": "District Eye Hospital Tele-Ophthalmology Center",
        "date": "2026-09-25",
        "content": [
            "Specialist Clinical Note (Attributed to Qualified Clinician)",
            "Reviewer: Dr. Manjunath Shenoy, MS (Ophthalmology, Registration: KMC-48192)",
            "Clinical Assessment: Clinically visible microvascular changes noted in right eye.",
            "Follow-up Instructions: Hospital follow-up visit scheduled in 6 months.",
            "Care Coordinator Action: Confirm patient acknowledgement and appointment attendance."
        ]
    }
}

def build_pdf_stream(title: str, patient: str, facility: str, date: str, content_lines: list) -> bytes:
    # A4 dimensions: 595 x 842 pt
    stream_lines = []
    
    # Title & Subtitle
    stream_lines.append("BT /F1 16 Tf 50 780 Td (RETINAX CARE - OPERATIONAL CARE CONTINUITY) Tj ET")
    stream_lines.append("BT /F2 10 Tf 50 762 Td (Closing the Loop in Diabetic Eye Care | Health-a-thon 2026) Tj ET")
    
    # Horizontal divider rule
    # Metadata Box
    stream_lines.append(f"BT /F1 12 Tf 50 725 Td ({title}) Tj ET")
    stream_lines.append(f"BT /F2 10 Tf 50 705 Td (Patient: {patient}) Tj ET")
    stream_lines.append(f"BT /F2 10 Tf 50 688 Td (Facility: {facility}) Tj ET")
    stream_lines.append(f"BT /F2 10 Tf 50 671 Td (Date: {date}    |    Verification: Document Verified) Tj ET")
    
    # Section Header
    stream_lines.append("BT /F1 11 Tf 50 635 Td (OPERATIONAL DOSSIER & RECORD DETAILS) Tj ET")
    
    y = 610
    for line in content_lines:
        safe_line = line.replace("(", r"\(").replace(")", r"\)")
        stream_lines.append(f"BT /F2 10 Tf 60 {y} Td ({safe_line}) Tj ET")
        y -= 22

    # Disclaimer Footer
    stream_lines.append("BT /F2 8 Tf 50 85 Td (DISCLAIMER: RetinaX Care supports operational care coordination and continuity tracking.) Tj ET")
    stream_lines.append("BT /F2 8 Tf 50 72 Td (It does not provide diagnosis, disease grading (DR 0-4), treatment recommendations, or autonomous CDS.) Tj ET")
    stream_lines.append("BT /F2 8 Tf 50 59 Td (All clinical interpretations and management decisions remain with qualified healthcare professionals.) Tj ET")
    stream_lines.append("BT /F2 8 Tf 50 46 Td (Synthetic demonstration record generated strictly for Health-a-thon 2026 evaluation.) Tj ET")

    stream_content = "\n".join(stream_lines) + "\n"
    stream_bytes = stream_content.encode("latin1")

    # PDF Object Catalog
    objs = []
    # 1: Catalog
    objs.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    # 2: Pages
    objs.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    # 3: Page
    objs.append(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>\nendobj\n")
    # 4: Stream
    objs.append(f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin1") + stream_bytes + b"\nendstream\nendobj\n")
    # 5: Bold Font
    objs.append(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n")
    # 6: Regular Font
    objs.append(b"6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    body = b""
    offsets = [len(header)]
    for obj in objs:
        body += obj
        offsets.append(len(header) + len(body))

    xref_offset = len(header) + len(body)
    xref = f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n"
    for off in offsets[:-1]:
        xref += f"{off:010d} 00000 n \n"
    trailer = f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
    
    return header + body + xref.encode("latin1") + trailer.encode("latin1")

def main():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    for filename, meta in DOC_METADATA.items():
        pdf_bytes = build_pdf_stream(
            title=meta["title"],
            patient=meta["patient"],
            facility=meta["facility"],
            date=meta["date"],
            content_lines=meta["content"]
        )
        dest_file = UPLOADS_DIR / filename
        dest_file.write_bytes(pdf_bytes)
        sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        print(f"Generated valid PDF: {filename:32} ({len(pdf_bytes)} bytes) SHA256: {sha256[:12]}...")

if __name__ == "__main__":
    main()
