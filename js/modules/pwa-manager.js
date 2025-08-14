/**
 * PWA Manager - Progressive Web App Features
 * Handles service worker, offline capabilities, and mobile app-like features
 */

class PWAManager {
    constructor() {
        this.serviceWorker = null;
        this.isInstalled = false;
        this.isOnline = navigator.onLine;
        this.offlineData = new Map();
        this.syncQueue = [];
        this.installPrompt = null;
        
        this.init();
    }

    /**
     * Initialize PWA features
     */
    async init() {
        try {
            // Register service worker
            await this.registerServiceWorker();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Check installation status
            this.checkInstallationStatus();
            
            // Initialize offline storage
            this.initOfflineStorage();
            
            console.log('[PWA] Initialized successfully');
        } catch (error) {
            console.error('[PWA] Initialization failed:', error);
        }
    }

    /**
     * Register service worker
     */
    async registerServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            console.warn('[PWA] Service Worker not supported');
            throw new Error('Service Worker not supported');
        }
        try {
            const registration = await navigator.serviceWorker.register('/sw.js', {
                scope: '/'
            });

            // Enable navigation preload for faster SSR/HTML responses where supported
            if ('navigationPreload' in registration) {
                try {
                    await registration.navigationPreload.enable();
                } catch (e) {
                    console.warn('[PWA] Navigation preload enable failed:', e);
                }
            }

            this.serviceWorker = registration;
            console.log('[PWA] Service Worker registered:', registration);

            // Handle service worker updates
            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;
                if (!newWorker) return;
                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        this.showUpdateNotification();
                    }
                });
            });

            // Listen for controllerchange to reload to the latest SW
            navigator.serviceWorker.addEventListener('controllerchange', () => {
                console.log('[PWA] Controller changed, new SW in control');
            });

            return registration;
        } catch (error) {
            console.error('[PWA] Service Worker registration failed:', error);
            throw error;
        }
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Online/offline status
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.onOnline();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.onOffline();
        });

        // Install prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.installPrompt = e;
            this.showInstallPrompt();
        });

        // App installed
        window.addEventListener('appinstalled', () => {
            this.isInstalled = true;
            this.hideInstallPrompt();
            console.log('[PWA] App installed successfully');
        });

        // Visibility change (for background sync)
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                this.onAppVisible();
            }
        });

        // Listen for SW messages (version, cache ops)
        navigator.serviceWorker?.addEventListener('message', (event) => {
            if (!event.data) return;
            if (event.data.version) {
                console.log('[PWA] SW version:', event.data);
            }
        });
    }

    /**
     * Check if app is installed
     */
    checkInstallationStatus() {
        // Check if running in standalone mode (installed)
        this.isInstalled = window.matchMedia('(display-mode: standalone)').matches ||
                          window.navigator.standalone === true;
        
        if (this.isInstalled) {
            console.log('[PWA] App is installed');
        }
    }

    /**
     * Initialize offline storage
     */
    initOfflineStorage() {
        // Use IndexedDB for offline data storage
        if ('indexedDB' in window) {
            this.initIndexedDB();
        } else {
            console.warn('[PWA] IndexedDB not supported, using localStorage fallback');
            this.useLocalStorageFallback();
        }
    }

    /**
     * Initialize IndexedDB
     */
    async initIndexedDB() {
        const request = indexedDB.open('ValorIVX_PWA', 1);
        
        request.onerror = () => {
            console.error('[PWA] IndexedDB error:', request.error);
            this.useLocalStorageFallback();
        };
        
        request.onsuccess = () => {
            this.db = request.result;
            console.log('[PWA] IndexedDB initialized');
        };
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            // Create object stores
            if (!db.objectStoreNames.contains('offlineData')) {
                const offlineStore = db.createObjectStore('offlineData', { keyPath: 'key' });
                offlineStore.createIndex('timestamp', 'timestamp', { unique: false });
            }
            
            if (!db.objectStoreNames.contains('syncQueue')) {
                const syncStore = db.createObjectStore('syncQueue', { keyPath: 'id', autoIncrement: true });
                syncStore.createIndex('timestamp', 'timestamp', { unique: false });
            }
        };
    }

    /**
     * Use localStorage as fallback
     */
    useLocalStorageFallback() {
        this.storageType = 'localStorage';
        console.log('[PWA] Using localStorage for offline storage');
    }

    /**
     * Store data for offline use
     */
    async storeOfflineData(key, data) {
        const offlineItem = {
            key: key,
            data: data,
            timestamp: Date.now()
        };
        
        if (this.db) {
            // Use IndexedDB
            const transaction = this.db.transaction(['offlineData'], 'readwrite');
            const store = transaction.objectStore('offlineData');
            await store.put(offlineItem);
        } else {
            // Use localStorage
            localStorage.setItem(`pwa_${key}`, JSON.stringify(offlineItem));
        }
        
        this.offlineData.set(key, offlineItem);
    }

    /**
     * Retrieve offline data
     */
    async getOfflineData(key) {
        if (this.offlineData.has(key)) {
            return this.offlineData.get(key).data;
        }
        
        if (this.db) {
            // Use IndexedDB
            const transaction = this.db.transaction(['offlineData'], 'readonly');
            const store = transaction.objectStore('offlineData');
            const request = store.get(key);
            
            return new Promise((resolve, reject) => {
                request.onsuccess = () => {
                    resolve(request.result ? request.result.data : null);
                };
                request.onerror = () => reject(request.error);
            });
        } else {
            // Use localStorage
            const item = localStorage.getItem(`pwa_${key}`);
            return item ? JSON.parse(item).data : null;
        }
    }

    /**
     * Add item to sync queue
     */
    async addToSyncQueue(action, data) {
        const syncItem = {
            action: action,
            data: data,
            timestamp: Date.now(),
            retries: 0
        };
        
        if (this.db) {
            // Use IndexedDB
            const transaction = this.db.transaction(['syncQueue'], 'readwrite');
            const store = transaction.objectStore('syncQueue');
            await store.add(syncItem);
        } else {
            // Use localStorage
            const queue = JSON.parse(localStorage.getItem('pwa_syncQueue') || '[]');
            queue.push(syncItem);
            localStorage.setItem('pwa_syncQueue', JSON.stringify(queue));
        }
        
        this.syncQueue.push(syncItem);
        
        // Try to sync immediately if online
        if (this.isOnline) {
            this.processSyncQueue();
        }
    }

    /**
     * Process sync queue
     */
    async processSyncQueue() {
        if (!this.isOnline || this.syncQueue.length === 0) {
            return;
        }
        
        console.log('[PWA] Processing sync queue...');
        
        const itemsToProcess = [...this.syncQueue];
        this.syncQueue = [];
        
        for (const item of itemsToProcess) {
            try {
                await this.processSyncItem(item);
            } catch (error) {
                console.error('[PWA] Sync item failed:', error);
                item.retries++;
                
                // Re-add to queue if retries < 3
                if (item.retries < 3) {
                    this.syncQueue.push(item);
                }
            }
        }
    }

    /**
     * Process individual sync item
     */
    async processSyncItem(item) {
        switch (item.action) {
            case 'save_dcf':
                await this.syncDCFData(item.data);
                break;
            case 'save_lbo':
                await this.syncLBOData(item.data);
                break;
            case 'save_ma':
                await this.syncMAData(item.data);
                break;
            case 'save_scenario':
                await this.syncScenarioData(item.data);
                break;
            default:
                console.warn('[PWA] Unknown sync action:', item.action);
        }
    }

    /**
     * Sync DCF data
     */
    async syncDCFData(data) {
        const response = await fetch('/api/runs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('DCF sync failed');
        }
    }

    /**
     * Sync LBO data
     */
    async syncLBOData(data) {
        const response = await fetch('/api/lbo/runs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('LBO sync failed');
        }
    }

    /**
     * Sync M&A data
     */
    async syncMAData(data) {
        const response = await fetch('/api/ma/runs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('M&A sync failed');
        }
    }

    /**
     * Sync scenario data
     */
    async syncScenarioData(data) {
        const response = await fetch('/api/scenarios', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Scenario sync failed');
        }
    }

    /**
     * Show install prompt
     */
    showInstallPrompt() {
        if (!this.installPrompt || this.isInstalled) {
            return;
        }
        
        // Create install button
        const installButton = document.createElement('button');
        installButton.textContent = 'Install App';
        installButton.className = 'pwa-install-btn';
        installButton.onclick = () => this.installApp();
        
        // Add to page
        const container = document.createElement('div');
        container.className = 'pwa-install-container';
        container.appendChild(installButton);
        
        document.body.appendChild(container);
    }

    /**
     * Hide install prompt
     */
    hideInstallPrompt() {
        const container = document.querySelector('.pwa-install-container');
        if (container) {
            container.remove();
        }
        this.installPrompt = null;
    }

    /**
     * Install app
     */
    async installApp() {
        if (!this.installPrompt) {
            return;
        }
        
        this.installPrompt.prompt();
        const result = await this.installPrompt.userChoice;
        
        if (result.outcome === 'accepted') {
            console.log('[PWA] User accepted install prompt');
        } else {
            console.log('[PWA] User dismissed install prompt');
        }
        
        this.installPrompt = null;
        this.hideInstallPrompt();
    }

    /**
     * Show update notification
     */
    showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'pwa-update-notification';
        notification.innerHTML = `
            <div class="pwa-update-content">
                <span>New version available</span>
                <button onclick="window.pwaManager.updateApp()">Update</button>
                <button onclick="this.parentElement.parentElement.remove()">Dismiss</button>
            </div>
        `;
        
        document.body.appendChild(notification);
    }

    /**
     * Update app
     */
    updateApp() {
        if (this.serviceWorker && this.serviceWorker.waiting) {
            this.serviceWorker.waiting.postMessage({ type: 'SKIP_WAITING' });
        }

        // Ask for current SW version and optionally clear caches
        navigator.serviceWorker.controller?.postMessage({ type: 'GET_VERSION' });

        // Remove update notification
        const notification = document.querySelector('.pwa-update-notification');
        if (notification) {
            notification.remove();
        }
    }

    /**
     * Handle online event
     */
    onOnline() {
        console.log('[PWA] App is online');
        this.processSyncQueue();
        this.showOnlineNotification();
    }

    /**
     * Handle offline event
     */
    onOffline() {
        console.log('[PWA] App is offline');
        this.showOfflineNotification();
    }

    /**
     * Handle app becoming visible
     */
    onAppVisible() {
        // Process any pending sync items
        this.processSyncQueue();
    }

    /**
     * Show online notification
     */
    showOnlineNotification() {
        this.showNotification('Connection restored', 'You are back online');
    }

    /**
     * Show offline notification
     */
    showOfflineNotification() {
        this.showNotification('Offline mode', 'Changes will be synced when online');
    }

    /**
     * Show notification
     */
    showNotification(title, message) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, { body: message });
        } else {
            // Fallback to in-app notification
            this.showInAppNotification(title, message);
        }
    }

    /**
     * Show in-app notification
     */
    showInAppNotification(title, message) {
        const notification = document.createElement('div');
        notification.className = 'pwa-notification';
        notification.innerHTML = `
            <div class="pwa-notification-content">
                <strong>${title}</strong>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 3000);
    }

    /**
     * Request notification permission
     */
    async requestNotificationPermission() {
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            return permission === 'granted';
        }
        return false;
    }

    /**
     * Get app status
     */
    getStatus() {
        return {
            isInstalled: this.isInstalled,
            isOnline: this.isOnline,
            hasServiceWorker: !!this.serviceWorker,
            offlineDataCount: this.offlineData.size,
            syncQueueLength: this.syncQueue.length,
            storageType: this.db ? 'IndexedDB' : 'localStorage'
        };
    }

    /**
     * Clear all caches via SW
     */
    clearAllCaches() {
        navigator.serviceWorker.controller?.postMessage({ type: 'CLEAR_CACHES' });
    }

    /**
     * Clear offline data
     */
    async clearOfflineData() {
        if (this.db) {
            const transaction = this.db.transaction(['offlineData'], 'readwrite');
            const store = transaction.objectStore('offlineData');
            await store.clear();
        } else {
            // Clear localStorage
            Object.keys(localStorage).forEach(key => {
                if (key.startsWith('pwa_')) {
                    localStorage.removeItem(key);
                }
            });
        }
        
        this.offlineData.clear();
        console.log('[PWA] Offline data cleared');
    }

    /**
     * Clear sync queue
     */
    async clearSyncQueue() {
        if (this.db) {
            const transaction = this.db.transaction(['syncQueue'], 'readwrite');
            const store = transaction.objectStore('syncQueue');
            await store.clear();
        } else {
            localStorage.removeItem('pwa_syncQueue');
        }
        
        this.syncQueue = [];
        console.log('[PWA] Sync queue cleared');
    }
}

// Export for use in other modules
window.PWAManager = PWAManager;
