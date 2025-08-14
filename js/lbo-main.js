// Valor IVX - LBO Main Entry Point
// LBO analysis application initialization

import { lboEngine, readLBOInputs, applyLBOInputs, validateLBOInputs, lboPreset, resetLBOForm } from './modules/lbo-engine.js';
import { logLine } from './modules/ui-handlers.js';

// Application state
let isInitialized = false;
let currentResults = null;

// Initialize application
async function initializeApp() {
  if (isInitialized) return;
  
  try {
    // Load preset values
    lboPreset();
    logLine("Loaded LBO preset values");
    
    // Initialize UI event listeners
    initializeUI();
    
    // Set up additional event listeners
    setupEventListeners();
    
    // Run initial analysis
    setTimeout(() => {
      runLBOAnalysis();
    }, 100);
    
    isInitialized = true;
    logLine("LBO application initialized successfully");
    
  } catch (error) {
    console.error("LBO initialization error:", error);
    logLine(`LBO initialization error: ${error.message}`, "err");
  }
}

// Initialize UI event listeners
function initializeUI() {
  // Tab switching
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const tabName = tab.dataset.tab;
      switchTab(tabName);
    });
  });
}

// Switch between tabs
function switchTab(tabName) {
  // Update tab buttons
  document.querySelectorAll('.tab').forEach(tab => {
    tab.classList.remove('active');
  });
  document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
  
  // Update tab content
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.remove('active');
  });
  document.getElementById(tabName).classList.add('active');
}

// Setup additional event listeners
function setupEventListeners() {
  // Preset button
  document.getElementById('lboPreset')?.addEventListener('click', () => {
    lboPreset();
    logLine("Loaded LBO preset values");
    runLBOAnalysis();
  });
  
  // Reset button
  document.getElementById('lboReset')?.addEventListener('click', () => {
    resetLBOForm();
    logLine("Reset LBO form");
    runLBOAnalysis();
  });
  
  // Run LBO button
  document.getElementById('runLBO')?.addEventListener('click', () => {
    runLBOAnalysis();
  });
  
  // Export JSON
  document.getElementById('exportLBOJSON')?.addEventListener('click', () => {
    exportLBOJSON();
  });
  
  // Import JSON
  document.getElementById('importLBOJSON')?.addEventListener('click', () => {
    document.getElementById('importLBOJSONFile')?.click();
  });
  
  document.getElementById('importLBOJSONFile')?.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const data = JSON.parse(event.target.result);
        importLBOJSON(data);
      } catch (error) {
        logLine(`Import error: ${error.message}`, "err");
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  });
  
  // Send to backend
  document.getElementById('sendLBORun')?.addEventListener('click', async () => {
    await sendLBORunToBackend();
  });
  
  // Load from backend
  document.getElementById('loadLastLBORun')?.addEventListener('click', async () => {
    await loadLastLBORunFromBackend();
  });
  
  // Export CSV
  document.getElementById('exportLBOCSV')?.addEventListener('click', () => {
    exportLBOCSV();
  });
  
  // Switch to DCF
  document.getElementById('openDCF')?.addEventListener('click', () => {
    window.location.href = 'index.html';
  });
  
  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    // Enter to run
    if (e.key === 'Enter' && !e.ctrlKey && !e.metaKey) {
      const activeElement = document.activeElement;
      if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
        return; // Don't run if typing in input
      }
      
      e.preventDefault();
      runLBOAnalysis();
    }
  });
  
  // Input change listeners for real-time updates
  const lboInputs = [
    'lboCompanyName', 'lboPurchasePrice', 'lboEquityContribution', 'lboRevenue',
    'lboEbitdaMargin', 'lboRevenueGrowth', 'lboGrowthDecay', 'lboYears',
    'lboTaxRate', 'lboDepreciationRatio', 'lboCapexRatio', 'lboWorkingCapitalRatio',
    'lboSeniorDebtRatio', 'lboMezzanineDebtRatio', 'lboHighYieldDebtRatio',
    'lboSeniorDebtRate', 'lboMezzanineDebtRate', 'lboHighYieldDebtRate'
  ];
  
  lboInputs.forEach(id => {
    const input = document.getElementById(id);
    if (input) {
      input.addEventListener('input', () => {
        // Debounce the analysis
        clearTimeout(window.lboAnalysisTimeout);
        window.lboAnalysisTimeout = setTimeout(() => {
          runLBOAnalysis();
        }, 500);
      });
    }
  });
}

