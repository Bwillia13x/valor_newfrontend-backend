/* eslint-disable no-useless-escape */
// Valor IVX Improved Frontend Logic (Standalone, no deps)

// DOM helpers
const $ = (id) => document.getElementById(id);
const fmt = (n, opts = {}) => {
  if (!isFinite(n)) return "—";
  const { currency = false, decimals = 0, suffix = "" } = opts;
  const fixed = n.toLocaleString(undefined, {
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals,
  });
  return currency ? "$" + fixed + suffix : fixed + suffix;
};
const clamp = (x, a, b) => Math.min(Math.max(x, a), b);

// Backend helpers: safe fetch with latency log and pill updates
const backend = {
  lastLatencyMs: null,
  status: "unknown", // online | offline | unknown
};
function setBackendPill(text, ok) {
  const pill = document.getElementById("backendPill");
  if (!pill) return;
  pill.textContent = text;
  pill.style.borderColor = ok === true ? "#2a6f4f" : ok === false ? "#7a3b3b" : "#223444";
  pill.style.background = ok === true ? "#103023" : ok === false ? "#2a1518" : "#0f1822";
  pill.style.color = ok === true ? "#b8ffe3" : ok === false ? "#ffb3b3" : "#bfefff";
}
async function safeFetch(url, opts = {}) {
  const t0 = performance.now();
  try {
    const res = await fetch(url, { ...opts });
    const t1 = performance.now();
    backend.lastLatencyMs = t1 - t0;
    const ok = res.ok;
    backend.status = ok ? "online" : "offline";
    setBackendPill(`Backend: ${ok ? "Online" : "Offline"}${isFinite(backend.lastLatencyMs) ? ` • ${backend.lastLatencyMs.toFixed(0)} ms` : ""}`, ok);
    if (!ok) {
      logLine(`Backend request failed ${res.status} ${res.statusText} (${url})`, "warn");
      return { ok: false, status: res.status, res };
    }
    return { ok: true, res };
  } catch (err) {
    const t1 = performance.now();
    backend.lastLatencyMs = t1 - t0;
    backend.status = "offline";
    setBackendPill(`Backend: Offline • ${backend.lastLatencyMs?.toFixed(0)} ms`, false);
    logLine(`Backend unreachable (${url}): ${err?.message || err}`, "warn");
    return { ok: false, error: err };
  }
}
// Initial backend pill
setBackendPill("Backend: Unknown", null);

