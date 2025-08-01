/**
 * VALOR IVX - DCF CORE MODULE
 * Discounted Cash Flow Analysis Engine
 * 
 * This module handles:
 * - DCF calculations
 * - Sensitivity analysis
 * - Chart updates
 * - Input validation
 */

class DCFCore {
  constructor() {
    this.inputs = {};
    this.results = {};
    this.charts = {};
    
    this.init();
  }
  
  init() {
    console.log('📊 Initializing DCF Core Module...');
    
    this.bindInputEvents();
    this.initializeCharts();
    this.setupValidation();
    
    console.log('✅ DCF Core Module initialized');
  }
  
  /**
   * Bind input change events for real-time feedback
   */
  bindInputEvents() {
    const inputs = document.querySelectorAll('#dcf-module .input-field');
    
    inputs.forEach(input => {
      input.addEventListener('input', (e) => {
        this.validateInput(e.target);
        this.updatePreview();
      });
      
      input.addEventListener('blur', (e) => {
        this.formatInput(e.target);
      });
      
      // Add subtle hover effects
      input.addEventListener('mouseenter', (e) => {
        if (!e.target.matches(':focus')) {
          e.target.style.transform = 'translateY(-1px)';
        }
      });
      
      input.addEventListener('mouseleave', (e) => {
        if (!e.target.matches(':focus')) {
          e.target.style.transform = 'translateY(0)';
        }
      });
    });
  }
  
  /**
   * Validate individual input
   */
  validateInput(input) {
    const value = parseFloat(input.value);
    const id = input.id;
    let isValid = true;
    let validationType = '';
    
    // Remove existing validation classes
    input.removeAttribute('data-validation');
    
    if (isNaN(value)) {
      if (input.value.trim() !== '' && id !== 'ticker') {
        isValid = false;
        validationType = 'error';
      }
    } else {
      // Value-specific validations
      switch (id) {
        case 'revenue':
          if (value <= 0) {
            isValid = false;
            validationType = 'error';
          } else if (value > 100000) {
            validationType = 'warning';
          }
          break;
          
        case 'growthY1':
          if (value < -50 || value > 100) {
            isValid = false;
            validationType = 'error';
          } else if (value > 50) {
            validationType = 'warning';
          }
          break;
          
        case 'termGrowth':
          if (value < 0 || value > 10) {
            isValid = false;
            validationType = 'error';
          } else if (value > 5) {
            validationType = 'warning';
          }
          break;
          
        case 'wacc':
          if (value <= 0 || value > 50) {
            isValid = false;
            validationType = 'error';
          } else if (value > 20) {
            validationType = 'warning';
          }
          break;
          
        case 'ebitMargin':
          if (value < 0 || value > 100) {
            isValid = false;
            validationType = 'error';
          } else if (value > 50) {
            validationType = 'warning';
          }
          break;
          
        case 'taxRate':
          if (value < 0 || value > 100) {
            isValid = false;
            validationType = 'error';
          }
          break;
          
        case 'salesToCap':
          if (value <= 0) {
            isValid = false;
            validationType = 'error';
          } else if (value > 10) {
            validationType = 'warning';
          }
          break;
      }
    }
    
    // Apply validation styling
    if (validationType) {
      input.setAttribute('data-validation', validationType);
    }
    
    return isValid;
  }
  
  /**
   * Format input values
   */
  formatInput(input) {
    const value = parseFloat(input.value);
    const id = input.id;
    
    if (!isNaN(value)) {
      switch (id) {
        case 'revenue':
        case 'shares':
        case 'netDebt':
          input.value = value.toFixed(2);
          break;
          
        case 'growthY1':
        case 'termGrowth':
        case 'wacc':
        case 'ebitMargin':
        case 'taxRate':
        case 'waccMin':
        case 'waccMax':
        case 'tgMin':
        case 'tgMax':
          input.value = value.toFixed(1);
          break;
          
        case 'salesToCap':
          input.value = value.toFixed(2);
          break;
      }
    }
  }
  
