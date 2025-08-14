/**
 * Real Options Analysis Module
 * Phase 5A Implementation - Advanced Financial Models
 * 
 * This module provides comprehensive real options analysis capabilities
 * for strategic investment decisions.
 */

class RealOptionsAnalysis {
    constructor() {
        this.currentAnalysis = null;
        this.results = null;
        this.charts = {};
        this.backend = new BackendAPI();
        this.initializeModule();
    }

    /**
     * Initialize the real options module
     */
    async initializeModule() {
        try {
            console.log('Initializing Real Options Analysis module...');
            
            // Check if backend is available
            const healthCheck = await this.backend.get('/api/real-options/health');
            if (healthCheck.success) {
                console.log('Real Options backend is operational');
            } else {
                console.warn('Real Options backend health check failed');
            }
            
            // Load predefined scenarios
            await this.loadPredefinedScenarios();
            
        } catch (error) {
            console.error('Error initializing Real Options module:', error);
        }
    }

    /**
     * Load predefined scenarios from backend
     */
    async loadPredefinedScenarios() {
        try {
            const response = await this.backend.get('/api/real-options/scenarios');
            if (response.success) {
                this.predefinedScenarios = response.result;
                console.log('Predefined scenarios loaded successfully');
            }
        } catch (error) {
            console.error('Error loading predefined scenarios:', error);
        }
    }

    /**
     * Calculate expansion option value
     */
    async calculateExpansionOption(params) {
        try {
            console.log('Calculating expansion option with params:', params);
            
            const response = await this.backend.post('/api/real-options/expansion', params);
            
            if (response.success) {
                this.currentAnalysis = {
                    type: 'expansion',
                    params: params,
                    results: response.result
                };
                this.results = response.result;
                
                console.log('Expansion option calculated successfully:', this.results);
                return this.results;
            } else {
                throw new Error(response.error || 'Failed to calculate expansion option');
            }
        } catch (error) {
            console.error('Error calculating expansion option:', error);
            throw error;
        }
    }

    /**
     * Calculate abandonment option value
     */
    async calculateAbandonmentOption(params) {
        try {
            console.log('Calculating abandonment option with params:', params);
            
            const response = await this.backend.post('/api/real-options/abandonment', params);
            
            if (response.success) {
                this.currentAnalysis = {
                    type: 'abandonment',
                    params: params,
                    results: response.result
                };
                this.results = response.result;
                
                console.log('Abandonment option calculated successfully:', this.results);
                return this.results;
            } else {
                throw new Error(response.error || 'Failed to calculate abandonment option');
            }
        } catch (error) {
            console.error('Error calculating abandonment option:', error);
            throw error;
        }
    }

    /**
     * Calculate timing option value
     */
    async calculateTimingOption(params) {
        try {
            console.log('Calculating timing option with params:', params);
            
            const response = await this.backend.post('/api/real-options/timing', params);
            
            if (response.success) {
                this.currentAnalysis = {
                    type: 'timing',
                    params: params,
                    results: response.result
                };
                this.results = response.result;
                
                console.log('Timing option calculated successfully:', this.results);
                return this.results;
            } else {
                throw new Error(response.error || 'Failed to calculate timing option');
            }
        } catch (error) {
            console.error('Error calculating timing option:', error);
            throw error;
        }
    }

    /**
     * Calculate compound option value
     */
    async calculateCompoundOption(params) {
        try {
            console.log('Calculating compound option with params:', params);
            
            const response = await this.backend.post('/api/real-options/compound', params);
            
            if (response.success) {
                this.currentAnalysis = {
                    type: 'compound',
                    params: params,
                    results: response.result
                };
                this.results = response.result;
                
                console.log('Compound option calculated successfully:', this.results);
                return this.results;
            } else {
                throw new Error(response.error || 'Failed to calculate compound option');
            }
        } catch (error) {
            console.error('Error calculating compound option:', error);
            throw error;
        }
    }

    /**
     * Calculate option Greeks
     */
    async calculateGreeks(params) {
        try {
            console.log('Calculating Greeks with params:', params);
            
            const response = await this.backend.post('/api/real-options/greeks', params);
            
            if (response.success) {
                return response.result;
            } else {
                throw new Error(response.error || 'Failed to calculate Greeks');
            }
        } catch (error) {
            console.error('Error calculating Greeks:', error);
            throw error;
        }
    }

