/**
 * Enhanced Service Worker for Valor IVX PWA - Phase 5
 * Advanced offline caching, background sync, push notifications, and performance optimizations
 */

const APP_VERSION = '1.3.0';
const CACHE_VERSION = APP_VERSION;
const STATIC_CACHE = `valor-ivx-static-v${CACHE_VERSION}`;
const RUNTIME_CACHE = `valor-ivx-runtime-v${CACHE_VERSION}`;
const API_CACHE = `valor-ivx-api-v${CACHE_VERSION}`;
const FALLBACK_CACHE = `valor-ivx-fallback-v${CACHE_VERSION}`;
const DATA_CACHE = `valor-ivx-data-v${CACHE_VERSION}`;

// Enhanced cache strategies
const CACHE_STRATEGIES = {
  STATIC: 'cache-first',
  API: 'network-first',
  DATA: 'stale-while-revalidate',
  FALLBACK: 'cache-only'
};

// Files to cache for offline use (enhanced list)
const STATIC_FILES = [
    '/',
    '/index.html',
    '/lbo.html',
    '/ma.html',
    '/real-options.html',
    '/analytics.html',
    '/styles.css',
    '/manifest.json',
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
    '/js/modules/error-handler.js',
    '/js/modules/performance-optimizer.js',
    '/js/modules/accessibility-manager.js',
    '/js/modules/analytics.js',
    '/js/modules/analytics-dashboard.js',
    '/js/modules/realtime.js',
    '/js/modules/version-control.js',
    '/js/modules/real-options.js'
];

// API endpoints to cache
const API_ENDPOINTS = [
    '/api/dcf/runs',
    '/api/dcf/scenarios',
    '/api/lbo/runs',
    '/api/lbo/scenarios',
    '/api/ma/runs',
    '/api/ma/scenarios',
    '/api/real-options/runs',
    '/api/analytics/revenue-prediction',
    '/api/analytics/portfolio-optimization'
];

// Fallback assets
const OFFLINE_FALLBACK_URL = '/index.html';
const NOT_FOUND_FALLBACK = new Response('Not Found', { status: 404 });

// Navigation fallback for SPA routes
const NAV_FALLBACK_URL = OFFLINE_FALLBACK_URL;

// Background sync queue
let backgroundSyncQueue = [];

/**
 * Install event - enhanced caching with versioning
 */
self.addEventListener('install', (event) => {
  console.log('[SW] Installing enhanced service worker...');

  event.waitUntil(
    (async () => {
      try {
        // Open all caches
        const [staticCache, fallbackCache, dataCache] = await Promise.all([
          caches.open(STATIC_CACHE),
          caches.open(FALLBACK_CACHE),
          caches.open(DATA_CACHE)
        ]);

        console.log('[SW] Caching static files');
        
        // Cache static files with better error handling
        const cachePromises = STATIC_FILES.map(async (file) => {
          try {
            const response = await fetch(file, { cache: 'reload' });
            if (response.ok) {
              await staticCache.put(file, response.clone());
            }
          } catch (error) {
            console.warn(`[SW] Failed to cache ${file}:`, error);
          }
        });

        await Promise.all(cachePromises);

        // Cache fallback page
        try {
          const resp = await fetch(OFFLINE_FALLBACK_URL, { cache: 'reload' });
          if (resp.ok) {
            await fallbackCache.put(OFFLINE_FALLBACK_URL, resp.clone());
          }
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

/**
 * Activate event - enhanced cleanup with cache versioning
 */
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating enhanced service worker...');

  event.waitUntil(
    (async () => {
      try {
        const keys = await caches.keys();
        const currentCaches = [STATIC_CACHE, RUNTIME_CACHE, API_CACHE, FALLBACK_CACHE, DATA_CACHE];
        
        await Promise.all(
          keys.map((key) => {
            if (!currentCaches.includes(key)) {
              console.log('[SW] Deleting old cache:', key);
              return caches.delete(key);
            }
          })
        );

        // Clear old IndexedDB data
        await clearOldIndexedDBData();

        console.log('[SW] Enhanced service worker activated');
        await self.clients.claim();
      } catch (error) {
        console.error('[SW] Activation failed:', error);
      }
    })()
  );
});

/**
 * Enhanced fetch event with multiple strategies
 */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Handle different types of requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
  } else if (isStaticAsset(url.pathname)) {
    event.respondWith(handleStaticRequest(request));
  } else if (isExternalRequest(url)) {
    event.respondWith(handleExternalRequest(request));
  } else {
    event.respondWith(handleNavigationRequest(request));
  }
});

/**
 * Handle API requests with network-first strategy
 */
async function handleApiRequest(request) {
  const cache = await caches.open(API_CACHE);
  
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache successful responses
      const responseClone = networkResponse.clone();
      cache.put(request, responseClone);
      return networkResponse;
    }
    
    throw new Error('Network response not ok');
  } catch (error) {
    // Fallback to cache
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      console.log('[SW] Serving API from cache:', request.url);
      return cachedResponse;
    }
    
    // Return offline response
    return offlineApiResponse();
  }
}

/**
 * Handle static asset requests with cache-first strategy
 */
async function handleStaticRequest(request) {
  const cache = await caches.open(STATIC_CACHE);
  
  try {
    // Try cache first
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      console.log('[SW] Serving static asset from cache:', request.url);
      return cachedResponse;
    }
    
    // Fallback to network
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const responseClone = networkResponse.clone();
      cache.put(request, responseClone);
    }
    
    return networkResponse;
  } catch (error) {
    console.error('[SW] Static asset fetch failed:', error);
    return NOT_FOUND_FALLBACK;
  }
}

