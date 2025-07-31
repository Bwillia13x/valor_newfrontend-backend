// Valor IVX - Charting Module
// Chart rendering and visualization functions

import { fmt } from './utils.js';

// Render FCFF chart with multiple modes
export function renderFcfChart(canvas, series, mode = "fcf", tooltipDiv = null, overlaySeries = null) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  
  const years = series.rev.length - 1;
  if (years < 1) return;
  
  // Determine data to plot based on mode
  let data, yLabel, color1, color2;
  switch (mode) {
    case "fcf":
      data = series.fcff.slice(1);
      yLabel = "FCFF ($MM)";
      color1 = "#72efdd";
      color2 = "#4ecdc4";
      break;
    case "rev":
      data = series.rev.slice(1);
      yLabel = "Revenue ($MM)";
      color1 = "#ffd166";
      color2 = "#f4a261";
      break;
    case "margin":
      data = series.margins.slice(1).map(m => m * 100);
      yLabel = "EBIT Margin (%)";
      color1 = "#e76f51";
      color2 = "#f4a261";
      break;
    case "pv":
      data = series.pvFcff.slice(1);
      yLabel = "PV(FCFF) ($MM)";
      color1 = "#a8dadc";
      color2 = "#457b9d";
      break;
    default:
      data = series.fcff.slice(1);
      yLabel = "FCFF ($MM)";
      color1 = "#72efdd";
      color2 = "#4ecdc4";
  }
  
  const yMin = Math.min(...data, ...(overlaySeries ? overlaySeries.slice(1) : []));
  const yMax = Math.max(...data, ...(overlaySeries ? overlaySeries.slice(1) : []));
  
  // Draw grid
  ctx.strokeStyle = "#2a465c";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 5; i++) {
    const x = 40 + (W - 60) * i / 5;
    ctx.beginPath();
    ctx.moveTo(x, 20);
    ctx.lineTo(x, H - 20);
    ctx.stroke();
  }
  for (let i = 0; i <= 4; i++) {
    const y = 20 + (H - 40) * i / 4;
    ctx.beginPath();
    ctx.moveTo(40, y);
    ctx.lineTo(W - 20, y);
    ctx.stroke();
  }
  
  // Draw axis labels
  ctx.fillStyle = "#cfe3f7";
  ctx.font = "11px system-ui";
  ctx.textAlign = "center";
  for (let i = 0; i <= 5; i++) {
    const x = 40 + (W - 60) * i / 5;
    ctx.fillText(i === 0 ? "0" : String(i), x, H - 5);
  }
  
  // Draw Y-axis labels
  ctx.textAlign = "right";
  for (let i = 0; i <= 4; i++) {
    const y = 20 + (H - 40) * i / 4;
    const val = yMin + (yMax - yMin) * (1 - i / 4);
    ctx.fillText(fmt(val, { decimals: 1 }), 35, y + 3);
  }
  
  // Draw main series
  plotLine(ctx, data, years, 
    (i) => 40 + (W - 60) * ((i - 1) / (years - 1 || 1)),
    (v) => (H - 24) - (H - 44) * ((v - yMin) / ((yMax - yMin) || 1)),
    color1, color2
  );
  
  // Draw overlay if provided
  if (overlaySeries) {
    const overlayData = overlaySeries.slice(1);
    plotLine(ctx, overlayData, years,
      (i) => 40 + (W - 60) * ((i - 1) / (years - 1 || 1)),
      (v) => (H - 24) - (H - 44) * ((v - yMin) / ((yMax - yMin) || 1)),
      "#ffd166", "#f4a261", true
    );
  }
  
  // Draw title
  ctx.fillStyle = "#e7f6ff";
  ctx.font = "12px system-ui";
  ctx.textAlign = "center";
  ctx.fillText(yLabel, W / 2, 10);
  
  // Setup tooltip
  if (tooltipDiv) {
    canvas.addEventListener("mousemove", (e) => {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const yearIndex = Math.round(((x - 40) / (W - 60)) * (years - 1)) + 1;
      if (yearIndex >= 1 && yearIndex <= years) {
        const value = data[yearIndex - 1];
        tooltipDiv.style.display = "block";
        tooltipDiv.style.left = e.clientX + 10 + "px";
        tooltipDiv.style.top = e.clientY - 10 + "px";
        tooltipDiv.textContent = `Year ${yearIndex}: ${fmt(value, { decimals: 1 })}`;
      } else {
        tooltipDiv.style.display = "none";
      }
    });
    
    canvas.addEventListener("mouseleave", () => {
      tooltipDiv.style.display = "none";
    });
  }
}

