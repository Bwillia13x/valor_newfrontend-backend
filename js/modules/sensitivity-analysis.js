/**
 * Enhanced Sensitivity Analysis Module
 * Provides advanced sensitivity analysis capabilities including:
 * - 2D and 3D sensitivity analysis
 * - Interactive visualizations
 * - Scenario comparison tools
 * - Monte Carlo integration
 * - Real-time parameter adjustment
 */

import { $, fmt, clamp } from './utils.js';

class SensitivityAnalysis {
    constructor() {
        this.results = null;
        this.isCalculating = false;
        this.cancellationToken = null;
        this.charts = {};
    }

    /**
     * Run 2D sensitivity analysis
     */
    async run2DSensitivity(params, dcfEngine) {
        if (this.isCalculating) {
            throw new Error('Analysis already in progress');
        }

        this.isCalculating = true;
        this.cancellationToken = { cancelled: false };

        try {
            const { param1, param2, range1, range2, steps, metric } = params;
            
            // Validate inputs
            this.validateSensitivityInputs(params);

            const results = {
                param1: { name: param1, range: range1, steps: steps },
                param2: { name: param2, range: range2, steps: steps },
                metric: metric,
                data: [],
                minValue: Infinity,
                maxValue: -Infinity,
                timestamp: new Date().toISOString()
            };

            const step1 = (range1.max - range1.min) / (steps - 1);
            const step2 = (range2.max - range2.min) / (steps - 1);

            let progress = 0;
            const totalSteps = steps * steps;

            for (let i = 0; i < steps; i++) {
                if (this.cancellationToken.cancelled) {
                    throw new Error('Analysis cancelled');
                }

                const value1 = range1.min + (i * step1);
                const row = [];

                for (let j = 0; j < steps; j++) {
                    const value2 = range2.min + (j * step2);

                    // Create test parameters
                    const testParams = { ...dcfEngine.getCurrentInputs() };
                    testParams[param1] = value1;
                    testParams[param2] = value2;

                    // Run DCF calculation
                    const dcfResult = dcfEngine.calculateDCF(testParams);
                    const metricValue = this.extractMetric(dcfResult, metric);

                    row.push(metricValue);

                    // Update min/max
                    results.minValue = Math.min(results.minValue, metricValue);
                    results.maxValue = Math.max(results.maxValue, metricValue);

                    progress++;
                    this.updateProgress(progress / totalSteps);
                }

                results.data.push(row);
            }

            this.results = results;
            return results;

        } catch (error) {
            if (this.cancellationToken.cancelled) {
                throw new Error('Analysis cancelled');
            }
            throw error;
        } finally {
            this.isCalculating = false;
            this.cancellationToken = null;
        }
    }

    /**
     * Run 1D sensitivity analysis
     */
    async run1DSensitivity(params, dcfEngine) {
        if (this.isCalculating) {
            throw new Error('Analysis already in progress');
        }

        this.isCalculating = true;
        this.cancellationToken = { cancelled: false };

        try {
            const { parameter, range, steps, metric } = params;
            
            // Validate inputs
            this.validate1DSensitivityInputs(params);

            const results = {
                parameter: { name: parameter, range: range, steps: steps },
                metric: metric,
                data: [],
                baseline: null,
                timestamp: new Date().toISOString()
            };

            const step = (range.max - range.min) / (steps - 1);
            const baselineParams = dcfEngine.getCurrentInputs();
            const baselineResult = dcfEngine.calculateDCF(baselineParams);
            results.baseline = this.extractMetric(baselineResult, metric);

            for (let i = 0; i < steps; i++) {
                if (this.cancellationToken.cancelled) {
                    throw new Error('Analysis cancelled');
                }

                const value = range.min + (i * step);

                // Create test parameters
                const testParams = { ...baselineParams };
                testParams[parameter] = value;

                // Run DCF calculation
                const dcfResult = dcfEngine.calculateDCF(testParams);
                const metricValue = this.extractMetric(dcfResult, metric);

                results.data.push({
                    parameterValue: value,
                    metricValue: metricValue,
                    change: ((metricValue - results.baseline) / results.baseline) * 100
                });

                this.updateProgress((i + 1) / steps);
            }

            this.results = results;
            return results;

        } catch (error) {
            if (this.cancellationToken.cancelled) {
                throw new Error('Analysis cancelled');
            }
            throw error;
        } finally {
            this.isCalculating = false;
            this.cancellationToken = null;
        }
    }

