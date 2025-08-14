// Valor IVX - LBO Engine Module
// Leveraged Buyout analysis and modeling

import { clamp } from './utils.js';

// Core LBO calculation engine
export function lboEngine(params) {
  const p = { ...params };
  const warnings = [];
  
  // Safety clamp years
  p.years = clamp(p.years, 3, 10);
  
  // Validate required parameters
  if (!p.purchasePrice || p.purchasePrice <= 0) {
    warnings.push("Purchase price must be positive");
    return { error: "Invalid purchase price" };
  }
  
  if (!p.equityContribution || p.equityContribution <= 0) {
    warnings.push("Equity contribution must be positive");
    return { error: "Invalid equity contribution" };
  }
  
  if (p.equityContribution > p.purchasePrice) {
    warnings.push("Equity contribution cannot exceed purchase price");
    return { error: "Equity contribution exceeds purchase price" };
  }
  
  // Calculate debt structure
  const totalDebt = p.purchasePrice - p.equityContribution;
  const seniorDebt = totalDebt * (p.seniorDebtRatio || 0.6);
  const mezzanineDebt = totalDebt * (p.mezzanineDebtRatio || 0.3);
  const highYieldDebt = totalDebt * (p.highYieldDebtRatio || 0.1);
  
  // Initialize arrays
  const revenue = [];
  const ebitda = [];
  const ebit = [];
  const interestExpense = [];
  const taxes = [];
  const netIncome = [];
  const depreciation = [];
  const capex = [];
  const workingCapital = [];
  const deltaWC = [];
  const freeCashFlow = [];
  const debtBalance = [];
  const principalPayments = [];
  const availableCash = [];
  const cumulativeCash = [];
  
  // Starting values
  revenue[0] = p.revenue;
  ebitda[0] = revenue[0] * p.ebitdaMargin;
  ebit[0] = ebitda[0] - (p.depreciationRatio * revenue[0]);
  debtBalance[0] = totalDebt;
  cumulativeCash[0] = 0;
  
  // Calculate weighted average cost of debt
  const wacd = (seniorDebt * p.seniorDebtRate + 
                mezzanineDebt * p.mezzanineDebtRate + 
                highYieldDebt * p.highYieldDebtRate) / totalDebt;
  
  // Project cash flows
  for (let t = 1; t <= p.years; t++) {
    // Revenue growth
    const growthRate = Math.max(0, p.revenueGrowth - p.growthDecay * (t - 1));
    revenue[t] = revenue[t - 1] * (1 + growthRate);
    
    // EBITDA and EBIT
    ebitda[t] = revenue[t] * p.ebitdaMargin;
    depreciation[t] = revenue[t] * p.depreciationRatio;
    ebit[t] = ebitda[t] - depreciation[t];
    
    // Interest expense (simplified - assumes average debt balance)
    const avgDebtBalance = debtBalance[t - 1];
    interestExpense[t] = avgDebtBalance * wacd;
    
    // Taxes
    const taxableIncome = ebit[t] - interestExpense[t];
    taxes[t] = Math.max(0, taxableIncome * p.taxRate);
    
    // Net income
    netIncome[t] = taxableIncome - taxes[t];
    
    // Working capital
    workingCapital[t] = revenue[t] * p.workingCapitalRatio;
    deltaWC[t] = workingCapital[t] - workingCapital[t - 1];
    
    // Capital expenditures
    capex[t] = revenue[t] * p.capexRatio;
    
    // Free cash flow
    freeCashFlow[t] = ebitda[t] - taxes[t] - capex[t] - deltaWC[t];
    
    // Debt repayment (assume all excess cash goes to debt repayment)
    const excessCash = freeCashFlow[t] - interestExpense[t];
    principalPayments[t] = Math.min(excessCash, debtBalance[t - 1]);
    
    // Update debt balance
    debtBalance[t] = Math.max(0, debtBalance[t - 1] - principalPayments[t]);
    
    // Available cash after debt service
    availableCash[t] = freeCashFlow[t] - interestExpense[t] - principalPayments[t];
    cumulativeCash[t] = cumulativeCash[t - 1] + availableCash[t];
  }
  
  // Calculate exit scenarios
  const exitScenarios = [];
  
  // Exit multiple scenarios
  const exitMultiples = [6, 8, 10, 12, 14];
  exitMultiples.forEach(multiple => {
    const exitEbitda = ebitda[p.years];
    const exitValue = exitEbitda * multiple;
    const remainingDebt = debtBalance[p.years];
    const equityValue = exitValue - remainingDebt;
    const irr = calculateIRR(p.equityContribution, equityValue, p.years);
    const moic = equityValue / p.equityContribution;
    
    exitScenarios.push({
      type: 'multiple',
      multiple: multiple,
      exitValue: exitValue,
      remainingDebt: remainingDebt,
      equityValue: equityValue,
      irr: irr,
      moic: moic
    });
  });
  
  // Exit IRR scenarios
  const targetIRRs = [15, 20, 25, 30];
  targetIRRs.forEach(targetIRR => {
    const requiredEquityValue = p.equityContribution * Math.pow(1 + targetIRR / 100, p.years);
    const requiredExitValue = requiredEquityValue + debtBalance[p.years];
    const impliedMultiple = requiredExitValue / ebitda[p.years];
    
    exitScenarios.push({
      type: 'irr',
      targetIRR: targetIRR,
      requiredExitValue: requiredExitValue,
      impliedMultiple: impliedMultiple,
      equityValue: requiredEquityValue
    });
  });
  
  // Calculate key metrics
  const finalEbitda = ebitda[p.years];
  const finalDebt = debtBalance[p.years];
  const totalInterestPaid = interestExpense.slice(1).reduce((sum, val) => sum + val, 0);
  const totalPrincipalPaid = principalPayments.slice(1).reduce((sum, val) => sum + val, 0);
  const avgIRR = exitScenarios.filter(s => s.type === 'multiple').reduce((sum, s) => sum + s.irr, 0) / 5;
  const avgMOIC = exitScenarios.filter(s => s.type === 'multiple').reduce((sum, s) => sum + s.moic, 0) / 5;
  
  return {
    series: {
      revenue, ebitda, ebit, interestExpense, taxes, netIncome,
      depreciation, capex, workingCapital, deltaWC, freeCashFlow,
      debtBalance, principalPayments, availableCash, cumulativeCash
    },
    metrics: {
      totalDebt: totalDebt,
      equityContribution: p.equityContribution,
      leverageRatio: totalDebt / p.equityContribution,
      wacd: wacd,
      finalEbitda: finalEbitda,
      finalDebt: finalDebt,
      totalInterestPaid: totalInterestPaid,
      totalPrincipalPaid: totalPrincipalPaid,
      avgIRR: avgIRR,
      avgMOIC: avgMOIC
    },
    exitScenarios: exitScenarios,
    debtStructure: {
      seniorDebt: seniorDebt,
      mezzanineDebt: mezzanineDebt,
      highYieldDebt: highYieldDebt,
      seniorDebtRate: p.seniorDebtRate,
      mezzanineDebtRate: p.mezzanineDebtRate,
      highYieldDebtRate: p.highYieldDebtRate
    },
    params: p,
    warnings: warnings
  };
}