// Helper function to plot lines
export function plotLine(ctx, data, years, xFn, yFn, color1, color2, dashed = false) {
  if (data.length < 2) return;
  
  ctx.strokeStyle = color1;
  ctx.lineWidth = 2;
  if (dashed) {
    ctx.setLineDash([5, 5]);
  } else {
    ctx.setLineDash([]);
  }
  
  ctx.beginPath();
  ctx.moveTo(xFn(1), yFn(data[0]));
  
  for (let i = 1; i < data.length; i++) {
    ctx.lineTo(xFn(i + 1), yFn(data[i]));
  }
  ctx.stroke();
  ctx.setLineDash([]);
  
  // Draw points
  ctx.fillStyle = color2;
  for (let i = 0; i < data.length; i++) {
    ctx.beginPath();
    ctx.arc(xFn(i + 1), yFn(data[i]), 3, 0, 2 * Math.PI);
    ctx.fill();
  }
}

// Render sensitivity heatmap
export async function renderHeatmap(canvas, params, baseInputs) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  
  const { dcfEngine } = await import('./dcf-engine.js');
  
  const waccSteps = 20;
  const gSteps = 20;
  const waccMin = params.waccMin * 100;
  const waccMax = params.waccMax * 100;
  const gMin = params.tgMin * 100;
  const gMax = params.tgMax * 100;
  
  const round2 = (x, p) => Math.round(x * p) / p; // e.g., p=100 -> 2 decimals
  
  // Cache for performance
  const cache = new Map();
  const getFromCache = (wacc, g) => {
    const key = `${round2(wacc, 100)}_${round2(g, 100)}`;
    return cache.get(key);
  };
  const setInCache = (wacc, g, val) => {
    const key = `${round2(wacc, 100)}_${round2(g, 100)}`;
    cache.set(key, val);
  };
  
  // Compute values
  const values = [];
  let minVal = Infinity, maxVal = -Infinity;
  
  for (let i = 0; i <= waccSteps; i++) {
    const row = [];
    const wacc = waccMin + (waccMax - waccMin) * i / waccSteps;
    
    for (let j = 0; j <= gSteps; j++) {
      const g = gMin + (gMax - gMin) * j / gSteps;
      
      let val = getFromCache(wacc, g);
      if (val === undefined) {
        const inputs = { ...baseInputs, wacc: wacc / 100, termGrowth: g / 100 };
        const res = dcfEngine(inputs);
        val = res.totals.perShare;
        setInCache(wacc, g, val);
      }
      
      row.push(val);
      minVal = Math.min(minVal, val);
      maxVal = Math.max(maxVal, val);
    }
    values.push(row);
  }
  
  // Color function
  function colorFor(val, min, max) {
    const t = (val - min) / (max - min);
    const r = Math.round(255 * (1 - t));
    const g = Math.round(255 * t);
    const b = 0;
    return `rgb(${r}, ${g}, ${b})`;
  }
  
  // Draw heatmap
  const cellW = (W - 80) / waccSteps;
  const cellH = (H - 60) / gSteps;
  
  const paintRow = () => {
    for (let i = 0; i <= waccSteps; i++) {
      for (let j = 0; j <= gSteps; j++) {
        const val = values[i][j];
        const color = colorFor(val, minVal, maxVal);
        
        ctx.fillStyle = color;
        const x = 40 + i * cellW;
        const y = 20 + j * cellH;
        ctx.fillRect(x, y, cellW, cellH);
      }
    }
  };
  
  paintRow();
  
  // Draw grid
  ctx.strokeStyle = "#2a465c";
  ctx.lineWidth = 1;
  for (let i = 0; i <= waccSteps; i += 5) {
    const x = 40 + i * cellW;
    ctx.beginPath();
    ctx.moveTo(x, 20);
    ctx.lineTo(x, H - 20);
    ctx.stroke();
  }
  for (let j = 0; j <= gSteps; j += 5) {
    const y = 20 + j * cellH;
    ctx.beginPath();
    ctx.moveTo(40, y);
    ctx.lineTo(W - 40, y);
    ctx.stroke();
  }
  
  // Draw axis labels
  ctx.fillStyle = "#cfe3f7";
  ctx.font = "11px system-ui";
  ctx.textAlign = "center";
  
  // WACC labels (bottom)
  for (let i = 0; i <= waccSteps; i += 5) {
    const x = 40 + i * cellW;
    const wacc = waccMin + (waccMax - waccMin) * i / waccSteps;
    ctx.fillText(wacc.toFixed(1) + "%", x, H - 5);
  }
  
  // Growth labels (left)
  ctx.textAlign = "right";
  for (let j = 0; j <= gSteps; j += 5) {
    const y = 20 + j * cellH;
    const g = gMin + (gMax - gMin) * j / gSteps;
    ctx.fillText(g.toFixed(1) + "%", 35, y + 3);
  }
  
  // Draw title
  ctx.fillStyle = "#e7f6ff";
  ctx.font = "12px system-ui";
  ctx.textAlign = "center";
  ctx.fillText("WACC vs Terminal Growth Sensitivity", W / 2, 10);
}

