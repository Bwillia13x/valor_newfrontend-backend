/**
 * Performance Optimizer Module - Phase 5 Frontend UX and Reliability
 * Handles lazy loading, caching, memory management, and performance monitoring
 */

class PerformanceOptimizer {
    constructor() {
        this.metrics = {
            pageLoadTime: 0,
            firstContentfulPaint: 0,
            largestContentfulPaint: 0,
            cumulativeLayoutShift: 0,
            firstInputDelay: 0,
            memoryUsage: 0,
            cacheHitRatio: 0
        };

        this.cache = new Map();
        this.maxCacheSize = 100;
        this.lazyLoadQueue = [];
        this.performanceObserver = null;
        this.memoryMonitor = null;
        
        this.init();
    }

    init() {
        this.setupPerformanceMonitoring();
        this.setupMemoryMonitoring();
        this.setupLazyLoading();
        this.setupCaching();
        this.setupIntersectionObserver();
        
        console.log('[PerformanceOptimizer] Initialized');
    }

    /**
     * Setup performance monitoring using Performance API
     */
    setupPerformanceMonitoring() {
        // Monitor Core Web Vitals
        if ('PerformanceObserver' in window) {
            try {
                // First Contentful Paint
                this.performanceObserver = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (entry.name === 'first-contentful-paint') {
                            this.metrics.firstContentfulPaint = entry.startTime;
                            this.reportMetric('FCP', entry.startTime);
                        }
                    }
                });
                this.performanceObserver.observe({ entryTypes: ['paint'] });

