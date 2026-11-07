'use client';

import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';

export default function PatientsPage() {
  const [patients, setPatients] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [search, setSearch] = useState('');
  const [filterMode, setFilterMode] = useState('all');
  const [loading, setLoading] = useState(true);
  const [selectedPatient, setSelectedPatient] = useState<any | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPatientName, setNewPatientName] = useState('');
  const [newPatientAge, setNewPatientAge] = useState('50');
  const [newPatientSex, setNewPatientSex] = useState('Male');
  const [newPatientContact, setNewPatientContact] = useState('');
  const [newPatientFacility, setNewPatientFacility] = useState('Primary Health Centre - Ramanagara');

  const filterTabs = [
    { key: 'all', label: 'All Patients' },
    { key: 'needs_attention', label: 'Needs Attention' },
    { key: 'pending_screening', label: 'Pending Screening' },
    { key: 'scheduled', label: 'Screening Scheduled' },
    { key: 'screening_completed', label: 'Screening Completed' },
    { key: 'report_missing', label: 'Report Missing' },
    { key: 'awaiting_review', label: 'Awaiting Review' },
    { key: 'followup_pending', label: 'Follow-Up Pending' },
    { key: 'unable_to_contact', label: 'Unable to Contact' },
    { key: 'completed', label: 'Care Loop Closed' }
  ];

  useEffect(() => {
    loadPatients();
  }, [filterMode]);

  async function loadPatients(searchVal = search) {
    setLoading(true);
    try {
      const res = await api.getPatients({ search: searchVal, filter: filterMode });
      setPatients(res.patients);
      setMetrics(res.metrics);
    } catch (err) {
      console.error('Failed to load patients:', err);
    } finally {
      setLoading(false);
    }
  }

  async function openPatientDetail(patientId: string) {
    setDetailLoading(true);
    try {
      const data = await api.getPatient(patientId);
      setSelectedPatient(data);
    } catch (err: any) {
      alert(`Error loading patient details: ${err.message}`);
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleCreatePatient(e: React.FormEvent) {
    e.preventDefault();
    if (!newPatientName.trim()) return;

    try {
      await api.createPatient({
        name: newPatientName.trim(),
        age: parseInt(newPatientAge, 10) || 45,
        sex: newPatientSex,
        contact: newPatientContact.trim(),
        facility: newPatientFacility,
        clinician: 'Care Coordinator Desk'
      });
      setShowCreateModal(false);
      setNewPatientName('');
      setNewPatientContact('');
      loadPatients();
      alert('New synthetic patient registered successfully into care cohort.');
    } catch (err: any) {
      alert(`Registration failed: ${err.message}`);
    }
  }

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, margin: 0, color: 'var(--ink)' }}>
            Patient Directory & Screening Worklist
          </h1>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 2 }}>
            Manage diabetic screening pathways, view record completeness, and resolve care gaps. (Fictional demonstration records)
          </div>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
          style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
        >
          <span>+</span> Register Synthetic Patient
        </button>
      </div>

      {/* Filter Tabs */}
      <div
        style={{
          display: 'flex',
          gap: 6,
          overflowX: 'auto',
          paddingBottom: 6,
          borderBottom: '1px solid var(--line)'
        }}
      >
        {filterTabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilterMode(tab.key)}
            style={{
              padding: '6px 14px',
              borderRadius: 20,
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              border: filterMode === tab.key ? '1px solid var(--primary)' : '1px solid var(--line)',
              background: filterMode === tab.key ? 'var(--primary-subtle)' : 'var(--surface)',
              color: filterMode === tab.key ? 'var(--primary-dark)' : 'var(--ink-secondary)'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Search Input Bar */}
      <div style={{ display: 'flex', gap: 10 }}>
        <input
          type="text"
          placeholder="Search by patient name, ID (e.g. RX-1001), phone, or clinic..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            loadPatients(e.target.value);
          }}
          style={{
            flex: 1,
            padding: '10px 14px',
            borderRadius: 8,
            border: '1px solid var(--line)',
            background: 'var(--surface)',
            color: 'var(--ink)',
            fontSize: 14
          }}
        />
        <button
          className="btn btn-outline"
          onClick={() => loadPatients(search)}
        >
          Search
        </button>
      </div>

      {/* Patient Directory Table */}
      <div className="card" style={{ background: 'var(--surface-card)', borderRadius: 12, border: '1px solid var(--line)', overflow: 'hidden' }}>
        <div className="table-responsive">
          <table className="table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13 }}>
            <thead>
              <tr style={{ background: 'var(--surface-subtle)', borderBottom: '2px solid var(--line)', color: 'var(--muted)' }}>
                <th style={{ padding: '12px 14px' }}>Patient ID</th>
                <th style={{ padding: '12px 14px' }}>Demographics</th>
                <th style={{ padding: '12px 14px' }}>Facility</th>
                <th style={{ padding: '12px 14px' }}>Workflow Stage</th>
                <th style={{ padding: '12px 14px' }}>Next Action</th>
                <th style={{ padding: '12px 14px' }}>Completeness</th>
                <th style={{ padding: '12px 14px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>
                    Loading patient cohort...
                  </td>
                </tr>
              ) : patients.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>
                    No synthetic patients match the current filter.
                  </td>
                </tr>
              ) : (
                patients.map((p) => (
                  <tr key={p.id} style={{ borderBottom: '1px solid var(--line)' }}>
                    <td style={{ padding: '12px 14px', fontWeight: 700, color: 'var(--primary)' }}>
                      {p.id}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ fontWeight: 600, color: 'var(--ink)' }}>{p.name}</div>
                      <div style={{ fontSize: 11, color: 'var(--muted)' }}>{p.age}y • {p.sex} • {p.contact || 'No phone'}</div>
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--ink-secondary)', fontSize: 12 }}>
                      {p.facility}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className="badge" style={{ background: 'var(--primary-subtle)', color: 'var(--primary-dark)', padding: '3px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600 }}>
                        {p.workflow_status?.overall_stage || 'Enrolled'}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 12, color: 'var(--ink-secondary)', maxWidth: 220 }}>
                      {p.workflow_status?.next_workflow_action || 'Pending action'}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <div style={{ flex: 1, background: 'var(--line)', height: 6, borderRadius: 3, overflow: 'hidden', minWidth: 50 }}>
                          <div style={{ width: `${p.completeness_score || 0}%`, background: p.completeness_score >= 80 ? 'var(--emerald)' : 'var(--amber)', height: '100%' }} />
                        </div>
                        <span style={{ fontSize: 11, fontWeight: 700 }}>{p.completeness_score || 0}%</span>
                      </div>
                    </td>
                    <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                      <button
                        className="btn btn-outline btn-sm"
                        onClick={() => openPatientDetail(p.id)}
                        style={{ fontSize: 11, padding: '4px 10px' }}
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Patient Detail Modal / Drawer */}
      {selectedPatient && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(15, 23, 42, 0.6)',
            zIndex: 10000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 16
          }}
          onClick={() => setSelectedPatient(null)}
        >
          <div
            style={{
              background: 'var(--surface)',
              width: '100%',
              maxWidth: 750,
              maxHeight: '90vh',
              overflowY: 'auto',
              borderRadius: 16,
              padding: 24,
              boxShadow: 'var(--shadow-xl)',
              border: '1px solid var(--line-strong)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--line)', paddingBottom: 14, marginBottom: 16 }}>
              <div>
                <span className="badge" style={{ background: 'var(--primary-subtle)', color: 'var(--primary-dark)', marginRight: 8 }}>
                  {selectedPatient.id}
                </span>
                <span style={{ fontSize: 18, fontWeight: 800, color: 'var(--ink)' }}>
                  {selectedPatient.name}
                </span>
                <span style={{ fontSize: 13, color: 'var(--muted)', marginLeft: 8 }}>
                  ({selectedPatient.age}y, {selectedPatient.sex})
                </span>
              </div>
              <button
                onClick={() => setSelectedPatient(null)}
                style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--muted)' }}
              >
                ✕
              </button>
            </div>

            {/* Content Sections */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Profile Bar */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, background: 'var(--surface-subtle)', padding: 12, borderRadius: 8, fontSize: 12 }}>
                <div><strong>Contact:</strong> {selectedPatient.contact || 'None'}</div>
                <div><strong>Facility:</strong> {selectedPatient.facility}</div>
                <div><strong>Registration:</strong> {selectedPatient.registration_date}</div>
              </div>

              {/* Workflow Status Box */}
              <div style={{ padding: 14, background: 'var(--primary-subtle)', borderRadius: 10, border: '1px solid var(--line)' }}>
                <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--primary-dark)' }}>
                  Current Care Journey Stage
                </div>
                <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--ink)', margin: '4px 0' }}>
                  {selectedPatient.workflow_status?.overall_stage}
                </div>
                <div style={{ fontSize: 13, color: 'var(--ink-secondary)' }}>
                  <strong>Next Operational Action:</strong> {selectedPatient.workflow_status?.next_workflow_action}
                </div>
              </div>

              {/* Specialist Review Section */}
              <div style={{ border: '1px solid var(--line)', borderRadius: 10, padding: 14 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--ink)', marginBottom: 8 }}>
                  🩺 Specialist Ophthalmologist Review
                </div>
                {selectedPatient.specialist_review?.completed ? (
                  <div style={{ fontSize: 12, lineHeight: 1.5 }}>
                    <div><strong>Reviewer:</strong> {selectedPatient.specialist_review.assigned_specialist || selectedPatient.specialist_review.clinician_name} ({selectedPatient.specialist_review.clinician_specialty})</div>
                    <div><strong>Status:</strong> {selectedPatient.specialist_review.review_status}</div>
                    <div><strong>Directive:</strong> {selectedPatient.specialist_review.clinician_instruction || 'Follow-up tracking active'}</div>
                    <div style={{ color: 'var(--muted)', fontSize: 11, marginTop: 4 }}>Date: {selectedPatient.specialist_review.review_completed_at || selectedPatient.specialist_review.review_timestamp}</div>
                  </div>
                ) : (
                  <div style={{ fontSize: 12, color: 'var(--muted)' }}>
                    Specialist review has not yet been recorded for this screening cycle.
                  </div>
                )}
              </div>

              {/* Documents Attached */}
              <div style={{ border: '1px solid var(--line)', borderRadius: 10, padding: 14 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--ink)', marginBottom: 8 }}>
                  📁 Attached Records & Screening Reports ({selectedPatient.documents?.length || 0})
                </div>
                {selectedPatient.documents?.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {selectedPatient.documents.map((d: any) => (
                      <div key={d.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--surface-subtle)', padding: '8px 10px', borderRadius: 6, fontSize: 12 }}>
                        <div>
                          <strong>{d.title}</strong> ({d.doc_type})
                          <div style={{ fontSize: 11, color: 'var(--muted)' }}>{d.upload_date} • {d.size_kb} KB</div>
                        </div>
                        <a
                          href={api.getDocumentDownloadUrl(d.id)}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-sm btn-outline"
                          style={{ fontSize: 11, textDecoration: 'none' }}
                        >
                          Download PDF
                        </a>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: 12, color: 'var(--muted)' }}>No documents currently uploaded.</div>
                )}
              </div>

              {/* Timeline Log */}
              <div style={{ border: '1px solid var(--line)', borderRadius: 10, padding: 14 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--ink)', marginBottom: 8 }}>
                  📜 Care Continuity Timeline ({selectedPatient.timeline?.length || 0})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 180, overflowY: 'auto' }}>
                  {selectedPatient.timeline?.map((t: any) => (
                    <div key={t.id} style={{ fontSize: 12, borderLeft: '2px solid var(--primary)', paddingLeft: 8 }}>
                      <div style={{ fontWeight: 600, color: 'var(--ink)' }}>{t.stage} ({t.timestamp})</div>
                      <div style={{ color: 'var(--ink-secondary)' }}>{t.note}</div>
                      <div style={{ fontSize: 10, color: 'var(--muted)' }}>Actor: {t.actor} ({t.source})</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Register New Patient Modal */}
      {showCreateModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(15, 23, 42, 0.6)',
            zIndex: 10000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 16
          }}
          onClick={() => setShowCreateModal(false)}
        >
          <div
            style={{
              background: 'var(--surface)',
              width: '100%',
              maxWidth: 480,
              borderRadius: 16,
              padding: 24,
              boxShadow: 'var(--shadow-xl)',
              border: '1px solid var(--line)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ fontSize: 18, fontWeight: 800, margin: 0, color: 'var(--ink)' }}>
                Register Synthetic Patient
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--muted)' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreatePatient} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Full Name (Fictional)</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Savitha Gowda"
                  value={newPatientName}
                  onChange={(e) => setNewPatientName(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Age</label>
                  <input
                    type="number"
                    min="1"
                    max="120"
                    value={newPatientAge}
                    onChange={(e) => setNewPatientAge(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Sex</label>
                  <select
                    value={newPatientSex}
                    onChange={(e) => setNewPatientSex(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Contact Phone (Synthetic)</label>
                <input
                  type="text"
                  placeholder="+91 98450 00000"
                  value={newPatientContact}
                  onChange={(e) => setNewPatientContact(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                />
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Care Facility</label>
                <input
                  type="text"
                  value={newPatientFacility}
                  onChange={(e) => setNewPatientFacility(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 12 }}>
                <button type="button" className="btn btn-outline" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Patient Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
