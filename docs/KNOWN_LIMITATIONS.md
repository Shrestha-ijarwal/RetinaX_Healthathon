# RetinaX Care — Known Limitations & Future Work Disclosures

**Document Version:** 2.0.0  
**Health-a-thon 2026 Evaluation Notice**  

---

## 1. Non-Clinical Operational Scope Boundary

RetinaX Care is built strictly as an assistive workflow coordination platform to close operational loops in diabetic eye screening.

- **No Medical Diagnosis:** The platform does not diagnose diabetic retinopathy, assess severity, or generate DR grades (0–4).
- **No Autonomous Clinical Decision Support:** All referrals, recall intervals, and medical decisions remain the sole responsibility of qualified ophthalmologists and clinicians.
- **No Regulatory Clearance:** This platform is an educational MVP developed for Health-a-thon 2026. It has not received CDSCO, FDA 510(k), or CE Mark medical device clearance.

---

## 2. Simulated & Mock Integrations (MVP Scope)

To ensure safe local evaluation without incurring external cloud expenses or sending unauthorized communications:

1. **Patient Notifications (SMS / WhatsApp):**
   - Implemented via a simulation engine (`sent_status: "Simulated Sent (Demo notification — not actually sent)"`).
   - Production integration with telecom aggregators (Twilio, Gupshup, Meta WhatsApp Business API) requires enterprise DLT registration and is documented as future work.
2. **HL7 / FHIR Interoperability:**
   - FHIR R4 resource generators for `Patient`, `Task`, and `DocumentReference` are fully implemented and verified.
   - Live synchronization with proprietary hospital EMRs (Epic, Cerner, ABDM HMIS) is simulated via mock endpoints and sandbox payloads.
3. **AWS Deployment:**
   - Infrastructure as Code (Terraform), ECS Fargate task definitions, and IAM least-privilege policies are prepared and validated in `infrastructure/aws/`.
   - Real cloud provisioning has not been initiated without user authorization to avoid cloud billing.
4. **Antivirus & Malware Scanning:**
   - Heuristic byte inspection is active in `document_service.py`. Integration with an enterprise daemon (e.g., ClamAV via TCP socket) is documented as an extension point.

---

## 3. Synthetic Demonstration Data Disclosure

- All patient profiles, names, telephone numbers, and clinical narratives in `data/synthetic_patients.json` are **entirely synthetic and fictional**.
- Any resemblance to real persons or actual clinical events is purely coincidental.
- Real Protected Health Information (PHI) must never be loaded into this demonstration environment.