// URL state helpers (include ramp params)
function encodeStateToQuery(params) {
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
function applyScenarioInputs(inputs) {
  try {
    const map = {
      ticker:"ticker", revenue:"revenue", growthY1:"growthY1", growthDecay:"growthDecay", years:"years",
      termGrowth:"termGrowth", ebitMargin:"ebitMargin", taxRate:"taxRate", salesToCap:"salesToCap",
      wacc:"wacc", shares:"shares", netDebt:"netDebt", waccMin:"waccMin", waccMax:"waccMax",
      tgMin:"tgMin", tgMax:"tgMax",
      stage1End:"stage1End", stage2End:"stage2End",
      s1Growth:"s1Growth", s1Margin:"s1Margin", s1S2C:"s1S2C", s1NWC:"s1NWC",
      s2Growth:"s2Growth", s2Margin:"s2Margin", s2S2C:"s2S2C", s2NWC:"s2NWC",
      s3Growth:"s3Growth", s3Margin:"s3Margin", s3S2C:"s3S2C", s3NWC:"s3NWC"
    };
    Object.entries(map).forEach(([k,id])=>{
      if (typeof inputs[k] === "undefined") return;
      const el = $(id);
      if (!el) return;
      const v = inputs[k];
      el.value = (typeof v === "number") ? String(Number.isFinite(v) ? v : el.value) : String(v);
    });
    // update TV controls if present on inputs
    const tvPerp = document.getElementById("tvPerp");
    const tvMultiple = document.getElementById("tvMultiple");
    const tvMultipleVal = document.getElementById("tvMultipleVal");
    if (inputs.tvMethod === "multiple") {
      tvMultiple && (tvMultiple.checked = true);
      tvPerp && (tvPerp.checked = false);
      tvMultipleVal && (tvMultipleVal.disabled = false);
      if (typeof inputs.tvMultipleVal !== "undefined" && tvMultipleVal) tvMultipleVal.value = String(inputs.tvMultipleVal);
    } else if (inputs.tvMethod === "perpetuity") {
      tvPerp && (tvPerp.checked = true);
      tvMultiple && (tvMultiple.checked = false);
      tvMultipleVal && (tvMultipleVal.disabled = true);
    }
  } catch(e) {
    logLine("Failed to apply scenario inputs: " + (e?.message || e), "err");
  }
}

function decodeStateFromQuery() {
  const q = new URLSearchParams(location.search);
  const getNum = (k, d) => (q.has(k) ? Number(q.get(k)) : d);
  const getStr = (k, d) => (q.has(k) ? String(q.get(k)) : d);
  const data = {
    ticker: getStr("ticker", "SAMPLE"),
    revenue: getNum("revenue", 500),
    growthY1: getNum("growthY1", 12) / 100,
    growthDecay: getNum("growthDecay", 1.5) / 100,
    years: Math.round(getNum("years", 7)),
    termGrowth: getNum("termGrowth", 2.5) / 100,
    ebitMargin: getNum("ebitMargin", 22) / 100,
    taxRate: getNum("taxRate", 23) / 100,
    salesToCap: getNum("salesToCap", 2.5),
    wacc: getNum("wacc", 9) / 100,
    shares: getNum("shares", 150),
    netDebt: getNum("netDebt", 300),
    waccMin: getNum("waccMin", 7) / 100,
    waccMax: getNum("waccMax", 12) / 100,
    tgMin: getNum("tgMin", 1) / 100,
    tgMax: getNum("tgMax", 3.5) / 100,
    // ramps
    stage1End: Math.max(1, Math.round(getNum("stage1End", 3))),
    stage2End: Math.max(2, Math.round(getNum("stage2End", 6))),
    s1Growth: getNum("s1Growth", 12) / 100,
    s1Margin: getNum("s1Margin", 20) / 100,
    s1S2C: getNum("s1S2C", 2.5),
    s1NWC: getNum("s1NWC", 5) / 100,
    s2Growth: getNum("s2Growth", 8) / 100,
    s2Margin: getNum("s2Margin", 22) / 100,
    s2S2C: getNum("s2S2C", 3.0),
    s2NWC: getNum("s2NWC", 4) / 100,
    s3Growth: getNum("s3Growth", 4) / 100,
    s3Margin: getNum("s3Margin", 24) / 100,
    s3S2C: getNum("s3S2C", 3.5),
    s3NWC: getNum("s3NWC", 3.5) / 100,
  };
  return data;
}

// Scenario storage helpers
function loadScenarios() {
  try {
    const raw = localStorage.getItem("valor:scenarios");
    const arr = raw ? JSON.parse(raw) : [];
    return Array.isArray(arr) ? arr : [];
  } catch { return []; }
}
function saveScenarios(list) {
  try { localStorage.setItem("valor:scenarios", JSON.stringify(list)); } catch {}
}
function refreshScenarioDropdown() {
  const sel = $("scenarioSelect");
  if (!sel) return;
  const list = loadScenarios();
  const current = sel.value;
  sel.innerHTML = '<option value="">— Saved Scenarios —</option>';
  list.forEach((s, idx) => {
    const name = s?.name || `Scenario ${idx+1}`;
    const opt = document.createElement("option");
    opt.value = String(idx);
    opt.textContent = name;
    sel.appendChild(opt);
  });
  // restore selection if possible
  if (current && Number(current) < list.length) sel.value = current;
}
function scenarioKey(inputs) {
  const keys = ["ticker","years","wacc","termGrowth","ebitMargin","salesToCap","shares","netDebt","stage1End","stage2End","s1Growth","s2Growth","s3Growth"];
  return keys.map(k=>String(inputs[k])).join("|");
}
function dedupeScenarios(list) {
  const seen = new Set();
  const res = [];
  for (const s of list) {
    const key = s && s.inputs ? scenarioKey(s.inputs) : Math.random().toString(36);
    if (seen.has(key)) continue;
    seen.add(key); res.push(s);
  }
  return res;
}

// Notes helpers
function notesKey(ticker) {
  const t = (ticker || "SAMPLE").trim().toUpperCase();
  return `valor:notes:${t}`;
}
function loadNotes(ticker) {
  try { return localStorage.getItem(notesKey(ticker)) || ""; } catch { return ""; }
}
function saveNotes(ticker, text) {
  try { localStorage.setItem(notesKey(ticker), text || ""); } catch {}
}

// Logging
function logLine(msg, cls = "") {
  const el = document.createElement("div");
  el.className = "term-line" + (cls ? " " + cls : "");
  el.innerHTML = msg;
  $("terminal").appendChild(el);
  $("terminal").scrollTop = $("terminal").scrollHeight;
}

// Input reading
function readInputs() {
  return {
    ticker: $("ticker").value.trim() || "SAMPLE",
    revenue: Number($("revenue").value),
    growthY1: Number($("growthY1").value) / 100,
    growthDecay: Number($("growthDecay").value) / 100,
    years: Math.round(Number($("years").value)),
    termGrowth: Number($("termGrowth").value) / 100,
    ebitMargin: Number($("ebitMargin").value) / 100,
    taxRate: Number($("taxRate").value) / 100,
    salesToCap: Number($("salesToCap").value),
    wacc: Number($("wacc").value) / 100,
    shares: Number($("shares").value),
    netDebt: Number($("netDebt").value),
    waccMin: Number($("waccMin").value) / 100,
    waccMax: Number($("waccMax").value) / 100,
    tgMin: Number($("tgMin").value) / 100,
    tgMax: Number($("tgMax").value) / 100,
    // Ramps
    stage1End: Math.max(1, Math.round(Number($("stage1End")?.value || 3))),
    stage2End: Math.max(2, Math.round(Number($("stage2End")?.value || 6))),
    s1Growth: Number($("s1Growth")?.value || 12) / 100,
    s1Margin: Number($("s1Margin")?.value || 20) / 100,
    s1S2C: Number($("s1S2C")?.value || 2.5),
    s1NWC: Number($("s1NWC")?.value || 5) / 100,
    s2Growth: Number($("s2Growth")?.value || 8) / 100,
    s2Margin: Number($("s2Margin")?.value || 22) / 100,
    s2S2C: Number($("s2S2C")?.value || 3.0),
    s2NWC: Number($("s2NWC")?.value || 4) / 100,
    s3Growth: Number($("s3Growth")?.value || 4) / 100,
    s3Margin: Number($("s3Margin")?.value || 24) / 100,
    s3S2C: Number($("s3S2C")?.value || 3.5),
    s3NWC: Number($("s3NWC")?.value || 3.5) / 100,
  };
}

function preset() {
  $("ticker").value = "VALR";
  $("revenue").value = 850;
  $("growthY1").value = 14;
  $("growthDecay").value = 1.8;
  $("years").value = 8;
  $("termGrowth").value = 2.5;
  $("ebitMargin").value = 24;
  $("taxRate").value = 24;
  $("salesToCap").value = 2.8;
  $("wacc").value = 9.0;
  $("shares").value = 160;
  $("netDebt").value = 250;
  $("waccMin").value = 7.5;
  $("waccMax").value = 11.0;
  $("tgMin").value = 1.0;
  $("tgMax").value = 3.0;

  // Advanced MC sensible defaults
  if ($("mcMarginVol")) $("mcMarginVol").value = String($("mcVol")?.value || "2.0");
  if ($("mcS2CVol")) $("mcS2CVol").value = "5.0";
  if ($("mcCorrGM")) $("mcCorrGM").value = "0.30";
}

function resetForm() {
  document.querySelectorAll("input").forEach((i) => (i.value = i.defaultValue));
  // Also clear advanced MC controls explicitly
  if ($("mcMarginVol")) $("mcMarginVol").value = "";
  if ($("mcS2CVol")) $("mcS2CVol").value = "";
  if ($("mcCorrGM")) $("mcCorrGM").value = "";
  // Clear invalid states
  ["mcMarginVol","mcS2CVol","mcCorrGM"].forEach(id => { const el = $(id); if (el) el.removeAttribute("aria-invalid"); });

  $("terminal").innerHTML = "";
  $("evVal").textContent = "—";
  $("eqVal").textContent = "—";
  $("psVal").textContent = "—";
  $("tvPct").textContent = "—";
  $("fcffSummary").textContent = "—";
  $("statusPill").textContent = "Idle";
}

// DCF Engine with ΔNWC allowed to be negative (cash release)
function dcfEngine(params) {
  const p = { ...params };
  const warnings = [];
  // Safety clamp years
  p.years = clamp(p.years, 3, 15);
  // If WACC <= g, adjust slightly; UI should prevent this, but guard anyway.
  if (p.wacc <= p.termGrowth && (p.tvMethod || "perpetuity") === "perpetuity") {
    warnings.push("Terminal growth >= WACC; adjusted g down slightly.");
    p.termGrowth = Math.max(0, p.wacc - 0.005);
  }

  const rev = [];
  const growths = [];
  const margins = [];
  const ebit = [];
  const nopat = [];
  const nwcRatio = [];
  const nwc = [];
  const deltaNwc = [];
  const capexProxy = [];
  const reinvest = [];
  const fcff = [];
  rev[0] = p.revenue;

  const s1End = Math.min(p.years, Math.max(1, p.stage1End || 3));
  const s2End = Math.min(p.years, Math.max(s1End + 1, p.stage2End || 6));
  function stageFor(t) {
    if (t <= s1End) return 1;
    if (t <= s2End) return 2;
    return 3;
  }
  function getStageValue(t, key) {
    const s = stageFor(t);
    if (s === 1) return p["s1" + key];
    if (s === 2) return p["s2" + key];
    return p["s3" + key];
  }

  for (let t = 1; t <= p.years; t++) {
    const g = Math.max(0, getStageValue(t, "Growth") ?? p.growthY1 - p.growthDecay * (t - 1));
    growths[t] = g;
    rev[t] = (rev[t - 1] ?? p.revenue) * (1 + g);

    const m = Math.max(0, getStageValue(t, "Margin") ?? p.ebitMargin);
    margins[t] = m;
    ebit[t] = rev[t] * m;
    const tax = ebit[t] * p.taxRate;
    nopat[t] = ebit[t] - tax;

    const nwcPct = Math.max(0, getStageValue(t, "NWC") ?? 0);
    nwcRatio[t] = nwcPct;
    nwc[t] = rev[t] * nwcPct;

    // Base-year NWC anchored to stage1 assumption
    const baseNwc = rev[0] * (getStageValue(1, "NWC") ?? 0);
    deltaNwc[t] = (nwc[t] - (nwc[t - 1] ?? baseNwc));

    // Add warning for significant cash release from NWC
    if (-deltaNwc[t] > 0.05 * rev[t]) {
      warnings.push(`Year ${t}: Significant cash release from NWC ($${(-deltaNwc[t]).toFixed(1)}M)`);
    }

    const s2c = Math.max(0.01, getStageValue(t, "S2C") ?? p.salesToCap);
    const deltaSales = rev[t] - (rev[t - 1] ?? rev[0]);
    capexProxy[t] = Math.max(0, deltaSales / s2c);

    // Allow negative ΔNWC (cash release)
    reinvest[t] = Math.max(0, capexProxy[t]) + (deltaNwc[t] || 0);
    fcff[t] = nopat[t] - reinvest[t];
  }

  const disc = (r, t) => Math.pow(1 + r, t);
  const pvFcff = [];
  let sumPvFcff = 0;
  for (let t = 1; t <= p.years; t++) {
    pvFcff[t] = fcff[t] / disc(p.wacc, t);
    sumPvFcff += pvFcff[t];
  }

  const fcffN = fcff[p.years];

  // Terminal value methods:
  // - perpetuity (Gordon): TV = FCFF_{n+1} / (WACC - g)
  // - multiple: TV = EV/FCFF multiple * FCFF_{n+1}
  const method = (p.tvMethod || "perpetuity");
  let tvNext = fcffN * (1 + p.termGrowth);
  let tv = 0;
  if (method === "multiple") {
    const mult = Math.max(0, Number(p.tvMultipleVal) || 0);
    tv = mult * tvNext;
  } else {
    // default to perpetuity
    tv = (p.wacc > p.termGrowth) ? (tvNext / (p.wacc - p.termGrowth)) : 0;
  }
  const pvTv = tv / disc(p.wacc, p.years);

  const ev = sumPvFcff + pvTv;
  const equity = ev - p.netDebt;
  const perShare = equity / Math.max(1, p.shares);
  const tvPct = ev > 0 ? pvTv / ev : 0;

  return {
    series: { rev, growths, margins, ebit, nopat, nwcRatio, nwc, deltaNwc, capexProxy, reinvest, fcff, pvFcff },
    totals: { sumPvFcff, pvTv, ev, equity, perShare, tvPct },
    params: { ...p, stage1End: s1End, stage2End: s2End },
    warnings,
  };
}

// Validation guardrails
function validateInputs(inputs) {
  const errors = [];
  const markInvalid = (id, on) => {
    const el = $(id);
    if (el) el.setAttribute("aria-invalid", on ? "true" : "false");
  };
  ["wacc", "termGrowth", "years", "taxRate", "salesToCap", "stage1End", "stage2End"].forEach((id) =>
    markInvalid(id, false)
  );

  if (inputs.termGrowth >= inputs.wacc) {
    errors.push("Terminal growth must be less than WACC.");
    markInvalid("termGrowth", true);
    markInvalid("wacc", true);
  }
  if (inputs.stage2End <= inputs.stage1End) {
    errors.push("Stage 2 end must be after Stage 1 end.");
    markInvalid("stage2End", true);
    markInvalid("stage1End", true);
  }
  if (inputs.stage1End > inputs.years || inputs.stage2End > inputs.years) {
    errors.push("Stage end years must not exceed projection years.");
    markInvalid("stage1End", true);
    markInvalid("stage2End", true);
    markInvalid("years", true);
  }
  if (inputs.years < 3 || inputs.years > 15) {
    errors.push("Projection years must be between 3 and 15.");
    markInvalid("years", true);
  }
  if (inputs.wacc <= 0.02 || inputs.wacc > 0.30) {
    errors.push("WACC out of typical bounds (2%–30%).");
    markInvalid("wacc", true);
  }
  if (inputs.termGrowth < -0.01 || inputs.termGrowth > 0.08) {
    errors.push("Terminal growth out of typical bounds (-1%–8%).");
    markInvalid("termGrowth", true);
  }
  if (inputs.taxRate < 0 || inputs.taxRate > 0.50) {
    errors.push("Tax rate out of bounds (0%–50%).");
    markInvalid("taxRate", true);
  }
  if (inputs.salesToCap < 0.1) {
    errors.push("Sales-to-Capital must be ≥ 0.1.");
    markInvalid("salesToCap", true);
  }
  return errors;
}

// KPI calculation
function computeKPIs(res) {
  const s = res.series, t = res.totals;
  const years = s.rev.length - 1;
  let cumInvested = 0;
  for (let i = 1; i <= years; i++) cumInvested += s.reinvest[i] || 0;
  const roic = cumInvested > 0 ? s.nopat[years] / cumInvested : NaN;
  const reinvRate = s.nopat[years] ? s.reinvest[years] / s.nopat[years] : NaN;
  const f1 = s.fcff[1] || 0.0001;
  const fn = s.fcff[years] || f1;
  const fcfCAGR = years > 1 ? Math.pow(fn / f1, 1 / (years - 1)) - 1 : 0;
  let cumPV = 0, payback = NaN;
  for (let i = 1; i <= years; i++) {
    cumPV += s.pvFcff[i] || 0;
    if (!isFinite(payback) && cumPV >= t.ev) payback = i;
  }
  const evNopat = s.nopat[years] ? t.ev / s.nopat[years] : NaN;
  return { roic, reinvRate, fcfCAGR, payback, evNopat };
}
function updateKPIUI(k) {
  const pct = (x) => (isFinite(x) ? (x * 100).toFixed(1) + "%" : "—");
  const num = (x, d = 2) => (isFinite(x) ? x.toFixed(d) : "—");
  $("kpiROIC").textContent = pct(k.roic);
  $("kpiReinv").textContent = pct(k.reinvRate);
  $("kpiFcfCAGR").textContent = pct(k.fcfCAGR);
  $("kpiPayback").textContent = isFinite(k.payback) ? k.payback.toFixed(0) : "—";
  $("kpiEVNOPAT").textContent = num(k.evNopat, 2);
}

// Simple charts (reuse from original with minimal functionality)
function toCSV(series, totals, params) {
  const years = series.rev.length - 1;
  const rows = [];
  rows.push(["Ticker", params.ticker || ""]);
  rows.push(["Years", String(params.years)]);
  rows.push([]);
  rows.push(["Year","Revenue (M)","Growth","EBIT (M)","NOPAT (M)","NWC%","NWC (M)","ΔNWC (M)","Sales-to-Cap","CapexProxy (M)","Reinvestment (M)","FCFF (M)","PV(FCFF) (M)"]);
  for (let t = 1; t <= years; t++) {
    rows.push([
      "Y"+t,
      (series.rev[t] || 0).toFixed(2),
      ((series.growths[t] || 0) * 100).toFixed(2) + "%",
      (series.ebit[t] || 0).toFixed(2),
      (series.nopat[t] || 0).toFixed(2),
      ((series.nwcRatio[t] || 0) * 100).toFixed(2) + "%",
      (series.nwc[t] || 0).toFixed(2),
      (series.deltaNwc[t] || 0).toFixed(2),
      (params.salesToCap || 0).toFixed(2),
      (series.capexProxy[t] || 0).toFixed(2),
      (series.reinvest[t] || 0).toFixed(2),
      (series.fcff[t] || 0).toFixed(2),
      (series.pvFcff[t] || 0).toFixed(2),
    ]);
  }
  rows.push([]);
  rows.push(["PV(FCFF) (M)", totals.sumPvFcff.toFixed(2)]);
  rows.push(["PV(TV) (M)", totals.pvTv.toFixed(2)]);
  rows.push(["EV (M)", totals.ev.toFixed(2)]);
  rows.push(["Equity (M)", totals.equity.toFixed(2)]);
  rows.push(["Per Share ($)", totals.perShare.toFixed(2)]);
  // CSV escaping
  const csv = rows.map(r => r.map(cell => {
    const s = String(cell ?? "");
    if (s.includes(",") || s.includes('"') || /\s/.test(s)) {
      return '"' + s.replace(/"/g, '""') + '"';
    }
    return s;
  }).join(",")).join("\n");
  return csv;
}

function renderFcfChart(canvas, series, mode = "fcf", tooltipDiv = null, overlaySeries = null) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  // Data mapping
  const dataMap = {
    fcf: series.fcff,
    rev: series.rev,
    margin: series.ebit,
    pv: series.pvFcff,
  };
  const arr = dataMap[mode] || series.fcff;
  const years = arr.length - 1;
  if (years <= 0) return;

  const vals = arr.slice(1);
  let allVals = [...vals];

  // Include overlay series in min/max calculation
  let overlayVals = [];
  if (overlaySeries) {
    const overlayArr = dataMap[mode] || overlaySeries.fcff;
    if (overlayArr && overlayArr.length > 1) {
      overlayVals = overlayArr.slice(1);
      allVals = allVals.concat(overlayVals);
    }
  }

  const minV = Math.min(0, ...allVals.filter(isFinite));
  const maxV = Math.max(...allVals.filter(isFinite));
  const pad = (maxV - minV) * 0.15 || 1;
  const yMin = minV - pad;
  const yMax = maxV + pad;

  const x = (i) => 40 + (W - 60) * ((i - 1) / (years - 1 || 1));
  const y = (v) => (H - 24) - (H - 44) * ((v - yMin) / ((yMax - yMin) || 1));

  // Axes and Grid
  ctx.strokeStyle = "#1b2a3a";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(40, 10);
  ctx.lineTo(40, H - 24);
  ctx.lineTo(W - 10, H - 24);
  ctx.stroke();
  ctx.strokeStyle = "rgba(114,239,221,0.08)";
  ctx.setLineDash([4, 4]);
  for (let i = 0; i <= 4; i++) {
    const yy = 10 + (H - 34) * (i / 4);
    ctx.beginPath(); ctx.moveTo(40, yy); ctx.lineTo(W - 10, yy); ctx.stroke();
  }
  ctx.setLineDash([]);

  // Plot main series
  plotLine(ctx, vals, years, x, y, "#72efdd", "#4cc9f0");

  // Plot overlay series if available
  if (overlayVals.length > 0) {
    plotLine(ctx, overlayVals, Math.min(years, overlayVals.length), x, y, "#ffd166", "#ff9a5c", true);
  }

  // Axes labels
  ctx.fillStyle = "#9cb4c9";
  ctx.font = "11px ui-monospace, monospace";
  for (let i = 1; i <= years; i++) ctx.fillText("Y" + i, x(i) - 6, H - 8);
  for (let i = 0; i <= 4; i++) {
    const value = yMax - (i * (yMax - yMin) / 4);
    const yy = 10 + (H - 34) * (i / 4);
    ctx.fillText("$" + value.toFixed(0) + "M", 6, yy + 4);
  }

  // Tooltip
  if (tooltipDiv) {
    const bounds = canvas.getBoundingClientRect();
    canvas.onmousemove = (e) => {
      const mx = e.clientX - bounds.left;
      const t = Math.round(((mx - 40) / (W - 60)) * (years - 1) + 1);
      const idx = clamp(t, 1, years);
      const v = vals[idx - 1];
      const ov = overlayVals[idx - 1];
      let tipText = `Y${idx}: ${fmt(v, {currency:true, decimals:2, suffix:"M"})}`;
      if (isFinite(ov)) tipText += ` | Overlay: ${fmt(ov, {currency:true, decimals:2, suffix:"M"})}`;
      if (isFinite(v)) {
        tooltipDiv.style.display = "block";
        tooltipDiv.textContent = tipText;
        tooltipDiv.style.left = e.clientX - bounds.left + "px";
        tooltipDiv.style.top = e.clientY - bounds.top + "px";
      }
    };
    canvas.onmouseleave = () => { tooltipDiv.style.display = "none"; };
  }
}

function plotLine(ctx, data, years, xFn, yFn, color1, color2, dashed = false) {
  ctx.beginPath();
  ctx.lineWidth = 2;
  const grad = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
  grad.addColorStop(0, color1);
  grad.addColorStop(1, color2);
  ctx.strokeStyle = grad;
  if (dashed) ctx.setLineDash([5, 5]);
  for (let i = 1; i <= years; i++) {
    if (i === 1) ctx.moveTo(xFn(i), yFn(data[i - 1]));
    else ctx.lineTo(xFn(i), yFn(data[i - 1]));
  }
  ctx.stroke();
  if (dashed) ctx.setLineDash([]);

  // Points
  ctx.fillStyle = color1;
  for (let i = 1; i <= years; i++) {
    ctx.beginPath();
    ctx.arc(xFn(i), yFn(data[i - 1]), 2.8, 0, Math.PI * 2);
    ctx.fill();
  }
}

/**
 * Chunked heatmap renderer with caching and progress indicator.
 */
const _hmCache = new Map(); // key -> perShare
const MAX_HM_CACHE_SIZE = 5000;

function getFromHmCache(key) {
  const val = _hmCache.get(key);
  if (val !== undefined) {
    // Move to end to mark as recently used
    _hmCache.delete(key);
    _hmCache.set(key, val);
  }
  return val;
}

function setInHmCache(key, value) {
  if (_hmCache.size >= MAX_HM_CACHE_SIZE) {
    // Evict least recently used (first item in map)
    const oldestKey = _hmCache.keys().next().value;
    _hmCache.delete(oldestKey);
  }
  _hmCache.set(key, value);
}

function renderHeatmap(canvas, params, baseInputs) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const padL = 40, padB = 24, padR = 10, padT = 10;
  const gridW = W - padL - padR, gridH = H - padT - padB;
  const steps = 24;

  // Helper rounding to cache fewer cells
  const round2 = (x, p) => Math.round(x * p) / p; // e.g., p=100 -> 2 decimals

  // Draw axes now
  ctx.strokeStyle = "#1b2a3a";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padL, padT);
  ctx.lineTo(padL, padT + gridH);
  ctx.lineTo(padL + gridW, padT + gridH);
  ctx.stroke();

  // Axis labels
  ctx.fillStyle = "#9cb4c9";
  ctx.font = "11px ui-monospace, monospace";
  for (let i = 0; i <= 4; i++) {
    const t = i / 4;
    const w = baseInputs.waccMin + t * (baseInputs.waccMax - baseInputs.waccMin);
    const x = padL + t * gridW;
    ctx.fillText((w * 100).toFixed(1) + "%", x - 10, H - 6);
  }
  for (let i = 0; i <= 4; i++) {
    const t = i / 4;
    const g = baseInputs.tgMin + t * (baseInputs.tgMax - baseInputs.tgMin);
    const y = padT + (1 - t) * gridH;
    ctx.fillText((g * 100).toFixed(1) + "%", 6, y + 4);
  }

  // Progress pill
  const pill = document.getElementById("statusPill");
  const prevText = pill ? pill.textContent : "";

  // Precompute ranges by coarse sampling for colorscale
  let vMin = +Infinity, vMax = -Infinity;
  const coarse = 6;
  for (let yi = 0; yi <= coarse; yi++) {
    const g = baseInputs.tgMin + (yi / coarse) * (baseInputs.tgMax - baseInputs.tgMin);
    for (let xi = 0; xi <= coarse; xi++) {
      const w = baseInputs.waccMin + (xi / coarse) * (baseInputs.waccMax - baseInputs.waccMin);
      const key = `${round2(w,1000)}|${round2(g,1000)}|${round2(params.termGrowth,1000)}|${round2(params.wacc,1000)}|${params.years}|${round2(params.ebitMargin,1000)}|${round2(params.salesToCap,1000)}`;
      let ps = getFromHmCache(key);
      if (ps === undefined) {
        ps = dcfEngine({ ...params, termGrowth: g, wacc: w }).totals.perShare;
        setInHmCache(key, ps);
      }
      if (isFinite(ps)) {
        vMin = Math.min(vMin, ps);
        vMax = Math.max(vMax, ps);
      }
    }
  }
  if (!isFinite(vMin) || !isFinite(vMax) || vMin === vMax) { vMin = 0; vMax = 1; }

  const cw = gridW / (steps + 1), ch = gridH / (steps + 1);
  function colorFor(val, min, max) {
    const t = (val - min) / ((max - min) || 1);
    const r = Math.floor(128 + 127 * t);
    const g = Math.floor(255 - 155 * t);
    const b = Math.floor(128 - 64 * t);
    return `rgba(${r},${g},${b},0.9)`;
  }

  // Chunked paint
  let yi = 0;
  const totalRows = steps + 1;
  const paintRow = () => {
    const yVal = baseInputs.tgMin + (yi / steps) * (baseInputs.tgMax - baseInputs.tgMin);
    for (let xi = 0; xi <= steps; xi++) {
      const wVal = baseInputs.waccMin + (xi / steps) * (baseInputs.waccMax - baseInputs.waccMin);
      const key = `${round2(wVal,1000)}|${round2(yVal,1000)}|${round2(params.termGrowth,1000)}|${round2(params.wacc,1000)}|${params.years}|${round2(params.ebitMargin,1000)}|${round2(params.salesToCap,1000)}`;
      let ps = getFromHmCache(key);
      if (ps === undefined) {
        ps = dcfEngine({ ...params, termGrowth: yVal, wacc: wVal }).totals.perShare;
        setInHmCache(key, ps);
      }
      ctx.fillStyle = colorFor(ps, vMin, vMax);
      const x = padL + xi * cw;
      const y = padT + (steps - yi) * ch;
      ctx.fillRect(x, y, Math.ceil(cw) + 1, Math.ceil(ch) + 1);
    }
    yi++;
    if (pill) pill.textContent = `Rendering… ${Math.round(yi / totalRows * 100)}%`;
    if (yi <= steps) {
      (window.requestIdleCallback || window.setTimeout)(paintRow);
    } else {
      if (pill) pill.textContent = prevText || "Done";

      // Draw vertical color scale legend on the right
      const scaleW = 12;
      const scaleX = padL + gridW + 8;
      const scaleY = padT;
      const scaleH = gridH;
      for (let i = 0; i < scaleH; i++) {
        const t = 1 - i / (scaleH - 1);
        const val = vMin + t * (vMax - vMin);
        ctx.fillStyle = colorFor(val, vMin, vMax);
        ctx.fillRect(scaleX, scaleY + i, scaleW, 1);
      }
      // ticks
      ctx.fillStyle = "#9cb4c9"; ctx.font = "11px ui-monospace, monospace";
      ctx.strokeStyle = "#203142"; ctx.lineWidth = 1;
      for (let i = 0; i <= 4; i++) {
        const t = i / 4;
        const y = scaleY + (1 - t) * scaleH;
        ctx.beginPath(); ctx.moveTo(scaleX + scaleW, y); ctx.lineTo(scaleX + scaleW + 6, y); ctx.stroke();
        const val = vMin + t * (vMax - vMin);
        ctx.fillText("$" + val.toFixed(2), scaleX + scaleW + 8, y + 4);
      }
    }
  };

  (window.requestIdleCallback || window.setTimeout)(paintRow);

  // Hover tooltip for heatmap
  const tooltipId = "heatmapTooltip";
  let tooltip = document.getElementById(tooltipId);
  if (!tooltip) {
    tooltip = document.createElement("div");
    tooltip.id = tooltipId;
    tooltip.className = "tooltip";
    tooltip.style.display = "none";
    canvas.parentElement?.appendChild(tooltip);
  }
  canvas.onmousemove = (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const xi = Math.floor((mx - padL) / cw);
    const yiInv = Math.floor((my - padT) / ch);
    if (xi < 0 || xi > steps || yiInv < 0 || yiInv > steps) { tooltip.style.display = "none"; return; }
    const yiIdx = steps - yiInv;
    const wVal = baseInputs.waccMin + (xi / steps) * (baseInputs.waccMax - baseInputs.waccMin);
    const gVal = baseInputs.tgMin + (yiIdx / steps) * (baseInputs.tgMax - baseInputs.tgMin);
    const key = `${round2(wVal,1000)}|${round2(gVal,1000)}|${round2(params.termGrowth,1000)}|${round2(params.wacc,1000)}|${params.years}|${round2(params.ebitMargin,1000)}|${round2(params.salesToCap,1000)}`;
    const ps = getFromHmCache(key);
    if (!isFinite(ps)) { tooltip.style.display = "none"; return; }
    tooltip.style.display = "block";
    tooltip.textContent = `WACC ${ (wVal*100).toFixed(2)}% | g ${ (gVal*100).toFixed(2)}% → $${ps.toFixed(2)}/sh`;
    tooltip.style.left = `${mx}px`;
    tooltip.style.top = `${my - 10}px`;
  };
  canvas.onmouseleave = () => { const el = document.getElementById(tooltipId); if (el) el.style.display = "none"; };
}

