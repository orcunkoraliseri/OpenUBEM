# Deep-Research Prompt V04 — MODERN DISTRIBUTIONAL IMPUTATION (the frontier check)

> SCOPE GUARD — READ FIRST. This prompt covers **modern methods that emit a full predictive
> distribution or samples** rather than a point — quantile-regression forests, conformalized quantile
> regression, distributional gradient boosting (NGBoost), generative imputers (GAIN, VAE/denoising-AE,
> normalizing flows, diffusion), and pretrained tabular foundation models (TabPFN and successors) used
> as samplers. It scores each against classical donor baselines (`V01`) AND against the arc's
> **four-filter test**. **Do NOT** re-cover classical single-draw methods (`V01`), multiple-imputation
> propagation (`V02`), or metric definitions (`V03`). See `V00_README_variance_preserving_prompt_set.md`
> for shared facts, and the general set's `M05`/`M06`/`M10` + `RESULTS_phaseE.md` for the arc's prior
> frontier rulings (do not contradict them silently — update them with evidence).

---

## What this document is

A frontier appraisal: do any modern distribution-emitting imputers **beat classical donor methods**
(PMM, hot-deck, KDE-draw) for OpenUBEM's targets, at OpenUBEM's scale, without breaking its rules? The
arc has already ruled deep-generative **SKIP** (classical dominates below ~n=30k), GNN **REJECT**
(spatial signal already captured), LLM **FIRM DISQUALIFICATION** (hallucination/no-provenance), and
TabPFN **NOT READY** (`RESULTS_phaseE.md`). This prompt re-tests those rulings **specifically for the
variance-preservation objective** — because a method judged "no better on point accuracy" might still be
the best at restoring *spread*, which changes the calculus.

## Role

ML-for-tabular / probabilistic-forecasting researcher. Ground each method in its canonical source
(Meinshausen for QRF; Duan et al. for NGBoost; Romano/Sesia/Candès for conformalized quantile
regression; Yoon et al. for GAIN; Hollmann et al. for TabPFN; the flow/diffusion-imputation papers)
**and** in any tabular/spatial benchmark that measured *distributional* recovery, not just RMSE.

## Why this matters (so you scope correctly)

The arc's earlier frontier rejections were argued on **point-accuracy** grounds and the four filters.
The variance-preservation objective is different: it rewards methods that *output a distribution*. Some
modern methods do this natively and cheaply (QRF, conformal, NGBoost) and might clear the four filters
where full generative models do not. The manager needs to know whether to (a) keep the `draw` tier
purely classical, (b) add ONE distribution-emitting ML method as an opt-in registry entry, or (c) hold
the line at classical and re-confirm the Phase-E rulings for this objective too.

---

## REQUIRED OUTPUT TABLES — fill every cell

### The four-filter test (apply to EVERY method in Table 1)

1. **Zero-fitted-parameters** — no knob tuned against a validation EUI/attribute target (library
   defaults / stated α are fine).
2. **Reproducible & offline** — deterministic under a fixed seed; runs locally, no external API/service.
3. **Provenance** — emits a per-building confidence/flag naturally.
4. **Viable at scale** — works at hundreds-to-low-thousands observed rows per cell (not tens of
   thousands).

### Table 1 — Distribution-emitting method appraisal

| Method | Native output (interval / quantiles / samples / full density) | Restores marginal variance? | F1 zero-param | F2 offline/deterministic | F3 provenance | F4 small-n viable | Beats classical donor on *distribution*? | Source |
|---|---|---|---|---|---|---|---|---|
| Quantile regression forests (QRF) |  |  |  |  |  |  |  |  |
| NGBoost (distributional GBM) |  |  |  |  |  |  |  |  |
| Conformalized quantile regression (CQR) |  |  |  |  |  |  |  |  |
| Bayesian additive regression trees (BART) |  |  |  |  |  |  |  |  |
| GAIN (generative adversarial imputation) |  |  |  |  |  |  |  |  |
| VAE / denoising autoencoder imputation |  |  |  |  |  |  |  |  |
| Normalizing-flow imputation |  |  |  |  |  |  |  |  |
| Diffusion-model imputation (e.g. TabDDPM/TabCSDI) |  |  |  |  |  |  |  |  |
| TabPFN (+ successors) as sampler |  |  |  |  |  |  |  |  |

### Table 2 — Reported distributional performance vs classical baselines

Only rows where a study measured a *distributional* metric (KS/Wasserstein/CRPS/coverage), on
tabular/spatial data at a comparable scale.

| Method | Baseline it was compared to | Distributional metric + result | Sample size (n) | Dataset / study | Source |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

### Table 3 — Verdict vs the arc's existing Phase-E rulings

| Method family | Phase-E ruling (M05/M06/M10, RESULTS_phaseE) | Does the variance-preservation objective change it? | New verdict for the `draw` tier | Source |
|---|---|---|---|---|
| Deep generative (GAIN/VAE/flow/diffusion) | SKIP (classical dominates <~30k) |  |  |  |
| GNN / spatial deep | REJECT (signal already captured) |  |  |  |
| LLM-prompted | FIRM DISQUALIFICATION |  |  |  |
| TabPFN / foundation | NOT READY |  |  |  |
| Distributional trees (QRF/NGBoost/CQR) | *not previously assessed* |  |  |  |

---

## Part C — Synthesis (the frontier ruling)

Give: (1) a single verdict — **keep the `draw` tier purely classical**, or **add exactly one
distribution-emitting ML method** as an opt-in registry entry (name it), justified by clearing all four
filters AND beating classical donors on a distributional metric; (2) special attention to
**quantile-regression forests / conformalized quantile regression** — the most likely to clear the
filters (deterministic, offline, native intervals → provenance, moderate-n) — do they actually restore
`year_built`/`levels` spread better than PMM/KDE-draw, or just re-describe the same uncertainty? (3) an
explicit **re-confirmation or revision** of each Phase-E ruling for this objective (do not silently
contradict `RESULTS_phaseE.md`); (4) if the answer is "hold the line at classical," say so plainly and
give the one-line reason the frontier does not earn its place here.

## Output format (follow exactly)

1. **Lead with Tables 1–3 fully populated** (four-filter columns filled for every method).
2. Then Part C ruling.
3. Cite the method's source and, separately, any distributional-benchmark source.
4. **"Confidence and caveats":** which method is most likely to be re-rated within a year (fast-moving
   area), and what evidence would flip the verdict.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Fill the four-filter columns for every method** — a method failing any single filter is out for the
  default/opt-in registry regardless of accuracy; say which filter killed it.
- **Judge on distributional recovery, not point RMSE** — that is the objective; a method that only
  improves RMSE adds nothing over the existing `ml` tier.
- **Do not silently contradict the Phase-E rulings** — cite and update them.
- **Respect the two hard constraints;** flag violators. **No fabricated precision;** mark GAPs.
- **Stay on topic** — distribution-emitting modern methods only.
