// Valor IVX - UI Handlers Module
// User interface interactions and event management

import { fmt } from './utils.js';
import { dcfEngine, validateInputs, computeKPIs, readInputs, preset, resetForm } from './dcf-engine.js';
import { runMonteCarlo, renderHistogram, validateMCInputs, getMCSettings } from './monte-carlo.js';
import { renderFcfChart, renderHeatmap, renderRampPreview, renderWaterfall, renderSensitivity1D } from './charting.js';
import { saveCurrentScenario, applyScenario, deleteScenario, exportScenarios, importScenarios, exportRunData, importRunData, resetAllData, loadNotes, saveNotes } from './scenarios.js';
import { sendRunToBackend, loadLastRunFromBackend, sendScenariosToBackend, fetchScenariosFromBackend } from './backend.js';

// Global state
let currentResult = null;
let mcCancelSignal = { requested: false };
let overlaySeries = null;

let __toastRegion;
let __lastFocused;

function ensureToastRegion() {
  if (!__toastRegion) {
    __toastRegion = document.getElementById("aria-live-toasts");
    if (!__toastRegion) {
      __toastRegion = document.createElement("div");
      __toastRegion.id = "aria-live-toasts";
      __toastRegion.setAttribute("role", "region");
      __toastRegion.setAttribute("aria-live", "polite");
      __toastRegion.setAttribute("aria-atomic", "true");
      __toastRegion.style.position = "fixed";
      __toastRegion.style.top = "20px";
      __toastRegion.style.right = "20px";
      __toastRegion.style.zIndex = "1002";
      document.body.appendChild(__toastRegion);
    }
  }
  return __toastRegion;
}

export function showToast(message, type = "info", timeoutMs = 3000) {
  const region = ensureToastRegion();
  const toast = document.createElement("div");
  toast.className = `pwa-notification`;
  toast.setAttribute("role", "status");
  toast.setAttribute("aria-live", "polite");
  toast.innerHTML = `
    <div class="pwa-notification-content">
      <strong>${type.toUpperCase()}</strong>
      <span>${message}</span>
      <div class="row" style="gap:6px;margin-top:6px;justify-content:flex-end">
        <button class="btn" data-toast-dismiss>Dismiss</button>
      </div>
    </div>
  `;
  region.appendChild(toast);

  const dismiss = () => toast.remove();
  toast.querySelector('[data-toast-dismiss]')?.addEventListener("click", dismiss);
  if (timeoutMs > 0) setTimeout(dismiss, timeoutMs);
}

// Logging utilities
export function logLine(msg, cls = "") {
  const terminal = document.getElementById("terminal");
  if (terminal) {
    const line = document.createElement("div");
    line.className = `term-line ${cls}`;
    line.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
  }
  // Mirror to toasts for errors/warnings to improve visibility
  if (cls?.includes("err")) showToast(msg, "error", 4000);
  else if (cls?.includes("warn")) showToast(msg, "warning", 3500);
}

// Update KPI display
export function updateKPIUI(kpis) {
  const pct = (x) => (isFinite(x) ? (x * 100).toFixed(1) + "%" : "—");
  const num = (x, d = 2) => (isFinite(x) ? x.toFixed(d) : "—");
  
  document.getElementById("kpiROIC")?.textContent = pct(kpis.roic);
  document.getElementById("kpiReinv")?.textContent = pct(kpis.reinvestRate);
  document.getElementById("kpiFcfCAGR")?.textContent = pct(kpis.fcffCAGR);
  document.getElementById("kpiPayback")?.textContent = num(kpis.payback, 1);
  document.getElementById("kpiEVNOPAT")?.textContent = num(kpis.evNopat, 1);
}

// Update main output display
export function updateOutputs(result) {
  document.getElementById("evVal")?.textContent = fmt(result.totals.ev, { currency: true, suffix: "M" });
  document.getElementById("eqVal")?.textContent = fmt(result.totals.equity, { currency: true, suffix: "M" });
  document.getElementById("psVal")?.textContent = fmt(result.totals.perShare, { currency: true });
  document.getElementById("tvPct")?.textContent = fmt(result.totals.tvPct * 100, { decimals: 1, suffix: "%" });
}

// Update status pill
export function updateStatusPill(text, className = "") {
  const pill = document.getElementById("statusPill");
  if (pill) {
    pill.textContent = text;
    pill.className = `pill ${className}`;
  }
}

