'use client';

import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [docTypeFilter, setDocTypeFilter] = useState('All');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  // Upload modal state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadPatientId, setUploadPatientId] = useState('RX-1001');
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadDocType, setUploadDocType] = useState('Retinal Screening Report');
  const [uploadSource, setUploadSource] = useState('Tele-Ophthalmology Mobile Unit');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    loadDocs();
  }, [docTypeFilter]);

  async function loadDocs(searchVal = search) {
    setLoading(true);
    try {
      const data = await api.getDocuments({
        docType: docTypeFilter === 'All' ? undefined : docTypeFilter,
        search: searchVal
      });
      setDocuments(data);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    setUploadError(null);
    if (!e.target.files || e.target.files.length === 0) {
      setSelectedFile(null);
      return;
    }
    const file = e.target.files[0];

    // Client-side quick check
    const allowed = ['pdf', 'jpg', 'jpeg', 'png'];
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !allowed.includes(ext)) {
      setUploadError(`File extension '.${ext}' is not permitted. Only PDF, JPEG, and PNG allowed.`);
      setSelectedFile(null);
      return;
    }

    if (file.size > 32 * 1024 * 1024) {
      setUploadError('File exceeds 32 MB maximum size limit.');
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    if (!uploadTitle) {
      setUploadTitle(file.name.replace(/\.[^/.]+$/, ''));
    }
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedFile) {
      alert('Please choose a valid file to upload.');
      return;
    }

    setUploading(true);
    setUploadError(null);
    try {
      await api.uploadDocument(
        uploadPatientId,
        selectedFile,
        uploadTitle.trim(),
        uploadDocType,
        uploadSource
      );
      alert('Document successfully validated with binary magic-byte inspection and securely stored.');
      setShowUploadModal(false);
      setSelectedFile(null);
      setUploadTitle('');
      loadDocs();
    } catch (err: any) {
      setUploadError(err.message || 'Upload validation failed');
    } finally {
      setUploading(false);
    }
  }

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, margin: 0, color: 'var(--ink)' }}>
            Clinical Document Repository
          </h1>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 2 }}>
            Secure archive for retinal screening photography dossiers, specialist consultation notes, and laboratory reports.
          </div>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => setShowUploadModal(true)}
          style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}
        >
          <span>⬆</span> Upload Document (Secured)
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <input
          type="text"
          placeholder="Search documents by title, file name, or patient ID..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            loadDocs(e.target.value);
          }}
          style={{ flex: 1, minWidth: 260, padding: '10px 14px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)', color: 'var(--ink)' }}
        />

        <select
          value={docTypeFilter}
          onChange={(e) => setDocTypeFilter(e.target.value)}
          style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)', color: 'var(--ink)' }}
        >
          <option value="All">All Document Categories</option>
          <option value="Retinal Screening Report">Retinal Screening Reports</option>
          <option value="Specialist Consultation">Specialist Notes</option>
          <option value="Laboratory">Laboratory Summaries</option>
          <option value="Referral">Referral Forms</option>
        </select>
      </div>

      {/* Documents Table */}
      <div className="card" style={{ background: 'var(--surface-card)', borderRadius: 12, border: '1px solid var(--line)', overflow: 'hidden' }}>
        <div className="table-responsive">
          <table className="table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13 }}>
            <thead>
              <tr style={{ background: 'var(--surface-subtle)', borderBottom: '2px solid var(--line)', color: 'var(--muted)' }}>
                <th style={{ padding: '12px 14px' }}>Document Title</th>
                <th style={{ padding: '12px 14px' }}>Associated Patient</th>
                <th style={{ padding: '12px 14px' }}>Document Type</th>
                <th style={{ padding: '12px 14px' }}>Upload Date</th>
                <th style={{ padding: '12px 14px' }}>Verification State</th>
                <th style={{ padding: '12px 14px' }}>Size</th>
                <th style={{ padding: '12px 14px', textAlign: 'right' }}>Download</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>
                    Loading documents repository...
                  </td>
                </tr>
              ) : documents.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>
                    No documents found matching the criteria.
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={doc.id} style={{ borderBottom: '1px solid var(--line)' }}>
                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ fontWeight: 700, color: 'var(--ink)' }}>{doc.title}</div>
                      <div style={{ fontSize: 11, color: 'var(--muted)' }}>{doc.file_name}</div>
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span style={{ fontWeight: 700, color: 'var(--primary)' }}>{doc.patient_id}</span>
                      <div style={{ fontSize: 11, color: 'var(--muted)' }}>{doc.patient_name}</div>
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 12 }}>
                      <span className="badge" style={{ background: 'var(--primary-subtle)', color: 'var(--primary-dark)', padding: '2px 8px', borderRadius: 4 }}>
                        {doc.doc_type}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 12, color: 'var(--muted)' }}>
                      {doc.upload_date}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span style={{ color: 'var(--emerald)', fontWeight: 600, fontSize: 12 }}>
                        ✓ {doc.review_status}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 12, color: 'var(--muted)' }}>
                      {doc.size_kb} KB
                    </td>
                    <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                      <a
                        href={api.getDocumentDownloadUrl(doc.id)}
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn-outline btn-sm"
                        style={{ fontSize: 11, textDecoration: 'none', padding: '4px 10px' }}
                      >
                        Download PDF
                      </a>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Upload Modal with File Validation */}
      {showUploadModal && (
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
          onClick={() => setShowUploadModal(false)}
        >
          <div
            style={{
              background: 'var(--surface)',
              width: '100%',
              maxWidth: 500,
              borderRadius: 16,
              padding: 24,
              boxShadow: 'var(--shadow-xl)',
              border: '1px solid var(--line)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <h2 style={{ fontSize: 18, fontWeight: 800, margin: 0, color: 'var(--ink)' }}>
                Secure Document Ingestion
              </h2>
              <button onClick={() => setShowUploadModal(false)} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer' }}>
                ✕
              </button>
            </div>

            <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 14, background: 'var(--surface-subtle)', padding: 10, borderRadius: 8 }}>
              🔒 <strong>Security Policy:</strong> Files undergo binary signature / magic-byte verification. Only legitimate PDF, JPEG, and PNG files are accepted. Maximum size: 32 MB.
            </div>

            {uploadError && (
              <div style={{ padding: 10, background: 'var(--red-subtle)', color: 'var(--red)', borderRadius: 8, fontSize: 12, marginBottom: 14, border: '1px solid var(--red)' }}>
                ⚠️ {uploadError}
              </div>
            )}

            <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Associated Patient ID</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. RX-1001"
                  value={uploadPatientId}
                  onChange={(e) => setUploadPatientId(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                />
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Document Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Fundus Screening Photography - Bilateral"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Document Type</label>
                  <select
                    value={uploadDocType}
                    onChange={(e) => setUploadDocType(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                  >
                    <option value="Retinal Screening Report">Retinal Screening Report</option>
                    <option value="Specialist Consultation Note">Specialist Consultation Note</option>
                    <option value="Laboratory Summary">Laboratory Summary</option>
                    <option value="Hospital Referral Form">Hospital Referral Form</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Source Clinic / Unit</label>
                  <input
                    type="text"
                    value={uploadSource}
                    onChange={(e) => setUploadSource(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 4 }}>Select File (PDF, PNG, JPG)</label>
                <input
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={handleFileChange}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--line)', background: 'var(--surface)', fontSize: 13 }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
                <button type="button" className="btn btn-outline" onClick={() => setShowUploadModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={uploading}>
                  {uploading ? 'Validating & Uploading...' : 'Upload & Verify'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
