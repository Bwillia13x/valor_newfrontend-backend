// Valor IVX - DCF Engine Module
// Core financial modeling logic and validation

import { clamp } from './utils.js';

// Core DCF calculation engine
export function dcfEngine(params) {
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

// Input validation with visual feedback
export function validateInputs(inputs) {
  const errors = [];
  const markInvalid = (id, on) => {
    const el = document.getElementById(id);
    if (el) el.setAttribute("aria-invalid", on ? "true" : "false");
  };
  
  // Clear previous validation marks
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
  if (inputs.taxRate < 0 || inputs.taxRate > 1) {
    errors.push("Tax rate must be between 0% and 100%.");
    markInvalid("taxRate", true);
  }
  if (inputs.salesToCap <= 0) {
    errors.push("Sales-to-Capital must be positive.");
    markInvalid("salesToCap", true);
  }

  return errors;
}

// Compute key performance indicators
export function computeKPIs(res) {
  const { series, totals, params } = res;
  const years = params.years;
  
  // ROIC approximation (NOPAT / Invested Capital)
  const avgNopat = series.nopat.slice(1, years + 1).reduce((a, b) => a + b, 0) / years;
  const avgReinvest = series.reinvest.slice(1, years + 1).reduce((a, b) => a + b, 0) / years;
  const roic = avgReinvest > 0 ? avgNopat / avgReinvest : 0;
  
  // Reinvestment rate
  const avgFcff = series.fcff.slice(1, years + 1).reduce((a, b) => a + b, 0) / years;
  const reinvestRate = avgNopat > 0 ? avgReinvest / avgNopat : 0;
  
  // FCFF CAGR
  const fcffCAGR = years > 1 ? Math.pow(series.fcff[years] / series.fcff[1], 1 / (years - 1)) - 1 : 0;
  
  // Payback period (PV-based)
  let payback = 0;
  let cumulativePV = 0;
  for (let t = 1; t <= years; t++) {
    cumulativePV += series.pvFcff[t];
    if (cumulativePV >= totals.ev * 0.5) { // 50% of EV
      payback = t;
      break;
    }
  }
  
  // EV / NOPAT (Year N)
  const evNopat = series.nopat[years] > 0 ? totals.ev / series.nopat[years] : 0;
  
  return {
    roic,
    reinvestRate,
    fcffCAGR,
    payback,
    evNopat
  };
}

// Read form inputs
export function readInputs() {
  return {
    ticker: document.getElementById("ticker")?.value || "SAMPLE",
    revenue: Number(document.getElementById("revenue")?.value || 500),
    growthY1: Number(document.getElementById("growthY1")?.value || 12) / 100,
    growthDecay: Number(document.getElementById("growthDecay")?.value || 1.5) / 100,
    years: Number(document.getElementById("years")?.value || 7),
    termGrowth: Number(document.getElementById("termGrowth")?.value || 2.5) / 100,
    ebitMargin: Number(document.getElementById("ebitMargin")?.value || 22) / 100,
    taxRate: Number(document.getElementById("taxRate")?.value || 23) / 100,
    salesToCap: Number(document.getElementById("salesToCap")?.value || 2.5),
    wacc: Number(document.getElementById("wacc")?.value || 9.0) / 100,
    shares: Number(document.getElementById("shares")?.value || 150),
    netDebt: Number(document.getElementById("netDebt")?.value || 300),
    waccMin: Number(document.getElementById("waccMin")?.value || 7) / 100,
    waccMax: Number(document.getElementById("waccMax")?.value || 12) / 100,
    tgMin: Number(document.getElementById("tgMin")?.value || 1.0) / 100,
    tgMax: Number(document.getElementById("tgMax")?.value || 3.5) / 100,
    // ramps
    stage1End: Number(document.getElementById("stage1End")?.value || 3),
    stage2End: Number(document.getElementById("stage2End")?.value || 6),
    s1Growth: Number(document.getElementById("s1Growth")?.value || 12.0) / 100,
    s1Margin: Number(document.getElementById("s1Margin")?.value || 20.0) / 100,
    s1S2C: Number(document.getElementById("s1S2C")?.value || 2.5),
    s1NWC: Number(document.getElementById("s1NWC")?.value || 5.0) / 100,
    s2Growth: Number(document.getElementById("s2Growth")?.value || 8.0) / 100,
    s2Margin: Number(document.getElementById("s2Margin")?.value || 22.0) / 100,
    s2S2C: Number(document.getElementById("s2S2C")?.value || 3.0),
    s2NWC: Number(document.getElementById("s2NWC")?.value || 4.0) / 100,
    s3Growth: Number(document.getElementById("s3Growth")?.value || 4.0) / 100,
    s3Margin: Number(document.getElementById("s3Margin")?.value || 24.0) / 100,
    s3S2C: Number(document.getElementById("s3S2C")?.value || 3.5),
    s3NWC: Number(document.getElementById("s3NWC")?.value || 3.5) / 100,
  };
}

// Apply inputs to form
export function applyInputs(inputs) {
  const map = {
    ticker: "ticker", revenue: "revenue", growthY1: "growthY1", growthDecay: "growthDecay", years: "years",
    termGrowth: "termGrowth", ebitMargin: "ebitMargin", taxRate: "taxRate", salesToCap: "salesToCap",
    wacc: "wacc", shares: "shares", netDebt: "netDebt", waccMin: "waccMin", waccMax: "waccMax",
    tgMin: "tgMin", tgMax: "tgMax",
    stage1End: "stage1End", stage2End: "stage2End",
    s1Growth: "s1Growth", s1Margin: "s1Margin", s1S2C: "s1S2C", s1NWC: "s1NWC",
    s2Growth: "s2Growth", s2Margin: "s2Margin", s2S2C: "s2S2C", s2NWC: "s2NWC",
    s3Growth: "s3Growth", s3Margin: "s3Margin", s3S2C: "s3S2C", s3NWC: "s3NWC"
  };
  
  const percentFields = new Set(["growthY1", "growthDecay", "termGrowth", "ebitMargin", "taxRate", "wacc", "waccMin", "waccMax", "tgMin", "tgMax", "s1Growth", "s1Margin", "s1NWC", "s2Growth", "s2Margin", "s2NWC", "s3Growth", "s3Margin", "s3NWC"]);
  
  for (const [key, id] of Object.entries(map)) {
    const el = document.getElementById(id);
    if (el && inputs[key] !== undefined) {
      const value = percentFields.has(key) ? inputs[key] * 100 : inputs[key];
      el.value = value;
    }
  }
}

// Preset values for demo
export function preset() {
  const inputs = {
    ticker: "SAMPLE",
    revenue: 500,
    growthY1: 0.12,
    growthDecay: 0.015,
    years: 7,
    termGrowth: 0.025,
    ebitMargin: 0.22,
    taxRate: 0.23,
    salesToCap: 2.5,
    wacc: 0.09,
    shares: 150,
    netDebt: 300,
    waccMin: 0.07,
    waccMax: 0.12,
    tgMin: 0.01,
    tgMax: 0.035,
    stage1End: 3,
    stage2End: 6,
    s1Growth: 0.12,
    s1Margin: 0.20,
    s1S2C: 2.5,
    s1NWC: 0.05,
    s2Growth: 0.08,
    s2Margin: 0.22,
    s2S2C: 3.0,
    s2NWC: 0.04,
    s3Growth: 0.04,
    s3Margin: 0.24,
    s3S2C: 3.5,
    s3NWC: 0.035,
  };
  applyInputs(inputs);
}

// Reset form to defaults
export function resetForm() {
  const inputs = {
    ticker: "SAMPLE",
    revenue: 500,
    growthY1: 0.12,
    growthDecay: 0.015,
    years: 7,
    termGrowth: 0.025,
    ebitMargin: 0.22,
    taxRate: 0.23,
    salesToCap: 2.5,
    wacc: 0.09,
    shares: 150,
    netDebt: 300,
    waccMin: 0.07,
    waccMax: 0.12,
    tgMin: 0.01,
    tgMax: 0.035,
    stage1End: 3,
    stage2End: 6,
    s1Growth: 0.12,
    s1Margin: 0.20,
    s1S2C: 2.5,
    s1NWC: 0.05,
    s2Growth: 0.08,
    s2Margin: 0.22,
    s2S2C: 3.0,
    s2NWC: 0.04,
    s3Growth: 0.04,
    s3Margin: 0.24,
    s3S2C: 3.5,
    s3NWC: 0.035,
  };
  applyInputs(inputs);
} 