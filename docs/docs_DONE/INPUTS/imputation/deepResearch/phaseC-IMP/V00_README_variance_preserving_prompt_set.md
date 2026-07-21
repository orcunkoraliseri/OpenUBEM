# Variance-Preserving Imputation — Deep-Research Prompt Set (INDEX)

> READ FIRST. This set is a **focused follow-up to the general imputation set**
> (`../general/00_README_imputation_prompt_set.md`, M01–M10). It exists because of one specific,
> measured finding: OpenUBEM's shipped statistical tier — and even the built-but-off classical-ML
> tier — fills missing continuous inputs with a **single point estimate per stratum** (group median /
> group mode / neighbour average), which **mathematically collapses the distribution's spread**. In
> the Phase-B/C predicted-vs-actual scatter figures this shows as a **flat horizontal band**: the real
> `year_built`/`levels` are genuinely spread, the imputed values are nearly constant. The manager has
> documented this in `../../implementation/IMPLEMENTATION_phaseC_ml_imputer.md` (Part I §I.4–I.6) and
> `../../../../../docs_EXPLANATION/OpenUBEM_imputation_methods.md` (§6–7), and has drafted an opt-in
> `draw`-tier plan (`../../implementation/IMPLEMENTATION_phaseC_ml_imputer.md` Part II) seeding
> five candidate methods (KDE-draw · PMM · hot-deck · stochastic-residual · categorical-frequency).
> **This prompt set exists to find MORE and BETTER methods before that plan is executed** — to widen
> and rank the candidate menu with sourced evidence, so the manager finalizes the `draw`-tier registry
> on the literature, not on a first guess.
>
> Run each prompt in your deep-research tool (Gemini Antigravity). Save each answer beside it as
> `RESULT_<id>_<slug>.md`. The manager audits each RESULT, then updates the `draw`-tier plan's method
> menu (§3/§5) accordingly.

---

## The exact decision this set must inform

The seeded `draw`-tier plan already has five candidate methods. This set must answer, with sources:

1. **Is the seeded menu complete?** Which *additional* variance-preserving / distribution-preserving
   imputers exist that we have not listed (proper multiple imputation, Bayesian bootstrap / ABB,
   approximate-Bayesian PMM, quantile-regression donors, conformal-interval draws, sequential
   regression multivariate imputation, copula sampling, …)?
2. **Which of the (seeded + newly-found) methods best fit OpenUBEM's two hard constraints** —
   **zero-fitted-parameters** and **mandatory provenance** — at OpenUBEM's data scale (hundreds to a
   few thousand observed rows per cell; low-dimensional tables; heavy MAR)?
3. **How should we MEASURE variance restoration** so the CP-DRAW leaderboard is judged on the right
   metrics (the current plan uses KS + Wasserstein + a MAE do-no-harm guard — is that the field norm,
   or are energy-distance / PIT-calibration / interval-coverage / sharpness better)?
4. **Does anything modern (ML/generative/foundation) actually beat classical donor methods** for our
   n and constraints, or does it fail the four-filter test the arc already applied to Phase E
   (zero-fitted-params · reproducible-offline · provenance · viable at hundreds-to-low-thousands
   scale)?

| Question | Primary prompt |
|---|---|
| Complete the donor / stochastic single-imputation catalogue | `V01` |
| Multiple imputation + proper uncertainty propagation through a UBEM | `V02` |
| Distributional-fidelity evaluation metrics (how to score variance restoration) | `V03` |
| Modern/ML/generative distribution-preserving imputation — frontier check under the four filters | `V04` |

---

## The prompts

