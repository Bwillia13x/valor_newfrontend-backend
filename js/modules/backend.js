import { normalizeError, Logger, withTimeout } from "./utils.js";
import { showToast } from "./ui-handlers.js";

// Valor IVX - Backend Communication Module
// Handles API interactions and backend status management

// Backend state management
const backend = {
  lastLatencyMs: null,
  status: "unknown", // online | offline | unknown
};

// Update backend status pill
export function setBackendPill(text, ok) {
  const pill = document.getElementById("backendPill");
  if (!pill) return;
  pill.textContent = text;
  pill.style.borderColor = ok === true ? "#2a6f4f" : ok === false ? "#7a3b3b" : "#223444";
  pill.style.background = ok === true ? "#103023" : ok === false ? "#2a1518" : "#0f1822";
  pill.style.color = ok === true ? "#b8ffe3" : ok === false ? "#ffb3b3" : "#bfefff";
}

// Safe fetch with latency tracking and error handling
export async function safeFetch(url, opts = {}) {
  const t0 = performance.now();
  const controller = new AbortController();
  const timeoutMs = opts.timeoutMs ?? 8000;
  const headers = {
    ...(opts.headers || {}),
    "X-Requested-With": "ValorIVX",
  };
  try {
    const res = await withTimeout(fetch(url, { ...opts, headers, signal: controller.signal }), timeoutMs, "fetch-timeout");
    const t1 = performance.now();
    backend.lastLatencyMs = t1 - t0;
    const ok = res.ok;
    backend.status = ok ? "online" : "offline";
    setBackendPill(`Backend: ${ok ? "Online" : "Offline"}${isFinite(backend.lastLatencyMs) ? ` • ${backend.lastLatencyMs.toFixed(0)} ms` : ""}`, ok);
    if (!ok) {
      Logger.warn("Backend request failed", { url, status: res.status, statusText: res.statusText });
      return { ok: false, status: res.status, res };
    }
    return { ok: true, res };
  } catch (err) {
    const t1 = performance.now();
    backend.lastLatencyMs = t1 - t0;
    backend.status = "offline";
    setBackendPill(`Backend: Offline • ${backend.lastLatencyMs?.toFixed(0)} ms`, false);
    const nerr = normalizeError(err);
    Logger.warn("Backend unreachable", { url, error: nerr });
    return { ok: false, error: nerr };
  } finally {
    controller.abort(); // ensure no leaks
  }
}

// Backend API functions
export async function sendRunToBackend(runData) {
  const { ok, res, error } = await safeFetch("http://localhost:5002/api/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(runData)
  });
  if (ok) {
    try {
      const data = await res.json();
      return { success: true, data };
    } catch (e) {
      const msg = normalizeError(e).message;
      showToast(`Failed to parse backend response: ${msg}`, { type: "error", ttl: 6000 });
      return { success: false, error: msg };
    }
  }
  const msg = error?.message || `HTTP ${res?.status ?? "Network error"}`;
  showToast(`Send run failed: ${msg}`, { type: "error", ttl: 6000 });
  return { success: false, error: msg };
}

export async function loadLastRunFromBackend() {
  const { ok, res, error } = await safeFetch("http://localhost:5002/api/runs/last");
  if (ok) {
    try {
      const data = await res.json();
      return { success: true, data };
    } catch (e) {
      const msg = normalizeError(e).message;
      showToast(`Failed to parse last run: ${msg}`, { type: "error", ttl: 6000 });
      return { success: false, error: msg };
    }
  }
  const msg = error?.message || `HTTP ${res?.status ?? "Network error"}`;
  showToast(`Load last run failed: ${msg}`, { type: "error", ttl: 6000 });
  return { success: false, error: msg };
}

export async function sendScenariosToBackend(scenarios) {
  const { ok, res, error } = await safeFetch("http://localhost:5002/api/scenarios", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(scenarios)
  });
  if (ok) {
    try {
      const data = await res.json();
      return { success: true, data };
    } catch (e) {
      const msg = normalizeError(e).message;
      showToast(`Failed to parse scenarios response: ${msg}`, { type: "error", ttl: 6000 });
      return { success: false, error: msg };
    }
  }
  const msg = error?.message || `HTTP ${res?.status ?? "Network error"}`;
  showToast(`Send scenarios failed: ${msg}`, { type: "error", ttl: 6000 });
  return { success: false, error: msg };
}

export async function fetchScenariosFromBackend() {
  const { ok, res, error } = await safeFetch("http://localhost:5002/api/scenarios");
  if (ok) {
    try {
      const data = await res.json();
      return { success: true, data };
    } catch (e) {
      const msg = normalizeError(e).message;
      showToast(`Failed to parse fetched scenarios: ${msg}`, { type: "error", ttl: 6000 });
      return { success: false, error: msg };
    }
  }
  const msg = error?.message || `HTTP ${res?.status ?? "Network error"}`;
  showToast(`Fetch scenarios failed: ${msg}`, { type: "error", ttl: 6000 });
  return { success: false, error: msg };
}

// Initialize backend status
export function initBackendStatus() {
  setBackendPill("Backend: Unknown", null);
}

// Get backend status
export function getBackendStatus() {
  return {
    status: backend.status,
    latency: backend.lastLatencyMs
  };
}
