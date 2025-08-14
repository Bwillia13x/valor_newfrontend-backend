/**
 * Advanced Charting Module - Enhanced Financial Visualizations
 * Provides 3D charts, waterfall charts, tornado diagrams, and advanced visualizations
 */

class AdvancedCharting {
    constructor() {
        this.charts = new Map();
        this.benchmarkData = new Map();
        this.accessibilityEnabled = true;
        this.themes = {
            dark: {
                background: '#0c131b',
                grid: '#1a2b3d',
                text: '#e7f6ff',
                textDim: '#a5bed6',
                primary: '#4cc9f0',
                secondary: '#7209b7',
                success: '#4ade80',
                warning: '#fbbf24',
                error: '#f87171',
                accent1: '#3b82f6',
                accent2: '#10b981',
                accent3: '#f59e0b'
            },
            light: {
                background: '#ffffff',
                grid: '#e5e7eb',
                text: '#1f2937',
                textDim: '#6b7280',
                primary: '#3b82f6',
                secondary: '#8b5cf6',
                success: '#10b981',
                warning: '#f59e0b',
                error: '#ef4444',
                accent1: '#06b6d4',
                accent2: '#059669',
                accent3: '#d97706'
            }
        };
        this.currentTheme = 'dark';
        this.tooltipContainer = null;
        this.dataTableContainer = null;
        this.initializeAccessibility();
    }

    /**
     * Initialize accessibility features
     */
    initializeAccessibility() {
        // Create tooltip container
        this.tooltipContainer = document.createElement('div');
        this.tooltipContainer.className = 'chart-tooltip';
        this.tooltipContainer.setAttribute('role', 'tooltip');
        this.tooltipContainer.setAttribute('aria-live', 'polite');
        this.tooltipContainer.style.display = 'none';
        document.body.appendChild(this.tooltipContainer);
        
        // Create data table container
        this.dataTableContainer = document.createElement('div');
        this.dataTableContainer.className = 'chart-data-tables';
        this.dataTableContainer.setAttribute('aria-label', 'Chart data tables');
        document.body.appendChild(this.dataTableContainer);
    }