| # | File | What it learns | Priority |
|---|------|----------------|----------|
| V01 | `V01_variance_preserving_single_imputation_prompt.md` | The full **single-draw** catalogue that preserves variance: stochastic regression, predictive-mean-matching (PMM) + its approximate-Bayesian variants, hot-deck/donor families, KDE/parametric/copula sampling, Bayesian bootstrap / ABB — assumptions, small-n behaviour, provenance story. Widens the seeded 5-method menu. | **core** |
| V02 | `V02_multiple_imputation_uncertainty_propagation_prompt.md` | **Multiple imputation** (MICE/FCS proper, Rubin's rules) and how to carry M draws through Stage-3→5 into an EUI ensemble — is per-building distributional recovery worth the M× simulation cost, or is single stochastic imputation + a confidence flag adequate for OpenUBEM's aggregate-EUI purpose? | high |
| V03 | `V03_distributional_fidelity_evaluation_prompt.md` | How the field **measures** whether imputed values match the observed *distribution* (not just the mean): KS, Wasserstein/energy distance, PIT histograms & calibration, prediction-interval coverage & sharpness, variance-ratio. Validates or upgrades the CP-DRAW metric set. | **core** |
| V04 | `V04_modern_distributional_imputation_frontier_prompt.md` | The frontier: methods that emit a **distribution or samples** rather than a point — quantile-regression forests, conformalized quantile regression, GAIN/VAE/normalizing-flow/diffusion imputers, TabPFN-style pretrained samplers — scored against the arc's **four-filter test** and classical donor baselines. Does anything modern earn its place? | medium |

> **Load-bearing core: `V01 + V03`.** They decide the finalized `draw`-tier menu and the metric it is
> judged on. Run them first. `V02` matters only if per-building *uncertainty propagation* (not just a
> realistic marginal) is wanted. `V04` is the research-frontier check — run only if V01's classical
> menu looks insufficient.

---

## Shared facts (all prompts assume these — do not re-derive)

Grounded in `../../implementation/IMPLEMENTATION_phaseC_ml_imputer.md`,
`../../../../../docs_EXPLANATION/OpenUBEM_imputation_methods.md`, and the general set's shared facts
(`../general/00_README_imputation_prompt_set.md`).

- **The problem is variance collapse, not bias.** The production `_statistical_tier` fills continuous
  targets with the **group-wise stratified median** and categoricals with the **group mode** — one
  value per stratum. The built-but-off `ml` tier's winner (`knn`) is a distance-weighted neighbour
  **average**. All are single point estimates → they collapse spread.
- **Measured evidence (the harness that will also judge the fix).** On the pooled 12-cell holdout,
  `σ(imputed)/σ(actual) ≈ 0.31–0.44` and the imputed inter-quartile range is `≈ 0` (the middle 50% of
  imputed values is a single constant), while the real data spans ~29–49 distinct `year_built` values
  (σ ≈ 23–34) and `levels` 1–63 (σ ≈ 13). The real data is genuinely spread; the flatness is entirely
  on the prediction side.
- **Why it was missed, and the right metrics.** The gate metrics — **NMBE** (mean-bias) and **MAE/RMSE**
  (point error) — are structurally blind to variance collapse: a constant-mean predictor is unbiased by
  construction and scores well on MAE precisely *because* it collapses to the centre. The metrics that
  DO see it — **KS statistic** and **Wasserstein distance** — are already computed by
  `openubem/validation/mask_recover.py::score_continuous`. This set must confirm/upgrade that metric
  choice (see `V03`).
- **OpenUBEM's purpose is aggregate EUI.** The fleet rollup depends on the *centre* of the distribution,
  which is already unbiased (CP-2: NMBE +0.49% NYC / +0.08% LA). So variance collapse does **not** bias
  the current headline. The `draw` tier is wanted for the *future* case where the **per-building
  distribution/spread** matters (e.g. retrofit targeting, risk tails) — every prompt must keep this
  distinction (marginal-fidelity vs aggregate-unbiasedness) sharp.
- **A variance-preserving primitive already exists in-repo but is unwired:**
  `impute_column(method="kde")` fits `scipy.stats.gaussian_kde` on observed values and returns
  `kde.resample(...)` — a draw, not a central value. The seeded M1 reuses it. The İşeri et al. in-repo
  paper (`../../resources/…`) is itself a KDE-based *distribution-sampling* method — every prompt should
  check whether peer practice supports generalizing draw-based fills.
- **Ship posture is fixed: opt-in / OFF.** The `draw` tier will NOT enter the default pipeline in this
  arc; the default stays byte-identical (CP-1 intact), evaluation is LOCAL (no cluster, no EnergyPlus).
  So a method's cost is judged on *local* feasibility, not on a simulation budget.

## The two hard constraints (a method that fails either is a non-starter — say so)

1. **Zero-fitted-parameters.** No bandwidth, donor-`k`, interval level, prior, or network weight may be
   *tuned against a validation EUI or attribute target*. A published convention or library default is
   fine (KDE = Scott's rule; donor `k` = fixed; conformal level = a stated α). A method whose accuracy
   depends on target-tuned knobs violates the arc's core rule — flag it.
2. **Mandatory provenance.** Every imputed value must leave a queryable marker (a flag token +
   HIGH/MED/LOW confidence), matching the `FUSED_*` / `HOTDECK_*` / `GROUPMODE_MED` / `ML_*` /
   `DRAW_*` convention. A method that cannot report *which* buildings it touched and *how confident* is
   unacceptable regardless of accuracy.

## Method / source roster (use across prompts where relevant)

van Buuren *Flexible Imputation of Missing Data* (MICE, PMM, FCS) · Little & Rubin *Statistical Analysis
with Missing Data* (multiple imputation, Rubin's rules) · Andridge & Little (hot-deck review) · Rubin &
Schenker (approximate Bayesian bootstrap) · Morris/White/Royston (PMM tuning & pitfalls) · Meng
(congeniality) · Meinshausen (quantile regression forests) · Romano/Candès (conformalized quantile
regression) · Yoon et al. (GAIN) · Hollmann et al. (TabPFN) · plus the building-stock imputation
literature already catalogued in the general set (İşeri, Wang, Nägeli, Mastrucci, Kristensen,
Cerezo/Sokol) and the UBEM peer tools (UMI, CEA, CityBES, AutoBEM, URBANopt, TEASER).

## Conventions for every answer (enforced by each prompt)

1. **Lead with the filled tables;** prose after. Empty / "TBD" cells are failures.
2. Every method/value carries a **named, dated source** (author, venue, year; library docs; DOI/URL).
   Blogs/vendor pages last resort, labelled.
3. **Always compare against OpenUBEM's actual behaviour** (the group-median/mode fill and the seeded
   `draw`-menu, given inline in each prompt) — say whether the method is strictly better, equivalent,
   or worse for our targets (`year_built`, `levels`, `height`, `use_class`).
4. **No fabricated precision.** If a value is your synthesis, say so. If unpublished, write **"GAP —
   needs manager decision"** + the closest defensible default and its source.
5. **Keep the two evaluation lenses separate:** per-building *distributional fidelity* (the goal here)
   vs aggregate-EUI *unbiasedness* (already achieved). Never conflate them.
6. **Respect the two hard constraints** in every recommendation (zero-fitted-parameters, provenance).
7. **Stay on topic per prompt;** do not re-litigate archetype classification or geometry/zoning.

---

*OpenUBEM — variance-preserving imputation deep-research set (Phase-C follow-up). Markdown only;
binding specs remain `docs/docs_main/`. Grounded in the Phase-C variance-collapse finding and the
opt-in `draw`-tier plan. 2026-07-16.*