// Main run function
export async function run() {
  try {
    updateStatusPill("Running...", "running");
    
    const inputs = readInputs();
    const validation = validateInputs(inputs);
    
    if (validation.errors.length > 0) {
      updateStatusPill("Validation Errors", "error");
      validation.errors.forEach(error => {
        logLine(`❌ ${error.message}`, "err");
        if (error.explanation) {
          logLine(`   💡 ${error.explanation}`, "err-detail");
        }
        if (error.suggestion) {
          logLine(`   📝 ${error.suggestion}`, "err-suggestion");
        }
      });
      return;
    }
    
    if (validation.warnings.length > 0) {
      validation.warnings.forEach(warning => {
        logLine(`⚠️  ${warning}`, "warn");
      });
    }
    
    // Get terminal value method
    const tvMethod = document.getElementById("tvMultiple")?.checked ? "multiple" : "perpetuity";
    const tvMultipleVal = Number(document.getElementById("tvMultipleVal")?.value || 12);
    
    const result = dcfEngine({ ...inputs, tvMethod, tvMultipleVal });
    currentResult = result;
    
    // Update outputs
    updateOutputs(result);
    
    // Update KPIs
    const kpis = computeKPIs(result);
    updateKPIUI(kpis);
    
    // Render charts
    const fcfChart = document.getElementById("fcfChart");
    const heatmap = document.getElementById("heatmap");
    const rampPreview = document.getElementById("rampPreview");
    
    if (fcfChart) {
      renderFcfChart(fcfChart, result.series, "fcf", document.getElementById("chartTooltip"), overlaySeries);
    }
    
    if (heatmap) {
      renderHeatmap(heatmap, inputs, inputs);
    }
    
    if (rampPreview) {
      renderRampPreview(rampPreview, inputs);
    }
    
    // Log warnings
    if (result.warnings.length > 0) {
      result.warnings.forEach(warning => logLine(warning, "warn"));
    }
    
    logLine(`Analysis complete: EV $${fmt(result.totals.ev)}M, Per Share $${fmt(result.totals.perShare)}`);
    updateStatusPill("Complete", "success");
    
  } catch (err) {
    logLine(`Error: ${err.message}`, "err");
    updateStatusPill("Error", "error");
  }
}

// Monte Carlo run handler
export async function runMonteCarloHandler() {
  try {
    const inputs = readInputs();
    const mcSettings = getMCSettings();
    
    const errors = validateMCInputs(
      mcSettings.trials,
      mcSettings.volPP,
      mcSettings.marginVolPP,
      mcSettings.s2cVolPct,
      mcSettings.corrGM
    );
    
    if (errors.length > 0) {
      errors.forEach(error => logLine(error, "err"));
      return;
    }
    
    mcCancelSignal.requested = false;
    const runButton = document.getElementById("runMC");
    const cancelButton = document.getElementById("cancelMC");
    const summary = document.getElementById("mcSummary");
    
    if (runButton) runButton.style.display = "none";
    if (cancelButton) cancelButton.style.display = "inline";
    if (summary) summary.textContent = "Running...";
    
    updateStatusPill("Monte Carlo Running...", "running");
    
    const onProgress = (done, total, elapsed) => {
      if (summary) {
        const eta = done > 0 ? (elapsed / done) * (total - done) : 0;
        summary.textContent = `${done}/${total} (${elapsed.toFixed(0)}ms${eta > 0 ? `, ETA ${eta.toFixed(0)}ms` : ""})`;
      }
    };
    
    const mcResult = await runMonteCarlo(
      inputs,
      mcSettings.trials,
      mcSettings.volPP,
      mcSettings.seedStr,
      mcCancelSignal,
      {
        marginVolPP: mcSettings.marginVolPP,
        s2cVolPct: mcSettings.s2cVolPct,
        corrGM: mcSettings.corrGM,
        onProgress
      }
    );
    
    if (mcCancelSignal.requested) {
      logLine("Monte Carlo canceled", "warn");
      updateStatusPill("MC Canceled", "warning");
    } else {
      // Render histogram
      const histCanvas = document.getElementById("mcHist");
      const showAnnotations = document.getElementById("toggleHistAnn")?.checked !== false;
      
      if (histCanvas) {
        renderHistogram(histCanvas, mcResult.results, showAnnotations);
      }
      
      // Update summary
      if (summary) {
        summary.textContent = `μ: $${fmt(mcResult.stats.mean)} | med: $${fmt(mcResult.stats.median)} | p10: $${fmt(mcResult.stats.p10)} | p90: $${fmt(mcResult.stats.p90)}`;
      }
      
      logLine(`Monte Carlo complete: ${mcResult.stats.n} trials, μ $${fmt(mcResult.stats.mean)}`);
      updateStatusPill("MC Complete", "success");
    }
    
  } catch (err) {
    logLine(`Monte Carlo error: ${err.message}`, "err");
    updateStatusPill("MC Error", "error");
  } finally {
    const runButton = document.getElementById("runMC");
    const cancelButton = document.getElementById("cancelMC");
    
    if (runButton) runButton.style.display = "inline";
    if (cancelButton) cancelButton.style.display = "none";
  }
}

