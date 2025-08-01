/**
 * Advanced Charting Module - Enhanced Financial Visualizations
 * Provides 3D charts, waterfall charts, tornado diagrams, and advanced visualizations
 */

class AdvancedCharting {
    constructor() {
        this.charts = new Map();
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
     * Render waterfall chart
     */
    renderWaterfallChart(chart) {
        const { data, options } = chart;
        const ctx = chart.ctx;
        const theme = this.themes[this.currentTheme];

        // Clear canvas
        ctx.clearRect(0, 0, chart.canvas.width, chart.canvas.height);

        const width = chart.canvas.width;
        const height = chart.canvas.height;
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

        // Draw bars
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
                barHeight = item.value * yScale;
                runningTotal += item.value;
            }

            // Draw bar
            ctx.fillStyle = this.getWaterfallColor(item, theme);
            ctx.fillRect(x, y, barWidth, barHeight);

            // Draw border
            ctx.strokeStyle = theme.grid;
            ctx.lineWidth = 1;
            ctx.strokeRect(x, y, barWidth, barHeight);

            // Draw label
            ctx.fillStyle = theme.text;
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(item.label, x + barWidth / 2, height - 20);

            // Draw value
            ctx.fillText(item.value.toLocaleString(), x + barWidth / 2, y - 5);
        });

        // Draw axes
        this.drawAxes(chart, theme);
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
     * Initialize canvas for 2D charts
     */
    initCanvas(chart) {
        const canvas = document.createElement('canvas');
        canvas.width = chart.container.clientWidth;
        canvas.height = chart.container.clientHeight;
        canvas.style.width = '100%';
        canvas.style.height = '100%';

        chart.container.innerHTML = '';
        chart.container.appendChild(canvas);

        chart.canvas = canvas;
        chart.ctx = canvas.getContext('2d');

        // Handle resize
        const resizeObserver = new ResizeObserver(() => {
            canvas.width = chart.container.clientWidth;
            canvas.height = chart.container.clientHeight;
            this.renderChart(chart);
        });
        resizeObserver.observe(chart.container);
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
     * Destroy chart
     */
    destroyChart(chartId) {
        const chart = this.charts.get(chartId);
        if (chart) {
            if (chart.type === '3d') {
                chart.renderer.dispose();
                chart.scene.clear();
            }
            chart.container.innerHTML = '';
            this.charts.delete(chartId);
        }
    }
}

// Export for use in other modules
window.AdvancedCharting = AdvancedCharting;