// Valor IVX - Scenarios Module
// Scenario management and data persistence

import { loadFromStorage, saveToStorage } from './utils.js';

// Load scenarios from localStorage
export function loadScenarios() {
  try {
    return JSON.parse(localStorage.getItem("valor:scenarios") || "[]");
  } catch {
    return [];
  }
}

// Save scenarios to localStorage
export function saveScenarios(list) {
  try {
    localStorage.setItem("valor:scenarios", JSON.stringify(list));
    return true;
  } catch {
    return false;
  }
}

// Refresh scenario dropdown
export function refreshScenarioDropdown() {
  const select = document.getElementById("scenarioSelect");
  if (!select) return;
  
  const scenarios = loadScenarios();
  select.innerHTML = '<option value="">— Saved Scenarios —</option>';
  
  scenarios.forEach((scenario, index) => {
    const option = document.createElement("option");
    option.value = index;
    option.textContent = scenario.name || `Scenario ${index + 1}`;
    select.appendChild(option);
  });
}

// Generate scenario key for deduplication
export function scenarioKey(inputs) {
  const key = [
    inputs.ticker,
    inputs.revenue,
    inputs.growthY1,
    inputs.growthDecay,
    inputs.years,
    inputs.termGrowth,
    inputs.ebitMargin,
    inputs.taxRate,
    inputs.salesToCap,
    inputs.wacc,
    inputs.shares,
    inputs.netDebt,
    inputs.stage1End,
    inputs.stage2End,
    inputs.s1Growth,
    inputs.s1Margin,
    inputs.s1S2C,
    inputs.s1NWC,
    inputs.s2Growth,
    inputs.s2Margin,
    inputs.s2S2C,
    inputs.s2NWC,
    inputs.s3Growth,
    inputs.s3Margin,
    inputs.s3S2C,
    inputs.s3NWC
  ].join("|");
  return key;
}