    /**
     * Run scenario comparison analysis
     */
    async runScenarioComparison(scenarios, dcfEngine) {
        if (this.isCalculating) {
            throw new Error('Analysis already in progress');
        }

        this.isCalculating = true;
        this.cancellationToken = { cancelled: false };

        try {
            const results = {
                scenarios: [],
                comparison: {},
                timestamp: new Date().toISOString()
            };

            const metrics = ['enterpriseValue', 'equityValue', 'perShareValue', 'irr'];

            for (let i = 0; i < scenarios.length; i++) {
                if (this.cancellationToken.cancelled) {
                    throw new Error('Analysis cancelled');
                }

                const scenario = scenarios[i];
                const dcfResult = dcfEngine.calculateDCF(scenario.inputs);

                const scenarioResult = {
                    name: scenario.name,
                    inputs: scenario.inputs,
                    results: {}
                };

                // Extract all metrics
                for (const metric of metrics) {
                    scenarioResult.results[metric] = this.extractMetric(dcfResult, metric);
                }

                results.scenarios.push(scenarioResult);
                this.updateProgress((i + 1) / scenarios.length);
            }

            // Calculate comparison metrics
            results.comparison = this.calculateComparisonMetrics(results.scenarios);

            this.results = results;
            return results;

        } catch (error) {
            if (this.cancellationToken.cancelled) {
                throw new Error('Analysis cancelled');
            }
            throw error;
        } finally {
            this.isCalculating = false;
            this.cancellationToken = null;
        }
    }

    /**
     * Validate sensitivity analysis inputs
     */
    validateSensitivityInputs(params) {
        const { param1, param2, range1, range2, steps, metric } = params;

        if (!param1 || !param2) {
            throw new Error('Both parameters must be specified');
        }

        if (!range1 || !range2) {
            throw new Error('Both parameter ranges must be specified');
        }

        if (range1.min >= range1.max || range2.min >= range2.max) {
            throw new Error('Range min must be less than max');
        }

        if (steps < 2 || steps > 100) {
            throw new Error('Steps must be between 2 and 100');
        }

        if (!metric) {
            throw new Error('Metric must be specified');
        }

        return true;
    }

    /**
     * Validate 1D sensitivity inputs
     */
    validate1DSensitivityInputs(params) {
        const { parameter, range, steps, metric } = params;

        if (!parameter) {
            throw new Error('Parameter must be specified');
        }

        if (!range || range.min >= range.max) {
            throw new Error('Valid range must be specified');
        }

        if (steps < 2 || steps > 100) {
            throw new Error('Steps must be between 2 and 100');
        }

        if (!metric) {
            throw new Error('Metric must be specified');
        }

        return true;
    }

    /**
     * Extract metric value from DCF results
     */
    extractMetric(dcfResult, metric) {
        switch (metric) {
            case 'enterpriseValue':
                return dcfResult.enterpriseValue;
            case 'equityValue':
                return dcfResult.equityValue;
            case 'perShareValue':
                return dcfResult.perShareValue;
            case 'irr':
                return dcfResult.irr || 0;
            case 'npv':
                return dcfResult.npv || 0;
            case 'paybackPeriod':
                return dcfResult.paybackPeriod || 0;
            default:
                throw new Error(`Unknown metric: ${metric}`);
        }
    }

    /**
     * Calculate comparison metrics between scenarios
     */
    calculateComparisonMetrics(scenarios) {
        if (scenarios.length < 2) {
            return {};
        }

        const comparison = {
            bestScenario: null,
            worstScenario: null,
            ranges: {},
            averages: {}
        };

        const metrics = Object.keys(scenarios[0].results);

        for (const metric of metrics) {
            const values = scenarios.map(s => s.results[metric]);
            const min = Math.min(...values);
            const max = Math.max(...values);
            const avg = values.reduce((a, b) => a + b, 0) / values.length;

            comparison.ranges[metric] = { min, max, range: max - min };
            comparison.averages[metric] = avg;

            // Find best and worst scenarios for each metric
            const bestIdx = values.indexOf(max);
            const worstIdx = values.indexOf(min);

            if (!comparison.bestScenario || max > comparison.bestScenario.value) {
                comparison.bestScenario = {
                    name: scenarios[bestIdx].name,
                    metric: metric,
                    value: max
                };
            }

            if (!comparison.worstScenario || min < comparison.worstScenario.value) {
                comparison.worstScenario = {
                    name: scenarios[worstIdx].name,
                    metric: metric,
                    value: min
                };
            }
        }

        return comparison;
    }

