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

  // Operational Review Form state (strictly non-clinical)
  const [assignedSpecialist, setAssignedSpecialist] = useState('Dr. Suresh Chandran, MS');
  const [clinicianTitle, setClinicianTitle] = useState('Dr.');
  const [clinicianSpecialty, setClinicianSpecialty] = useState('Ophthalmology');
  const [clinicianFacility, setClinicianFacility] = useState('District Eye Hospital');
  const [registrationNumber, setRegistrationNumber] = useState('MCI-2016-849201');
  const [reviewStatus, setReviewStatus] = useState('followup_initiated');
  const [operationalNotes, setOperationalNotes] = useState('');
  const [clinicianInstruction, setClinicianInstruction] = useState('');
  const [taskOwner, setTaskOwner] = useState('Care Coordinator');
  const [reconciliationStatus, setReconciliationStatus] = useState('Reconciled');

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
        setAssignedSpecialist(data.review.assigned_specialist || assignedSpecialist);
        setReviewStatus(data.review.review_status || 'review_completed');
        setOperationalNotes(data.review.operational_notes || '');
        setClinicianInstruction(data.review.clinician_instruction || '');
        setReconciliationStatus(data.review.reconciliation_status || 'Reconciled');
      } else {
        setOperationalNotes('');
        setClinicianInstruction('');
        setReviewStatus('followup_initiated');
        setReconciliationStatus('Reconciled');
      }
    } catch (err: any) {
      alert(`Error loading review workspace: ${err.message}`);
    }
  }

  async function handleSubmitReview(e: React.FormEvent) {
    e.preventDefault();
    if (!isSpecialist) {
      alert('Permission Denied: Only users with the "Specialist" role are authorized to record specialist review directives.');
      return;
    }
    if (!operationalNotes.trim() || !clinicianInstruction.trim()) {
      alert('Please fill out both the operational notes and the attributed clinician instruction.');
      return;
    }

    setSubmitting(true);
    try {
      await api.submitSpecialistReview(selectedPatientId!, {
        assigned_specialist: assignedSpecialist.trim(),
        clinician_title: clinicianTitle,
        clinician_specialty: clinicianSpecialty,
        clinician_facility: clinicianFacility,
        registration_number: registrationNumber,
        review_status: reviewStatus,
        operational_notes: operationalNotes.trim(),
        clinician_instruction: clinicianInstruction.trim(),
        task_owner: taskOwner,
        operational_task_status: reviewStatus === 'followup_completed' ? 'Completed' : 'In Progress',
        reconciliation_status: reconciliationStatus
      });
      alert('Specialist operational review and attributed directives successfully recorded.');
      setSelectedPatientId(null);
      loadQueue();
    } catch (err: any) {
      alert(`Submission failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  }

  const formatReviewStatus = (status: string) => {
    switch (status) {
      case 'awaiting_specialist_review':
        return { label: 'Awaiting Specialist Review', bg: 'var(--amber-subtle)', color: 'var(--amber)' };
      case 'review_scheduled':
        return { label: 'Review Scheduled', bg: 'var(--blue-subtle)', color: 'var(--blue)' };
      case 'review_completed':
        return { label: 'Review Completed', bg: 'var(--emerald-subtle)', color: 'var(--emerald)' };
      case 'awaiting_clinician_instruction':
        return { label: 'Awaiting Clinician Directive', bg: 'var(--amber-subtle)', color: 'var(--amber)' };
      case 'followup_initiated':
        return { label: 'Follow-Up Initiated', bg: 'var(--indigo-subtle)', color: 'var(--indigo)' };
      case 'followup_completed':
        return { label: 'Follow-Up Completed', bg: 'var(--emerald-subtle)', color: 'var(--emerald)' };
      case 'record_reconciliation_required':
        return { label: 'Record Reconciliation Required', bg: 'var(--rose-subtle)', color: 'var(--rose)' };
      default:
        return { label: status, bg: 'var(--surface-subtle)', color: 'var(--muted)' };
    }
  };

  return (
    <div style={{ padding: '24px 0', maxWidth: 1200, margin: '0 auto' }}>
      {/* Scope Disclaimer */}
      <div style={{
        background: 'var(--surface-card)',
        borderLeft: '4px solid var(--teal)',
        padding: '12px 16px',
        borderRadius: 8,
        fontSize: 12,
        color: 'var(--ink-secondary)',
        marginBottom: 20,
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
      }}>
        <strong>Operational Care Tracking Notice:</strong> Specialist review captures verified document availability and coordinates administrative follow-up. RetinaX Care does not generate clinical diagnoses, disease severity grades, or autonomous care decisions.
      </div>

      {!selectedPatientId ? (
        <div>
          {/* Header & Controls */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
            <div>
              <h1 style={{ fontSize: 24, fontWeight: 700, margin: '0 0 4px', color: 'var(--ink)' }}>
                Specialist Review Portal
              </h1>
              <p style={{ margin: 0, fontSize: 13, color: 'var(--muted)' }}>
                Screening document review, operational triage, and clinician-attributed follow-up coordination.
              </p>
            </div>

            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <input
                type="text"
                placeholder="Search patient name or ID..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  loadQueue(e.target.value);
                }}
                style={{
                  padding: '8px 12px',
                  borderRadius: 8,
                  border: '1px solid var(--line)',
                  fontSize: 13,
                  width: 240,
                  background: 'var(--surface)'
                }}
              />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{
                  padding: '8px 12px',
                  borderRadius: 8,
                  border: '1px solid var(--line)',
                  fontSize: 13,
                  background: 'var(--surface)'
                }}
              >
                <option value="all">All Queue Items</option>
                <option value="pending">Awaiting Review</option>
                <option value="completed">Review Recorded</option>
              </select>
            </div>
          </div>

          {/* Queue Table */}
          <div className="card" style={{ background: 'var(--surface-card)', borderRadius: 14, border: '1px solid var(--line)', overflow: 'hidden' }}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: 700 }}>
                <thead>
                  <tr style={{ background: 'var(--surface-subtle)', borderBottom: '1px solid var(--line)', fontSize: 12, color: 'var(--muted)' }}>
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
                      <td colSpan={6} style={{ padding: 32, textAlign: 'center', color: 'var(--muted)', fontSize: 13 }}>
                        Loading specialist review queue...
                      </td>
                    </tr>
                  ) : queue.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ padding: 32, textAlign: 'center', color: 'var(--muted)', fontSize: 13 }}>
                        No records matching filter criteria.
                      </td>
                    </tr>
                  ) : (
                    queue.map((item) => {
                      const badge = formatReviewStatus(item.review_status || item.review_state);
                      return (
                        <tr key={item.patient_id} style={{ borderBottom: '1px solid var(--line)' }}>
                          <td style={{ padding: '12px 14px' }}>
                            <div style={{ fontWeight: 600, color: 'var(--ink)', fontSize: 13 }}>{item.patient_name}</div>
                            <div style={{ fontSize: 11, color: 'var(--muted)' }}>{item.patient_id} • {item.patient_age}y, {item.patient_sex}</div>
                          </td>
                          <td style={{ padding: '12px 14px', fontSize: 12, color: 'var(--ink-secondary)' }}>
                            {item.facility}
                          </td>
                          <td style={{ padding: '12px 14px' }}>
                            <span style={{
                              display: 'inline-block',
                              padding: '3px 8px',
                              borderRadius: 6,
                              fontSize: 11,
                              fontWeight: 600,
                              background: badge.bg,
                              color: badge.color
                            }}>
                              {badge.label}
                            </span>
                          </td>
                          <td style={{ padding: '12px 14px', fontSize: 12 }}>
                            {item.screening_report_available ? (
                              <span style={{ color: 'var(--emerald)', fontWeight: 600 }}>✓ Attached ({item.report_document_count})</span>
                            ) : (
                              <span style={{ color: 'var(--rose)', fontWeight: 600 }}>Missing Report</span>
                            )}
                          </td>
                          <td style={{ padding: '12px 14px', fontSize: 12, color: 'var(--ink-secondary)' }}>
                            {item.assigned_specialist || 'Unassigned'}
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
                      );
                    })
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
              Operational Review Workspace: <strong>{reviewWorkspace?.patient_name} ({reviewWorkspace?.patient_id})</strong>
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            {/* Left Column: Screening Documentation Dossier */}
            <div className="card" style={{ background: 'var(--surface-card)', borderRadius: 14, border: '1px solid var(--line)', padding: 20 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, margin: '0 0 14px', color: 'var(--ink)' }}>
                Screening Documentation Dossier
              </h2>

              <div style={{ background: 'var(--surface-subtle)', padding: 12, borderRadius: 8, fontSize: 12, marginBottom: 16 }}>
                <div><strong>Patient:</strong> {reviewWorkspace?.patient_name} ({reviewWorkspace?.patient_age}y, {reviewWorkspace?.patient_sex})</div>
                <div><strong>Primary Care Unit:</strong> {reviewWorkspace?.facility}</div>
                <div><strong>Diabetes Record:</strong> {reviewWorkspace?.diabetes_profile?.type || 'Type 2 Diabetes'}</div>
                <div><strong>Last Recorded HbA1c:</strong> {reviewWorkspace?.diabetes_profile?.last_hba1c || 'Not Recorded'}</div>
              </div>

              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink)', marginBottom: 8 }}>
                Verified Document Attachments:
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
                          View PDF
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
                  Specialist Review & Care Directives
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
                    value={assignedSpecialist}
                    onChange={(e) => setAssignedSpecialist(e.target.value)}
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
                    Operational Review Status
                  </label>
                  <select
                    value={reviewStatus}
                    onChange={(e) => setReviewStatus(e.target.value)}
                    disabled={!isSpecialist}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: isSpecialist ? 'var(--surface)' : 'var(--surface-subtle)' }}
                  >
                    <option value="followup_initiated">Follow-Up Initiated (Coordinate Scheduled Visit)</option>
                    <option value="followup_completed">Follow-Up Completed (Annual Screening Cycle Closed)</option>
                    <option value="review_completed">Review Completed (Awaiting Coordinator Scheduling)</option>
                    <option value="record_reconciliation_required">Record Reconciliation Required (Document Incomplete)</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>
                    Operational & Document Notes
                  </label>
                  <textarea
                    rows={2}
                    required
                    placeholder="Enter notes on document legibility, identification verification, or imaging quality..."
                    value={operationalNotes}
                    onChange={(e) => setOperationalNotes(e.target.value)}
                    disabled={!isSpecialist}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: isSpecialist ? 'var(--surface)' : 'var(--surface-subtle)', fontSize: 13 }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>
                    Attributed Clinician Directive (For Care Coordinator)
                  </label>
                  <textarea
                    rows={3}
                    required
                    placeholder="Directive for care coordination team: e.g., 'Coordinate hospital ophthalmology evaluation within 6 months. Care coordinator to monitor attendance.'"
                    value={clinicianInstruction}
                    onChange={(e) => setClinicianInstruction(e.target.value)}
                    disabled={!isSpecialist}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: isSpecialist ? 'var(--surface)' : 'var(--surface-subtle)', fontSize: 13 }}
                  />
                </div>

                {!isSpecialist && (
                  <div style={{ padding: 10, background: 'var(--amber-subtle)', color: 'var(--amber)', borderRadius: 8, fontSize: 11 }}>
                    ⚠️ Note: You are logged in as <strong>{currentUser?.role || 'Guest'}</strong>. Only users with the <strong>Specialist</strong> role can record specialist reviews. Switch to a Specialist account from the login screen to submit.
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
                    {submitting ? 'Recording Directives...' : 'Record Attributed Directives'}
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
