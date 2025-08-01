/**
 * VALOR IVX - UNIFIED SHELL
 * Single Page Application Router and Shell Management
 * 
 * This module implements:
 * - SPA routing between modules
 * - Progressive disclosure interactions
 * - Smooth animations and transitions
 * - State management for the shell
 */

class ValorShell {
  constructor() {
    this.currentModule = 'dcf';
    this.isLoading = false;
    this.moduleCache = new Map();
    
    this.init();
  }
  
  async init() {
    console.log('🚀 Initializing Valor IVX Shell...');
    
    // Bind event listeners
    this.bindNavigationEvents();
    this.bindProgressiveDisclosure();
    this.bindKeyboardShortcuts();
    this.bindRunAnalysisEvents();
    
    // Initialize the current module
    await this.loadModule(this.currentModule);
    
    // Setup performance monitoring
    this.setupPerformanceMonitoring();
    
    console.log('✅ Shell initialized successfully');
  }
  
  /**
   * Navigation Events - Handle module switching
   */
  bindNavigationEvents() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
      item.addEventListener('click', async (e) => {
        const module = e.currentTarget.dataset.module;
        if (module && module !== this.currentModule) {
          await this.switchModule(module);
        }
      });
      
      // Keyboard navigation
      item.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          const module = e.currentTarget.dataset.module;
          if (module && module !== this.currentModule) {
            await this.switchModule(module);
          }
        }
      });
    });
  }
  
  /**
   * Progressive Disclosure - Handle collapsible sections
   */
  bindProgressiveDisclosure() {
    const collapsibleSections = document.querySelectorAll('.collapsible-section');
    
    collapsibleSections.forEach(section => {
      const header = section.querySelector('.section-header');
      const content = section.querySelector('.section-content');
      
      if (header && content) {
        header.addEventListener('click', () => {
          this.toggleSection(header, content);
        });
        
        header.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            this.toggleSection(header, content);
          }
        });
      }
    });
  }
  
  /**
   * Toggle section with smooth animation
   */
  toggleSection(header, content) {
    const isExpanded = header.getAttribute('aria-expanded') === 'true';
    const newState = !isExpanded;
    
    header.setAttribute('aria-expanded', newState.toString());
    content.setAttribute('aria-hidden', (!newState).toString());
    
    // Add subtle animation feedback
    if (newState) {
      // Expanding
      content.style.transition = 'all 350ms cubic-bezier(0.4, 0, 0.2, 1)';
      requestAnimationFrame(() => {
        content.style.maxHeight = content.scrollHeight + 'px';
        content.style.opacity = '1';
      });
    } else {
      // Collapsing
      content.style.transition = 'all 250ms cubic-bezier(0.4, 0, 0.2, 1)';
      content.style.maxHeight = '0';
      content.style.opacity = '0';
    }
    
    // Provide haptic feedback if available
    if ('vibrate' in navigator) {
      navigator.vibrate(10);
    }
  }
  
  /**
   * Keyboard Shortcuts
   */
  bindKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Global shortcuts
      if (e.key === 'Enter' && !e.target.matches('input, textarea, button')) {
        e.preventDefault();
        this.runAnalysis();
      }
      
      if (e.key.toLowerCase() === 'p' && !e.target.matches('input, textarea')) {
        e.preventDefault();
        this.loadPresetData();
      }
      
      // Module switching shortcuts
      if (e.altKey) {
        switch(e.key) {
          case '1':
            e.preventDefault();
            this.switchModule('dcf');
            break;
          case '2':
            e.preventDefault();
            this.switchModule('lbo');
            break;
          case '3':
            e.preventDefault();
            this.switchModule('ma');
            break;
          case '4':
            e.preventDefault();
            this.switchModule('real-options');
            break;
        }
      }
    });
  }
  
  /**
   * Run Analysis Events
   */
  bindRunAnalysisEvents() {
    const runButtons = document.querySelectorAll('#runAnalysis, #runModelButton');
    
    runButtons.forEach(button => {
      button.addEventListener('click', () => {
        this.runAnalysis();
      });
    });
  }
  
  /**
   * Module switching with smooth transitions
   */
  async switchModule(moduleId) {
    if (this.isLoading || moduleId === this.currentModule) return;
    
    console.log(`🔄 Switching from ${this.currentModule} to ${moduleId}`);
    
    try {
      this.setLoadingState(true);
      
      // Update navigation state
      this.updateNavigationState(moduleId);
      
      // Hide current module with animation
      await this.hideCurrentModule();
      
      // Load and show new module
      await this.loadModule(moduleId);
      await this.showModule(moduleId);
      
      this.currentModule = moduleId;
      
      // Update document title
      this.updateDocumentTitle(moduleId);
      
      // Update URL without page reload
      this.updateURL(moduleId);
      
    } catch (error) {
      console.error('❌ Error switching modules:', error);
      this.showError('Failed to switch modules. Please try again.');
    } finally {
      this.setLoadingState(false);
    }
  }
  
  /**
   * Update navigation visual state
   */
  updateNavigationState(activeModule) {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
      const isActive = item.dataset.module === activeModule;
      
      item.classList.toggle('active', isActive);
      item.setAttribute('aria-current', isActive ? 'page' : 'false');
    });
  }
  
  /**
   * Hide current module with fade out
   */
  async hideCurrentModule() {
    const currentModuleElement = document.querySelector(`#${this.currentModule}-module`);
    if (!currentModuleElement) return;
    
    return new Promise(resolve => {
      currentModuleElement.style.transition = 'all 250ms cubic-bezier(0.4, 0, 0.2, 1)';
      currentModuleElement.style.opacity = '0';
      currentModuleElement.style.transform = 'translateY(-8px)';
      
      setTimeout(() => {
        currentModuleElement.style.display = 'none';
        currentModuleElement.classList.remove('active');
        resolve();
      }, 250);
    });
  }
  
  /**
   * Show module with fade in
   */
  async showModule(moduleId) {
    const moduleElement = document.querySelector(`#${moduleId}-module`);
    if (!moduleElement) return;
    
    return new Promise(resolve => {
      moduleElement.style.display = 'flex';
      moduleElement.style.opacity = '0';
      moduleElement.style.transform = 'translateY(8px)';
      
      requestAnimationFrame(() => {
        moduleElement.style.transition = 'all 350ms cubic-bezier(0.4, 0, 0.2, 1)';
        moduleElement.style.opacity = '1';
        moduleElement.style.transform = 'translateY(0)';
        moduleElement.classList.add('active');
        
        setTimeout(resolve, 350);
      });
    });
  }
  
  /**
   * Load module content (placeholder for now)
   */
  async loadModule(moduleId) {
    if (this.moduleCache.has(moduleId)) {
      console.log(`📦 Module ${moduleId} loaded from cache`);
      return this.moduleCache.get(moduleId);
    }
    
    // Simulate module loading (replace with actual module loading logic)
    const moduleData = {
      dcf: { name: 'DCF Analysis', loaded: true },
      lbo: { name: 'LBO Analysis', loaded: true },
      ma: { name: 'M&A Analysis', loaded: true },
      'real-options': { name: 'Real Options Analysis', loaded: true }
    };
    
    // Simulate async loading
    await new Promise(resolve => setTimeout(resolve, 100));
    
    this.moduleCache.set(moduleId, moduleData[moduleId]);
    console.log(`✅ Module ${moduleId} loaded`);
    
    return moduleData[moduleId];
  }
  
  /**
   * Set loading state
   */
  setLoadingState(isLoading) {
    this.isLoading = isLoading;
    const loadingElement = document.getElementById('shell-loading');
    
    if (loadingElement) {
      loadingElement.setAttribute('aria-hidden', (!isLoading).toString());
    }
  }
  
  /**
   * Update document title
   */
  updateDocumentTitle(moduleId) {
    const titles = {
      dcf: 'DCF Analysis — Valor IVX',
      lbo: 'LBO Analysis — Valor IVX',
      ma: 'M&A Analysis — Valor IVX',
      'real-options': 'Real Options — Valor IVX'
    };
    
    document.title = titles[moduleId] || 'Valor IVX — Financial Analysis Platform';
  }
  
  /**
   * Update URL without page reload
   */
  updateURL(moduleId) {
    const url = moduleId === 'dcf' ? '/' : `/${moduleId}`;
    history.pushState({ module: moduleId }, '', url);
  }
  
  /**
   * Run analysis with visual feedback
   */
  async runAnalysis() {
    console.log(`🔬 Running ${this.currentModule.toUpperCase()} analysis...`);
    
    // Update status indicators
    this.updateStatus('input-status', 'Processing...', 'active');
    this.updateStatus('output-status', 'Calculating...', 'active');
    
    // Add loading state to run buttons
    const runButtons = document.querySelectorAll('#runAnalysis, #runModelButton');
    runButtons.forEach(button => {
      button.classList.add('loading');
      button.disabled = true;
    });
    
    try {
      // Simulate analysis (replace with actual analysis logic)
      await this.simulateAnalysis();
      
      // Update results
      this.updateResults();
      
      // Success feedback
      this.updateStatus('input-status', 'Complete', 'success');
      this.updateStatus('output-status', 'Updated', 'success');
      
      console.log('✅ Analysis completed successfully');
      
    } catch (error) {
      console.error('❌ Analysis failed:', error);
      this.updateStatus('input-status', 'Error', 'error');
      this.updateStatus('output-status', 'Failed', 'error');
      this.showError('Analysis failed. Please check your inputs and try again.');
    } finally {
      // Remove loading state
      runButtons.forEach(button => {
        button.classList.remove('loading');
        button.disabled = false;
      });
    }
  }
  
  /**
   * Simulate analysis process
   */
  async simulateAnalysis() {
    // Simulate processing time
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Add some realistic randomness
    if (Math.random() < 0.05) {
      throw new Error('Simulation error for testing');
    }
  }
  
  /**
   * Update results display
   */
  updateResults() {
    // Sample result updates (replace with actual calculation results)
    const results = {
      psVal: '$42.75',
      evVal: '$6,412.5M',
      eqVal: '$6,112.5M'
    };
    
    Object.entries(results).forEach(([id, value]) => {
      const element = document.getElementById(id);
      if (element) {
        // Animate value change
        element.style.transition = 'all 250ms cubic-bezier(0.4, 0, 0.2, 1)';
        element.style.opacity = '0.5';
        
        setTimeout(() => {
          element.textContent = value;
          element.style.opacity = '1';
        }, 125);
      }
    });
  }
  
  /**
   * Update status indicators
   */
  updateStatus(elementId, text, state = '') {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.textContent = text;
    element.className = 'status-indicator';
    
    if (state) {
      element.classList.add(state);
    }
  }
  
  /**
   * Load preset data
   */
  loadPresetData() {
    console.log('📋 Loading preset data...');
    
    // Sample preset values
    const presets = {
      ticker: 'DEMO',
      revenue: '750',
      growthY1: '15',
      termGrowth: '3.0',
      wacc: '8.5',
      ebitMargin: '25',
      taxRate: '21',
      salesToCap: '3.0'
    };
    
    Object.entries(presets).forEach(([id, value]) => {
      const input = document.getElementById(id);
      if (input) {
        // Animate input changes
        input.style.transition = 'all 200ms cubic-bezier(0.4, 0, 0.2, 1)';
        input.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
        input.value = value;
        
        setTimeout(() => {
          input.style.backgroundColor = '';
        }, 500);
      }
    });
    
    // Provide feedback
    const hint = document.createElement('div');
    hint.textContent = 'Preset data loaded';
    hint.style.cssText = `
      position: fixed;
      top: 80px;
      right: 24px;
      background: var(--accent-success);
      color: white;
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 500;
      box-shadow: var(--shadow-lg);
      z-index: 1000;
      opacity: 0;
      transform: translateY(-8px);
      transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
    `;
    
    document.body.appendChild(hint);
    
    requestAnimationFrame(() => {
      hint.style.opacity = '1';
      hint.style.transform = 'translateY(0)';
    });
    
    setTimeout(() => {
      hint.style.opacity = '0';
      hint.style.transform = 'translateY(-8px)';
      setTimeout(() => hint.remove(), 250);
    }, 2000);
  }
  
  /**
   * Show error message
   */
  showError(message) {
    const error = document.createElement('div');
    error.textContent = message;
    error.style.cssText = `
      position: fixed;
      top: 80px;
      right: 24px;
      background: var(--accent-error);
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 500;
      box-shadow: var(--shadow-lg);
      z-index: 1000;
      max-width: 300px;
      opacity: 0;
      transform: translateY(-8px);
      transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
    `;
    
    document.body.appendChild(error);
    
    requestAnimationFrame(() => {
      error.style.opacity = '1';
      error.style.transform = 'translateY(0)';
    });
    
    setTimeout(() => {
      error.style.opacity = '0';
      error.style.transform = 'translateY(-8px)';
      setTimeout(() => error.remove(), 250);
    }, 4000);
  }
  
  /**
   * Setup performance monitoring
   */
  setupPerformanceMonitoring() {
    // Monitor long tasks
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.duration > 50) {
              console.warn(`⚠️ Long task detected: ${entry.duration.toFixed(1)}ms`);
            }
          }
        });
        observer.observe({ entryTypes: ['longtask'] });
      } catch (e) {
        console.log('PerformanceObserver not supported');
      }
    }
    
    // Monitor navigation timing
    window.addEventListener('load', () => {
      setTimeout(() => {
        const navigation = performance.getEntriesByType('navigation')[0];
        if (navigation) {
          console.log(`📊 Page load time: ${navigation.loadEventEnd - navigation.loadEventStart}ms`);
        }
      }, 0);
    });
  }
}

// Initialize the shell when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.valorShell = new ValorShell();
  });
} else {
  window.valorShell = new ValorShell();
}

// Handle browser back/forward
window.addEventListener('popstate', (e) => {
  if (e.state && e.state.module && window.valorShell) {
    window.valorShell.switchModule(e.state.module);
  }
});

// Export for module usage
export default ValorShell;