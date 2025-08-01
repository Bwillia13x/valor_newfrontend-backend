/**
 * Analytics Dashboard Module for Valor IVX
 * Phase 8 Implementation - Advanced Analytics and Enterprise Features
 * 
 * This module provides a comprehensive analytics dashboard that integrates:
 * - Revenue prediction visualizations
 * - Risk assessment metrics
 * - Portfolio optimization results
 * - Sentiment analysis charts
 * - Market trend analysis
 * - Anomaly detection alerts
 */

class AnalyticsDashboard {
    constructor() {
        this.charts = {};
        this.currentData = {};
        this.refreshInterval = null;
        this.isInitialized = false;
        
        // Initialize dashboard
        this.init();
    }
    
    async init() {
        try {
            await this.setupDashboard();
            this.setupEventListeners();
            this.startAutoRefresh();
            this.isInitialized = true;
            console.log('Analytics Dashboard initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Analytics Dashboard:', error);
        }
    }
    
    async setupDashboard() {
        // Create dashboard container
        const dashboardContainer = document.createElement('div');
        dashboardContainer.id = 'analytics-dashboard';
        dashboardContainer.className = 'analytics-dashboard';
        dashboardContainer.innerHTML = this.getDashboardHTML();
        
        // Add to main content area
        const mainContent = document.querySelector('#main-content') || document.body;
        mainContent.appendChild(dashboardContainer);
        
        // Initialize charts
        await this.initializeCharts();
        
        // Load initial data
        await this.loadDashboardData();
    }
    
    getDashboardHTML() {
        return `
            <div class="dashboard-header">
                <h1><i class="fas fa-chart-line"></i> Analytics Dashboard</h1>
                <div class="dashboard-controls">
                    <button id="refresh-dashboard" class="btn btn-primary">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                    <button id="export-dashboard" class="btn btn-secondary">
                        <i class="fas fa-download"></i> Export
                    </button>
                    <select id="time-range" class="form-select">
                        <option value="1d">Last 24 Hours</option>
                        <option value="7d" selected>Last 7 Days</option>
                        <option value="30d">Last 30 Days</option>
                        <option value="90d">Last 90 Days</option>
                    </select>
                </div>
            </div>
            
            <div class="dashboard-grid">
                <!-- Key Metrics Cards -->
                <div class="metrics-section">
                    <div class="metric-card">
                        <div class="metric-header">
                            <h3>Revenue Growth</h3>
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <div class="metric-value" id="revenue-growth">--</div>
                        <div class="metric-change" id="revenue-change">--</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-header">
                            <h3>Risk Score</h3>
                            <i class="fas fa-shield-alt"></i>
                        </div>
                        <div class="metric-value" id="risk-score">--</div>
                        <div class="metric-change" id="risk-change">--</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-header">
                            <h3>Portfolio Return</h3>
                            <i class="fas fa-chart-pie"></i>
                        </div>
                        <div class="metric-value" id="portfolio-return">--</div>
                        <div class="metric-change" id="portfolio-change">--</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-header">
                            <h3>Sentiment Score</h3>
                            <i class="fas fa-smile"></i>
                        </div>
                        <div class="metric-value" id="sentiment-score">--</div>
                        <div class="metric-change" id="sentiment-change">--</div>
                    </div>
                </div>
                
                <!-- Revenue Prediction Chart -->
                <div class="chart-section">
                    <div class="chart-card">
                        <div class="chart-header">
                            <h3>Revenue Prediction</h3>
                            <div class="chart-controls">
                                <button class="btn btn-sm btn-outline" id="revenue-forecast-btn">Forecast</button>
                            </div>
                        </div>
                        <div class="chart-container">
                            <canvas id="revenue-chart"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- Risk Assessment Chart -->
                <div class="chart-section">
                    <div class="chart-card">
                        <div class="chart-header">
                            <h3>Risk Assessment</h3>
                            <div class="chart-controls">
                                <button class="btn btn-sm btn-outline" id="risk-assess-btn">Assess</button>
                            </div>
                        </div>
                        <div class="chart-container">
                            <canvas id="risk-chart"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- Portfolio Optimization -->
                <div class="chart-section">
                    <div class="chart-card">
                        <div class="chart-header">
                            <h3>Portfolio Optimization</h3>
                            <div class="chart-controls">
                                <button class="btn btn-sm btn-outline" id="portfolio-optimize-btn">Optimize</button>
                            </div>
                        </div>
                        <div class="chart-container">
                            <canvas id="portfolio-chart"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- Sentiment Analysis -->
                <div class="chart-section">
                    <div class="chart-card">
                        <div class="chart-header">
                            <h3>Market Sentiment</h3>
                            <div class="chart-controls">
                                <button class="btn btn-sm btn-outline" id="sentiment-analyze-btn">Analyze</button>
                            </div>
                        </div>
                        <div class="chart-container">
                            <canvas id="sentiment-chart"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- Market Trends -->
                <div class="chart-section full-width">
                    <div class="chart-card">
                        <div class="chart-header">
                            <h3>Market Trends</h3>
                            <div class="chart-controls">
                                <button class="btn btn-sm btn-outline" id="trend-analyze-btn">Analyze</button>
                            </div>
                        </div>
                        <div class="chart-container">
                            <canvas id="trend-chart"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- Anomaly Detection -->
                <div class="chart-section">
                    <div class="chart-card">
                        <div class="chart-header">
                            <h3>Anomaly Detection</h3>
                            <div class="chart-controls">
                                <button class="btn btn-sm btn-outline" id="anomaly-detect-btn">Detect</button>
                            </div>
                        </div>
                        <div class="chart-container">
                            <canvas id="anomaly-chart"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- Real Options Analysis -->
                <div class="chart-section">
                    <div class="chart-card">
                        <div class="chart-header">
                            <h3>Real Options Value</h3>
                            <div class="chart-controls">
                                <button class="btn btn-sm btn-outline" id="options-value-btn">Value</button>
                            </div>
                        </div>
                        <div class="chart-container">
                            <canvas id="options-chart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Alerts Panel -->
            <div class="alerts-panel" id="alerts-panel">
                <div class="alerts-header">
                    <h3><i class="fas fa-bell"></i> Alerts & Notifications</h3>
                    <button class="btn btn-sm btn-outline" id="clear-alerts">Clear All</button>
                </div>
                <div class="alerts-list" id="alerts-list">
                    <!-- Alerts will be populated here -->
                </div>
            </div>
        `;
    }
    