/**
 * Handle navigation requests for SPA
 */
async function handleNavigationRequest(request) {
  const cache = await caches.open(FALLBACK_CACHE);
  
  try {
    // Try network first for navigation
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      return networkResponse;
    }
    
    throw new Error('Navigation failed');
  } catch (error) {
    // Fallback to cached navigation page
    const cachedResponse = await cache.match(NAV_FALLBACK_URL);
    
    if (cachedResponse) {
      console.log('[SW] Serving navigation fallback');
      return cachedResponse;
    }
    
    return NOT_FOUND_FALLBACK;
  }
}

/**
 * Handle external requests
 */
async function handleExternalRequest(request) {
  // For external requests, try network only
  try {
    const response = await fetch(request);
    return response;
  } catch (error) {
    console.error('[SW] External request failed:', error);
    return NOT_FOUND_FALLBACK;
  }
}

/**
 * Check if request is for static asset
 */
function isStaticAsset(pathname) {
  return pathname.match(/\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/);
}

/**
 * Check if request is external
 */
function isExternalRequest(url) {
  return url.origin !== self.location.origin;
}

/**
 * Generate offline API response
 */
function offlineApiResponse() {
  return new Response(JSON.stringify({
    error: 'offline',
    message: 'You are currently offline. Please check your connection.',
    timestamp: new Date().toISOString()
  }), {
    status: 503,
    statusText: 'Service Unavailable',
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache'
    }
  });
}

/**
 * Background sync for offline data
 */
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(syncOfflineData());
  }
});

/**
 * Push notification handling
 */
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');
  
  const options = {
    body: event.data ? event.data.text() : 'New notification from Valor IVX',
    icon: '/icon-192x192.png',
    badge: '/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'View Details',
        icon: '/icon-192x192.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/icon-192x192.png'
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
  console.log('[SW] Notification clicked:', event.action);
  
  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

/**
 * Message handling for communication with main thread
 */
self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_DATA') {
    event.waitUntil(cacheData(event.data.key, event.data.data));
  }
  
  if (event.data && event.data.type === 'GET_CACHED_DATA') {
    event.waitUntil(getCachedData(event.data.key));
  }
});

/**
 * Cache data in IndexedDB
 */
async function cacheData(key, data) {
  try {
    const db = await openIndexedDB();
    const transaction = db.transaction(['offlineData'], 'readwrite');
    const store = transaction.objectStore('offlineData');
    
    await store.put({
      key,
      data,
      timestamp: Date.now()
    });
    
    console.log('[SW] Data cached successfully:', key);
  } catch (error) {
    console.error('[SW] Failed to cache data:', error);
  }
}

/**
 * Get cached data from IndexedDB
 */
async function getCachedData(key) {
  try {
    const db = await openIndexedDB();
    const transaction = db.transaction(['offlineData'], 'readonly');
    const store = transaction.objectStore('offlineData');
    
    const result = await store.get(key);
    return result ? result.data : null;
  } catch (error) {
    console.error('[SW] Failed to get cached data:', error);
    return null;
  }
}

/**
 * Sync offline data when back online
 */
async function syncOfflineData() {
  try {
    const db = await openIndexedDB();
    const transaction = db.transaction(['syncQueue'], 'readonly');
    const store = transaction.objectStore('syncQueue');
    
    const items = await store.getAll();
    
    for (const item of items) {
      try {
        await syncDataItem(item);
        await store.delete(item.id);
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
 * Sync individual data item
 */
async function syncDataItem(item) {
  const response = await fetch(item.url, {
    method: item.method,
    headers: item.headers,
    body: item.body
  });
  
  if (!response.ok) {
    throw new Error(`Sync failed: ${response.status}`);
  }
  
  return response;
}

/**
 * Open IndexedDB
 */
function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('ValorIVXOffline', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      // Create object stores
      if (!db.objectStoreNames.contains('offlineData')) {
        db.createObjectStore('offlineData', { keyPath: 'key' });
      }
      
      if (!db.objectStoreNames.contains('syncQueue')) {
        db.createObjectStore('syncQueue', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

/**
 * Clear old IndexedDB data
 */
async function clearOldIndexedDBData() {
  try {
    const db = await openIndexedDB();
    const transaction = db.transaction(['offlineData'], 'readwrite');
    const store = transaction.objectStore('offlineData');
    
    const cutoff = Date.now() - (7 * 24 * 60 * 60 * 1000); // 7 days
    
    const items = await store.getAll();
    for (const item of items) {
      if (item.timestamp < cutoff) {
        await store.delete(item.key);
      }
    }
    
    console.log('[SW] Old IndexedDB data cleared');
  } catch (error) {
    console.error('[SW] Failed to clear old IndexedDB data:', error);
  }
}

/**
 * Periodic cache cleanup
 */
setInterval(async () => {
  try {
    const keys = await caches.keys();
    const currentCaches = [STATIC_CACHE, RUNTIME_CACHE, API_CACHE, FALLBACK_CACHE, DATA_CACHE];
    
    for (const key of keys) {
      if (!currentCaches.includes(key)) {
        await caches.delete(key);
        console.log('[SW] Cleaned up old cache:', key);
      }
    }
  } catch (error) {
    console.error('[SW] Cache cleanup failed:', error);
  }
}, 24 * 60 * 60 * 1000); // Daily cleanup

console.log('[SW] Enhanced service worker loaded');