// Run LBO analysis
function runLBOAnalysis() {
  try {
    logLine("Running LBO analysis...");
    
    // Read inputs
    const inputs = readLBOInputs();
    
    // Validate inputs
    const errors = validateLBOInputs(inputs);
    if (errors.length > 0) {
      errors.forEach(error => logLine(`Validation error: ${error}`, "err"));
      return;
    }
    
    // Run LBO engine
    const results = lboEngine(inputs);
    
    if (results.error) {
      logLine(`LBO analysis error: ${results.error}`, "err");
      return;
    }
    
    // Store results
    currentResults = results;
    
    // Update UI
    updateResults(results);
    
    logLine("LBO analysis completed successfully");
    
  } catch (error) {
    console.error("LBO analysis error:", error);
    logLine(`LBO analysis error: ${error.message}`, "err");
  }
}

// Update results in UI
function updateResults(results) {
  const { metrics, exitScenarios } = results;
  
  // Update key metrics
  document.getElementById('leverageRatio').textContent = metrics.leverageRatio.toFixed(2) + 'x';
  document.getElementById('wacd').textContent = (metrics.wacd * 100).toFixed(1) + '%';
  document.getElementById('finalEbitda').textContent = '$' + metrics.finalEbitda.toFixed(0) + 'M';
  document.getElementById('finalDebt').textContent = '$' + metrics.finalDebt.toFixed(0) + 'M';
  document.getElementById('avgIRR').textContent = metrics.avgIRR.toFixed(1) + '%';
  document.getElementById('avgMOIC').textContent = metrics.avgMOIC.toFixed(2) + 'x';
  
  // Update exit scenarios tables
  updateExitScenariosTables(exitScenarios);
  
  // Update charts
  updateCharts(results);
}

// Update exit scenarios tables
function updateExitScenariosTables(exitScenarios) {
  const multipleScenarios = exitScenarios.filter(s => s.type === 'multiple');
  const irrScenarios = exitScenarios.filter(s => s.type === 'irr');
  
  // Update exit multiples table
  const multiplesBody = document.getElementById('exitMultiplesBody');
  if (multiplesBody) {
    multiplesBody.innerHTML = multipleScenarios.map(scenario => `
      <tr>
        <td>${scenario.multiple}x</td>
        <td>$${scenario.exitValue.toFixed(0)}M</td>
        <td>$${scenario.remainingDebt.toFixed(0)}M</td>
        <td>$${scenario.equityValue.toFixed(0)}M</td>
        <td>${scenario.irr.toFixed(1)}%</td>
        <td>${scenario.moic.toFixed(2)}x</td>
      </tr>
    `).join('');
  }
  
  // Update IRR scenarios table
  const irrsBody = document.getElementById('exitIRRsBody');
  if (irrsBody) {
    irrsBody.innerHTML = irrScenarios.map(scenario => `
      <tr>
        <td>${scenario.targetIRR}%</td>
        <td>$${scenario.requiredExitValue.toFixed(0)}M</td>
        <td>${scenario.impliedMultiple.toFixed(1)}x</td>
        <td>$${scenario.equityValue.toFixed(0)}M</td>
      </tr>
    `).join('');
  }
}

// Update charts
function updateCharts(results) {
  const { series } = results;
  const years = results.params.years;
  
  // Cash flow chart
  const cashFlowCanvas = document.getElementById('lboCashFlowChart');
  if (cashFlowCanvas) {
    renderCashFlowChart(cashFlowCanvas, series, years);
  }
  
  // Debt chart
  const debtCanvas = document.getElementById('lboDebtChart');
  if (debtCanvas) {
    renderDebtChart(debtCanvas, series, years);
  }
}

