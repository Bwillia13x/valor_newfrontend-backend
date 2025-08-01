/**
 * Service Worker for Valor IVX PWA
 * Handles offline caching, background sync, and app updates
 */

const APP_VERSION = '1.2.0';
const CACHE_VERSION = APP_VERSION; // tie to build version
const STATIC_CACHE = `valor-ivx-static-v${CACHE_VERSION}`;
const RUNTIME_CACHE = `valor-ivx-runtime-v${CACHE_VERSION}`;
const API_CACHE = `valor-ivx-api-v${CACHE_VERSION}`;
const FALLBACK_CACHE = `valor-ivx-fallback-v${CACHE_VERSION}`;

// Files to cache for offline use
const STATIC_FILES = [
    '/',
    '/index.html',
    '/lbo.html',
    '/ma.html',
    '/real-options.html',
    '/styles.css',
    '/js/main.js',
    '/js/modules/utils.js',
    '/js/modules/backend.js',
    '/js/modules/dcf-engine.js',
    '/js/modules/lbo-engine.js',
    '/js/modules/ma-engine.js',
    '/js/modules/monte-carlo.js',
    '/js/modules/sensitivity-analysis.js',
    '/js/modules/charting.js',
    '/js/modules/scenarios.js',
    '/js/modules/financial-data.js',
    '/js/modules/ui-handlers.js',
    '/js/modules/collaboration-engine.js',
    '/js/modules/conflict-resolver.js',
    '/js/modules/advanced-charting.js',
    '/js/modules/pwa-manager.js',
    '/js/modules/video-conference.js',
    '/manifest.json'
];

// Fallback assets (should be small, always available)
const OFFLINE_FALLBACK_URL = '/index.html'; // basic offline fallback
const NOT_FOUND_FALLBACK = new Response('Not Found', { status: 404 });

/**
 * Navigation fallback for SPA routes
 */
const NAV_FALLBACK_URL = OFFLINE_FALLBACK_URL;

// Install event - cache static files
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');

  event.waitUntil(
    (async () => {
      try {
        const [staticCache, fallbackCache] = await Promise.all([
          caches.open(STATIC_CACHE),
          caches.open(FALLBACK_CACHE),
        ]);
        console.log('[SW] Caching static files');
        await staticCache.addAll(STATIC_FILES);
        // Ensure fallback page is cached
        try {
          const resp = await fetch(OFFLINE_FALLBACK_URL, { cache: 'reload' });
          if (resp.ok) await fallbackCache.put(OFFLINE_FALLBACK_URL, resp.clone());
        } catch (e) {
          console.warn('[SW] Could not prefetch fallback:', e);
        }
        console.log('[SW] Static files cached successfully');
        await self.skipWaiting();
      } catch (error) {
        console.error('[SW] Failed to cache static files:', error);
      }
    })()
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');

  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys.map((key) => {
          if (![STATIC_CACHE, RUNTIME_CACHE, API_CACHE, FALLBACK_CACHE].includes(key)) {
            console.log('[SW] Deleting old cache:', key);
            return caches.delete(key);
          }
        })
      );
      console.log('[SW] Service worker activated');
      await self.clients.claim();
    })()
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Navigation requests: SPA fallback
  if (request.mode === 'navigate') {
    event.respondWith(
      (async () => {
        try {
          const preload = await event.preloadResponse;
          if (preload) return preload;
          const network = await fetch(request);
          return network;
        } catch {
          const cache = await caches.open(STATIC_CACHE);
          const cached = await cache.match(NAV_FALLBACK_URL);
          return cached || Response.error();
        }
      })()
    );
    return;
  }

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // Handle static file requests from same origin
  if (url.origin === self.location.origin) {
    event.respondWith(handleStaticRequest(request));
    return;
  }

  // Handle external requests (financial data APIs)
  if (url.hostname.includes('alphavantage.co')) {
    event.respondWith(handleExternalRequest(request));
    return;
  }
});

/**
 * Handle API requests with offline support
 */
async function handleApiRequest(request) {
  // NetworkFirst with timeout, fallback to cache for GETs, SWR otherwise
  const isGET = request.method === 'GET';
  const cache = await caches.open(API_CACHE);

  if (isGET) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    try {
      const network = await fetch(request, { signal: controller.signal });
      clearTimeout(timeout);
      if (network && network.ok) cache.put(request, network.clone());
      const cached = await cache.match(request);
      return network.ok ? network : cached || offlineApiResponse();
    } catch (e) {
      clearTimeout(timeout);
      const cached = await cache.match(request);
      return cached || offlineApiResponse();
    }
  }

  // For non-GET (mutations), try network, no cache write
  try {
    return await fetch(request);
  } catch {
    return offlineApiResponse();
  }
}

