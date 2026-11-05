'use client';

import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';

export default function ContinuityInsightsPage() {
  const [analytics, setAnalytics] = useState<any | null>(null);
  const [gapRadar, setGapRadar] = useState<any | null>(null);
  const [reconciliation, setReconciliation] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'metrics' | 'radar' | 'reconciliation'>('metrics');

  useEffect(() => {
    loadAllInsights();
  }, []);

  async function loadAllInsights() {
    setLoading(true);
    try {
      const [anData, gapData, recData] = await Promise.all([
        api.getAnalytics(),
        api.getGapRadar(),
        api.getReconciliation()
      ]);
      setAnalytics(anData);
      setGapRadar(gapData);
      setReconciliation(recData);
    } catch (err) {
      console.error('Failed to load insights:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleResolveReconciliation(patientId: string) {
    try {
      await api.resolveReconciliation(patientId);
      alert(`Record discrepancy for ${patientId} marked as resolved.`);
      loadAllInsights();
    } catch (err: any) {
      alert(`Resolution failed: ${err.message}`);
    }
  }

  const counts = analytics?.counts || {};

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, margin: 0, color: 'var(--ink)' }}>
            Continuity Insights & Operational Intelligence
          </h1>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 2 }}>
            Real-time care continuity telemetry, gap detection radar, and record reconciliation queue.
          </div>
        </div>

        {/* Tab Buttons */}
        <div style={{ display: 'flex', gap: 6, background: 'var(--surface-subtle)', padding: 4, borderRadius: 10, border: '1px solid var(--line)' }}>
          <button
            onClick={() => setActiveTab('metrics')}
            style={{
              padding: '6px 14px',
              borderRadius: 8,
              border: 'none',
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
              background: activeTab === 'metrics' ? 'var(--surface)' : 'transparent',
              color: activeTab === 'metrics' ? 'var(--primary)' : 'var(--muted)',
              boxShadow: activeTab === 'metrics' ? 'var(--shadow-sm)' : 'none'
            }}
          >
            📊 Operational Metrics
          </button>
          <button
            onClick={() => setActiveTab('radar')}
            style={{
              padding: '6px 14px',
              borderRadius: 8,
              border: 'none',
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
              background: activeTab === 'radar' ? 'var(--surface)' : 'transparent',
              color: activeTab === 'radar' ? 'var(--primary)' : 'var(--muted)',
              boxShadow: activeTab === 'radar' ? 'var(--shadow-sm)' : 'none'
            }}
          >
            🎯 Care Gap Radar ({gapRadar?.total_flagged || 0})
          </button>
          <button
            onClick={() => setActiveTab('reconciliation')}
            style={{
              padding: '6px 14px',
              borderRadius: 8,
              border: 'none',
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
              background: activeTab === 'reconciliation' ? 'var(--surface)' : 'transparent',
              color: activeTab === 'reconciliation' ? 'var(--primary)' : 'var(--muted)',
              boxShadow: activeTab === 'reconciliation' ? 'var(--shadow-sm)' : 'none'
            }}
          >
            ⚖️ Reconciliation Queue ({reconciliation.length})
          </button>
        </div>
      </div>

      {/* Scope and Denominator Notice */}
      <div style={{ background: 'var(--primary-subtle)', border: '1px solid var(--line)', borderRadius: 10, padding: 12, fontSize: 12, color: 'var(--ink-secondary)' }}>
        ℹ️ <strong>Scope Note:</strong> {analytics?.disclaimer || 'Operational care continuity analytics only.'} <br />
        <strong>Denominator:</strong> {analytics?.denominator_explanation || 'All active synthetic demonstration records.'}
      </div>

      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--muted)' }}>
          Computing live database metrics...
        </div>
      ) : (
        <>
          {/* TAB 1: OPERATIONAL METRICS */}
          {activeTab === 'metrics' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {/* Top Row Cards */}
              <div className="metrics-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
                <div className="card" style={{ padding: 18, background: 'var(--surface-card)', borderRadius: 12, border: '1px solid var(--line)' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>
                    Total Cohort
                  </div>
                  <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--ink)', margin: '6px 0 2px' }}>
                    {counts.total_patients ?? 0}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--muted)' }}>Synthetic participants</div>
                </div>

                <div className="card" style={{ padding: 18, background: 'var(--surface-card)', borderRadius: 12, border: '1px solid var(--line)' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>
                    Loop Closure Rate
                  </div>
                  <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--emerald)', margin: '6px 0 2px' }}>
                    {counts.loop_closure_rate_pct ?? 0}%
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--emerald)', fontWeight: 600 }}>
                    {counts.care_loops_closed ?? 0} closed / {counts.total_patients ?? 0}
                  </div>
                </div>

                <div className="card" style={{ padding: 18, background: 'var(--surface-card)', borderRadius: 12, border: '1px solid var(--line)' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>
                    Awaiting Specialist Review
                  </div>
                  <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--amber)', margin: '6px 0 2px' }}>
                    {counts.awaiting_specialist_review ?? 0}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--muted)' }}>Photos ready for review</div>
                </div>

                <div className="card" style={{ padding: 18, background: 'var(--surface-card)', borderRadius: 12, border: '1px solid var(--line)' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>
                    Follow-Ups In Progress
                  </div>
                  <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--primary)', margin: '6px 0 2px' }}>
                    {counts.followup_pending ?? 0}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--muted)' }}>
                    {counts.unable_to_contact ?? 0} unable to contact
                  </div>
                </div>
              </div>

              {/* Two Column Section: Turnaround Times & Stage Breakdown */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                {/* Turnaround Time Telemetry */}
                <div className="card" style={{ background: 'var(--surface-card)', borderRadius: 12, border: '1px solid var(--line)', padding: 20 }}>
                  <h2 style={{ fontSize: 16, fontWeight: 700, margin: '0 0 14px', color: 'var(--ink)' }}>
                    ⏱️ Operational Turnaround Benchmarks (Days)
                  </h2>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: 13 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: 8 }}>
                      <span>Screening to Report Upload</span>
                      <strong>{analytics?.avg_turnaround_days?.screening_to_report} days</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: 8 }}>
                      <span>Report to Specialist Review</span>
                      <strong>{analytics?.avg_turnaround_days?.report_to_specialist_review} days</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: 8 }}>
                      <span>Review to First Patient Contact</span>
                      <strong>{analytics?.avg_turnaround_days?.review_to_first_contact} days</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: 4, fontWeight: 700, color: 'var(--primary)' }}>
                      <span>End-to-End Care Cycle</span>
                      <strong>{analytics?.avg_turnaround_days?.overall_journey_cycle} days</strong>
                    </div>
                  </div>
                </div>

                {/* Facility Distribution */}
                <div className="card" style={{ background: 'var(--surface-card)', borderRadius: 12, border: '1px solid var(--line)', padding: 20 }}>
                  <h2 style={{ fontSize: 16, fontWeight: 700, margin: '0 0 14px', color: 'var(--ink)' }}>
                    🏥 Primary Health Care Facility Distribution
                  </h2>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {Object.entries(analytics?.facility_breakdown || {}).map(([fac, count]: any) => (
                      <div key={fac} style={{ fontSize: 12 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                          <span style={{ fontWeight: 600 }}>{fac}</span>
                          <span style={{ color: 'var(--muted)' }}>{count} patient(s)</span>
                        </div>
                        <div style={{ background: 'var(--line)', height: 6, borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ width: `${(count / (counts.total_patients || 1)) * 100}%`, background: 'var(--primary)', height: '100%' }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: CARE GAP RADAR */}
          {activeTab === 'radar' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
                <div style={{ background: 'var(--red-subtle)', border: '1px solid var(--red)', padding: 14, borderRadius: 10 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--red)' }}>MISSING REPORTS</div>
                  <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--red)', margin: '4px 0' }}>
                    {gapRadar?.report_missing_count || 0}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--muted)' }}>Screened without PDF</div>
                </div>

                <div style={{ background: 'var(--amber-subtle)', border: '1px solid var(--amber)', padding: 14, borderRadius: 10 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--amber)' }}>REVIEWS OVERDUE</div>
                  <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--amber)', margin: '4px 0' }}>
                    {gapRadar?.review_overdue_count || 0}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--muted)' }}>Awaiting specialist</div>
                </div>

                <div style={{ background: 'var(--primary-subtle)', border: '1px solid var(--primary)', padding: 14, borderRadius: 10 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--primary)' }}>FOLLOW-UPS PENDING</div>
                  <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--primary)', margin: '4px 0' }}>
                    {gapRadar?.followup_overdue_count || 0}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--muted)' }}>Coordinator action required</div>
                </div>

                <div style={{ background: 'var(--red-subtle)', border: '1px solid var(--red)', padding: 14, borderRadius: 10 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--red)' }}>UNABLE TO CONTACT</div>
                  <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--red)', margin: '4px 0' }}>
                    {gapRadar?.unable_to_contact_count || 0}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--muted)' }}>ASHA outreach needed</div>
                </div>
              </div>

              {/* Flagged Patients List */}
              <div className="card" style={{ background: 'var(--surface-card)', borderRadius: 12, border: '1px solid var(--line)', padding: 20 }}>
                <h2 style={{ fontSize: 16, fontWeight: 700, margin: '0 0 14px', color: 'var(--ink)' }}>
                  Patients Flagged by Care Continuity Gap Radar ({gapRadar?.flagged_patients?.length || 0})
                </h2>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {gapRadar?.flagged_patients?.map((fp: any) => (
                    <div key={fp.patient_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--surface-subtle)', padding: '12px 16px', borderRadius: 8, border: '1px solid var(--line)' }}>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--ink)' }}>
                          {fp.patient_name} <span style={{ color: 'var(--primary)' }}>({fp.patient_id})</span>
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--muted)' }}>
                          {fp.facility} • Assigned: {fp.assigned_to}
                        </div>
                        <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
                          {fp.issues?.map((iss: string, idx: number) => (
                            <span key={idx} className="badge" style={{ background: 'var(--amber-subtle)', color: 'var(--amber)', fontSize: 11 }}>
                              ⚠️ {iss}
                            </span>
                          ))}
                        </div>
                      </div>

                      <a href={`/patients?selected=${fp.patient_id}`} className="btn btn-outline btn-sm" style={{ textDecoration: 'none', fontSize: 12 }}>
                        Investigate Patient →
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: RECONCILIATION QUEUE */}
          {activeTab === 'reconciliation' && (
            <div className="card" style={{ background: 'var(--surface-card)', borderRadius: 12, border: '1px solid var(--line)', padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <div>
                  <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
                    Data & Workflow Discrepancy Reconciliation
                  </h2>
                  <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>
                    Reconciles operational mismatches between outreach camps, primary clinics, and hospital centers.
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {reconciliation.length === 0 ? (
                  <div style={{ padding: 24, textAlign: 'center', color: 'var(--emerald)', fontWeight: 600 }}>
                    ✓ Zero discrepancies detected. All patient milestones and documentation are synchronized.
                  </div>
                ) : (
                  reconciliation.map((item, idx) => (
                    <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--surface-subtle)', padding: 14, borderRadius: 8, border: '1px solid var(--line)' }}>
                      <div style={{ maxWidth: '75%' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span className="badge" style={{ background: 'var(--red-subtle)', color: 'var(--red)', fontSize: 11 }}>
                            {item.issue_type}
                          </span>
                          <span style={{ fontWeight: 700, fontSize: 13, color: 'var(--ink)' }}>
                            {item.patient_name} ({item.patient_id})
                          </span>
                        </div>
                        <div style={{ fontSize: 13, color: 'var(--ink-secondary)', marginTop: 4 }}>
                          {item.description}
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--primary-dark)', marginTop: 4, fontWeight: 600 }}>
                          Suggested Action: {item.suggested_action}
                        </div>
                      </div>

                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => handleResolveReconciliation(item.patient_id)}
                        style={{ fontSize: 11, padding: '6px 12px' }}
                      >
                        Mark Reconciled ✓
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
