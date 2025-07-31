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

// Logging utilities
export function logLine(msg, cls = "") {
  const terminal = document.getElementById("terminal");
  if (!terminal) return;
  
  const line = document.createElement("div");
  line.className = `term-line ${cls}`;
  line.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
  terminal.appendChild(line);
  terminal.scrollTop = terminal.scrollHeight;
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
    const errors = validateInputs(inputs);
    
    if (errors.length > 0) {
      updateStatusPill("Validation Errors", "error");
      errors.forEach(error => logLine(error, "err"));
      return;
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
    modal.style.display = "flex";
    document.getElementById("solverTarget")?.focus();
  }
}

export function closeSolver() {
  const modal = document.getElementById("solverModal");
  if (modal) {
    modal.style.display = "none";
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

// Initialize UI event listeners
export function initializeUI() {
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