                // Largest Contentful Paint
                const lcpObserver = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        this.metrics.largestContentfulPaint = entry.startTime;
                        this.reportMetric('LCP', entry.startTime);
                    }
                });
                lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });

                // Cumulative Layout Shift
                const clsObserver = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        this.metrics.cumulativeLayoutShift += entry.value;
                        this.reportMetric('CLS', this.metrics.cumulativeLayoutShift);
                    }
                });
                clsObserver.observe({ entryTypes: ['layout-shift'] });

                // First Input Delay
                const fidObserver = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        this.metrics.firstInputDelay = entry.processingStart - entry.startTime;
                        this.reportMetric('FID', this.metrics.firstInputDelay);
                    }
                });
                fidObserver.observe({ entryTypes: ['first-input'] });

            } catch (error) {
                console.warn('[PerformanceOptimizer] Performance monitoring setup failed:', error);
            }
        }

        // Measure page load time
        window.addEventListener('load', () => {
            const loadTime = performance.now();
            this.metrics.pageLoadTime = loadTime;
            this.reportMetric('PageLoad', loadTime);
        });
    }

    /**
     * Setup memory monitoring
     */
    setupMemoryMonitoring() {
        if ('memory' in performance) {
            this.memoryMonitor = setInterval(() => {
                this.metrics.memoryUsage = performance.memory.usedJSHeapSize;
                this.checkMemoryUsage();
            }, 30000); // Check every 30 seconds
        }
    }

    /**
     * Check memory usage and optimize if needed
     */
    checkMemoryUsage() {
        if (!('memory' in performance)) return;

        const memory = performance.memory;
        const usageRatio = memory.usedJSHeapSize / memory.jsHeapSizeLimit;

        if (usageRatio > 0.8) {
            console.warn('[PerformanceOptimizer] High memory usage detected:', usageRatio);
            this.optimizeMemory();
        }
    }

    /**
     * Optimize memory usage
     */
    optimizeMemory() {
        // Clear old cache entries
        this.clearOldCacheEntries();
        
        // Clear lazy load queue if too large
        if (this.lazyLoadQueue.length > 50) {
            this.lazyLoadQueue = this.lazyLoadQueue.slice(-25);
        }

        // Force garbage collection if available
        if (window.gc) {
            window.gc();
        }
    }

    /**
     * Setup lazy loading system
     */
    setupLazyLoading() {
        // Process lazy load queue
        setInterval(() => {
            this.processLazyLoadQueue();
        }, 100); // Process every 100ms
    }

    /**
     * Setup intersection observer for lazy loading
     */
    setupIntersectionObserver() {
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const element = entry.target;
                        const loadAction = element.dataset.lazyLoad;
                        
                        if (loadAction) {
                            this.queueLazyLoad(loadAction, element);
                            observer.unobserve(element);
                        }
                    }
                });
            }, {
                rootMargin: '50px' // Start loading 50px before element is visible
            });

            // Observe all elements with lazy-load attribute
            document.querySelectorAll('[data-lazy-load]').forEach(element => {
                observer.observe(element);
            });
        }
    }

    /**
     * Queue lazy load action
     */
    queueLazyLoad(action, element) {
        this.lazyLoadQueue.push({
            action,
            element,
            timestamp: Date.now()
        });
    }

    /**
     * Process lazy load queue
     */
    processLazyLoadQueue() {
        if (this.lazyLoadQueue.length === 0) return;

        const item = this.lazyLoadQueue.shift();
        
        try {
            this.executeLazyLoad(item.action, item.element);
        } catch (error) {
            console.error('[PerformanceOptimizer] Lazy load failed:', error);
        }
    }

    /**
     * Execute lazy load action
     */
    executeLazyLoad(action, element) {
        switch (action) {
            case 'image':
                this.lazyLoadImage(element);
                break;
            case 'script':
                this.lazyLoadScript(element);
                break;
            case 'module':
                this.lazyLoadModule(element);
                break;
            case 'chart':
                this.lazyLoadChart(element);
                break;
            default:
                console.warn('[PerformanceOptimizer] Unknown lazy load action:', action);
        }
    }

    /**
     * Lazy load image
     */
    lazyLoadImage(element) {
        const src = element.dataset.src;
        if (src) {
            element.src = src;
            element.removeAttribute('data-src');
            element.classList.remove('lazy');
        }
    }

    /**
     * Lazy load script
     */
    lazyLoadScript(element) {
        const src = element.dataset.src;
        if (src) {
            const script = document.createElement('script');
            script.src = src;
            script.async = true;
            element.parentNode.replaceChild(script, element);
        }
    }

    /**
     * Lazy load module
     */
    async lazyLoadModule(element) {
        const moduleName = element.dataset.module;
        if (moduleName) {
            try {
                const module = await import(moduleName);
                if (module.default && typeof module.default.init === 'function') {
                    module.default.init(element);
                }
            } catch (error) {
                console.error('[PerformanceOptimizer] Module load failed:', error);
            }
        }
    }

    /**
     * Lazy load chart
     */
    lazyLoadChart(element) {
        const chartType = element.dataset.chartType;
        const chartData = element.dataset.chartData;
        
        if (chartType && chartData) {
            try {
                const data = JSON.parse(chartData);
                this.renderChart(element, chartType, data);
            } catch (error) {
                console.error('[PerformanceOptimizer] Chart load failed:', error);
            }
        }
    }

    /**
     * Render chart based on type
     */
    renderChart(element, type, data) {
        // Use existing charting module if available
        if (window.renderChart) {
            window.renderChart(element, type, data);
        } else {
            // Fallback chart rendering
            this.renderFallbackChart(element, type, data);
        }
    }

    /**
     * Fallback chart rendering
     */
    renderFallbackChart(element, type, data) {
        const canvas = document.createElement('canvas');
        canvas.width = element.clientWidth || 400;
        canvas.height = element.clientHeight || 300;
        element.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#f0f0f0';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#333';
        ctx.font = '14px Arial';
        ctx.fillText(`${type} Chart`, 10, 20);
    }

    /**
     * Setup caching system
     */
    setupCaching() {
        // Clear old cache entries periodically
        setInterval(() => {
            this.clearOldCacheEntries();
        }, 60000); // Every minute
    }

    /**
     * Cache data with TTL
     */
    cache(key, data, ttl = 300000) { // 5 minutes default
        const entry = {
            data,
            timestamp: Date.now(),
            ttl
        };

        this.cache.set(key, entry);
        
        // Enforce cache size limit
        if (this.cache.size > this.maxCacheSize) {
            this.clearOldCacheEntries();
        }
    }

    /**
     * Get cached data
     */
    getCached(key) {
        const entry = this.cache.get(key);
        
        if (!entry) {
            return null;
        }

        // Check if entry has expired
        if (Date.now() - entry.timestamp > entry.ttl) {
            this.cache.delete(key);
            return null;
        }

        return entry.data;
    }

    /**
     * Clear old cache entries
     */
    clearOldCacheEntries() {
        const now = Date.now();
        const keysToDelete = [];

        for (const [key, entry] of this.cache.entries()) {
            if (now - entry.timestamp > entry.ttl) {
                keysToDelete.push(key);
            }
        }

        keysToDelete.forEach(key => this.cache.delete(key));
    }

    /**
     * Preload critical resources
     */
    preloadResources(resources) {
        resources.forEach(resource => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = resource.url;
            link.as = resource.type || 'fetch';
            
            if (resource.crossorigin) {
                link.crossOrigin = resource.crossorigin;
            }
            
            document.head.appendChild(link);
        });
    }

    /**
     * Optimize images
     */
    optimizeImages() {
        const images = document.querySelectorAll('img[data-optimize]');
        
        images.forEach(img => {
            // Add loading="lazy" for images below the fold
            if (!this.isElementInViewport(img)) {
                img.loading = 'lazy';
            }
            
            // Add srcset for responsive images
            if (img.dataset.srcset) {
                img.srcset = img.dataset.srcset;
            }
        });
    }

    /**
     * Check if element is in viewport
     */
    isElementInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }

    /**
     * Debounce function calls
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Throttle function calls
     */
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * Report performance metric
     */
    reportMetric(name, value) {
        // Send to analytics if available
        if (window.gtag) {
            window.gtag('event', 'performance', {
                metric_name: name,
                metric_value: value
            });
        }

        // Store locally
        this.metrics[name] = value;
    }

    /**
     * Get performance metrics
     */
    getMetrics() {
        return { ...this.metrics };
    }

    /**
     * Get performance score
     */
    getPerformanceScore() {
        let score = 100;

        // FCP penalty
        if (this.metrics.firstContentfulPaint > 1800) {
            score -= 10;
        }

        // LCP penalty
        if (this.metrics.largestContentfulPaint > 2500) {
            score -= 15;
        }

        // CLS penalty
        if (this.metrics.cumulativeLayoutShift > 0.1) {
            score -= 15;
        }

        // FID penalty
        if (this.metrics.firstInputDelay > 100) {
            score -= 10;
        }

        return Math.max(0, score);
    }

    /**
     * Optimize DOM operations
     */
    optimizeDOMOperations() {
        // Use DocumentFragment for multiple DOM operations
        const fragment = document.createDocumentFragment();
        
        return {
            appendChild: (element) => {
                fragment.appendChild(element);
            },
            commit: () => {
                document.body.appendChild(fragment);
            }
        };
    }

    /**
     * Batch DOM updates
     */
    batchDOMUpdates(updates) {
        // Use requestAnimationFrame for smooth updates
        requestAnimationFrame(() => {
            updates.forEach(update => {
                try {
                    update();
                } catch (error) {
                    console.error('[PerformanceOptimizer] DOM update failed:', error);
                }
            });
        });
    }

    /**
     * Cleanup resources
     */
    cleanup() {
        if (this.performanceObserver) {
            this.performanceObserver.disconnect();
        }

        if (this.memoryMonitor) {
            clearInterval(this.memoryMonitor);
        }

        this.cache.clear();
        this.lazyLoadQueue = [];
    }
}

// Create global performance optimizer instance
window.performanceOptimizer = new PerformanceOptimizer();

// Export for module usage
export default window.performanceOptimizer; 