/**
 * Error Handler Module - Phase 5 Frontend UX and Reliability
 * Standardized error handling, categorization, and user-friendly error reporting
 */

class ErrorHandler {
    constructor() {
        this.errorTypes = {
            VALIDATION: 'validation',
            NETWORK: 'network',
            CALCULATION: 'calculation',
            AUTHENTICATION: 'authentication',
            PERMISSION: 'permission',
            RESOURCE: 'resource',
            SYSTEM: 'system',
            UNKNOWN: 'unknown'
        };

        this.errorSeverity = {
            LOW: 'low',
            MEDIUM: 'medium',
            HIGH: 'high',
            CRITICAL: 'critical'
        };

        this.errorCounts = new Map();
        this.errorHistory = [];
        this.maxHistorySize = 100;
        this.reportingEnabled = true;
        
        this.init();
    }

    init() {
        // Set up global error handlers
        this.setupGlobalHandlers();
        
        // Initialize error reporting
        this.setupErrorReporting();
        
        console.log('[ErrorHandler] Initialized');
    }

    /**
     * Setup global error handlers
     */
    setupGlobalHandlers() {
        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError(event.reason, {
                type: this.errorTypes.SYSTEM,
                severity: this.errorSeverity.HIGH,
                context: 'unhandled-rejection'
            });
            event.preventDefault();
        });

        // Handle JavaScript errors
        window.addEventListener('error', (event) => {
            this.handleError(event.error || new Error(event.message), {
                type: this.errorTypes.SYSTEM,
                severity: this.errorSeverity.HIGH,
                context: 'javascript-error',
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });

        // Handle resource loading errors
        window.addEventListener('error', (event) => {
            if (event.target && event.target !== window) {
                this.handleError(new Error(`Failed to load resource: ${event.target.src || event.target.href}`), {
                    type: this.errorTypes.RESOURCE,
                    severity: this.errorSeverity.MEDIUM,
                    context: 'resource-load',
                    element: event.target.tagName,
                    url: event.target.src || event.target.href
                });
            }
        }, true);
    }

    /**
     * Setup error reporting to backend
     */
    setupErrorReporting() {
        // Report errors to backend if available
        if (this.reportingEnabled && window.backend && window.backend.status === 'online') {
            setInterval(() => {
                this.flushErrorQueue();
            }, 30000); // Flush every 30 seconds
        }
    }

    /**
     * Main error handling method
     */
    handleError(error, options = {}) {
        const errorInfo = this.categorizeError(error, options);
        
        // Log error
        this.logError(errorInfo);
        
        // Track error counts
        this.trackError(errorInfo);
        
        // Add to history
        this.addToHistory(errorInfo);
        
        // Show user-friendly message
        this.showUserMessage(errorInfo);
        
        // Report to backend if critical
        if (errorInfo.severity === this.errorSeverity.CRITICAL) {
            this.reportError(errorInfo);
        }

        return errorInfo;
    }

    /**
     * Categorize and normalize error
     */
    categorizeError(error, options = {}) {
        const normalizedError = this.normalizeError(error);
        
        return {
            id: this.generateErrorId(),
            timestamp: new Date().toISOString(),
            type: options.type || this.detectErrorType(normalizedError),
            severity: options.severity || this.detectSeverity(normalizedError),
            message: normalizedError.message,
            code: normalizedError.code,
            details: normalizedError.details,
            context: options.context || 'unknown',
            userAgent: navigator.userAgent,
            url: window.location.href,
            stack: normalizedError.stack,
            ...options
        };
    }

    /**
     * Normalize any error object
     */
    normalizeError(error) {
        if (!error) {
            return {
                message: 'Unknown error occurred',
                code: 'UNKNOWN',
                details: null,
                stack: null
            };
        }

        if (typeof error === 'string') {
            return {
                message: error,
                code: 'ERROR',
                details: null,
                stack: null
            };
        }

        if (error.name === 'AbortError') {
            return {
                message: 'Request was cancelled',
                code: 'ABORTED',
                details: null,
                stack: null
            };
        }

        return {
            message: error.message || 'Unknown error',
            code: error.code || error.status || 'ERROR',
            details: error.details || null,
            stack: error.stack || null
        };
    }

    /**
     * Detect error type based on error characteristics
     */
    detectErrorType(error) {
        const message = error.message.toLowerCase();
        const code = error.code?.toString() || '';

        if (message.includes('validation') || message.includes('invalid')) {
            return this.errorTypes.VALIDATION;
        }
        
        if (message.includes('network') || message.includes('fetch') || message.includes('timeout')) {
            return this.errorTypes.NETWORK;
        }
        
        if (message.includes('calculation') || message.includes('math') || message.includes('nan')) {
            return this.errorTypes.CALCULATION;
        }
        
        if (message.includes('auth') || message.includes('login') || message.includes('token')) {
            return this.errorTypes.AUTHENTICATION;
        }
        
        if (message.includes('permission') || message.includes('access') || message.includes('forbidden')) {
            return this.errorTypes.PERMISSION;
        }
        
        if (message.includes('resource') || message.includes('load') || message.includes('404')) {
            return this.errorTypes.RESOURCE;
        }

        return this.errorTypes.UNKNOWN;
    }

    /**
     * Detect error severity
     */
    detectSeverity(error) {
        const message = error.message.toLowerCase();
        const code = error.code?.toString() || '';

        // Critical errors
        if (message.includes('critical') || code === '500' || code === '503') {
            return this.errorSeverity.CRITICAL;
        }

        // High severity
        if (code === '401' || code === '403' || message.includes('authentication')) {
            return this.errorSeverity.HIGH;
        }

        // Medium severity
        if (code === '400' || code === '404' || message.includes('validation')) {
            return this.errorSeverity.MEDIUM;
        }

        return this.errorSeverity.LOW;
    }

    /**
     * Generate unique error ID
     */
    generateErrorId() {
        return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Log error to console
     */
    logError(errorInfo) {
        const logLevel = this.getLogLevel(errorInfo.severity);
        const logMessage = `[${errorInfo.type.toUpperCase()}] ${errorInfo.message}`;
        
        console[logLevel](logMessage, {
            error: errorInfo,
            context: errorInfo.context,
            severity: errorInfo.severity
        });
    }

    /**
     * Get console log level based on severity
     */
    getLogLevel(severity) {
        switch (severity) {
            case this.errorSeverity.CRITICAL:
                return 'error';
            case this.errorSeverity.HIGH:
                return 'warn';
            case this.errorSeverity.MEDIUM:
                return 'info';
            default:
                return 'log';
        }
    }

    /**
     * Track error counts for analytics
     */
    trackError(errorInfo) {
        const key = `${errorInfo.type}_${errorInfo.severity}`;
        this.errorCounts.set(key, (this.errorCounts.get(key) || 0) + 1);
    }

    /**
     * Add error to history
     */
    addToHistory(errorInfo) {
        this.errorHistory.unshift(errorInfo);
        
        // Keep history size manageable
        if (this.errorHistory.length > this.maxHistorySize) {
            this.errorHistory = this.errorHistory.slice(0, this.maxHistorySize);
        }
    }

    /**
     * Show user-friendly error message
     */
    showUserMessage(errorInfo) {
        const message = this.getUserFriendlyMessage(errorInfo);
        const type = this.getToastType(errorInfo.severity);
        
        // Use existing toast system if available
        if (window.showToast) {
            window.showToast(message, type, this.getToastDuration(errorInfo.severity));
        } else {
            this.showFallbackMessage(message, type);
        }
    }

    /**
     * Get user-friendly error message
     */
    getUserFriendlyMessage(errorInfo) {
        const messages = {
            [this.errorTypes.VALIDATION]: {
                [this.errorSeverity.LOW]: 'Please check your input and try again.',
                [this.errorSeverity.MEDIUM]: 'Some values need to be corrected. Please review the highlighted fields.',
                [this.errorSeverity.HIGH]: 'Invalid data detected. Please verify all inputs before proceeding.',
                [this.errorSeverity.CRITICAL]: 'Critical validation error. Please refresh and try again.'
            },
            [this.errorTypes.NETWORK]: {
                [this.errorSeverity.LOW]: 'Network issue detected. Your data is saved locally.',
                [this.errorSeverity.MEDIUM]: 'Connection problem. Please check your internet connection.',
                [this.errorSeverity.HIGH]: 'Unable to connect to server. Please try again later.',
                [this.errorSeverity.CRITICAL]: 'Server unavailable. Please contact support if this persists.'
            },
            [this.errorTypes.CALCULATION]: {
                [this.errorSeverity.LOW]: 'Calculation warning. Results may need review.',
                [this.errorSeverity.MEDIUM]: 'Calculation error detected. Please check your inputs.',
                [this.errorSeverity.HIGH]: 'Unable to complete calculation. Please verify your data.',
                [this.errorSeverity.CRITICAL]: 'Critical calculation failure. Please contact support.'
            },
            [this.errorTypes.AUTHENTICATION]: {
                [this.errorSeverity.LOW]: 'Session expired. Please log in again.',
                [this.errorSeverity.MEDIUM]: 'Authentication required. Please log in.',
                [this.errorSeverity.HIGH]: 'Access denied. Please check your credentials.',
                [this.errorSeverity.CRITICAL]: 'Security error. Please contact support immediately.'
            },
            [this.errorTypes.PERMISSION]: {
                [this.errorSeverity.LOW]: 'Limited access to this feature.',
                [this.errorSeverity.MEDIUM]: 'You don\'t have permission for this action.',
                [this.errorSeverity.HIGH]: 'Access denied. Contact your administrator.',
                [this.errorSeverity.CRITICAL]: 'Security violation detected.'
            },
            [this.errorTypes.RESOURCE]: {
                [this.errorSeverity.LOW]: 'Resource loading issue. Some features may be limited.',
                [this.errorSeverity.MEDIUM]: 'Unable to load some resources. Please refresh.',
                [this.errorSeverity.HIGH]: 'Critical resources failed to load.',
                [this.errorSeverity.CRITICAL]: 'Application resources unavailable.'
            },
            [this.errorTypes.SYSTEM]: {
                [this.errorSeverity.LOW]: 'Minor system issue detected.',
                [this.errorSeverity.MEDIUM]: 'System warning. Please save your work.',
                [this.errorSeverity.HIGH]: 'System error. Please refresh the page.',
                [this.errorSeverity.CRITICAL]: 'Critical system failure. Please contact support.'
            }
        };

        return messages[errorInfo.type]?.[errorInfo.severity] || 
               messages[this.errorTypes.SYSTEM][this.errorSeverity.MEDIUM];
    }

    /**
     * Get toast type based on severity
     */
    getToastType(severity) {
        switch (severity) {
            case this.errorSeverity.CRITICAL:
                return 'error';
            case this.errorSeverity.HIGH:
                return 'error';
            case this.errorSeverity.MEDIUM:
                return 'warning';
            default:
                return 'info';
        }
    }

    /**
     * Get toast duration based on severity
     */
    getToastDuration(severity) {
        switch (severity) {
            case this.errorSeverity.CRITICAL:
                return 8000;
            case this.errorSeverity.HIGH:
                return 6000;
            case this.errorSeverity.MEDIUM:
                return 4000;
            default:
                return 3000;
        }
    }

    /**
     * Show fallback message if toast system unavailable
     */
    showFallbackMessage(message, type) {
        const alert = document.createElement('div');
        alert.className = `error-alert error-alert-${type}`;
        alert.innerHTML = `
            <div class="error-alert-content">
                <span class="error-alert-message">${message}</span>
                <button class="error-alert-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Add styles if not present
        if (!document.getElementById('error-alert-styles')) {
            const style = document.createElement('style');
            style.id = 'error-alert-styles';
            style.textContent = `
                .error-alert {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 10000;
                    max-width: 400px;
                    padding: 12px;
                    border-radius: 6px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    animation: slideIn 0.3s ease-out;
                }
                .error-alert-error { background: #fee; border: 1px solid #fcc; color: #c33; }
                .error-alert-warning { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }
                .error-alert-info { background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }
                .error-alert-content { display: flex; align-items: center; justify-content: space-between; }
                .error-alert-close { background: none; border: none; font-size: 18px; cursor: pointer; opacity: 0.7; }
                .error-alert-close:hover { opacity: 1; }
                @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentElement) {
                alert.remove();
            }
        }, 5000);
    }

    /**
     * Report error to backend
     */
    async reportError(errorInfo) {
        if (!this.reportingEnabled || !window.backend || window.backend.status !== 'online') {
            return;
        }

        try {
            const response = await fetch('/api/errors', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'ValorIVX'
                },
                body: JSON.stringify({
                    error: errorInfo,
                    timestamp: new Date().toISOString(),
                    sessionId: this.getSessionId()
                })
            });

            if (!response.ok) {
                console.warn('[ErrorHandler] Failed to report error to backend');
            }
        } catch (error) {
            console.warn('[ErrorHandler] Error reporting failed:', error);
        }
    }

    /**
     * Flush error queue to backend
     */
    async flushErrorQueue() {
        if (this.errorHistory.length === 0) return;

        const errorsToReport = this.errorHistory.filter(error => 
            error.severity === this.errorSeverity.HIGH || 
            error.severity === this.errorSeverity.CRITICAL
        );

        if (errorsToReport.length === 0) return;

        try {
            const response = await fetch('/api/errors/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'ValorIVX'
                },
                body: JSON.stringify({
                    errors: errorsToReport,
                    timestamp: new Date().toISOString(),
                    sessionId: this.getSessionId()
                })
            });

            if (response.ok) {
                // Remove reported errors from history
                this.errorHistory = this.errorHistory.filter(error => 
                    !errorsToReport.includes(error)
                );
            }
        } catch (error) {
            console.warn('[ErrorHandler] Batch error reporting failed:', error);
        }
    }

    /**
     * Get session ID for error tracking
     */
    getSessionId() {
        if (!window.sessionStorage.getItem('valor_session_id')) {
            window.sessionStorage.setItem('valor_session_id', 
                `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
            );
        }
        return window.sessionStorage.getItem('valor_session_id');
    }

    /**
     * Get error statistics
     */
    getErrorStats() {
        const stats = {
            total: this.errorHistory.length,
            byType: {},
            bySeverity: {},
            recent: this.errorHistory.slice(0, 10)
        };

        // Count by type
        this.errorHistory.forEach(error => {
            stats.byType[error.type] = (stats.byType[error.type] || 0) + 1;
            stats.bySeverity[error.severity] = (stats.bySeverity[error.severity] || 0) + 1;
        });

        return stats;
    }

    /**
     * Clear error history
     */
    clearHistory() {
        this.errorHistory = [];
        this.errorCounts.clear();
    }

    /**
     * Enable/disable error reporting
     */
    setReportingEnabled(enabled) {
        this.reportingEnabled = enabled;
    }
}

// Create global error handler instance
window.errorHandler = new ErrorHandler();

// Export for module usage
export default window.errorHandler; 