// Render cash flow chart
function renderCashFlowChart(canvas, series, years) {
  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;
  
  // Clear canvas
  ctx.clearRect(0, 0, width, height);
  
  // Set up chart area
  const margin = 40;
  const chartWidth = width - 2 * margin;
  const chartHeight = height - 2 * margin;
  
  // Find data ranges
  const fcffData = series.freeCashFlow.slice(0, years + 1);
  const maxFcff = Math.max(...fcffData);
  const minFcff = Math.min(...fcffData);
  
  // Draw axes
  ctx.strokeStyle = '#3f79a0';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(margin, margin);
  ctx.lineTo(margin, height - margin);
  ctx.lineTo(width - margin, height - margin);
  ctx.stroke();
  
  // Draw grid lines
  ctx.strokeStyle = '#1a2b3d';
  ctx.lineWidth = 0.5;
  for (let i = 0; i <= 5; i++) {
    const y = margin + (chartHeight * i) / 5;
    ctx.beginPath();
    ctx.moveTo(margin, y);
    ctx.lineTo(width - margin, y);
    ctx.stroke();
  }
  
  // Draw FCFF line
  ctx.strokeStyle = '#4cc9f0';
  ctx.lineWidth = 2;
  ctx.beginPath();
  
  for (let i = 0; i <= years; i++) {
    const x = margin + (chartWidth * i) / years;
    const y = height - margin - (chartHeight * (fcffData[i] - minFcff)) / (maxFcff - minFcff);
    
    if (i === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  }
  ctx.stroke();
  
  // Draw data points
  ctx.fillStyle = '#4cc9f0';
  for (let i = 0; i <= years; i++) {
    const x = margin + (chartWidth * i) / years;
    const y = height - margin - (chartHeight * (fcffData[i] - minFcff)) / (maxFcff - minFcff);
    
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, 2 * Math.PI);
    ctx.fill();
  }
  
  // Draw labels
  ctx.fillStyle = '#cfe3f7';
  ctx.font = '12px Inter';
  ctx.textAlign = 'center';
  
  // X-axis labels
  for (let i = 0; i <= years; i++) {
    const x = margin + (chartWidth * i) / years;
    ctx.fillText(`Y${i}`, x, height - margin + 20);
  }
  
  // Y-axis labels
  ctx.textAlign = 'right';
  for (let i = 0; i <= 5; i++) {
    const y = margin + (chartHeight * i) / 5;
    const value = minFcff + (maxFcff - minFcff) * (5 - i) / 5;
    ctx.fillText(`$${value.toFixed(0)}M`, margin - 10, y + 4);
  }
  
  // Title
  ctx.fillStyle = '#d7e6f5';
  ctx.font = '14px Inter';
  ctx.textAlign = 'center';
  ctx.fillText('Free Cash Flow Projection', width / 2, margin - 10);
}

// Render debt chart
function renderDebtChart(canvas, series, years) {
  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;
  
  // Clear canvas
  ctx.clearRect(0, 0, width, height);
  
  // Set up chart area
  const margin = 40;
  const chartWidth = width - 2 * margin;
  const chartHeight = height - 2 * margin;
  
  // Find data ranges
  const debtData = series.debtBalance.slice(0, years + 1);
  const maxDebt = Math.max(...debtData);
  
  // Draw axes
  ctx.strokeStyle = '#3f79a0';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(margin, margin);
  ctx.lineTo(margin, height - margin);
  ctx.lineTo(width - margin, height - margin);
  ctx.stroke();
  
  // Draw grid lines
  ctx.strokeStyle = '#1a2b3d';
  ctx.lineWidth = 0.5;
  for (let i = 0; i <= 5; i++) {
    const y = margin + (chartHeight * i) / 5;
    ctx.beginPath();
    ctx.moveTo(margin, y);
    ctx.lineTo(width - margin, y);
    ctx.stroke();
  }
  
  // Draw debt line
  ctx.strokeStyle = '#ff6b6b';
  ctx.lineWidth = 2;
  ctx.beginPath();
  
  for (let i = 0; i <= years; i++) {
    const x = margin + (chartWidth * i) / years;
    const y = height - margin - (chartHeight * debtData[i]) / maxDebt;
    
    if (i === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  }
  ctx.stroke();
  
  // Draw data points
  ctx.fillStyle = '#ff6b6b';
  for (let i = 0; i <= years; i++) {
    const x = margin + (chartWidth * i) / years;
    const y = height - margin - (chartHeight * debtData[i]) / maxDebt;
    
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, 2 * Math.PI);
    ctx.fill();
  }
  
  // Draw labels
  ctx.fillStyle = '#cfe3f7';
  ctx.font = '12px Inter';
  ctx.textAlign = 'center';
  
  // X-axis labels
  for (let i = 0; i <= years; i++) {
    const x = margin + (chartWidth * i) / years;
    ctx.fillText(`Y${i}`, x, height - margin + 20);
  }
  
  // Y-axis labels
  ctx.textAlign = 'right';
  for (let i = 0; i <= 5; i++) {
    const y = margin + (chartHeight * i) / 5;
    const value = maxDebt * (5 - i) / 5;
    ctx.fillText(`$${value.toFixed(0)}M`, margin - 10, y + 4);
  }
  
  // Title
  ctx.fillStyle = '#d7e6f5';
  ctx.font = '14px Inter';
  ctx.textAlign = 'center';
  ctx.fillText('Debt Paydown', width / 2, margin - 10);
}