// Cancel Monte Carlo
export function cancelMonteCarlo() {
  mcCancelSignal.requested = true;
}

// Tab switching
export function switchTab(tabName, tabList) {
  // Update tab buttons
  tabList.forEach(tab => {
    const button = document.querySelector(`[data-tab="${tab}"]`);
    if (button) {
      button.classList.toggle("active", tab === tabName);
      button.setAttribute("aria-selected", tab === tabName ? "true" : "false");
    }
  });
  
  // Update chart content
  if (currentResult) {
    const fcfChart = document.getElementById("fcfChart");
    const chartTooltip = document.getElementById("chartTooltip");
    
    if (fcfChart) {
      renderFcfChart(fcfChart, currentResult.series, tabName, chartTooltip, overlaySeries);
    }
  }
  
  // Update titles and summaries
  const titles = {
    fcf: "Projected FCFF",
    rev: "Projected Revenue",
    margin: "EBIT Margins",
    pv: "PV Contributions",
    waterfall: "EV Waterfall"
  };
  
  const seriesTitle = document.getElementById("seriesTitle");
  if (seriesTitle && titles[tabName]) {
    seriesTitle.textContent = titles[tabName];
  }
}

// Solver functionality
export function openSolver() {
  const modal = document.getElementById("solverModal");
  if (modal) {
    __lastFocused = document.activeElement;
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.style.display = "flex";
    // Focus first focusable element
    const first = modal.querySelector("input, select, textarea, button, [tabindex]:not([tabindex='-1'])");
    (first || modal).focus();

    // Simple focus trap
    const focusable = () =>
      Array.from(modal.querySelectorAll("input, select, textarea, button, [tabindex]:not([tabindex='-1'])"))
        .filter(el => !el.hasAttribute("disabled"));
    const onKey = (e) => {
      if (e.key === "Tab") {
        const nodes = focusable();
        if (!nodes.length) return;
        const idx = nodes.indexOf(document.activeElement);
        if (e.shiftKey) {
          if (idx <= 0) {
            nodes[nodes.length - 1].focus();
            e.preventDefault();
          }
        } else {
          if (idx === nodes.length - 1) {
            nodes[0].focus();
            e.preventDefault();
          }
        }
      } else if (e.key === "Escape") {
        closeSolver();
      }
    };
    modal.__trapHandler = onKey;
    document.addEventListener("keydown", onKey);
  }
}

export function closeSolver() {
  const modal = document.getElementById("solverModal");
  if (modal) {
    modal.style.display = "none";
    if (modal.__trapHandler) {
      document.removeEventListener("keydown", modal.__trapHandler);
      delete modal.__trapHandler;
    }
    // Return focus to previously focused trigger if still in DOM
    if (__lastFocused && document.contains(__lastFocused)) {
      __lastFocused.focus();
    }
  }
}

// CLI functionality
export function cliPrint(msg, cls = "") {
  const output = document.getElementById("cliOutput");
  if (!output) return;
  
  const line = document.createElement("div");
  line.className = `cli-line ${cls}`;
  line.textContent = msg;
  output.appendChild(line);
  output.scrollTop = output.scrollHeight;
}

