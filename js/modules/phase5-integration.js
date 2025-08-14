/**
 * Phase 5 Integration Module - Frontend UX and Reliability
 * Coordinates all Phase 5 features: error handling, performance optimization, accessibility, and PWA enhancements
 */

class Phase5Integration {
    constructor() {
        this.modules = {
            errorHandler: null,
            performanceOptimizer: null,
            accessibilityManager: null,
            pwaManager: null
        };
        
        this.features = {
            errorHandling: true,
            performanceOptimization: true,
            accessibility: true,
            pwaEnhancement: true
        };
        
        this.status = {
            initialized: false,
            modulesLoaded: 0,
            totalModules: 4
        };
        
        this.init();
    }

    async init() {
        console.log('[Phase5Integration] Initializing Phase 5 features...');
        
        try {
            await this.loadModules();
            await this.setupIntegration();
            await this.initializeFeatures();
            await this.setupMonitoring();
            
            this.status.initialized = true;
            console.log('[Phase5Integration] Phase 5 features initialized successfully');
            
            // Report initialization to analytics
            this.reportInitialization();
        } catch (error) {
            console.error('[Phase5Integration] Initialization failed:', error);
            this.handleInitializationError(error);
        }
    }

    /**
     * Load all Phase 5 modules
     */
    async loadModules() {
        const moduleLoaders = [
            { name: 'errorHandler', loader: () => import('./error-handler.js') },
            { name: 'performanceOptimizer', loader: () => import('./performance-optimizer.js') },
            { name: 'accessibilityManager', loader: () => import('./accessibility-manager.js') },
            { name: 'pwaManager', loader: () => import('./pwa-manager.js') }
        ];

        for (const module of moduleLoaders) {
            try {
                const moduleInstance = await module.loader();
                this.modules[module.name] = moduleInstance.default || moduleInstance;
                this.status.modulesLoaded++;
                console.log(`[Phase5Integration] Loaded ${module.name}`);
            } catch (error) {
                console.warn(`[Phase5Integration] Failed to load ${module.name}:`, error);
                this.features[this.getFeatureFromModule(module.name)] = false;
            }
        }
    }

    /**
     * Setup integration between modules
     */
    async setupIntegration() {
        // Connect error handler to performance optimizer
        if (this.modules.errorHandler && this.modules.performanceOptimizer) {
            this.modules.errorHandler.onError = (error) => {
                this.modules.performanceOptimizer.reportMetric('error', 1);
            };
        }

        // Connect accessibility manager to error handler
        if (this.modules.accessibilityManager && this.modules.errorHandler) {
            this.modules.accessibilityManager.onAnnouncement = (message) => {
                this.modules.errorHandler.handleError(new Error(message), {
                    type: 'accessibility',
                    severity: 'low'
                });
            };
        }

        // Connect PWA manager to performance optimizer
        if (this.modules.pwaManager && this.modules.performanceOptimizer) {
            this.modules.pwaManager.onOffline = () => {
                this.modules.performanceOptimizer.reportMetric('offline', 1);
            };
            
            this.modules.pwaManager.onOnline = () => {
                this.modules.performanceOptimizer.reportMetric('online', 1);
            };
        }
    }

    /**
     * Initialize all features
     */
    async initializeFeatures() {
        // Initialize error handling
        if (this.features.errorHandling && this.modules.errorHandler) {
            this.setupErrorHandling();
        }

        // Initialize performance optimization
        if (this.features.performanceOptimization && this.modules.performanceOptimizer) {
            this.setupPerformanceOptimization();
        }

        // Initialize accessibility
        if (this.features.accessibility && this.modules.accessibilityManager) {
            this.setupAccessibility();
        }

        // Initialize PWA enhancement
        if (this.features.pwaEnhancement && this.modules.pwaManager) {
            this.setupPWAEnhancement();
        }
    }

    /**
     * Setup error handling integration
     */
    setupErrorHandling() {
        // Override global error handlers
        window.addEventListener('error', (event) => {
            this.modules.errorHandler.handleError(event.error, {
                type: 'system',
                severity: 'high',
                context: 'global-error'
            });
        });

        window.addEventListener('unhandledrejection', (event) => {
            this.modules.errorHandler.handleError(event.reason, {
                type: 'system',
                severity: 'high',
                context: 'unhandled-rejection'
            });
        });

        // Override console methods for better error tracking
        this.overrideConsoleMethods();
    }

