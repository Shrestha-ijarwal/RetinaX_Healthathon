'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import './globals.css';
import { api, getCurrentUser, setCurrentUser, User, clearCurrentUser } from '../lib/api';
import {
  getPendingMutations,
  syncPendingMutations,
  getLastSyncTime,
  getConflictMutations,
  resolveConflict,
  OfflineMutation
} from '../lib/offline-store';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [currentUser, setUser] = useState<User | null>(null);
  const [darkMode, setDarkMode] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [pendingCount, setPendingCount] = useState(0);
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [conflicts, setConflicts] = useState<OfflineMutation[]>([]);
  const [activeConflict, setActiveConflict] = useState<OfflineMutation | null>(null);

  // Authenticate session via secure HttpOnly cookie session (No localStorage token exposure)
  useEffect(() => {
    async function verifyAuth() {
      const cached = getCurrentUser();
      if (cached) {
        setUser(cached);
      }
      try {
        const profile = await api.getMe();
        setUser(profile);
        setCurrentUser(profile);
      } catch {
        // Session expired or unauthenticated
        clearCurrentUser();
        setUser(null);
      }
    }
    verifyAuth();
  }, [pathname]);

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

      // Register PWA service worker with message listener for background sync
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.addEventListener('message', (event) => {
          if (event.data?.type === 'PROCESS_OFFLINE_SYNC') {
            triggerSync();
          }
        });

        navigator.serviceWorker.register('/sw.js').catch((err) => {
          console.warn('SW registration:', err);
        });
      }

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
      const conflictItems = await getConflictMutations();
      setConflicts(conflictItems);
      if (conflictItems.length > 0 && !activeConflict) {
        setActiveConflict(conflictItems[0]);
      }
    } catch {
      // ignore
    }
  }

  async function triggerSync() {
    try {
      await syncPendingMutations();
      await updatePendingQueue();
    } catch (e) {
      console.warn('Sync failed:', e);
    }
  }

  async function handleLogout() {
    await api.logout();
    setUser(null);
    setUserMenuOpen(false);
    router.push('/login');
    router.refresh();
  }

  async function handleResolveConflict(action: 'keep_local' | 'keep_server' | 'dismiss') {
    if (!activeConflict) return;
    if (action === 'keep_local') {
      const confirmed = window.confirm(
        'Confirm Overwrite: Are you sure you want to overwrite the server record with your offline changes? This will submit a new operation with the latest version.'
      );
      if (!confirmed) return;
    }
    const latestServerVersion = (activeConflict.conflictData?.server as any)?.current_version;
    await resolveConflict(activeConflict.id, action, latestServerVersion);
    setActiveConflict(null);
    await updatePendingQueue();
    if (action !== 'dismiss') {
      await triggerSync();
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

  const getRoleBadge = (role?: string) => {
    switch (role) {
      case 'Specialist':
        return { label: 'Specialist', bg: 'var(--indigo-subtle)', color: 'var(--indigo)' };
      case 'Care Coordinator':
        return { label: 'Coordinator', bg: 'var(--teal-subtle)', color: 'var(--teal)' };
      case 'Administrator':
        return { label: 'Admin', bg: 'var(--rose-subtle)', color: 'var(--rose)' };
      default:
        return { label: 'Guest', bg: 'var(--surface-subtle)', color: 'var(--muted)' };
    }
  };

  const badge = getRoleBadge(currentUser?.role);

  return (
    <html lang="en">
      <head>
        <title>RetinaX Care | Closing the Loop in Diabetic Eye Care</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#0d9488" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className={darkMode ? 'dark-mode' : ''}>
        <div className="app-shell">
          {/* Offline / Sync Notification Bar */}
          {!isOnline && (
            <div className="offline-sync-bar offline-active">
              <span>⚠️ Offline Mode Active — Operational updates are saved securely to IndexedDB and will synchronize upon reconnection.</span>
              <span>{pendingCount} change(s) queued</span>
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

          {/* Conflict Resolution Banner */}
          {conflicts.length > 0 && activeConflict && (
            <div style={{
              background: 'var(--amber-subtle)',
              borderBottom: '2px solid var(--amber)',
              padding: '10px 24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: 12,
              color: 'var(--ink)'
            }}>
              <div>
                <strong>⚠️ Concurrency Conflict Detected:</strong> A server record was modified while update{' '}
                <code>{activeConflict.id.substring(0, 8)}...</code> ({activeConflict.description}) was queued offline.
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  className="btn btn-sm btn-outline"
                  style={{ fontSize: 11, padding: '2px 8px' }}
                  onClick={() => handleResolveConflict('keep_server')}
                >
                  Accept Server Record
                </button>
                <button
                  className="btn btn-sm btn-primary"
                  style={{ fontSize: 11, padding: '2px 8px' }}
                  onClick={() => handleResolveConflict('keep_local')}
                >
                  Overwrite with Local
                </button>
                <button
                  className="btn btn-sm"
                  style={{ fontSize: 11, padding: '2px 8px', background: 'none' }}
                  onClick={() => handleResolveConflict('dismiss')}
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}

          {/* Minimalist Topbar Header */}
          <header className="topbar">
            <div className="topbar-left" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <Link href="/" className="brand" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div className="brand-mark">
                  <svg className="brand-eye-icon" viewBox="0 0 32 32" fill="none" style={{ width: 26, height: 26, color: 'var(--teal)' }}>
                    <circle cx="16" cy="16" r="14" stroke="currentColor" strokeWidth="2" strokeDasharray="3 3" />
                    <circle cx="16" cy="16" r="9" fill="currentColor" fillOpacity="0.2" stroke="currentColor" strokeWidth="2" />
                    <circle cx="16" cy="16" r="4" fill="currentColor" />
                    <path d="M16 4v4M16 24v4M4 16h4M24 16h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                  <span className="brand-rx">Rx</span>
                </div>
                <div className="brand-title">
                  RetinaX <span>Care</span>
                </div>
              </Link>
              <div className="tagline-pill">Closing the Loop in Diabetic Eye Care</div>
            </div>

            {/* Top Navigation Links */}
            <nav className="top-nav" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Link href="/patients" className={`nav-link ${pathname.startsWith('/patients') ? 'active' : ''}`}>
                Patients
              </Link>
              <Link href="/journeys" className={`nav-link ${pathname.startsWith('/journeys') ? 'active' : ''}`}>
                Care Journeys
              </Link>
              <Link href="/reviews" className={`nav-link ${pathname.startsWith('/reviews') ? 'active' : ''}`}>
                Specialist Reviews
              </Link>
              <Link href="/followups" className={`nav-link ${pathname.startsWith('/followups') ? 'active' : ''}`}>
                Follow-Ups
              </Link>
              <Link href="/documents" className={`nav-link ${pathname.startsWith('/documents') ? 'active' : ''}`}>
                Documents
              </Link>
              <Link href="/analytics" className={`nav-link ${pathname.startsWith('/analytics') ? 'active' : ''}`}>
                Continuity Insights
              </Link>
            </nav>

            {/* Actions & Session Profile Menu */}
            <div className="topbar-right" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {/* Dark mode toggle */}
              <button
                className="icon-btn"
                onClick={toggleTheme}
                title="Toggle Theme"
                style={{ background: 'none', border: '1px solid var(--line)', borderRadius: '8px', padding: '6px 10px', cursor: 'pointer' }}
              >
                {darkMode ? '☀️' : '🌙'}
              </button>

              {/* User Session Profile & Role Picker */}
              <div style={{ position: 'relative' }}>
                {currentUser ? (
                  <button
                    className="user-profile-btn"
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '4px 10px',
                      background: 'var(--surface-card)',
                      border: '1px solid var(--line)',
                      borderRadius: '20px',
                      cursor: 'pointer'
                    }}
                  >
                    <span
                      style={{
                        fontSize: '11px',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        background: badge.bg,
                        color: badge.color,
                        fontWeight: 600
                      }}
                    >
                      {badge.label}
                    </span>
                    <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--ink)' }}>
                      {currentUser.full_name}
                    </span>
                    <span style={{ fontSize: '10px', color: 'var(--muted)' }}>▼</span>
                  </button>
                ) : (
                  <Link
                    href="/login"
                    className="btn btn-sm btn-primary"
                    style={{ textDecoration: 'none', padding: '6px 14px', fontSize: '12px', fontWeight: 600 }}
                  >
                    Sign In
                  </Link>
                )}

                {/* Profile Dropdown Menu */}
                {userMenuOpen && currentUser && (
                  <div
                    style={{
                      position: 'absolute',
                      right: 0,
                      top: '110%',
                      width: 260,
                      background: 'var(--surface-card)',
                      border: '1px solid var(--line)',
                      borderRadius: 12,
                      boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
                      zIndex: 100,
                      padding: '12px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 8
                    }}
                  >
                    <div style={{ paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink)' }}>{currentUser.full_name}</div>
                      <div style={{ fontSize: 11, color: 'var(--muted)' }}>{currentUser.email}</div>
                      <div style={{ fontSize: 11, color: badge.color, fontWeight: 500, marginTop: 2 }}>{currentUser.role}</div>
                    </div>

                    <Link
                      href="/login"
                      onClick={() => setUserMenuOpen(false)}
                      style={{
                        fontSize: 12,
                        textDecoration: 'none',
                        color: 'var(--ink)',
                        padding: '6px 8px',
                        borderRadius: 6,
                        background: 'var(--surface-subtle)'
                      }}
                    >
                      🔄 Switch Evaluation Account
                    </Link>

                    <button
                      onClick={handleLogout}
                      style={{
                        fontSize: 12,
                        color: 'var(--rose)',
                        background: 'none',
                        border: 'none',
                        padding: '6px 8px',
                        textAlign: 'left',
                        cursor: 'pointer',
                        borderRadius: 6
                      }}
                    >
                      🚪 Sign Out
                    </button>
                  </div>
                )}
              </div>
            </div>
          </header>

          {/* Main Body View */}
          <main className="main-content" style={{ minHeight: 'calc(100vh - 120px)' }}>
            {children}
          </main>

          {/* Persistent Healthcare Scope Disclaimer Footer */}
          <footer className="footer-bar" style={{
            padding: '16px 24px',
            borderTop: '1px solid var(--line)',
            fontSize: '11px',
            color: 'var(--muted)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'var(--surface)'
          }}>
            <div>
              <strong>RetinaX Care:</strong> Closing the Loop in Diabetic Eye Care (Diabetic Retinopathy Screening Follow-up & Continuity of Care).
            </div>
            <div>
              <strong>Operational Care Continuity Platform:</strong> Strictly non-clinical. Excludes diagnosis, grading (DR 0–4), and clinical risk scoring.
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