export function cliHelp() {
  cliPrint("Available commands:");
  cliPrint("  run                    - Run DCF analysis");
  cliPrint("  set <param> <value>    - Set parameter (e.g., set wacc 8.5)");
  cliPrint("  eval <metric>          - Evaluate metric (e.g., eval ps, eval ev)");
  cliPrint("  mc <trials> <vol>      - Run Monte Carlo (e.g., mc 1000 2.0)");
  cliPrint("  grid <param> <min> <max> <steps> - 1D sensitivity");
  cliPrint("  clear                  - Clear output");
  cliPrint("  help                   - Show this help");
}

export function setInput(key, value) {
  const el = document.getElementById(key);
  if (el) {
    el.value = value;
    el.dispatchEvent(new Event("input"));
  } else {
    cliPrint(`Unknown parameter: ${key}`, "err");
  }
}

export function getInputValue(key) {
  const el = document.getElementById(key);
  return el ? el.value : null;
}

export function handleCli(line) {
  const parts = line.trim().split(/\s+/);
  const cmd = parts[0]?.toLowerCase();
  
  switch (cmd) {
    case "run":
      run();
      break;
      
    case "set":
      if (parts.length >= 3) {
        const param = parts[1];
        const value = parts[2];
        setInput(param, value);
        cliPrint(`Set ${param} = ${value}`);
      } else {
        cliPrint("Usage: set <param> <value>", "err");
      }
      break;
      
    case "eval":
      if (parts.length >= 2) {
        const metric = parts[1].toLowerCase();
        if (currentResult) {
          const values = {
            ps: currentResult.totals.perShare,
            ev: currentResult.totals.ev,
            equity: currentResult.totals.equity,
            tv: currentResult.totals.pvTv
          };
          const value = values[metric];
          if (value !== undefined) {
            cliPrint(`${metric.toUpperCase()}: $${fmt(value)}`);
          } else {
            cliPrint(`Unknown metric: ${metric}`, "err");
          }
        } else {
          cliPrint("No analysis results available. Run 'run' first.", "err");
        }
      } else {
        cliPrint("Usage: eval <metric>", "err");
      }
      break;
      
    case "mc":
      if (parts.length >= 3) {
        const trials = parseInt(parts[1]);
        const vol = parseFloat(parts[2]);
        if (!isNaN(trials) && !isNaN(vol)) {
          setInput("mcTrials", trials);
          setInput("mcVol", vol);
          runMonteCarloHandler();
        } else {
          cliPrint("Invalid trials or volatility", "err");
        }
      } else {
        cliPrint("Usage: mc <trials> <vol>", "err");
      }
      break;
      
    case "clear":
      const output = document.getElementById("cliOutput");
      if (output) output.innerHTML = "";
      break;
      
    case "help":
      cliHelp();
      break;
      
    default:
      cliPrint(`Unknown command: ${cmd}. Type 'help' for available commands.`, "err");
  }
}

