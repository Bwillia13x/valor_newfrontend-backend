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

// Enhanced financial validation with contextual explanations
export function validateInputs(inputs) {
  const errors = [];
  const warnings = [];
  
  const markInvalid = (id, on) => {
    const el = document.getElementById(id);
    if (el) {
      el.setAttribute("aria-invalid", on ? "true" : "false");
      // Add visual feedback class
      if (on) {
        el.classList.add('validation-error');
      } else {
        el.classList.remove('validation-error');
      }
    }
  };
  
  const showFieldWarning = (id, message) => {
    const el = document.getElementById(id);
    if (el) {
      el.classList.add('validation-warning');
      // Create or update warning tooltip
      let tooltip = el.parentNode.querySelector('.validation-tooltip');
      if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.className = 'validation-tooltip warning';
        el.parentNode.appendChild(tooltip);
      }
      tooltip.textContent = message;
      tooltip.style.display = 'block';
    }
  };
  
  const clearWarnings = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.classList.remove('validation-warning');
      const tooltip = el.parentNode.querySelector('.validation-tooltip');
      if (tooltip) tooltip.style.display = 'none';
    }
  };
  
  // Clear previous validation marks
  const validationFields = ["wacc", "termGrowth", "years", "taxRate", "salesToCap", "stage1End", "stage2End", 
                           "ebitMargin", "revenue", "shares", "netDebt", "s1Growth", "s2Growth", "s3Growth",
                           "s1Margin", "s2Margin", "s3Margin", "s1S2C", "s2S2C", "s3S2C"];
  
  validationFields.forEach((id) => {
    markInvalid(id, false);
    clearWarnings(id);
  });

  // Critical financial constraints
  if (inputs.termGrowth >= inputs.wacc) {
    errors.push({
      message: "Terminal growth rate cannot equal or exceed WACC",
      explanation: "This violates the Gordon Growth Model assumptions and would result in infinite or negative valuation. In efficient markets, no company can grow faster than the cost of capital indefinitely.",
      suggestion: `Consider reducing terminal growth to ${(inputs.wacc * 100 - 0.5).toFixed(1)}% or increasing WACC to ${(inputs.termGrowth * 100 + 0.5).toFixed(1)}%`,
      fields: ["termGrowth", "wacc"]
    });
    markInvalid("termGrowth", true);
    markInvalid("wacc", true);
  }
  
  // Stage sequencing validation
  if (inputs.stage2End <= inputs.stage1End) {
    errors.push({
      message: "Growth stage timeline is invalid",
      explanation: "Stage 2 must begin after Stage 1 ends to maintain proper modeling sequence. This ensures logical progression from high-growth to mature phases.",
      suggestion: `Set Stage 2 end to year ${inputs.stage1End + 2} or later`,
      fields: ["stage2End", "stage1End"]
    });
    markInvalid("stage2End", true);
    markInvalid("stage1End", true);
  }
  
  if (inputs.stage1End > inputs.years || inputs.stage2End > inputs.years) {
    errors.push({
      message: "Growth stages exceed projection period",
      explanation: "Stage endpoints cannot be beyond the total projection years. This would create gaps in the forecast model.",
      suggestion: `Increase projection years to ${Math.max(inputs.stage1End, inputs.stage2End) + 1} or reduce stage endpoints`,
      fields: ["stage1End", "stage2End", "years"]
    });
    markInvalid("stage1End", true);
    markInvalid("stage2End", true);
    markInvalid("years", true);
  }
  
  // Financial range validations with industry context
  if (inputs.years < 3 || inputs.years > 15) {
    errors.push({
      message: "Projection period outside acceptable range",
      explanation: "DCF models require 3-15 years for reliability. Shorter periods lack sufficient data; longer periods have excessive uncertainty.",
      suggestion: "Industry standard is 5-10 years depending on business cycle and visibility",
      fields: ["years"]
    });
    markInvalid("years", true);
  }
  
  if (inputs.taxRate < 0 || inputs.taxRate > 0.6) {
    errors.push({
      message: "Tax rate outside reasonable bounds",
      explanation: "Corporate tax rates typically range from 15-35% globally. Rates above 60% are unrealistic for most jurisdictions.",
      suggestion: "Check local corporate tax rates. US federal rate is 21%, most developed markets are 20-30%",
      fields: ["taxRate"]
    });
    markInvalid("taxRate", true);
  }
  
  if (inputs.salesToCap <= 0 || inputs.salesToCap > 10) {
    errors.push({
      message: "Sales-to-Capital ratio is unrealistic",
      explanation: "This ratio measures capital efficiency. Values below 0.5 suggest capital-intensive businesses; above 5 suggests highly efficient operations.",
      suggestion: "Typical ranges: Tech (3-6), Manufacturing (1-3), Utilities (0.3-1), Retail (4-8)",
      fields: ["salesToCap"]
    });
    markInvalid("salesToCap", true);
  }
  
  // WACC validation with market context
  if (inputs.wacc < 0.03 || inputs.wacc > 0.25) {
    errors.push({
      message: "WACC outside typical market range",
      explanation: "Cost of capital below 3% or above 25% is unusual. Very low rates suggest risk-free assets; very high rates suggest distressed situations.",
      suggestion: "Typical ranges: Large-cap (6-12%), Mid-cap (8-15%), Small-cap/Growth (10-20%)",
      fields: ["wacc"]
    });
    markInvalid("wacc", true);
  }
  
  // Revenue and size validations
  if (inputs.revenue <= 0) {
    errors.push({
      message: "Revenue must be positive",
      explanation: "Base year revenue is required for all projections. This represents the starting point for growth calculations.",
      suggestion: "Enter the most recent annual revenue in millions",
      fields: ["revenue"]
    });
    markInvalid("revenue", true);
  }
  
  if (inputs.shares <= 0) {
    errors.push({
      message: "Share count must be positive",
      explanation: "Outstanding shares are needed to calculate per-share value from enterprise value.",
      suggestion: "Use diluted shares outstanding from most recent financial statements",
      fields: ["shares"]
    });
    markInvalid("shares", true);
  }
  
  // Growth rate warnings (not errors)
  if (inputs.s1Growth > 0.5) {
    warnings.push("Stage 1 growth above 50% annually is very aggressive for most businesses");
    showFieldWarning("s1Growth", "Growth >50% is rare and typically unsustainable");
  }
  
  if (inputs.s1Growth < 0) {
    warnings.push("Negative growth in Stage 1 suggests declining business fundamentals");
    showFieldWarning("s1Growth", "Consider if company is in turnaround situation");
  }
  
  // Margin validation with industry context
  const marginFields = [{field: "s1Margin", stage: "Stage 1"}, {field: "s2Margin", stage: "Stage 2"}, {field: "s3Margin", stage: "Stage 3"}];
  marginFields.forEach(({field, stage}) => {
    const margin = inputs[field];
    if (margin > 0.6) {
      warnings.push(`${stage} margin above 60% is exceptionally high`);
      showFieldWarning(field, "Margins >60% are rare except in software/IP businesses");
    }
    if (margin < 0) {
      warnings.push(`${stage} has negative margins`);
      showFieldWarning(field, "Negative margins suggest operational challenges");
    }
  });
  
  // Terminal growth warnings
  if (inputs.termGrowth > 0.04) {
    warnings.push("Terminal growth above 4% exceeds long-term GDP growth in most developed markets");
    showFieldWarning("termGrowth", "Consider using 2-3% for conservative modeling");
  }
  
  if (inputs.termGrowth < 0) {
    warnings.push("Negative terminal growth assumes permanent decline");
    showFieldWarning("termGrowth", "Typically used only for declining industries");
  }
  
  // Debt-to-equity warnings
  const impliedEquityValue = (inputs.revenue * 3); // Rough approximation
  const debtToEquityRatio = Math.abs(inputs.netDebt) / impliedEquityValue;
  if (debtToEquityRatio > 2) {
    warnings.push("High debt levels may indicate financial distress");
    showFieldWarning("netDebt", "D/E ratio appears elevated - verify capital structure");
  }

  return { errors, warnings };
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