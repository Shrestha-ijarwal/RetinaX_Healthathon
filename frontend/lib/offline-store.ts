// RetinaX Care - IndexedDB Offline Storage & Synchronization Engine (V3)
// Cryptographic UUID Idempotency, Concurrency Control, Background Sync & Safe Conflict Resolution

import { getAuthToken } from './api';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export interface OfflineMutation {
  id: string; // Cryptographic UUID
  operationType: string;
  resourceId?: string;
  endpoint: string;
  method: 'POST' | 'PATCH' | 'PUT';
  payload: any;
  timestamp: string;
  description: string;
  status: 'pending' | 'syncing' | 'failed' | 'synced' | 'conflict';
  retryCount: number;
  serverVersion?: number | string;
  csrfToken?: string;
  conflictData?: {
    local: any;
    server: any;
    message: string;
  };
  errorMessage?: string;
}

const DB_NAME = 'retinax_care_offline_db';
const DB_VERSION = 3;

export function generateSecureUUID(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    bytes[6] = (bytes[6] & 0x0f) | 0x40; // Version 4
    bytes[8] = (bytes[8] & 0x3f) | 0x80; // Variant 10
    const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function getCsrfFromCookie(): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(^| )retinax_csrf_token=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined') {
      return reject(new Error('IndexedDB not supported in SSR'));
    }
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (e) => {
      const db = (e.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains('offline_mutations')) {
        db.createObjectStore('offline_mutations', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('metadata')) {
        db.createObjectStore('metadata', { keyPath: 'key' });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function queueOfflineMutation(
  operationType: string,
  endpoint: string,
  method: 'POST' | 'PATCH' | 'PUT',
  payload: any,
  description: string,
  resourceId?: string,
  serverVersion?: number | string
): Promise<OfflineMutation> {
  const db = await openDB();
  const csrf = getCsrfFromCookie();

  // Ensure expected_version is populated in payload if serverVersion is provided
  const adjustedPayload = { ...(payload || {}) };
  if (serverVersion !== undefined && adjustedPayload.expected_version === undefined) {
    adjustedPayload.expected_version = typeof serverVersion === 'number'
      ? serverVersion
      : parseInt(String(serverVersion), 10);
  }

  const mutation: OfflineMutation = {
    id: generateSecureUUID(),
    operationType,
    resourceId,
    endpoint,
    method,
    payload: adjustedPayload,
    timestamp: new Date().toISOString(),
    description,
    status: 'pending',
    retryCount: 0,
    serverVersion,
    csrfToken: csrf || undefined
  };

  // Persist CSRF token into metadata store for autonomous Service Worker background access
  if (csrf) {
    try {
      const metaTx = db.transaction('metadata', 'readwrite');
      metaTx.objectStore('metadata').put({ key: 'csrf_token', value: csrf });
    } catch {}
  }

  return new Promise((resolve, reject) => {
    const tx = db.transaction('offline_mutations', 'readwrite');
    const store = tx.objectStore('offline_mutations');
    const req = store.add(mutation);
    req.onsuccess = () => {
      registerBackgroundSync();
      resolve(mutation);
    };
    req.onerror = () => reject(req.error);
  });
}

export async function getPendingMutations(): Promise<OfflineMutation[]> {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('offline_mutations', 'readonly');
      const store = tx.objectStore('offline_mutations');
      const req = store.getAll();
      req.onsuccess = () => {
        const items: OfflineMutation[] = req.result || [];
        resolve(items.filter((i) => i.status === 'pending' || i.status === 'failed' || i.status === 'conflict'));
      };
      req.onerror = () => reject(req.error);
    });
  } catch {
    return [];
  }
}

export async function getConflictMutations(): Promise<OfflineMutation[]> {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('offline_mutations', 'readonly');
      const store = tx.objectStore('offline_mutations');
      const req = store.getAll();
      req.onsuccess = () => {
        const items: OfflineMutation[] = req.result || [];
        resolve(items.filter((i) => i.status === 'conflict'));
      };
      req.onerror = () => reject(req.error);
    });
  } catch {
    return [];
  }
}

export async function resolveConflict(
  mutationId: string,
  resolution: 'keep_server' | 'keep_local' | 'dismiss',
  latestServerVersion?: number | string
): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('offline_mutations', 'readwrite');
    const store = tx.objectStore('offline_mutations');
    const req = store.get(mutationId);

    req.onsuccess = async () => {
      const mut: OfflineMutation = req.result;
      if (!mut) return resolve();

      if (resolution === 'keep_server') {
        // Discard local changes, server state wins
        store.delete(mutationId);
        return resolve();
      }

      if (resolution === 'dismiss') {
        // Do not delete local changes; keep pending sync status
        mut.status = 'conflict';
        store.put(mut);
        return resolve();
      }

      if (resolution === 'keep_local') {
        // Overwrite: create a fresh mutation with NEW idempotency key and updated server version
        const newKey = generateSecureUUID();
        const updatedPayload = { ...mut.payload };
        if (latestServerVersion !== undefined) {
          updatedPayload.expected_version = latestServerVersion;
        }

        // Delete old conflicting mutation
        store.delete(mutationId);

        // Insert new mutation for immediate sync
        const newMut: OfflineMutation = {
          ...mut,
          id: newKey,
          payload: updatedPayload,
          serverVersion: latestServerVersion,
          status: 'pending',
          retryCount: 0,
          conflictData: undefined,
          errorMessage: undefined,
          timestamp: new Date().toISOString()
        };
        store.add(newMut);
        registerBackgroundSync();
        return resolve();
      }
      resolve();
    };
    req.onerror = () => reject(req.error);
  });
}