    /**
     * Estimate volatility from historical data
     */
    async estimateVolatility(historicalData, method = 'historical') {
        try {
            console.log('Estimating volatility with method:', method);
            
            const params = {
                historical_data: historicalData,
                method: method
            };
            
            const response = await this.backend.post('/api/real-options/volatility', params);
            
            if (response.success) {
                return response.result;
            } else {
                throw new Error(response.error || 'Failed to estimate volatility');
            }
        } catch (error) {
            console.error('Error estimating volatility:', error);
            throw error;
        }
    }

    /**
     * Run sensitivity analysis
     */
    async runSensitivityAnalysis(baseParams, parameter, rangeValues) {
        try {
            console.log('Running sensitivity analysis for parameter:', parameter);
            
            const params = {
                base_params: baseParams,
                parameter: parameter,
                range_values: rangeValues
            };
            
            const response = await this.backend.post('/api/real-options/sensitivity', params);
            
            if (response.success) {
                return response.result;
            } else {
                throw new Error(response.error || 'Failed to run sensitivity analysis');
            }
        } catch (error) {
            console.error('Error running sensitivity analysis:', error);
            throw error;
        }
    }

    /**
     * Get available pricing models
     */
    async getAvailableModels() {
        try {
            const response = await this.backend.get('/api/real-options/models');
            
            if (response.success) {
                return response.result;
            } else {
                throw new Error(response.error || 'Failed to get available models');
            }
        } catch (error) {
            console.error('Error getting available models:', error);
            throw error;
        }
    }

