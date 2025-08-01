/**
 * Service Worker for Valor IVX PWA
 * Handles offline caching, background sync, and app updates
 */

const CACHE_NAME = 'valor-ivx-v1.0.0';
const STATIC_CACHE = 'valor-ivx-static-v1.0.0';
const DYNAMIC_CACHE = 'valor-ivx-dynamic-v1.0.0';

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

// API endpoints to cache
const API_CACHE = [
    '/api/health',
    '/api/financial-data/',
    '/api/runs',
    '/api/lbo/runs',
    '/api/ma/runs',
    '/api/scenarios'
];

// Install event - cache static files
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[SW] Caching static files');
                return cache.addAll(STATIC_FILES);
            })
            .then(() => {
                console.log('[SW] Static files cached successfully');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('[SW] Failed to cache static files:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                            console.log('[SW] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('[SW] Service worker activated');
                return self.clients.claim();
            })
    );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Handle API requests
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(handleApiRequest(request));
        return;
    }
    
    // Handle static file requests
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
    try {
        // Try network first
        const response = await fetch(request);
        
        if (response.ok) {
            // Cache successful responses
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, response.clone());
            return response;
        }
    } catch (error) {
        console.log('[SW] Network request failed, trying cache:', error);
    }
    
    // Fallback to cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }
    
    // Return offline response for API requests
    return new Response(
        JSON.stringify({
            success: false,
            error: 'Offline mode - data not available',
            offline: true
        }),
        {
            status: 503,
            statusText: 'Service Unavailable',
            headers: {
                'Content-Type': 'application/json'
            }
        }
    );
}

/**
 * Handle static file requests
 */
async function handleStaticRequest(request) {
    // Try cache first for static files
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }
    
    // Fallback to network
    try {
        const response = await fetch(request);
        if (response.ok) {
            // Cache new static files
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.error('[SW] Failed to fetch static file:', error);
        
        // Return offline page for HTML requests
        if (request.headers.get('accept').includes('text/html')) {
            return caches.match('/index.html');
        }
    }
}

/**
 * Handle external API requests
 */
async function handleExternalRequest(request) {
    try {
        // Try network first
        const response = await fetch(request);
        
        if (response.ok) {
            // Cache external API responses
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, response.clone());
            return response;
        }
    } catch (error) {
        console.log('[SW] External API request failed, trying cache:', error);
    }
    
    // Fallback to cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }
    
    // Return error response
    return new Response(
        JSON.stringify({
            success: false,
            error: 'External API unavailable offline'
        }),
        {
            status: 503,
            statusText: 'Service Unavailable',
            headers: {
                'Content-Type': 'application/json'
            }
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
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({ version: CACHE_NAME });
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