    /**
     * Update progress indicator
     */
    updateProgress(progress) {
        const progressBar = $('#sensitivity-progress-fill');
        if (progressBar) {
            progressBar.style.width = `${progress * 100}%`;
        }
    }

    /**
     * Cancel ongoing analysis
     */
    cancelAnalysis() {
        if (this.cancellationToken) {
            this.cancellationToken.cancelled = true;
        }
    }

    /**
     * Get analysis results
     */
    getResults() {
        return this.results;
    }

    /**
     * Export results to JSON
     */
    exportResults() {
        if (!this.results) {
            throw new Error('No analysis results to export');
        }
        return JSON.stringify(this.results, null, 2);
    }

    /**
     * Render 2D sensitivity heatmap
     */
    render2DHeatmap(canvasId, results) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !results) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        const data = results.data;
        const rows = data.length;
        const cols = data[0].length;

        const cellWidth = width / cols;
        const cellHeight = height / rows;

        // Color scale
        const colorScale = this.createColorScale(results.minValue, results.maxValue);

        // Draw heatmap
        for (let i = 0; i < rows; i++) {
            for (let j = 0; j < cols; j++) {
                const value = data[i][j];
                const color = colorScale(value);

                ctx.fillStyle = color;
                ctx.fillRect(j * cellWidth, i * cellHeight, cellWidth, cellHeight);
            }
        }

        // Draw axes labels
        this.drawHeatmapLabels(ctx, width, height, results);
    }

    /**
     * Render 1D sensitivity chart
     */
    render1DChart(canvasId, results) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !results) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        const data = results.data;
        const values = data.map(d => d.metricValue);
        const changes = data.map(d => d.change);

        const minValue = Math.min(...values);
        const maxValue = Math.max(...values);
        const minChange = Math.min(...changes);
        const maxChange = Math.max(...changes);

        // Draw grid
        this.drawGrid(ctx, width, height);

        // Draw baseline
        ctx.strokeStyle = '#666';
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(0, height - (results.baseline - minValue) / (maxValue - minValue) * height);
        ctx.lineTo(width, height - (results.baseline - minValue) / (maxValue - minValue) * height);
        ctx.stroke();
        ctx.setLineDash([]);

        // Draw data line
        ctx.strokeStyle = '#007bff';
        ctx.lineWidth = 2;
        ctx.beginPath();

        for (let i = 0; i < data.length; i++) {
            const x = (i / (data.length - 1)) * width;
            const y = height - (values[i] - minValue) / (maxValue - minValue) * height;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }

        ctx.stroke();

        // Draw labels
        this.draw1DChartLabels(ctx, width, height, results);
    }

    /**
     * Create color scale for heatmap
     */
    createColorScale(min, max) {
        return (value) => {
            const normalized = (value - min) / (max - min);
            const hue = (1 - normalized) * 240; // Blue to Red
            return `hsl(${hue}, 70%, 50%)`;
        };
    }

    /**
     * Draw heatmap labels
     */
    drawHeatmapLabels(ctx, width, height, results) {
        ctx.fillStyle = '#fff';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';

        // X-axis labels
        const xStep = width / (results.param2.steps - 1);
        for (let i = 0; i < results.param2.steps; i++) {
            const value = results.param2.range.min + (i * (results.param2.range.max - results.param2.range.min) / (results.param2.steps - 1));
            ctx.fillText(fmt(value, 'number'), i * xStep, height - 5);
        }

        // Y-axis labels
        ctx.save();
        ctx.translate(5, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText(results.param1.name, 0, 0);
        ctx.restore();
    }

    /**
     * Draw grid for charts
     */
    drawGrid(ctx, width, height) {
        ctx.strokeStyle = '#ddd';
        ctx.lineWidth = 1;

        // Vertical lines
        for (let i = 0; i <= 10; i++) {
            const x = (i / 10) * width;
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, height);
            ctx.stroke();
        }

        // Horizontal lines
        for (let i = 0; i <= 10; i++) {
            const y = (i / 10) * height;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }
    }

    /**
     * Draw 1D chart labels
     */
    draw1DChartLabels(ctx, width, height, results) {
        ctx.fillStyle = '#fff';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';

        // X-axis label
        ctx.fillText(results.parameter.name, width / 2, height - 5);

        // Y-axis label
        ctx.save();
        ctx.translate(5, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText(results.metric, 0, 0);
        ctx.restore();
    }

    /**
     * Update UI with results
     */
    updateUI() {
        if (!this.results) return;

        // Show results section
        $('#sensitivity-results-section').style.display = 'block';

        if (this.results.data && this.results.data.length > 0) {
            if (Array.isArray(this.results.data[0])) {
                // 2D sensitivity results
                this.update2DResults();
            } else {
                // 1D sensitivity results
                this.update1DResults();
            }
        } else if (this.results.scenarios) {
            // Scenario comparison results
            this.updateScenarioResults();
        }
    }

    /**
     * Update 2D sensitivity results
     */
    update2DResults() {
        const { param1, param2, metric, minValue, maxValue } = this.results;

        $('#sensitivity-param1').text(param1.name);
        $('#sensitivity-param2').text(param2.name);
        $('#sensitivity-metric').text(metric);
        $('#sensitivity-min-value').text(fmt(minValue, 'currency'));
        $('#sensitivity-max-value').text(fmt(maxValue, 'currency'));

        // Render heatmap
        this.render2DHeatmap('sensitivity-heatmap', this.results);
    }

    /**
     * Update 1D sensitivity results
     */
    update1DResults() {
        const { parameter, metric, baseline, data } = this.results;

        $('#sensitivity-parameter').text(parameter.name);
        $('#sensitivity-metric').text(metric);
        $('#sensitivity-baseline').text(fmt(baseline, 'currency'));

        const maxChange = Math.max(...data.map(d => Math.abs(d.change)));
        $('#sensitivity-max-change').text(fmt(maxChange, 'percent'));

        // Render chart
        this.render1DChart('sensitivity-chart', this.results);
    }

    /**
     * Update scenario comparison results
     */
    updateScenarioResults() {
        const { scenarios, comparison } = this.results;

        $('#sensitivity-scenario-count').text(scenarios.length);
        
        if (comparison.bestScenario) {
            $('#sensitivity-best-scenario').text(comparison.bestScenario.name);
            $('#sensitivity-best-value').text(fmt(comparison.bestScenario.value, 'currency'));
        }

        if (comparison.worstScenario) {
            $('#sensitivity-worst-scenario').text(comparison.worstScenario.name);
            $('#sensitivity-worst-value').text(fmt(comparison.worstScenario.value, 'currency'));
        }

        // Render comparison chart
        this.renderScenarioComparison('sensitivity-comparison-chart', this.results);
    }

    /**
     * Render scenario comparison chart
     */
    renderScenarioComparison(canvasId, results) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !results) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        const { scenarios } = results;
        const metrics = Object.keys(scenarios[0].results);

        // Draw bar chart for each scenario
        const barWidth = width / (scenarios.length + 1);
        const colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1'];

        for (let i = 0; i < scenarios.length; i++) {
            const scenario = scenarios[i];
            const x = (i + 1) * barWidth;
            const value = scenario.results.enterpriseValue;
            const barHeight = (value / Math.max(...scenarios.map(s => s.results.enterpriseValue))) * height * 0.8;

            ctx.fillStyle = colors[i % colors.length];
            ctx.fillRect(x, height - barHeight, barWidth * 0.8, barHeight);

            // Draw label
            ctx.fillStyle = '#fff';
            ctx.font = '10px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(scenario.name, x + barWidth * 0.4, height - 5);
        }
    }
}

// Export the sensitivity analysis engine
export const sensitivityAnalysis = new SensitivityAnalysis();