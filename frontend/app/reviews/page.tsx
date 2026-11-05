'use client';

import React, { useState, useEffect } from 'react';
import { api, getCurrentUser } from '../../lib/api';

export default function SpecialistReviewsPage() {
  const [queue, setQueue] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [reviewWorkspace, setReviewWorkspace] = useState<any | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Review Form state
  const [clinicianName, setClinicianName] = useState('Dr. Suresh Chandran, MS');
  const [clinicianTitle, setClinicianTitle] = useState('Dr.');
  const [clinicianSpecialty, setClinicianSpecialty] = useState('Ophthalmology');
  const [clinicianFacility, setClinicianFacility] = useState('District Eye Hospital');
  const [registrationNumber, setRegistrationNumber] = useState('MCI-2016-849201');
  const [clinicalAssessment, setClinicalAssessment] = useState('');
  const [followupInstructions, setFollowupInstructions] = useState('');
  const [referralStatus, setReferralStatus] = useState('Hospital Follow-Up (6 Months)');

  const currentUser = getCurrentUser();
  const isSpecialist = currentUser?.role === 'Specialist';

  useEffect(() => {
    loadQueue();
  }, [statusFilter]);

  async function loadQueue(searchVal = search) {
    setLoading(true);
    try {
      const data = await api.getReviewQueue(
        statusFilter === 'all' ? undefined : statusFilter,
        searchVal
      );
      setQueue(data);
    } catch (err) {
      console.error('Failed to load review queue:', err);
    } finally {
      setLoading(false);
    }
  }

  async function openReviewWorkspace(patientId: string) {
    setSelectedPatientId(patientId);
    try {
      const data = await api.getPatientReview(patientId);
      setReviewWorkspace(data);

      if (data.review?.completed) {
        setClinicianName(data.review.clinician_name || clinicianName);
        setClinicalAssessment(data.review.clinical_assessment || '');
        setFollowupInstructions(data.review.followup_instructions || '');
        setReferralStatus(data.review.referral_status || 'Hospital Follow-Up (6 Months)');
      } else {
        setClinicalAssessment('');
        setFollowupInstructions('');
      }
    } catch (err: any) {
      alert(`Error loading review workspace: ${err.message}`);
    }
  }

  async function handleSubmitReview(e: React.FormEvent) {
    e.preventDefault();
    if (!isSpecialist) {
      alert('Permission Denied: Only users with the "Specialist" role are authorized to submit clinical reviews.');
      return;
    }
    if (!clinicalAssessment.trim() || !followupInstructions.trim()) {
      alert('Please fill out both the clinical assessment and follow-up directives.');
      return;
    }

    setSubmitting(true);
    try {
      await api.submitSpecialistReview(selectedPatientId!, {
        clinician_name: clinicianName.trim(),
        clinician_title: clinicianTitle,
        clinician_specialty: clinicianSpecialty,
        clinician_facility: clinicianFacility,
        registration_number: registrationNumber,
        clinical_assessment: clinicalAssessment.trim(),
        followup_instructions: followupInstructions.trim(),
        referral_status: referralStatus,
        notes: `Attributed ophthalmologist tele-review completed by ${clinicianName}.`
      });
      alert('Specialist review successfully recorded and attributed in patient continuity record.');
      setSelectedPatientId(null);
      loadQueue();
    } catch (err: any) {
      alert(`Submission failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, margin: 0, color: 'var(--ink)' }}>
            Specialist Review Portal & Queue
          </h1>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 2 }}>
            Dedicated ophthalmology reading queue. Coordinates operational follow-up directives with strict clinician attribution.
          </div>
        </div>

        {/* Role Notice */}
        <div style={{ fontSize: 12, padding: '6px 12px', borderRadius: 8, background: isSpecialist ? 'var(--emerald-subtle)' : 'var(--amber-subtle)', color: isSpecialist ? 'var(--emerald)' : 'var(--amber)', border: '1px solid currentColor' }}>
          Active Role: <strong>{currentUser?.role || 'Guest'}</strong> {isSpecialist ? '(Authorized to Sign Off)' : '(Read-Only Mode)'}
        </div>
      </div>

      {!selectedPatientId ? (
        /* Review Queue Directory */
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Filter & Search Bar */}
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <input
              type="text"
              placeholder="Search queue by patient name or ID..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                loadQueue(e.target.value);
              }}
              style={{ flex: 1, minWidth: 260, padding: '10px 14px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)', color: 'var(--ink)' }}
            />

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)', color: 'var(--ink)' }}
            >
              <option value="all">All Patients</option>
              <option value="pending">Pending Review Only</option>
              <option value="completed">Completed Reviews</option>
            </select>
          </div>

          {/* Queue Table */}
          <div className="card" style={{ background: 'var(--surface-card)', borderRadius: 12, border: '1px solid var(--line)', overflow: 'hidden' }}>
            <div className="table-responsive">
              <table className="table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: 'var(--surface-subtle)', borderBottom: '2px solid var(--line)', color: 'var(--muted)' }}>
                    <th style={{ padding: '12px 14px' }}>Patient</th>
                    <th style={{ padding: '12px 14px' }}>Facility</th>
                    <th style={{ padding: '12px 14px' }}>Review Status</th>
                    <th style={{ padding: '12px 14px' }}>Screening Report</th>
                    <th style={{ padding: '12px 14px' }}>Assigned Specialist</th>
                    <th style={{ padding: '12px 14px', textAlign: 'right' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={6} style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>
                        Loading specialist review queue...
                      </td>
                    </tr>
                  ) : queue.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>
                        No patients currently match this review queue status.
                      </td>
                    </tr>
                  ) : (
                    queue.map((item) => (
                      <tr key={item.patient_id} style={{ borderBottom: '1px solid var(--line)' }}>
                        <td style={{ padding: '12px 14px' }}>
                          <span style={{ fontWeight: 700, color: 'var(--primary)' }}>{item.patient_id}</span>
                          <span style={{ marginLeft: 8, fontWeight: 600, color: 'var(--ink)' }}>{item.patient_name}</span>
                          <span style={{ fontSize: 11, color: 'var(--muted)', marginLeft: 6 }}>({item.patient_age}y • {item.patient_sex})</span>
                        </td>
                        <td style={{ padding: '12px 14px', color: 'var(--ink-secondary)', fontSize: 12 }}>
                          {item.facility}
                        </td>
                        <td style={{ padding: '12px 14px' }}>
                          <span className="badge" style={{
                            padding: '3px 8px',
                            borderRadius: 4,
                            fontSize: 11,
                            fontWeight: 600,
                            background: item.completed ? 'var(--emerald-subtle)' : item.review_state === 'Pending Review' ? 'var(--amber-subtle)' : 'var(--surface-subtle)',
                            color: item.completed ? 'var(--emerald)' : item.review_state === 'Pending Review' ? 'var(--amber)' : 'var(--muted)'
                          }}>
                            {item.review_state}
                          </span>
                        </td>
                        <td style={{ padding: '12px 14px', fontSize: 12 }}>
                          {item.screening_report_available ? (
                            <span style={{ color: 'var(--emerald)', fontWeight: 600 }}>✓ {item.report_document_count} Report(s)</span>
                          ) : (
                            <span style={{ color: 'var(--muted)' }}>Pending Upload</span>
                          )}
                        </td>
                        <td style={{ padding: '12px 14px', fontSize: 12, color: 'var(--ink-secondary)' }}>
                          {item.assigned_specialist || 'Dr. Suresh Chandran'}
                        </td>
                        <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                          <button
                            className={`btn btn-sm ${item.completed ? 'btn-outline' : 'btn-primary'}`}
                            onClick={() => openReviewWorkspace(item.patient_id)}
                            style={{ fontSize: 11, padding: '4px 12px' }}
                          >
                            {item.completed ? 'View Directive' : 'Open Workspace →'}
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        /* Review Workspace */
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button className="btn btn-outline btn-sm" onClick={() => setSelectedPatientId(null)}>
              ← Back to Review Queue
            </button>
            <span style={{ fontSize: 13, color: 'var(--muted)' }}>
              Patient Review Workspace: <strong>{reviewWorkspace?.patient_name} ({reviewWorkspace?.patient_id})</strong>
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            {/* Left Column: Attached Screening Documents & Operational Context */}
            <div className="card" style={{ background: 'var(--surface-card)', borderRadius: 14, border: '1px solid var(--line)', padding: 20 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, margin: '0 0 14px', color: 'var(--ink)' }}>
                Screening Photography & Record Dossier
              </h2>

              <div style={{ background: 'var(--surface-subtle)', padding: 12, borderRadius: 8, fontSize: 12, marginBottom: 16 }}>
                <div><strong>Patient:</strong> {reviewWorkspace?.patient_name} ({reviewWorkspace?.patient_age}y, {reviewWorkspace?.patient_sex})</div>
                <div><strong>Primary Care Unit:</strong> {reviewWorkspace?.facility}</div>
                <div><strong>Diabetes Profile:</strong> {reviewWorkspace?.diabetes_profile?.type || 'Type 2 Diabetes'}</div>
                <div><strong>Last Documented HbA1c:</strong> {reviewWorkspace?.diabetes_profile?.last_hba1c || 'Not Recorded'}</div>
              </div>

              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink)', marginBottom: 8 }}>
                Screening Document Attachments:
              </div>

              {reviewWorkspace?.screening_reports?.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {reviewWorkspace.screening_reports.map((doc: any) => (
                    <div key={doc.id} style={{ border: '1px solid var(--line)', padding: 12, borderRadius: 8, background: 'var(--surface)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: 13, color: 'var(--ink)' }}>{doc.title}</div>
                          <div style={{ fontSize: 11, color: 'var(--muted)' }}>Uploaded: {doc.upload_date} • {doc.source}</div>
                        </div>
                        <a
                          href={api.getDocumentDownloadUrl(doc.id)}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-outline btn-sm"
                          style={{ fontSize: 11, textDecoration: 'none' }}
                        >
                          View Verified PDF
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ padding: 16, textAlign: 'center', background: 'var(--surface-subtle)', borderRadius: 8, fontSize: 12, color: 'var(--muted)' }}>
                  ⚠️ No screening report document uploaded yet for this patient.
                </div>
              )}
            </div>

            {/* Right Column: Specialist Review & Directives Form */}
            <div className="card" style={{ background: 'var(--surface-card)', borderRadius: 14, border: '1px solid var(--line)', padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
                  Ophthalmologist Clinical Directives
                </h2>
                {reviewWorkspace?.review?.completed && (
                  <span className="badge" style={{ background: 'var(--emerald-subtle)', color: 'var(--emerald)', fontSize: 11, padding: '3px 8px' }}>
                    ✓ Previously Recorded
                  </span>
                )}
              </div>

              <form onSubmit={handleSubmitReview} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>
                    Reviewing Clinician (Attributed)
                  </label>
                  <input
                    type="text"
                    required
                    value={clinicianName}
                    onChange={(e) => setClinicianName(e.target.value)}
                    disabled={!isSpecialist}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: isSpecialist ? 'var(--surface)' : 'var(--surface-subtle)' }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Specialty</label>
                    <input
                      type="text"
                      value={clinicianSpecialty}
                      onChange={(e) => setClinicianSpecialty(e.target.value)}
                      disabled={!isSpecialist}
                      style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: isSpecialist ? 'var(--surface)' : 'var(--surface-subtle)' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Medical Registration</label>
                    <input
                      type="text"
                      value={registrationNumber}
                      onChange={(e) => setRegistrationNumber(e.target.value)}
                      disabled={!isSpecialist}
                      style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: isSpecialist ? 'var(--surface)' : 'var(--surface-subtle)' }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>
                    Operational Referral / Follow-Up Classification
                  </label>
                  <select
                    value={referralStatus}
                    onChange={(e) => setReferralStatus(e.target.value)}
                    disabled={!isSpecialist}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: isSpecialist ? 'var(--surface)' : 'var(--surface-subtle)' }}
                  >
                    <option value="Hospital Follow-Up (6 Months)">Hospital Follow-Up (6 Months)</option>
                    <option value="Hospital Eye Clinic Urgent Referral">Hospital Eye Clinic Urgent Referral</option>
                    <option value="Routine Annual Retinal Screening">Routine Annual Retinal Screening (Close Loop)</option>
                    <option value="Optical Correction / Low Vision Referral">Optical Correction / Low Vision Referral</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>
                    Qualitative Assessment (Clinician-Entered)
                  </label>
                  <textarea
                    rows={3}
                    required
                    placeholder="Enter specialist tele-ophthalmology findings manually..."
                    value={clinicalAssessment}
                    onChange={(e) => setClinicalAssessment(e.target.value)}
                    disabled={!isSpecialist}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: isSpecialist ? 'var(--surface)' : 'var(--surface-subtle)', fontSize: 13 }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>
                    Clinician Follow-Up Instructions (For Care Coordinator)
                  </label>
                  <textarea
                    rows={2}
                    required
                    placeholder="Operational instructions for care coordination team..."
                    value={followupInstructions}
                    onChange={(e) => setFollowupInstructions(e.target.value)}
                    disabled={!isSpecialist}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: isSpecialist ? 'var(--surface)' : 'var(--surface-subtle)', fontSize: 13 }}
                  />
                </div>

                {!isSpecialist && (
                  <div style={{ padding: 10, background: 'var(--amber-subtle)', color: 'var(--amber)', borderRadius: 8, fontSize: 11 }}>
                    ⚠️ Note: You are logged in as <strong>{currentUser?.role}</strong>. Only users with the <strong>Specialist</strong> role can record clinical reviews. Switch to the Specialist demo account from the topbar menu to submit.
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
                  <button type="button" className="btn btn-outline" onClick={() => setSelectedPatientId(null)}>
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={!isSpecialist || submitting}
                  >
                    {submitting ? 'Recording Review...' : 'Record Specialist Directives'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