// Mobile financial input enhancements
function initializeMobileOptimizations() {
  // Add quick value buttons for common financial inputs
  const financialInputs = [
    { id: 'wacc', values: [7, 8, 9, 10, 11, 12], suffix: '%' },
    { id: 'termGrowth', values: [1.5, 2.0, 2.5, 3.0], suffix: '%' },
    { id: 'ebitMargin', values: [15, 20, 25, 30], suffix: '%' },
    { id: 'salesToCap', values: [1.5, 2.0, 2.5, 3.0, 3.5], suffix: '' }
  ];
  
  financialInputs.forEach(input => {
    const inputElement = document.getElementById(input.id);
    if (inputElement && inputElement.parentNode) {
      const quickValuesDiv = document.createElement('div');
      quickValuesDiv.className = 'quick-values';
      
      input.values.forEach(value => {
        const btn = document.createElement('button');
        btn.className = 'quick-value-btn';
        btn.textContent = `${value}${input.suffix}`;
        btn.type = 'button';
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          inputElement.value = value;
          inputElement.dispatchEvent(new Event('input', { bubbles: true }));
          // Provide haptic feedback on mobile
          if (navigator.vibrate) {
            navigator.vibrate(10);
          }
        });
        quickValuesDiv.appendChild(btn);
      });
      
      inputElement.parentNode.appendChild(quickValuesDiv);
    }
  });
  
  // Enhanced mobile chart interactions
  const charts = document.querySelectorAll('canvas');
  charts.forEach(canvas => {
    let touchStartTime = 0;
    let touchStartPos = { x: 0, y: 0 };
    
    canvas.addEventListener('touchstart', (e) => {
      touchStartTime = Date.now();
      if (e.touches.length === 1) {
        touchStartPos = {
          x: e.touches[0].clientX,
          y: e.touches[0].clientY
        };
      }
    }, { passive: true });
    
    canvas.addEventListener('touchend', (e) => {
      const touchEndTime = Date.now();
      const touchDuration = touchEndTime - touchStartTime;
      
      // Detect tap vs swipe
      if (touchDuration < 300 && e.changedTouches.length === 1) {
        const touchEndPos = {
          x: e.changedTouches[0].clientX,
          y: e.changedTouches[0].clientY
        };
        
        const distance = Math.sqrt(
          Math.pow(touchEndPos.x - touchStartPos.x, 2) +
          Math.pow(touchEndPos.y - touchStartPos.y, 2)
        );
        
        // If it's a tap (not a swipe), show tooltip
        if (distance < 20) {
          // Trigger chart tooltip/interaction
          canvas.dispatchEvent(new MouseEvent('click', {
            clientX: touchEndPos.x,
            clientY: touchEndPos.y
          }));
        }
      }
    }, { passive: true });
  });
  
  // Enhanced real-time validation with financial context
  const numberInputs = document.querySelectorAll('input[type="number"]');
  numberInputs.forEach(input => {
    // Real-time validation on input
    input.addEventListener('input', (e) => {
      const value = parseFloat(e.target.value);
      
      // Auto-format number inputs
      if (!isNaN(value) && e.target.step) {
        const step = parseFloat(e.target.step);
        const decimals = step >= 1 ? 0 : step.toString().split('.')[1]?.length || 0;
        
        // Format with appropriate decimal places
        if (e.target.value !== '' && !e.target.value.endsWith('.')) {
          const formatted = value.toFixed(decimals);
          if (parseFloat(formatted) === value) {
            e.target.value = formatted;
          }
        }
      }
      
      // Real-time contextual validation
      validateInputRealTime(e.target);
    });
    
    // Enhanced blur validation
    input.addEventListener('blur', (e) => {
      validateInputRealTime(e.target, true);
    });
    
    // Show financial context on focus
    input.addEventListener('focus', (e) => {
      showFinancialInputContext(e.target);
    });
  });
  
  // Add live validation for key financial relationships
  const waccInput = document.getElementById('wacc');
  const termGrowthInput = document.getElementById('termGrowth');
  
  if (waccInput && termGrowthInput) {
    [waccInput, termGrowthInput].forEach(input => {
      input.addEventListener('input', () => {
        validateWaccTermGrowthRelationship();
      });
    });
  }
}

// Real-time input validation with financial context
function validateInputRealTime(input, isBlur = false) {
  const value = parseFloat(input.value);
  const id = input.id;
  const min = parseFloat(input.min) || -Infinity;
  const max = parseFloat(input.max) || Infinity;
  
  // Clear previous styling
  input.classList.remove('validation-error', 'validation-warning');
  
  // Remove existing tooltips
  const existingTooltip = input.parentNode.querySelector('.validation-tooltip');
  if (existingTooltip) {
    existingTooltip.remove();
  }
  
  if (isNaN(value) && input.value !== '') {
    showValidationError(input, 'Must be a valid number');
    return;
  }
  
  if (!isNaN(value)) {
    // Basic range validation
    if (value < min || value > max) {
      showValidationError(input, `Value must be between ${min} and ${max}`);
      return;
    }
    
    // Financial context validation
    const warning = getFinancialContextWarning(id, value);
    if (warning) {
      showValidationWarning(input, warning);
      return;
    }
    
    // Success styling for positive validation
    if (isBlur) {
      input.style.borderColor = '#10b981';
      input.style.boxShadow = '0 0 0 2px rgba(16, 185, 129, 0.2)';
      setTimeout(() => {
        input.style.borderColor = '';
        input.style.boxShadow = '';
      }, 1500);
    }
  }
}

// Show validation error with enhanced styling
function showValidationError(input, message) {
  input.classList.add('validation-error');
  
  const tooltip = document.createElement('div');
  tooltip.className = 'validation-tooltip error';
  tooltip.textContent = message;
  input.parentNode.appendChild(tooltip);
  
  // Auto-hide after 3 seconds
  setTimeout(() => {
    if (tooltip.parentNode) {
      tooltip.remove();
    }
  }, 3000);
}

