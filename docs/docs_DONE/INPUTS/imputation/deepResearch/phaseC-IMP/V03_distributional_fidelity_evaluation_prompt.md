# Deep-Research Prompt V03 — DISTRIBUTIONAL-FIDELITY EVALUATION METRICS

> SCOPE GUARD — READ FIRST. This prompt is about **how to MEASURE** whether an imputer restores the
> observed *distribution* — the metric layer that will judge the CP-DRAW leaderboard. Cover: the
> distance/goodness metrics (KS, Cramér–von Mises, Anderson–Darling, Wasserstein/earth-mover, energy
> distance, MMD), calibration diagnostics (PIT histograms, reliability), prediction-interval coverage &
> sharpness, proper scoring rules (CRPS, log-score), and variance/quantile-ratio checks. It must
> confirm or upgrade OpenUBEM's current choice (KS + Wasserstein + a MAE do-no-harm guard). **Do NOT**
> catalogue imputation methods (`V01`/`V02`/`V04`). See `V00_README_variance_preserving_prompt_set.md`
> for shared facts.

---

## What this document is

A metric-by-metric appraisal of how the missing-data, forecasting, and UQ literatures score *whether
imputed values match the observed distribution*, so OpenUBEM's mask-and-recover harness judges the
`draw` tier on the right numbers. The harness already computes KS and Wasserstein (and MAE/RMSE); this
prompt decides whether that is the field norm, what it misses, and what to add.

## Role

Statistical-evaluation / forecast-verification methodologist. Ground each metric in its canonical source
(Gneiting & Raftery for proper scoring rules & CRPS; Gneiting/Balabdaoui/Raftery for calibration &
sharpness; Székely & Rizzo for energy distance; the two-sample-test literature for KS/CvM/AD/MMD) and,
where possible, in an imputation or building-stock evaluation that actually used it.

## Why this matters (so you scope correctly)

OpenUBEM signed Phase B "accurate" on NMBE — a mean-bias metric structurally blind to variance collapse.
The whole point of the `draw` tier is to fix a distributional defect, so it MUST be judged on
distributional metrics, and the manager must not repeat the NMBE mistake. This prompt establishes a
principled, sourced metric set: what each metric sees, what it misses, how to read it for
`year_built`/`levels` (continuous) and `use_class` (categorical), and how to combine "did it restore
spread?" with the "did it do no harm to central accuracy?" guard.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Distributional-fidelity metric catalogue

| Metric | What it measures | Sensitive to variance collapse? | Continuous / categorical / both | Bounded & interpretable? | Reference impl | Source |
|---|---|---|---|---|---|---|
| Kolmogorov–Smirnov statistic |  |  | continuous |  | `scipy.stats.ks_2samp` |  |
| Cramér–von Mises |  |  | continuous |  | `scipy.stats` |  |
| Anderson–Darling (k-sample) |  |  | continuous |  | `scipy.stats` |  |
| Wasserstein / earth-mover |  |  | continuous |  | `scipy.stats.wasserstein_distance` |  |
| Energy distance |  |  | both |  | `dcor` |  |
| Maximum mean discrepancy (MMD) |  |  | both |  | custom |  |
| Variance ratio σ_imp/σ_obs · IQR ratio |  | (directly) | continuous |  | trivial |  |
| PIT histogram / calibration |  |  | continuous |  | custom |  |
| Prediction-interval coverage + sharpness |  |  | continuous |  | custom |  |
| CRPS (continuous ranked prob. score) |  |  | continuous (dist. output) |  | `properscoring` |  |
| Total-variation / Jensen–Shannon (categories) |  |  | categorical |  | `scipy` |  |
| Multinomial calibration (category proportions) |  |  | categorical |  | custom |  |

### Table 2 — What each metric would report for a mean/median collapse vs a good draw

Illustrate on OpenUBEM's measured case (σ_imp/σ_obs ≈ 0.31–0.44, IQR_imp ≈ 0).

| Metric | Value under group-median collapse (qualitative) | Value under a faithful draw | Does it cleanly separate the two? | Source |
|---|---|---|---|---|
| KS |  |  |  |  |
| Wasserstein |  |  |  |  |
| Energy distance |  |  |  |  |
| Variance / IQR ratio |  |  |  |  |
| PIT / coverage |  |  |  |  |
| CRPS |  |  |  |  |

### Table 3 — Recommended CP-DRAW metric set

| Role | Metric(s) | Why chosen | Pass/read guidance (what "good" looks like) | Source |
|---|---|---|---|---|
| Primary — variance restored |  |  |  |  |
| Secondary — full-distribution match |  |  |  |  |
| Do-no-harm — central accuracy kept |  |  |  |  |
| Categorical fidelity (`use_class`) |  |  |  |  |
| Aggregate-unbiasedness guard (kept from CP-2) | NMBE |  | \|NMBE\|→0 by construction for an unbiased draw |  |

### Table 4 — Peer imputation/UBEM studies: which metrics they report

| Study / tool | Imputation evaluated | Distributional metric(s) used | Did they catch/avoid variance collapse? | Source |
|---|---|---|---|---|
|  |  |  |  |  |

---

## Part C — Synthesis (the metric ruling)

Give: (1) the **recommended CP-DRAW metric set** — the 1 primary + 1–2 secondary distributional metrics
plus the do-no-harm guard — with an explicit statement of what each adds over KS/Wasserstein alone;
(2) whether OpenUBEM should add **energy distance / MMD** (multivariate, catches joint-distribution
defects the marginal KS misses) given targets are imputed one at a time but correlate
(`levels`↔`height`); (3) the right **categorical** fidelity metric for `use_class`; (4) a plain reading
rule so the leaderboard is not over-interpreted — e.g. "a draw method is expected to *lose* on MAE and
*win* on KS/Wasserstein; that trade is the intended result, not a regression"; (5) an explicit warning
list of **metrics that would repeat the NMBE blind-spot** if used alone.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C metric ruling.
3. Cite the metric's methods source and, separately, any imputation-evaluation application.
4. **"Confidence and caveats":** which metric is easiest to misread at OpenUBEM's small holdout sizes
   (n≈130–560) — small-sample behaviour of KS/energy-distance/CRPS.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Every metric states explicitly whether it is sensitive to variance collapse** — that is the whole
  point; a metric that is not (like NMBE/MAE alone) must be labelled a do-no-harm guard, never a
  fidelity metric.
- **Address small-sample reliability** — OpenUBEM's per-cell holdouts are small.
- **Cover both continuous and categorical** targets.
- **No fabricated precision;** mark GAPs. **Stay on topic** — evaluation metrics only, no imputation
  methods.
