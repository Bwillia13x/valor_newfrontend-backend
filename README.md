# Valor IVX — New Frontend/Backend MVP

This standalone MVP demonstrates a DCF engine with multi-stage ramps, sensitivity tools, and a Monte Carlo (MC) simulation. It runs purely in the browser without external dependencies.

## Monte Carlo Parameters

MC perturbs key drivers around the base case to generate a per-share distribution:

- Growth vol (pp): Absolute percentage-point volatility for revenue growth per stage. Input as pp (e.g., 2.0 = ±2.0pp).
- Margin vol (pp): Absolute percentage-point volatility for EBIT margin. Blank defaults to Growth vol.
- S2C vol (%): Relative volatility on Sales-to-Capital ratio (multiplicative). Enter as a percent (e.g., 5 = ±5%).
- Corr(G↔M): Correlation between stage-1 Growth and Margin shocks, clamped to [-0.99, 0.99].
- Trials: Number of MC draws (100–10,000).
- Seed: Optional deterministic seed string for reproducibility.

Correlation mechanics use a simple Cholesky-like construction for two correlated normals:
- Let z1, z2 ~ N(0,1) i.i.d. Then define:
  - Growth shock base: uG = z1
  - Margin shock base: uM = ρ·z1 + sqrt(1-ρ²)·z2
- Growth per stage uses independent normals for stages 2/3 to reduce over-correlation beyond stage 1.
- Margin applies the correlated component primarily in stage 1, independent in later stages.
- S2C volatility is applied multiplicatively as s' = s · (1 + σ · N(0,1)), clamped to ≥0.1 to avoid degenerate reinvestment.

## Reproducibility

- seedStr: Provide a seed string to make the MC run deterministic. The UI stores and reuses your last MC settings.
- Scenario snapshot: Scenarios store both inputs and an MC snapshot (trials, volPP, seedStr, marginVolPP, s2cVolPct, corrGM). Applying a scenario will prepopulate the MC panel and write back to localStorage for parity.
- Deep-link parameters:
  - Core inputs and ramp parameters are encoded in the URL query string.
  - TV method and multiple are also encoded.
  - Advanced MC parameters can be deep-linked via mcMarginVolPP, mcS2CVolPct, mcCorrGM; they are applied on load and persisted to localStorage (valor:mc-settings) for consistency.

## Performance Guidance

- Trials:
  - 1k trials: Fast, good for quick checks.
  - 5k trials: Balanced sampling for presentations and analysis.
  - 10k trials: Heavier, best used on typical modern hardware when needed.
- Runtime expectations: On a typical modern laptop CPU, 1k–5k trials should complete interactively; 10k may take a few seconds. The UI displays ETA and allows cancel.
- Throttling: Progress updates are throttled to ~20 ticks regardless of trial count. The histogram is rendered once at the end (or canceled), avoiding heavy incremental re-rendering.

## Advanced MC Grouping

The Advanced MC controls are visually grouped for clarity and accessibility with a subtle bordered box. Labels include aria-labels and hints to improve screen reader experience.

## Scenarios

- Save/Apply/Delete scenarios from the toolbar. The UI shows a hint “Scenarios include MC settings”.
- Export/Import:
  - Export produces a JSON payload with a schema tag: { "_schema": "valor:scenarios@1", "scenarios": [ ... ] }.
  - Run data can be exported with the schema `_schema: "valor:run@1"`.
  - Import accepts either the schema-wrapped format or a raw array of scenarios.
  - The tool dedupes scenarios by a simple input-key (ticker/wacc/g/years…).
- Backend round-trip buttons (optional) are present if you have a backend running at /api.
- A "Reset All" button is available to clear all `localStorage` data for a clean slate.

## Terminal Value Methods

- Perpetuity (Gordon): TV = FCFF_{n+1} / (WACC - g), discounted back to PV.
- Exit Multiple: TV = EV/FCFF multiple * FCFF_{n+1}, discounted back to PV.
- A TV mix panel shows PV(FCFF) vs PV(Terminal). A counterfactual outline demonstrates the other method’s split for quick audit.

## Accessibility

- Status pill uses aria-live="polite" for progress and state changes.
- Helper aria-labels are added to advanced MC labels for improved screen reader output.
- Skip link and semantic roles are used to improve keyboard and screen reader navigation.
- The Solver modal includes focus trapping and can be closed with the `Escape` key.
- Tab selections are persisted in `localStorage` to maintain the user's view across sessions.

## Files

- index.html: Markup and UI structure (inputs, charts, MC panel, scenarios).
- styles.css: Theme, layout, advanced MC fieldset styles, and components.
- main.js: DCF engine, charts, MC engine with correlation, ETA, cancel support, scenarios, deep-linking, and exports.

## Running

Open index.html in a browser. No build step required. Use the Preset to load sensible defaults, Run to compute, and Monte Carlo to generate distributions. Copy Link for sharing deep-links.