  /**
   * Update real-time preview
   */
  updatePreview() {
    // Collect current input values
    this.collectInputs();
    
    // Quick validation check
    if (!this.validateAllInputs()) {
      return;
    }
    
    // Update preview calculations (simplified)
    this.updateQuickMetrics();
  }
  
  /**
   * Collect all input values
   */
  collectInputs() {
    const inputs = {
      ticker: document.getElementById('ticker')?.value || 'SAMPLE',
      revenue: parseFloat(document.getElementById('revenue')?.value) || 500,
      growthY1: parseFloat(document.getElementById('growthY1')?.value) || 12,
      termGrowth: parseFloat(document.getElementById('termGrowth')?.value) || 2.5,
      wacc: parseFloat(document.getElementById('wacc')?.value) || 9.0,
      ebitMargin: parseFloat(document.getElementById('ebitMargin')?.value) || 22,
      taxRate: parseFloat(document.getElementById('taxRate')?.value) || 23,
      salesToCap: parseFloat(document.getElementById('salesToCap')?.value) || 2.5,
      shares: parseFloat(document.getElementById('shares')?.value) || 150,
      netDebt: parseFloat(document.getElementById('netDebt')?.value) || 300,
      waccMin: parseFloat(document.getElementById('waccMin')?.value) || 7,
      waccMax: parseFloat(document.getElementById('waccMax')?.value) || 12,
      tgMin: parseFloat(document.getElementById('tgMin')?.value) || 1.0,
      tgMax: parseFloat(document.getElementById('tgMax')?.value) || 3.5
    };
    
    this.inputs = inputs;
    return inputs;
  }
  
  /**
   * Validate all inputs
   */
  validateAllInputs() {
    const requiredFields = ['revenue', 'growthY1', 'termGrowth', 'wacc', 'ebitMargin', 'taxRate', 'salesToCap', 'shares'];
    
    for (const field of requiredFields) {
      const input = document.getElementById(field);
      if (!input || !this.validateInput(input)) {
        return false;
      }
    }
    
    return true;
  }
  
  /**
   * Update quick metrics for preview
   */
  updateQuickMetrics() {
    try {
      const { revenue, growthY1, termGrowth, wacc, ebitMargin, taxRate, salesToCap, shares, netDebt } = this.inputs;
      
      // Simplified DCF calculation for preview
      const year1Revenue = revenue * (1 + growthY1 / 100);
      const year1EBIT = year1Revenue * (ebitMargin / 100);
      const year1NOPAT = year1EBIT * (1 - taxRate / 100);
      const year1FCFF = year1NOPAT - (year1Revenue - revenue) / salesToCap;
      
      // Simple terminal value (Gordon Growth Model)
      const terminalFCFF = year1FCFF * (1 + termGrowth / 100);
      const terminalValue = terminalFCFF / ((wacc - termGrowth) / 100);
      
      // Present values
      const pvFCFF = year1FCFF / (1 + wacc / 100);
      const pvTerminal = terminalValue / (1 + wacc / 100);
      const enterpriseValue = pvFCFF + pvTerminal;
      const equityValue = enterpriseValue - netDebt;
      const perShare = equityValue / shares;
      
      // Update display with smooth animation
      this.updateMetricDisplay('evVal', this.formatCurrency(enterpriseValue, 'M'));
      this.updateMetricDisplay('eqVal', this.formatCurrency(equityValue, 'M'));
      this.updateMetricDisplay('psVal', this.formatCurrency(perShare));
      
    } catch (error) {
      console.warn('Preview calculation error:', error);
    }
  }
  
  /**
   * Update metric display with animation
   */
  updateMetricDisplay(elementId, value) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Only update if value changed
    if (element.textContent === value) return;
    
    element.style.transition = 'all 200ms cubic-bezier(0.4, 0, 0.2, 1)';
    element.style.opacity = '0.6';
    element.style.transform = 'scale(0.98)';
    
