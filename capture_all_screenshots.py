import os
import sys
import time
import subprocess
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
SCREENSHOTS_DIR = ROOT / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACTS_DIR = Path(r"C:\Users\sijar\.gemini\antigravity\brain\ba2c2860-f3b9-4de7-a183-b84a8dc3d691")

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_EXE):
    CHROME_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

VIEWS = [
    {
        "name": "01_care_journeys_directory_desktop.png",
        "url": "http://localhost:5000/?skip_welcome=1&screen=screen-journeys",
        "size": "1440,900",
        "desc": "Care Journeys directory (desktop)"
    },
    {
        "name": "02_care_journeys_directory_needs_attention.png",
        "url": "http://localhost:5000/?skip_welcome=1&screen=screen-journeys&filter=needs_attention",
        "size": "1440,900",
        "desc": "Care Journeys directory filtered by Attention Needed"
    },
    {
        "name": "03_care_journeys_directory_mobile.png",
        "url": "http://localhost:5000/?skip_welcome=1&screen=screen-journeys",
        "size": "390,844",
        "desc": "Care Journeys directory on mobile"
    },
    {
        "name": "04_care_journey_workspace_rajesh_kumar.png",
        "url": "http://localhost:5000/?skip_welcome=1&screen=screen-journeys&patient=RX-1001",
        "size": "1440,900",
        "desc": "Care Journey twin workspace for Rajesh Kumar"
    },
    {
        "name": "05_care_journey_workspace_completed_sunita.png",
        "url": "http://localhost:5000/?skip_welcome=1&screen=screen-journeys&patient=RX-1005",
        "size": "1440,900",
        "desc": "Care Journey twin workspace for completed patient (Sunita Verma)"
    },
    {
        "name": "06_care_journey_node_inspection_open.png",
        "url": "http://localhost:5000/?skip_welcome=1&screen=screen-journeys&patient=RX-1001&node=4",
        "size": "1440,900",
        "desc": "Care Journey node inspection panel open (Step 5: Specialist Review)"
    },
    {
        "name": "07_specialist_reviews_queue_desktop.png",
        "url": "http://localhost:5000/?skip_welcome=1&screen=screen-reviews",
        "size": "1440,900",
        "desc": "Specialist Reviews queue (desktop)"
    },
    {
        "name": "08_specialist_reviews_queue_reconciliation.png",
        "url": "http://localhost:5000/?skip_welcome=1&screen=screen-reviews&filter=reconciliation",
        "size": "1440,900",
        "desc": "Specialist Reviews queue filtered by Record Reconciliation Required"
    },
    {
        "name": "09_specialist_reviews_queue_mobile.png",
        "url": "http://localhost:5000/?skip_welcome=1&screen=screen-reviews",
        "size": "390,844",
        "desc": "Specialist Reviews queue on mobile"
    },
    {
        "name": "10_specialist_review_workspace_rajesh_desktop.png",
        "url": "http://localhost:5000/?skip_welcome=1&screen=screen-reviews&patient=RX-1001&role=specialist",
        "size": "1440,900",
        "desc": "Specialist Review workspace for Rajesh Kumar (Specialist Authoring Mode)"
    },
    {
        "name": "11_specialist_review_workspace_restricted_role.png",
        "url": "http://localhost:5000/?skip_welcome=1&screen=screen-reviews&patient=RX-1001&role=coordinator",
        "size": "1440,900",
        "desc": "Specialist Review workspace when non-specialist role active (Role restriction banner)"
    },
    {
        "name": "12_specialist_review_workspace_recorded_state.png",
        "url": "http://localhost:5000/?skip_welcome=1&screen=screen-reviews&patient=RX-1005",
        "size": "1440,900",
        "desc": "Specialist Review workspace with Recorded Review state (Provenance chain)"
    },
    {
        "name": "13_specialist_review_submission_success.png",
        "url": "http://localhost:5000/?skip_welcome=1&screen=screen-reviews&patient=RX-1001&role=specialist&submitted=1",
        "size": "1440,900",
        "desc": "Successful review submission banner + auto-created follow-up task notice"
    },
    {
        "name": "14_care_journey_updated_after_review.png",
        "url": "http://localhost:5000/?skip_welcome=1&screen=screen-journeys&patient=RX-1005&node=4",
        "size": "1440,900",
        "desc": "Full Care Journey showing Node 5 recorded review state"
    }
]

def capture():
    print("=" * 60)
    print("Capturing 14 RetinaX Care Verification Screenshots")
    print("=" * 60)
    
    for i, v in enumerate(VIEWS, 1):
        target_path = SCREENSHOTS_DIR / v["name"]
        cmd = [
            CHROME_EXE,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--window-size={v['size']}",
            f"--screenshot={str(target_path)}",
            v["url"]
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if target_path.exists() and target_path.stat().st_size > 0:
                print(f"[{i:02d}/14] PASS: {v['name']} ({target_path.stat().st_size // 1024} KB) - {v['desc']}")
                # Also copy to artifacts dir
                if ARTIFACTS_DIR.exists():
                    shutil.copy2(target_path, ARTIFACTS_DIR / v["name"])
            else:
                print(f"[{i:02d}/14] FAIL: {v['name']} not generated")
        except Exception as e:
            print(f"[{i:02d}/14] ERROR capturing {v['name']}: {e}")
            
    print("=" * 60)
    print("Screenshot capture complete!")

if __name__ == "__main__":
    capture()