function renderRampPreview(canvas, inputs) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  const years = Math.max(3, Math.min(15, Number($("years").value) || 7));
  const s1End = Math.min(years, Math.max(1, inputs.stage1End));
  const s2End = Math.min(years, Math.max(s1End + 1, inputs.stage2End));
  function forYear(t, k) {
    if (t <= s1End) return inputs["s1" + k];
    if (t <= s2End) return inputs["s2" + k];
    return inputs["s3" + k];
  }
  const growth = [], margin = [], nwc = [];
  for (let t = 1; t <= years; t++) {
    growth[t] = forYear(t, "Growth") * 100;
    margin[t] = forYear(t, "Margin") * 100;
    nwc[t] = forYear(t, "NWC") * 100;
  }

  // axes
  ctx.strokeStyle = "#1b2a3a"; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(40, 10); ctx.lineTo(40, H - 24); ctx.lineTo(W - 10, H - 24); ctx.stroke();

  const all = [...growth.slice(1), ...margin.slice(1), ...nwc.slice(1)];
  const minV = Math.min(...all, 0), maxV = Math.max(...all, 10);
  const pad = (maxV - minV) * 0.15 || 1;
  const yMin = minV - pad, yMax = maxV + pad;
  const x = (i) => 40 + (W - 60) * ((i - 1) / ((years - 1) || 1));
  const y = (v) => (H - 24) - (H - 44) * ((v - yMin) / ((yMax - yMin) || 1));

  function plotLine(arr, color) {
    ctx.beginPath(); ctx.lineWidth = 2; ctx.strokeStyle = color;
    ctx.moveTo(x(1), y(arr[1]));
    for (let i = 2; i <= years; i++) ctx.lineTo(x(i), y(arr[i]));
    ctx.stroke();
  }
  plotLine(growth, "#72efdd");
  plotLine(margin, "#4cc9f0");
  plotLine(nwc, "#ffd166");

  ctx.fillStyle = "#9cb4c9"; ctx.font = "11px ui-monospace, monospace";
  ctx.fillText("Growth%", 50, 14);
  ctx.fillText("Margin%", 120, 14);
  ctx.fillText("NWC%", 190, 14);
}

// Waterfall minimal renderer
function renderWaterfall(canvas, res) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  const barW = (W - 80) / 5;
  const baseX = 40, baseY = H - 40;
  const pvF = res.totals.sumPvFcff;
  const pvT = res.totals.pvTv;
  const ev = res.totals.ev;
  const equity = res.totals.equity;
  const netDebt = res.params.netDebt;
  function drawBar(x, y, h, color, label, value) {
    ctx.fillStyle = color;
    ctx.fillRect(x, y - h, barW, h);
    ctx.fillStyle = "#9cb4c9";
    ctx.font = "12px ui-monospace, monospace";
    ctx.fillText(label, x, H - 20);
    ctx.fillText("$" + value.toFixed(0) + "M", x, y - h - 6);
  }
  const scale = (val) => {
    const maxVal = Math.max(pvF + pvT + Math.abs(netDebt), equity);
    const maxH = H - 80;
    return (val / Math.max(1, maxVal)) * maxH;
  };
  const hF = scale(pvF);
  const hT = scale(pvT);
  const hEV = scale(ev);
  const hND = scale(Math.abs(netDebt));
  const hEq = scale(Math.max(0, equity));
  drawBar(baseX + 0 * barW + 0 * 20, baseY, hF, "#72efdd", "PV(FCFF)", pvF);
  drawBar(baseX + 1 * barW + 1 * 20, baseY, hT, "#4cc9f0", "PV(TV)", pvT);
  ctx.strokeStyle = "#35546b"; ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(baseX + 0.5 * barW, baseY - hF);
  ctx.lineTo(baseX + 1.5 * barW + 20, baseY - (hF + hT));
  ctx.stroke();
  drawBar(baseX + 2 * barW + 2 * 20, baseY, hEV, "#19b394", "EV", ev);
  // Net debt negative bar
  ctx.fillStyle = "#ff6b6b";
  ctx.fillRect(baseX + 3 * barW + 3 * 20, baseY, barW, -hND);
  ctx.fillStyle = "#9cb4c9";
  ctx.fillText("Net Debt", baseX + 3 * barW + 3 * 20, H - 20);
  ctx.fillText("$" + (netDebt).toFixed(0) + "M", baseX + 3 * barW + 3 * 20, baseY - hND - 6);
  drawBar(baseX + 4 * barW + 4 * 20, baseY, hEq, "#80ffdb", "Equity", equity);
}

// Sensitivity 1D
function renderSensitivity1D(canvas, inputs, axis, minVal, maxVal, steps) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  const percentFields = new Set(["wacc", "termGrowth", "ebitMargin"]);
  const toModel = (k, v) => (percentFields.has(k) ? v / 100 : v);
  const xs = [], ys = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const v = minVal + t * (maxVal - minVal);
    const p = { ...inputs, [axis]: toModel(axis, v) };
    const res = dcfEngine(p);
    xs.push(v);
    ys.push(res.totals.perShare);
  }
  const minY = Math.min(...ys.filter(isFinite));
  const maxY = Math.max(...ys.filter(isFinite));
  const padY = (maxY - minY) * 0.15 || 1;
  ctx.strokeStyle = "#1b2a3a"; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(40, 10); ctx.lineTo(40, H - 24); ctx.lineTo(W - 10, H - 24); ctx.stroke();
  const x = (i) => 40 + (W - 60) * (i / steps);
  const y = (v) => (H - 24) - (H - 44) * ((v - (minY - padY)) / ((maxY - minY + 2 * padY) || 1));
  ctx.beginPath(); ctx.lineWidth = 2; ctx.strokeStyle = "#72efdd";
  for (let i = 0; i <= steps; i++) {
    const px = x(i), py = y(ys[i]);
    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
  }
  ctx.stroke();
  ctx.fillStyle = "#9cb4c9"; ctx.font = "11px ui-monospace, monospace";
  ctx.fillText(minVal.toFixed(1) + (percentFields.has(axis) ? "%" : ""), 40, H - 6);
  ctx.fillText(((minVal + maxVal) / 2).toFixed(1) + (percentFields.has(axis) ? "%" : ""), W / 2 - 16, H - 6);
  ctx.fillText(maxVal.toFixed(1) + (percentFields.has(axis) ? "%" : ""), W - 60, H - 6);
  ctx.fillText("$" + minY.toFixed(1), 6, y(minY));
  ctx.fillText("$" + maxY.toFixed(1), 6, y(maxY));
}

