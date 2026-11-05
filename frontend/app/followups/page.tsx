'use client';

import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';

export default function FollowUpsPage() {
  const [worklist, setWorklist] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState('All');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  // Contact Attempt modal state
  const [contactModalPatient, setContactModalPatient] = useState<any | null>(null);
  const [contactMethod, setContactMethod] = useState('Phone Call');
  const [contactResult, setContactResult] = useState('');
  const [newFollowupStatus, setNewFollowupStatus] = useState('Pending');
  const [newPlannedDate, setNewPlannedDate] = useState('');
  const [contactNotes, setContactNotes] = useState('');

  // Reminder simulator modal state
  const [reminderModalPatient, setReminderModalPatient] = useState<any | null>(null);
  const [reminderType, setReminderType] = useState('Follow-Up Attendance');
  const [reminderLang, setReminderLang] = useState<'en' | 'hi'>('en');
  const [reminderCustomNote, setReminderCustomNote] = useState('');
  const [reminderSending, setReminderSending] = useState(false);
  const [reminderSentData, setReminderSentData] = useState<any | null>(null);

  useEffect(() => {
    loadWorklist();
  }, [statusFilter]);

  async function loadWorklist(searchVal = search) {
    setLoading(true);
    try {
      const data = await api.getFollowupsWorklist(
        statusFilter === 'All' ? undefined : statusFilter,
        searchVal
      );
      setWorklist(data);
    } catch (err) {
      console.error('Failed to load follow-ups worklist:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleLogContact(e: React.FormEvent) {
    e.preventDefault();
    if (!contactModalPatient) return;
    if (!contactResult.trim()) {
      alert('Please describe the contact attempt result.');
      return;
    }

    try {
      await api.updatePatientFollowup(contactModalPatient.patient_id, {
        status: newFollowupStatus,
        planned_date: newPlannedDate || undefined,
        notes: contactNotes || undefined,
        contact_attempt: {
          method: contactMethod,
          result: contactResult.trim(),
          staff: 'Care Coordinator',
          notes: contactNotes
        }
      });
      alert('Follow-up status and contact attempt logged successfully.');
      setContactModalPatient(null);
      setContactResult('');
      setContactNotes('');
      loadWorklist();
    } catch (err: any) {
      alert(`Update failed: ${err.message}`);
    }
  }

  async function handleSendReminder(e: React.FormEvent) {
    e.preventDefault();
    if (!reminderModalPatient) return;

    setReminderSending(true);
    try {
      const data = await api.sendSimulatedReminder(reminderModalPatient.patient_id, {
        type: reminderType,
        language: reminderLang,
        custom_note: reminderCustomNote || undefined
      });
      setReminderSentData(data);
    } catch (err: any) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      setReminderSending(false);
    }
  }

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, margin: 0, color: 'var(--ink)' }}>
            Follow-Up Worklist & Communication Hub
          </h1>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 2 }}>
            Coordinate clinician-directed patient contact attempts, track appointment adherence, and preview bilingual reminders.
          </div>
        </div>
      </div>

      {/* Filter Tabs & Search */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <input
          type="text"
          placeholder="Search by patient name, ID, or phone..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            loadWorklist(e.target.value);
          }}
          style={{ flex: 1, minWidth: 260, padding: '10px 14px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)', color: 'var(--ink)' }}
        />

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)', color: 'var(--ink)' }}
        >
          <option value="All">All Follow-Up Statuses</option>
          <option value="Pending">Pending Coordination</option>
          <option value="Scheduled">Scheduled Visit</option>
          <option value="Completed">Completed / Loop Closed</option>
          <option value="Unable to Contact">Unable to Contact</option>
        </select>
      </div>

      {/* Worklist Table */}
      <div className="card" style={{ background: 'var(--surface-card)', borderRadius: 12, border: '1px solid var(--line)', overflow: 'hidden' }}>
        <div className="table-responsive">
          <table className="table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13 }}>
            <thead>
              <tr style={{ background: 'var(--surface-subtle)', borderBottom: '2px solid var(--line)', color: 'var(--muted)' }}>
                <th style={{ padding: '12px 14px' }}>Patient</th>
                <th style={{ padding: '12px 14px' }}>Telephone</th>
                <th style={{ padding: '12px 14px' }}>Follow-Up Status</th>
                <th style={{ padding: '12px 14px' }}>Planned Target Date</th>
                <th style={{ padding: '12px 14px' }}>Specialist Directive</th>
                <th style={{ padding: '12px 14px' }}>Contact History</th>
                <th style={{ padding: '12px 14px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>
                    Loading follow-up worklist...
                  </td>
                </tr>
              ) : worklist.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>
                    No follow-up records found matching filter.
                  </td>
                </tr>
              ) : (
                worklist.map((item) => (
                  <tr key={item.patient_id} style={{ borderBottom: '1px solid var(--line)' }}>
                    <td style={{ padding: '12px 14px' }}>
                      <span style={{ fontWeight: 700, color: 'var(--primary)' }}>{item.patient_id}</span>
                      <span style={{ marginLeft: 8, fontWeight: 600, color: 'var(--ink)' }}>{item.patient_name}</span>
                      <div style={{ fontSize: 11, color: 'var(--muted)' }}>{item.facility}</div>
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--ink-secondary)', fontSize: 12 }}>
                      {item.contact || <span style={{ color: 'var(--red)' }}>Missing Phone</span>}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className="badge" style={{
                        padding: '3px 8px',
                        borderRadius: 4,
                        fontSize: 11,
                        fontWeight: 600,
                        background: item.followup_status === 'Completed' ? 'var(--emerald-subtle)' : item.followup_status === 'Unable to Contact' ? 'var(--red-subtle)' : 'var(--primary-subtle)',
                        color: item.followup_status === 'Completed' ? 'var(--emerald)' : item.followup_status === 'Unable to Contact' ? 'var(--red)' : 'var(--primary-dark)'
                      }}>
                        {item.followup_status}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 12 }}>
                      {item.planned_date || <span style={{ color: 'var(--muted)' }}>Not Scheduled</span>}
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 12, color: 'var(--ink-secondary)' }}>
                      {item.specialist_referral}
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 11 }}>
                      {item.contact_attempts_count > 0 ? (
                        <div>
                          <strong>{item.contact_attempts_count} attempt(s)</strong>
                          <div style={{ color: 'var(--muted)' }}>Last: {item.last_contact_attempt?.date} ({item.last_contact_attempt?.method})</div>
                        </div>
                      ) : (
                        <span style={{ color: 'var(--muted)' }}>No attempts logged</span>
                      )}
                    </td>
                    <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6 }}>
                        <button
                          className="btn btn-outline btn-sm"
                          onClick={() => {
                            setContactModalPatient(item);
                            setNewFollowupStatus(item.followup_status);
                            setNewPlannedDate(item.planned_date || '');
                          }}
                          style={{ fontSize: 11, padding: '4px 10px' }}
                        >
                          Log Contact
                        </button>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => {
                            setReminderModalPatient(item);
                            setReminderSentData(null);
                          }}
                          style={{ fontSize: 11, padding: '4px 10px' }}
                        >
                          Simulate Reminder
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Log Contact Attempt Modal */}
      {contactModalPatient && (
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
          onClick={() => setContactModalPatient(null)}
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
              <div>
                <h2 style={{ fontSize: 18, fontWeight: 800, margin: 0, color: 'var(--ink)' }}>
                  Log Contact Attempt
                </h2>
                <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>
                  Patient: {contactModalPatient.patient_name} ({contactModalPatient.patient_id})
                </div>
              </div>
              <button onClick={() => setContactModalPatient(null)} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer' }}>
                ✕
              </button>
            </div>

            <form onSubmit={handleLogContact} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Communication Channel</label>
                <select
                  value={contactMethod}
                  onChange={(e) => setContactMethod(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                >
                  <option value="Phone Call">Phone Call</option>
                  <option value="SMS">SMS</option>
                  <option value="WhatsApp">WhatsApp</option>
                  <option value="Home Visit (ASHA)">Home Visit (ASHA Worker)</option>
                  <option value="In-Clinic Counseling">In-Clinic Counseling</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Call / Contact Result</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Confirmed appointment attendance with patient"
                  value={contactResult}
                  onChange={(e) => setContactResult(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Transition Status</label>
                  <select
                    value={newFollowupStatus}
                    onChange={(e) => setNewFollowupStatus(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                  >
                    <option value="Pending">Pending</option>
                    <option value="Scheduled">Scheduled</option>
                    <option value="Completed">Completed (Close Loop)</option>
                    <option value="Unable to Contact">Unable to Contact</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Scheduled Date</label>
                  <input
                    type="date"
                    value={newPlannedDate}
                    onChange={(e) => setNewPlannedDate(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Operational Notes</label>
                <textarea
                  rows={2}
                  placeholder="Additional details regarding transport, escort, or barriers..."
                  value={contactNotes}
                  onChange={(e) => setContactNotes(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
                <button type="button" className="btn btn-outline" onClick={() => setContactModalPatient(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Record Contact & Update
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Bilingual Reminder Simulator Modal */}
      {reminderModalPatient && (
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
          onClick={() => setReminderModalPatient(null)}
        >
          <div
            style={{
              background: 'var(--surface)',
              width: '100%',
              maxWidth: 540,
              borderRadius: 16,
              padding: 24,
              boxShadow: 'var(--shadow-xl)',
              border: '1px solid var(--line)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--amber)' }}>
                  SIMULATION ENVIRONMENT • DEMO PREVIEW
                </div>
                <h2 style={{ fontSize: 18, fontWeight: 800, margin: '2px 0 0', color: 'var(--ink)' }}>
                  Patient Reminder Engine
                </h2>
              </div>
              <button onClick={() => setReminderModalPatient(null)} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer' }}>
                ✕
              </button>
            </div>

            <div style={{ padding: 10, background: 'var(--amber-subtle)', color: 'var(--amber)', borderRadius: 8, fontSize: 12, marginBottom: 14 }}>
              <strong>Notice:</strong> Real messages are strictly disabled during development and demonstration. Simulated dispatches are previewed and archived to the continuity audit log.
            </div>

            {!reminderSentData ? (
              <form onSubmit={handleSendReminder} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Reminder Type</label>
                    <select
                      value={reminderType}
                      onChange={(e) => setReminderType(e.target.value)}
                      style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                    >
                      <option value="Follow-Up Attendance">Follow-Up Attendance</option>
                      <option value="Screening Scheduled">Screening Appointment</option>
                      <option value="Document Request">Missing Records Request</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Language</label>
                    <select
                      value={reminderLang}
                      onChange={(e) => setReminderLang(e.target.value as any)}
                      style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                    >
                      <option value="en">English (EN)</option>
                      <option value="hi">Hindi (हिंदी)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Custom Coordinator Note (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. Please bring previous glasses prescription"
                    value={reminderCustomNote}
                    onChange={(e) => setReminderCustomNote(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
                  <button type="button" className="btn btn-outline" onClick={() => setReminderModalPatient(null)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={reminderSending}>
                    {reminderSending ? 'Simulating...' : 'Dispatch Simulated Reminder'}
                  </button>
                </div>
              </form>
            ) : (
              /* Sent Preview */
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div style={{ padding: 12, background: 'var(--emerald-subtle)', color: 'var(--emerald)', borderRadius: 8, fontSize: 13, fontWeight: 600 }}>
                  ✓ Simulated Dispatch Successful (Archived to Patient Log)
                </div>

                <div style={{ background: 'var(--surface-subtle)', padding: 14, borderRadius: 10, border: '1px solid var(--line)' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 6 }}>
                    Rendered Message Preview ({reminderSentData.language.toUpperCase()})
                  </div>
                  <div style={{ fontSize: 14, lineHeight: 1.5, color: 'var(--ink)' }}>
                    {reminderSentData.language === 'hi' ? reminderSentData.text_hi : reminderSentData.text_en}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 10 }}>
                    Channel: {reminderSentData.channel} • Scheduled: {reminderSentData.scheduled_for}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <button className="btn btn-primary btn-sm" onClick={() => setReminderModalPatient(null)}>
                    Close Preview
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
