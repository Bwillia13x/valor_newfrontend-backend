/**
 * VALOR IVX - Financial Precision Library
 * High-precision financial calculations using decimal.js
 * 
 * This module provides:
 * - Decimal precision handling for financial calculations
 * - Currency formatting and normalization
 * - Input sanitization and validation
 * - Mathematical operations with proper rounding
 */

// Import decimal.js for precise arithmetic (assumes it's loaded globally)
// In production, this should be imported as a module

class FinancialPrecision {
  constructor() {
    // Configure decimal precision for financial calculations
    if (typeof Decimal !== 'undefined') {
      Decimal.set({
        precision: 20,          // 20 significant digits
        rounding: 4,           // ROUND_HALF_UP
        toExpNeg: -7,          // -1e+7
        toExpPos: 21,          // 1e+21
        maxE: 9e15,           // 9e15
        minE: -9e15,          // -9e15
        modulo: 1,            // ROUND_DOWN
        crypto: false         // Browser crypto
      });
      
      this.Decimal = Decimal;
      this.precision = new Decimal('0.01'); // 2 decimal places for currency
    } else {
      console.warn('Decimal.js not available. Falling back to Number with limited precision.');
      this.Decimal = null;
      this.precision = 0.01;
    }
    
    this.currencyFormatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
    
    this.percentFormatter = new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
    
    this.numberFormatter = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }
  
  /**
   * Create a precise decimal value
   */
  decimal(value) {
    if (this.Decimal) {
      try {
        return new this.Decimal(value);
      } catch (e) {
        console.error('Invalid decimal value:', value, e);
        return new this.Decimal(0);
      }
    }
    return Number(value) || 0;
  }
  
  /**
   * Add two values with precision
   */
  add(a, b) {
    if (this.Decimal) {
      return this.decimal(a).add(this.decimal(b));
    }
    return a + b;
  }
  
  /**
   * Subtract two values with precision
   */
  subtract(a, b) {
    if (this.Decimal) {
      return this.decimal(a).sub(this.decimal(b));
    }
    return a - b;
  }
  
  /**
   * Multiply two values with precision
   */
  multiply(a, b) {
    if (this.Decimal) {
      return this.decimal(a).mul(this.decimal(b));
    }
    return a * b;
  }
  
  /**
   * Divide two values with precision
   */
  divide(a, b) {
    if (this.Decimal) {
      const divisor = this.decimal(b);
      if (divisor.isZero()) {
        throw new Error('Division by zero');
      }
      return this.decimal(a).div(divisor);
    }
    if (b === 0) {
      throw new Error('Division by zero');
    }
    return a / b;
  }
  
  /**
   * Calculate power with precision
   */
  power(base, exponent) {
    if (this.Decimal) {
      return this.decimal(base).pow(this.decimal(exponent));
    }
    return Math.pow(base, exponent);
  }
  
  /**
   * Round to financial precision (2 decimal places)
   */
  round(value, decimalPlaces = 2) {
    if (this.Decimal) {
      const factor = this.decimal(10).pow(decimalPlaces);
      return this.decimal(value).mul(factor).round().div(factor);
    }
    return Math.round(value * Math.pow(10, decimalPlaces)) / Math.pow(10, decimalPlaces);
  }
  
  /**
   * Convert to number for display/comparison
   */
  toNumber(value) {
    if (this.Decimal && value && typeof value.toNumber === 'function') {
      return value.toNumber();
    }
    return Number(value) || 0;
  }
  
  /**
   * Format as currency
   */
  formatCurrency(value) {
    const numValue = this.toNumber(value);
    return this.currencyFormatter.format(numValue);
  }
  
  /**
   * Format as percentage
   */
  formatPercentage(value) {
    const numValue = this.toNumber(value) / 100; // Convert to decimal for percentage formatting
    return this.percentFormatter.format(numValue);
  }
  
  /**
   * Format as number with thousands separators
   */
  formatNumber(value) {
    const numValue = this.toNumber(value);
    return this.numberFormatter.format(numValue);
  }
  
  /**
   * Sanitize and validate financial input
   */
  sanitizeInput(input) {
    if (typeof input !== 'string') {
      input = String(input);
    }
    
    // Remove common formatting characters
    let cleaned = input
      .replace(/[$,\s]/g, '')  // Remove $ , and spaces
      .replace(/[()]/g, '')    // Remove parentheses
      .trim();
    
    // Handle negative values in parentheses (accounting format)
    if (input.includes('(') && input.includes(')')) {
      cleaned = '-' + cleaned;
    }
    
    // Validate the cleaned input
    if (!/^-?\d*\.?\d*$/.test(cleaned)) {
      throw new Error('Invalid numeric format');
    }
    
    return cleaned;
  }
  
