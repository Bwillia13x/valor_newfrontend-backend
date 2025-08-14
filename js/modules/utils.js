/* Valor IVX - Utilities Module
 * Common helper functions and utilities
 * Extended with standardized error handling and logging utilities
 */

/* ========== DOM helpers ========== */
export const $ = (id) => document.getElementById(id);

/* ========== Error handling & logging ========== */
/**
 * Normalize any thrown value into a consistent shape.
 * Returns: { code, message, details }
 */
export function normalizeError(err, fallbackMessage = "Unexpected error") {
  if (!err) return { code: "UNKNOWN", message: fallbackMessage, details: null };
  if (typeof err === "string") return { code: "ERROR", message: err, details: null };
  if (err.name === "AbortError") return { code: "ABORTED", message: "Request aborted", details: null };
  const code = err.code || err.status || "ERROR";
  const message = err.message || fallbackMessage;
  const details = err.stack ? { stack: err.stack } : null;
  return { code, message, details };
}

/**
 * Basic logger with level gating. In production, this could POST to /api/logs.
 */
export const Logger = (() => {
  const levelPriority = { debug: 10, info: 20, warn: 30, error: 40 };
  let current = "info";
  function setLevel(lvl) { if (levelPriority[lvl]) current = lvl; }
  function shouldLog(lvl) { return levelPriority[lvl] >= levelPriority[current]; }
  function fmtPayload(payload) {
    try { return typeof payload === "string" ? payload : JSON.stringify(payload); } catch { return String(payload); }
  }
  return {
    setLevel,
    debug: (...args) => shouldLog("debug") && console.debug("[VI:DEBUG]", ...args),
    info:  (...args) => shouldLog("info")  && console.info("[VI:INFO]", ...args),
    warn:  (...args) => shouldLog("warn")  && console.warn("[VI:WARN]", ...args),
    error: (...args) => shouldLog("error") && console.error("[VI:ERROR]", ...args),
    logEvent: (name, payload = {}) => shouldLog("info") && console.info(`[VI:EVENT] ${name}`, fmtPayload(payload)),
  };
})();

/**
 * Safe JSON parse with fallback
 */
export function safeJsonParse(text, fallback = null) {
  try { return JSON.parse(text); } catch { return fallback; }
}

/**
 * Timeout a promise (e.g., fetch) after ms
 */
export function withTimeout(promise, ms, reason = "timeout") {
  let to;
  const timeout = new Promise((_, rej) => { to = setTimeout(() => rej(new Error(reason)), ms); });
  return Promise.race([promise.finally(() => clearTimeout(to)), timeout]);
}

/* ========== Formatting utilities ========== */
export const fmt = (n, opts = {}) => {
  if (!isFinite(n)) return "—";
  const { currency = false, decimals = 0, suffix = "" } = opts;
  const fixed = n.toLocaleString(undefined, {
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals,
  });
  return currency ? "$" + fixed + suffix : fixed + suffix;
};

// Math utilities
export const clamp = (x, a, b) => Math.min(Math.max(x, a), b);