// Render ramp preview chart
export function renderRampPreview(canvas, inputs) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  
  const years = inputs.years;
  
  function forYear(t, k) {
    if (t <= inputs.stage1End) return inputs["s1" + k];
    if (t <= inputs.stage2End) return inputs["s2" + k];
    return inputs["s3" + k];
  }
  
  // Prepare data
  const growths = [];
  const margins = [];
  const s2c = [];
  
  for (let t = 1; t <= years; t++) {
    growths.push(forYear(t, "Growth") * 100);
    margins.push(forYear(t, "Margin") * 100);
    s2c.push(forYear(t, "S2C"));
  }
  
  const yMin = Math.min(...growths, ...margins, ...s2c);
  const yMax = Math.max(...growths, ...margins, ...s2c);
  
  // Draw grid
  ctx.strokeStyle = "#2a465c";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 5; i++) {
    const x = 40 + (W - 60) * i / 5;
    ctx.beginPath();
    ctx.moveTo(x, 20);
    ctx.lineTo(x, H - 20);
    ctx.stroke();
  }
  for (let i = 0; i <= 4; i++) {
    const y = 20 + (H - 40) * i / 4;
    ctx.beginPath();
    ctx.moveTo(40, y);
    ctx.lineTo(W - 20, y);
    ctx.stroke();
  }
  
  // Draw axis labels
  ctx.fillStyle = "#cfe3f7";
  ctx.font = "11px system-ui";
  ctx.textAlign = "center";
  for (let i = 0; i <= 5; i++) {
    const x = 40 + (W - 60) * i / 5;
    ctx.fillText(i === 0 ? "0" : String(i), x, H - 5);
  }
  
  // Draw Y-axis labels
  ctx.textAlign = "right";
  for (let i = 0; i <= 4; i++) {
    const y = 20 + (H - 40) * i / 4;
    const val = yMin + (yMax - yMin) * (1 - i / 4);
    ctx.fillText(fmt(val, { decimals: 1 }), 35, y + 3);
  }
  
  const x = (i) => 40 + (W - 60) * ((i - 1) / ((years - 1) || 1));
  const y = (v) => (H - 24) - (H - 44) * ((v - yMin) / ((yMax - yMin) || 1));
  
  function plotLine(arr, color) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x(1), y(arr[0]));
    for (let i = 1; i < arr.length; i++) {
      ctx.lineTo(x(i + 1), y(arr[i]));
    }
    ctx.stroke();
    
    // Draw points
    ctx.fillStyle = color;
    for (let i = 0; i < arr.length; i++) {
      ctx.beginPath();
      ctx.arc(x(i + 1), y(arr[i]), 3, 0, 2 * Math.PI);
      ctx.fill();
    }
  }
  
  plotLine(growths, "#72efdd");
  plotLine(margins, "#ffd166");
  plotLine(s2c, "#e76f51");
  
  // Draw legend
  ctx.fillStyle = "#e7f6ff";
  ctx.font = "12px system-ui";
  ctx.textAlign = "left";
  ctx.fillText("Growth %", 50, 15);
  ctx.fillStyle = "#ffd166";
  ctx.fillText("Margin %", 120, 15);
  ctx.fillStyle = "#e76f51";
  ctx.fillText("S2C", 190, 15);
}