    /**
     * Override console methods for better error tracking
     */
    overrideConsoleMethods() {
        const originalConsole = {
            error: console.error,
            warn: console.warn,
            log: console.log
        };

        console.error = (...args) => {
            originalConsole.error(...args);
            this.modules.errorHandler.handleError(args.join(' '), {
                type: 'console',
                severity: 'high',
                context: 'console-error'
            });
        };

        console.warn = (...args) => {
            originalConsole.warn(...args);
            this.modules.errorHandler.handleError(args.join(' '), {
                type: 'console',
                severity: 'medium',
                context: 'console-warning'
            });
        };
    }

    /**
     * Setup performance optimization integration
     */
    setupPerformanceOptimization() {
        // Monitor page load performance
        window.addEventListener('load', () => {
            this.modules.performanceOptimizer.reportMetric('pageLoad', performance.now());
        });

        // Monitor user interactions
        this.setupInteractionMonitoring();

        // Setup resource monitoring
        this.setupResourceMonitoring();
    }

    /**
     * Setup interaction monitoring
     */
    setupInteractionMonitoring() {
        const interactionEvents = ['click', 'input', 'scroll', 'resize'];
        
        interactionEvents.forEach(eventType => {
            document.addEventListener(eventType, this.modules.performanceOptimizer.throttle(() => {
                this.modules.performanceOptimizer.reportMetric(`userInteraction_${eventType}`, 1);
            }, 1000));
        });
    }