    /**
     * Create a 3D chart using Three.js
     */
    create3DChart(containerId, data, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`[AdvancedCharting] Container not found: ${containerId}`);
            return null;
        }

        // Check if Three.js is available
        if (typeof THREE === 'undefined') {
            console.warn('[AdvancedCharting] Three.js not loaded, falling back to 2D chart');
            return this.create2DChart(containerId, data, options);
        }

        const chart = {
            id: containerId,
            type: '3d',
            container: container,
            scene: null,
            camera: null,
            renderer: null,
            data: data,
            options: this.mergeOptions(this.getDefault3DOptions(), options)
        };

        this.init3DScene(chart);
        this.render3DChart(chart);
        this.charts.set(containerId, chart);

        return chart;
    }

    /**
     * Initialize 3D scene
     */
    init3DScene(chart) {
        const container = chart.container;
        const width = container.clientWidth;
        const height = container.clientHeight;

        // Create scene
        chart.scene = new THREE.Scene();
        chart.scene.background = new THREE.Color(this.themes[this.currentTheme].background);

        // Create camera
        chart.camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
        chart.camera.position.set(5, 5, 5);

        // Create renderer
        chart.renderer = new THREE.WebGLRenderer({ antialias: true });
        chart.renderer.setSize(width, height);
        chart.renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(chart.renderer.domElement);

        // Add controls
        const controls = new THREE.OrbitControls(chart.camera, chart.renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        chart.controls = controls;

        // Add lighting
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        chart.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 5);
        chart.scene.add(directionalLight);
    }

    /**
     * Render 3D chart
     */
    render3DChart(chart) {
        const { data, options } = chart;

        // Clear existing objects
        while (chart.scene.children.length > 0) {
            chart.scene.remove(chart.scene.children[0]);
        }

        // Add lighting back
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        chart.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 5);
        chart.scene.add(directionalLight);

        if (options.chartType === '3d_bar') {
            this.render3DBarChart(chart);
        } else if (options.chartType === '3d_surface') {
            this.render3DSurfaceChart(chart);
        } else if (options.chartType === '3d_scatter') {
            this.render3DScatterChart(chart);
        }

        // Start animation loop
        this.animate3DChart(chart);
    }

    /**
     * Render 3D bar chart
     */
    render3DBarChart(chart) {
        const { data, options } = chart;
        const theme = this.themes[this.currentTheme];

        data.forEach((series, seriesIndex) => {
            series.data.forEach((value, index) => {
                const geometry = new THREE.BoxGeometry(0.8, value, 0.8);
                const material = new THREE.MeshLambertMaterial({
                    color: this.getColor(index, theme),
                    transparent: true,
                    opacity: 0.8
                });

                const bar = new THREE.Mesh(geometry, material);
                bar.position.set(index * 1.2, value / 2, seriesIndex * 1.2);
                chart.scene.add(bar);

                // Add value label
                if (options.showLabels) {
                    this.add3DLabel(chart, value.toString(), bar.position.x, bar.position.y + 0.5, bar.position.z);
                }
            });
        });
    }

    /**
     * Render 3D surface chart
     */
    render3DSurfaceChart(chart) {
        const { data, options } = chart;
        const theme = this.themes[this.currentTheme];

        // Create surface geometry
        const geometry = new THREE.PlaneGeometry(10, 10, data.length - 1, data[0].length - 1);
        const material = new THREE.MeshLambertMaterial({
            color: theme.primary,
            wireframe: options.wireframe || false,
            transparent: true,
            opacity: 0.7
        });

        // Apply height data
        const vertices = geometry.attributes.position.array;
        for (let i = 0; i < vertices.length; i += 3) {
            const x = Math.floor((i / 3) % data.length);
            const z = Math.floor((i / 3) / data.length);
            if (data[x] && data[x][z] !== undefined) {
                vertices[i + 1] = data[x][z] * options.heightScale || 1;
            }
        }

        const surface = new THREE.Mesh(geometry, material);
        surface.rotation.x = -Math.PI / 2;
        chart.scene.add(surface);
    }

    /**
     * Render 3D scatter chart
     */
    render3DScatterChart(chart) {
        const { data, options } = chart;
        const theme = this.themes[this.currentTheme];

        data.forEach((point, index) => {
            const geometry = new THREE.SphereGeometry(0.1, 8, 8);
            const material = new THREE.MeshLambertMaterial({
                color: this.getColor(index, theme)
            });

            const sphere = new THREE.Mesh(geometry, material);
            sphere.position.set(point.x, point.y, point.z);
            chart.scene.add(sphere);
        });
    }

    /**
     * Add 3D text label
     */
    add3DLabel(chart, text, x, y, z) {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = 256;
        canvas.height = 64;

        context.fillStyle = this.themes[this.currentTheme].text;
        context.font = '24px Arial';
        context.fillText(text, 10, 40);

        const texture = new THREE.CanvasTexture(canvas);
        const material = new THREE.SpriteMaterial({ map: texture });
        const sprite = new THREE.Sprite(material);
        sprite.position.set(x, y, z);
        sprite.scale.set(2, 0.5, 1);

        chart.scene.add(sprite);
    }

    /**
     * Animate 3D chart
     */
    animate3DChart(chart) {
        const animate = () => {
            requestAnimationFrame(animate);
            
            if (chart.controls) {
                chart.controls.update();
            }
            
            chart.renderer.render(chart.scene, chart.camera);
        };
        
        animate();
    }

    /**
     * Create waterfall chart
     */
    createWaterfallChart(containerId, data, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`[AdvancedCharting] Container not found: ${containerId}`);
            return null;
        }

        const chart = {
            id: containerId,
            type: 'waterfall',
            container: container,
            canvas: null,
            ctx: null,
            data: data,
            options: this.mergeOptions(this.getDefaultWaterfallOptions(), options)
        };

        this.initCanvas(chart);
        this.renderWaterfallChart(chart);
        this.charts.set(containerId, chart);

        return chart;
    }

    /**
     * Render waterfall chart with enhanced features
     */
    renderWaterfallChart(chart) {
        const { data, options } = chart;
        const ctx = chart.ctx;
        const theme = this.themes[this.currentTheme];

        // Apply zoom and pan transformations
        ctx.save();
        const zoomLevel = chart.zoomLevel || 1;
        const panOffset = chart.panOffset || { x: 0, y: 0 };
        
        ctx.scale(zoomLevel, zoomLevel);
        ctx.translate(panOffset.x / zoomLevel, panOffset.y / zoomLevel);

        // Clear canvas
        ctx.clearRect(-panOffset.x / zoomLevel, -panOffset.y / zoomLevel, 
                     chart.canvas.width / zoomLevel, chart.canvas.height / zoomLevel);

        const width = chart.canvas.width / zoomLevel;
        const height = chart.canvas.height / zoomLevel;
        const padding = 60;
        const chartWidth = width - 2 * padding;
        const chartHeight = height - 2 * padding;

        // Calculate scales
        const values = data.map(item => item.value);
        const minValue = Math.min(...values);
        const maxValue = Math.max(...values);
        const range = maxValue - minValue;

        const xScale = chartWidth / (data.length + 1);
        const yScale = chartHeight / range;

        // Draw benchmark lines if available
        const benchmarks = this.benchmarkData.get(chart.id);
        if (benchmarks) {
            this.drawBenchmarkLines(ctx, benchmarks, width, height, padding, yScale, maxValue, theme);
        }

        // Draw bars with enhanced styling
        let runningTotal = 0;
        data.forEach((item, index) => {
            const x = padding + index * xScale;
            const barWidth = xScale * 0.8;
            
            let y, barHeight;
            if (item.type === 'total') {
                y = padding + (maxValue - runningTotal) * yScale;
                barHeight = runningTotal * yScale;
            } else {
                y = padding + (maxValue - runningTotal) * yScale;
                barHeight = Math.abs(item.value) * yScale;
                if (item.value < 0) {
                    y += barHeight;
                }
                runningTotal += item.value;
            }

            // Draw bar with gradient
            const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
            const baseColor = this.getWaterfallColor(item, theme);
            gradient.addColorStop(0, baseColor);
            gradient.addColorStop(1, baseColor + '80');
            
            ctx.fillStyle = gradient;
            ctx.fillRect(x, y, barWidth, barHeight);

            // Draw enhanced border
            ctx.strokeStyle = theme.grid;
            ctx.lineWidth = 2;
            ctx.strokeRect(x, y, barWidth, barHeight);
            
            // Add subtle shadow
            ctx.shadowColor = 'rgba(0,0,0,0.3)';
            ctx.shadowBlur = 4;
            ctx.shadowOffsetX = 2;
            ctx.shadowOffsetY = 2;
            ctx.fillRect(x, y, barWidth, barHeight);
            ctx.shadowColor = 'transparent';

            // Draw label with better formatting
            ctx.fillStyle = theme.text;
            ctx.font = `${Math.max(10, 12 / zoomLevel)}px Arial`;
            ctx.textAlign = 'center';
            
            // Rotate labels if zoomed out to prevent overlap
            if (zoomLevel < 0.8) {
                ctx.save();
                ctx.translate(x + barWidth / 2, height - 20);
                ctx.rotate(-Math.PI / 4);
                ctx.fillText(item.label, 0, 0);
                ctx.restore();
            } else {
                ctx.fillText(item.label, x + barWidth / 2, height - 20);
            }

            // Draw value with financial formatting
            const formattedValue = item.value >= 0 ? 
                `+$${item.value.toLocaleString()}M` : 
                `-$${Math.abs(item.value).toLocaleString()}M`;
            ctx.fillStyle = item.value >= 0 ? theme.success : theme.error;
            ctx.font = `bold ${Math.max(10, 11 / zoomLevel)}px Arial`;
            ctx.fillText(formattedValue, x + barWidth / 2, y - 5);
        });

        // Draw axes with grid lines
        this.drawEnhancedAxes(chart, theme, width, height, padding, data.length);
        
        ctx.restore();
    }
    
    /**
     * Draw benchmark comparison lines
     */
    drawBenchmarkLines(ctx, benchmarks, width, height, padding, yScale, maxValue, theme) {
        benchmarks.forEach((benchmark, index) => {
            const y = padding + (maxValue - benchmark.value) * yScale;
            
            // Draw benchmark line
            ctx.strokeStyle = benchmark.color || theme.accent2;
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(width - padding, y);
            ctx.stroke();
            ctx.setLineDash([]);
            
            // Draw benchmark label
            ctx.fillStyle = benchmark.color || theme.accent2;
            ctx.font = '12px Arial';
            ctx.textAlign = 'left';
            ctx.fillText(`${benchmark.label}: $${benchmark.value.toLocaleString()}M`, 
                        padding + 10, y - 5);
        });
    }
    
    /**
     * Draw enhanced axes with grid lines
     */
    drawEnhancedAxes(chart, theme, width, height, padding, dataLength) {
        const ctx = chart.ctx;
        
        // Draw grid lines
        ctx.strokeStyle = theme.grid + '40';
        ctx.lineWidth = 1;
        
        // Vertical grid lines
        for (let i = 0; i <= dataLength; i++) {
            const x = padding + (i / dataLength) * (width - 2 * padding);
            ctx.beginPath();
            ctx.moveTo(x, padding);
            ctx.lineTo(x, height - padding);
            ctx.stroke();
        }
        
        // Horizontal grid lines
        for (let i = 0; i <= 10; i++) {
            const y = padding + (i / 10) * (height - 2 * padding);
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(width - padding, y);
            ctx.stroke();
        }
        
        // Draw main axes
        ctx.strokeStyle = theme.grid;
        ctx.lineWidth = 2;
        
        // X-axis
        ctx.beginPath();
        ctx.moveTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding);
        ctx.stroke();
        
        // Y-axis
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, height - padding);
        ctx.stroke();
    }

    /**
     * Create tornado diagram
     */
    createTornadoChart(containerId, data, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`[AdvancedCharting] Container not found: ${containerId}`);
            return null;
        }

        const chart = {
            id: containerId,
            type: 'tornado',
            container: container,
            canvas: null,
            ctx: null,
            data: data,
            options: this.mergeOptions(this.getDefaultTornadoOptions(), options)
        };

        this.initCanvas(chart);
        this.renderTornadoChart(chart);
        this.charts.set(containerId, chart);

        return chart;
    }

    /**
     * Render tornado diagram
     */
    renderTornadoChart(chart) {
        const { data, options } = chart;
        const ctx = chart.ctx;
        const theme = this.themes[this.currentTheme];

        // Clear canvas
        ctx.clearRect(0, 0, chart.canvas.width, chart.canvas.height);

        const width = chart.canvas.width;
        const height = chart.canvas.height;
        const padding = 80;
        const chartWidth = width - 2 * padding;
        const chartHeight = height - 2 * padding;

        // Calculate scales
        const maxImpact = Math.max(...data.map(item => Math.abs(item.impact)));
        const xScale = (chartWidth / 2) / maxImpact;
        const yScale = chartHeight / data.length;

        // Draw center line
        const centerX = width / 2;
        ctx.strokeStyle = theme.grid;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(centerX, padding);
        ctx.lineTo(centerX, height - padding);
        ctx.stroke();

        // Draw bars
        data.forEach((item, index) => {
            const y = padding + index * yScale + yScale / 2;
            const barHeight = yScale * 0.6;

            // Left bar (negative impact)
            if (item.impact < 0) {
                const barWidth = Math.abs(item.impact) * xScale;
                ctx.fillStyle = theme.error;
                ctx.fillRect(centerX - barWidth, y - barHeight / 2, barWidth, barHeight);
            }

            // Right bar (positive impact)
            if (item.impact > 0) {
                const barWidth = item.impact * xScale;
                ctx.fillStyle = theme.success;
                ctx.fillRect(centerX, y - barHeight / 2, barWidth, barHeight);
            }

            // Draw label
            ctx.fillStyle = theme.text;
            ctx.font = '12px Arial';
            ctx.textAlign = 'right';
            ctx.fillText(item.label, centerX - 10, y + 4);

            // Draw impact value
            ctx.textAlign = 'left';
            ctx.fillText(item.impact.toFixed(2) + '%', centerX + 10, y + 4);
        });

        // Draw title
        ctx.fillStyle = theme.text;
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(options.title || 'Sensitivity Analysis', width / 2, 30);
    }

    /**
     * Create spider/radar chart
     */
    createSpiderChart(containerId, data, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`[AdvancedCharting] Container not found: ${containerId}`);
            return null;
        }

        const chart = {
            id: containerId,
            type: 'spider',
            container: container,
            canvas: null,
            ctx: null,
            data: data,
            options: this.mergeOptions(this.getDefaultSpiderOptions(), options)
        };

        this.initCanvas(chart);
        this.renderSpiderChart(chart);
        this.charts.set(containerId, chart);

        return chart;
    }

    /**
     * Render spider/radar chart
     */
    renderSpiderChart(chart) {
        const { data, options } = chart;
        const ctx = chart.ctx;
        const theme = this.themes[this.currentTheme];

        // Clear canvas
        ctx.clearRect(0, 0, chart.canvas.width, chart.canvas.height);

        const width = chart.canvas.width;
        const height = chart.canvas.height;
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) / 2 - 60;

        const categories = data.categories;
        const values = data.values;
        const angleStep = (2 * Math.PI) / categories.length;

        // Draw grid circles
        for (let i = 1; i <= 5; i++) {
            const gridRadius = (radius * i) / 5;
            ctx.strokeStyle = theme.grid;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(centerX, centerY, gridRadius, 0, 2 * Math.PI);
            ctx.stroke();
        }

        // Draw category lines
        categories.forEach((category, index) => {
            const angle = index * angleStep - Math.PI / 2;
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);

            // Draw line
            ctx.strokeStyle = theme.grid;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.lineTo(x, y);
            ctx.stroke();

            // Draw label
            ctx.fillStyle = theme.text;
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(category, x, y + 20);
        });

        // Draw data polygon
        ctx.fillStyle = theme.primary + '40';
        ctx.strokeStyle = theme.primary;
        ctx.lineWidth = 2;
        ctx.beginPath();

        values.forEach((value, index) => {
            const angle = index * angleStep - Math.PI / 2;
            const pointRadius = (radius * value) / 100;
            const x = centerX + pointRadius * Math.cos(angle);
            const y = centerY + pointRadius * Math.sin(angle);

            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });

        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Draw data points
        values.forEach((value, index) => {
            const angle = index * angleStep - Math.PI / 2;
            const pointRadius = (radius * value) / 100;
            const x = centerX + pointRadius * Math.cos(angle);
            const y = centerY + pointRadius * Math.sin(angle);

            ctx.fillStyle = theme.primary;
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 2 * Math.PI);
            ctx.fill();
        });
    }

    /**
     * Initialize canvas for 2D charts with accessibility and mobile support
     */
    initCanvas(chart) {
        const canvas = document.createElement('canvas');
        canvas.width = chart.container.clientWidth;
        canvas.height = chart.container.clientHeight;
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        
        // Add accessibility attributes
        canvas.setAttribute('role', 'img');
        canvas.setAttribute('tabindex', '0');
        canvas.setAttribute('aria-label', this.generateChartDescription(chart));
        
        chart.container.innerHTML = '';
        chart.container.appendChild(canvas);

        chart.canvas = canvas;
        chart.ctx = canvas.getContext('2d');
        
        // Add chart controls
        this.addChartControls(chart);
        
        // Add mobile interactions
        this.addMobileInteractions(chart);
        
        // Add keyboard navigation
        this.addKeyboardNavigation(chart);
        
        // Create data table alternative
        this.createDataTable(chart);

        // Handle resize
        const resizeObserver = new ResizeObserver(() => {
            canvas.width = chart.container.clientWidth;
            canvas.height = chart.container.clientHeight;
            this.renderChart(chart);
            this.updateDataTable(chart);
        });
        resizeObserver.observe(chart.container);
    }
    
    /**
     * Generate accessible chart description
     */
    generateChartDescription(chart) {
        const { data, options } = chart;
        let description = `${options.title || 'Financial chart'} showing `;
        
        if (chart.type === 'waterfall') {
            const totalItems = data.length;
            const positiveCount = data.filter(item => item.value > 0).length;
            const negativeCount = data.filter(item => item.value < 0).length;
            description += `${totalItems} data points with ${positiveCount} positive and ${negativeCount} negative values. `;
            description += `Starting value ${data[0]?.value || 0}, ending value ${data[data.length - 1]?.value || 0}.`;
        } else if (chart.type === 'tornado') {
            const maxImpact = Math.max(...data.map(item => Math.abs(item.impact)));
            description += `sensitivity analysis with ${data.length} variables. `;
            description += `Maximum impact is ${maxImpact.toFixed(2)}% from ${data.find(item => Math.abs(item.impact) === maxImpact)?.label}.`;
        } else if (chart.type === 'spider') {
            description += `performance across ${data.categories.length} dimensions. `;
            const avgScore = data.values.reduce((a, b) => a + b, 0) / data.values.length;
            description += `Average performance score is ${avgScore.toFixed(1)}%.`;
        }
        
        return description;
    }
    
    /**
     * Add chart controls for accessibility and functionality
     */
    addChartControls(chart) {
        const controlsDiv = document.createElement('div');
        controlsDiv.className = 'chart-controls';
        controlsDiv.setAttribute('role', 'toolbar');
        controlsDiv.setAttribute('aria-label', 'Chart controls');
        
        // Toggle data table button
        const tableToggle = document.createElement('button');
        tableToggle.className = 'chart-control-btn';
        tableToggle.textContent = 'Show Data Table';
        tableToggle.setAttribute('aria-pressed', 'false');
        tableToggle.addEventListener('click', () => this.toggleDataTable(chart.id));
        
        // Export button
        const exportBtn = document.createElement('button');
        exportBtn.className = 'chart-control-btn';
        exportBtn.textContent = 'Export Chart';
        exportBtn.addEventListener('click', () => this.exportChart(chart.id));
        
        // Zoom controls for applicable charts
        if (['waterfall', 'tornado'].includes(chart.type)) {
            const zoomInBtn = document.createElement('button');
            zoomInBtn.className = 'chart-control-btn';
            zoomInBtn.textContent = 'Zoom In';
            zoomInBtn.setAttribute('aria-label', 'Zoom in on chart');
            zoomInBtn.addEventListener('click', () => this.zoomChart(chart.id, 1.2));
            
            const zoomOutBtn = document.createElement('button');
            zoomOutBtn.className = 'chart-control-btn';
            zoomOutBtn.textContent = 'Zoom Out';
            zoomOutBtn.setAttribute('aria-label', 'Zoom out on chart');
            zoomOutBtn.addEventListener('click', () => this.zoomChart(chart.id, 0.8));
            
            const resetZoomBtn = document.createElement('button');
            resetZoomBtn.className = 'chart-control-btn';
            resetZoomBtn.textContent = 'Reset';
            resetZoomBtn.setAttribute('aria-label', 'Reset zoom level');
            resetZoomBtn.addEventListener('click', () => this.resetZoom(chart.id));
            
            controlsDiv.appendChild(zoomInBtn);
            controlsDiv.appendChild(zoomOutBtn);
            controlsDiv.appendChild(resetZoomBtn);
        }
        
        controlsDiv.appendChild(tableToggle);
        controlsDiv.appendChild(exportBtn);
        
        chart.container.insertBefore(controlsDiv, chart.canvas);
        chart.controls = controlsDiv;
    }
    
    /**
     * Add mobile touch interactions
     */
    addMobileInteractions(chart) {
        const canvas = chart.canvas;
        let touchStartTime = 0;
        let touchStartPos = { x: 0, y: 0 };
        let isPanning = false;
        let lastPanPos = { x: 0, y: 0 };
        
        // Initialize zoom and pan state
        chart.zoomLevel = 1;
        chart.panOffset = { x: 0, y: 0 };
        
        canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            touchStartTime = Date.now();
            
            if (e.touches.length === 1) {
                const rect = canvas.getBoundingClientRect();
                touchStartPos = {
                    x: e.touches[0].clientX - rect.left,
                    y: e.touches[0].clientY - rect.top
                };
                lastPanPos = { ...touchStartPos };
            } else if (e.touches.length === 2) {
                // Pinch zoom start
                const touch1 = e.touches[0];
                const touch2 = e.touches[1];
                chart.initialPinchDistance = Math.sqrt(
                    Math.pow(touch2.clientX - touch1.clientX, 2) +
                    Math.pow(touch2.clientY - touch1.clientY, 2)
                );
                chart.initialZoomLevel = chart.zoomLevel;
            }
        }, { passive: false });
        
        canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            
            if (e.touches.length === 1 && isPanning) {
                const rect = canvas.getBoundingClientRect();
                const currentPos = {
                    x: e.touches[0].clientX - rect.left,
                    y: e.touches[0].clientY - rect.top
                };
                
                chart.panOffset.x += currentPos.x - lastPanPos.x;
                chart.panOffset.y += currentPos.y - lastPanPos.y;
                lastPanPos = currentPos;
                
                this.renderChart(chart);
            } else if (e.touches.length === 2) {
                // Pinch zoom
                const touch1 = e.touches[0];
                const touch2 = e.touches[1];
                const currentDistance = Math.sqrt(
                    Math.pow(touch2.clientX - touch1.clientX, 2) +
                    Math.pow(touch2.clientY - touch1.clientY, 2)
                );
                
                if (chart.initialPinchDistance) {
                    const zoomFactor = currentDistance / chart.initialPinchDistance;
                    chart.zoomLevel = Math.max(0.5, Math.min(3, chart.initialZoomLevel * zoomFactor));
                    this.renderChart(chart);
                }
            }
        }, { passive: false });
        
        canvas.addEventListener('touchend', (e) => {
            const touchDuration = Date.now() - touchStartTime;
            
            if (e.changedTouches.length === 1 && touchDuration < 300 && !isPanning) {
                const rect = canvas.getBoundingClientRect();
                const touchEndPos = {
                    x: e.changedTouches[0].clientX - rect.left,
                    y: e.changedTouches[0].clientY - rect.top
                };
                
                const distance = Math.sqrt(
                    Math.pow(touchEndPos.x - touchStartPos.x, 2) +
                    Math.pow(touchEndPos.y - touchStartPos.y, 2)
                );
                
                // If it's a tap (not a drag), show tooltip
                if (distance < 20) {
                    this.showTooltipAtPosition(chart, touchEndPos.x, touchEndPos.y);
                    
                    // Provide haptic feedback if available
                    if (navigator.vibrate) {
                        navigator.vibrate(50);
                    }
                }
            }
            
            isPanning = false;
            chart.initialPinchDistance = null;
        });
        
        // Enable panning after a short delay to distinguish from taps
        canvas.addEventListener('touchstart', () => {
            setTimeout(() => {
                if (touchStartTime) {
                    isPanning = true;
                }
            }, 200);
        });
    }
    
    /**
     * Add keyboard navigation support
     */
    addKeyboardNavigation(chart) {
        const canvas = chart.canvas;
        
        canvas.addEventListener('keydown', (e) => {
            switch (e.key) {
                case 'ArrowUp':
                    chart.panOffset.y += 10;
                    this.renderChart(chart);
                    e.preventDefault();
                    break;
                case 'ArrowDown':
                    chart.panOffset.y -= 10;
                    this.renderChart(chart);
                    e.preventDefault();
                    break;
                case 'ArrowLeft':
                    chart.panOffset.x += 10;
                    this.renderChart(chart);
                    e.preventDefault();
                    break;
                case 'ArrowRight':
                    chart.panOffset.x -= 10;
                    this.renderChart(chart);
                    e.preventDefault();
                    break;
                case '+':
                case '=':
                    this.zoomChart(chart.id, 1.2);
                    e.preventDefault();
                    break;
                case '-':
                    this.zoomChart(chart.id, 0.8);
                    e.preventDefault();
                    break;
                case '0':
                    this.resetZoom(chart.id);
                    e.preventDefault();
                    break;
                case 'Enter':
                case ' ':
                    this.toggleDataTable(chart.id);
                    e.preventDefault();
                    break;
            }
        });
        
        // Add focus/blur handlers for better UX
        canvas.addEventListener('focus', () => {
            canvas.style.outline = '3px solid #4cc9f0';
        });
        
        canvas.addEventListener('blur', () => {
            canvas.style.outline = 'none';
        });
    }

    /**
     * Draw axes for charts
     */
    drawAxes(chart, theme) {
        const ctx = chart.ctx;
        const width = chart.canvas.width;
        const height = chart.canvas.height;
        const padding = 60;

        // X-axis
        ctx.strokeStyle = theme.grid;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding);
        ctx.stroke();

        // Y-axis
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, height - padding);
        ctx.stroke();
    }

    /**
     * Get color for chart elements
     */
    getColor(index, theme) {
        const colors = [theme.primary, theme.secondary, theme.accent1, theme.accent2, theme.accent3];
        return colors[index % colors.length];
    }

    /**
     * Get waterfall chart color
     */
    getWaterfallColor(item, theme) {
        if (item.type === 'total') {
            return theme.primary;
        } else if (item.value >= 0) {
            return theme.success;
        } else {
            return theme.error;
        }
    }

    /**
     * Merge options with defaults
     */
    mergeOptions(defaults, options) {
        return { ...defaults, ...options };
    }

    /**
     * Get default 3D chart options
     */
    getDefault3DOptions() {
        return {
            chartType: '3d_bar',
            showLabels: true,
            heightScale: 1,
            wireframe: false
        };
    }

    /**
     * Get default waterfall chart options
     */
    getDefaultWaterfallOptions() {
        return {
            title: 'Waterfall Chart',
            showValues: true,
            showLabels: true
        };
    }

    /**
     * Get default tornado chart options
     */
    getDefaultTornadoOptions() {
        return {
            title: 'Tornado Diagram',
            showValues: true,
            showLabels: true
        };
    }

    /**
     * Get default spider chart options
     */
    getDefaultSpiderOptions() {
        return {
            title: 'Spider Chart',
            showValues: true,
            showLabels: true
        };
    }

    /**
     * Set theme
     */
    setTheme(theme) {
        this.currentTheme = theme;
        this.charts.forEach(chart => {
            this.renderChart(chart);
        });
    }

    /**
     * Render chart based on type
     */
    renderChart(chart) {
        switch (chart.type) {
            case 'waterfall':
                this.renderWaterfallChart(chart);
                break;
            case 'tornado':
                this.renderTornadoChart(chart);
                break;
            case 'spider':
                this.renderSpiderChart(chart);
                break;
            case '3d':
                this.render3DChart(chart);
                break;
        }
    }

    /**
     * Export chart as image
     */
    exportChart(chartId, format = 'png') {
        const chart = this.charts.get(chartId);
        if (!chart) {
            console.error(`[AdvancedCharting] Chart not found: ${chartId}`);
            return null;
        }

        if (chart.type === '3d') {
            // For 3D charts, render to canvas first
            chart.renderer.render(chart.scene, chart.camera);
            return chart.renderer.domElement.toDataURL(`image/${format}`);
        } else {
            return chart.canvas.toDataURL(`image/${format}`);
        }
    }

    /**
     * Show tooltip at specific position with financial context
     */
    showTooltipAtPosition(chart, x, y) {
        const dataPoint = this.getDataPointAtPosition(chart, x, y);
        if (dataPoint) {
            this.showFinancialTooltip(dataPoint, x, y, chart);
        }
    }
    
    /**
     * Get data point at canvas position
     */
    getDataPointAtPosition(chart, x, y) {
        // Implementation depends on chart type
        // This is a simplified version - real implementation would be more complex
        const { data } = chart;
        
        if (chart.type === 'waterfall') {
            const barWidth = chart.canvas.width / (data.length + 1) * 0.8;
            const barIndex = Math.floor(x / (chart.canvas.width / (data.length + 1)));
            if (barIndex >= 0 && barIndex < data.length) {
                return {
                    ...data[barIndex],
                    type: 'waterfall',
                    index: barIndex
                };
            }
        }
        
        return null;
    }
    
    /**
     * Show financial context tooltip
     */
    showFinancialTooltip(dataPoint, x, y, chart) {
        if (!this.tooltipContainer) return;
        
        let content = '';
        
        if (dataPoint.type === 'waterfall') {
            const formatValue = (val) => `$${Math.abs(val).toLocaleString()}M`;
            const changeType = dataPoint.value >= 0 ? 'increase' : 'decrease';
            
            content = `
                <div class="tooltip-header">${dataPoint.label}</div>
                <div class="tooltip-value ${dataPoint.value >= 0 ? 'positive' : 'negative'}">
                    ${formatValue(dataPoint.value)}
                </div>
                <div class="tooltip-description">
                    ${changeType.charAt(0).toUpperCase() + changeType.slice(1)} of ${formatValue(dataPoint.value)}
                </div>
                <div class="tooltip-financial-context">
                    ${this.getFinancialContext(dataPoint)}
                </div>
            `;
        }
        
        this.tooltipContainer.innerHTML = content;
        this.tooltipContainer.style.display = 'block';
        this.tooltipContainer.style.left = `${x + 10}px`;
        this.tooltipContainer.style.top = `${y - 10}px`;
        
        // Hide after 3 seconds
        setTimeout(() => {
            if (this.tooltipContainer) {
                this.tooltipContainer.style.display = 'none';
            }
        }, 3000);
    }
    
    /**
     * Get financial context for tooltip
     */
    getFinancialContext(dataPoint) {
        const contexts = {
            'Revenue': 'Top-line growth indicates market expansion and business scaling',
            'EBIT': 'Earnings Before Interest and Tax - core operational profitability',
            'Tax': 'Corporate tax impact on net earnings',
            'FCFF': 'Free Cash Flow to Firm - available for all stakeholders',
            'Terminal Value': 'Long-term value beyond explicit forecast period',
            'Net Debt': 'Financial leverage impact on equity value'
        };
        
        for (const [key, context] of Object.entries(contexts)) {
            if (dataPoint.label.includes(key)) {
                return context;
            }
        }
        
        return 'Financial component contributing to enterprise value';
    }
    
    /**
     * Create accessible data table alternative
     */
    createDataTable(chart) {
        const tableId = `table-${chart.id}`;
        let tableHtml = `
            <div id="${tableId}" class="chart-data-table" style="display:none;" role="table" aria-label="Data table for ${chart.type} chart">
                <div class="table-header">
                    <h3>Chart Data: ${chart.options.title || chart.type.charAt(0).toUpperCase() + chart.type.slice(1)}</h3>
                    <button class="close-table-btn" onclick="this.parentElement.parentElement.style.display='none'">×</button>
                </div>
        `;
        
        if (chart.type === 'waterfall') {
            tableHtml += `
                <table class="financial-table">
                    <thead>
                        <tr role="row">
                            <th role="columnheader" scope="col">Component</th>
                            <th role="columnheader" scope="col">Value ($M)</th>
                            <th role="columnheader" scope="col">Type</th>
                            <th role="columnheader" scope="col">Impact</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            chart.data.forEach((item, index) => {
                const impact = item.value >= 0 ? 'Positive' : 'Negative';
                const impactClass = item.value >= 0 ? 'pos' : 'neg';
                
                tableHtml += `
                    <tr role="row">
                        <td role="cell">${item.label}</td>
                        <td role="cell" class="${impactClass}">${item.value.toLocaleString()}</td>
                        <td role="cell">${item.type || 'Component'}</td>
                        <td role="cell" class="${impactClass}">${impact}</td>
                    </tr>
                `;
            });
            
            tableHtml += '</tbody></table>';
        }
        
        tableHtml += '</div>';
        this.dataTableContainer.insertAdjacentHTML('beforeend', tableHtml);
        chart.dataTableId = tableId;
    }
    
    /**
     * Update data table when chart changes
     */
    updateDataTable(chart) {
        const table = document.getElementById(chart.dataTableId);
        if (table) {
            table.remove();
            this.createDataTable(chart);
        }
    }
    
    /**
     * Toggle data table visibility
     */
    toggleDataTable(chartId) {
        const chart = this.charts.get(chartId);
        if (chart && chart.dataTableId) {
            const table = document.getElementById(chart.dataTableId);
            const toggleBtn = chart.controls.querySelector('button[aria-pressed]');
            
            if (table) {
                const isVisible = table.style.display !== 'none';
                table.style.display = isVisible ? 'none' : 'block';
                
                if (toggleBtn) {
                    toggleBtn.setAttribute('aria-pressed', isVisible ? 'false' : 'true');
                    toggleBtn.textContent = isVisible ? 'Show Data Table' : 'Hide Data Table';
                }
                
                // Announce to screen readers
                const announcement = isVisible ? 'Data table hidden' : 'Data table shown';
                this.announceToScreenReader(announcement);
            }
        }
    }
    
    /**
     * Zoom chart functionality
     */
    zoomChart(chartId, factor) {
        const chart = this.charts.get(chartId);
        if (chart) {
            chart.zoomLevel = Math.max(0.5, Math.min(3, (chart.zoomLevel || 1) * factor));
            this.renderChart(chart);
            
            // Update ARIA label with zoom level
            if (chart.canvas) {
                const zoomPercent = Math.round(chart.zoomLevel * 100);
                chart.canvas.setAttribute('aria-label', 
                    `${this.generateChartDescription(chart)} Zoom level: ${zoomPercent}%`);
            }
        }
    }
    
    /**
     * Reset zoom to default
     */
    resetZoom(chartId) {
        const chart = this.charts.get(chartId);
        if (chart) {
            chart.zoomLevel = 1;
            chart.panOffset = { x: 0, y: 0 };
            this.renderChart(chart);
            
            if (chart.canvas) {
                chart.canvas.setAttribute('aria-label', this.generateChartDescription(chart));
            }
        }
    }
    
    /**
     * Add benchmark data for industry comparisons
     */
    addBenchmarkData(chartId, benchmarks) {
        this.benchmarkData.set(chartId, benchmarks);
        const chart = this.charts.get(chartId);
        if (chart) {
            this.renderChart(chart);
        }
    }
    
    /**
     * Announce messages to screen readers
     */
    announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }
    
    /**
     * Destroy chart with proper cleanup
     */
    destroyChart(chartId) {
        const chart = this.charts.get(chartId);
        if (chart) {
            if (chart.type === '3d') {
                chart.renderer.dispose();
                chart.scene.clear();
            }
            
            // Clean up data table
            if (chart.dataTableId) {
                const table = document.getElementById(chart.dataTableId);
                if (table) table.remove();
            }
            
            chart.container.innerHTML = '';
            this.charts.delete(chartId);
        }
    }
}

// Export for use in other modules
window.AdvancedCharting = AdvancedCharting;

// Initialize global instance
window.advancedCharting = new AdvancedCharting();