  /**
   * Validate financial value
   */
  validateFinancialValue(value, fieldName, options = {}) {
    const {
      min = -1e12,
      max = 1e12,
      allowNegative = true,
      allowZero = true
    } = options;
    
    let numValue;
    
    try {
      const cleaned = this.sanitizeInput(value);
      numValue = this.toNumber(this.decimal(cleaned));
    } catch (e) {
      throw new Error(`${fieldName}: Invalid numeric value "${value}"`);
    }
    
    if (isNaN(numValue) || !isFinite(numValue)) {
      throw new Error(`${fieldName}: Invalid numeric value "${value}"`);
    }
    
    if (!allowNegative && numValue < 0) {
      throw new Error(`${fieldName}: Negative values not allowed`);
    }
    
    if (!allowZero && numValue === 0) {
      throw new Error(`${fieldName}: Zero not allowed`);
    }
    
    if (numValue < min) {
      throw new Error(`${fieldName}: Value ${numValue} is below minimum ${min}`);
    }
    
    if (numValue > max) {
      throw new Error(`${fieldName}: Value ${numValue} is above maximum ${max}`);
    }
    
    return this.decimal(numValue);
  }
  
  /**
   * Calculate DCF with precision
   */
  calculateDCF(inputs) {
    try {
      const revenue = this.validateFinancialValue(inputs.revenue, 'Revenue', { min: 0, max: 1e6 });
      const growthRates = [
        this.validateFinancialValue(inputs.growthY1, 'Year 1 Growth', { min: -50, max: 100 }),
        this.validateFinancialValue(inputs.growthY2, 'Year 2 Growth', { min: -50, max: 100 }),
        this.validateFinancialValue(inputs.growthY3, 'Year 3 Growth', { min: -50, max: 100 }),
        this.validateFinancialValue(inputs.growthY4, 'Year 4 Growth', { min: -50, max: 100 }),
        this.validateFinancialValue(inputs.growthY5, 'Year 5 Growth', { min: -50, max: 100 })
      ];
      const terminalGrowth = this.validateFinancialValue(inputs.termGrowth, 'Terminal Growth', { min: 0, max: 5 });
      const wacc = this.validateFinancialValue(inputs.wacc, 'WACC', { min: 1, max: 50 });
      const ebitdaMargin = this.validateFinancialValue(inputs.ebitdaMargin, 'EBITDA Margin', { min: -50, max: 100 });
      const taxRate = this.validateFinancialValue(inputs.taxRate, 'Tax Rate', { min: 0, max: 60 });
      
      // Calculate projected cash flows
      const projectedCashFlows = [];
      let currentRevenue = revenue;
      
      for (let i = 0; i < 5; i++) {
        const growth = this.divide(growthRates[i], 100); // Convert percentage to decimal
        currentRevenue = this.multiply(currentRevenue, this.add(1, growth));
        
        const ebitda = this.multiply(currentRevenue, this.divide(ebitdaMargin, 100));
        const tax = this.multiply(ebitda, this.divide(taxRate, 100));
        const fcf = this.subtract(ebitda, tax);
        
        projectedCashFlows.push(fcf);
      }
      
      // Calculate terminal value
      const finalCashFlow = projectedCashFlows[4];
      const terminalCashFlow = this.multiply(finalCashFlow, this.add(1, this.divide(terminalGrowth, 100)));
      const terminalValue = this.divide(terminalCashFlow, this.subtract(this.divide(wacc, 100), this.divide(terminalGrowth, 100)));
      
      // Calculate present values
      const discountRate = this.divide(wacc, 100);
      let totalPV = this.decimal(0);
      
      for (let i = 0; i < projectedCashFlows.length; i++) {
        const discountFactor = this.power(this.add(1, discountRate), i + 1);
        const pv = this.divide(projectedCashFlows[i], discountFactor);
        totalPV = this.add(totalPV, pv);
      }
      
      // Terminal value present value
      const terminalPV = this.divide(terminalValue, this.power(this.add(1, discountRate), 5));
      const enterpriseValue = this.add(totalPV, terminalPV);
      
      return {
        success: true,
        projectedCashFlows: projectedCashFlows.map(cf => this.toNumber(cf)),
        terminalValue: this.toNumber(terminalValue),
        presentValueCashFlows: this.toNumber(totalPV),
        presentValueTerminal: this.toNumber(terminalPV),
        enterpriseValue: this.toNumber(enterpriseValue),
        formattedEnterpriseValue: this.formatCurrency(enterpriseValue)
      };
      
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
  
  /**
   * Calculate sensitivity analysis
   */
  calculateSensitivity(baseInputs, parameter, range) {
    const results = [];
    
    for (const value of range) {
      const inputs = { ...baseInputs };
      inputs[parameter] = value;
      
      const dcfResult = this.calculateDCF(inputs);
      results.push({
        value: this.toNumber(value),
        enterpriseValue: dcfResult.success ? dcfResult.enterpriseValue : null,
        error: dcfResult.success ? null : dcfResult.error
      });
    }
    
    return results;
  }
}

// Global instance
if (typeof window !== 'undefined') {
  window.FinancialPrecision = new FinancialPrecision();
}

// Export for Node.js environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = FinancialPrecision;
}