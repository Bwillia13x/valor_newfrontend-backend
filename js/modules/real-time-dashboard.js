/**
 * Real-time Dashboard Module for Valor IVX Platform
 * Phase 9: Advanced Analytics and Machine Learning
 * 
 * This module provides real-time dashboard capabilities including:
 * - Real-time data visualization
 * - Live market updates
 * - Interactive dashboards
 * - Real-time analytics
 * - Live alerts and notifications
 * - Custom dashboard layouts
 */

class RealTimeDashboard {
    constructor() {
        this.dashboards = new Map();
        this.websocketConnections = new Map();
        this.dataStreams = new Map();
        this.alertHandlers = new Map();
        this.updateIntervals = new Map();
        
        // Dashboard configurations
        this.defaultConfig = {
            updateInterval: 1000,
            autoRefresh: true,
            showAlerts: true,
            showMetrics: true,
            theme: 'dark',
            layout: 'grid'
        };
        
        // Real-time data cache
        this.dataCache = new Map();
        this.lastUpdate = new Map();
        
        // Performance tracking
        this.metrics = {
            updatesReceived: 0,
            alertsGenerated: 0,
            errors: 0,
            latency: []
        };
        
        this.init();
    }
    
    async init() {
        try {
            this.setupEventListeners();
            this.initializeWebSocket();
            console.log('Real-time Dashboard initialized');
        } catch (error) {
            console.error('Error initializing Real-time Dashboard:', error);
        }
    }
    
    setupEventListeners() {
        // Listen for window focus/blur to manage updates
        window.addEventListener('focus', () => {
            this.resumeUpdates();
        });
        
        window.addEventListener('blur', () => {
            this.pauseUpdates();
        });
        
        // Listen for network status changes
        window.addEventListener('online', () => {
            this.reconnectWebSocket();
        });
        
        window.addEventListener('offline', () => {
            this.disconnectWebSocket();
        });
    }
    
    initializeWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected for real-time dashboard');
                this.subscribeToSymbols();
            };
            
            this.websocket.onmessage = (event) => {
                this.handleWebSocketMessage(event.data);
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.scheduleReconnect();
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.metrics.errors++;
            };
            
        } catch (error) {
            console.error('Error initializing WebSocket:', error);
        }
    }
    
    // Dashboard Creation and Management
    createDashboard(containerId, config = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return null;
        }
        
        const dashboardConfig = { ...this.defaultConfig, ...config };
        
        const dashboard = {
            id: containerId,
            container,
            config: dashboardConfig,
            widgets: new Map(),
            data: {},
            alerts: [],
            metrics: {},
            isActive: true,
            
            // Dashboard methods
            addWidget: (widgetId, widgetType, widgetConfig) => {
                return this.addWidgetToDashboard(dashboard, widgetId, widgetType, widgetConfig);
            },
            removeWidget: (widgetId) => {
                return this.removeWidgetFromDashboard(dashboard, widgetId);
            },
            update: (data) => {
                return this.updateDashboard(dashboard, data);
            },
            refresh: () => {
                return this.refreshDashboard(dashboard);
            },
            destroy: () => {
                return this.destroyDashboard(dashboard);
            }
        };
        
        this.dashboards.set(containerId, dashboard);
        this.renderDashboard(dashboard);
        
        return dashboard;
    }
    
    addWidgetToDashboard(dashboard, widgetId, widgetType, widgetConfig) {
        const widgetContainer = document.createElement('div');
        widgetContainer.id = `widget-${widgetId}`;
        widgetContainer.className = 'dashboard-widget';
        
        dashboard.container.appendChild(widgetContainer);
        
        let widget;
        switch (widgetType) {
            case 'price-ticker':
                widget = this.createPriceTickerWidget(widgetContainer, widgetConfig);
                break;
            case 'market-overview':
                widget = this.createMarketOverviewWidget(widgetContainer, widgetConfig);
                break;
            case 'sentiment-gauge':
                widget = this.createSentimentGaugeWidget(widgetContainer, widgetConfig);
                break;
            case 'alerts-panel':
                widget = this.createAlertsPanelWidget(widgetContainer, widgetConfig);
                break;
            case 'performance-chart':
                widget = this.createPerformanceChartWidget(widgetContainer, widgetConfig);
                break;
            case 'analytics-summary':
                widget = this.createAnalyticsSummaryWidget(widgetContainer, widgetConfig);
                break;
            case 'real-time-chart':
                widget = this.createRealTimeChartWidget(widgetContainer, widgetConfig);
                break;
            default:
                console.error(`Unknown widget type: ${widgetType}`);
                return null;
        }
        
        dashboard.widgets.set(widgetId, widget);
        return widget;
    }
    
    removeWidgetFromDashboard(dashboard, widgetId) {
        const widget = dashboard.widgets.get(widgetId);
        if (widget) {
            if (widget.destroy) {
                widget.destroy();
            }
            dashboard.widgets.delete(widgetId);
            
            const widgetContainer = document.getElementById(`widget-${widgetId}`);
            if (widgetContainer) {
                widgetContainer.remove();
            }
        }
    }
    
    // Widget Creation Methods
    createPriceTickerWidget(container, config) {
        const widget = {
            type: 'price-ticker',
            container,
            config,
            data: {},
            
            update: (data) => {
                this.updatePriceTickerWidget(widget, data);
            },
            
            destroy: () => {
                container.innerHTML = '';
            }
        };
        
        // Initialize widget HTML
        container.innerHTML = `
            <div class="price-ticker-widget">
                <div class="widget-header">
                    <h3>${config.title || 'Price Ticker'}</h3>
                    <div class="widget-controls">
                        <button class="refresh-btn" onclick="realTimeDashboard.refreshWidget('${container.id}')">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </div>
                </div>
                <div class="ticker-content">
                    <div class="symbol-info">
                        <span class="symbol">${config.symbol || 'N/A'}</span>
                        <span class="price">$0.00</span>
                        <span class="change">0.00 (0.00%)</span>
                    </div>
                    <div class="ticker-details">
                        <div class="detail-item">
                            <span class="label">Volume:</span>
                            <span class="value volume">0</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">Market Cap:</span>
                            <span class="value market-cap">$0</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        return widget;
    }
    
    createMarketOverviewWidget(container, config) {
        const widget = {
            type: 'market-overview',
            container,
            config,
            data: {},
            
            update: (data) => {
                this.updateMarketOverviewWidget(widget, data);
            },
            
            destroy: () => {
                container.innerHTML = '';
            }
        };
        
        // Initialize widget HTML
        container.innerHTML = `
            <div class="market-overview-widget">
                <div class="widget-header">
                    <h3>${config.title || 'Market Overview'}</h3>
                </div>
                <div class="market-content">
                    <div class="market-indices">
                        <div class="index-item">
                            <span class="index-name">S&P 500</span>
                            <span class="index-value">0.00</span>
                            <span class="index-change">0.00%</span>
                        </div>
                        <div class="index-item">
                            <span class="index-name">NASDAQ</span>
                            <span class="index-value">0.00</span>
                            <span class="index-change">0.00%</span>
                        </div>
                        <div class="index-item">
                            <span class="index-name">DOW</span>
                            <span class="index-value">0.00</span>
                            <span class="index-change">0.00%</span>
                        </div>
                    </div>
                    <div class="market-metrics">
                        <div class="metric-item">
                            <span class="metric-label">VIX:</span>
                            <span class="metric-value vix">0.00</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Sentiment:</span>
                            <span class="metric-value sentiment">Neutral</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        return widget;
    }
    
    createSentimentGaugeWidget(container, config) {
        const widget = {
            type: 'sentiment-gauge',
            container,
            config,
            data: {},
            
            update: (data) => {
                this.updateSentimentGaugeWidget(widget, data);
            },
            
            destroy: () => {
                container.innerHTML = '';
            }
        };
        
        // Initialize widget HTML
        container.innerHTML = `
            <div class="sentiment-gauge-widget">
                <div class="widget-header">
                    <h3>${config.title || 'Market Sentiment'}</h3>
                </div>
                <div class="gauge-content">
                    <div class="gauge-container">
                        <canvas id="sentiment-gauge-${container.id}" width="200" height="200"></canvas>
                    </div>
                    <div class="sentiment-info">
                        <div class="sentiment-score">
                            <span class="score-label">Score:</span>
                            <span class="score-value">0.00</span>
                        </div>
                        <div class="sentiment-label">
                            <span class="label">Neutral</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Initialize gauge chart
        this.initializeSentimentGauge(widget);
        
        return widget;
    }
    
    createAlertsPanelWidget(container, config) {
        const widget = {
            type: 'alerts-panel',
            container,
            config,
            data: {},
            alerts: [],
            
            update: (data) => {
                this.updateAlertsPanelWidget(widget, data);
            },
            
            addAlert: (alert) => {
                this.addAlertToWidget(widget, alert);
            },
            
            destroy: () => {
                container.innerHTML = '';
            }
        };
        
        // Initialize widget HTML
        container.innerHTML = `
            <div class="alerts-panel-widget">
                <div class="widget-header">
                    <h3>${config.title || 'Alerts'}</h3>
                    <div class="widget-controls">
                        <button class="clear-alerts-btn" onclick="realTimeDashboard.clearAlerts('${container.id}')">
                            Clear All
                        </button>
                    </div>
                </div>
                <div class="alerts-content">
                    <div class="alerts-list">
                        <!-- Alerts will be dynamically added here -->
                    </div>
                </div>
            </div>
        `;
        
        return widget;
    }
    
    createPerformanceChartWidget(container, config) {
        const widget = {
            type: 'performance-chart',
            container,
            config,
            data: {},
            chart: null,
            
            update: (data) => {
                this.updatePerformanceChartWidget(widget, data);
            },
            
            destroy: () => {
                if (widget.chart) {
                    widget.chart.destroy();
                }
                container.innerHTML = '';
            }
        };
        
        // Initialize widget HTML
        container.innerHTML = `
            <div class="performance-chart-widget">
                <div class="widget-header">
                    <h3>${config.title || 'Performance Chart'}</h3>
                </div>
                <div class="chart-content">
                    <canvas id="performance-chart-${container.id}" width="400" height="300"></canvas>
                </div>
            </div>
        `;
        
        // Initialize chart
        this.initializePerformanceChart(widget);
        
        return widget;
    }
    
    createAnalyticsSummaryWidget(container, config) {
        const widget = {
            type: 'analytics-summary',
            container,
            config,
            data: {},
            
            update: (data) => {
                this.updateAnalyticsSummaryWidget(widget, data);
            },
            
            destroy: () => {
                container.innerHTML = '';
            }
        };
        
        // Initialize widget HTML
        container.innerHTML = `
            <div class="analytics-summary-widget">
                <div class="widget-header">
                    <h3>${config.title || 'Analytics Summary'}</h3>
                </div>
                <div class="analytics-content">
                    <div class="analytics-metrics">
                        <div class="metric-item">
                            <span class="metric-label">RSI:</span>
                            <span class="metric-value rsi">0.00</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">MACD:</span>
                            <span class="metric-value macd">0.00</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Volatility:</span>
                            <span class="metric-value volatility">0.00%</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Beta:</span>
                            <span class="metric-value beta">0.00</span>
                        </div>
                    </div>
                    <div class="analytics-signals">
                        <div class="signal-item">
                            <span class="signal-label">Trend:</span>
                            <span class="signal-value trend">Neutral</span>
                        </div>
                        <div class="signal-item">
                            <span class="signal-label">Strength:</span>
                            <span class="signal-value strength">Medium</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        return widget;
    }
    
    createRealTimeChartWidget(container, config) {
        const widget = {
            type: 'real-time-chart',
            container,
            config,
            data: {},
            chart: null,
            
            update: (data) => {
                this.updateRealTimeChartWidget(widget, data);
            },
            
            destroy: () => {
                if (widget.chart) {
                    widget.chart.destroy();
                }
                container.innerHTML = '';
            }
        };
        
        // Initialize widget HTML
        container.innerHTML = `
            <div class="real-time-chart-widget">
                <div class="widget-header">
                    <h3>${config.title || 'Real-time Chart'}</h3>
                </div>
                <div class="chart-content">
                    <canvas id="realtime-chart-${container.id}" width="400" height="300"></canvas>
                </div>
            </div>
        `;
        
        // Initialize real-time chart
        this.initializeRealTimeChart(widget);
        
        return widget;
    }
    
    // Widget Update Methods
    updatePriceTickerWidget(widget, data) {
        const container = widget.container;
        
        if (data.symbol) {
            container.querySelector('.symbol').textContent = data.symbol;
        }
        
        if (data.price !== undefined) {
            const priceElement = container.querySelector('.price');
            const changeElement = container.querySelector('.change');
            
            priceElement.textContent = `$${data.price.toFixed(2)}`;
            
            if (data.change !== undefined && data.changePercent !== undefined) {
                const changeColor = data.change >= 0 ? 'positive' : 'negative';
                changeElement.textContent = `${data.change >= 0 ? '+' : ''}${data.change.toFixed(2)} (${data.changePercent >= 0 ? '+' : ''}${data.changePercent.toFixed(2)}%)`;
                changeElement.className = `change ${changeColor}`;
            }
        }
        
        if (data.volume !== undefined) {
            container.querySelector('.volume').textContent = this.formatNumber(data.volume);
        }
        
        if (data.marketCap !== undefined) {
            container.querySelector('.market-cap').textContent = this.formatCurrency(data.marketCap);
        }
    }
    
    updateMarketOverviewWidget(widget, data) {
        const container = widget.container;
        
        if (data.indices) {
            Object.keys(data.indices).forEach(index => {
                const indexElement = container.querySelector(`.index-item:has(.index-name:contains('${index}'))`);
                if (indexElement && data.indices[index]) {
                    const indexData = data.indices[index];
                    indexElement.querySelector('.index-value').textContent = indexData.current.toFixed(2);
                    indexElement.querySelector('.index-change').textContent = `${indexData.changePercent >= 0 ? '+' : ''}${indexData.changePercent.toFixed(2)}%`;
                }
            });
        }
        
        if (data.vix !== undefined) {
            container.querySelector('.vix').textContent = data.vix.toFixed(2);
        }
        
        if (data.sentiment !== undefined) {
            container.querySelector('.sentiment').textContent = data.sentiment;
        }
    }
    
    updateSentimentGaugeWidget(widget, data) {
        if (data.sentiment !== undefined) {
            const container = widget.container;
            const scoreElement = container.querySelector('.score-value');
            const labelElement = container.querySelector('.sentiment-label .label');
            
            scoreElement.textContent = data.sentiment.toFixed(2);
            
            let sentimentLabel = 'Neutral';
            if (data.sentiment > 0.3) sentimentLabel = 'Bullish';
            else if (data.sentiment < -0.3) sentimentLabel = 'Bearish';
            
            labelElement.textContent = sentimentLabel;
            
            // Update gauge chart
            this.updateSentimentGauge(widget, data.sentiment);
        }
    }
    
    updateAlertsPanelWidget(widget, data) {
        if (data.alerts && Array.isArray(data.alerts)) {
            data.alerts.forEach(alert => {
                this.addAlertToWidget(widget, alert);
            });
        }
    }
    
    updatePerformanceChartWidget(widget, data) {
        if (data.performance && widget.chart) {
            // Update chart data
            widget.chart.data.labels = data.performance.labels || [];
            widget.chart.data.datasets[0].data = data.performance.values || [];
            widget.chart.update('none');
        }
    }
    
    updateAnalyticsSummaryWidget(widget, data) {
        const container = widget.container;
        
        if (data.rsi !== undefined) {
            container.querySelector('.rsi').textContent = data.rsi.toFixed(2);
        }
        
        if (data.macd !== undefined) {
            container.querySelector('.macd').textContent = data.macd.toFixed(2);
        }
        
        if (data.volatility !== undefined) {
            container.querySelector('.volatility').textContent = `${(data.volatility * 100).toFixed(2)}%`;
        }
        
        if (data.beta !== undefined) {
            container.querySelector('.beta').textContent = data.beta.toFixed(2);
        }
        
        if (data.trend !== undefined) {
            container.querySelector('.trend').textContent = data.trend;
        }
        
        if (data.strength !== undefined) {
            container.querySelector('.strength').textContent = data.strength;
        }
    }
    
    updateRealTimeChartWidget(widget, data) {
        if (data.chartData && widget.chart) {
            // Update real-time chart
            widget.chart.data.labels = data.chartData.labels || [];
            widget.chart.data.datasets[0].data = data.chartData.values || [];
            widget.chart.update('none');
        }
    }
    
    // Alert Management
    addAlertToWidget(widget, alert) {
        const container = widget.container;
        const alertsList = container.querySelector('.alerts-list');
        
        const alertElement = document.createElement('div');
        alertElement.className = `alert-item ${alert.severity || 'info'}`;
        alertElement.innerHTML = `
            <div class="alert-header">
                <span class="alert-time">${new Date(alert.timestamp).toLocaleTimeString()}</span>
                <span class="alert-severity">${alert.severity || 'info'}</span>
            </div>
            <div class="alert-message">${alert.message}</div>
        `;
        
        alertsList.insertBefore(alertElement, alertsList.firstChild);
        
        // Limit number of alerts
        const maxAlerts = widget.config.maxAlerts || 10;
        while (alertsList.children.length > maxAlerts) {
            alertsList.removeChild(alertsList.lastChild);
        }
        
        // Auto-remove alert after some time
        setTimeout(() => {
            if (alertElement.parentNode) {
                alertElement.remove();
            }
        }, (widget.config.alertTimeout || 30000));
    }
    
    clearAlerts(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            const alertsList = container.querySelector('.alerts-list');
            if (alertsList) {
                alertsList.innerHTML = '';
            }
        }
    }
    
    // Chart Initialization Methods
    initializeSentimentGauge(widget) {
        const canvas = widget.container.querySelector('canvas');
        const ctx = canvas.getContext('2d');
        
        // Create gauge chart using Chart.js
        widget.chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [0, 100],
                    backgroundColor: ['#ff6b6b', '#f0f0f0'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '80%',
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            }
        });
    }
    
    initializePerformanceChart(widget) {
        const canvas = widget.container.querySelector('canvas');
        const ctx = canvas.getContext('2d');
        
        widget.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Performance',
                    data: [],
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    borderWidth: 2,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    initializeRealTimeChart(widget) {
        const canvas = widget.container.querySelector('canvas');
        const ctx = canvas.getContext('2d');
        
        widget.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Real-time Data',
                    data: [],
                    borderColor: '#2196F3',
                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                    borderWidth: 2,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'second'
                        }
                    }
                }
            }
        });
    }
    
    // WebSocket Message Handling
    handleWebSocketMessage(data) {
        try {
            const message = JSON.parse(data);
            
            switch (message.type) {
                case 'data_update':
                    this.handleDataUpdate(message);
                    break;
                case 'alert':
                    this.handleAlert(message);
                    break;
                case 'market_update':
                    this.handleMarketUpdate(message);
                    break;
                default:
                    console.log('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Error handling WebSocket message:', error);
        }
    }
    
    handleDataUpdate(message) {
        this.metrics.updatesReceived++;
        
        // Update data cache
        if (message.symbol) {
            this.dataCache.set(message.symbol, message.data);
            this.lastUpdate.set(message.symbol, new Date());
        }
        
        // Update dashboards
        this.dashboards.forEach(dashboard => {
            if (dashboard.isActive) {
                this.updateDashboard(dashboard, message.data);
            }
        });
    }
    
    handleAlert(message) {
        this.metrics.alertsGenerated++;
        
        // Add alert to all alert panels
        this.dashboards.forEach(dashboard => {
            dashboard.widgets.forEach(widget => {
                if (widget.type === 'alerts-panel' && widget.addAlert) {
                    widget.addAlert(message.alert);
                }
            });
        });
        
        // Show notification if enabled
        if (this.defaultConfig.showAlerts) {
            this.showNotification(message.alert);
        }
    }
    
    handleMarketUpdate(message) {
        // Update market overview widgets
        this.dashboards.forEach(dashboard => {
            dashboard.widgets.forEach(widget => {
                if (widget.type === 'market-overview') {
                    widget.update(message.data);
                }
            });
        });
    }
    
    // Utility Methods
    subscribeToSymbols() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            const symbols = this.getSubscribedSymbols();
            this.websocket.send(JSON.stringify({
                type: 'subscribe',
                symbols: symbols
            }));
        }
    }
    
    getSubscribedSymbols() {
        const symbols = new Set();
        this.dashboards.forEach(dashboard => {
            dashboard.widgets.forEach(widget => {
                if (widget.config.symbol) {
                    symbols.add(widget.config.symbol);
                }
            });
        });
        return Array.from(symbols);
    }
    
    showNotification(alert) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Valor IVX Alert', {
                body: alert.message,
                icon: '/favicon.ico'
            });
        }
    }
    
    formatNumber(num) {
        if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
        if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
        if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
        return num.toString();
    }
    
    formatCurrency(amount) {
        if (amount >= 1e9) return '$' + (amount / 1e9).toFixed(2) + 'B';
        if (amount >= 1e6) return '$' + (amount / 1e6).toFixed(2) + 'M';
        if (amount >= 1e3) return '$' + (amount / 1e3).toFixed(2) + 'K';
        return '$' + amount.toFixed(2);
    }
    
    // Dashboard Management Methods
    updateDashboard(dashboard, data) {
        dashboard.widgets.forEach(widget => {
            if (widget.update) {
                widget.update(data);
            }
        });
    }
    
    refreshDashboard(dashboard) {
        // Force refresh of all widgets
        dashboard.widgets.forEach(widget => {
            if (widget.refresh) {
                widget.refresh();
            }
        });
    }
    
    destroyDashboard(dashboard) {
        dashboard.widgets.forEach(widget => {
            if (widget.destroy) {
                widget.destroy();
            }
        });
        dashboard.widgets.clear();
        dashboard.container.innerHTML = '';
        this.dashboards.delete(dashboard.id);
    }
    
    renderDashboard(dashboard) {
        // Apply dashboard styling
        dashboard.container.className = 'real-time-dashboard';
        dashboard.container.style.display = 'grid';
        dashboard.container.style.gridTemplateColumns = 'repeat(auto-fit, minmax(300px, 1fr))';
        dashboard.container.style.gap = '20px';
        dashboard.container.style.padding = '20px';
        dashboard.container.style.backgroundColor = dashboard.config.theme === 'dark' ? '#1a1a1a' : '#f5f5f5';
        dashboard.container.style.color = dashboard.config.theme === 'dark' ? '#ffffff' : '#000000';
    }
    
    // Connection Management
    scheduleReconnect() {
        setTimeout(() => {
            this.initializeWebSocket();
        }, 5000);
    }
    
    reconnectWebSocket() {
        if (this.websocket && this.websocket.readyState === WebSocket.CLOSED) {
            this.initializeWebSocket();
        }
    }
    
    disconnectWebSocket() {
        if (this.websocket) {
            this.websocket.close();
        }
    }
    
    pauseUpdates() {
        this.dashboards.forEach(dashboard => {
            dashboard.isActive = false;
        });
    }
    
    resumeUpdates() {
        this.dashboards.forEach(dashboard => {
            dashboard.isActive = true;
        });
    }
    
    // Public API Methods
    getDashboard(dashboardId) {
        return this.dashboards.get(dashboardId);
    }
    
    getMetrics() {
        return { ...this.metrics };
    }
    
    refreshWidget(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            // Trigger refresh for the specific widget
            const dashboard = this.findDashboardByContainer(container);
            if (dashboard) {
                const widget = this.findWidgetByContainer(dashboard, container);
                if (widget && widget.refresh) {
                    widget.refresh();
                }
            }
        }
    }
    
    findDashboardByContainer(container) {
        for (const [id, dashboard] of this.dashboards) {
            if (dashboard.container === container || dashboard.container.contains(container)) {
                return dashboard;
            }
        }
        return null;
    }
    
    findWidgetByContainer(dashboard, container) {
        for (const [id, widget] of dashboard.widgets) {
            if (widget.container === container) {
                return widget;
            }
        }
        return null;
    }
}

// Initialize the module
const realTimeDashboard = new RealTimeDashboard();

// Export for use in other modules
window.RealTimeDashboard = RealTimeDashboard;
window.realTimeDashboard = realTimeDashboard;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        realTimeDashboard.init();
    });
} else {
    realTimeDashboard.init();
} 