    async initializeCharts() {
        // Initialize Chart.js charts
        this.charts.revenue = this.createRevenueChart();
        this.charts.risk = this.createRiskChart();
        this.charts.portfolio = this.createPortfolioChart();
        this.charts.sentiment = this.createSentimentChart();
        this.charts.trend = this.createTrendChart();
        this.charts.anomaly = this.createAnomalyChart();
        this.charts.options = this.createOptionsChart();
    }
    
    createRevenueChart() {
        const ctx = document.getElementById('revenue-chart');
        if (!ctx) return null;
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Historical Revenue',
                    data: [],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Predicted Revenue',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderDash: [5, 5],
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
    
    createRiskChart() {
        const ctx = document.getElementById('risk-chart');
        if (!ctx) return null;
        
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Low Risk', 'Medium Risk', 'High Risk', 'Critical Risk'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        '#10b981',
                        '#f59e0b',
                        '#ef4444',
                        '#dc2626'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    createPortfolioChart() {
        const ctx = document.getElementById('portfolio-chart');
        if (!ctx) return null;
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Current Allocation',
                    data: [],
                    backgroundColor: '#2563eb'
                }, {
                    label: 'Optimized Allocation',
                    data: [],
                    backgroundColor: '#10b981'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    createSentimentChart() {
        const ctx = document.getElementById('sentiment-chart');
        if (!ctx) return null;
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Sentiment Score',
                    data: [],
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        min: -1,
                        max: 1,
                        ticks: {
                            callback: function(value) {
                                if (value === 0) return 'Neutral';
                                if (value > 0) return 'Positive';
                                return 'Negative';
                            }
                        }
                    }
                }
            }
        });
    }
    
    createTrendChart() {
        const ctx = document.getElementById('trend-chart');
        if (!ctx) return null;
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Price Trend',
                    data: [],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Support Level',
                    data: [],
                    borderColor: '#10b981',
                    borderDash: [5, 5],
                    fill: false
                }, {
                    label: 'Resistance Level',
                    data: [],
                    borderColor: '#ef4444',
                    borderDash: [5, 5],
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                }
            }
        });
    }
    
    createAnomalyChart() {
        const ctx = document.getElementById('anomaly-chart');
        if (!ctx) return null;
        
        return new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Normal Data',
                    data: [],
                    backgroundColor: '#2563eb'
                }, {
                    label: 'Anomalies',
                    data: [],
                    backgroundColor: '#ef4444'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Value'
                        }
                    }
                }
            }
        });
    }
    
    createOptionsChart() {
        const ctx = document.getElementById('options-chart');
        if (!ctx) return null;
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Option Value', 'Intrinsic Value', 'Time Value'],
                datasets: [{
                    label: 'Real Options Analysis',
                    data: [0, 0, 0],
                    backgroundColor: [
                        '#2563eb',
                        '#10b981',
                        '#f59e0b'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
    
    setupEventListeners() {
        // Refresh button
        document.getElementById('refresh-dashboard')?.addEventListener('click', () => {
            this.loadDashboardData();
        });
        
        // Export button
        document.getElementById('export-dashboard')?.addEventListener('click', () => {
            this.exportDashboard();
        });
        
        // Time range selector
        document.getElementById('time-range')?.addEventListener('change', (e) => {
            this.loadDashboardData(e.target.value);
        });
        
        // Analysis buttons
        document.getElementById('revenue-forecast-btn')?.addEventListener('click', () => {
            this.performRevenueForecast();
        });
        
        document.getElementById('risk-assess-btn')?.addEventListener('click', () => {
            this.performRiskAssessment();
        });
        
        document.getElementById('portfolio-optimize-btn')?.addEventListener('click', () => {
            this.performPortfolioOptimization();
        });
        
        document.getElementById('sentiment-analyze-btn')?.addEventListener('click', () => {
            this.performSentimentAnalysis();
        });
        
        document.getElementById('trend-analyze-btn')?.addEventListener('click', () => {
            this.performTrendAnalysis();
        });
        
        document.getElementById('anomaly-detect-btn')?.addEventListener('click', () => {
            this.performAnomalyDetection();
        });
        
        document.getElementById('options-value-btn')?.addEventListener('click', () => {
            this.performOptionsValuation();
        });
        
        // Clear alerts
        document.getElementById('clear-alerts')?.addEventListener('click', () => {
            this.clearAlerts();
        });
    }
    
    async loadDashboardData(timeRange = '7d') {
        try {
            // Show loading state
            this.showLoading();
            
            // Load comprehensive analytics data
            const response = await fetch(`/api/analytics/comprehensive`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    time_range: timeRange,
                    include_all_models: true
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.currentData = data;
            
            // Update dashboard with new data
            this.updateMetrics(data);
            this.updateCharts(data);
            this.updateAlerts(data.alerts || []);
            
            // Hide loading state
            this.hideLoading();
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showError('Failed to load dashboard data');
            this.hideLoading();
        }
    }
    
    updateMetrics(data) {
        // Update revenue growth metric
        if (data.revenue_prediction) {
            const growth = data.revenue_prediction.predicted_value;
            const change = data.revenue_prediction.confidence_interval;
            document.getElementById('revenue-growth').textContent = `${growth.toFixed(2)}%`;
            document.getElementById('revenue-change').textContent = `±${change.toFixed(2)}%`;
        }
        
        // Update risk score metric
        if (data.risk_assessment) {
            const score = data.risk_assessment.risk_score;
            const level = data.risk_assessment.risk_level;
            document.getElementById('risk-score').textContent = `${score.toFixed(2)}`;
            document.getElementById('risk-change').textContent = level.toUpperCase();
        }
        
        // Update portfolio return metric
        if (data.portfolio_optimization) {
            const return_val = data.portfolio_optimization.expected_return;
            const risk = data.portfolio_optimization.portfolio_risk;
            document.getElementById('portfolio-return').textContent = `${return_val.toFixed(2)}%`;
            document.getElementById('portfolio-change').textContent = `Risk: ${risk.toFixed(2)}%`;
        }
        
        // Update sentiment score metric
        if (data.sentiment_analysis) {
            const score = data.sentiment_analysis.sentiment_score;
            const confidence = data.sentiment_analysis.confidence;
            document.getElementById('sentiment-score').textContent = score.toFixed(3);
            document.getElementById('sentiment-change').textContent = `${confidence.toFixed(1)}% conf.`;
        }
    }
    
    updateCharts(data) {
        // Update revenue chart
        if (data.revenue_prediction && this.charts.revenue) {
            this.charts.revenue.data.labels = data.revenue_prediction.time_labels || [];
            this.charts.revenue.data.datasets[0].data = data.revenue_prediction.historical_data || [];
            this.charts.revenue.data.datasets[1].data = data.revenue_prediction.predicted_data || [];
            this.charts.revenue.update();
        }
        
        // Update risk chart
        if (data.risk_assessment && this.charts.risk) {
            this.charts.risk.data.datasets[0].data = [
                data.risk_assessment.low_risk_percent || 0,
                data.risk_assessment.medium_risk_percent || 0,
                data.risk_assessment.high_risk_percent || 0,
                data.risk_assessment.critical_risk_percent || 0
            ];
            this.charts.risk.update();
        }
        
        // Update portfolio chart
        if (data.portfolio_optimization && this.charts.portfolio) {
            this.charts.portfolio.data.labels = data.portfolio_optimization.asset_names || [];
            this.charts.portfolio.data.datasets[0].data = data.portfolio_optimization.current_weights || [];
            this.charts.portfolio.data.datasets[1].data = data.portfolio_optimization.optimized_weights || [];
            this.charts.portfolio.update();
        }
        
        // Update sentiment chart
        if (data.sentiment_analysis && this.charts.sentiment) {
            this.charts.sentiment.data.labels = data.sentiment_analysis.time_labels || [];
            this.charts.sentiment.data.datasets[0].data = data.sentiment_analysis.sentiment_scores || [];
            this.charts.sentiment.update();
        }
        
        // Update trend chart
        if (data.market_trend && this.charts.trend) {
            this.charts.trend.data.labels = data.market_trend.time_labels || [];
            this.charts.trend.data.datasets[0].data = data.market_trend.price_data || [];
            this.charts.trend.data.datasets[1].data = data.market_trend.support_levels || [];
            this.charts.trend.data.datasets[2].data = data.market_trend.resistance_levels || [];
            this.charts.trend.update();
        }
        
        // Update anomaly chart
        if (data.anomaly_detection && this.charts.anomaly) {
            this.charts.anomaly.data.datasets[0].data = data.anomaly_detection.normal_data || [];
            this.charts.anomaly.data.datasets[1].data = data.anomaly_detection.anomalies || [];
            this.charts.anomaly.update();
        }
        
        // Update options chart
        if (data.real_options && this.charts.options) {
            this.charts.options.data.datasets[0].data = [
                data.real_options.option_value || 0,
                data.real_options.intrinsic_value || 0,
                data.real_options.time_value || 0
            ];
            this.charts.options.update();
        }
    }
    
    updateAlerts(alerts) {
        const alertsList = document.getElementById('alerts-list');
        if (!alertsList) return;
        
        alertsList.innerHTML = '';
        
        alerts.forEach(alert => {
            const alertElement = document.createElement('div');
            alertElement.className = `alert alert-${alert.severity}`;
            alertElement.innerHTML = `
                <div class="alert-header">
                    <span class="alert-title">${alert.title}</span>
                    <span class="alert-time">${new Date(alert.timestamp).toLocaleString()}</span>
                </div>
                <div class="alert-message">${alert.message}</div>
            `;
            alertsList.appendChild(alertElement);
        });
    }
    
    async performRevenueForecast() {
        try {
            const response = await fetch('/api/analytics/revenue/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    forecast_periods: 12,
                    include_confidence_intervals: true
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateRevenueChart(data);
                this.addAlert('Revenue forecast completed successfully', 'success');
            }
        } catch (error) {
            console.error('Revenue forecast failed:', error);
            this.addAlert('Revenue forecast failed', 'error');
        }
    }
    
    async performRiskAssessment() {
        try {
            const response = await fetch('/api/analytics/risk/assess', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    include_detailed_analysis: true
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateRiskChart(data);
                this.addAlert('Risk assessment completed successfully', 'success');
            }
        } catch (error) {
            console.error('Risk assessment failed:', error);
            this.addAlert('Risk assessment failed', 'error');
        }
    }
    
    async performPortfolioOptimization() {
        try {
            const response = await fetch('/api/analytics/portfolio/optimize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    target_return: 0.10,
                    risk_tolerance: 0.15
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updatePortfolioChart(data);
                this.addAlert('Portfolio optimization completed successfully', 'success');
            }
        } catch (error) {
            console.error('Portfolio optimization failed:', error);
            this.addAlert('Portfolio optimization failed', 'error');
        }
    }
    
    async performSentimentAnalysis() {
        try {
            const response = await fetch('/api/analytics/sentiment/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    include_historical_trends: true
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateSentimentChart(data);
                this.addAlert('Sentiment analysis completed successfully', 'success');
            }
        } catch (error) {
            console.error('Sentiment analysis failed:', error);
            this.addAlert('Sentiment analysis failed', 'error');
        }
    }
    
    async performTrendAnalysis() {
        try {
            const response = await fetch('/api/analytics/market/trend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    period: 30,
                    include_support_resistance: true
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateTrendChart(data);
                this.addAlert('Trend analysis completed successfully', 'success');
            }
        } catch (error) {
            console.error('Trend analysis failed:', error);
            this.addAlert('Trend analysis failed', 'error');
        }
    }
    
    async performAnomalyDetection() {
        try {
            const response = await fetch('/api/analytics/anomalies/detect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    metric: 'revenue',
                    sensitivity: 'medium'
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateAnomalyChart(data);
                this.addAlert('Anomaly detection completed successfully', 'success');
            }
        } catch (error) {
            console.error('Anomaly detection failed:', error);
            this.addAlert('Anomaly detection failed', 'error');
        }
    }
    
    async performOptionsValuation() {
        try {
            const response = await fetch('/api/analytics/real-options/value', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    option_type: 'expansion',
                    include_sensitivity_analysis: true
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateOptionsChart(data);
                this.addAlert('Real options valuation completed successfully', 'success');
            }
        } catch (error) {
            console.error('Real options valuation failed:', error);
            this.addAlert('Real options valuation failed', 'error');
        }
    }
    
    updateRevenueChart(data) {
        if (this.charts.revenue && data.predicted_data) {
            this.charts.revenue.data.datasets[1].data = data.predicted_data;
            this.charts.revenue.update();
        }
    }
    
    updateRiskChart(data) {
        if (this.charts.risk && data.risk_distribution) {
            this.charts.risk.data.datasets[0].data = data.risk_distribution;
            this.charts.risk.update();
        }
    }
    
    updatePortfolioChart(data) {
        if (this.charts.portfolio && data.optimized_weights) {
            this.charts.portfolio.data.datasets[1].data = data.optimized_weights;
            this.charts.portfolio.update();
        }
    }
    
    updateSentimentChart(data) {
        if (this.charts.sentiment && data.sentiment_trends) {
            this.charts.sentiment.data.datasets[0].data = data.sentiment_trends;
            this.charts.sentiment.update();
        }
    }
    
    updateTrendChart(data) {
        if (this.charts.trend && data.trend_data) {
            this.charts.trend.data.datasets[0].data = data.trend_data;
            this.charts.trend.update();
        }
    }
    
    updateAnomalyChart(data) {
        if (this.charts.anomaly && data.anomalies) {
            this.charts.anomaly.data.datasets[1].data = data.anomalies;
            this.charts.anomaly.update();
        }
    }
    
    updateOptionsChart(data) {
        if (this.charts.options && data.option_components) {
            this.charts.options.data.datasets[0].data = data.option_components;
            this.charts.options.update();
        }
    }
    
    addAlert(message, severity = 'info') {
        const alertsList = document.getElementById('alerts-list');
        if (!alertsList) return;
        
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${severity}`;
        alertElement.innerHTML = `
            <div class="alert-header">
                <span class="alert-title">${severity.toUpperCase()}</span>
                <span class="alert-time">${new Date().toLocaleString()}</span>
            </div>
            <div class="alert-message">${message}</div>
        `;
        
        alertsList.insertBefore(alertElement, alertsList.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertElement.parentNode) {
                alertElement.remove();
            }
        }, 5000);
    }
    
    clearAlerts() {
        const alertsList = document.getElementById('alerts-list');
        if (alertsList) {
            alertsList.innerHTML = '';
        }
    }
    
    async exportDashboard() {
        try {
            const response = await fetch('/api/analytics/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    format: 'pdf',
                    include_charts: true,
                    include_data: true
                })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `analytics-dashboard-${new Date().toISOString().split('T')[0]}.pdf`;
                a.click();
                window.URL.revokeObjectURL(url);
                
                this.addAlert('Dashboard exported successfully', 'success');
            }
        } catch (error) {
            console.error('Export failed:', error);
            this.addAlert('Export failed', 'error');
        }
    }
    
    startAutoRefresh() {
        // Refresh every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData();
        }, 5 * 60 * 1000);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    showLoading() {
        const dashboard = document.getElementById('analytics-dashboard');
        if (dashboard) {
            dashboard.classList.add('loading');
        }
    }
    
    hideLoading() {
        const dashboard = document.getElementById('analytics-dashboard');
        if (dashboard) {
            dashboard.classList.remove('loading');
        }
    }
    
    showError(message) {
        this.addAlert(message, 'error');
    }
    
    getAuthToken() {
        return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    }
    
    destroy() {
        this.stopAutoRefresh();
        
        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.destroy) {
                chart.destroy();
            }
        });
        
        // Remove dashboard element
        const dashboard = document.getElementById('analytics-dashboard');
        if (dashboard) {
            dashboard.remove();
        }
        
        this.isInitialized = false;
    }
}

// Export for use in other modules
window.AnalyticsDashboard = AnalyticsDashboard;