    setTimeout(() => {
      element.textContent = value;
      element.style.opacity = '1';
      element.style.transform = 'scale(1)';
    }, 100);
  }
  
  /**
   * Format currency values
   */
  formatCurrency(value, unit = '') {
    if (isNaN(value) || !isFinite(value)) return '—';
    
    const absValue = Math.abs(value);
    const sign = value < 0 ? '-' : '';
    
    if (unit === 'M') {
      return `${sign}$${absValue.toFixed(1)}M`;
    } else {
      return `${sign}$${absValue.toFixed(2)}`;
    }
  }
  
  /**
   * Initialize placeholder charts
   */
  initializeCharts() {
    const primaryChart = document.getElementById('primaryChart');
    const sensitivityChart = document.getElementById('sensitivityChart');
    
    if (primaryChart) {
      this.initializePrimaryChart(primaryChart);
    }
    
    if (sensitivityChart) {
      this.initializeSensitivityChart(sensitivityChart);
    }
  }
  
  /**
   * Initialize primary chart (placeholder)
   */
  initializePrimaryChart(canvas) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Set styles
    ctx.fillStyle = '#1A2332';
    ctx.fillRect(0, 0, width, height);
    
    // Add placeholder content
    ctx.fillStyle = '#B8C5D1';
    ctx.font = '16px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Free Cash Flow Chart', width / 2, height / 2 - 10);
    ctx.fillText('Run analysis to view projection', width / 2, height / 2 + 15);
  }
  
  /**
   * Initialize sensitivity chart (placeholder)
   */
  initializeSensitivityChart(canvas) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Set styles
    ctx.fillStyle = '#1A2332';
    ctx.fillRect(0, 0, width, height);
    
    // Add placeholder content
    ctx.fillStyle = '#B8C5D1';
    ctx.font = '16px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Sensitivity Heatmap', width / 2, height / 2 - 10);
    ctx.fillText('Run analysis to view sensitivity', width / 2, height / 2 + 15);
  }
  
  /**
   * Setup input validation feedback
   */
  setupValidation() {
    // Add validation tooltips
    const style = document.createElement('style');
    style.textContent = `
      .input-field[data-validation="error"]::after {
        content: '';
        position: absolute;
        right: 8px;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 4px;
        background: var(--accent-error);
        border-radius: 50%;
        pointer-events: none;
      }
      
      .input-field[data-validation="warning"]::after {
        content: '';
        position: absolute;
        right: 8px;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 4px;
        background: var(--accent-warning);
        border-radius: 50%;
        pointer-events: none;
      }
    `;
    document.head.appendChild(style);
  }
  
  /**
   * Run full DCF analysis
   */
  async runAnalysis() {
    console.log('🔬 Running DCF Analysis...');
    
    if (!this.validateAllInputs()) {
      throw new Error('Please fix input validation errors before running analysis');
    }
    
    this.collectInputs();
    
    // Simulate analysis process
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Calculate results
    this.calculateDCF();
    
    // Update charts
    this.updateCharts();
    
    console.log('✅ DCF Analysis completed');
  }
  
  /**
   * Calculate DCF (simplified version)
   */
  calculateDCF() {
    const { revenue, growthY1, termGrowth, wacc, ebitMargin, taxRate, salesToCap, shares, netDebt } = this.inputs;
    
    // Multi-year projection (simplified)
    const years = 5;
    const projections = [];
    
    let currentRevenue = revenue;
    let currentGrowth = growthY1;
    
    for (let year = 1; year <= years; year++) {
      currentRevenue *= (1 + currentGrowth / 100);
      const ebit = currentRevenue * (ebitMargin / 100);
      const nopat = ebit * (1 - taxRate / 100);
      const reinvestment = (currentRevenue - projections[year - 2]?.revenue || revenue) / salesToCap;
      const fcff = nopat - reinvestment;
      
      projections.push({
        year,
        revenue: currentRevenue,
        growth: currentGrowth,
        ebit,
        nopat,
        fcff,
        pvFcff: fcff / Math.pow(1 + wacc / 100, year)
      });
      
      // Decay growth
      currentGrowth = Math.max(termGrowth, currentGrowth - 1.5);
    }
    
    // Terminal value
    const lastYear = projections[projections.length - 1];
    const terminalFCFF = lastYear.fcff * (1 + termGrowth / 100);
    const terminalValue = terminalFCFF / ((wacc - termGrowth) / 100);
    const pvTerminal = terminalValue / Math.pow(1 + wacc / 100, years);
    
    // Enterprise and equity value
    const sumPvFcff = projections.reduce((sum, p) => sum + p.pvFcff, 0);
    const enterpriseValue = sumPvFcff + pvTerminal;
    const equityValue = enterpriseValue - netDebt;
    const perShare = equityValue / shares;
    
    this.results = {
      projections,
      terminalValue,
      pvTerminal,
      enterpriseValue,
      equityValue,
      perShare,
      sumPvFcff
    };
  }
  
  /**
   * Update charts with results
   */
  updateCharts() {
    this.updatePrimaryChart();
    this.updateSensitivityChart();
  }
  
  /**
   * Update primary chart with FCFF data
   */
  updatePrimaryChart() {
    const canvas = document.getElementById('primaryChart');
    if (!canvas || !this.results.projections) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Set background
    ctx.fillStyle = '#1A2332';
    ctx.fillRect(0, 0, width, height);
    
    // Draw FCFF bars
    const projections = this.results.projections;
    const maxFcff = Math.max(...projections.map(p => p.fcff));
    const barWidth = (width - 100) / projections.length;
    const maxBarHeight = height - 100;
    
    ctx.fillStyle = '#72efdd';
    
    projections.forEach((proj, index) => {
      const barHeight = (proj.fcff / maxFcff) * maxBarHeight;
      const x = 50 + index * barWidth + barWidth * 0.1;
      const y = height - 50 - barHeight;
      const w = barWidth * 0.8;
      
      ctx.fillRect(x, y, w, barHeight);
      
      // Add year labels
      ctx.fillStyle = '#B8C5D1';
      ctx.font = '12px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(`Y${proj.year}`, x + w / 2, height - 25);
      
      // Add value labels
      ctx.fillText(`$${proj.fcff.toFixed(0)}M`, x + w / 2, y - 10);
      
      ctx.fillStyle = '#72efdd';
    });
    
    // Add title
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '16px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Free Cash Flow Projections', 20, 30);
  }
  
  /**
   * Update sensitivity heatmap
   */
  updateSensitivityChart() {
    const canvas = document.getElementById('sensitivityChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Set background
    ctx.fillStyle = '#1A2332';
    ctx.fillRect(0, 0, width, height);
    
    // Create simple sensitivity grid
    const { waccMin, waccMax, tgMin, tgMax } = this.inputs;
    const basePerShare = this.results.perShare;
    
    const gridSize = 10;
    const cellWidth = (width - 100) / gridSize;
    const cellHeight = (height - 100) / gridSize;
    
    for (let i = 0; i < gridSize; i++) {
      for (let j = 0; j < gridSize; j++) {
        const wacc = waccMin + (waccMax - waccMin) * (i / (gridSize - 1));
        const tg = tgMin + (tgMax - tgMin) * (j / (gridSize - 1));
        
        // Quick sensitivity calculation
        const sensitivityRatio = (basePerShare * (9.0 - wacc) * (tg - 2.5)) / (9.0 * 2.5);
        const adjustedValue = basePerShare + sensitivityRatio;
        const colorIntensity = Math.max(0, Math.min(1, (adjustedValue - basePerShare) / basePerShare + 0.5));
        
        // Color based on value
        const red = Math.floor(255 * (1 - colorIntensity));
        const green = Math.floor(255 * colorIntensity);
        
        ctx.fillStyle = `rgb(${red}, ${green}, 100)`;
        ctx.fillRect(50 + i * cellWidth, 50 + j * cellHeight, cellWidth - 1, cellHeight - 1);
      }
    }
    
    // Add title
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '16px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Sensitivity: WACC vs Terminal Growth', 20, 30);
  }
}

// Initialize DCF Core when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('dcf-module')) {
      window.dcfCore = new DCFCore();
    }
  });
} else {
  if (document.getElementById('dcf-module')) {
    window.dcfCore = new DCFCore();
  }
}

// Export for module usage
export default DCFCore;