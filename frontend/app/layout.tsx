'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import './globals.css';
import { api, getCurrentUser, setCurrentUser, User, getAuthToken } from '../lib/api';
import { getPendingMutations, syncPendingMutations, getLastSyncTime } from '../lib/offline-store';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [currentUser, setUser] = useState<User | null>(null);
  const [darkMode, setDarkMode] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [pendingCount, setPendingCount] = useState(0);
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [roleMenuOpen, setRoleMenuOpen] = useState(false);
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);

  // Demo accounts
  const demoAccounts = [
    {
      role: 'Specialist' as const,
      email: 'specialist@retinax.care',
      password: 'Specialist@2026',
      name: 'Dr. Suresh Chandran, MS',
      title: 'Consultant Ophthalmologist',
      badge: 'Specialist'
    },
    {
      role: 'Care Coordinator' as const,
      email: 'coordinator@retinax.care',
      password: 'Coordinator@2026',
      name: 'Ananya Sharma',
      title: 'Lead Care Coordinator',
      badge: 'Coordinator'
    },
    {
      role: 'Administrator' as const,
      email: 'admin@retinax.care',
      password: 'Admin@2026',
      name: 'Rajiv Menon',
      title: 'Platform Administrator',
      badge: 'Admin'
    }
  ];

  // Auto-login to default Coordinator if not logged in
  useEffect(() => {
    async function initAuth() {
      const existing = getCurrentUser();
      const token = getAuthToken();
      if (existing && token) {
        setUser(existing);
      } else {
        try {
          const res = await api.login('coordinator@retinax.care', 'Coordinator@2026');
          setUser(res.user);
        } catch (e) {
          console.warn('Initial demo login fallback:', e);
        }
      }
    }
    initAuth();
  }, []);

  // Online / Offline listeners & Service Worker registration
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setIsOnline(navigator.onLine);
      const handleOnline = () => {
        setIsOnline(true);
        triggerSync();
      };
      const handleOffline = () => setIsOnline(false);

      window.addEventListener('online', handleOnline);
      window.addEventListener('offline', handleOffline);

      // Register PWA service worker
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch((err) => {
          console.warn('SW registration:', err);
        });
      }

      // Refresh pending offline mutations
      updatePendingQueue();

      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
      };
    }
  }, []);

  async function updatePendingQueue() {
    try {
      const items = await getPendingMutations();
      setPendingCount(items.length);
      const syncTime = await getLastSyncTime();
      setLastSync(syncTime);
    } catch {
      // ignore
    }
  }

  async function triggerSync() {
    try {
      const token = getAuthToken() || undefined;
      await syncPendingMutations(token);
      updatePendingQueue();
    } catch (e) {
      console.warn('Sync failed:', e);
    }
  }

  async function switchDemoRole(acc: typeof demoAccounts[0]) {
    try {
      const res = await api.login(acc.email, acc.password);
      setUser(res.user);
      setRoleMenuOpen(false);
    } catch (e: any) {
      alert(`Role switch error: ${e.message}`);
    }
  }

  function toggleTheme() {
    setDarkMode(!darkMode);
    if (!darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }

  return (
    <html lang="en">
      <head>
        <title>RetinaX Care | Closing the Loop in Diabetic Eye Care</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#0284c7" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className={darkMode ? 'dark-mode' : ''}>
        <div className="app-shell">
          {/* Offline / Sync Banner */}
          {!isOnline && (
            <div className="offline-sync-bar offline-active">
              <span>⚠️ Offline Mode Active — Updates are saved locally to IndexedDB and will sync when reconnected.</span>
              <span>{pendingCount} change(s) pending</span>
            </div>
          )}
          {isOnline && pendingCount > 0 && (
            <div className="offline-sync-bar">
              <span>📶 Online — {pendingCount} offline update(s) ready to synchronize.</span>
              <button
                className="btn btn-sm"
                style={{ background: '#0f172a', color: '#fff', marginLeft: 12, padding: '2px 10px' }}
                onClick={triggerSync}
              >
                Sync Now
              </button>
            </div>
          )}

          {/* Minimalist Topbar Header */}
          <header className="topbar">
            <div className="topbar-left" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <Link href="/" className="brand" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div className="brand-mark">
                  <svg className="brand-eye-icon" viewBox="0 0 32 32" fill="none" style={{ width: 26, height: 26, color: 'var(--primary)' }}>
                    <circle cx="16" cy="16" r="14" stroke="currentColor" strokeWidth="2" strokeDasharray="3 3" />
                    <circle cx="16" cy="16" r="9" fill="currentColor" fillOpacity="0.2" stroke="currentColor" strokeWidth="2" />
                    <circle cx="16" cy="16" r="4" fill="currentColor" />
                    <path d="M16 4v4M16 24v4M4 16h4M24 16h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                  <span className="brand-rx">RX</span>
                </div>
                <div className="brand-title">
                  RetinaX <span>Care</span>
                </div>
              </Link>

              {/* Primary Navigation Tabs */}
              <nav className="top-nav-tabs" role="tablist">
                <Link href="/" className={`nav-tab-btn ${pathname === '/' ? 'active' : ''}`}>
                  Overview
                </Link>
                <Link href="/patients" className={`nav-tab-btn ${pathname.startsWith('/patients') ? 'active' : ''}`}>
                  Patients
                </Link>
                <Link href="/followups" className={`nav-tab-btn ${pathname.startsWith('/followups') ? 'active' : ''}`}>
                  Follow-Ups
                </Link>
                <Link href="/journeys" className={`nav-tab-btn ${pathname.startsWith('/journeys') ? 'active' : ''}`}>
                  Care Journeys
                </Link>
                <Link href="/reviews" className={`nav-tab-btn ${pathname.startsWith('/reviews') ? 'active' : ''}`}>
                  Specialist Reviews
                </Link>
                <Link href="/documents" className={`nav-tab-btn ${pathname.startsWith('/documents') ? 'active' : ''}`}>
                  Documents
                </Link>
                <Link href="/analytics" className={`nav-tab-btn ${pathname.startsWith('/analytics') ? 'active' : ''}`}>
                  Insights
                </Link>
              </nav>
            </div>

            {/* Topbar Right Controls */}
            <div className="top-controls" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {/* Reset Demo Data Button */}
              <button
                className="btn btn-outline btn-sm"
                title="Reset synthetic cohort to baseline"
                style={{ fontSize: 12, padding: '4px 10px' }}
                onClick={async () => {
                  if (confirm('Reset synthetic demonstration cohort to baseline seed state?')) {
                    await api.resetCohort();
                    window.location.reload();
                  }
                }}
              >
                🔄 Reset Demo Data
              </button>

              {/* Theme Toggle */}
              <button
                id="themeToggle"
                className="header-icon-btn"
                type="button"
                title="Toggle Theme"
                onClick={toggleTheme}
                style={{ cursor: 'pointer', background: 'none', border: '1px solid var(--line)', borderRadius: '8px', padding: '6px 10px' }}
              >
                {darkMode ? '☀️' : '🌙'}
              </button>

              {/* User Profile & Demo Role Switcher */}
              <div className="user-profile-wrapper" style={{ position: 'relative' }}>
                <button
                  className="user-profile-btn"
                  onClick={() => setRoleMenuOpen(!roleMenuOpen)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    background: 'var(--surface-subtle)',
                    border: '1px solid var(--line)',
                    padding: '4px 10px',
                    borderRadius: 20,
                    cursor: 'pointer'
                  }}
                >
                  <div className="user-avatar-sm" style={{ background: 'var(--primary)', color: '#fff', borderRadius: '50%', width: 24, height: 24, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700 }}>
                    {currentUser?.role === 'Specialist' ? 'SC' : currentUser?.role === 'Administrator' ? 'RM' : 'AS'}
                  </div>
                  <span className="user-name-sm" style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink)' }}>
                    {currentUser?.full_name || 'Dr. Suresh Chandran'}
                  </span>
                  <span className="badge" style={{ fontSize: 10, padding: '2px 6px', background: 'var(--primary-subtle)', color: 'var(--primary-dark)' }}>
                    {currentUser?.role || 'Specialist'}
                  </span>
                  <span style={{ fontSize: 10 }}>▼</span>
                </button>

                {roleMenuOpen && (
                  <div
                    style={{
                      position: 'absolute',
                      right: 0,
                      top: '110%',
                      background: 'var(--surface)',
                      border: '1px solid var(--line-strong)',
                      borderRadius: 12,
                      boxShadow: '0 10px 25px rgba(0,0,0,0.15)',
                      padding: 12,
                      zIndex: 10000,
                      minWidth: 260
                    }}
                  >
                    <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 8 }}>
                      Switch Demonstration Role
                    </div>
                    {demoAccounts.map((acc) => (
                      <div
                        key={acc.email}
                        onClick={() => switchDemoRole(acc)}
                        style={{
                          padding: '8px 10px',
                          borderRadius: 8,
                          cursor: 'pointer',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          background: currentUser?.role === acc.role ? 'var(--primary-subtle)' : 'transparent',
                          marginBottom: 4
                        }}
                      >
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink)' }}>{acc.name}</div>
                          <div style={{ fontSize: 11, color: 'var(--muted)' }}>{acc.title}</div>
                        </div>
                        <span className="badge" style={{ fontSize: 10 }}>{acc.badge}</span>
                      </div>
                    ))}
                    <div style={{ borderTop: '1px solid var(--line)', marginTop: 8, paddingTop: 8, fontSize: 11, color: 'var(--muted)' }}>
                      Strict backend RBAC enforced.
                    </div>
                  </div>
                )}
              </div>
            </div>
          </header>

          {/* Main App Content Viewport */}
          <main className="main-content" style={{ flex: 1, padding: '20px 24px' }}>
            {children}
          </main>

          {/* Mandatory Non-Clinical Scope Disclaimer Footer */}
          <footer
            style={{
              background: 'var(--surface)',
              borderTop: '1px solid var(--line)',
              padding: '14px 24px',
              fontSize: '12px',
              color: 'var(--muted)',
              display: 'flex',
              flexDirection: 'column',
              gap: 4,
              textAlign: 'center'
            }}
          >
            <div>
              <strong>RetinaX Care — Closing the Loop in Diabetic Eye Care</strong> • Health-a-thon 2026 (Diabetes Care & RSSDI Track)
            </div>
            <div style={{ color: 'var(--ink-secondary)', maxWidth: 900, margin: '0 auto', fontSize: 11, lineHeight: 1.4 }}>
              <strong>Scope Notice:</strong> RetinaX Care supports operational care coordination, milestone tracking, and clinician-directed follow-up.
              It does NOT provide diagnosis, disease grading (DR 0–4), clinical risk assessment, treatment recommendations, or autonomous clinical decision-making.
              All medical judgments remain the sole responsibility of qualified healthcare professionals.
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
