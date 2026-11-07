// RetinaX Care - Service Worker (Hardened Healthcare PWA)
// Compliant with healthcare data privacy: Caches ONLY public static shell assets.
// NEVER caches patient, review, follow-up, or document API responses.

const CACHE_NAME = 'retinax-care-v4';
const STATIC_ASSETS = [
  '/',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Use allSettled so that missing optional assets never abort SW installation
      return Promise.allSettled(
        STATIC_ASSETS.map((asset) => cache.add(asset).catch((err) => console.warn(`Precache skipped: ${asset}`, err)))
      );
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 1. STRICT NETWORK-ONLY POLICY FOR ALL SENSITIVE APIS & AUTH
  // Never cache patient records, specialist reviews, documents, follow-ups, or credentials
  if (url.pathname.startsWith('/api/') || request.method !== 'GET') {
    event.respondWith(fetch(request));
    return;
  }

  // 2. Cache-first strategy for immutable Next.js static bundles and fonts
  if (url.pathname.startsWith('/_next/static/') || url.pathname.includes('/fonts/')) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          if (response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        });
      })
    );
    return;
  }

  // 3. Network-first with cache fallback for HTML pages (App Shell)
  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response.status === 200 && response.type === 'basic') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return response;
      })
      .catch(() => caches.match(request).then((res) => res || caches.match('/')))
  );
});

// Background Sync Event for offline queued mutations
// Supports autonomous processing when no pages are open, and foreground notification when pages exist.
const DB_NAME = 'retinax_care_offline_db';
const DB_VERSION = 3;

function openOfflineDB() {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') return reject(new Error('IndexedDB unavailable in ServiceWorker'));
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function processOfflineQueueAutonomously() {
  try {
    const db = await openOfflineDB();

    // Retrieve cached CSRF token from metadata store if available
    let storedCsrf = null;
    try {
      const metaTx = db.transaction('metadata', 'readonly');
      const metaStore = metaTx.objectStore('metadata');
      const csrfEntry = await new Promise((res) => {
        const req = metaStore.get('csrf_token');
        req.onsuccess = () => res(req.result ? req.result.value : null);
        req.onerror = () => res(null);
      });
      storedCsrf = csrfEntry;
    } catch (_) {}

    const tx = db.transaction('offline_mutations', 'readonly');
    const store = tx.objectStore('offline_mutations');
    const allMutations = await new Promise((res, rej) => {
      const getReq = store.getAll();
      getReq.onsuccess = () => res(getReq.result || []);
      getReq.onerror = () => rej(getReq.error);
    });

    const executable = allMutations.filter(
      (m) => m.status === 'pending' || (m.status === 'failed' && m.retryCount < 5)
    );

    for (const mut of executable) {
      try {
        const headers = {
          'Content-Type': 'application/json',
          'X-Idempotency-Key': mut.id,
        };

        const csrf = mut.csrfToken || storedCsrf;
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

        const res = await fetch(mut.endpoint, {
          method: mut.method,
          headers,
          credentials: 'include',
          body: JSON.stringify(payloadToSend)
        });

        const writeTx = db.transaction('offline_mutations', 'readwrite');
        const writeStore = writeTx.objectStore('offline_mutations');

        if (res.ok) {
          writeStore.delete(mut.id);
        } else if (res.status === 401 || res.status === 403) {
          // Authentication error - preserve mutation for when coordinator logs back in
          let errDetail = {};
          try { errDetail = await res.json(); } catch (_) {}
          mut.status = 'failed';
          mut.errorMessage = errDetail.detail || `Authentication required (HTTP ${res.status}). Record preserved for login.`;
          writeStore.put(mut);
        } else if (res.status === 409) {
          // Concurrency conflict - record without discarding data
          let conflictDetail = {};
          try { conflictDetail = await res.json(); } catch (_) {}
          mut.status = 'conflict';
          mut.conflictData = {
            local: mut.payload,
            server: conflictDetail.detail || conflictDetail,
            message: 'Conflict detected during autonomous background sync: server version mismatch.'
          };
          writeStore.put(mut);
        } else if (res.status >= 400 && res.status < 500) {
          // Client / validation failure - preserve record with error details
          let errDetail = {};
          try { errDetail = await res.json(); } catch (_) {}
          mut.status = 'failed';
          mut.retryCount = 5;
          mut.errorMessage = errDetail.detail || `Client error HTTP ${res.status}`;
          writeStore.put(mut);
        } else {
          // 5xx transient server error
          mut.retryCount = (mut.retryCount || 0) + 1;
          mut.status = mut.retryCount >= 5 ? 'failed' : 'pending';
          mut.errorMessage = `Transient server error HTTP ${res.status}`;
          writeStore.put(mut);
        }
      } catch (err) {
        const writeTx = db.transaction('offline_mutations', 'readwrite');
        const writeStore = writeTx.objectStore('offline_mutations');
        mut.retryCount = (mut.retryCount || 0) + 1;
        mut.status = mut.retryCount >= 5 ? 'failed' : 'pending';
        mut.errorMessage = err.message || 'Autonomous network failure';
        writeStore.put(mut);
      }
    }
  } catch (err) {
    console.warn('[RetinaX SW] Autonomous background sync error:', err);
  }
}

self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-retinax-mutations' || event.tag === 'retinax-offline-sync') {
    event.waitUntil(
      self.clients.matchAll().then((clients) => {
        if (clients && clients.length > 0) {
          clients.forEach((client) => {
            client.postMessage({ type: 'PROCESS_OFFLINE_SYNC' });
          });
        } else {
          // Autonomous background sync without open window where browser allows
          return processOfflineQueueAutonomously();
        }
      })
    );
  }
});