// Export LBO data as JSON
function exportLBOJSON() {
  if (!currentResults) {
    logLine("No LBO results to export", "err");
    return;
  }
  
  const exportData = {
    inputs: currentResults.params,
    results: currentResults,
    timestamp: new Date().toISOString()
  };
  
  const dataStr = JSON.stringify(exportData, null, 2);
  const dataBlob = new Blob([dataStr], { type: 'application/json' });
  
  const link = document.createElement('a');
  link.href = URL.createObjectURL(dataBlob);
  link.download = `lbo-analysis-${currentResults.params.companyName}-${new Date().toISOString().split('T')[0]}.json`;
  link.click();
  
  logLine("LBO analysis exported as JSON");
}

// Import LBO data from JSON
function importLBOJSON(data) {
  try {
    if (data.inputs) {
      applyLBOInputs(data.inputs);
      logLine("LBO inputs imported successfully");
      runLBOAnalysis();
    } else {
      logLine("Invalid LBO JSON format", "err");
    }
  } catch (error) {
    logLine(`Import error: ${error.message}`, "err");
  }
}

// Send LBO run to backend
async function sendLBORunToBackend() {
  if (!currentResults) {
    logLine("No LBO results to save", "err");
    return;
  }
  
  try {
    const runData = {
      inputs: currentResults.params,
      results: currentResults,
      timestamp: new Date().toISOString()
    };
    
    const response = await fetch('/api/lbo/runs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(runData)
    });
    
    const result = await response.json();
    
    if (result.success) {
      logLine("LBO run saved to backend");
    } else {
      logLine(`Failed to save LBO run: ${result.error}`, "err");
    }
  } catch (error) {
    logLine(`Backend error: ${error.message}`, "err");
  }
}

// Load last LBO run from backend
async function loadLastLBORunFromBackend() {
  try {
    const response = await fetch('/api/lbo/runs/last');
    const result = await response.json();
    
    if (result.success) {
      applyLBOInputs(result.data.inputs);
      logLine("Last LBO run loaded from backend");
      runLBOAnalysis();
    } else {
      logLine(`Failed to load LBO run: ${result.error}`, "err");
    }
  } catch (error) {
    logLine(`Backend error: ${error.message}`, "err");
  }
}

// Export LBO data as CSV
function exportLBOCSV() {
  if (!currentResults) {
    logLine("No LBO results to export", "err");
    return;
  }
  
  const { series } = currentResults;
  const years = currentResults.params.years;
  
  let csv = 'Year,Revenue,EBITDA,EBIT,Interest Expense,Taxes,Net Income,Free Cash Flow,Debt Balance,Principal Payments\n';
  
  for (let i = 0; i <= years; i++) {
    csv += `${i},`;
    csv += `${series.revenue[i] || 0},`;
    csv += `${series.ebitda[i] || 0},`;
    csv += `${series.ebit[i] || 0},`;
    csv += `${series.interestExpense[i] || 0},`;
    csv += `${series.taxes[i] || 0},`;
    csv += `${series.netIncome[i] || 0},`;
    csv += `${series.freeCashFlow[i] || 0},`;
    csv += `${series.debtBalance[i] || 0},`;
    csv += `${series.principalPayments[i] || 0}\n`;
  }
  
  const dataBlob = new Blob([csv], { type: 'text/csv' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(dataBlob);
  link.download = `lbo-cashflows-${currentResults.params.companyName}-${new Date().toISOString().split('T')[0]}.csv`;
  link.click();
  
  logLine("LBO cash flows exported as CSV");
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}

// Export for global access if needed
window.ValorIVXLBO = {
  run: () => runLBOAnalysis(),
  preset: () => lboPreset(),
  reset: () => resetLBOForm()
}; 