// Deterministic RNG for MC
function mulberry32(a) {
  return function () {
    let t = (a += 0x6D2B79F5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function randn(seedFn) {
  const u1 = Math.max(1e-12, seedFn());
  const u2 = Math.max(1e-12, seedFn());
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

/**
 * Monte Carlo engine: perturbs growth by N(0, vol_pp) per year, optional seed.
 * Returns array of per-share results and summary stats.
 */
function runMonteCarlo(baseInputs, trials, volPP, seedStr, cancelSignal, options = {}) {
  const base = { ...baseInputs };
  const vol = Number(volPP) || 0;
  const trialsN = Math.max(100, Math.min(10000, Math.round(Number(trials) || 1000)));
  const {
    marginVolPP = volPP,         // pp volatility for margins
    s2cVolPct = 5,               // % volatility for Sales-to-Capital (relative, not pp)
    corrGM = 0.3,                // correlation between Growth and Margin shocks
    persistKey = "valor:mc-settings",
    onProgress = null,           // optional progress callback: (done, total) => void
    progressEvery = 500          // update every N samples
  } = options;

  // Persist settings
  try {
    const save = {
      trials: trialsN, volPP: Number(volPP) || 0, seedStr: seedStr || "",
      marginVolPP: Number(marginVolPP) || 0,
      s2cVolPct: Number(s2cVolPct) || 0,
      corrGM: Number(corrGM) || 0
    };
    localStorage.setItem(persistKey, JSON.stringify(save));
  } catch {}

  // Build a deterministic 32-bit seed from seedStr if present, else random
  let seed = 0xDEADBEEF;
  if (seedStr && typeof seedStr === "string") {
    for (let i = 0; i < seedStr.length; i++) {
      seed = (seed ^ seedStr.charCodeAt(i)) >>> 0;
      seed = Math.imul(seed, 2654435761) >>> 0;
    }
  } else {
    seed = (Math.random() * 0xffffffff) >>> 0;
  }
  const rnd = mulberry32(seed);

  // Correlated shocks (Growth and Margin using Cholesky)
  const rho = Math.max(-0.99, Math.min(0.99, Number(corrGM) || 0));
  const a11 = 1, a21 = rho, a22 = Math.sqrt(1 - rho * rho);

  const results = new Array(trialsN);
  const tStart = performance.now();
  for (let t = 0; t < trialsN; t++) {
    if (cancelSignal?.requested) {
      results.length = t; // truncate to completed trials
      break;
    }
    const p = { ...base };
    const gPP = Number(volPP) / 100;         // growth pp -> fraction
    const mPP = Number(marginVolPP) / 100;   // margin pp -> fraction
    const s2cPct = Math.max(0, Number(s2cVolPct) / 100);

    // Base shocks (independent standard normals)
    const z1 = randn(rnd); // for growth
    const z2 = randn(rnd); // for margin
    // Apply correlation
    const uG = z1;
    const uM = a21 * z1 + a22 * z2;

    // Growth stage shocks
    const e1 = uG * gPP, e2 = randn(rnd) * gPP, e3 = randn(rnd) * gPP;
    p.s1Growth = Math.max(0, (base.s1Growth ?? base.growthY1) + e1);
    p.s2Growth = Math.max(0, (base.s2Growth ?? Math.max(0, base.growthY1 - base.growthDecay * (base.stage1End || 3))) + e2);
    p.s3Growth = Math.max(0, (base.s3Growth ?? Math.max(0, base.termGrowth)) + e3);

    // Margin stage shocks (correlated to growth via uM primarily in stage 1, independent later)
    const m1 = uM * mPP, m2 = randn(rnd) * mPP, m3 = randn(rnd) * mPP;
    p.s1Margin = Math.max(0, (base.s1Margin ?? base.ebitMargin) + m1);
    p.s2Margin = Math.max(0, (base.s2Margin ?? base.ebitMargin) + m2);
    p.s3Margin = Math.max(0, (base.s3Margin ?? base.ebitMargin) + m3);

    // Sales-to-Capital shocks (lognormal-style multiplicative)
    const s1 = (base.s1S2C ?? base.salesToCap);
    const s2 = (base.s2S2C ?? base.salesToCap);
    const s3 = (base.s3S2C ?? base.salesToCap);
    const k1 = Math.max(0.1, s1 * (1 + s2cPct * randn(rnd)));
    const k2 = Math.max(0.1, s2 * (1 + s2cPct * randn(rnd)));
    const k3 = Math.max(0.1, s3 * (1 + s2cPct * randn(rnd)));
    p.s1S2C = k1; p.s2S2C = k2; p.s3S2C = k3;

    const res = dcfEngine(p);
    results[t] = res.totals.perShare;

    // Progress callback
    if (typeof onProgress === "function" && (t + 1) % Math.max(1, progressEvery) === 0) {
      try {
        const elapsed = performance.now() - tStart;
        onProgress(t + 1, trialsN, elapsed);
      } catch {}
    }
  }
  // final progress
  if (typeof onProgress === "function") {
    try { onProgress(trialsN, trialsN, performance.now() - tStart); } catch {}
  }

  const clean = results.filter(isFinite).sort((a,b)=>a-b);
  const n = clean.length || 1;
  const mean = clean.reduce((a,b)=>a+b,0) / n;
  const median = clean[Math.floor(n/2)] ?? NaN;
  const p10 = clean[Math.floor(0.10*n)] ?? NaN;
  const p90 = clean[Math.floor(0.90*n)] ?? NaN;
  return { results: clean, stats: { mean, median, p10, p90, n, seed, corrGM: rho } };
}

let histShowAnnotations = true;
function renderHistogram(canvas, data, annotations) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  if (!data || data.length === 0) return;
  const bins = 30;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = (max - min) || 1;
  const counts = Array(bins).fill(0);
  data.forEach(v => {
    let idx = Math.floor((v - min) / range * bins);
    if (idx === bins) idx = bins - 1;
    counts[idx]++;
  });
  const maxC = Math.max(...counts) || 1;
  ctx.strokeStyle = "#1b2a3a"; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(40, 10); ctx.lineTo(40, H - 24); ctx.lineTo(W - 10, H - 24); ctx.stroke();
  const gridW = W - 50;
  const barW = gridW / bins;
  for (let i = 0; i < bins; i++) {
    const h = ((H - 40) * (counts[i] / maxC));
    const x = 40 + i * barW;
    const y = (H - 24) - h;
    const t = i / (bins - 1);
    const r = Math.floor(64 + 128 * t);
    const g = Math.floor(200 - 120 * t);
    const b = Math.floor(240 - 100 * t);
    ctx.fillStyle = `rgba(${r},${g},${b},0.85)`;
    ctx.fillRect(x, y, Math.ceil(barW) - 1, Math.ceil(h));
  }
  ctx.fillStyle = "#9cb4c9";
  ctx.font = "11px ui-monospace, monospace";
  ctx.fillText("$" + min.toFixed(2), 40, H - 6);
  ctx.fillText("$" + max.toFixed(2), W - 80, H - 6);

  // Histogram annotations (mean, median, p10, p90)
  if (histShowAnnotations && annotations) {
    const { mean, median, p10, p90 } = annotations;
    const xForVal = (v) => 40 + ((v - min) / range) * gridW;
    function vline(x, color, label) {
      const y0 = 10, y1 = H - 24;
      ctx.strokeStyle = color; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, y0); ctx.lineTo(x, y1); ctx.stroke();
      ctx.fillStyle = color; ctx.font = "10px ui-monospace, monospace";
      ctx.fillText(label, Math.min(W - 30, Math.max(42, x + 2)), y0 + 10);
    }
    if (isFinite(mean)) vline(xForVal(mean), "#72efdd", "μ");
    if (isFinite(median)) vline(xForVal(median), "#cfe3f7", "med");
    if (isFinite(p10)) vline(xForVal(p10), "rgba(255,209,102,0.9)", "p10");
    if (isFinite(p90)) vline(xForVal(p90), "rgba(255,209,102,0.9)", "p90");
  }

  // Lightweight tooltip for bins: show bin range and count
  const bounds = canvas.getBoundingClientRect();
  const tooltipId = "histTooltip";
  let tip = document.getElementById(tooltipId);
  if (!tip) {
    tip = document.createElement("div");
    tip.id = tooltipId;
    tip.className = "tooltip";
    tip.style.display = "none";
    canvas.parentElement?.appendChild(tip);
  }
  canvas.onmousemove = (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    // compute bin by x
    const idx = Math.floor(((mx - 40) / (gridW)) * bins);
    if (idx < 0 || idx >= bins || my < 10 || my > H - 24) { tip.style.display = "none"; return; }
    const lo = min + (idx / bins) * range;
    const hi = min + ((idx + 1) / bins) * range;
    const cnt = counts[idx] || 0;
    tip.style.display = "block";
    tip.textContent = `$${lo.toFixed(2)} – $${hi.toFixed(2)}: ${cnt}`;
    tip.style.left = `${mx}px`;
    tip.style.top = `${my - 10}px`;
  };
  canvas.onmouseleave = () => { const el = document.getElementById(tooltipId); if (el) el.style.display = "none"; };
}

/**
 * Wire Monte Carlo UI
 */
/** MC cancel/ETA state */
let mcCancel = { requested: false };
const cancelBtn = $("cancelMC");
cancelBtn?.addEventListener("click", () => {
  mcCancel.requested = true;
  cancelBtn.style.display = "none";
  const pill = $("statusPill");
  if (pill) pill.textContent = "Canceling…";
});

$("runMC")?.addEventListener("click", () => {
  try {
    const inputs = readInputs();
    const trials = Number($("mcTrials")?.value || 1000);
    const vol = Number($("mcVol")?.value || 2.0);
    const seedStr = String($("mcSeed")?.value || "");

    // Attempt to restore persisted MC settings
    let savedOpts = {};
    try {
      const saved = localStorage.getItem("valor:mc-settings");
      if (saved) savedOpts = JSON.parse(saved) || {};
    } catch {}

    // Read advanced controls; if blank, fall back to saved or defaults
    const marginVolInput = $("mcMarginVol")?.value;
    const s2cVolInput = $("mcS2CVol")?.value;
    const corrGMInput = $("mcCorrGM")?.value;

    // Validation and clamping
    const clampCorr = (x) => Math.max(-0.99, Math.min(0.99, x));
    const parsedCorr = corrGMInput !== "" ? clampCorr(Number(corrGMInput)) : (isFinite(savedOpts.corrGM) ? clampCorr(savedOpts.corrGM) : 0.3);
    const parsedS2C = s2cVolInput !== "" ? Math.max(0, Number(s2cVolInput)) : Math.max(0, savedOpts.s2cVolPct ?? 5);
    const parsedMVol = marginVolInput !== "" ? Math.max(0, Number(marginVolInput)) : Math.max(0, savedOpts.marginVolPP ?? vol);

    // Toggle invalid states
    const mark = (id, on) => { const el = $(id); if (el) el.setAttribute("aria-invalid", on ? "true" : "false"); };
    mark("mcCorrGM", !(isFinite(Number(corrGMInput)) || corrGMInput === "")); // non-numeric input
    mark("mcS2CVol", !(isFinite(Number(s2cVolInput)) || s2cVolInput === "" || Number(s2cVolInput) >= 0));
    mark("mcMarginVol", !(isFinite(Number(marginVolInput)) || marginVolInput === "" || Number(marginVolInput) >= 0));

    // Write back clamped value to the field for UX if user supplied it
    if (corrGMInput !== "" && $("mcCorrGM")) $("mcCorrGM").value = String(parsedCorr);

    const opts = {
      marginVolPP: parsedMVol,
      s2cVolPct: parsedS2C,
      corrGM: parsedCorr
    };

    // Cancel flag setup and UI
    mcCancel.requested = false;
    if (cancelBtn) cancelBtn.style.display = "";
    const pill = $("statusPill");
    if (pill) pill.textContent = "MC… starting";

    const t0 = performance.now();
    let finalResults = null, finalStats = null, canceled = false;

    const { results, stats } = runMonteCarlo(inputs, trials, vol, seedStr, mcCancel, {
      ...opts,
      onProgress: (done, total, elapsedMs) => {
        if (total >= 500) {
          const etaMs = (elapsedMs / Math.max(1, done)) * (total - done);
          const pct = Math.round((done / total) * 100);
          const mins = Math.floor(etaMs / 60000);
          const secs = Math.round((etaMs % 60000) / 1000);
          if (pill) pill.textContent = `MC… ${done}/${total} (${pct}%) • ETA: ${mins}m ${secs}s`;
        }
      },
      progressEvery: Math.max(100, Math.floor(trials / 20)) // ~20 updates
    });

    finalResults = results;
    finalStats = stats;

    const t1 = performance.now();
    renderHistogram($("mcHist"), finalResults, finalStats);
    const sum = finalStats;
    const msg = `n=${sum.n}, mean=$${isFinite(sum.mean)?sum.mean.toFixed(2):"—"}, median=$${isFinite(sum.median)?sum.median.toFixed(2):"—"}, p10=$${isFinite(sum.p10)?sum.p10.toFixed(2):"—"}, p90=$${isFinite(sum.p90)?sum.p90.toFixed(2):"—"}, ρ=${(sum.corrGM??0).toFixed(2)} • ${(t1-t0).toFixed(1)} ms`;
    const summaryEl = $("mcSummary");
    if (summaryEl) summaryEl.textContent = msg + (mcCancel.requested ? " (canceled)" : "");
    logLine("MC complete • " + msg + (mcCancel.requested ? " (canceled)" : ""));
    if (cancelBtn) cancelBtn.style.display = "none";
    if (pill) pill.textContent = "MC Done";
  } catch (e) {
    if (e && e.__mc_cancel__) {
      // Graceful cancel: no histogram render to avoid partial data; just update UI
      const pill = $("statusPill");
      if (pill) pill.textContent = "MC canceled";
      const summaryEl = $("mcSummary");
      if (summaryEl) summaryEl.textContent = "Monte Carlo canceled.";
      logLine("Monte Carlo canceled by user.", "warn");
      if (cancelBtn) cancelBtn.style.display = "none";
      return;
    }
    logLine("Monte Carlo failed: " + (e?.message || e), "err");
    if (cancelBtn) cancelBtn.style.display = "none";
  }
});

/**
 * Core run
 */
function run() {
  const inputs = readInputs();
  $("terminal").innerHTML = "";
  $("statusPill").textContent = "Running...";

  const errs = validateInputs(inputs);
  if (errs.length) {
    $("statusPill").textContent = "Invalid";
    errs.forEach(e => logLine("ERROR: " + e, "err"));
    return;
  }

  // Log assumptions
  logLine(`<span class="tag">Ticker</span> ${inputs.ticker}`);
  logLine(`<span class="tag">Revenue</span> $${inputs.revenue.toFixed(0)}M`);
  logLine(`<span class="tag">Growth Y1</span> ${(inputs.growthY1 * 100).toFixed(1)}% | Decay ${(inputs.growthDecay * 100).toFixed(1)} pp/yr | Years ${inputs.years}`);
  logLine(`<span class="tag">Margins</span> EBIT ${(inputs.ebitMargin * 100).toFixed(1)}% | Tax ${(inputs.taxRate * 100).toFixed(1)}%`);
  logLine(`<span class="tag">Reinvestment</span> Sales-to-Capital ${inputs.salesToCap.toFixed(2)}`);
  logLine(`<span class="tag">Discount</span> WACC ${(inputs.wacc * 100).toFixed(1)}% | Terminal g ${(inputs.termGrowth * 100).toFixed(1)}%`);
  logLine(`<span class="tag">Capital</span> Shares ${inputs.shares.toFixed(1)}M | Net Debt $${inputs.netDebt.toFixed(0)}M`);

  const start = performance.now();
  // inject terminal method inputs before run
  const method = (document.getElementById("tvMultiple")?.checked ? "multiple" : "perpetuity");
  const multVal = Number(document.getElementById("tvMultipleVal")?.value || 12);
  const result = dcfEngine({ ...inputs, tvMethod: method, tvMultipleVal: multVal });
  result.warnings.forEach(w => logLine("WARN: " + w, "warn"));

  const { ev, equity, perShare, tvPct, sumPvFcff, pvTv } = result.totals;
  $("evVal").textContent = fmt(ev, { currency: true, decimals: 0, suffix: "M" });
  $("eqVal").textContent = fmt(equity, { currency: true, decimals: 0, suffix: "M" });
  $("psVal").textContent = isFinite(perShare) ? "$" + perShare.toFixed(2) : "—";
  $("tvPct").textContent = isFinite(tvPct) ? (tvPct * 100).toFixed(1) + "%" : "—";
  $("fcffSummary").textContent = `PV(FCFF) ${fmt(sumPvFcff, { currency: true, decimals: 0, suffix: "M" })} | PV(TV) ${fmt(pvTv, { currency: true, decimals: 0, suffix: "M" })}`;

  // TV dominance warning
  if (isFinite(tvPct) && tvPct > 0.85) {
    logLine("WARN: Terminal value contributes over 85% of EV. Consider extending projection years, reducing g, or increasing reinvestment.", "warn");
  }

  // Render charts
  const fcfCanvas = $("fcfChart");
  const heatCanvas = $("heatmap");
  const rampCanvas = $("rampPreview");
  const tooltipDiv = $("chartTooltip");
  if (rampCanvas) renderRampPreview(rampCanvas, inputs);

  const activeLeft = document.querySelector('.tabs[aria-label="Left data views"] .tab.active')?.getAttribute('data-tab') || "fcf";
  $("legendOverlay").style.display = overlaySeriesCache ? "" : "none";
  if (overlaySeriesCache?.label) $("overlayLabel").textContent = overlaySeriesCache.label;

  if (activeLeft === "waterfall") {
    renderWaterfall(fcfCanvas, result);
    $("seriesTitle").textContent = "EV Waterfall";
    $("sensi1dControls").hidden = true;
  } else if (activeLeft === "sensi1d") {
    $("seriesTitle").textContent = "1D Sensitivity (Per-Share vs Axis)";
    $("sensi1dControls").hidden = false;
    const axis = $("s1dAxis").value;
    const minV = Number($("s1dMin").value);
    const maxV = Number($("s1dMax").value);
    const steps = Math.max(5, Math.min(200, Number($("s1dSteps").value)));
    renderSensitivity1D(fcfCanvas, inputs, axis, minV, maxV, steps);
  } else {
    renderFcfChart(fcfCanvas, result.series, activeLeft, tooltipDiv, overlaySeriesCache?.series);
    $("sensi1dControls").hidden = true;
  }

  // KPIs
  const k = computeKPIs(result);
  updateKPIUI(k);

  // Right tabs
  const rightTabs = document.querySelectorAll('.tabs')[1];
  const activeRight = rightTabs.querySelector('.tab.active')?.getAttribute('data-tab') || "sens";
  const tornadoCanvas = $("tornadoChart");
  // Toggle export buttons
  const btnT = $("exportTornado");
  if (btnT) btnT.disabled = activeRight !== "tornado";
  const tornadoControls = $("tornadoControls");
  if (tornadoControls) tornadoControls.style.display = activeRight === "tornado" ? "flex" : "none";

  if (activeRight === "sens") {
    renderHeatmap(heatCanvas, result.params, inputs);
    tornadoCanvas.style.display = "none";
  } else if (activeRight === "twoWay") {
    // Use heatmap as 2D grid reusing renderHeatmap by mapping axes min/max from controls
    const axisX = $("axisX").value;
    const axisY = $("axisY").value;
    const xMin = Number($("xMin").value);
    const xMax = Number($("xMax").value);
    const yMin = Number($("yMin").value);
    const yMax = Number($("yMax").value);
    // Construct a temporary inputs with sensitivity ranges
    const tmp = { ...inputs };
    tmp.waccMin = axisX === "wacc" ? xMin / 100 : inputs.waccMin;
    tmp.waccMax = axisX === "wacc" ? xMax / 100 : inputs.waccMax;
    tmp.tgMin = axisY === "termGrowth" ? yMin / 100 : inputs.tgMin;
    tmp.tgMax = axisY === "termGrowth" ? yMax / 100 : inputs.tgMax;
    renderHeatmap(heatCanvas, result.params, tmp);
    tornadoCanvas.style.display = "none";
  } else if (activeRight === "tvm") {
    const ctx = heatCanvas.getContext("2d");
    const W = heatCanvas.width, H = heatCanvas.height;
    ctx.clearRect(0, 0, W, H);
    const pv = result.totals.sumPvFcff;
    const tv = result.totals.pvTv;
    const total = Math.max(1e-9, pv + tv);
    const pvPct = pv / total, tvP = tv / total;
    // base split bars
    ctx.fillStyle = "#17334a";
    ctx.fillRect(40, 30, W - 60, H - 60);
    ctx.fillStyle = "#72efdd";
    ctx.fillRect(40, 30, (W - 60) * pvPct, H - 60);
    ctx.fillStyle = "#4cc9f0";
    ctx.fillRect(40 + (W - 60) * pvPct, 30, (W - 60) * tvP, H - 60);
    ctx.fillStyle = "#9cb4c9"; ctx.font = "12px ui-monospace, monospace";
    ctx.fillText("PV(FCFF): " + fmt(pv, { currency: true, decimals: 0, suffix: "M" }) + " (" + (pvPct * 100).toFixed(1) + "%)", 48, 24);
    ctx.fillText("PV(Terminal): " + fmt(tv, { currency: true, decimals: 0, suffix: "M" }) + " (" + (tvP * 100).toFixed(1) + "%)", 48, H - 12);

    // Counterfactual TV method comparison marker
    const baseMethod = (document.getElementById("tvMultiple")?.checked ? "multiple" : "perpetuity");
    let cfTv = tv;
    if (baseMethod === "perpetuity") {
      // compare to exit multiple with current tvMultipleVal
      const mult = Number(document.getElementById("tvMultipleVal")?.value || 12);
      const fcffN1_cf = (result.series.fcff[result.params.years] || 0) * (1 + result.params.termGrowth);
      const tvVal = Math.max(0, mult * fcffN1_cf);
      cfTv = tvVal / Math.pow(1 + result.params.wacc, result.params.years);
    } else {
      // compare to perpetuity with current g
      const fcffN = result.series.fcff[result.params.years] || 0;
      const tvVal = (result.params.wacc > result.params.termGrowth) ? (fcffN * (1 + result.params.termGrowth) / (result.params.wacc - result.params.termGrowth)) : 0;
      cfTv = tvVal / Math.pow(1 + result.params.wacc, result.params.years);
    }
    const cfPct = Math.max(0, Math.min(1, cfTv / Math.max(1e-9, pv + cfTv)));
    // draw thin outline marker for counterfactual split
    ctx.strokeStyle = "#ffd166"; ctx.lineWidth = 2;
    const xCFStart = 40 + (W - 60) * (1 - cfPct); // pv proportion = 1-cfPct
    ctx.strokeRect(40, 30, (W - 60) * (1 - cfPct), H - 60);
    ctx.strokeRect(xCFStart, 30, (W - 60) * cfPct, H - 60);

    tornadoCanvas.style.display = "none";
  } else if (activeRight === "tornado") {
    // Minimal working tornado chart using +/- deltas for key drivers
    tornadoCanvas.style.display = "block";
    const ctx = tornadoCanvas.getContext("2d");
    const W=tornadoCanvas.width, H=tornadoCanvas.height;
    ctx.clearRect(0,0,W,H);
    const metric = $("tornadoMetric")?.value || "perShare";
    const drivers = [
      { key:"wacc", label:"WACC (%)", delta: Number($("tornadoWacc")?.value) || 1.0, percent:true },
      { key:"termGrowth", label:"Terminal g (%)", delta: Number($("tornadoG")?.value) || 0.5, percent:true },
      { key:"ebitMargin", label:"EBIT Margin (%)", delta: Number($("tornadoMargin")?.value) || 1.0, percent:true },
      { key:"salesToCap", label:"Sales-to-Capital", delta: Number($("tornadoS2C")?.value) || 0.2, percent:false }
    ];
    const baseResult = dcfEngine(inputs).totals;
    const base = baseResult[metric];
    const bars = drivers.map(d=>{
      const inc = {...inputs, [d.key]: d.percent ? (inputs[d.key]+d.delta/100) : (inputs[d.key]+d.delta) };
      const dec = {...inputs, [d.key]: d.percent ? (inputs[d.key]-d.delta/100) : (inputs[d.key]-d.delta) };
      const up = dcfEngine(inc).totals[metric];
      const dn = dcfEngine(dec).totals[metric];
      const low = Math.min(up, dn), high = Math.max(up, dn);
      return { label:d.label, low, high };
    });
    const minV = Math.min(...bars.map(b=>b.low), base);
    const maxV = Math.max(...bars.map(b=>b.high), base);
    const pad = (maxV-minV)*0.2 || 1;
    const left=120, right=W-20, top=20, rowH = (H-40)/drivers.length;
    const X = (v)=> left + (right-left)*((v-(minV-pad))/((maxV - minV + 2*pad) || 1));
    // base line
    ctx.strokeStyle="#35546b"; ctx.lineWidth=1.5;
    ctx.beginPath(); ctx.moveTo(X(base), top); ctx.lineTo(X(base), H-20); ctx.stroke();
    ctx.font="12px ui-monospace, monospace";
    bars.forEach((b, i)=>{
      const y = top + i*rowH + rowH/3;
      ctx.fillStyle="#4cc9f0";
      ctx.fillRect(Math.min(X(b.low), X(b.high)), y, Math.abs(X(b.high)-X(b.low)), rowH/3);
      ctx.fillStyle="#cfe3f7";
      ctx.fillText(b.label, 10, y + rowH/3);
      ctx.fillStyle="#9cb4c9";
      ctx.fillText(`${metric === "perShare" ? "$" : ""}${b.low.toFixed(2)} - ${metric === "perShare" ? "$" : ""}${b.high.toFixed(2)}`, right-180, y + rowH/3);
    });
  }

  // Update TV mini panel
  try {
    const methodStr = (document.getElementById("tvMultiple")?.checked ? "Exit Multiple" : "Perpetuity");
    $("tvInfoMethod").textContent = methodStr;
    $("tvInfoPVTV").textContent = fmt(result.totals.pvTv, { currency: true, decimals: 0, suffix: "M" });
    $("tvInfoPVPV").textContent = fmt(result.totals.sumPvFcff, { currency: true, decimals: 0, suffix: "M" });
    $("tvInfoPct").textContent = isFinite(result.totals.tvPct) ? (result.totals.tvPct * 100).toFixed(1) + "%" : "—";
    const fcffN1 = (result.series.fcff[result.params.years] || 0) * (1 + result.params.termGrowth);
    const impliedMultWrap = $("tvInfoImpliedMultWrap");
    const impliedGWrap = $("tvInfoImpliedGWrap");
    if (methodStr === "Perpetuity") {
      // implied multiple = TV / FCFF_{n+1} (using undiscounted TV)
      const tvUndisc = (result.params.wacc > result.params.termGrowth) ? (fcffN1 / (result.params.wacc - result.params.termGrowth)) : NaN;
      const mult = isFinite(tvUndisc) && fcffN1 > 0 ? tvUndisc / fcffN1 : NaN;
      if (impliedMultWrap) impliedMultWrap.style.display = "";
      if (impliedGWrap) impliedGWrap.style.display = "none";
      $("tvInfoImpliedMult").textContent = isFinite(mult) ? mult.toFixed(2) + "x" : "—";
    } else {
      // implied g so that perpetuity pvTv matches current pvTv (bisection on g)
      if (impliedMultWrap) impliedMultWrap.style.display = "none";
      if (impliedGWrap) impliedGWrap.style.display = "";
      const targetPvTv = result.totals.pvTv;
      const w = result.params.wacc;
      const fcffN = result.series.fcff[result.params.years] || 0;
      const n = result.params.years;
      function pvTvPerp(g) {
        if (w <= g) return NaN;
        const tvUnd = fcffN * (1 + g) / (w - g);
        return tvUnd / Math.pow(1 + w, n);
      }
      let lo = Math.max(-0.01, 0), hi = Math.max(0, w - 0.0005), sol = NaN;
      for (let it = 0; it < 60; it++) {
        const mid = 0.5 * (lo + hi);
        const val = pvTvPerp(mid);
        if (!isFinite(val)) { hi = mid; continue; }
        if (Math.abs(val - targetPvTv) < 1e-6) { sol = mid; break; }
        if (val > targetPvTv) hi = mid; else lo = mid;
        sol = mid;
      }
      $("tvInfoImpliedG").textContent = isFinite(sol) ? (sol * 100).toFixed(2) + "%" : "—";
    }
  } catch {}

  const end = performance.now();
  $("statusPill").textContent = "Done";
  logLine(`<span class="tag">EV</span> ${fmt(ev, { currency: true, decimals: 0, suffix: "M" })} | <span class="tag">Equity</span> ${fmt(equity, { currency: true, decimals: 0, suffix: "M" })} | <span class="tag">Per Share</span> $${perShare.toFixed(2)}`);
  logLine(`<span class="tag">TV%</span> ${(tvPct * 100).toFixed(1)}% of EV | Runtime ${(end - start).toFixed(1)} ms`);
}

/**
 * Solver modal wiring and implementation
 * - Supports solving for implied WACC or implied Terminal g to reach target per-share.
 * - Uses bisection with 60 iterations max and safe guards.
 */
let lastFocusedElement = null;
function openSolver() {
  const m = $("solverModal");
  if (m) {
    m.style.display = "flex";
    lastFocusedElement = document.activeElement;
    const firstFocusable = m.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    firstFocusable?.focus();
    m.addEventListener("keydown", handleSolverTrapFocus);
  }
}
function closeSolver() {
  const m = $("solverModal");
  if (m) {
    m.style.display = "none";
    m.removeEventListener("keydown", handleSolverTrapFocus);
    lastFocusedElement?.focus();
  }
}
function handleSolverTrapFocus(e) {
  const m = $("solverModal");
  if (!m) return;
  const focusable = Array.from(m.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'));
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (e.key === "Escape") {
    closeSolver();
  }
  if (e.key === "Tab") {
    if (e.shiftKey) {
      if (document.activeElement === first) {
        last.focus();
        e.preventDefault();
      }
    } else {
      if (document.activeElement === last) {
        first.focus();
        e.preventDefault();
      }
    }
  }
}
$("openSolver")?.addEventListener("click", openSolver);
$("closeSolver")?.addEventListener("click", closeSolver);
$("runSolver")?.addEventListener("click", () => {
  try {
    const target = Number($("solverTarget")?.value || 0);
    const type = $("solverType")?.value || "wacc"; // "wacc" | "termGrowth"
    const loIn = Number($("solverMin")?.value || (type==="wacc"?5:0));
    const hiIn = Number($("solverMax")?.value || (type==="wacc"?15:10));
    const logEl = $("solverLog"); if (logEl) logEl.innerHTML = "";
    const statusEl = $("solverStatus");
    const inputs = readInputs();

    // Helper to append lines to solver terminal
    const slog = (txt) => {
      const d = document.createElement("div");
      d.textContent = txt;
      d.className = "term-line";
      logEl?.appendChild(d);
      logEl && (logEl.scrollTop = logEl.scrollHeight);
    };

    const unit = (type==="wacc" ? "%" : "%");
    const toModel = (x) => (type==="wacc" || type==="termGrowth") ? x/100 : x;

    let lo = loIn, hi = hiIn;
    if (!(isFinite(target) && target > 0)) { statusEl && (statusEl.textContent = "Invalid target"); return; }
    if (!(isFinite(lo) && isFinite(hi) && lo < hi)) { statusEl && (statusEl.textContent = "Invalid bounds"); return; }

    const t0 = performance.now();
    // Define evaluator f(x) = perShare(x) - target
    function perShareAt(xPct) {
      const v = toModel(xPct);
      const p = { ...inputs };
      if (type === "wacc") p.wacc = v;
      else if (type === "termGrowth") p.termGrowth = v;
      const res = dcfEngine(p).totals.perShare;
      return res;
    }

    // Guard: for perpetuity method, require wacc>g during eval
    const maxIter = 60;
    let bestX = NaN, bestDiff = Infinity;
    let leftPS = perShareAt(lo), rightPS = perShareAt(hi);
    slog(`Initial: x in [${lo}${unit}, ${hi}${unit}] → PS(lo)=${isFinite(leftPS)?leftPS.toFixed(2):"—"}, PS(hi)=${isFinite(rightPS)?rightPS.toFixed(2):"—"}`);
    // Bisection
    for (let it = 0; it < maxIter; it++) {
      const mid = 0.5 * (lo + hi);
      const ps = perShareAt(mid);
      const diff = ps - target;
      if (Math.abs(diff) < bestDiff) { bestDiff = Math.abs(diff); bestX = mid; }
      slog(`Iter ${it+1}: x=${mid.toFixed(4)}${unit}, ps=$${isFinite(ps)?ps.toFixed(4):"—"}, diff=${isFinite(diff)?diff.toFixed(4):"—"}`);
      if (!isFinite(ps)) {
        // If invalid (e.g., g>=w), move bounds towards feasibility
        if (type === "termGrowth") { hi = mid; } else { lo = mid; }
        continue;
      }
      if (diff === 0 || Math.abs(diff) < 1e-4) { bestX = mid; break; }
      // Decide side: if ps > target, need to increase discount (for WACC) or reduce g
      if (type === "wacc") {
        if (ps > target) lo = mid; else hi = mid;
      } else {
        if (ps > target) hi = mid; else lo = mid;
      }
    }
    const t1 = performance.now();
    const solvedPS = perShareAt(bestX);
    statusEl && (statusEl.textContent = `Solved ${type}: ${bestX.toFixed(4)}${unit} → $${isFinite(solvedPS)?solvedPS.toFixed(2):"—"} • ${(t1-t0).toFixed(1)} ms`);
    slog(`Done. Best ${type}=${bestX.toFixed(4)}${unit}, per-share=$${isFinite(solvedPS)?solvedPS.toFixed(4):"—"}. Runtime ${(t1-t0).toFixed(1)} ms`);
  } catch (e) {
    const statusEl = $("solverStatus");
    statusEl && (statusEl.textContent = "Solver error");
  }
});

/** Heatmap/tornado export helpers */
function exportCanvasPNG(canvas, name) {
  if (!canvas) return;
  const url = canvas.toDataURL("image/png");
  const a = document.createElement("a");
  a.href = url; a.download = name;
  document.body.appendChild(a); a.click(); a.remove();
}
$("exportHeatmap")?.addEventListener("click", () => {
  const inputs = readInputs();
  // Determine active right tab for filename suffix
  const rightTabs = document.querySelectorAll('.tabs')[1];
  const activeRight = rightTabs?.querySelector('.tab.active')?.getAttribute('data-tab') || "sens";
  const suffix = activeRight === "twoWay" ? "grid" : activeRight === "tvm" ? "tvmix" : "heatmap";
  exportCanvasPNG($("heatmap"), `${inputs.ticker || "chart"}-${suffix}.png`);
});
$("exportTornado")?.addEventListener("click", () => {
  const inputs = readInputs();
  exportCanvasPNG($("tornadoChart"), `${inputs.ticker || "chart"}-tornado.png`);
});

/**
 * Copy Link
 */
$("copyLink")?.addEventListener("click", async () => {
  try {
    const inputs = readInputs();
    // include tv method/multiple in params for URL parity
    const tvMethod = (document.getElementById("tvMultiple")?.checked ? "multiple" : "perpetuity");
    const tvMultipleVal = Number(document.getElementById("tvMultipleVal")?.value || 12);

    // include MC settings (read from fields first, fallback to saved)
    const s = (() => { try { return JSON.parse(localStorage.getItem("valor:mc-settings") || "{}"); } catch { return {}; }})();
    const trials = $("mcTrials")?.value || s.trials;
    const volPP = $("mcVol")?.value || s.volPP;
    const seedStr = $("mcSeed")?.value || s.seedStr;
    const marginVolPP = $("mcMarginVol")?.value || s.marginVolPP;
    const s2cVolPct = $("mcS2CVol")?.value || s.s2cVolPct;
    const corrGM = $("mcCorrGM")?.value || s.corrGM;

    const q = encodeStateToQuery(inputs);
    const parts = [
      `${q}`,
      tvMethod === "multiple" ? `tvMethod=multiple&tvMultipleVal=${encodeURIComponent(tvMultipleVal)}` : `tvMethod=perpetuity`
    ];
    if (trials !== undefined && trials !== "") parts.push(`mcTrials=${encodeURIComponent(trials)}`);
    if (volPP !== undefined && volPP !== "") parts.push(`mcVolPP=${encodeURIComponent(volPP)}`);
    if (seedStr !== undefined && seedStr !== "") parts.push(`mcSeedStr=${encodeURIComponent(seedStr)}`);
    if (marginVolPP !== undefined && marginVolPP !== "") parts.push(`mcMarginVolPP=${encodeURIComponent(marginVolPP)}`);
    if (s2cVolPct !== undefined && s2cVolPct !== "") parts.push(`mcS2CVolPct=${encodeURIComponent(s2cVolPct)}`);
    if (corrGM !== undefined && corrGM !== "") parts.push(`mcCorrGM=${encodeURIComponent(corrGM)}`);
    const url = `${location.origin}${location.pathname}?${parts.join("&")}`;
    await navigator.clipboard.writeText(url);
    logLine("Link copied to clipboard.");
    $("statusPill").textContent = "Link copied";
  } catch (e) {
    logLine("Failed to copy link: " + (e?.message || e), "err");
  }
});

/**
 * Export CSV
 */
$("exportCSV")?.addEventListener("click", () => {
  try {
    const inputs = readInputs();
    const tvMethod = (document.getElementById("tvMultiple")?.checked ? "multiple" : "perpetuity");
    const tvMultipleVal = Number(document.getElementById("tvMultipleVal")?.value || 12);
    const res = dcfEngine({ ...inputs, tvMethod, tvMultipleVal });
    const csv = toCSV(res.series, res.totals, res.params);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `${inputs.ticker || "output"}-dcf-series.csv`;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    logLine("Exported CSV.");
  } catch (e) {
    logLine("Failed to export CSV: " + (e?.message || e), "err");
  }
});

// Backend round-trip buttons
$("sendRun")?.addEventListener("click", async () => {
  const inputs = readInputs();
  const tvMethod = (document.getElementById("tvMultiple")?.checked ? "multiple" : "perpetuity");
  const tvMultipleVal = Number(document.getElementById("tvMultipleVal")?.value || 12);
  const res = dcfEngine({ ...inputs, tvMethod, tvMultipleVal });

  // TV method audit
  const years = res.params.years;
  const fcffN = res.series.fcff[years] || 0;
  const fcffN1 = fcffN * (1 + res.params.termGrowth);
  const baseMethod = tvMethod;
  let tvUnd_base = 0, tvUnd_cf = 0, pvTv_base = res.totals.pvTv, pvTv_cf = 0;
  if (baseMethod === "perpetuity") {
    tvUnd_base = res.params.wacc > res.params.termGrowth ? (fcffN1 / (res.params.wacc - res.params.termGrowth)) : 0;
    tvUnd_cf = Math.max(0, tvMultipleVal * fcffN1);
  } else {
    tvUnd_base = Math.max(0, (res.params.tvMultipleVal || tvMultipleVal) * fcffN1);
    tvUnd_cf = res.params.wacc > res.params.termGrowth ? (fcffN1 / (res.params.wacc - res.params.termGrowth)) : 0;
  }
  pvTv_cf = tvUnd_cf / Math.pow(1 + res.params.wacc, years);
  const ev_cf = res.totals.sumPvFcff + pvTv_cf;

  const payload = {
    inputs: { ...inputs, tvMethod, tvMultipleVal },
    result: res,
    tvAudit: {
      baseMethod,
      counterfactualMethod: baseMethod === "perpetuity" ? "multiple" : "perpetuity",
      fcffN1,
      tvUndiscounted_base: tvUnd_base,
      tvUndiscounted_cf: tvUnd_cf,
      pvTv_base,
      pvTv_cf,
      ev_base: res.totals.ev,
      ev_cf
    }
  };
  const r = await safeFetch("/api/save-run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (r.ok) logLine(`Sent run to backend • ${backend.lastLatencyMs?.toFixed(0)} ms`);
  else logLine("Backend not available or failed to save run.", "warn");
});

$("loadLastRun")?.addEventListener("click", async () => {
  const r = await safeFetch("/api/last-run", { method: "GET", cache: "no-store" });
  if (!r.ok) { logLine("Backend not available or no last run.", "warn"); return; }
  try {
    const data = await r.res.json();
    const obj = data?.inputs ? data : (Array.isArray(data) ? data[0] : null);
    if (!obj?.inputs) throw new Error("Invalid payload");
    applyScenarioInputs(obj.inputs);
    // apply tv method if present
    const tvPerp = document.getElementById("tvPerp");
    const tvMultiple = document.getElementById("tvMultiple");
    const tvMultipleVal = document.getElementById("tvMultipleVal");
    if (obj.inputs.tvMethod === "multiple") {
      tvMultiple && (tvMultiple.checked = true);
      tvPerp && (tvPerp.checked = false);
      if (tvMultipleVal) tvMultipleVal.disabled = false;
      if (typeof obj.inputs.tvMultipleVal !== "undefined" && tvMultipleVal) tvMultipleVal.value = String(obj.inputs.tvMultipleVal);
    } else {
      tvPerp && (tvPerp.checked = true);
      tvMultiple && (tvMultiple.checked = false);
      if (tvMultipleVal) tvMultipleVal.disabled = true;
    }
    logLine("Loaded last run from backend.");
    run();
  } catch (e) {
    logLine("Failed to parse last run payload.", "err");
  }
});

/**
 * Scenarios: Save/Apply/Delete/Export/Import
 */
function currentScenarioName(inputs) {
  return `${(inputs.ticker || "SCN").toUpperCase()} • ${((inputs.wacc*100)||0).toFixed(1)}% / g ${((inputs.termGrowth*100)||0).toFixed(1)}% • ${inputs.years}y`;
}
$("saveScenario")?.addEventListener("click", () => {
  const inputs = readInputs();
  const list = loadScenarios();
  const name = prompt("Scenario name:", currentScenarioName(inputs));
  if (name === null) return;

  // Attach MC snapshot to scenario for reproducibility
  const saved = (() => { try { return JSON.parse(localStorage.getItem("valor:mc-settings") || "{}"); } catch { return {}; }})();
  const entry = {
    name: String(name || currentScenarioName(inputs)),
    inputs,
    mc: {
      trials: Number($("mcTrials")?.value || saved.trials || 1000),
      volPP: Number($("mcVol")?.value || saved.volPP || 2.0),
      seedStr: String($("mcSeed")?.value || saved.seedStr || ""),
      marginVolPP: Number($("mcMarginVol")?.value || saved.marginVolPP || $("mcVol")?.value || 2.0),
      s2cVolPct: Number($("mcS2CVol")?.value || saved.s2CVolPct || saved.s2cVolPct || 5),
      corrGM: Number($("mcCorrGM")?.value || saved.corrGM || 0.3)
    }
  };
  const merged = dedupeScenarios(list.concat([entry]));
  saveScenarios(merged);
  refreshScenarioDropdown();
  logLine(`Saved scenario "${entry.name}".`);
});
$("applyScenario")?.addEventListener("click", () => {
  const sel = $("scenarioSelect");
  const idx = Number(sel?.value || -1);
  const list = loadScenarios();
  if (!(idx >= 0 && idx < list.length)) { logLine("Select a scenario to apply.", "warn"); return; }
  const scn = list[idx];
  applyScenarioInputs(scn.inputs);
  // Apply MC extras if present (prefill to ensure identical runs)
  if (scn.mc && typeof scn.mc === "object") {
    if ($("mcTrials") && isFinite(Number(scn.mc.trials))) $("mcTrials").value = String(scn.mc.trials);
    if ($("mcVol") && isFinite(Number(scn.mc.volPP))) $("mcVol").value = String(scn.mc.volPP);
    if ($("mcSeed") && typeof scn.mc.seedStr === "string") $("mcSeed").value = String(scn.mc.seedStr);
    if ($("mcMarginVol") && isFinite(Number(scn.mc.marginVolPP))) $("mcMarginVol").value = String(scn.mc.marginVolPP);
    if ($("mcS2CVol") && isFinite(Number(scn.mc.s2cVolPct))) $("mcS2CVol").value = String(scn.mc.s2cVolPct);
    if ($("mcCorrGM") && isFinite(Number(scn.mc.corrGM))) $("mcCorrGM").value = String(Math.max(-0.99, Math.min(0.99, Number(scn.mc.corrGM))));
    // Also persist to valor:mc-settings for consistency
    try {
      const obj = {
        trials: Number($("mcTrials")?.value || 1000),
        volPP: Number($("mcVol")?.value || 2.0),
        seedStr: String($("mcSeed")?.value || ""),
        marginVolPP: Number($("mcMarginVol")?.value || $("mcVol")?.value || 2.0),
        s2cVolPct: Number($("mcS2CVol")?.value || 5),
        corrGM: Math.max(-0.99, Math.min(0.99, Number($("mcCorrGM")?.value || 0.3)))
      };
      localStorage.setItem("valor:mc-settings", JSON.stringify(obj));
    } catch {}
  }
  logLine(`Applied scenario "${scn.name || ("Scenario " + (idx+1))}".`);
  run();
});
$("deleteScenario")?.addEventListener("click", () => {
  const sel = $("scenarioSelect");
  const idx = Number(sel?.value || -1);
  const list = loadScenarios();
  if (!(idx >= 0 && idx < list.length)) { logLine("Select a scenario to delete.", "warn"); return; }
  const name = list[idx].name || ("Scenario " + (idx+1));
  list.splice(idx, 1);
  saveScenarios(list);
  refreshScenarioDropdown();
  logLine(`Deleted scenario "${name}".`);
});
$("exportScenarios")?.addEventListener("click", () => {
  const list = loadScenarios();
  const payload = { _schema: "valor:scenarios@1", scenarios: list };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "valor-scenarios.json";
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
  logLine(`Exported ${list.length} scenarios (with schema tag).`);
});
$("importScenarios")?.addEventListener("click", () => {
  $("importScenariosFile")?.click();
});
$("importScenariosFile")?.addEventListener("change", async (e) => {
  try {
    const file = e.target?.files?.[0];
    if (!file) return;
    const text = await file.text();
    const parsed = JSON.parse(text);
    const arr = Array.isArray(parsed) ? parsed : (Array.isArray(parsed?.scenarios) ? parsed.scenarios : null);
    if (!Array.isArray(arr)) throw new Error("Expected an array of scenarios.");
    const cleaned = arr.filter(s => s && typeof s === "object" && s.inputs);
    const merged = dedupeScenarios(loadScenarios().concat(cleaned));
    saveScenarios(merged);
    refreshScenarioDropdown();
    logLine(`Imported ${cleaned.length} scenarios.`);
  } catch (err) {
    logLine("Failed to import scenarios: " + (err?.message || err), "err");
  } finally {
    if (e.target) e.target.value = "";
  }
});

// Existing backend round-trip buttons
$("sendScenarios")?.addEventListener("click", async () => {
  const list = loadScenarios();
  const r = await safeFetch("/api/save-scenarios", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(list)
  });
  if (r.ok) logLine(`Sent ${list.length} scenarios to backend • ${backend.lastLatencyMs?.toFixed(0)} ms`);
  else logLine("Backend not available or failed to save scenarios.", "warn");
});

$("fetchScenarios")?.addEventListener("click", async () => {
  const r = await safeFetch("/api/scenarios", { method: "GET", cache: "no-store" });
  if (!r.ok) { logLine("Backend not available or no scenarios.", "warn"); return; }
  try {
    const arr = await r.res.json();
    if (!Array.isArray(arr)) throw new Error("Invalid scenarios payload");
    // basic validation
    const cleaned = arr.filter(s => s && typeof s === "object" && s.inputs);
    const merged = loadScenarios().concat(cleaned);
    saveScenarios(merged);
    refreshScenarioDropdown();
    logLine(`Fetched ${cleaned.length} scenarios from backend.`);
  } catch (e) {
    logLine("Failed to parse scenarios from backend.", "err");
  }
});

// Overlay series cache
let overlaySeriesCache = null; // { series, label }
$("overlaySave")?.addEventListener("click", () => {
  const inputs = readInputs();
  const res = dcfEngine(inputs);
  overlaySeriesCache = {
    series: res.series,
    label: `Overlay ${((inputs.wacc * 100).toFixed(1))}% / g ${((inputs.termGrowth * 100).toFixed(1))}%`,
  };
  $("legendOverlay").style.display = "";
  $("overlayLabel").textContent = overlaySeriesCache.label;
  logLine("Overlay saved.");
  run();
});
$("overlayClear")?.addEventListener("click", () => {
  overlaySeriesCache = null;
  $("legendOverlay").style.display = "none";
  logLine("Overlay cleared.");
  run();
});

/**
 * MC settings initialization: populate controls from persisted settings
 */
(function initMCSettings() {
  try {
    // 1) Apply persisted settings if present
    const saved = localStorage.getItem("valor:mc-settings");
    if (saved) {
      const s = JSON.parse(saved);
      if (s && typeof s === "object") {
        if ($("mcTrials") && isFinite(Number(s.trials))) $("mcTrials").value = String(s.trials);
        if ($("mcVol") && isFinite(Number(s.volPP))) $("mcVol").value = String(s.volPP);
        if ($("mcSeed") && typeof s.seedStr === "string") $("mcSeed").value = String(s.seedStr);
        if ($("mcMarginVol") && isFinite(Number(s.marginVolPP))) $("mcMarginVol").value = String(s.marginVolPP);
        if ($("mcS2CVol") && isFinite(Number(s.s2cVolPct))) $("mcS2CVol").value = String(s.s2cVolPct);
        if ($("mcCorrGM") && isFinite(Number(s.corrGM))) $("mcCorrGM").value = String(Math.max(-0.99, Math.min(0.99, Number(s.corrGM))));
      }
    }
    // 2) Deep-link: parse mc params from URL and apply/persist
    const q = new URLSearchParams(location.search);
    let changed = false;
    const clampCorr = (x) => Math.max(-0.99, Math.min(0.99, x));
    if (q.has("mcMarginVolPP") && $("mcMarginVol")) { $("mcMarginVol").value = String(q.get("mcMarginVolPP")); changed = true; }
    if (q.has("mcS2CVolPct") && $("mcS2CVol")) { $("mcS2CVol").value = String(q.get("mcS2CVolPct")); changed = true; }
    if (q.has("mcCorrGM") && $("mcCorrGM")) { $("mcCorrGM").value = String(clampCorr(Number(q.get("mcCorrGM")))); changed = true; }

    // Also accept trials, volPP, seedStr via deep-link (write-back to persist for reproducibility)
    if (q.has("mcTrials") && $("mcTrials")) { $("mcTrials").value = String(q.get("mcTrials")); changed = true; }
    if (q.has("mcVolPP") && $("mcVol")) { $("mcVol").value = String(q.get("mcVolPP")); changed = true; }
    if (q.has("mcSeedStr") && $("mcSeed")) { $("mcSeed").value = String(q.get("mcSeedStr")); changed = true; }

    if (changed) {
      // Write to valor:mc-settings to keep consistency
      const trials = Number($("mcTrials")?.value || 1000);
      const volPP = Number($("mcVol")?.value || 2.0);
      const seedStr = String($("mcSeed")?.value || "");
      const marginVolPP = Number($("mcMarginVol")?.value || volPP);
      const s2cVolPct = Number($("mcS2CVol")?.value || 5);
      const corrGM = clampCorr(Number($("mcCorrGM")?.value || 0.3));
      const obj = { trials, volPP, seedStr, marginVolPP, s2cVolPct, corrGM };
      try { localStorage.setItem("valor:mc-settings", JSON.stringify(obj)); } catch {}
    }
  } catch {}
})();

// Notes persistence
(function wireNotes() {
  const ta = $("notesArea");
  if (!ta) return;
  const getTicker = () => ($("ticker")?.value || "SAMPLE");
  // initial load
  ta.value = loadNotes(getTicker());
  ta.addEventListener("input", () => { saveNotes(getTicker(), ta.value); });
  // save/clear buttons
  $("saveNotes")?.addEventListener("click", () => { saveNotes(getTicker(), ta.value); logLine("Notes saved."); });
  $("clearNotes")?.addEventListener("click", () => { ta.value = ""; saveNotes(getTicker(), ""); logLine("Notes cleared."); });
  // when ticker changes, swap notes
  $("ticker")?.addEventListener("input", () => { ta.value = loadNotes(getTicker()); });
})();

/** Link hints for accessibility: connect hints to inputs via aria-describedby */
(function a11yHints(){
  try {
    const link = (inputId, hintTextMatch) => {
      const input = document.getElementById(inputId);
      if (!input) return;
      // find the immediate sibling hint span that contains the match text
      const parent = input.parentElement?.parentElement || input.parentElement;
      let hintSpan = null;
      if (parent) {
        hintSpan = Array.from(parent.querySelectorAll(".hint")).find(s => s.textContent?.toLowerCase().includes(hintTextMatch));
      }
      if (!hintSpan) {
        // broader search within the row
        const container = document;
        hintSpan = Array.from(container.querySelectorAll(".hint")).find(s => s.textContent?.toLowerCase().includes(hintTextMatch));
      }
      if (hintSpan) {
        if (!hintSpan.id) hintSpan.id = `${inputId}-hint`;
        input.setAttribute("aria-describedby", hintSpan.id);
      }
    };
    link("mcMarginVol", "margin vol");
    link("mcS2CVol", "s2c vol");
    link("mcCorrGM", "corr(g");
  } catch {}
})();

// Tab state persistence
function saveTabState(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch (e) {
    console.warn("Failed to save tab state:", e);
  }
}

function applyTabState() {
  try {
    const leftTab = localStorage.getItem("valor:left-tab");
    const rightTab = localStorage.getItem("valor:right-tab");

    if (leftTab) {
      const container = document.querySelector('.tabs[aria-label="Left data views"]');
      const tabToActivate = container?.querySelector(`[data-tab="${leftTab}"]`);
      if (tabToActivate) {
        container.querySelectorAll(".tab").forEach(b => {
          b.classList.remove("active");
          b.setAttribute("aria-selected", "false");
        });
        tabToActivate.classList.add("active");
        tabToActivate.setAttribute("aria-selected", "true");
      }
    }

    if (rightTab) {
      const container = document.querySelector('.tabs[aria-label="Right data views"]');
      const tabToActivate = container?.querySelector(`[data-tab="${rightTab}"]`);
      if (tabToActivate) {
        container.querySelectorAll(".tab").forEach(b => {
          b.classList.remove("active");
          b.setAttribute("aria-selected", "false");
        });
        tabToActivate.classList.add("active");
        tabToActivate.setAttribute("aria-selected", "true");
      }
    }
  } catch (e) {
    console.warn("Failed to apply tab state:", e);
  }
}
applyTabState();


// Export chart
$("exportChart")?.addEventListener("click", () => {
  const canvas = $("fcfChart");
  const url = canvas.toDataURL("image/png");
  const a = document.createElement("a");
  a.href = url; a.download = "valor-chart.png";
  document.body.appendChild(a); a.click(); a.remove();
});

// Tabs wiring
document.querySelector('.tabs[aria-label="Left data views"]')?.addEventListener("click", (e) => {
  const btn = e.target.closest(".tab");
  if (!btn) return;
  const container = e.currentTarget;
  container.querySelectorAll(".tab").forEach(b => {
    b.classList.remove("active");
    b.setAttribute("aria-selected", "false");
  });
  btn.classList.add("active");
  btn.setAttribute("aria-selected", "true");
  const mode = btn.getAttribute("data-tab");
  saveTabState("valor:left-tab", mode);
  const titles = { fcf: "Projected FCFF", rev: "Projected Revenue", margin: "Projected EBIT (margin path)", pv: "PV Contributions by Year" };
  $("seriesTitle").textContent = titles[mode] || "Projected FCFF";
  run();
});
document.querySelector('.tabs[aria-label="Right data views"]')?.addEventListener("click", (e) => {
  const btn = e.target.closest(".tab");
  if (!btn) return;
  const container = e.currentTarget;
  container.querySelectorAll(".tab").forEach(b => {
    b.classList.remove("active");
    b.setAttribute("aria-selected", "false");
  });
  btn.classList.add("active");
  btn.setAttribute("aria-selected", "true");
  const mode = btn.getAttribute("data-tab");
  saveTabState("valor:right-tab", mode);
  const titles = { sens: "Sensitivity: WACC vs Terminal Growth", twoWay: "Two-way Grid (X vs Y -> Per Share)", tvm: "Terminal vs PV Split", tornado: "Tornado" };
  $("sensTitle").textContent = titles[mode] || "Sensitivity";
  run();
});

/**
 * Buttons and CLI wiring
 */
$("runModel")?.addEventListener("click", run);
$("btnRunLeft")?.addEventListener("click", run);
$("presetExample")?.addEventListener("click", () => { preset(); logLine("Preset loaded."); });
$("btnPresetLeft")?.addEventListener("click", () => { preset(); logLine("Preset loaded."); });
$("resetForm")?.addEventListener("click", () => { resetForm(); logLine("Reset to defaults."); });
$("btnResetLeft")?.addEventListener("click", () => { resetForm(); logLine("Reset to defaults."); });

$("resetAll")?.addEventListener("click", () => {
  if (confirm("Are you sure you want to reset all saved scenarios, notes, and settings? This cannot be undone.")) {
    try {
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith("valor:")) {
          localStorage.removeItem(key);
        }
      });
      logLine("All settings, scenarios, and notes have been reset.");
      resetForm();
      refreshScenarioDropdown();
    } catch (e) {
      logLine("Failed to reset all settings.", "err");
    }
  }
});

