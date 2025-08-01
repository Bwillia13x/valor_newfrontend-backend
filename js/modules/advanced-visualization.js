/**
 * Advanced Visualization Module for Valor IVX Platform
 * Phase 9: Advanced Analytics and Machine Learning
 * 
 * This module provides advanced visualization capabilities including:
 * - Interactive real-time charts
 * - Custom dashboards
 * - Advanced technical indicators
 * - Real-time data visualization
 * - Interactive analytics charts
 * - Custom chart types
 */

class AdvancedVisualization {
    constructor() {
        this.charts = new Map();
        this.dashboards = new Map();
        this.realTimeConnections = new Map();
        this.chartConfigs = new Map();
        this.updateIntervals = new Map();
        
        // Chart libraries
        this.chartLibraries = {
            tradingView: null,
            chartjs: null,
            d3: null
        };
        
        // Default configurations
        this.defaultConfig = {
            theme: 'dark',
            responsive: true,
            animation: true,
            realTime: false,
            updateInterval: 1000
        };
        
        this.init();
    }
    
    async init() {
        try {
            await this.loadChartLibraries();
            this.setupEventListeners();
            this.initializeDefaultCharts();
            console.log('Advanced Visualization initialized');
        } catch (error) {
            console.error('Error initializing Advanced Visualization:', error);
        }
    }
    
    async loadChartLibraries() {
        // Load Chart.js
        if (typeof Chart !== 'undefined') {
            this.chartLibraries.chartjs = Chart;
        } else {
            await this.loadScript('https://cdn.jsdelivr.net/npm/chart.js');
            this.chartLibraries.chartjs = Chart;
        }
        
        // Load D3.js
        if (typeof d3 !== 'undefined') {
            this.chartLibraries.d3 = d3;
        } else {
            await this.loadScript('https://d3js.org/d3.v7.min.js');
            this.chartLibraries.d3 = d3;
        }
        
        // Load TradingView widget
        if (typeof TradingView !== 'undefined') {
            this.chartLibraries.tradingView = TradingView;
        } else {
            await this.loadScript('https://s3.tradingview.com/tv.js');
            this.chartLibraries.tradingView = TradingView;
        }
    }
    
    async loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    setupEventListeners() {
        // Listen for window resize events
        window.addEventListener('resize', () => {
            this.charts.forEach(chart => {
                if (chart && chart.resize) {
                    chart.resize();
                }
            });
        });
        
        // Listen for theme changes
        document.addEventListener('themeChanged', (event) => {
            this.updateTheme(event.detail.theme);
        });
    }
    
    initializeDefaultCharts() {
        // Initialize default chart configurations
        this.chartConfigs.set('price', this.getDefaultPriceChartConfig());
        this.chartConfigs.set('volume', this.getDefaultVolumeChartConfig());
        this.chartConfigs.set('technical', this.getDefaultTechnicalChartConfig());
        this.chartConfigs.set('sentiment', this.getDefaultSentimentChartConfig());
        this.chartConfigs.set('analytics', this.getDefaultAnalyticsChartConfig());
    }
    
    // Chart Creation Methods
    createPriceChart(containerId, symbol, config = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return null;
        }
        
        const chartConfig = { ...this.chartConfigs.get('price'), ...config };
        const chart = this.createTradingViewChart(container, symbol, chartConfig);
        
