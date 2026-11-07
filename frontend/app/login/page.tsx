'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, setCurrentUser } from '../../lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await api.login({ email: email.trim(), password });
      // Update client user metadata (Strict cookie session; no tokens stored in localStorage)
      setCurrentUser(res.user);
      router.push('/');
      router.refresh();
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  }

  const fillDemoAccount = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError(null);
  };

  return (
    <div style={{
      minHeight: '80vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px 16px'
    }}>
      <div style={{
        width: '100%',
        maxWidth: 440,
        background: 'var(--surface-card)',
        borderRadius: 16,
        border: '1px solid var(--line)',
        padding: 32,
        boxShadow: '0 8px 30px rgba(0,0,0,0.06)'
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 48,
            height: 48,
            borderRadius: 12,
            background: 'var(--teal)',
            color: '#fff',
            fontSize: 24,
            fontWeight: 800,
            marginBottom: 12
          }}>
            Rx
          </div>
          <h1 style={{ fontSize: 22, fontWeight: 700, margin: '0 0 6px', color: 'var(--ink)' }}>
            RetinaX Care
          </h1>
          <p style={{ margin: 0, fontSize: 13, color: 'var(--muted)' }}>
            Closing the Loop in Diabetic Eye Care
          </p>
        </div>

        {/* Operational Notice */}
        <div style={{
          background: 'var(--surface-subtle)',
          borderLeft: '3px solid var(--teal)',
          padding: '10px 12px',
          borderRadius: 6,
          fontSize: 11,
          color: 'var(--ink-secondary)',
          marginBottom: 20,
          lineHeight: 1.4
        }}>
          <strong>Health-a-thon 2026 Portal:</strong> Operational screening follow-up & care-continuity tracking. Strictly non-clinical; no autonomous diagnostic AI.
        </div>

        {error && (
          <div style={{
            background: 'var(--rose-subtle)',
            color: 'var(--rose)',
            padding: '10px 14px',
            borderRadius: 8,
            fontSize: 12,
            marginBottom: 16,
            fontWeight: 500
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 4, color: 'var(--ink)' }}>
              Email or Username
            </label>
            <input
              type="text"
              required
              autoComplete="username"
              placeholder="e.g. coordinator@retinax.care"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: 8,
                border: '1px solid var(--line)',
                fontSize: 13,
                background: 'var(--surface)'
              }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--ink)' }}>
                Password
              </label>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--teal)',
                  fontSize: 11,
                  cursor: 'pointer',
                  padding: 0
                }}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
            <input
              type={showPassword ? 'text' : 'password'}
              required
              autoComplete="current-password"
              placeholder="Enter secure password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: 8,
                border: '1px solid var(--line)',
                fontSize: 13,
                background: 'var(--surface)'
              }}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{
              width: '100%',
              padding: '10px 0',
              fontSize: 14,
              fontWeight: 600,
              marginTop: 6
            }}
          >
            {loading ? 'Authenticating...' : 'Sign In to Care Portal'}
          </button>
        </form>

        {/* Development & Evaluation Presets - hidden in production */}
        {process.env.NEXT_PUBLIC_ENVIRONMENT !== 'production' && (
          <div style={{ marginTop: 24, paddingTop: 18, borderTop: '1px solid var(--line)' }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Health-a-thon Evaluation Credentials
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => fillDemoAccount('coordinator@retinax.care', 'Coordinator@2026')}
                style={{ fontSize: 11, textAlign: 'left', display: 'flex', justifyContent: 'space-between' }}
              >
                <span><strong>Care Coordinator</strong> (Ananya Sharma)</span>
                <span style={{ color: 'var(--muted)' }}>Fill →</span>
              </button>
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => fillDemoAccount('specialist@retinax.care', 'Specialist@2026')}
                style={{ fontSize: 11, textAlign: 'left', display: 'flex', justifyContent: 'space-between' }}
              >
                <span><strong>Retina Specialist</strong> (Dr. Suresh Chandran)</span>
                <span style={{ color: 'var(--muted)' }}>Fill →</span>
              </button>
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => fillDemoAccount('admin@retinax.care', 'Admin@2026')}
                style={{ fontSize: 11, textAlign: 'left', display: 'flex', justifyContent: 'space-between' }}
              >
                <span><strong>Platform Admin</strong> (Rajiv Menon)</span>
                <span style={{ color: 'var(--muted)' }}>Fill →</span>
              </button>
            </div>
            <div style={{ fontSize: 10, color: 'var(--muted)', marginTop: 8, textAlign: 'center' }}>
              Pre-configured seed credentials for competition judging and non-production testing.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
