// Valor IVX - Main Entry Point
// Modular application initialization

import { decodeStateFromQuery, encodeStateToQuery, toCSV } from './modules/utils.js';
import { initBackendStatus } from './modules/backend.js';
import { applyInputs, preset } from './modules/dcf-engine.js';
import { initMCSettings } from './modules/monte-carlo.js';
import { refreshScenarioDropdown, loadNotes } from './modules/scenarios.js';
import { initializeUI, logLine } from './modules/ui-handlers.js';
import { initFinancialDataUI } from './modules/financial-data.js';

// Application state
let isInitialized = false;

// Initialize application
async function initializeApp() {
  if (isInitialized) return;
  
  try {
    // Initialize backend status
    initBackendStatus();
    
    // Load URL parameters if present
    const urlParams = decodeStateFromQuery();
    if (urlParams && Object.keys(urlParams).length > 0) {
      applyInputs(urlParams);
      logLine("Loaded parameters from URL");
    } else {
      // Load preset if no URL parameters
      preset();
      logLine("Loaded preset values");
    }
    
    // Initialize Monte Carlo settings
    initMCSettings();
    
    // Load scenarios
    refreshScenarioDropdown();
    
    // Load notes for current ticker
    const ticker = document.getElementById("ticker")?.value || "SAMPLE";
    const notes = loadNotes(ticker);
    const notesArea = document.getElementById("notesArea");
    if (notesArea && notes) {
      notesArea.value = notes;
    }
    
    // Initialize UI event listeners
    initializeUI();
    
    // Initialize financial data UI
    initFinancialDataUI();
    
    // Set up additional event listeners
    setupEventListeners();
    
    // Run initial analysis
    setTimeout(() => {
      const { run } = await import('./modules/ui-handlers.js');
      run();
    }, 100);
    
    isInitialized = true;
    logLine("Application initialized successfully");
    
  } catch (error) {
    console.error("Initialization error:", error);
    logLine(`Initialization error: ${error.message}`, "err");
  }
}