// Render waterfall chart
export function renderWaterfall(canvas, res) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  
  const { sumPvFcff, pvTv, ev, equity, netDebt } = res.totals;
  const items = [
    { label: "PV(FCFF)", value: sumPvFcff, color: "#72efdd" },
    { label: "PV(TV)", value: pvTv, color: "#4ecdc4" },
    { label: "Enterprise Value", value: ev, color: "#2a9d8f" },
    { label: "Net Debt", value: -netDebt, color: "#e76f51" },
    { label: "Equity Value", value: equity, color: "#f4a261" }
  ];
  
  const maxVal = Math.max(...items.map(item => Math.abs(item.value)));
  const scale = (val) => (val / maxVal) * (H - 80);
  
  function drawBar(x, y, h, color, label, value) {
    ctx.fillStyle = color;
    ctx.fillRect(x, y, 60, h);
    
    ctx.fillStyle = "#e7f6ff";
    ctx.font = "10px system-ui";
    ctx.textAlign = "center";
    ctx.fillText(label, x + 30, y + h + 12);
    ctx.fillText(fmt(value, { decimals: 1 }), x + 30, y + h + 24);
  }
  
  let currentY = 20;
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const h = scale(Math.abs(item.value));
    const y = item.value >= 0 ? currentY : currentY - h;
    
    drawBar(40 + i * 80, y, h, item.color, item.label, item.value);
    
    if (item.value >= 0) {
      currentY += h;
    }
  }
  
  // Draw title
  ctx.fillStyle = "#e7f6ff";
  ctx.font = "12px system-ui";
  ctx.textAlign = "center";
  ctx.fillText("Enterprise Value Waterfall", W / 2, 10);
}

// Render 1D sensitivity chart
export async function renderSensitivity1D(canvas, inputs, axis, minVal, maxVal, steps) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  
  const { dcfEngine } = await import('./dcf-engine.js');
  
  const percentFields = new Set(["wacc", "termGrowth", "ebitMargin"]);
  const toModel = (k, v) => (percentFields.has(k) ? v / 100 : v);
  
  // Compute sensitivity
  const values = [];
  const xValues = [];
  
  for (let i = 0; i <= steps; i++) {
    const x = minVal + (maxVal - minVal) * i / steps;
    xValues.push(x);
    
    const testInputs = { ...inputs };
    testInputs[axis] = toModel(axis, x);
    const res = dcfEngine(testInputs);
    values.push(res.totals.perShare);
  }
  
  const yMin = Math.min(...values);
  const yMax = Math.max(...values);
  const padY = (yMax - yMin) * 0.1;
  
  // Draw grid
  ctx.strokeStyle = "#2a465c";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 5; i++) {
    const x = 40 + (W - 60) * i / 5;
    ctx.beginPath();
    ctx.moveTo(x, 20);
    ctx.lineTo(x, H - 20);
    ctx.stroke();
  }
  for (let i = 0; i <= 4; i++) {
    const y = 20 + (H - 40) * i / 4;
    ctx.beginPath();
    ctx.moveTo(40, y);
    ctx.lineTo(W - 20, y);
    ctx.stroke();
  }
  
  // Draw axis labels
  ctx.fillStyle = "#cfe3f7";
  ctx.font = "11px system-ui";
  ctx.textAlign = "center";
  for (let i = 0; i <= 5; i++) {
    const x = 40 + (W - 60) * i / 5;
    const xVal = minVal + (maxVal - minVal) * i / 5;
    ctx.fillText(fmt(xVal, { decimals: 1 }), x, H - 5);
  }
  
  // Draw Y-axis labels
  ctx.textAlign = "right";
  for (let i = 0; i <= 4; i++) {
    const y = 20 + (H - 40) * i / 4;
    const val = yMin - padY + (yMax - yMin + 2 * padY) * (1 - i / 4);
    ctx.fillText(fmt(val, { decimals: 1 }), 35, y + 3);
  }
  
  const x = (i) => 40 + (W - 60) * (i / steps);
  const y = (v) => (H - 24) - (H - 44) * ((v - (yMin - padY)) / ((yMax - yMin + 2 * padY) || 1));
  
  // Draw sensitivity line
  plotLine(ctx, values, steps, x, y, "#72efdd", "#4ecdc4");
  
  // Draw title
  ctx.fillStyle = "#e7f6ff";
  ctx.font = "12px system-ui";
  ctx.textAlign = "center";
  const axisLabels = {
    wacc: "WACC",
    termGrowth: "Terminal Growth",
    ebitMargin: "EBIT Margin",
    salesToCap: "Sales-to-Capital"
  };
  ctx.fillText(`${axisLabels[axis]} Sensitivity`, W / 2, 10);
} 