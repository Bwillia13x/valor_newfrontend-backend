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
  try {
    const res = await fetch(url, { ...opts });
    const t1 = performance.now();
    backend.lastLatencyMs = t1 - t0;
    const ok = res.ok;
    backend.status = ok ? "online" : "offline";
    setBackendPill(`Backend: ${ok ? "Online" : "Offline"}${isFinite(backend.lastLatencyMs) ? ` • ${backend.lastLatencyMs.toFixed(0)} ms` : ""}`, ok);
    if (!ok) {
      console.warn(`Backend request failed ${res.status} ${res.statusText} (${url})`);
      return { ok: false, status: res.status, res };
    }
    return { ok: true, res };
  } catch (err) {
    const t1 = performance.now();
    backend.lastLatencyMs = t1 - t0;
    backend.status = "offline";
    setBackendPill(`Backend: Offline • ${backend.lastLatencyMs?.toFixed(0)} ms`, false);
    console.warn(`Backend unreachable (${url}): ${err?.message || err}`);
    return { ok: false, error: err };
  }
}

// Backend API functions
export async function sendRunToBackend(runData) {
  const { ok, res } = await safeFetch("http://localhost:5002/api/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(runData)
  });
  
  if (ok) {
    const data = await res.json();
    return { success: true, data };
  }
  return { success: false, error: res?.status || "Network error" };
}

export async function loadLastRunFromBackend() {
  const { ok, res } = await safeFetch("http://localhost:5002/api/runs/last");
  
  if (ok) {
    const data = await res.json();
    return { success: true, data };
  }
  return { success: false, error: res?.status || "Network error" };
}

export async function sendScenariosToBackend(scenarios) {
  const { ok, res } = await safeFetch("http://localhost:5002/api/scenarios", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(scenarios)
  });
  
  if (ok) {
    const data = await res.json();
    return { success: true, data };
  }
  return { success: false, error: res?.status || "Network error" };
}

export async function fetchScenariosFromBackend() {
  const { ok, res } = await safeFetch("http://localhost:5002/api/scenarios");
  
  if (ok) {
    const data = await res.json();
    return { success: true, data };
  }
  return { success: false, error: res?.status || "Network error" };
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