'use client';

import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';

export default function CareJourneysPage() {
  const [journeys, setJourneys] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [stageFilter, setStageFilter] = useState('All');
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [twinData, setTwinData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [twinLoading, setTwinLoading] = useState(false);

  useEffect(() => {
    loadJourneys();
  }, [stageFilter]);

  async function loadJourneys(searchVal = search) {
    setLoading(true);
    try {
      const data = await api.getCareJourneys({
        search: searchVal,
        stage: stageFilter === 'All' ? undefined : stageFilter
      });
      setJourneys(data);
    } catch (err) {
      console.error('Failed to load journeys:', err);
    } finally {
      setLoading(false);
    }
  }

  async function openJourneyTwin(patientId: string) {
    setSelectedPatientId(patientId);
    setTwinLoading(true);
    try {
      const [jData, pData] = await Promise.all([
        api.getPatientJourney(patientId),
        api.getPatient(patientId)
      ]);
      setTwinData({ ...jData, fullPatient: pData });
    } catch (err: any) {
      alert(`Error loading Care Journey Twin: ${err.message}`);
    } finally {
      setTwinLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, margin: 0, color: 'var(--ink)' }}>
            Care Journey Operational Directory
          </h1>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 2 }}>
            Track patient progression through screening, tele-ophthalmology review, and clinician-directed follow-up.
          </div>
        </div>
      </div>

      {/* Directory Search & Filters */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <input
          type="text"
          placeholder="Search by patient name or ID..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            loadJourneys(e.target.value);
          }}
          style={{
            flex: 1,
            minWidth: 260,
            padding: '10px 14px',
            borderRadius: 8,
            border: '1px solid var(--line)',
            background: 'var(--surface)',
            color: 'var(--ink)',
            fontSize: 14
          }}
        />

        <select
          value={stageFilter}
          onChange={(e) => setStageFilter(e.target.value)}
          style={{
            padding: '10px 14px',
            borderRadius: 8,
            border: '1px solid var(--line)',
            background: 'var(--surface)',
            color: 'var(--ink)',
            fontSize: 14
          }}
        >
          <option value="All">All Journey Stages</option>
          <option value="Enrollment">Initial Enrollment</option>
          <option value="Screening">Screening Workflow</option>
          <option value="Review">Specialist Review</option>
          <option value="Follow-Up">Follow-Up Pending</option>
          <option value="Closed">Care Loop Closed</option>
        </select>
      </div>

      {/* Primary Directory: Cards/Rows */}
      {!selectedPatientId ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {loading ? (
            <div style={{ padding: 32, textAlign: 'center', color: 'var(--muted)' }}>
              Loading care journeys directory...
            </div>
          ) : journeys.length === 0 ? (
            <div style={{ padding: 32, textAlign: 'center', color: 'var(--muted)' }}>
              No care journeys found matching query.
            </div>
          ) : (
            journeys.map((j) => (
              <div
                key={j.patient_id}
                className="card"
                onClick={() => openJourneyTwin(j.patient_id)}
                style={{
                  background: 'var(--surface-card)',
                  borderRadius: 12,
                  border: '1px solid var(--line)',
                  padding: 18,
                  cursor: 'pointer',
                  transition: 'border-color 0.15s, box-shadow 0.15s',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: 16
                }}
              >
                <div style={{ flex: '1 1 300px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontWeight: 800, color: 'var(--primary)', fontSize: 14 }}>{j.patient_id}</span>
                    <span style={{ fontWeight: 700, fontSize: 15, color: 'var(--ink)' }}>{j.patient_name}</span>
                    <span style={{ fontSize: 12, color: 'var(--muted)' }}>({j.patient_age}y • {j.patient_sex})</span>
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
                    Facility: {j.facility} • Assigned: {j.assigned_to || 'Unassigned'}
                  </div>
                </div>

                <div style={{ flex: '1 1 240px' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--muted)' }}>
                    Current Workflow Stage
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink)', marginTop: 2 }}>
                    {j.overall_stage}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--primary-dark)', marginTop: 2 }}>
                    Next Action: {j.next_workflow_action}
                  </div>
                </div>

                <div style={{ flex: '0 0 180px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, fontWeight: 600 }}>
                    <span>Progression</span>
                    <span style={{ color: j.progress_percentage === 100 ? 'var(--emerald)' : 'var(--primary)' }}>
                      {j.progress_percentage}%
                    </span>
                  </div>
                  <div style={{ width: '100%', background: 'var(--line)', height: 8, borderRadius: 4, overflow: 'hidden' }}>
                    <div style={{ width: `${j.progress_percentage}%`, height: '100%', background: j.progress_percentage === 100 ? 'var(--emerald)' : 'var(--primary)' }} />
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--muted)', textAlign: 'right' }}>
                    {j.care_loop_completed ? '✓ Loop Closed' : 'In Progress'}
                  </div>
                </div>

                <button
                  className="btn btn-primary btn-sm"
                  style={{ alignSelf: 'center', padding: '6px 14px', fontSize: 12 }}
                >
                  Open Journey Twin →
                </button>
              </div>
            ))
          )}
        </div>
      ) : (
        /* Selected Patient: Care Journey Digital Twin Workspace */
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button
              className="btn btn-outline btn-sm"
              onClick={() => setSelectedPatientId(null)}
              style={{ display: 'flex', alignItems: 'center', gap: 6 }}
            >
              ← Back to Care Journeys Directory
            </button>
            <span style={{ fontSize: 13, color: 'var(--muted)' }}>
              Interactive Operational Twin for <strong>{twinData?.patient_name} ({twinData?.patient_id})</strong>
            </span>
          </div>

          {twinLoading ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--muted)' }}>
              Loading Care Journey Twin...
            </div>
          ) : twinData && (
            <div className="card" style={{ background: 'var(--surface-card)', borderRadius: 16, border: '1px solid var(--line)', padding: 24 }}>
              {/* Twin Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--line)', paddingBottom: 16, marginBottom: 20 }}>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: 'var(--primary)' }}>
                    Care Journey Digital Twin
                  </div>
                  <h2 style={{ fontSize: 20, fontWeight: 800, margin: '4px 0 0', color: 'var(--ink)' }}>
                    {twinData.patient_name} <span style={{ fontSize: 14, color: 'var(--muted)' }}>({twinData.patient_id})</span>
                  </h2>
                  <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
                    Facility: {twinData.facility} • Assigned Coordinator: {twinData.assigned_to}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 12, color: 'var(--muted)' }}>Overall Loop Status</div>
                  <span className="badge" style={{ fontSize: 12, background: twinData.care_loop_completed ? 'var(--emerald-subtle)' : 'var(--primary-subtle)', color: twinData.care_loop_completed ? 'var(--emerald)' : 'var(--primary-dark)', padding: '4px 10px', borderRadius: 6, fontWeight: 700 }}>
                    {twinData.care_loop_completed ? '✓ Loop Closed (Annual Cycle)' : 'In Progress'}
                  </span>
                </div>
              </div>

              {/* 5-Phase Interactive Pathway */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginBottom: 24 }}>
                {/* Phase 1: Registration */}
                <div style={{ background: 'var(--surface-subtle)', padding: 14, borderRadius: 10, border: '1px solid var(--line)' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)' }}>PHASE 1</div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--ink)', margin: '4px 0' }}>Cohort Intake</div>
                  <div style={{ fontSize: 12, color: 'var(--emerald)', fontWeight: 600 }}>✓ Completed</div>
                  <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>Registered: {twinData.fullPatient?.registration_date}</div>
                </div>

                {/* Phase 2: Screening Appointment */}
                <div style={{ background: 'var(--surface-subtle)', padding: 14, borderRadius: 10, border: '1px solid var(--line)' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)' }}>PHASE 2</div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--ink)', margin: '4px 0' }}>Retinal Screening</div>
                  <div style={{ fontSize: 12, color: twinData.screening_workflow === 'Completed' ? 'var(--emerald)' : 'var(--amber)', fontWeight: 600 }}>
                    {twinData.screening_workflow === 'Completed' ? '✓ Completed' : 'Pending Screening'}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>Date: {twinData.screening_appointment_date || 'TBD'}</div>
                </div>

                {/* Phase 3: Screening Report */}
                <div style={{ background: 'var(--surface-subtle)', padding: 14, borderRadius: 10, border: '1px solid var(--line)' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)' }}>PHASE 3</div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--ink)', margin: '4px 0' }}>Report Dossier</div>
                  <div style={{ fontSize: 12, color: twinData.document_count > 0 ? 'var(--emerald)' : 'var(--red)', fontWeight: 600 }}>
                    {twinData.document_count > 0 ? `✓ ${twinData.document_count} Doc(s) Attached` : 'Report Missing'}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>Status: {twinData.document_status}</div>
                </div>

                {/* Phase 4: Specialist Review */}
                <div style={{ background: 'var(--surface-subtle)', padding: 14, borderRadius: 10, border: '1px solid var(--line)' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)' }}>PHASE 4</div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--ink)', margin: '4px 0' }}>Specialist Review</div>
                  <div style={{ fontSize: 12, color: twinData.specialist_review === 'Completed' ? 'var(--emerald)' : 'var(--amber)', fontWeight: 600 }}>
                    {twinData.specialist_review === 'Completed' ? '✓ Review Recorded' : 'Pending Review'}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>Directives recorded</div>
                </div>

                {/* Phase 5: Follow-Up Closure */}
                <div style={{ background: 'var(--surface-subtle)', padding: 14, borderRadius: 10, border: '1px solid var(--line)' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)' }}>PHASE 5</div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--ink)', margin: '4px 0' }}>Loop Closure</div>
                  <div style={{ fontSize: 12, color: twinData.care_loop_completed ? 'var(--emerald)' : 'var(--primary)', fontWeight: 600 }}>
                    {twinData.care_loop_completed ? '✓ Loop Closed' : 'Follow-Up Pending'}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>Due: {twinData.due_date || 'Routine Cycle'}</div>
                </div>
              </div>

              {/* Detailed Operational Context */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div style={{ border: '1px solid var(--line)', padding: 16, borderRadius: 10 }}>
                  <h3 style={{ fontSize: 14, fontWeight: 700, margin: '0 0 10px', color: 'var(--ink)' }}>
                    Immediate Next Care Action
                  </h3>
                  <div style={{ fontSize: 13, color: 'var(--ink-secondary)', background: 'var(--primary-subtle)', padding: 12, borderRadius: 8, border: '1px solid var(--line)' }}>
                    {twinData.next_workflow_action}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 8 }}>
                    Staff Responsible: <strong>{twinData.assigned_to}</strong>
                  </div>
                </div>

                <div style={{ border: '1px solid var(--line)', padding: 16, borderRadius: 10 }}>
                  <h3 style={{ fontSize: 14, fontWeight: 700, margin: '0 0 10px', color: 'var(--ink)' }}>
                    Screening & Follow-Up Targets
                  </h3>
                  <div style={{ fontSize: 12, lineHeight: 1.6 }}>
                    <div><strong>Screening Appointment:</strong> {twinData.screening_appointment_date || 'Not scheduled'}</div>
                    <div><strong>Follow-up Status:</strong> {twinData.followup_status}</div>
                    <div><strong>Target Completion Date:</strong> {twinData.due_date || 'Standard protocol'}</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