// Random number generation utilities
export function mulberry32(a) {
  return function() {
    a = a + 0x6D2B79F5 | 0;
    var t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

export function randn(seedFn) {
  // Box-Muller transform for normal distribution
  let u = 0, v = 0;
  while (u === 0) u = seedFn();
  while (v === 0) v = seedFn();
  return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

/* ========== Local storage utilities ========== */
export function loadFromStorage(key, defaultValue = null) {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch {
    return defaultValue;
  }
}

export function saveToStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

// URL utilities
export function encodeStateToQuery(params) {
  const q = new URLSearchParams({
    ticker: params.ticker,
    revenue: String(params.revenue),
    growthY1: String((params.growthY1 * 100).toFixed(3)),
    growthDecay: String((params.growthDecay * 100).toFixed(3)),
    years: String(params.years),
    termGrowth: String((params.termGrowth * 100).toFixed(3)),
    ebitMargin: String((params.ebitMargin * 100).toFixed(3)),
    taxRate: String((params.taxRate * 100).toFixed(3)),
    salesToCap: String(params.salesToCap),
    wacc: String((params.wacc * 100).toFixed(3)),
    shares: String(params.shares),
    netDebt: String(params.netDebt),
    waccMin: String((params.waccMin * 100).toFixed(3)),
    waccMax: String((params.waccMax * 100).toFixed(3)),
    tgMin: String((params.tgMin * 100).toFixed(3)),
    tgMax: String((params.tgMax * 100).toFixed(3)),
    // ramps
    stage1End: String(params.stage1End),
    stage2End: String(params.stage2End),
    s1Growth: String((params.s1Growth * 100).toFixed(3)),
    s1Margin: String((params.s1Margin * 100).toFixed(3)),
    s1S2C: String(params.s1S2C),
    s1NWC: String((params.s1NWC * 100).toFixed(3)),
    s2Growth: String((params.s2Growth * 100).toFixed(3)),
    s2Margin: String((params.s2Margin * 100).toFixed(3)),
    s2S2C: String(params.s2S2C),
    s2NWC: String((params.s2NWC * 100).toFixed(3)),
    s3Growth: String((params.s3Growth * 100).toFixed(3)),
    s3Margin: String((params.s3Margin * 100).toFixed(3)),
    s3S2C: String(params.s3S2C),
    s3NWC: String((params.s3NWC * 100).toFixed(3)),
  });
  return q.toString();
}

export function decodeStateFromQuery() {
  const q = new URLSearchParams(window.location.search);
  const getNum = (k, d) => (q.has(k) ? Number(q.get(k)) : d);
  const getStr = (k, d) => (q.has(k) ? String(q.get(k)) : d);
  
  return {
    ticker: getStr("ticker", "SAMPLE"),
    revenue: getNum("revenue", 500),
    growthY1: getNum("growthY1", 12) / 100,
    growthDecay: getNum("growthDecay", 1.5) / 100,
    years: getNum("years", 7),
    termGrowth: getNum("termGrowth", 2.5) / 100,
    ebitMargin: getNum("ebitMargin", 22) / 100,
    taxRate: getNum("taxRate", 23) / 100,
    salesToCap: getNum("salesToCap", 2.5),
    wacc: getNum("wacc", 9.0) / 100,
    shares: getNum("shares", 150),
    netDebt: getNum("netDebt", 300),
    waccMin: getNum("waccMin", 7) / 100,
    waccMax: getNum("waccMax", 12) / 100,
    tgMin: getNum("tgMin", 1.0) / 100,
    tgMax: getNum("tgMax", 3.5) / 100,
    // ramps
    stage1End: getNum("stage1End", 3),
    stage2End: getNum("stage2End", 6),
    s1Growth: getNum("s1Growth", 12.0) / 100,
    s1Margin: getNum("s1Margin", 20.0) / 100,
    s1S2C: getNum("s1S2C", 2.5),
    s1NWC: getNum("s1NWC", 5.0) / 100,
    s2Growth: getNum("s2Growth", 8.0) / 100,
    s2Margin: getNum("s2Margin", 22.0) / 100,
    s2S2C: getNum("s2S2C", 3.0),
    s2NWC: getNum("s2NWC", 4.0) / 100,
    s3Growth: getNum("s3Growth", 4.0) / 100,
    s3Margin: getNum("s3Margin", 24.0) / 100,
    s3S2C: getNum("s3S2C", 3.5),
    s3NWC: getNum("s3NWC", 3.5) / 100,
  };
}

/* ========== Export utilities ========== */
export function exportCanvasPNG(canvas, name) {
  try {
    const link = document.createElement("a");
    link.download = `${name || "chart"}.png`;
    link.href = canvas.toDataURL("image/png");
    document.body.appendChild(link);
    link.click();
    link.remove();
    return true;
  } catch (err) {
    console.error("Export failed:", err);
    return false;
  }
}

export function toCSV(series, totals, params) {
  const lines = [];
  lines.push("Year,Revenue,Growth%,EBIT Margin%,EBIT,NOPAT,NWC,ΔNWC,Capex,Reinvestment,FCFF,PV(FCFF)");
  
  for (let t = 1; t <= params.years; t++) {
    const row = [
      t,
      series.rev[t]?.toFixed(1) || "",
      (series.growths[t] * 100)?.toFixed(1) || "",
      (series.margins[t] * 100)?.toFixed(1) || "",
      series.ebit[t]?.toFixed(1) || "",
      series.nopat[t]?.toFixed(1) || "",
      series.nwc[t]?.toFixed(1) || "",
      series.deltaNwc[t]?.toFixed(1) || "",
      series.capexProxy[t]?.toFixed(1) || "",
      series.reinvest[t]?.toFixed(1) || "",
      series.fcff[t]?.toFixed(1) || "",
      series.pvFcff[t]?.toFixed(1) || ""
    ];
    lines.push(row.join(","));
  }
  
  lines.push("");
  lines.push("Summary");
  lines.push(`Enterprise Value,${totals.ev?.toFixed(1) || ""}`);
  lines.push(`Equity Value,${totals.equity?.toFixed(1) || ""}`);
  lines.push(`Per Share,${totals.perShare?.toFixed(2) || ""}`);
  lines.push(`Terminal Value %,${(totals.tvPct * 100)?.toFixed(1) || ""}`);
  
  return lines.join("\n");
}