// Calculate IRR using Newton-Raphson method
function calculateIRR(initialInvestment, finalValue, years) {
  if (finalValue <= initialInvestment) {
    return -100; // No positive IRR possible
  }
  
  let guess = 0.1; // Start with 10%
  const tolerance = 0.0001;
  const maxIterations = 100;
  
  for (let i = 0; i < maxIterations; i++) {
    const npv = -initialInvestment + finalValue / Math.pow(1 + guess, years);
    const derivative = -years * finalValue / Math.pow(1 + guess, years + 1);
    
    const newGuess = guess - npv / derivative;
    
    if (Math.abs(newGuess - guess) < tolerance) {
      return newGuess * 100; // Convert to percentage
    }
    
    guess = newGuess;
  }
  
  return guess * 100;
}

// Input validation for LBO model
export function validateLBOInputs(inputs) {
  const errors = [];
  const markInvalid = (id, on) => {
    const el = document.getElementById(id);
    if (el) el.setAttribute("aria-invalid", on ? "true" : "false");
  };
  
  // Clear previous validation marks
  const lboFields = [
    "purchasePrice", "equityContribution", "revenue", "ebitdaMargin",
    "revenueGrowth", "growthDecay", "years", "taxRate", "seniorDebtRatio",
    "mezzanineDebtRatio", "highYieldDebtRatio", "seniorDebtRate",
    "mezzanineDebtRate", "highYieldDebtRate"
  ];
  
  lboFields.forEach(id => markInvalid(id, false));
  
  // Validate purchase price and equity contribution
  if (inputs.equityContribution > inputs.purchasePrice) {
    errors.push("Equity contribution cannot exceed purchase price");
    markInvalid("equityContribution", true);
    markInvalid("purchasePrice", true);
  }
  
  if (inputs.equityContribution <= 0) {
    errors.push("Equity contribution must be positive");
    markInvalid("equityContribution", true);
  }
  
  if (inputs.purchasePrice <= 0) {
    errors.push("Purchase price must be positive");
    markInvalid("purchasePrice", true);
  }
  
  // Validate debt ratios
  const totalDebtRatio = (inputs.seniorDebtRatio || 0) + (inputs.mezzanineDebtRatio || 0) + (inputs.highYieldDebtRatio || 0);
  if (Math.abs(totalDebtRatio - 1) > 0.01) {
    errors.push("Debt ratios must sum to 100%");
    markInvalid("seniorDebtRatio", true);
    markInvalid("mezzanineDebtRatio", true);
    markInvalid("highYieldDebtRatio", true);
  }
  
  // Validate rates
  if (inputs.seniorDebtRate < 0 || inputs.mezzanineDebtRate < 0 || inputs.highYieldDebtRate < 0) {
    errors.push("Interest rates must be positive");
    markInvalid("seniorDebtRate", true);
    markInvalid("mezzanineDebtRate", true);
    markInvalid("highYieldDebtRate", true);
  }
  
  // Validate margins and ratios
  if (inputs.ebitdaMargin <= 0 || inputs.ebitdaMargin > 1) {
    errors.push("EBITDA margin must be between 0% and 100%");
    markInvalid("ebitdaMargin", true);
  }
  
  if (inputs.taxRate < 0 || inputs.taxRate > 1) {
    errors.push("Tax rate must be between 0% and 100%");
    markInvalid("taxRate", true);
  }
  
  if (inputs.years < 3 || inputs.years > 10) {
    errors.push("Projection years must be between 3 and 10");
    markInvalid("years", true);
  }
  
  return errors;
}

