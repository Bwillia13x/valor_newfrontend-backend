/**
 * Advanced Analytics Module
 * Phase 7 Implementation
 * 
 * This module provides frontend integration for machine learning analytics:
 * - Revenue prediction
 * - Risk assessment
 * - Market trend analysis
 * - Portfolio optimization
 * - Anomaly detection
 */

import { getApiUrl, safeFetch } from './backend.js';
import { getAuthHeaders } from './auth.js';

class AnalyticsManager {
    constructor() {
        this.apiBase = getApiUrl();
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    }
    
    /**
     * Predict revenue growth using machine learning
     */
    async predictRevenueGrowth(financialData, forecastPeriods = 5) {
        try {
            const cacheKey = `revenue_prediction_${JSON.stringify(financialData)}_${forecastPeriods}`;
            const cached = this.getCachedResult(cacheKey);
            if (cached) return cached;
            
            const response = await safeFetch(`${this.apiBase}/api/analytics/predict-revenue`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeaders()
                },
                body: JSON.stringify({
                    financial_data: financialData,
                    forecast_periods: forecastPeriods
                })
            });
            
            if (!response.ok) {
                throw new Error(`Prediction failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            this.cacheResult(cacheKey, result);
            return result;
            
        } catch (error) {
            console.error('Revenue prediction error:', error);
            throw error;
        }
    }
    
    /**
     * Assess financial risk using machine learning
     */
    async assessRisk(financialData) {
        try {
            const cacheKey = `risk_assessment_${JSON.stringify(financialData)}`;
            const cached = this.getCachedResult(cacheKey);
            if (cached) return cached;
            
            const response = await safeFetch(`${this.apiBase}/api/analytics/assess-risk`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeaders()
                },
                body: JSON.stringify({
                    financial_data: financialData
                })
            });
            
            if (!response.ok) {
                throw new Error(`Risk assessment failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            this.cacheResult(cacheKey, result);
            return result;
            
        } catch (error) {
            console.error('Risk assessment error:', error);
            throw error;
        }
    }
    
    /**
     * Analyze market trends using machine learning
     */
    async analyzeMarketTrend(priceData, period = 30) {
        try {
            const cacheKey = `market_trend_${JSON.stringify(priceData)}_${period}`;
            const cached = this.getCachedResult(cacheKey);
            if (cached) return cached;
            
            const response = await safeFetch(`${this.apiBase}/api/analytics/market-trend`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeaders()
                },
                body: JSON.stringify({
                    price_data: priceData,
                    period: period
                })
            });
            
            if (!response.ok) {
                throw new Error(`Market trend analysis failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            this.cacheResult(cacheKey, result);
            return result;
            
        } catch (error) {
            console.error('Market trend analysis error:', error);
            throw error;
        }
    }
    
    /**
     * Optimize portfolio allocation using modern portfolio theory
     */
    async optimizePortfolio(assets, targetReturn = 0.10, riskTolerance = 0.15) {
        try {
            const cacheKey = `portfolio_optimization_${JSON.stringify(assets)}_${targetReturn}_${riskTolerance}`;
            const cached = this.getCachedResult(cacheKey);
            if (cached) return cached;
            
            const response = await safeFetch(`${this.apiBase}/api/analytics/optimize-portfolio`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeaders()
                },
                body: JSON.stringify({
                    assets: assets,
                    target_return: targetReturn,
                    risk_tolerance: riskTolerance
                })
            });
            
            if (!response.ok) {
                throw new Error(`Portfolio optimization failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            this.cacheResult(cacheKey, result);
            return result;
            
        } catch (error) {
            console.error('Portfolio optimization error:', error);
            throw error;
        }
    }
    
    /**
     * Detect anomalies in financial data
     */
    async detectAnomalies(financialData, metric = 'revenue') {
        try {
            const cacheKey = `anomaly_detection_${JSON.stringify(financialData)}_${metric}`;
            const cached = this.getCachedResult(cacheKey);
            if (cached) return cached;
            
            const response = await safeFetch(`${this.apiBase}/api/analytics/detect-anomalies`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeaders()
                },
                body: JSON.stringify({
                    financial_data: financialData,
                    metric: metric
                })
            });
            
            if (!response.ok) {
                throw new Error(`Anomaly detection failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            this.cacheResult(cacheKey, result);
            return result;
            
        } catch (error) {
            console.error('Anomaly detection error:', error);
            throw error;
        }
    }
    
    /**
     * Get analytics engine statistics
     */
    async getAnalyticsStats() {
        try {
            const response = await safeFetch(`${this.apiBase}/api/analytics/stats`, {
                method: 'GET',
                headers: {
                    ...getAuthHeaders()
                }
            });
            
            if (!response.ok) {
                throw new Error(`Failed to get analytics stats: ${response.statusText}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Analytics stats error:', error);
            throw error;
        }
    }
    
    // Cache management
    getCachedResult(key) {
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            return cached.data;
        }
        this.cache.delete(key);
        return null;
    }
    
    cacheResult(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }
    
    clearCache() {
        this.cache.clear();
    }
}

// Create global instance
const analyticsManager = new AnalyticsManager();

// Export functions for use in other modules
export function predictRevenueGrowth(financialData, forecastPeriods = 5) {
    return analyticsManager.predictRevenueGrowth(financialData, forecastPeriods);
}

export function assessRisk(financialData) {
    return analyticsManager.assessRisk(financialData);
}

export function analyzeMarketTrend(priceData, period = 30) {
    return analyticsManager.analyzeMarketTrend(priceData, period);
}

export function optimizePortfolio(assets, targetReturn = 0.10, riskTolerance = 0.15) {
    return analyticsManager.optimizePortfolio(assets, targetReturn, riskTolerance);
}

