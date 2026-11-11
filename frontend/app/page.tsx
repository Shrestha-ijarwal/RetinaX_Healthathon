'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '../lib/api';

export default function OverviewPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [gapRadar, setGapRadar] = useState<any>(null);
  const [recentPatients, setRecentPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [patientsRes, radarRes] = await Promise.all([
          api.getPatients({ limit: 6 }),
          api.getGapRadar()
        ]);
        setMetrics(patientsRes.metrics);
        setRecentPatients(patientsRes.patients);
        setGapRadar(radarRes);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Error connecting to backend API');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Top Banner / Scope Announcement */}
      <div
        style={{
          background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
          color: '#ffffff',
          borderRadius: 16,
          padding: '24px 28px',
          boxShadow: 'var(--shadow-md)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 16
        }}
      >
        <div style={{ maxWidth: 800 }}>
          <div style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#bae6fd', marginBottom: 4 }}>
            Health-a-thon 2026 • Care Continuity Edition
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 800, margin: '0 0 8px 0', color: '#fff' }}>
            Closing the Loop in Diabetic Eye Care
          </h1>
          <p style={{ margin: 0, fontSize: 14, color: '#f0f9ff', lineHeight: 1.5 }}>
            Operational platform assisting diabetes care teams in detecting screening dropouts,
            coordinating ophthalmologist tele-reviews, and completing clinician-directed follow-up.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <Link href="/patients" className="btn btn-primary" style={{ background: '#fff', color: '#0369a1', fontWeight: 700 }}>
            Open Patient Cohort →
          </Link>
          <Link href="/reviews" className="btn btn-primary" style={{ background: '#fff', color: '#0369a1', fontWeight: 700 }}>
            Specialist Review →
          </Link>
        </div>
      </div>

      {error && (
        <div style={{ padding: 14, background: 'var(--red-subtle)', color: 'var(--red)', borderRadius: 10, fontSize: 13, border: '1px solid var(--red)' }}>
          ⚠️ Backend Notice: {error}. {error.toLowerCase().includes('auth') && (
            <span>Please <Link href="/login" style={{ textDecoration: 'underline', fontWeight: 700, color: 'inherit' }}>Sign In</Link> with evaluation credentials to open the patient cohort and specialist reviews.</span>
          )}
        </div>
      )}

      {/* Primary Operational Metrics Grid */}
      <div className="metrics-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
        <div className="card" style={{ padding: 18, background: 'var(--surface-card)', borderRadius: 12, border: '1px solid var(--line)' }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase' }}>
            Enrolled Cohort
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--ink)', margin: '8px 0 4px' }}>
            {metrics?.total_patients ?? 12}
          </div>
          <div style={{ fontSize: 12, color: 'var(--primary)' }}>
            Synthetic demo patients
          </div>
        </div>

        <div className="card" style={{ padding: 18, background: 'var(--surface-card)', borderRadius: 12, border: '1px solid var(--line)' }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase' }}>
            Screenings Completed
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--emerald)', margin: '8px 0 4px' }}>
            {metrics?.screening_completed ?? 8}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>
            {metrics?.screening_scheduled ?? 2} scheduled
          </div>
        </div>

        <div className="card" style={{ padding: 18, background: 'var(--surface-card)', borderRadius: 12, border: '1px solid var(--line)' }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase' }}>
            Awaiting Specialist Review
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--amber)', margin: '8px 0 4px' }}>
            {metrics?.awaiting_specialist_review ?? 3}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>
            Screening report attached
          </div>
        </div>

        <div className="card" style={{ padding: 18, background: 'var(--surface-card)', borderRadius: 12, border: '1px solid var(--line)' }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--muted)', textTransform: 'uppercase' }}>
            Care Loops Closed
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--primary-dark)', margin: '8px 0 4px' }}>
            {metrics?.care_loops_closed ?? 2}
          </div>
          <div style={{ fontSize: 12, color: 'var(--emerald)', fontWeight: 600 }}>
            {metrics?.total_patients ? Math.round((metrics.care_loops_closed / metrics.total_patients) * 100) : 17}% completion
          </div>
        </div>
      </div>

      {/* Care Continuity Radar Alert Box */}
      {gapRadar && gapRadar.total_flagged > 0 && (
        <div style={{ background: 'var(--amber-subtle)', border: '1px solid var(--amber)', borderRadius: 14, padding: '18px 20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 20 }}>🎯</span>
              <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
                Care Continuity Radar: {gapRadar.total_flagged} Patient(s) Requiring Attention
              </h2>
            </div>
            <Link href="/analytics" style={{ fontSize: 13, fontWeight: 600, color: 'var(--primary-dark)', textDecoration: 'none' }}>
              View Gap Radar →
            </Link>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
            {gapRadar.flagged_patients?.slice(0, 3).map((fp: any) => (
              <div key={fp.patient_id} style={{ background: 'var(--surface)', padding: 12, borderRadius: 8, border: '1px solid var(--line)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 700, fontSize: 13, color: 'var(--ink)' }}>{fp.patient_name} ({fp.patient_id})</span>
                  <span className="badge" style={{ fontSize: 10, background: 'var(--red-subtle)', color: 'var(--red)' }}>{fp.urgency}</span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
                  {fp.issues?.[0]}
                </div>
                <div style={{ marginTop: 8, textAlign: 'right' }}>
                  <Link href={`/patients?selected=${fp.patient_id}`} style={{ fontSize: 12, color: 'var(--primary)', fontWeight: 600, textDecoration: 'none' }}>
                    Open Patient Record →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Navigation Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 14 }}>
        <Link href="/patients" style={{ textDecoration: 'none' }}>
          <div className="card" style={{ padding: 16, background: 'var(--surface-card)', border: '1px solid var(--line)', borderRadius: 12, cursor: 'pointer', transition: 'transform 0.15s' }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>👥</div>
            <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--ink)' }}>Patients Directory</div>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>Search & manage cohort</div>
          </div>
        </Link>
        <Link href="/journeys" style={{ textDecoration: 'none' }}>
          <div className="card" style={{ padding: 16, background: 'var(--surface-card)', border: '1px solid var(--line)', borderRadius: 12, cursor: 'pointer' }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>🗺️</div>
            <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--ink)' }}>Care Journeys</div>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>Journey Twin & progression</div>
          </div>
        </Link>
        <Link href="/reviews" style={{ textDecoration: 'none' }}>
          <div className="card" style={{ padding: 16, background: 'var(--surface-card)', border: '1px solid var(--line)', borderRadius: 12, cursor: 'pointer' }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>🩺</div>
            <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--ink)' }}>Specialist Reviews</div>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>Ophthalmologist queue</div>
          </div>
        </Link>
        <Link href="/followups" style={{ textDecoration: 'none' }}>
          <div className="card" style={{ padding: 16, background: 'var(--surface-card)', border: '1px solid var(--line)', borderRadius: 12, cursor: 'pointer' }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>📞</div>
            <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--ink)' }}>Follow-Ups</div>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>Worklist & reminders</div>
          </div>
        </Link>
        <Link href="/documents" style={{ textDecoration: 'none' }}>
          <div className="card" style={{ padding: 16, background: 'var(--surface-card)', border: '1px solid var(--line)', borderRadius: 12, cursor: 'pointer' }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>📁</div>
            <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--ink)' }}>Documents</div>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>Verified PDF reports</div>
          </div>
        </Link>
        <Link href="/analytics" style={{ textDecoration: 'none' }}>
          <div className="card" style={{ padding: 16, background: 'var(--surface-card)', border: '1px solid var(--line)', borderRadius: 12, cursor: 'pointer' }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>📊</div>
            <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--ink)' }}>Continuity Insights</div>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>Reconciliation & metrics</div>
          </div>
        </Link>
      </div>

      {/* Cohort Snapshot Table */}
      <div className="card" style={{ background: 'var(--surface-card)', borderRadius: 14, border: '1px solid var(--line)', padding: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0, color: 'var(--ink)' }}>
            Active Patient Worklist Preview
          </h2>
          <Link href="/patients" className="btn btn-outline btn-sm" style={{ fontSize: 12 }}>
            View Full Patient Directory →
          </Link>
        </div>

        <div className="table-responsive" style={{ overflowX: 'auto' }}>
          <table className="table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--line)', color: 'var(--muted)' }}>
                <th style={{ padding: '10px 12px' }}>ID</th>
                <th style={{ padding: '10px 12px' }}>Patient Name</th>
                <th style={{ padding: '10px 12px' }}>Facility</th>
                <th style={{ padding: '10px 12px' }}>Workflow Stage</th>
                <th style={{ padding: '10px 12px' }}>Next Action</th>
                <th style={{ padding: '10px 12px' }}>Loop Closed</th>
              </tr>
            </thead>
            <tbody>
              {recentPatients.map((p) => (
                <tr key={p.id} style={{ borderBottom: '1px solid var(--line)' }}>
                  <td style={{ padding: '10px 12px', fontWeight: 700, color: 'var(--primary)' }}>
                    <Link href={`/patients?selected=${p.id}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                      {p.id}
                    </Link>
                  </td>
                  <td style={{ padding: '10px 12px', fontWeight: 600 }}>{p.name} ({p.age}y / {p.sex})</td>
                  <td style={{ padding: '10px 12px', color: 'var(--muted)' }}>{p.facility}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <span className="badge" style={{ background: 'var(--primary-subtle)', color: 'var(--primary-dark)', padding: '2px 8px', borderRadius: 4, fontSize: 11 }}>
                      {p.workflow_status?.overall_stage || 'Enrolled'}
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px', fontSize: 12, color: 'var(--ink-secondary)' }}>
                    {p.workflow_status?.next_workflow_action || 'Pending'}
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    {p.workflow_status?.care_loop_completed ? (
                      <span style={{ color: 'var(--emerald)', fontWeight: 700 }}>✓ Closed</span>
                    ) : (
                      <span style={{ color: 'var(--muted)' }}>In Progress</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