    /**
     * Render option value chart
     */
    renderOptionValueChart(canvasId, results) {
        try {
            const canvas = document.getElementById(canvasId);
            if (!canvas) {
                console.error('Canvas element not found:', canvasId);
                return;
            }

            const ctx = canvas.getContext('2d');
            
            // Clear previous chart
            if (this.charts[canvasId]) {
                this.charts[canvasId].destroy();
            }

            // Prepare data for chart
            const chartData = {
                labels: ['Option Value', 'Intrinsic Value', 'Time Value'],
                datasets: [{
                    label: 'Value ($)',
                    data: [
                        results.option_value,
                        results.intrinsic_value,
                        results.time_value
                    ],
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(255, 206, 86, 0.8)'
                    ],
                    borderColor: [
                        'rgba(54, 162, 235, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(255, 206, 86, 1)'
                    ],
                    borderWidth: 2
                }]
            };

            // Create chart
            this.charts[canvasId] = new Chart(ctx, {
                type: 'bar',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Option Value Breakdown'
                        },
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Value ($)'
                            }
                        }
                    }
                }
            });

        } catch (error) {
            console.error('Error rendering option value chart:', error);
        }
    }

    /**
     * Render Greeks analysis chart
     */
    renderGreeksAnalysis(canvasId, greeks) {
        try {
            const canvas = document.getElementById(canvasId);
            if (!canvas) {
                console.error('Canvas element not found:', canvasId);
                return;
            }

            const ctx = canvas.getContext('2d');
            
            // Clear previous chart
            if (this.charts[canvasId]) {
                this.charts[canvasId].destroy();
            }

            // Prepare data for chart
            const chartData = {
                labels: ['Delta', 'Gamma', 'Theta', 'Vega', 'Rho'],
                datasets: [{
                    label: 'Greeks Values',
                    data: [
                        greeks.delta,
                        greeks.gamma,
                        greeks.theta,
                        greeks.vega,
                        greeks.rho
                    ],
                    backgroundColor: 'rgba(153, 102, 255, 0.8)',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(153, 102, 255, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(153, 102, 255, 1)'
                }]
            };

            // Create chart
            this.charts[canvasId] = new Chart(ctx, {
                type: 'radar',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Option Greeks Analysis'
                        },
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        r: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Greeks Values'
                            }
                        }
                    }
                }
            });

        } catch (error) {
            console.error('Error rendering Greeks analysis chart:', error);
        }
    }

    /**
     * Render sensitivity heatmap
     */
    renderSensitivityHeatmap(canvasId, sensitivityData) {
        try {
            const canvas = document.getElementById(canvasId);
            if (!canvas) {
                console.error('Canvas element not found:', canvasId);
                return;
            }

            const ctx = canvas.getContext('2d');
            
            // Clear previous chart
            if (this.charts[canvasId]) {
                this.charts[canvasId].destroy();
            }

            // Prepare data for heatmap
            const labels = sensitivityData.results.map(item => item.parameter_value.toString());
            const optionValues = sensitivityData.results.map(item => item.option_value);

            const chartData = {
                labels: labels,
                datasets: [{
                    label: 'Option Value',
                    data: optionValues,
                    backgroundColor: 'rgba(255, 99, 132, 0.8)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1
                }]
            };

            // Create chart
            this.charts[canvasId] = new Chart(ctx, {
                type: 'line',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: `Sensitivity Analysis: ${sensitivityData.parameter}`
                        },
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: sensitivityData.parameter
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Option Value ($)'
                            }
                        }
                    }
                }
            });

        } catch (error) {
            console.error('Error rendering sensitivity heatmap:', error);
        }
    }

    /**
     * Render option value vs underlying price chart
     */
    renderOptionValueVsPrice(canvasId, results, priceRange) {
        try {
            const canvas = document.getElementById(canvasId);
            if (!canvas) {
                console.error('Canvas element not found:', canvasId);
                return;
            }

            const ctx = canvas.getContext('2d');
            
            // Clear previous chart
            if (this.charts[canvasId]) {
                this.charts[canvasId].destroy();
            }

            // Generate price range data
            const prices = [];
            const optionValues = [];
            const intrinsicValues = [];
            
            for (let price = priceRange.min; price <= priceRange.max; price += priceRange.step) {
                prices.push(price);
                
                // Calculate option value at this price (simplified)
                const intrinsic = Math.max(price - results.exercise_price || results.expansion_cost || results.salvage_value, 0);
                intrinsicValues.push(intrinsic);
                
                // Approximate option value (this would need proper calculation)
                const timeValue = results.time_value || 0;
                optionValues.push(intrinsic + timeValue);
            }

            const chartData = {
                labels: prices.map(p => p.toFixed(2)),
                datasets: [
                    {
                        label: 'Option Value',
                        data: optionValues,
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 2,
                        fill: false
                    },
                    {
                        label: 'Intrinsic Value',
                        data: intrinsicValues,
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 2,
                        fill: false
                    }
                ]
            };

            // Create chart
            this.charts[canvasId] = new Chart(ctx, {
                type: 'line',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Option Value vs Underlying Price'
                        },
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Underlying Price ($)'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Option Value ($)'
                            }
                        }
                    }
                }
            });

        } catch (error) {
            console.error('Error rendering option value vs price chart:', error);
        }
    }

    /**
     * Format currency values
     */
    formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    }

    /**
     * Format percentage values
     */
    formatPercentage(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'percent',
            minimumFractionDigits: 2,
            maximumFractionDigits: 4
        }).format(value);
    }

    /**
     * Create results summary HTML
     */
    createResultsSummary(results) {
        if (!results) return '';

        let html = '<div class="results-summary">';
        html += '<h3>Analysis Results</h3>';
        
        html += '<div class="result-item">';
        html += `<strong>Option Value:</strong> ${this.formatCurrency(results.option_value)}`;
        html += '</div>';
        
        if (results.intrinsic_value !== undefined) {
            html += '<div class="result-item">';
            html += `<strong>Intrinsic Value:</strong> ${this.formatCurrency(results.intrinsic_value)}`;
            html += '</div>';
        }
        
        if (results.time_value !== undefined) {
            html += '<div class="result-item">';
            html += `<strong>Time Value:</strong> ${this.formatCurrency(results.time_value)}`;
            html += '</div>';
        }
        
        // Add Greeks if available
        if (results.delta !== undefined) {
            html += '<div class="greeks-section">';
            html += '<h4>Option Greeks</h4>';
            html += `<div class="result-item"><strong>Delta:</strong> ${this.formatPercentage(results.delta)}</div>`;
            html += `<div class="result-item"><strong>Gamma:</strong> ${this.formatPercentage(results.gamma)}</div>`;
            html += `<div class="result-item"><strong>Theta:</strong> ${this.formatCurrency(results.theta)}/day</div>`;
            html += `<div class="result-item"><strong>Vega:</strong> ${this.formatCurrency(results.vega)}/1% vol</div>`;
            html += `<div class="result-item"><strong>Rho:</strong> ${this.formatCurrency(results.rho)}/1% rate</div>`;
            html += '</div>';
        }
        
        // Add option-specific results
        if (results.option_type === 'timing' && results.should_exercise_now !== undefined) {
            html += '<div class="timing-recommendation">';
            html += '<h4>Timing Recommendation</h4>';
            html += `<div class="result-item"><strong>Optimal Exercise Threshold:</strong> ${this.formatCurrency(results.optimal_exercise_threshold)}</div>`;
            html += `<div class="result-item"><strong>Should Exercise Now:</strong> ${results.should_exercise_now ? 'Yes' : 'No'}</div>`;
            html += '</div>';
        }
        
        html += '</div>';
        
        return html;
    }

    /**
     * Create parameter input form
     */
    createParameterForm(optionType) {
        let html = '<div class="parameter-form">';
        html += '<h3>Option Parameters</h3>';
        
        switch (optionType) {
            case 'expansion':
                html += this.createExpansionForm();
                break;
            case 'abandonment':
                html += this.createAbandonmentForm();
                break;
            case 'timing':
                html += this.createTimingForm();
                break;
            case 'compound':
                html += this.createCompoundForm();
                break;
            default:
                html += '<p>Unknown option type</p>';
        }
        
        html += '</div>';
        return html;
    }

    /**
     * Create expansion option form
     */
    createExpansionForm() {
        return `
            <div class="form-group">
                <label for="current_value">Current Project Value ($)</label>
                <input type="number" id="current_value" class="form-control" value="1000000" min="0" step="1000">
            </div>
            <div class="form-group">
                <label for="expansion_cost">Expansion Cost ($)</label>
                <input type="number" id="expansion_cost" class="form-control" value="500000" min="0" step="1000">
            </div>
            <div class="form-group">
                <label for="time_to_expiry">Time to Expiry (years)</label>
                <input type="number" id="time_to_expiry" class="form-control" value="2.0" min="0" step="0.1">
            </div>
            <div class="form-group">
                <label for="volatility">Volatility</label>
                <input type="number" id="volatility" class="form-control" value="0.3" min="0" max="5" step="0.01">
            </div>
            <div class="form-group">
                <label for="risk_free_rate">Risk-Free Rate</label>
                <input type="number" id="risk_free_rate" class="form-control" value="0.05" min="-0.5" max="1" step="0.01">
            </div>
            <div class="form-group">
                <label for="expansion_multiplier">Expansion Multiplier</label>
                <input type="number" id="expansion_multiplier" class="form-control" value="2.0" min="1" step="0.1">
            </div>
        `;
    }

    /**
     * Create abandonment option form
     */
    createAbandonmentForm() {
        return `
            <div class="form-group">
                <label for="current_value">Current Project Value ($)</label>
                <input type="number" id="current_value" class="form-control" value="20000000" min="0" step="1000">
            </div>
            <div class="form-group">
                <label for="salvage_value">Salvage Value ($)</label>
                <input type="number" id="salvage_value" class="form-control" value="5000000" min="0" step="1000">
            </div>
            <div class="form-group">
                <label for="time_to_expiry">Time to Expiry (years)</label>
                <input type="number" id="time_to_expiry" class="form-control" value="5.0" min="0" step="0.1">
            </div>
            <div class="form-group">
                <label for="volatility">Volatility</label>
                <input type="number" id="volatility" class="form-control" value="0.5" min="0" max="5" step="0.01">
            </div>
            <div class="form-group">
                <label for="risk_free_rate">Risk-Free Rate</label>
                <input type="number" id="risk_free_rate" class="form-control" value="0.03" min="-0.5" max="1" step="0.01">
            </div>
        `;
    }

    /**
     * Create timing option form
     */
    createTimingForm() {
        return `
            <div class="form-group">
                <label for="project_value">Project Value ($)</label>
                <input type="number" id="project_value" class="form-control" value="8000000" min="0" step="1000">
            </div>
            <div class="form-group">
                <label for="investment_cost">Investment Cost ($)</label>
                <input type="number" id="investment_cost" class="form-control" value="3000000" min="0" step="1000">
            </div>
            <div class="form-group">
                <label for="time_horizon">Time Horizon (years)</label>
                <input type="number" id="time_horizon" class="form-control" value="4.0" min="0" step="0.1">
            </div>
            <div class="form-group">
                <label for="volatility">Volatility</label>
                <input type="number" id="volatility" class="form-control" value="0.45" min="0" max="5" step="0.01">
            </div>
            <div class="form-group">
                <label for="risk_free_rate">Risk-Free Rate</label>
                <input type="number" id="risk_free_rate" class="form-control" value="0.05" min="-0.5" max="1" step="0.01">
            </div>
        `;
    }

    /**
     * Create compound option form
     */
    createCompoundForm() {
        return `
            <div class="form-group">
                <label for="underlying_value">Underlying Value ($)</label>
                <input type="number" id="underlying_value" class="form-control" value="10000000" min="0" step="1000">
            </div>
            <div class="form-group">
                <label for="exercise_price_1">First Exercise Price ($)</label>
                <input type="number" id="exercise_price_1" class="form-control" value="2000000" min="0" step="1000">
            </div>
            <div class="form-group">
                <label for="exercise_price_2">Second Exercise Price ($)</label>
                <input type="number" id="exercise_price_2" class="form-control" value="5000000" min="0" step="1000">
            </div>
            <div class="form-group">
                <label for="time_period_1">First Time Period (years)</label>
                <input type="number" id="time_period_1" class="form-control" value="2.0" min="0" step="0.1">
            </div>
            <div class="form-group">
                <label for="time_period_2">Second Time Period (years)</label>
                <input type="number" id="time_period_2" class="form-control" value="4.0" min="0" step="0.1">
            </div>
            <div class="form-group">
                <label for="volatility">Volatility</label>
                <input type="number" id="volatility" class="form-control" value="0.5" min="0" max="5" step="0.01">
            </div>
            <div class="form-group">
                <label for="risk_free_rate">Risk-Free Rate</label>
                <input type="number" id="risk_free_rate" class="form-control" value="0.04" min="-0.5" max="1" step="0.01">
            </div>
        `;
    }

    /**
     * Get form parameters
     */
    getFormParameters(optionType) {
        const params = {};
        
        switch (optionType) {
            case 'expansion':
                params.current_value = parseFloat(document.getElementById('current_value').value);
                params.expansion_cost = parseFloat(document.getElementById('expansion_cost').value);
                params.time_to_expiry = parseFloat(document.getElementById('time_to_expiry').value);
                params.volatility = parseFloat(document.getElementById('volatility').value);
                params.risk_free_rate = parseFloat(document.getElementById('risk_free_rate').value);
                params.expansion_multiplier = parseFloat(document.getElementById('expansion_multiplier').value);
                break;
                
            case 'abandonment':
                params.current_value = parseFloat(document.getElementById('current_value').value);
                params.salvage_value = parseFloat(document.getElementById('salvage_value').value);
                params.time_to_expiry = parseFloat(document.getElementById('time_to_expiry').value);
                params.volatility = parseFloat(document.getElementById('volatility').value);
                params.risk_free_rate = parseFloat(document.getElementById('risk_free_rate').value);
                break;
                
            case 'timing':
                params.project_value = parseFloat(document.getElementById('project_value').value);
                params.investment_cost = parseFloat(document.getElementById('investment_cost').value);
                params.time_horizon = parseFloat(document.getElementById('time_horizon').value);
                params.volatility = parseFloat(document.getElementById('volatility').value);
                params.risk_free_rate = parseFloat(document.getElementById('risk_free_rate').value);
                break;
                
            case 'compound':
                params.underlying_value = parseFloat(document.getElementById('underlying_value').value);
                params.exercise_prices = [
                    parseFloat(document.getElementById('exercise_price_1').value),
                    parseFloat(document.getElementById('exercise_price_2').value)
                ];
                params.time_periods = [
                    parseFloat(document.getElementById('time_period_1').value),
                    parseFloat(document.getElementById('time_period_2').value)
                ];
                params.volatility = parseFloat(document.getElementById('volatility').value);
                params.risk_free_rate = parseFloat(document.getElementById('risk_free_rate').value);
                break;
        }
        
        return params;
    }

    /**
     * Load predefined scenario
     */
    loadScenario(scenario) {
        try {
            // Populate form fields with scenario values
            Object.keys(scenario).forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    element.value = scenario[key];
                }
            });
            
            console.log('Scenario loaded successfully:', scenario);
        } catch (error) {
            console.error('Error loading scenario:', error);
        }
    }

    /**
     * Clear all charts
     */
    clearCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }

    /**
     * Destroy module and clean up resources
     */
    destroy() {
        this.clearCharts();
        this.currentAnalysis = null;
        this.results = null;
        console.log('Real Options Analysis module destroyed');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RealOptionsAnalysis;
} 