    /**
     * Setup resource monitoring
     */
    setupResourceMonitoring() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.entryType === 'resource') {
                        this.modules.performanceOptimizer.reportMetric('resourceLoad', entry.duration);
                    }
                }
            });
            observer.observe({ entryTypes: ['resource'] });
        }
    }

    /**
     * Setup accessibility integration
     */
    setupAccessibility() {
        // Monitor accessibility interactions
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Tab' || event.key === 'Enter' || event.key === ' ') {
                this.modules.accessibilityManager.announce('Keyboard navigation used');
            }
        });

        // Monitor focus changes
        document.addEventListener('focusin', (event) => {
            this.modules.performanceOptimizer.reportMetric('focusChange', 1);
        });
    }

    /**
     * Setup PWA enhancement integration
     */
    setupPWAEnhancement() {
        // Monitor PWA events
        this.modules.pwaManager.onInstall = () => {
            this.modules.performanceOptimizer.reportMetric('pwaInstall', 1);
        };

        this.modules.pwaManager.onUpdate = () => {
            this.modules.performanceOptimizer.reportMetric('pwaUpdate', 1);
        };
    }

    /**
     * Setup monitoring and reporting
     */
    async setupMonitoring() {
        // Setup periodic health checks
        setInterval(() => {
            this.performHealthCheck();
        }, 30000); // Every 30 seconds

        // Setup performance reporting
        setInterval(() => {
            this.reportPerformanceMetrics();
        }, 60000); // Every minute

        // Setup error reporting
        setInterval(() => {
            this.reportErrorMetrics();
        }, 300000); // Every 5 minutes
    }

    /**
     * Perform health check on all modules
     */
    performHealthCheck() {
        const health = {
            timestamp: new Date().toISOString(),
            modules: {},
            overall: 'healthy'
        };

        // Check each module
        Object.keys(this.modules).forEach(moduleName => {
            const module = this.modules[moduleName];
            if (module && typeof module.getStatus === 'function') {
                health.modules[moduleName] = module.getStatus();
            } else {
                health.modules[moduleName] = { status: 'unknown' };
            }
        });

        // Check for issues
        const hasIssues = Object.values(health.modules).some(module => 
            module.status === 'error' || module.status === 'unhealthy'
        );

        if (hasIssues) {
            health.overall = 'unhealthy';
            console.warn('[Phase5Integration] Health check failed:', health);
        }

        return health;
    }

    /**
     * Report performance metrics
     */
    reportPerformanceMetrics() {
        if (this.modules.performanceOptimizer) {
            const metrics = this.modules.performanceOptimizer.getMetrics();
            const score = this.modules.performanceOptimizer.getPerformanceScore();
            
            // Send to analytics
            this.sendToAnalytics('performance', {
                metrics,
                score,
                timestamp: new Date().toISOString()
            });
        }
    }

    /**
     * Report error metrics
     */
    reportErrorMetrics() {
        if (this.modules.errorHandler) {
            const stats = this.modules.errorHandler.getErrorStats();
            
            // Send to analytics
            this.sendToAnalytics('errors', {
                stats,
                timestamp: new Date().toISOString()
            });
        }
    }

    /**
     * Send data to analytics
     */
    sendToAnalytics(type, data) {
        try {
            // Use existing analytics if available
            if (window.gtag) {
                window.gtag('event', `phase5_${type}`, data);
            }
            
            // Send to backend if available
            if (window.backend && window.backend.status === 'online') {
                fetch('/api/analytics/phase5', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'ValorIVX'
                    },
                    body: JSON.stringify({
                        type,
                        data,
                        timestamp: new Date().toISOString()
                    })
                }).catch(error => {
                    console.warn('[Phase5Integration] Failed to send analytics:', error);
                });
            }
        } catch (error) {
            console.warn('[Phase5Integration] Analytics reporting failed:', error);
        }
    }

    /**
     * Report initialization
     */
    reportInitialization() {
        this.sendToAnalytics('initialization', {
            modulesLoaded: this.status.modulesLoaded,
            totalModules: this.status.totalModules,
            features: this.features,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Handle initialization error
     */
    handleInitializationError(error) {
        console.error('[Phase5Integration] Initialization error:', error);
        
        // Try to use basic error handling
        if (this.modules.errorHandler) {
            this.modules.errorHandler.handleError(error, {
                type: 'system',
                severity: 'critical',
                context: 'phase5-initialization'
            });
        }
    }

    /**
     * Get feature name from module name
     */
    getFeatureFromModule(moduleName) {
        const mapping = {
            'errorHandler': 'errorHandling',
            'performanceOptimizer': 'performanceOptimization',
            'accessibilityManager': 'accessibility',
            'pwaManager': 'pwaEnhancement'
        };
        return mapping[moduleName] || 'unknown';
    }

    /**
     * Get integration status
     */
    getStatus() {
        return {
            ...this.status,
            features: this.features,
            modules: Object.keys(this.modules).map(name => ({
                name,
                loaded: !!this.modules[name],
                status: this.modules[name]?.getStatus?.() || 'unknown'
            }))
        };
    }

    /**
     * Enable/disable features
     */
    setFeatureEnabled(featureName, enabled) {
        if (this.features.hasOwnProperty(featureName)) {
            this.features[featureName] = enabled;
            console.log(`[Phase5Integration] ${featureName} ${enabled ? 'enabled' : 'disabled'}`);
        }
    }

    /**
     * Get performance report
     */
    getPerformanceReport() {
        if (!this.modules.performanceOptimizer) {
            return null;
        }

        const metrics = this.modules.performanceOptimizer.getMetrics();
        const score = this.modules.performanceOptimizer.getPerformanceScore();

        return {
            score,
            metrics,
            recommendations: this.getPerformanceRecommendations(score, metrics)
        };
    }

    /**
     * Get performance recommendations
     */
    getPerformanceRecommendations(score, metrics) {
        const recommendations = [];

        if (score < 90) {
            recommendations.push('Consider optimizing page load performance');
        }

        if (metrics.firstContentfulPaint > 1800) {
            recommendations.push('First Contentful Paint is slow - optimize critical rendering path');
        }

        if (metrics.largestContentfulPaint > 2500) {
            recommendations.push('Largest Contentful Paint is slow - optimize main content loading');
        }

        if (metrics.cumulativeLayoutShift > 0.1) {
            recommendations.push('Cumulative Layout Shift is high - fix layout stability issues');
        }

        return recommendations;
    }

    /**
     * Cleanup resources
     */
    cleanup() {
        // Cleanup all modules
        Object.values(this.modules).forEach(module => {
            if (module && typeof module.cleanup === 'function') {
                module.cleanup();
            }
        });

        console.log('[Phase5Integration] Cleanup completed');
    }
}

// Create global Phase 5 integration instance
window.phase5Integration = new Phase5Integration();

// Export for module usage
export default window.phase5Integration; 