export function detectAnomalies(financialData, metric = 'revenue') {
    return analyticsManager.detectAnomalies(financialData, metric);
}

export function getAnalyticsStats() {
    return analyticsManager.getAnalyticsStats();
}

export function clearAnalyticsCache() {
    analyticsManager.clearCache();
}

// UI Integration Functions
export function initAnalyticsUI() {
    // Add analytics buttons to the interface
    addAnalyticsButtons();
    setupAnalyticsEventListeners();
}

function addAnalyticsButtons() {
    const actionsContainer = document.querySelector('.actions');
    if (!actionsContainer) return;
    
    // Create analytics dropdown
    const analyticsDropdown = document.createElement('div');
    analyticsDropdown.className = 'analytics-dropdown';
    analyticsDropdown.innerHTML = `
        <button class="btn analytics-btn" onclick="toggleAnalyticsDropdown()">
            📊 Analytics
        </button>
        <div class="analytics-menu" id="analytics-menu">
            <button onclick="runRevenuePrediction()">Revenue Prediction</button>
            <button onclick="runRiskAssessment()">Risk Assessment</button>
            <button onclick="runMarketTrendAnalysis()">Market Trends</button>
            <button onclick="runPortfolioOptimization()">Portfolio Optimization</button>
            <button onclick="runAnomalyDetection()">Anomaly Detection</button>
        </div>
    `;
    
    actionsContainer.appendChild(analyticsDropdown);
}

function setupAnalyticsEventListeners() {
    // Add global functions for button clicks
    window.runRevenuePrediction = async () => {
        try {
            showLoading('Running revenue prediction...');
            const financialData = getCurrentFinancialData();
            const result = await predictRevenueGrowth(financialData);
            showAnalyticsResult('Revenue Prediction', result);
        } catch (error) {
            showError('Revenue prediction failed: ' + error.message);
        } finally {
            hideLoading();
        }
    };
    
    window.runRiskAssessment = async () => {
        try {
            showLoading('Running risk assessment...');
            const financialData = getCurrentFinancialData();
            const result = await assessRisk(financialData);
            showAnalyticsResult('Risk Assessment', result);
        } catch (error) {
            showError('Risk assessment failed: ' + error.message);
        } finally {
            hideLoading();
        }
    };
    
    window.runMarketTrendAnalysis = async () => {
        try {
            showLoading('Running market trend analysis...');
            const priceData = getCurrentPriceData();
            const result = await analyzeMarketTrend(priceData);
            showAnalyticsResult('Market Trend Analysis', result);
        } catch (error) {
            showError('Market trend analysis failed: ' + error.message);
        } finally {
            hideLoading();
        }
    };
    
    window.runPortfolioOptimization = async () => {
        try {
            showLoading('Running portfolio optimization...');
            const assets = getCurrentPortfolioData();
            const result = await optimizePortfolio(assets);
            showAnalyticsResult('Portfolio Optimization', result);
        } catch (error) {
            showError('Portfolio optimization failed: ' + error.message);
        } finally {
            hideLoading();
        }
    };
    
    window.runAnomalyDetection = async () => {
        try {
            showLoading('Running anomaly detection...');
            const financialData = getCurrentFinancialData();
            const result = await detectAnomalies(financialData);
            showAnalyticsResult('Anomaly Detection', result);
        } catch (error) {
            showError('Anomaly detection failed: ' + error.message);
        } finally {
            hideLoading();
        }
    };
    
    window.toggleAnalyticsDropdown = () => {
        const menu = document.getElementById('analytics-menu');
        menu.classList.toggle('show');
    };
}

function getCurrentFinancialData() {
    // Extract current financial data from the form
    const inputs = document.querySelectorAll('input[type="number"]');
    const financialData = {};
    
    inputs.forEach(input => {
        if (input.value) {
            financialData[input.id] = parseFloat(input.value);
        }
    });
    
    return financialData;
}

function getCurrentPriceData() {
    // This would need to be implemented based on available price data
    // For now, return sample data
    return [
        { close: 100, volume: 1000000, timestamp: '2024-01-01' },
        { close: 105, volume: 1100000, timestamp: '2024-01-02' },
        { close: 103, volume: 900000, timestamp: '2024-01-03' }
    ];
}

function getCurrentPortfolioData() {
    // This would need to be implemented based on available portfolio data
    // For now, return sample data
    return [
        { symbol: 'AAPL', returns: [0.05, 0.03, -0.02, 0.04] },
        { symbol: 'MSFT', returns: [0.03, 0.06, 0.01, 0.02] },
        { symbol: 'GOOGL', returns: [0.02, 0.04, 0.03, 0.01] }
    ];
}

function showAnalyticsResult(title, result) {
    // Create modal to show analytics results
    const modal = document.createElement('div');
    modal.className = 'modal analytics-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>${title}</h2>
                <span class="close" onclick="this.parentElement.parentElement.parentElement.remove()">&times;</span>
            </div>
            <div class="modal-body">
                <pre>${JSON.stringify(result, null, 2)}</pre>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function showLoading(message) {
    // Show loading indicator
    const loading = document.createElement('div');
    loading.className = 'loading-overlay';
    loading.innerHTML = `
        <div class="loading-spinner"></div>
        <div class="loading-message">${message}</div>
    `;
    loading.id = 'loading-overlay';
    document.body.appendChild(loading);
}

function hideLoading() {
    // Hide loading indicator
    const loading = document.getElementById('loading-overlay');
    if (loading) {
        loading.remove();
    }
}

function showError(message) {
    // Show error message
    const error = document.createElement('div');
    error.className = 'error-notification';
    error.textContent = message;
    document.body.appendChild(error);
    
    setTimeout(() => {
        error.remove();
    }, 5000);
}

// Export the manager instance for advanced usage
export { analyticsManager }; 