// Keyboard
document.addEventListener("keydown", (e) => {
  // Avoid intercepting Enter when focused on CLI input
  const active = document.activeElement;
  const isCli = active && (active.id === "cliInput");
  if (!isCli && e.key === "Enter") run();
  if (e.key.toLowerCase() === "p") { preset(); logLine("Preset loaded (key)."); }
});

// CLI implementation (restored)
const cliOut = $("cliOutput");
const cliIn = $("cliInput");
const cliExecBtn = $("cliExec");
function cliPrint(msg, cls="") {
  if (!cliOut) return;
  const line = document.createElement("div");
  line.className = "cli-line" + (cls ? " " + cls : "");
  line.textContent = msg;
  cliOut.appendChild(line);
  cliOut.scrollTop = cliOut.scrollHeight;
}
function cliHelp() {
  cliPrint("Commands:");
  cliPrint("  help                         Show this help");
  cliPrint("  run                          Run DCF with current inputs");
  cliPrint("  set <key> <value>            Set an input (e.g., wacc 8.5, termGrowth 2.0, years 8)");
  cliPrint("  get <key>                    Get current input value");
  cliPrint("  eval ps                      Print per-share");
  cliPrint("  mc <trials> <vol_pp>         Monte Carlo (pp = percentage points)");
  cliPrint("  grid <x> <min> <max> <y> <min> <max>   Two-way grid");
  cliPrint("  export json|csv              Export data");
}
function setInput(key, value) {
  const map = {
    ticker:"ticker", revenue:"revenue", growthY1:"growthY1", growthDecay:"growthDecay", years:"years",
    termGrowth:"termGrowth", ebitMargin:"ebitMargin", taxRate:"taxRate", salesToCap:"salesToCap",
    wacc:"wacc", shares:"shares", netDebt:"netDebt"
  };
  const elId = map[key];
  if (!elId) return false;
  const el = $(elId);
  if (!el) return false;
  const num = Number(value);
  if (!isFinite(num) && key !== "ticker") return false;
  el.value = key === "ticker" ? String(value) : String(num);
  return true;
}
function getInputValue(key) {
  const map = {
    ticker:"ticker", revenue:"revenue", growthY1:"growthY1", growthDecay:"growthDecay", years:"years",
    termGrowth:"termGrowth", ebitMargin:"ebitMargin", taxRate:"taxRate", salesToCap:"salesToCap",
    wacc:"wacc", shares:"shares", netDebt:"netDebt"
  };
  const elId = map[key];
  const el = elId ? $(elId) : null;
  return el ? el.value : undefined;
}
function handleCli(line) {
  if (!line || !line.trim()) return;
  cliPrint("> " + line);
  const parts = line.trim().split(/\s+/);
  const cmd = parts[0]?.toLowerCase();
  try {
    switch (cmd) {
      case "help": cliHelp(); break;
      case "run": run(); cliPrint("Run completed.", "ok"); break;
      case "set":
        if (parts.length < 3) { cliPrint("Usage: set <key> <value>", "err"); break; }
        if (setInput(parts[1], parts.slice(2).join(" "))) cliPrint(`Set ${parts[1]}`, "ok");
        else cliPrint("Invalid key/value", "err");
        break;
      case "get":
        if (parts.length < 2) { cliPrint("Usage: get <key>", "err"); break; }
        const v = getInputValue(parts[1]);
        cliPrint(`${parts[1]} = ${v !== undefined ? v : "unknown"}`); break;
      case "eval":
        if (parts[1]?.toLowerCase() === "ps") {
          const res = dcfEngine(readInputs());
          cliPrint("Per-share: $" + (isFinite(res.totals.perShare) ? res.totals.perShare.toFixed(2) : "—"), "ok");
        } else cliPrint("Unknown eval target. Try: eval ps", "err");
        break;
      case "mc":
        if (parts.length < 3) { cliPrint("Usage: mc <trials> <vol_pp>", "err"); break; }
        $("mcTrials").value = String(Math.max(100, Math.min(10000, Math.round(Number(parts[1])))));
        $("mcVol").value = String(Number(parts[2]));
        $("runMC").click();
        cliPrint(`Monte Carlo started.`, "ok");
        break;
      case "grid":
        if (parts.length < 7) { cliPrint("Usage: grid <x> <min> <max> <y> <min> <max>", "err"); break; }
        $("axisX").value = parts[1];
        $("xMin").value = String(Number(parts[2]));
        $("xMax").value = String(Number(parts[3]));
        $("axisY").value = parts[4];
        $("yMin").value = String(Number(parts[5]));
        $("yMax").value = String(Number(parts[6]));
        // activate right tab twoWay
        const rightTabs = document.querySelectorAll('.tabs')[1];
        rightTabs.querySelectorAll(".tab").forEach(b=>b.classList.remove("active"));
        rightTabs.querySelector('[data-tab="twoWay"]')?.classList.add("active");
        run();
        cliPrint("Two-way grid updated.", "ok");
        break;
      case "export":
        if (parts[1]?.toLowerCase() === "json") { $("exportJSON").click(); cliPrint("Export JSON triggered.", "ok"); }
        else if (parts[1]?.toLowerCase() === "csv") { $("exportCSV").click(); cliPrint("Export CSV triggered.", "ok"); }
        else cliPrint("Unknown export kind. Use json|csv", "err");
        break;
      default:
        cliPrint("Unknown command. Type 'help'.", "err");
    }
  } catch (e) {
    cliPrint("Error: " + (e?.message || String(e)), "err");
  }
}
cliExecBtn?.addEventListener("click", () => { const line = cliIn?.value || ""; if (cliIn) cliIn.value = ""; handleCli(line); });
cliIn?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") { const line = e.currentTarget.value; e.currentTarget.value = ""; handleCli(line); }
});