// Read LBO form inputs
export function readLBOInputs() {
  return {
    companyName: document.getElementById("lboCompanyName")?.value || "Target Company",
    purchasePrice: Number(document.getElementById("lboPurchasePrice")?.value || 1000),
    equityContribution: Number(document.getElementById("lboEquityContribution")?.value || 400),
    revenue: Number(document.getElementById("lboRevenue")?.value || 500),
    ebitdaMargin: Number(document.getElementById("lboEbitdaMargin")?.value || 20) / 100,
    revenueGrowth: Number(document.getElementById("lboRevenueGrowth")?.value || 8) / 100,
    growthDecay: Number(document.getElementById("lboGrowthDecay")?.value || 1) / 100,
    years: Number(document.getElementById("lboYears")?.value || 5),
    taxRate: Number(document.getElementById("lboTaxRate")?.value || 25) / 100,
    depreciationRatio: Number(document.getElementById("lboDepreciationRatio")?.value || 3) / 100,
    capexRatio: Number(document.getElementById("lboCapexRatio")?.value || 4) / 100,
    workingCapitalRatio: Number(document.getElementById("lboWorkingCapitalRatio")?.value || 15) / 100,
    seniorDebtRatio: Number(document.getElementById("lboSeniorDebtRatio")?.value || 60) / 100,
    mezzanineDebtRatio: Number(document.getElementById("lboMezzanineDebtRatio")?.value || 30) / 100,
    highYieldDebtRatio: Number(document.getElementById("lboHighYieldDebtRatio")?.value || 10) / 100,
    seniorDebtRate: Number(document.getElementById("lboSeniorDebtRate")?.value || 6) / 100,
    mezzanineDebtRate: Number(document.getElementById("lboMezzanineDebtRate")?.value || 10) / 100,
    highYieldDebtRate: Number(document.getElementById("lboHighYieldDebtRate")?.value || 12) / 100
  };
}