        this.charts.set(containerId, chart);
        return chart;
    }
    
    createVolumeChart(containerId, data, config = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return null;
        }
        
        const chartConfig = { ...this.chartConfigs.get('volume'), ...config };
        const chart = this.createChartJSChart(container, data, chartConfig);
        
        this.charts.set(containerId, chart);
        return chart;
    }
    
    createTechnicalChart(containerId, data, config = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return null;
        }
        
        const chartConfig = { ...this.chartConfigs.get('technical'), ...config };
        const chart = this.createD3Chart(container, data, chartConfig);
        
        this.charts.set(containerId, chart);
        return chart;
    }
    
    createSentimentChart(containerId, data, config = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return null;
        }
        
        const chartConfig = { ...this.chartConfigs.get('sentiment'), ...config };
        const chart = this.createChartJSChart(container, data, chartConfig);
        
        this.charts.set(containerId, chart);
        return chart;
    }
    
    createAnalyticsChart(containerId, data, config = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return null;
        }
        
        const chartConfig = { ...this.chartConfigs.get('analytics'), ...config };
        const chart = this.createD3Chart(container, data, chartConfig);
        
        this.charts.set(containerId, chart);
        return chart;
    }
    
    // TradingView Chart Creation
    createTradingViewChart(container, symbol, config) {
        const widget = new this.chartLibraries.tradingView.widget({
            symbol: symbol,
            interval: config.interval || '1D',
            timezone: config.timezone || 'America/New_York',
            theme: config.theme || 'dark',
            style: config.style || '1',
            locale: config.locale || 'en',
            toolbar_bg: config.toolbarBg || '#f1f3f6',
            enable_publishing: false,
            allow_symbol_change: config.allowSymbolChange || true,
            container_id: container.id,
            width: container.clientWidth,
            height: container.clientHeight,
            studies: config.studies || [
                'RSI@tv-basicstudies',
                'MACD@tv-basicstudies',
                'BB@tv-basicstudies'
            ],
            disabled_features: config.disabledFeatures || [],
            enabled_features: config.enabledFeatures || []
        });
        
        return {
            widget,
            type: 'tradingview',
            container,
            config,
            update: (data) => this.updateTradingViewChart(widget, data),
            resize: () => widget.resize(),
            destroy: () => widget.remove()
        };
    }
    
    // Chart.js Chart Creation
    createChartJSChart(container, data, config) {
        const ctx = container.getContext('2d');
        const chart = new this.chartLibraries.chartjs(ctx, {
            type: config.type || 'line',
            data: this.prepareChartJSData(data, config),
            options: this.prepareChartJSOptions(config)
        });
        
        return {
            chart,
            type: 'chartjs',
            container,
            config,
            update: (newData) => this.updateChartJSChart(chart, newData, config),
            resize: () => chart.resize(),
            destroy: () => chart.destroy()
        };
    }
    
    // D3.js Chart Creation
    createD3Chart(container, data, config) {
        const chart = this.createD3Visualization(container, data, config);
        
        return {
            chart,
            type: 'd3',
            container,
            config,
            update: (newData) => this.updateD3Chart(chart, newData, config),
            resize: () => this.resizeD3Chart(chart, container, config),
            destroy: () => this.destroyD3Chart(chart)
        };
    }
    
    // Dashboard Creation
    createDashboard(containerId, layout, config = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return null;
        }
        
        const dashboard = {
            container,
            layout,
            charts: new Map(),
            config: { ...this.defaultConfig, ...config },
            addChart: (chartId, chartType, data, chartConfig) => {
                return this.addChartToDashboard(dashboard, chartId, chartType, data, chartConfig);
            },
            removeChart: (chartId) => {
                return this.removeChartFromDashboard(dashboard, chartId);
            },
            update: (data) => {
                return this.updateDashboard(dashboard, data);
            },
            resize: () => {
                return this.resizeDashboard(dashboard);
            },
            destroy: () => {
                return this.destroyDashboard(dashboard);
            }
        };
        
        this.dashboards.set(containerId, dashboard);
        this.renderDashboard(dashboard);
        
        return dashboard;
    }
    
    // Real-time Chart Updates
    startRealTimeUpdates(chartId, symbol, interval = 1000) {
        if (this.realTimeConnections.has(chartId)) {
            this.stopRealTimeUpdates(chartId);
        }
        
        const updateInterval = setInterval(async () => {
            try {
                const data = await this.fetchRealTimeData(symbol);
                const chart = this.charts.get(chartId);
                
                if (chart && chart.update) {
                    chart.update(data);
                }
            } catch (error) {
                console.error(`Error updating real-time chart ${chartId}:`, error);
            }
        }, interval);
        
        this.realTimeConnections.set(chartId, updateInterval);
        this.updateIntervals.set(chartId, interval);
    }
    
    stopRealTimeUpdates(chartId) {
        const interval = this.realTimeConnections.get(chartId);
        if (interval) {
            clearInterval(interval);
            this.realTimeConnections.delete(chartId);
            this.updateIntervals.delete(chartId);
        }
    }
    
    // Data Fetching
    async fetchRealTimeData(symbol) {
        try {
            const response = await fetch(`/api/advanced-analytics/real-time-dashboard`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    symbols: [symbol],
                    include_alerts: true,
                    include_sentiment: true
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            return result.data.symbols[symbol] || {};
        } catch (error) {
            console.error('Error fetching real-time data:', error);
            return {};
        }
    }
    
    // Chart Configuration Methods
    getDefaultPriceChartConfig() {
        return {
            type: 'tradingview',
            interval: '1D',
            theme: 'dark',
            style: '1',
            studies: [
                'RSI@tv-basicstudies',
                'MACD@tv-basicstudies',
                'BB@tv-basicstudies',
                'Volume@tv-basicstudies'
            ],
            enabledFeatures: ['study_templates'],
            disabledFeatures: ['header_symbol_search']
        };
    }
    
    getDefaultVolumeChartConfig() {
        return {
            type: 'bar',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1,
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Volume'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                }
            }
        };
    }
    
    getDefaultTechnicalChartConfig() {
        return {
            type: 'line',
            width: 800,
            height: 400,
            margin: { top: 20, right: 30, bottom: 30, left: 40 },
            colors: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'],
            showLegend: true,
            showGrid: true,
            animate: true
        };
    }
    
    getDefaultSentimentChartConfig() {
        return {
            type: 'doughnut',
            backgroundColor: [
                'rgba(255, 99, 132, 0.2)',
                'rgba(54, 162, 235, 0.2)',
                'rgba(255, 205, 86, 0.2)'
            ],
            borderColor: [
                'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(255, 205, 86, 1)'
            ],
            borderWidth: 1,
            responsive: true,
            maintainAspectRatio: false
        };
    }
    
    getDefaultAnalyticsChartConfig() {
        return {
            type: 'scatter',
            width: 800,
            height: 400,
            margin: { top: 20, right: 30, bottom: 30, left: 40 },
            colors: ['#1f77b4', '#ff7f0e', '#2ca02c'],
            showLegend: true,
            showGrid: true,
            animate: true
        };
    }
    
    // Data Preparation Methods
    prepareChartJSData(data, config) {
        const datasets = [];
        
        if (config.type === 'line' || config.type === 'bar') {
            datasets.push({
                label: config.label || 'Data',
                data: data.values || data,
                backgroundColor: config.backgroundColor || 'rgba(54, 162, 235, 0.2)',
                borderColor: config.borderColor || 'rgba(54, 162, 235, 1)',
                borderWidth: config.borderWidth || 1,
                fill: config.fill || false
            });
        } else if (config.type === 'doughnut' || config.type === 'pie') {
            return {
                labels: data.labels || [],
                datasets: [{
                    data: data.values || data,
                    backgroundColor: config.backgroundColor || [],
                    borderColor: config.borderColor || [],
                    borderWidth: config.borderWidth || 1
                }]
            };
        }
        
        return {
            labels: data.labels || [],
            datasets: datasets
        };
    }
    
    prepareChartJSOptions(config) {
        return {
            responsive: config.responsive !== false,
            maintainAspectRatio: config.maintainAspectRatio !== false,
            animation: config.animation !== false,
            scales: config.scales || {},
            plugins: {
                legend: {
                    display: config.showLegend !== false
                },
                tooltip: {
                    enabled: config.showTooltip !== false
                }
            }
        };
    }
    
    // D3.js Visualization Methods
    createD3Visualization(container, data, config) {
        const d3 = this.chartLibraries.d3;
        
        // Clear container
        d3.select(container).selectAll("*").remove();
        
        const svg = d3.select(container)
            .append("svg")
            .attr("width", config.width || 800)
            .attr("height", config.height || 400);
        
        // Add chart elements based on type
        if (config.type === 'line') {
            return this.createD3LineChart(svg, data, config);
        } else if (config.type === 'scatter') {
            return this.createD3ScatterChart(svg, data, config);
        } else if (config.type === 'bar') {
            return this.createD3BarChart(svg, data, config);
        }
        
        return svg;
    }
    
    createD3LineChart(svg, data, config) {
        const d3 = this.chartLibraries.d3;
        const margin = config.margin || { top: 20, right: 30, bottom: 30, left: 40 };
        const width = (config.width || 800) - margin.left - margin.right;
        const height = (config.height || 400) - margin.top - margin.bottom;
        
        const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
        
        // Scales
        const x = d3.scaleTime().range([0, width]);
        const y = d3.scaleLinear().range([height, 0]);
        
        // Line generator
        const line = d3.line()
            .x(d => x(d.date))
            .y(d => y(d.value));
        
        // Set domains
        x.domain(d3.extent(data, d => d.date));
        y.domain([0, d3.max(data, d => d.value)]);
        
        // Add line
        g.append("path")
            .datum(data)
            .attr("fill", "none")
            .attr("stroke", config.colors[0] || "#1f77b4")
            .attr("stroke-width", 2)
            .attr("d", line);
        
        // Add axes
        g.append("g")
            .attr("transform", `translate(0,${height})`)
            .call(d3.axisBottom(x));
        
        g.append("g")
            .call(d3.axisLeft(y));
        
        return { svg, g, x, y, line, data, config };
    }
    
    createD3ScatterChart(svg, data, config) {
        const d3 = this.chartLibraries.d3;
        const margin = config.margin || { top: 20, right: 30, bottom: 30, left: 40 };
        const width = (config.width || 800) - margin.left - margin.right;
        const height = (config.height || 400) - margin.top - margin.bottom;
        
        const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
        
        // Scales
        const x = d3.scaleLinear().range([0, width]);
        const y = d3.scaleLinear().range([height, 0]);
        
        // Set domains
        x.domain([0, d3.max(data, d => d.x)]);
        y.domain([0, d3.max(data, d => d.y)]);
        
        // Add dots
        g.selectAll("circle")
            .data(data)
            .enter().append("circle")
            .attr("cx", d => x(d.x))
            .attr("cy", d => y(d.y))
            .attr("r", 5)
            .attr("fill", config.colors[0] || "#1f77b4");
        
        // Add axes
        g.append("g")
            .attr("transform", `translate(0,${height})`)
            .call(d3.axisBottom(x));
        
        g.append("g")
            .call(d3.axisLeft(y));
        
        return { svg, g, x, y, data, config };
    }
    
    createD3BarChart(svg, data, config) {
        const d3 = this.chartLibraries.d3;
        const margin = config.margin || { top: 20, right: 30, bottom: 30, left: 40 };
        const width = (config.width || 800) - margin.left - margin.right;
        const height = (config.height || 400) - margin.top - margin.bottom;
        
        const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
        
        // Scales
        const x = d3.scaleBand().range([0, width]).padding(0.1);
        const y = d3.scaleLinear().range([height, 0]);
        
        // Set domains
        x.domain(data.map(d => d.label));
        y.domain([0, d3.max(data, d => d.value)]);
        
        // Add bars
        g.selectAll(".bar")
            .data(data)
            .enter().append("rect")
            .attr("class", "bar")
            .attr("x", d => x(d.label))
            .attr("width", x.bandwidth())
            .attr("y", d => y(d.value))
            .attr("height", d => height - y(d.value))
            .attr("fill", config.colors[0] || "#1f77b4");
        
        // Add axes
        g.append("g")
            .attr("transform", `translate(0,${height})`)
            .call(d3.axisBottom(x));
        
        g.append("g")
            .call(d3.axisLeft(y));
        
        return { svg, g, x, y, data, config };
    }
    
    // Chart Update Methods
    updateTradingViewChart(widget, data) {
        // TradingView charts are self-updating
        // This method can be used for custom updates if needed
        console.log('TradingView chart updated with data:', data);
    }
    
    updateChartJSChart(chart, newData, config) {
        const preparedData = this.prepareChartJSData(newData, config);
        chart.data = preparedData;
        chart.update('none'); // Update without animation for real-time
    }
    
    updateD3Chart(chartInstance, newData, config) {
        // Update D3 chart with new data
        if (chartInstance.line) {
            // Update line chart
            chartInstance.x.domain(d3.extent(newData, d => d.date));
            chartInstance.y.domain([0, d3.max(newData, d => d.value)]);
            
            chartInstance.g.select("path")
                .datum(newData)
                .attr("d", chartInstance.line);
        } else if (chartInstance.data) {
            // Update scatter or bar chart
            this.updateD3Data(chartInstance, newData);
        }
    }
    
    updateD3Data(chartInstance, newData) {
        const d3 = this.chartLibraries.d3;
        
        if (chartInstance.svg.selectAll("circle").size() > 0) {
            // Update scatter chart
            const circles = chartInstance.g.selectAll("circle")
                .data(newData);
            
            circles.exit().remove();
            
            circles.enter().append("circle")
                .merge(circles)
                .attr("cx", d => chartInstance.x(d.x))
                .attr("cy", d => chartInstance.y(d.y))
                .attr("r", 5)
                .attr("fill", chartInstance.config.colors[0] || "#1f77b4");
        } else if (chartInstance.svg.selectAll(".bar").size() > 0) {
            // Update bar chart
            const bars = chartInstance.g.selectAll(".bar")
                .data(newData);
            
            bars.exit().remove();
            
            bars.enter().append("rect")
                .attr("class", "bar")
                .merge(bars)
                .attr("x", d => chartInstance.x(d.label))
                .attr("width", chartInstance.x.bandwidth())
                .attr("y", d => chartInstance.y(d.value))
                .attr("height", d => chartInstance.height - chartInstance.y(d.value))
                .attr("fill", chartInstance.config.colors[0] || "#1f77b4");
        }
    }
    
    // Dashboard Methods
    addChartToDashboard(dashboard, chartId, chartType, data, chartConfig) {
        const chartContainer = document.createElement('div');
        chartContainer.id = `chart-${chartId}`;
        chartContainer.className = 'dashboard-chart';
        
        dashboard.container.appendChild(chartContainer);
        
        let chart;
        switch (chartType) {
            case 'price':
                chart = this.createPriceChart(chartContainer.id, data.symbol, chartConfig);
                break;
            case 'volume':
                chart = this.createVolumeChart(chartContainer.id, data, chartConfig);
                break;
            case 'technical':
                chart = this.createTechnicalChart(chartContainer.id, data, chartConfig);
                break;
            case 'sentiment':
                chart = this.createSentimentChart(chartContainer.id, data, chartConfig);
                break;
            case 'analytics':
                chart = this.createAnalyticsChart(chartContainer.id, data, chartConfig);
                break;
            default:
                console.error(`Unknown chart type: ${chartType}`);
                return null;
        }
        
        dashboard.charts.set(chartId, chart);
        return chart;
    }
    
    removeChartFromDashboard(dashboard, chartId) {
        const chart = dashboard.charts.get(chartId);
        if (chart) {
            if (chart.destroy) {
                chart.destroy();
            }
            dashboard.charts.delete(chartId);
            
            const chartContainer = document.getElementById(`chart-${chartId}`);
            if (chartContainer) {
                chartContainer.remove();
            }
        }
    }
    
    updateDashboard(dashboard, data) {
        dashboard.charts.forEach((chart, chartId) => {
            if (chart.update && data[chartId]) {
                chart.update(data[chartId]);
            }
        });
    }
    
    resizeDashboard(dashboard) {
        dashboard.charts.forEach(chart => {
            if (chart.resize) {
                chart.resize();
            }
        });
    }
    
    destroyDashboard(dashboard) {
        dashboard.charts.forEach(chart => {
            if (chart.destroy) {
                chart.destroy();
            }
        });
        dashboard.charts.clear();
        dashboard.container.innerHTML = '';
    }
    
    renderDashboard(dashboard) {
        // Apply layout and styling
        dashboard.container.className = 'advanced-dashboard';
        dashboard.container.style.display = 'grid';
        dashboard.container.style.gridTemplateColumns = 'repeat(auto-fit, minmax(400px, 1fr))';
        dashboard.container.style.gap = '20px';
        dashboard.container.style.padding = '20px';
    }
    
    // Utility Methods
    updateTheme(theme) {
        this.charts.forEach(chart => {
            if (chart.config) {
                chart.config.theme = theme;
                // Update chart theme if supported
                if (chart.widget && chart.widget.setTheme) {
                    chart.widget.setTheme(theme);
                }
            }
        });
    }
    
    getAuthToken() {
        // Get authentication token from storage or context
        return localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    }
    
    // Public API Methods
    getChart(chartId) {
        return this.charts.get(chartId);
    }
    
    getDashboard(dashboardId) {
        return this.dashboards.get(dashboardId);
    }
    
    destroyChart(chartId) {
        const chart = this.charts.get(chartId);
        if (chart) {
            this.stopRealTimeUpdates(chartId);
            if (chart.destroy) {
                chart.destroy();
            }
            this.charts.delete(chartId);
        }
    }
    
    destroyDashboard(dashboardId) {
        const dashboard = this.dashboards.get(dashboardId);
        if (dashboard) {
            this.destroyDashboard(dashboard);
            this.dashboards.delete(dashboardId);
        }
    }
    
    // Export/Import Methods
    exportChartConfig(chartId) {
        const chart = this.charts.get(chartId);
        if (chart) {
            return {
                id: chartId,
                type: chart.type,
                config: chart.config
            };
        }
        return null;
    }
    
    importChartConfig(config) {
        if (config && config.id && config.type) {
            // Recreate chart with imported configuration
            // Implementation depends on specific requirements
            console.log('Importing chart configuration:', config);
        }
    }
}

// Initialize the module
const advancedVisualization = new AdvancedVisualization();

// Export for use in other modules
window.AdvancedVisualization = AdvancedVisualization;
window.advancedVisualization = advancedVisualization;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        advancedVisualization.init();
    });
} else {
    advancedVisualization.init();
} 