function offlineApiResponse() {
  return new Response(
    JSON.stringify({
      success: false,
      error: 'Offline mode - data not available',
      offline: true
    }),
    {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'application/json' }
    }
  );
}

/**
 * Handle static file requests
 */
async function handleStaticRequest(request) {
  // Cache-first for static assets
  // Stale-While-Revalidate for same-origin static assets
  const cache = await caches.open(STATIC_CACHE);
  const cachedResponse = await cache.match(request);
  const fetchPromise = fetch(request)
    .then((networkResponse) => {
      if (networkResponse && networkResponse.ok) {
        cache.put(request, networkResponse.clone());
      }
      return networkResponse;
    })
    .catch(() => undefined);

  if (cachedResponse) {
    // Kick off revalidate in background
    fetchPromise.catch(() => {});
    return cachedResponse;
  }

  try {
    const network = await fetchPromise;
    if (network) return network;
  } catch (e) {
    // ignore
  }

  // Return offline page for HTML requests
  const accept = request.headers.get('accept') || '';
  if (accept.includes('text/html')) {
    const fb = await (await caches.open(FALLBACK_CACHE)).match(OFFLINE_FALLBACK_URL);
    return fb || new Response('Offline', { status: 503 });
  }
  return new Response('', { status: 504 });
}

/**
 * Handle external API requests
 */
async function handleExternalRequest(request) {
  // CacheFirst with background revalidate for third-party content
  const cache = await caches.open(RUNTIME_CACHE);
  const cached = await cache.match(request);
  const revalidate = fetch(request)
    .then((resp) => {
      if (resp && resp.ok) cache.put(request, resp.clone());
      return resp;
    })
    .catch(() => undefined);

  if (cached) {
    revalidate.catch(() => {});
    return cached;
  }

  try {
    const network = await revalidate;
    if (network) return network;
  } catch (e) {
    // ignore
  }

  return new Response(
    JSON.stringify({
      success: false,
      error: 'External API unavailable offline',
    }),
    {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'application/json' },
    }
  );
}

/**
 * Background sync for offline data
 */
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);

  if (event.tag === 'sync-offline-data') {
    event.waitUntil(syncOfflineData());
  }
});

/**
 * Sync offline data when connection is restored
 */
async function syncOfflineData() {
    try {
        // Get offline data from IndexedDB
        const offlineData = await getOfflineData();
        
        for (const item of offlineData) {
            try {
                await syncDataItem(item);
            } catch (error) {
                console.error('[SW] Failed to sync item:', error);
            }
        }
        
        console.log('[SW] Background sync completed');
    } catch (error) {
        console.error('[SW] Background sync failed:', error);
    }
}

/**
 * Get offline data from IndexedDB
 */
async function getOfflineData() {
    // This would interact with the PWA manager's IndexedDB
    // For now, return empty array
    return [];
}

/**
 * Sync individual data item
 */
async function syncDataItem(item) {
    const response = await fetch(item.url, {
        method: item.method || 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(item.data)
    });
    
    if (!response.ok) {
        throw new Error(`Sync failed: ${response.status}`);
    }
    
    return response;
}

/**
 * Push notification handling
 */
self.addEventListener('push', (event) => {
    console.log('[SW] Push notification received:', event);
    
    const options = {
        body: event.data ? event.data.text() : 'New update available',
        icon: '/icon-192x192.png',
        badge: '/icon-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'View',
                icon: '/icon-72x72.png'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/icon-72x72.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('Valor IVX', options)
    );
});

/**
 * Notification click handling
 */
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification clicked:', event);
    
    event.notification.close();
    
    if (event.action === 'explore') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

/**
 * Message handling from main thread
 */
self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);

  const data = event.data || {};
  if (data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (data.type === 'GET_VERSION') {
    event.ports[0]?.postMessage({
      version: APP_VERSION,
      caches: {
        static: STATIC_CACHE,
        runtime: RUNTIME_CACHE,
        api: API_CACHE,
        fallback: FALLBACK_CACHE,
      },
    });
  }

  if (data.type === 'CLEAR_CACHES') {
    event.waitUntil(
      (async () => {
        const keys = await caches.keys();
        await Promise.all(keys.map((k) => caches.delete(k)));
      })()
    );
  }
});

/**
 * Error handling
 */
self.addEventListener('error', (event) => {
    console.error('[SW] Service worker error:', event.error);
});

/**
 * Unhandled rejection handling
 */
self.addEventListener('unhandledrejection', (event) => {
    console.error('[SW] Unhandled rejection:', event.reason);
});