// Apply LBO inputs to form
export function applyLBOInputs(inputs) {
  const map = {
    lboCompanyName: "companyName",
    lboPurchasePrice: "purchasePrice",
    lboEquityContribution: "equityContribution",
    lboRevenue: "revenue",
    lboEbitdaMargin: "ebitdaMargin",
    lboRevenueGrowth: "revenueGrowth",
    lboGrowthDecay: "growthDecay",
    lboYears: "years",
    lboTaxRate: "taxRate",
    lboDepreciationRatio: "depreciationRatio",
    lboCapexRatio: "capexRatio",
    lboWorkingCapitalRatio: "workingCapitalRatio",
    lboSeniorDebtRatio: "seniorDebtRatio",
    lboMezzanineDebtRatio: "mezzanineDebtRatio",
    lboHighYieldDebtRatio: "highYieldDebtRatio",
    lboSeniorDebtRate: "seniorDebtRate",
    lboMezzanineDebtRate: "mezzanineDebtRate",
    lboHighYieldDebtRate: "highYieldDebtRate"
  };
  
  const percentFields = new Set([
    "ebitdaMargin", "revenueGrowth", "growthDecay", "taxRate", "depreciationRatio",
    "capexRatio", "workingCapitalRatio", "seniorDebtRatio", "mezzanineDebtRatio",
    "highYieldDebtRatio", "seniorDebtRate", "mezzanineDebtRate", "highYieldDebtRate"
  ]);
  
  for (const [id, key] of Object.entries(map)) {
    const el = document.getElementById(id);
    if (el && inputs[key] !== undefined) {
      const value = percentFields.has(key) ? inputs[key] * 100 : inputs[key];
      el.value = value;
    }
  }
}

// LBO preset values
export function lboPreset() {
  const inputs = {
    companyName: "Sample Target",
    purchasePrice: 1000,
    equityContribution: 400,
    revenue: 500,
    ebitdaMargin: 0.20,
    revenueGrowth: 0.08,
    growthDecay: 0.01,
    years: 5,
    taxRate: 0.25,
    depreciationRatio: 0.03,
    capexRatio: 0.04,
    workingCapitalRatio: 0.15,
    seniorDebtRatio: 0.60,
    mezzanineDebtRatio: 0.30,
    highYieldDebtRatio: 0.10,
    seniorDebtRate: 0.06,
    mezzanineDebtRate: 0.10,
    highYieldDebtRate: 0.12
  };
  applyLBOInputs(inputs);
}

// Reset LBO form
export function resetLBOForm() {
  const inputs = {
    companyName: "",
    purchasePrice: 0,
    equityContribution: 0,
    revenue: 0,
    ebitdaMargin: 0.15,
    revenueGrowth: 0.05,
    growthDecay: 0.005,
    years: 5,
    taxRate: 0.25,
    depreciationRatio: 0.03,
    capexRatio: 0.04,
    workingCapitalRatio: 0.15,
    seniorDebtRatio: 0.60,
    mezzanineDebtRatio: 0.30,
    highYieldDebtRatio: 0.10,
    seniorDebtRate: 0.06,
    mezzanineDebtRate: 0.10,
    highYieldDebtRate: 0.12
  };
  applyLBOInputs(inputs);
} 