// Setup additional event listeners
function setupEventListeners() {
  // Terminal value method toggle
  const tvPerp = document.getElementById("tvPerp");
  const tvMultiple = document.getElementById("tvMultiple");
  const tvMultipleVal = document.getElementById("tvMultipleVal");
  
  function updateTvControls() {
    if (!tvPerp || !tvMultiple || !tvMultipleVal) return;
    tvMultipleVal.disabled = tvPerp.checked;
  }
  
  tvPerp?.addEventListener("change", updateTvControls);
  tvMultiple?.addEventListener("change", updateTvControls);
  updateTvControls();
  
  // Ramp preview updates
  const rampInputs = [
    "stage1End", "stage2End",
    "s1Growth", "s1Margin", "s1S2C", "s1NWC",
    "s2Growth", "s2Margin", "s2S2C", "s2NWC",
    "s3Growth", "s3Margin", "s3S2C", "s3NWC"
  ];
  
  rampInputs.forEach(id => {
    const input = document.getElementById(id);
    if (input) {
      input.addEventListener("input", () => {
        const { readInputs } = await import('./modules/dcf-engine.js');
        const { renderRampPreview } = await import('./modules/charting.js');
        const inputs = readInputs();
        const canvas = document.getElementById("rampPreview");
        if (canvas) {
          renderRampPreview(canvas, inputs);
        }
      });
    }
  });
  
  // Scenario management
  document.getElementById("saveScenario")?.addEventListener("click", async () => {
    const { readInputs } = await import('./modules/dcf-engine.js');
    const { getMCSettings } = await import('./modules/monte-carlo.js');
    const { saveCurrentScenario } = await import('./modules/scenarios.js');
    
    const inputs = readInputs();
    const mcSettings = getMCSettings();
    const result = saveCurrentScenario(inputs, mcSettings);
    
    if (result.success) {
      logLine(`Scenario saved: ${result.name}`);
    } else {
      logLine(`Failed to save scenario: ${result.error}`, "err");
    }
  });
  
  document.getElementById("applyScenario")?.addEventListener("click", async () => {
    const select = document.getElementById("scenarioSelect");
    if (!select || !select.value) {
      logLine("No scenario selected", "err");
      return;
    }
    
    const { applyScenario } = await import('./modules/scenarios.js');
    const result = await applyScenario(parseInt(select.value));
    
    if (result.success) {
      logLine(`Applied scenario: ${result.scenario.name}`);
      // Re-run analysis with new inputs
      const { run } = await import('./modules/ui-handlers.js');
      run();
    } else {
      logLine(`Failed to apply scenario: ${result.error}`, "err");
    }
  });
  
  document.getElementById("deleteScenario")?.addEventListener("click", async () => {
    const select = document.getElementById("scenarioSelect");
    if (!select || !select.value) {
      logLine("No scenario selected", "err");
      return;
    }
    
    if (confirm("Delete this scenario?")) {
      const { deleteScenario } = await import('./modules/scenarios.js');
      const result = deleteScenario(parseInt(select.value));
      
      if (result.success) {
        logLine("Scenario deleted");
      } else {
        logLine(`Failed to delete scenario: ${result.error}`, "err");
      }
    }
  });
  
  // Export/Import scenarios
  document.getElementById("exportScenarios")?.addEventListener("click", async () => {
    const { exportScenarios } = await import('./modules/scenarios.js');
    const result = exportScenarios();
    
    if (result.success) {
      logLine("Scenarios exported");
    } else {
      logLine(`Failed to export scenarios: ${result.error}`, "err");
    }
  });
  
  document.getElementById("importScenarios")?.addEventListener("click", () => {
    document.getElementById("importScenariosFile")?.click();
  });
  
  document.getElementById("importScenariosFile")?.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      
      const { importScenarios } = await import('./modules/scenarios.js');
      const result = await importScenarios(data);
      
      if (result.success) {
        logLine(`Imported ${result.imported} scenarios (${result.total} total)`);
      } else {
        logLine(`Failed to import scenarios: ${result.error}`, "err");
      }
    } catch (err) {
      logLine(`Import error: ${err.message}`, "err");
    } finally {
      e.target.value = "";
    }
  });
  
  // Backend integration
  document.getElementById("sendRun")?.addEventListener("click", async () => {
    const { readInputs } = await import('./modules/dcf-engine.js');
    const { getMCSettings } = await import('./modules/monte-carlo.js');
    const { sendRunToBackend } = await import('./modules/backend.js');
    
    const inputs = readInputs();
    const mcSettings = getMCSettings();
    const runData = { inputs, mcSettings, timestamp: new Date().toISOString() };
    
    const result = await sendRunToBackend(runData);
    
    if (result.success) {
      logLine("Run sent to backend");
    } else {
      logLine(`Failed to send run: ${result.error}`, "err");
    }
  });
  
  document.getElementById("loadLastRun")?.addEventListener("click", async () => {
    const { loadLastRunFromBackend } = await import('./modules/backend.js');
    const { importRunData } = await import('./modules/scenarios.js');
    
    const result = await loadLastRunFromBackend();
    
    if (result.success) {
      const importResult = await importRunData(result.data);
      
      if (importResult.success) {
        logLine("Last run loaded from backend");
        // Re-run analysis with loaded data
        const { run } = await import('./modules/ui-handlers.js');
        run();
      } else {
        logLine(`Failed to load run: ${importResult.error}`, "err");
      }
    } else {
      logLine(`Failed to load from backend: ${result.error}`, "err");
    }
  });
  
  // Keyboard shortcuts
  document.addEventListener("keydown", (e) => {
    // Enter to run
    if (e.key === "Enter" && !e.ctrlKey && !e.metaKey) {
      const activeElement = document.activeElement;
      if (activeElement && (activeElement.tagName === "INPUT" || activeElement.tagName === "TEXTAREA")) {
        return; // Don't run if typing in input
      }
      
      e.preventDefault();
      const { run } = await import('./modules/ui-handlers.js');
      run();
    }
    
    // Ctrl/Cmd + Enter to run Monte Carlo
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      const { runMonteCarloHandler } = await import('./modules/ui-handlers.js');
      runMonteCarloHandler();
    }
  });
  
  // Notes auto-save
  let notesTimeout;
  document.getElementById("notesArea")?.addEventListener("input", () => {
    clearTimeout(notesTimeout);
    notesTimeout = setTimeout(async () => {
      const textarea = document.getElementById("notesArea");
      const ticker = document.getElementById("ticker")?.value || "SAMPLE";
      if (textarea) {
        const { saveNotes } = await import('./modules/scenarios.js');
        saveNotes(ticker, textarea.value);
      }
    }, 1000);
  });
  
  // Switch to LBO model
  document.getElementById("openLBO")?.addEventListener("click", () => {
    window.location.href = 'lbo.html';
  });
  
  // Ticker change - load notes
  document.getElementById("ticker")?.addEventListener("change", async () => {
    const ticker = document.getElementById("ticker")?.value || "SAMPLE";
    const notes = loadNotes(ticker);
    const notesArea = document.getElementById("notesArea");
    if (notesArea) {
      notesArea.value = notes;
    }
  });
}

// Initialize when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeApp);
} else {
  initializeApp();
}

// Export for global access if needed
window.ValorIVX = {
  run: async () => {
    const { run } = await import('./modules/ui-handlers.js');
    return run();
  },
  preset: () => preset(),
  reset: () => {
    const { resetForm } = await import('./modules/dcf-engine.js');
    return resetForm();
  }
}; 