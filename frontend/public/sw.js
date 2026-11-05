// RetinaX Care - Service Worker (Offline-First PWA)
const CACHE_NAME = 'retinax-care-v2';
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/styles.css'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
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
  
  // Do not cache API mutations or auth requests in SW
  if (request.method !== 'GET' || request.url.includes('/api/v1/auth/')) {
    return;
  }

  // Network-first with cache fallback for HTML and data
  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseClone);
          });
        }
        return response;
      })
      .catch(() => caches.match(request))
  );
});

// Background Sync Event for offline queued mutations
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-retinax-mutations') {
    event.waitUntil(
      self.clients.matchAll().then((clients) => {
        clients.forEach((client) => {
          client.postMessage({ type: 'PROCESS_OFFLINE_SYNC' });
        });
      })
    );
  }
});