/**
 * Import JSON (run payload)
 */
$("importJSON")?.addEventListener("click", () => {
  $("importJSONFile")?.click();
});
$("importJSONFile")?.addEventListener("change", async (e) => {
  try {
    const file = e.target?.files?.[0];
    if (!file) return;
    const text = await file.text();
    const data = JSON.parse(text);
    const obj = data?.inputs ? data : (Array.isArray(data) ? data[0] : null);
    if (!obj?.inputs) throw new Error("Invalid run JSON: missing inputs");
    applyScenarioInputs(obj.inputs);
    logLine("Imported run JSON and applied inputs.");
    run();
  } catch (err) {
    logLine("Failed to import JSON: " + (err?.message || err), "err");
  } finally {
    if (e.target) e.target.value = "";
  }
});

// Export JSON
$("exportJSON")?.addEventListener("click", () => {
  const inputs = readInputs();
  // Attach terminal settings to inputs for audit context
  const tvMethod = (document.getElementById("tvMultiple")?.checked ? "multiple" : "perpetuity");
  const tvMultipleVal = Number(document.getElementById("tvMultipleVal")?.value || 12);
  const res = dcfEngine({ ...inputs, tvMethod, tvMultipleVal });

  // MC settings snapshot
  const saved = (() => { try { return JSON.parse(localStorage.getItem("valor:mc-settings") || "{}"); } catch { return {}; }})();
  const mcSnapshot = {
    trials: Number($("mcTrials")?.value || saved.trials || 1000),
    volPP: Number($("mcVol")?.value || saved.volPP || 2.0),
    seedStr: String($("mcSeed")?.value || saved.seedStr || ""),
    marginVolPP: Number($("mcMarginVol")?.value || saved.marginVolPP || $("mcVol")?.value || 2.0),
    s2cVolPct: Number($("mcS2CVol")?.value || saved.s2cVolPct || 5),
    corrGM: Number($("mcCorrGM")?.value || saved.corrGM || 0.3)
  };

  // TV method comparison export (audit)
  const years = res.params.years;
  const fcffN = res.series.fcff[years] || 0;
  const fcffN1 = fcffN * (1 + res.params.termGrowth);

  // Base TV (already in result.totals.pvTv)
  const baseMethod = tvMethod;
  let cfMethod = baseMethod === "perpetuity" ? "multiple" : "perpetuity";
  let tvUnd_base = 0, tvUnd_cf = 0, pvTv_base = res.totals.pvTv, pvTv_cf = 0;

  if (baseMethod === "perpetuity") {
    tvUnd_base = res.params.wacc > res.params.termGrowth ? (fcffN1 / (res.params.wacc - res.params.termGrowth)) : 0;
    // counterfactual = multiple
    tvUnd_cf = Math.max(0, tvMultipleVal * fcffN1);
  } else {
    // base multiple
    tvUnd_base = Math.max(0, (res.params.tvMultipleVal || tvMultipleVal) * fcffN1);
    // counterfactual = perpetuity
    tvUnd_cf = res.params.wacc > res.params.termGrowth ? (fcffN1 / (res.params.wacc - res.params.termGrowth)) : 0;
  }
  pvTv_cf = tvUnd_cf / Math.pow(1 + res.params.wacc, years);

  const ev_cf = res.totals.sumPvFcff + pvTv_cf;

  const payload = {
    _schema: "valor:run@1",
    inputs: { ...inputs, tvMethod, tvMultipleVal, mc: mcSnapshot },
    result: res,
    tvAudit: {
      baseMethod,
      counterfactualMethod: cfMethod,
      fcffN1,
      tvUndiscounted_base: tvUnd_base,
      tvUndiscounted_cf: tvUnd_cf,
      pvTv_base,
      pvTv_cf,
      ev_base: res.totals.ev,
      ev_cf,
    }
  };

  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `${inputs.ticker || "output"}.valor-sample.json`;
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
  logLine("Exported JSON.");
});

