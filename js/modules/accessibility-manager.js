/**
 * Accessibility Manager Module - Phase 5 Frontend UX and Reliability
 * Handles keyboard navigation, screen reader support, focus management, and WCAG compliance
 */

class AccessibilityManager {
    constructor() {
        this.focusableSelectors = [
            'a[href]',
            'button:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable="true"]'
        ];

        this.focusHistory = [];
        this.maxFocusHistory = 10;
        this.skipLinks = [];
        this.liveRegions = new Map();
        this.announcements = [];
        this.highContrastMode = false;
        this.reducedMotionMode = false;
        this.fontSize = 16;
        
        this.init();
    }

    init() {
        this.setupKeyboardNavigation();
        this.setupFocusManagement();
        this.setupLiveRegions();
        this.setupSkipLinks();
        this.setupHighContrastMode();
        this.setupReducedMotionMode();
        this.setupFontSizeControls();
        this.setupScreenReaderSupport();
        this.setupColorContrast();
        
        console.log('[AccessibilityManager] Initialized');
    }

    /**
     * Setup keyboard navigation
     */
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (event) => {
            this.handleKeyboardNavigation(event);
        });

        // Handle escape key for modals and overlays
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.handleEscapeKey(event);
            }
        });
    }

    /**
     * Handle keyboard navigation
     */
    handleKeyboardNavigation(event) {
        // Skip if user is typing in an input
        if (this.isTypingInInput(event.target)) {
            return;
        }

        switch (event.key) {
            case 'Tab':
                this.handleTabNavigation(event);
                break;
            case 'Enter':
            case ' ':
                this.handleActivation(event);
                break;
            case 'ArrowUp':
            case 'ArrowDown':
            case 'ArrowLeft':
            case 'ArrowRight':
                this.handleArrowNavigation(event);
                break;
        }
    }

    /**
     * Handle tab navigation
     */
    handleTabNavigation(event) {
        const focusableElements = this.getFocusableElements();
        const currentIndex = focusableElements.indexOf(document.activeElement);

        if (event.shiftKey) {
            // Shift + Tab: move backwards
            if (currentIndex <= 0) {
                event.preventDefault();
                focusableElements[focusableElements.length - 1].focus();
            }
        } else {
            // Tab: move forwards
            if (currentIndex >= focusableElements.length - 1) {
                event.preventDefault();
                focusableElements[0].focus();
            }
        }
    }

    /**
     * Handle activation keys (Enter, Space)
     */
    handleActivation(event) {
        const target = event.target;
        
        if (target.tagName === 'BUTTON' || target.role === 'button') {
            event.preventDefault();
            target.click();
        } else if (target.tagName === 'A') {
            event.preventDefault();
            target.click();
        }
    }

    /**
     * Handle arrow key navigation
     */
    handleArrowNavigation(event) {
        const target = event.target;
        
        // Handle radio button groups
        if (target.type === 'radio') {
            this.handleRadioGroupNavigation(event);
        }
        
        // Handle select elements
        if (target.tagName === 'SELECT') {
            this.handleSelectNavigation(event);
        }
        
        // Handle custom components
        if (target.dataset.arrowNavigation) {
            this.handleCustomArrowNavigation(event);
        }
    }

    /**
     * Handle radio button group navigation
     */
    handleRadioGroupNavigation(event) {
        const radioGroup = document.querySelectorAll(`input[name="${event.target.name}"]`);
        const currentIndex = Array.from(radioGroup).indexOf(event.target);
        
        if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
            event.preventDefault();
            const prevIndex = currentIndex > 0 ? currentIndex - 1 : radioGroup.length - 1;
            radioGroup[prevIndex].focus();
        } else if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
            event.preventDefault();
            const nextIndex = currentIndex < radioGroup.length - 1 ? currentIndex + 1 : 0;
            radioGroup[nextIndex].focus();
        }
    }

    /**
     * Handle select element navigation
     */
    handleSelectNavigation(event) {
        const select = event.target;
        const options = Array.from(select.options);
        const currentIndex = select.selectedIndex;
        
        if (event.key === 'ArrowUp') {
            event.preventDefault();
            const prevIndex = currentIndex > 0 ? currentIndex - 1 : options.length - 1;
            select.selectedIndex = prevIndex;
            select.dispatchEvent(new Event('change'));
        } else if (event.key === 'ArrowDown') {
            event.preventDefault();
            const nextIndex = currentIndex < options.length - 1 ? currentIndex + 1 : 0;
            select.selectedIndex = nextIndex;
            select.dispatchEvent(new Event('change'));
        }
    }

    /**
     * Handle custom arrow navigation
     */
    handleCustomArrowNavigation(event) {
        const navigationConfig = JSON.parse(event.target.dataset.arrowNavigation);
        const direction = event.key.includes('Left') || event.key.includes('Up') ? 'prev' : 'next';
        
        if (navigationConfig[direction]) {
            event.preventDefault();
            const targetElement = document.querySelector(navigationConfig[direction]);
            if (targetElement) {
                targetElement.focus();
            }
        }
    }

    /**
     * Handle escape key
     */
    handleEscapeKey(event) {
        // Close modals
        const modals = document.querySelectorAll('.modal, [role="dialog"]');
        modals.forEach(modal => {
            if (modal.style.display !== 'none') {
                this.closeModal(modal);
            }
        });

        // Close dropdowns
        const dropdowns = document.querySelectorAll('.dropdown, [aria-expanded="true"]');
        dropdowns.forEach(dropdown => {
            if (dropdown.getAttribute('aria-expanded') === 'true') {
                dropdown.setAttribute('aria-expanded', 'false');
            }
        });
    }

    /**
     * Setup focus management
     */
    setupFocusManagement() {
        // Track focus changes
        document.addEventListener('focusin', (event) => {
            this.handleFocusIn(event);
        });

        document.addEventListener('focusout', (event) => {
            this.handleFocusOut(event);
        });

        // Trap focus in modals
        this.setupFocusTrapping();
    }

    /**
     * Handle focus in
     */
    handleFocusIn(event) {
        const target = event.target;
        
        // Add to focus history
        this.addToFocusHistory(target);
        
        // Announce focus changes for screen readers
        this.announceFocusChange(target);
        
        // Update focus indicators
        this.updateFocusIndicators(target);
    }

    /**
     * Handle focus out
     */
    handleFocusOut(event) {
        const target = event.target;
        
        // Remove focus indicators
        this.removeFocusIndicators(target);
    }

    /**
     * Add element to focus history
     */
    addToFocusHistory(element) {
        this.focusHistory.unshift(element);
        
        // Keep history size manageable
        if (this.focusHistory.length > this.maxFocusHistory) {
            this.focusHistory = this.focusHistory.slice(0, this.maxFocusHistory);
        }
    }

    /**
     * Announce focus change
     */
    announceFocusChange(element) {
        const label = this.getElementLabel(element);
        if (label) {
            this.announce(`Focused: ${label}`);
        }
    }

    /**
     * Get element label for screen readers
     */
    getElementLabel(element) {
        // Check for aria-label
        if (element.getAttribute('aria-label')) {
            return element.getAttribute('aria-label');
        }
        
        // Check for aria-labelledby
        if (element.getAttribute('aria-labelledby')) {
            const labelElement = document.getElementById(element.getAttribute('aria-labelledby'));
            if (labelElement) {
                return labelElement.textContent;
            }
        }
        
        // Check for associated label
        if (element.id) {
            const label = document.querySelector(`label[for="${element.id}"]`);
            if (label) {
                return label.textContent;
            }
        }
        
        // Check for title attribute
        if (element.getAttribute('title')) {
            return element.getAttribute('title');
        }
        
        // Check for placeholder
        if (element.getAttribute('placeholder')) {
            return element.getAttribute('placeholder');
        }
        
        return element.textContent || element.tagName.toLowerCase();
    }

    /**
     * Update focus indicators
     */
    updateFocusIndicators(element) {
        // Add focus class
        element.classList.add('focus-visible');
        
        // Add focus ring
        element.style.outline = '2px solid #007acc';
        element.style.outlineOffset = '2px';
    }

    /**
     * Remove focus indicators
     */
    removeFocusIndicators(element) {
        element.classList.remove('focus-visible');
        element.style.outline = '';
        element.style.outlineOffset = '';
    }

    /**
     * Setup focus trapping for modals
     */
    setupFocusTrapping() {
        const modals = document.querySelectorAll('.modal, [role="dialog"]');
        
        modals.forEach(modal => {
            const focusableElements = this.getFocusableElements(modal);
            
            if (focusableElements.length > 0) {
                // Store first and last focusable elements
                modal.dataset.firstFocusable = focusableElements[0];
                modal.dataset.lastFocusable = focusableElements[focusableElements.length - 1];
            }
        });
    }

    /**
     * Setup live regions for screen readers
     */
    setupLiveRegions() {
        // Create live regions for different types of announcements
        const regions = [
            { id: 'status-live', ariaLive: 'polite', ariaAtomic: 'false' },
            { id: 'alert-live', ariaLive: 'assertive', ariaAtomic: 'true' },
            { id: 'log-live', ariaLive: 'polite', ariaAtomic: 'false' }
        ];

        regions.forEach(region => {
            const element = document.createElement('div');
            element.id = region.id;
            element.setAttribute('aria-live', region.ariaLive);
            element.setAttribute('aria-atomic', region.ariaAtomic);
            element.style.position = 'absolute';
            element.style.left = '-10000px';
            element.style.width = '1px';
            element.style.height = '1px';
            element.style.overflow = 'hidden';
            
            document.body.appendChild(element);
            this.liveRegions.set(region.id, element);
        });
    }

    /**
     * Announce message to screen readers
     */
    announce(message, type = 'status') {
        const regionId = type === 'alert' ? 'alert-live' : 'status-live';
        const region = this.liveRegions.get(regionId);
        
        if (region) {
            region.textContent = message;
            
            // Clear after a short delay
            setTimeout(() => {
                region.textContent = '';
            }, 1000);
        }
    }

    /**
     * Setup skip links
     */
    setupSkipLinks() {
        const skipLinks = [
            { href: '#main-content', text: 'Skip to main content' },
            { href: '#navigation', text: 'Skip to navigation' },
            { href: '#footer', text: 'Skip to footer' }
        ];

        skipLinks.forEach(link => {
            const skipLink = document.createElement('a');
            skipLink.href = link.href;
            skipLink.textContent = link.text;
            skipLink.className = 'skip-link';
            skipLink.style.cssText = `
                position: absolute;
                top: -40px;
                left: 6px;
                background: #000;
                color: #fff;
                padding: 8px;
                text-decoration: none;
                z-index: 10000;
                transition: top 0.3s;
            `;
            
            skipLink.addEventListener('focus', () => {
                skipLink.style.top = '6px';
            });
            
            skipLink.addEventListener('blur', () => {
                skipLink.style.top = '-40px';
            });
            
            document.body.appendChild(skipLink);
            this.skipLinks.push(skipLink);
        });
    }

    /**
     * Setup high contrast mode
     */
    setupHighContrastMode() {
        // Check for user preference
        if (window.matchMedia && window.matchMedia('(prefers-contrast: high)').matches) {
            this.enableHighContrastMode();
        }

        // Listen for preference changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-contrast: high)').addEventListener('change', (e) => {
                if (e.matches) {
                    this.enableHighContrastMode();
                } else {
                    this.disableHighContrastMode();
                }
            });
        }
    }

    /**
     * Enable high contrast mode
     */
    enableHighContrastMode() {
        this.highContrastMode = true;
        document.body.classList.add('high-contrast');
        
        // Add high contrast styles
        if (!document.getElementById('high-contrast-styles')) {
            const style = document.createElement('style');
            style.id = 'high-contrast-styles';
            style.textContent = `
                .high-contrast {
                    filter: contrast(150%) brightness(110%);
                }
                .high-contrast * {
                    border-color: #000 !important;
                }
                .high-contrast button,
                .high-contrast input,
                .high-contrast select {
                    background: #fff !important;
                    color: #000 !important;
                    border: 2px solid #000 !important;
                }
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Disable high contrast mode
     */
    disableHighContrastMode() {
        this.highContrastMode = false;
        document.body.classList.remove('high-contrast');
    }

    /**
     * Setup reduced motion mode
     */
    setupReducedMotionMode() {
        // Check for user preference
        if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            this.enableReducedMotionMode();
        }

        // Listen for preference changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
                if (e.matches) {
                    this.enableReducedMotionMode();
                } else {
                    this.disableReducedMotionMode();
                }
            });
        }
    }

    /**
     * Enable reduced motion mode
     */
    enableReducedMotionMode() {
        this.reducedMotionMode = true;
        document.body.classList.add('reduced-motion');
        
        // Add reduced motion styles
        if (!document.getElementById('reduced-motion-styles')) {
            const style = document.createElement('style');
            style.id = 'reduced-motion-styles';
            style.textContent = `
                .reduced-motion *,
                .reduced-motion *::before,
                .reduced-motion *::after {
                    animation-duration: 0.01ms !important;
                    animation-iteration-count: 1 !important;
                    transition-duration: 0.01ms !important;
                }
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Disable reduced motion mode
     */
    disableReducedMotionMode() {
        this.reducedMotionMode = false;
        document.body.classList.remove('reduced-motion');
    }

    /**
     * Setup font size controls
     */
    setupFontSizeControls() {
        // Create font size controls
        const controls = document.createElement('div');
        controls.className = 'accessibility-controls';
        controls.innerHTML = `
            <button id="increase-font" aria-label="Increase font size">A+</button>
            <button id="decrease-font" aria-label="Decrease font size">A-</button>
            <button id="reset-font" aria-label="Reset font size">A</button>
        `;
        controls.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 1000;
            background: #fff;
            border: 1px solid #ccc;
            padding: 5px;
            border-radius: 4px;
        `;
        
        document.body.appendChild(controls);
        
        // Add event listeners
        document.getElementById('increase-font').addEventListener('click', () => {
            this.changeFontSize(2);
        });
        
        document.getElementById('decrease-font').addEventListener('click', () => {
            this.changeFontSize(-2);
        });
        
        document.getElementById('reset-font').addEventListener('click', () => {
            this.resetFontSize();
        });
    }

    /**
     * Change font size
     */
    changeFontSize(delta) {
        this.fontSize = Math.max(12, Math.min(24, this.fontSize + delta));
        document.documentElement.style.fontSize = `${this.fontSize}px`;
        
        // Save preference
        localStorage.setItem('valor-font-size', this.fontSize);
        
        this.announce(`Font size changed to ${this.fontSize} pixels`);
    }

    /**
     * Reset font size
     */
    resetFontSize() {
        this.fontSize = 16;
        document.documentElement.style.fontSize = '';
        localStorage.removeItem('valor-font-size');
        this.announce('Font size reset to default');
    }

    /**
     * Setup screen reader support
     */
    setupScreenReaderSupport() {
        // Add ARIA landmarks
        this.addAriaLandmarks();
        
        // Add ARIA labels
        this.addAriaLabels();
        
        // Setup form validation announcements
        this.setupFormValidationAnnouncements();
    }

    /**
     * Add ARIA landmarks
     */
    addAriaLandmarks() {
        // Main content
        const main = document.querySelector('main') || document.querySelector('#main-content');
        if (main) {
            main.setAttribute('role', 'main');
        }
        
        // Navigation
        const nav = document.querySelector('nav') || document.querySelector('#navigation');
        if (nav) {
            nav.setAttribute('role', 'navigation');
        }
        
        // Banner
        const header = document.querySelector('header') || document.querySelector('#header');
        if (header) {
            header.setAttribute('role', 'banner');
        }
        
        // Content info
        const footer = document.querySelector('footer') || document.querySelector('#footer');
        if (footer) {
            footer.setAttribute('role', 'contentinfo');
        }
    }

    /**
     * Add ARIA labels
     */
    addAriaLabels() {
        // Add labels to form controls
        const inputs = document.querySelectorAll('input:not([aria-label]):not([aria-labelledby])');
        inputs.forEach(input => {
            if (input.type !== 'hidden' && !input.id) {
                input.id = `input-${Math.random().toString(36).substr(2, 9)}`;
            }
        });
        
        // Add labels to buttons
        const buttons = document.querySelectorAll('button:not([aria-label])');
        buttons.forEach(button => {
            if (!button.textContent.trim()) {
                button.setAttribute('aria-label', 'Button');
            }
        });
    }

    /**
     * Setup form validation announcements
     */
    setupFormValidationAnnouncements() {
        document.addEventListener('invalid', (event) => {
            const element = event.target;
            const message = element.validationMessage;
            this.announce(`Validation error: ${message}`, 'alert');
        });
        
        document.addEventListener('input', (event) => {
            const element = event.target;
            if (element.validity.valid && element.dataset.wasInvalid) {
                delete element.dataset.wasInvalid;
                this.announce('Validation error cleared');
            } else if (!element.validity.valid) {
                element.dataset.wasInvalid = 'true';
            }
        });
    }

    /**
     * Setup color contrast checking
     */
    setupColorContrast() {
        // Check color contrast for text elements
        const textElements = document.querySelectorAll('p, span, div, h1, h2, h3, h4, h5, h6');
        textElements.forEach(element => {
            this.checkColorContrast(element);
        });
    }

    /**
     * Check color contrast
     */
    checkColorContrast(element) {
        const style = window.getComputedStyle(element);
        const backgroundColor = style.backgroundColor;
        const color = style.color;
        
        // Simple contrast check (in production, use a proper contrast calculation library)
        if (backgroundColor === 'rgba(0, 0, 0, 0)' || color === 'rgba(0, 0, 0, 0)') {
            console.warn('[AccessibilityManager] Low contrast detected:', element);
        }
    }

    /**
     * Get focusable elements
     */
    getFocusableElements(container = document) {
        const elements = container.querySelectorAll(this.focusableSelectors.join(', '));
        return Array.from(elements).filter(element => {
            // Filter out hidden elements
            const style = window.getComputedStyle(element);
            return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
        });
    }

    /**
     * Check if user is typing in an input
     */
    isTypingInInput(element) {
        return element.tagName === 'INPUT' || 
               element.tagName === 'TEXTAREA' || 
               element.contentEditable === 'true';
    }

    /**
     * Close modal
     */
    closeModal(modal) {
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
        
        // Restore focus to previous element
        if (this.focusHistory.length > 0) {
            this.focusHistory[0].focus();
        }
    }

    /**
     * Get accessibility status
     */
    getStatus() {
        return {
            highContrastMode: this.highContrastMode,
            reducedMotionMode: this.reducedMotionMode,
            fontSize: this.fontSize,
            focusHistoryLength: this.focusHistory.length,
            liveRegionsCount: this.liveRegions.size,
            skipLinksCount: this.skipLinks.length
        };
    }
}

// Create global accessibility manager instance
window.accessibilityManager = new AccessibilityManager();

// Export for module usage
export default window.accessibilityManager; 