export async function registerBackgroundSync(): Promise<boolean> {
  if (typeof window === 'undefined') return false;
  if ('serviceWorker' in navigator && 'SyncManager' in window) {
    try {
      const registration = await navigator.serviceWorker.ready;
      await (registration as any).sync.register('retinax-offline-sync');
      return true;
    } catch {
      return false;
    }
  }
  return false;
}

export async function syncPendingMutations(): Promise<{ synced: number; conflicts: number; failed: number }> {
  const pending = await getPendingMutations();
  const executable = pending.filter((m) => m.status === 'pending' || (m.status === 'failed' && m.retryCount < 5));
  if (executable.length === 0) {
    const conflicts = pending.filter((m) => m.status === 'conflict').length;
    return { synced: 0, conflicts, failed: 0 };
  }

  const db = await openDB();
  let synced = 0;
  let conflicts = 0;
  let failed = 0;

  for (const mut of executable) {
    try {
      mut.status = 'syncing';
      const csrf = getCsrfFromCookie() || mut.csrfToken;
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'X-Idempotency-Key': mut.id,
      };
      if (csrf) {
        headers['X-CSRF-Token'] = csrf;
      }
      if (mut.serverVersion !== undefined) {
        headers['X-Expected-Version'] = String(mut.serverVersion);
      }

      const payloadToSend = { ...(mut.payload || {}) };
      if (mut.serverVersion !== undefined && payloadToSend.expected_version === undefined) {
        payloadToSend.expected_version = typeof mut.serverVersion === 'number'
          ? mut.serverVersion
          : parseInt(String(mut.serverVersion), 10);
      }

      const authToken = getAuthToken();
      if (authToken && !headers['Authorization']) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const targetUrl = mut.endpoint.startsWith('http') ? mut.endpoint : `${BASE_URL}${mut.endpoint}`;

      const res = await fetch(targetUrl, {
        method: mut.method,
        headers,
        credentials: 'include',
        body: JSON.stringify(payloadToSend)
      });

      if (res.ok) {
        mut.status = 'synced';
        synced++;
        const tx = db.transaction('offline_mutations', 'readwrite');
        tx.objectStore('offline_mutations').delete(mut.id);
      } else if (res.status === 401 || res.status === 403) {
        // Authentication error - preserve mutation so it is not lost
        let errJson: any = {};
        try {
          errJson = await res.json();
        } catch {}
        mut.status = 'failed';
        mut.errorMessage = errJson.detail || `Authentication required (HTTP ${res.status}). Record preserved for login.`;
        failed++;
        const tx = db.transaction('offline_mutations', 'readwrite');
        tx.objectStore('offline_mutations').put(mut);
      } else if (res.status === 409) {
        let serverData: any = {};
        try {
          serverData = await res.json();
        } catch {
          serverData = { detail: 'Server record has updated concurrently.' };
        }
        mut.status = 'conflict';
        mut.conflictData = {
          local: mut.payload,
          server: serverData.detail || serverData,
          message: 'Conflict detected: Server record was modified while this update was queued offline.'
        };
        conflicts++;
        const tx = db.transaction('offline_mutations', 'readwrite');
        tx.objectStore('offline_mutations').put(mut);
      } else if (res.status >= 400 && res.status < 500) {
        // Permanent client error (validation / authorization) -> do not retry indefinitely
        mut.status = 'failed';
        mut.retryCount = 5;
        let errJson: any = {};
        try {
          errJson = await res.json();
        } catch {}
        mut.errorMessage = errJson.detail || `Server returned permanent error HTTP ${res.status}`;
        failed++;
        const tx = db.transaction('offline_mutations', 'readwrite');
        tx.objectStore('offline_mutations').put(mut);
      } else {
        // Transient error (5xx or network) -> bounded exponential retry
        mut.retryCount = (mut.retryCount || 0) + 1;
        mut.status = mut.retryCount >= 5 ? 'failed' : 'pending';
        mut.errorMessage = `Transient server error HTTP ${res.status}`;
        failed++;
        const tx = db.transaction('offline_mutations', 'readwrite');
        tx.objectStore('offline_mutations').put(mut);
      }
    } catch (err: any) {
      mut.retryCount = (mut.retryCount || 0) + 1;
      mut.status = mut.retryCount >= 5 ? 'failed' : 'pending';
      mut.errorMessage = err.message || 'Network error during sync';
      failed++;
      const tx = db.transaction('offline_mutations', 'readwrite');
      tx.objectStore('offline_mutations').put(mut);
    }
  }

  try {
    const tx = db.transaction('metadata', 'readwrite');
    tx.objectStore('metadata').put({ key: 'last_sync_time', value: new Date().toISOString() });
  } catch {}

  return { synced, conflicts, failed };
}

export async function getLastSyncTime(): Promise<string | null> {
  try {
    const db = await openDB();
    return new Promise((resolve) => {
      const tx = db.transaction('metadata', 'readonly');
      const req = tx.objectStore('metadata').get('last_sync_time');
      req.onsuccess = () => resolve(req.result ? req.result.value : null);
      req.onerror = () => resolve(null);
    });
  } catch {
    return null;
  }
}