// Show validation warning
function showValidationWarning(input, message) {
  input.classList.add('validation-warning');
  
  const tooltip = document.createElement('div');
  tooltip.className = 'validation-tooltip warning';
  tooltip.textContent = message;
  input.parentNode.appendChild(tooltip);
  
  // Auto-hide after 4 seconds
  setTimeout(() => {
    if (tooltip.parentNode) {
      tooltip.remove();
    }
  }, 4000);
}

// Get financial context warnings
function getFinancialContextWarning(fieldId, value) {
  const warnings = {
    wacc: {
      high: { threshold: 0.2, message: 'WACC above 20% suggests high-risk or distressed company' },
      low: { threshold: 0.04, message: 'WACC below 4% is unusually low - verify risk assessment' }
    },
    termGrowth: {
      high: { threshold: 0.04, message: 'Terminal growth >4% exceeds long-term GDP growth' },
      negative: { threshold: 0, message: 'Negative terminal growth assumes permanent decline' }
    },
    ebitMargin: {
      high: { threshold: 0.5, message: 'EBIT margin >50% is exceptional - verify sustainability' },
      low: { threshold: 0.05, message: 'EBIT margin <5% indicates low profitability' }
    },
    salesToCap: {
      high: { threshold: 8, message: 'Sales-to-Capital >8 suggests highly efficient operations' },
      low: { threshold: 0.5, message: 'Sales-to-Capital <0.5 indicates capital-intensive business' }
    },
    taxRate: {
      high: { threshold: 0.4, message: 'Tax rate >40% is high - verify jurisdiction' },
      low: { threshold: 0.1, message: 'Tax rate <10% is unusually low' }
    }
  };
  
  const fieldWarnings = warnings[fieldId];
  if (!fieldWarnings) return null;
  
  if (fieldWarnings.high && value > fieldWarnings.high.threshold) {
    return fieldWarnings.high.message;
  }
  
  if (fieldWarnings.low && value < fieldWarnings.low.threshold) {
    return fieldWarnings.low.message;
  }
  
  if (fieldWarnings.negative && value < fieldWarnings.negative.threshold) {
    return fieldWarnings.negative.message;
  }
  
  return null;
}

// Show financial input context
function showFinancialInputContext(input) {
  const contexts = {
    wacc: 'Weighted Average Cost of Capital - reflects company risk and capital structure',
    termGrowth: 'Long-term growth rate for terminal value calculation',
    ebitMargin: 'EBIT margin indicates operational efficiency and pricing power',
    salesToCap: 'Sales-to-Capital ratio measures asset utilization efficiency',
    taxRate: 'Effective corporate tax rate for NOPAT calculation',
    revenue: 'Base year revenue for growth projections (in millions)',
    shares: 'Diluted shares outstanding for per-share value calculation'
  };
  
  const context = contexts[input.id];
  if (context) {
    // Show context briefly in a subtle way
    const existingHint = input.parentNode.querySelector('.input-context-hint');
    if (existingHint) existingHint.remove();
    
    const hint = document.createElement('div');
    hint.className = 'input-context-hint';
    hint.textContent = context;
    input.parentNode.appendChild(hint);
    
    setTimeout(() => {
      if (hint.parentNode) {
        hint.style.opacity = '0';
        setTimeout(() => hint.remove(), 300);
      }
    }, 2000);
  }
}

// Validate WACC and terminal growth relationship in real-time
function validateWaccTermGrowthRelationship() {
  const waccInput = document.getElementById('wacc');
  const termGrowthInput = document.getElementById('termGrowth');
  
  if (!waccInput || !termGrowthInput) return;
  
  const wacc = parseFloat(waccInput.value) / 100;
  const termGrowth = parseFloat(termGrowthInput.value) / 100;
  
  // Clear previous relationship warnings
  [waccInput, termGrowthInput].forEach(input => {
    const relationshipWarning = input.parentNode.querySelector('.relationship-warning');
    if (relationshipWarning) relationshipWarning.remove();
    input.classList.remove('relationship-error');
  });
  
  if (!isNaN(wacc) && !isNaN(termGrowth)) {
    if (termGrowth >= wacc) {
      // Show error on both fields
      [waccInput, termGrowthInput].forEach(input => {
        input.classList.add('relationship-error');
        
        const warning = document.createElement('div');
        warning.className = 'validation-tooltip relationship-warning';
        warning.textContent = 'Terminal growth must be less than WACC for valid DCF model';
        input.parentNode.appendChild(warning);
      });
    } else if (wacc - termGrowth < 0.005) {
      // Show warning when they're very close
      [waccInput, termGrowthInput].forEach(input => {
        const warning = document.createElement('div');
        warning.className = 'validation-tooltip warning relationship-warning';
        warning.textContent = 'WACC and terminal growth are very close - consider increasing spread';
        input.parentNode.appendChild(warning);
      });
    }
  }
}