// Deduplicate scenarios
export function dedupeScenarios(list) {
  const seen = new Set();
  return list.filter(item => {
    const key = scenarioKey(item.inputs);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

// Notes management
export function notesKey(ticker) {
  return `valor:notes:${ticker || "SAMPLE"}`;
}

export function loadNotes(ticker) {
  try {
    return localStorage.getItem(notesKey(ticker)) || "";
  } catch {
    return "";
  }
}

export function saveNotes(ticker, text) {
  try {
    localStorage.setItem(notesKey(ticker), text);
    return true;
  } catch {
    return false;
  }
}

// Generate scenario name from inputs
export function currentScenarioName(inputs) {
  const parts = [];
  if (inputs.ticker && inputs.ticker !== "SAMPLE") {
    parts.push(inputs.ticker);
  }
  if (inputs.wacc !== 0.09) {
    parts.push(`WACC ${(inputs.wacc * 100).toFixed(1)}%`);
  }
  if (inputs.termGrowth !== 0.025) {
    parts.push(`g ${(inputs.termGrowth * 100).toFixed(1)}%`);
  }
  if (inputs.years !== 7) {
    parts.push(`${inputs.years}y`);
  }
  if (inputs.ebitMargin !== 0.22) {
    parts.push(`Margin ${(inputs.ebitMargin * 100).toFixed(1)}%`);
  }
  
  if (parts.length === 0) {
    return "Base Case";
  }
  
  return parts.slice(0, 3).join(" | ");
}

// Save current scenario
export function saveCurrentScenario(inputs, mcSettings = null) {
  const scenarios = loadScenarios();
  const name = currentScenarioName(inputs);
  
  const scenario = {
    name,
    inputs: { ...inputs },
    timestamp: new Date().toISOString(),
    mcSettings: mcSettings ? { ...mcSettings } : null
  };
  
  scenarios.push(scenario);
  const deduped = dedupeScenarios(scenarios);
  
  if (saveScenarios(deduped)) {
    refreshScenarioDropdown();
    return { success: true, name };
  }
  return { success: false, error: "Failed to save scenario" };
}

// Apply scenario to form
export async function applyScenario(scenarioIndex) {
  const scenarios = loadScenarios();
  const scenario = scenarios[scenarioIndex];
  
  if (!scenario) {
    return { success: false, error: "Scenario not found" };
  }
  
  // Apply inputs
  const { applyInputs } = await import('./dcf-engine.js');
  applyInputs(scenario.inputs);
  
  // Apply MC settings if available
  if (scenario.mcSettings) {
    const { initMCSettings } = await import('./monte-carlo.js');
    // Store MC settings temporarily and apply them
    localStorage.setItem("valor:mc-settings", JSON.stringify(scenario.mcSettings));
    initMCSettings();
  }
  
  return { success: true, scenario };
}

// Delete scenario
export function deleteScenario(scenarioIndex) {
  const scenarios = loadScenarios();
  if (scenarioIndex >= 0 && scenarioIndex < scenarios.length) {
    scenarios.splice(scenarioIndex, 1);
    if (saveScenarios(scenarios)) {
      refreshScenarioDropdown();
      return { success: true };
    }
  }
  return { success: false, error: "Failed to delete scenario" };
}

// Export scenarios as JSON
export function exportScenarios() {
  const scenarios = loadScenarios();
  const payload = {
    _schema: "valor:scenarios@1",
    scenarios: scenarios
  };
  
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "valor-scenarios.json";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  
  return { success: true };
}

// Import scenarios from JSON
export async function importScenarios(jsonData) {
  try {
    let scenarios = [];
    
    // Handle both schema-wrapped and raw array formats
    if (jsonData._schema && jsonData._schema.startsWith("valor:scenarios@")) {
      scenarios = jsonData.scenarios || [];
    } else if (Array.isArray(jsonData)) {
      scenarios = jsonData;
    } else {
      return { success: false, error: "Invalid scenario format" };
    }
    
    // Validate scenarios
    const validScenarios = scenarios.filter(s => s.inputs && typeof s.inputs === "object");
    
    if (validScenarios.length === 0) {
      return { success: false, error: "No valid scenarios found" };
    }
    
    // Merge with existing scenarios
    const existing = loadScenarios();
    const merged = [...existing, ...validScenarios];
    const deduped = dedupeScenarios(merged);
    
    if (saveScenarios(deduped)) {
      refreshScenarioDropdown();
      return { success: true, imported: validScenarios.length, total: deduped.length };
    }
    
    return { success: false, error: "Failed to save imported scenarios" };
  } catch (err) {
    return { success: false, error: `Import failed: ${err.message}` };
  }
}

// Export run data
export function exportRunData(inputs, result, mcSettings = null) {
  const payload = {
    _schema: "valor:run@1",
    inputs: { ...inputs },
    result: result,
    timestamp: new Date().toISOString(),
    mcSettings: mcSettings ? { ...mcSettings } : null
  };
  
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${inputs.ticker || "output"}.valor-run.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  
  return { success: true };
}

// Import run data
export async function importRunData(jsonData) {
  try {
    if (!jsonData._schema || !jsonData._schema.startsWith("valor:run@")) {
      return { success: false, error: "Invalid run data format" };
    }
    
    const { applyInputs } = await import('./dcf-engine.js');
    
    // Apply inputs
    if (jsonData.inputs) {
      applyInputs(jsonData.inputs);
    }
    
    // Apply MC settings if available
    if (jsonData.mcSettings) {
      localStorage.setItem("valor:mc-settings", JSON.stringify(jsonData.mcSettings));
      const { initMCSettings } = await import('./monte-carlo.js');
      initMCSettings();
    }
    
    return { success: true, data: jsonData };
  } catch (err) {
    return { success: false, error: `Import failed: ${err.message}` };
  }
}

// Reset all data
export function resetAllData() {
  try {
    // Clear all valor-related localStorage items
    const keys = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith("valor:")) {
        keys.push(key);
      }
    }
    
    keys.forEach(key => localStorage.removeItem(key));
    
    // Refresh UI
    refreshScenarioDropdown();
    
    return { success: true, cleared: keys.length };
  } catch (err) {
    return { success: false, error: `Reset failed: ${err.message}` };
  }
} 