// In-browser test harness
(function runTests() {
  if (location.search.includes("tests")) {
    console.log("--- Running In-Browser Tests ---");
    const testCase = {
      ticker: "TEST", revenue: 1000, growthY1: 0.15, growthDecay: 0.01, years: 5,
      termGrowth: 0.025, ebitMargin: 0.20, taxRate: 0.25, salesToCap: 2, wacc: 0.10,
      shares: 100, netDebt: 200,
      stage1End: 2, stage2End: 4,
      s1Growth: 0.15, s1Margin: 0.20, s1S2C: 2, s1NWC: 0.05,
      s2Growth: 0.10, s2Margin: 0.22, s2S2C: 2.5, s2NWC: 0.04,
      s3Growth: 0.05, s3Margin: 0.24, s3S2C: 3, s3NWC: 0.03,
    };
    const res = dcfEngine(testCase);
    console.assert(Math.abs(res.totals.perShare - 131.33) < 0.01, "DCF perShare mismatch");

    const mcRes = runMonteCarlo(testCase, 1000, 2.0, "test-seed", null, {});
    console.assert(Math.abs(mcRes.stats.mean - 131.3) < 0.5, "MC mean mismatch");
    console.assert(mcRes.results.length === 1000, "MC trial count mismatch");
    console.log("--- Tests Complete ---");
  }
})();