// Initialize UI event listeners
export function initializeUI() {
  // Initialize mobile optimizations
  if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
    initializeMobileOptimizations();
  }
  
  // Main action buttons
  document.getElementById("runModel")?.addEventListener("click", run);
  document.getElementById("presetExample")?.addEventListener("click", preset);
  document.getElementById("resetForm")?.addEventListener("click", resetForm);
  document.getElementById("resetAll")?.addEventListener("click", () => {
    if (confirm("Reset all data? This will clear scenarios, notes, and settings.")) {
      resetAllData();
      logLine("All data reset");
    }
  });
  
  // Monte Carlo
  document.getElementById("runMC")?.addEventListener("click", runMonteCarloHandler);
  document.getElementById("cancelMC")?.addEventListener("click", cancelMonteCarlo);
  
  // Tab switching
  const leftTabs = ["fcf", "rev", "margin", "pv", "waterfall", "sensi1d"];
  const rightTabs = ["sens", "twoWay", "tvm", "tornado"];
  
  leftTabs.forEach(tab => {
    document.querySelector(`[data-tab="${tab}"]`)?.addEventListener("click", () => {
      switchTab(tab, leftTabs);
    });
  });
  
  rightTabs.forEach(tab => {
    document.querySelector(`[data-tab="${tab}"]`)?.addEventListener("click", () => {
      switchTab(tab, rightTabs);
    });
  });
  
  // Solver
  document.getElementById("openSolver")?.addEventListener("click", openSolver);
  document.getElementById("closeSolver")?.addEventListener("click", closeSolver);
  
  // CLI
  document.getElementById("cliExec")?.addEventListener("click", () => {
    const input = document.getElementById("cliInput");
    if (input && input.value.trim()) {
      cliPrint(`> ${input.value}`);
      handleCli(input.value);
      input.value = "";
    }
  });
  
  document.getElementById("cliInput")?.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      document.getElementById("cliExec")?.click();
    }
  });
  
  // Notes
  document.getElementById("saveNotes")?.addEventListener("click", () => {
    const textarea = document.getElementById("notesArea");
    const ticker = document.getElementById("ticker")?.value || "SAMPLE";
    if (textarea && saveNotes(ticker, textarea.value)) {
      logLine("Notes saved");
    }
  });
  
  document.getElementById("clearNotes")?.addEventListener("click", () => {
    const textarea = document.getElementById("notesArea");
    if (textarea) {
      textarea.value = "";
      logLine("Notes cleared");
    }
  });
  
  // Export/Import
  document.getElementById("exportJSON")?.addEventListener("click", () => {
    if (currentResult) {
      const inputs = readInputs();
      const mcSettings = getMCSettings();
      exportRunData(inputs, currentResult, mcSettings);
      logLine("Exported JSON");
    }
  });
  
  document.getElementById("exportCSV")?.addEventListener("click", () => {
    if (currentResult) {
      const inputs = readInputs();
      const csv = toCSV(currentResult.series, currentResult.totals, inputs);
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${inputs.ticker || "output"}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      logLine("Exported CSV");
    }
  });
  
  // Copy link
  document.getElementById("copyLink")?.addEventListener("click", () => {
    const inputs = readInputs();
    const query = encodeStateToQuery(inputs);
    const url = `${window.location.origin}${window.location.pathname}?${query}`;
    
    navigator.clipboard.writeText(url).then(() => {
      logLine("Link copied to clipboard");
    }).catch(() => {
      logLine("Failed to copy link", "err");
    });
  });
  
  // Initialize on load
  logLine("Valor IVX initialized");
  cliHelp();
}
