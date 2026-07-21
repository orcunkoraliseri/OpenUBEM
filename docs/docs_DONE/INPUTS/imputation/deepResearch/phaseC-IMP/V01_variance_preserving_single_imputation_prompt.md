# Deep-Research Prompt V01 — VARIANCE-PRESERVING SINGLE IMPUTATION (the donor / stochastic menu)

> SCOPE GUARD — READ FIRST. This prompt widens and ranks the **single-imputation** methods that
> preserve the observed spread — i.e. every method that returns ONE fill per building but draws it so
> the imputed *distribution* matches the observed one, instead of collapsing to the stratum centre.
> Cover: stochastic regression imputation, predictive-mean-matching (PMM) and its approximate-Bayesian
> variants, the hot-deck/donor family (random, nearest-neighbour, spatial, sequential), KDE /
> parametric / copula distribution sampling, and Bayesian-bootstrap / ABB draws. **Do NOT cover**
> proper multiple imputation & Rubin's-rules propagation (that's `V02`), evaluation metrics (`V03`), or
> neural/generative/foundation samplers (`V04`). See `V00_README_variance_preserving_prompt_set.md` for
> shared facts.

---

## What this document is

A method-by-method appraisal of **variance-preserving single imputers** for building attributes,
benchmarked against OpenUBEM's current group-median/mode fill and its seeded `draw`-tier menu (KDE-draw,
PMM, hot-deck, stochastic-residual, categorical-frequency). The goal is a finalized, sourced,
zero-fitted-parameters registry: which methods to keep, which to add, which to drop, for each target
(`year_built`, `levels`, `height` continuous; `use_class` categorical).

## Role

Missing-data-methods analyst with a building-stock focus. Ground each method in its canonical source
(van Buuren for PMM/FCS; Andridge & Little for hot-deck; Rubin & Schenker for the approximate Bayesian
bootstrap; Morris/White/Royston for PMM pitfalls) **and** in at least one documented building/spatial
attribute application where available.

## Why this matters (so you scope correctly)

OpenUBEM's fill collapses variance because it returns a stratum central value. Every method here fixes
that by returning a *draw* — but they differ in how well-matched the donor is, how they behave at small
n (some OpenUBEM cells have only a few hundred observed rows), whether they can extrapolate
catastrophically (the arc already hit an AD-5000+ `mice`/`linear` footgun), and how naturally they emit
a confidence flag. This prompt gives the manager the evidence to finalize the `draw` registry.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Variance-preserving single-imputer catalogue

| Method | How it draws (one sentence) | Preserves marginal variance? (yes/partial) | Guarantees a real observed value? | Small-n behaviour (n≈200) | Extrapolation risk | Reference impl | Source |
|---|---|---|---|---|---|---|---|
| Stochastic regression imputation (pred + empirical residual) |  |  |  |  |  | `sklearn` + custom |  |
| Predictive mean matching (PMM, type-1/2) |  |  |  |  |  | R `mice`, `statsmodels` |  |
| Approximate-Bayesian PMM (proper) |  |  |  |  |  | R `mice` |  |
| Random hot-deck (within-cell) |  |  |  |  |  | R `VIM`/`hot.deck` |  |
| Nearest-neighbour / kNN hot-deck (donor draw, not average) |  |  |  |  |  | `sklearn` (custom draw) |  |
| Spatial hot-deck (neighbour donor) |  |  |  |  |  | custom (T06 primitives) |  |
| KDE / kernel distribution sampling |  |  |  |  |  | `scipy.stats.gaussian_kde` |  |
| Parametric distribution sampling (e.g. lognormal fit) |  |  |  |  |  | `scipy.stats` |  |
| Copula-based sampling (multivariate spread) |  |  |  |  |  | `copulas`/`statsmodels` |  |
| Bayesian bootstrap / ABB donor draw |  |  |  |  |  | custom |  |
| Categorical: empirical-frequency draw (vs mode) |  |  |  |  |  | custom |  |
| Categorical: latent-class / conditional-multinomial draw |  |  |  |  |  | custom |  |

### Table 2 — Reported performance on building / spatial attributes

Only rows where a study actually measured a *distribution-preserving* imputer on building or spatial
attribute data (not generic tabular benchmarks). Report the distributional metric, not just RMSE.

| Method | Attribute (height, vintage, area, use, storeys) | Distributional metric + value (KS / Wasserstein / variance-ratio / coverage) | Point-error cost vs a mean/median fill | Dataset / study | Source |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

### Table 3 — Fit to OpenUBEM's two hard constraints + the seeded menu

| Method | Zero-fitted-parameters? (default/convention, no target-tuned knobs) | Natural provenance/confidence signal (what dispersion measure → HIGH/MED/LOW?) | Already in the seeded `draw` menu? | Verdict (adopt / add / skip) | Source |
|---|---|---|---|---|---|
| Stochastic residual |  |  | yes (`resid`) |  |  |
| PMM |  |  | yes (`pmm`) |  |  |
| Approximate-Bayesian PMM |  |  | no |  |  |
| Random hot-deck |  |  | partial (`hotdeck`=spatial) |  |  |
| Spatial hot-deck |  |  | yes (`hotdeck`) |  |  |
| KDE sampling |  |  | yes (`kde`) |  |  |
| Parametric / copula sampling |  |  | no |  |  |
| Bayesian bootstrap / ABB |  |  | no |  |  |
| Empirical-frequency (categorical) |  |  | yes (`catfreq`) |  |  |

### Table 4 — Per-target recommendation for OpenUBEM

| OpenUBEM target | Current fill | Best variance-preserving method(s), ranked | Why (assumption fit + small-n behaviour) | Source |
|---|---|---|---|---|
| `year_built` (continuous, MAR, spatially clustered) | group-median | | | |
| `levels` (continuous, small-count, integer) | group-median | | | |
| `height` (continuous, correlated w/ levels) | group-median | | | |
| `use_class` (categorical) | group-mode | | | |

---

## Part C — Synthesis (the finalized `draw` menu)

Give: (1) a ranked, per-target shortlist of the methods OpenUBEM's opt-in `draw` tier should implement,
distinguishing **must-add** (fills a gap in the seeded 5) from **redundant** (already covered);
(2) an explicit call on **PMM vs KDE-draw vs stochastic-residual** for `year_built` specifically — which
best restores spread without the `mice`/`linear` extrapolation footgun, and why; (3) the **integer/count
handling** for `levels` (should draws be rounded, or drawn from an integer-respecting donor?); (4) for
each recommended method, the exact **dispersion signal** that should map to the HIGH/MED/LOW confidence
token; (5) any method that must be **flagged as a non-starter** for violating zero-fitted-parameters or
provenance, with the reason.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C.
3. Cite the methods source and, separately, any building-application source.
4. **"Confidence and caveats":** which method's suitability for UBEM-scale data is least evidenced.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Every method states the missing-data mechanism it is valid under** (MCAR/MAR/MNAR) and its
  **small-n floor** (does it need thousands of rows, or work at n≈200?).
- **Keep distributional fidelity and point accuracy separate** — a good draw method is *expected* to
  score slightly worse on MAE than a median fill; say so, and judge on the distributional metric.
- **Flag extrapolation-prone methods** (globally-linear predictors) explicitly — the arc already has an
  AD-5000+ footgun and an observed-range clamp.
- **Respect the two hard constraints;** flag any violator. **No fabricated precision;** mark GAPs.
- **Stay on topic** — single-draw methods only; no multiple-imputation propagation, no metrics deep-dive,
  no neural/generative.
