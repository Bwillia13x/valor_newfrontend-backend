// Valor IVX - Monte Carlo Module
// Monte Carlo simulation and analysis

import { mulberry32, randn, saveToStorage } from './utils.js';
import { dcfEngine } from './dcf-engine.js';

// Run Monte Carlo simulation
export function runMonteCarlo(baseInputs, trials, volPP, seedStr, cancelSignal, options = {}) {
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
    saveToStorage(persistKey, save);
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

// Render Monte Carlo histogram
export function renderHistogram(canvas, data, annotations = true) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  if (!data || data.length === 0) return;
  
  const bins = 30;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min;
  const binWidth = range / bins;
  
  // Count bins
  const counts = new Array(bins).fill(0);
  for (const val of data) {
    const bin = Math.min(bins - 1, Math.floor((val - min) / binWidth));
    counts[bin]++;
  }
  
  const maxCount = Math.max(...counts);
  const gridW = W - 80;
  const gridH = H - 60;
  
  // Draw grid
  ctx.strokeStyle = "#2a465c";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 5; i++) {
    const x = 40 + (gridW * i) / 5;
    ctx.beginPath();
    ctx.moveTo(x, 20);
    ctx.lineTo(x, H - 20);
    ctx.stroke();
  }
  for (let i = 0; i <= 4; i++) {
    const y = 20 + (gridH * i) / 4;
    ctx.beginPath();
    ctx.moveTo(40, y);
    ctx.lineTo(W - 40, y);
    ctx.stroke();
  }
  
  // Draw histogram bars
  ctx.fillStyle = "#72efdd";
  for (let i = 0; i < bins; i++) {
    const x = 40 + (gridW * i) / bins;
    const h = (counts[i] / maxCount) * gridH;
    const y = H - 20 - h;
    ctx.fillRect(x, y, gridW / bins - 1, h);
  }
  
  // Draw axis labels
  ctx.fillStyle = "#cfe3f7";
  ctx.font = "11px system-ui";
  ctx.textAlign = "center";
  for (let i = 0; i <= 5; i++) {
    const x = 40 + (gridW * i) / 5;
    const val = min + (range * i) / 5;
    ctx.fillText(val.toFixed(1), x, H - 5);
  }
  
  // Draw annotations if enabled
  if (annotations && data.length > 0) {
    const mean = data.reduce((a, b) => a + b, 0) / data.length;
    const median = data[Math.floor(data.length / 2)];
    const p10 = data[Math.floor(0.1 * data.length)];
    const p90 = data[Math.floor(0.9 * data.length)];
    
    const xForVal = (v) => 40 + ((v - min) / range) * gridW;
    
    function vline(x, color, label) {
      if (x < 40 || x > W - 40) return;
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(x, 20);
      ctx.lineTo(x, H - 20);
      ctx.stroke();
      
      ctx.fillStyle = color;
      ctx.font = "10px system-ui";
      ctx.textAlign = "center";
      ctx.fillText(label, x, 15);
    }
    
    vline(xForVal(mean), "#72efdd", "μ");
    vline(xForVal(median), "#cfe3f7", "med");
    vline(xForVal(p10), "#ffd166", "p10");
    vline(xForVal(p90), "#ffd166", "p90");
  }
  
  // Draw title
  ctx.fillStyle = "#e7f6ff";
  ctx.font = "12px system-ui";
  ctx.textAlign = "center";
  ctx.fillText(`Monte Carlo Distribution (${data.length} trials)`, W / 2, 10);
}

// Validate Monte Carlo inputs
export function validateMCInputs(trials, volPP, marginVolPP, s2cVolPct, corrGM) {
  const errors = [];
  const mark = (id, on) => { 
    const el = document.getElementById(id); 
    if (el) el.setAttribute("aria-invalid", on ? "true" : "false"); 
  };
  
  // Clear previous marks
  ["mcTrials", "mcVol", "mcMarginVol", "mcS2CVol", "mcCorrGM"].forEach(id => mark(id, false));
  
  if (trials < 100 || trials > 10000) {
    errors.push("Trials must be between 100 and 10,000.");
    mark("mcTrials", true);
  }
  
  if (volPP < 0 || volPP > 10) {
    errors.push("Growth volatility must be between 0 and 10 percentage points.");
    mark("mcVol", true);
  }
  
  if (marginVolPP !== undefined && (marginVolPP < 0 || marginVolPP > 10)) {
    errors.push("Margin volatility must be between 0 and 10 percentage points.");
    mark("mcMarginVol", true);
  }
  
  if (s2cVolPct !== undefined && (s2cVolPct < 0 || s2cVolPct > 50)) {
    errors.push("S2C volatility must be between 0 and 50 percent.");
    mark("mcS2CVol", true);
  }
  
  if (corrGM !== undefined && (corrGM < -0.99 || corrGM > 0.99)) {
    errors.push("Correlation must be between -0.99 and 0.99.");
    mark("mcCorrGM", true);
  }
  
  return errors;
}

// Initialize Monte Carlo settings from storage
export function initMCSettings() {
  try {
    const saved = JSON.parse(localStorage.getItem("valor:mc-settings") || "{}");
    if (saved.trials) document.getElementById("mcTrials")?.setAttribute("value", saved.trials);
    if (saved.volPP) document.getElementById("mcVol")?.setAttribute("value", saved.volPP);
    if (saved.seedStr) document.getElementById("mcSeed")?.setAttribute("value", saved.seedStr);
    if (saved.marginVolPP) document.getElementById("mcMarginVol")?.setAttribute("value", saved.marginVolPP);
    if (saved.s2cVolPct) document.getElementById("mcS2CVol")?.setAttribute("value", saved.s2cVolPct);
    if (saved.corrGM) document.getElementById("mcCorrGM")?.setAttribute("value", saved.corrGM);
  } catch {}
}

// Get Monte Carlo settings from form
export function getMCSettings() {
  const saved = (() => { 
    try { 
      return JSON.parse(localStorage.getItem("valor:mc-settings") || "{}"); 
    } catch { 
      return {}; 
    }
  })();
  
  return {
    trials: Number(document.getElementById("mcTrials")?.value || saved.trials || 1000),
    volPP: Number(document.getElementById("mcVol")?.value || saved.volPP || 2.0),
    seedStr: String(document.getElementById("mcSeed")?.value || saved.seedStr || ""),
    marginVolPP: Number(document.getElementById("mcMarginVol")?.value || saved.marginVolPP || document.getElementById("mcVol")?.value || 2.0),
    s2cVolPct: Number(document.getElementById("mcS2CVol")?.value || saved.s2cVolPct || 5),
    corrGM: Number(document.getElementById("mcCorrGM")?.value || saved.corrGM || 0.3)
  };
} 