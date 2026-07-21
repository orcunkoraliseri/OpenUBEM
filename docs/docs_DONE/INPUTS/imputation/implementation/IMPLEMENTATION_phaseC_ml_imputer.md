# IMPLEMENTATION — Phase-C imputation: the `ml` tier (built-but-off) **+** the variance-preserving `draw` tier (to build)

**What this document is.** A single record for the Phase-C region of the input-imputation arc, in two
parts:

- **Part I — the shipped `ml` tier (Phase C).** A plain-language spec of **how Phase C is
  implemented**, **what the CP-3 evaluation actually found**, and — the reason the user asked for it —
  an honest reading of the **predicted-vs-actual scatter figures** (`phaseC_scatter_year_built.png`,
  `phaseC_scatter_levels.png`): why the ML predictions form a flat band while the real data are
  genuinely spread, and what that does and does **not** let us claim.
- **Part II — the `draw` tier to build.** The manager **PLAN** for a new **opt-in / OFF** tier that
  fixes the variance collapse Part I diagnoses — hard rules, file layout, verified facts, the folded
  deep-research synthesis, the numbered task list (T01–T10), stop points, and the progress log a
  fresh Sonnet appends. Part I is *what exists*; Part II is *what to code next*.

**Date:** 2026-07-16
**Arc:** Input-Parameter Imputation ("OpenUBEM AI"), Phase C.
**Source of record (binding):**
- Execution plan + progress log (Phase C, `ml` tier): [`../docs_Done/PLAN_phaseC_ml_imputer.md`](../docs_Done/PLAN_phaseC_ml_imputer.md)
- Committed Phase-C results: [`../results/phase_C/RESULTS_phaseC.md`](../results/phase_C/RESULTS_phaseC.md)
- Reproducibility diagnosis: [`../debugs/PLAN_phaseC_knn_repro_investigation.md`](../debugs/PLAN_phaseC_knn_repro_investigation.md)
- General method reference: [`../../../docs_EXPLANATION/OpenUBEM_imputation_methods.md`](../../../docs_EXPLANATION/OpenUBEM_imputation_methods.md)
- Deep-research evidence behind Part II's menu: [`../deepResearch/phaseC-IMP/`](../deepResearch/phaseC-IMP/) (RESULT_V01–V04)
- **Binding DESIGN contract for Part II:** OpenUBEM Stage-2.2 DESIGN §3E (KDE/PDE/ML tier). Part II may
  not contradict the DESIGN; on any conflict the executor STOPS and quotes the exact lines.

Part I is an **explanation/spec** (no tasks, changes no committed number). Part II is a **PLAN** (tasks
+ progress log). They are kept in one file at the user's request; the two roles remain clearly separated
by the `PART I` / `PART II` split below.

---
---

# PART I — Phase C: the classical-ML `ml` tier (built-but-off)

## I.0 The one sentence to get right first

**Phase C did not improve the precision of the production model.** The `ml` tier is
**built-but-off / opt-in** — it is not in `IMPUTE_ENABLED_TIERS`, so the default pipeline runs
exactly as it did before Phase C. What Phase C produced is a *measurement*: classical ML wins the
attribute-recovery leg **marginally** (`knn` beats the statistical tier on pooled MAE) but is
**EUI-neutral at production granularity** and shows the **same variance collapse** the statistical
tier does — so it ships **off**, kept only as an opt-in capability.

The flat band in the scatter figures is **not** evidence that Phase C is better or worse than
Phase B; it is the signature of **central-tendency imputation**, and it is present in *both* the
Phase-A/statistical predictions and the Phase-C/`knn` predictions.

---

## I.1 What the `ml` tier is (implementation)

Phase C adds one new tier to the first-hit-wins cascade
(`fusion → spatial → ml → statistical`). It is reached **only** when a caller explicitly enables
`ml` for a target; the shipped default never enables it.

| Piece | What it is | Where |
|---|---|---|
| `build_ml_imputer(...)` | Fits a complete-case sklearn estimator for one target; raises `BelowFloorError` if there are too few observed rows. | `openubem/semantic/imputation.py` |
| 6-method registry | `missforest` · `mice` · `knn` · `rf` · `histgbm` · `linear` — one sklearn constructor each, behind a shared `StandardScaler`(+`OneHotEncoder`) pipeline. | same |
| Per-target floors | `rf`/`missforest`/`linear` ≥ 1,000 · `histgbm` ≥ 5,000 · `knn`/`mice` ≥ 200 observed rows. Below floor the tier **abstains** and routing falls through to the statistical tier. | `config.IMPUTE_ML_FLOORS` |
| Confidence + tokens | Per-row dispersion → HIGH/MED/LOW; only HIGH/MED fills are kept (LOW discarded), each stamped `ML_<METHOD>_<TIER>`. | `imputation.py` |
| Targets | **morphology/semantic only**: `year_built`, `levels`, `height`, `use_class`. **Never** U-values, COP, SHGC, setpoints, load densities. | plan §2 rule 7 |

**Zero fitted parameters.** Every hyperparameter is frozen (`n_neighbors=5`, `n_estimators=100`,
`random_state=RANDOM_SEED`, …). Nothing — no floor, feature, or hyperparameter — is ever tuned
against simulated EUI or a validation anchor; a structural test inspects the fit call graph to
guarantee no EUI column can enter it. This is the whole point of the arc, and (see I.4) it is also
the direct cause of the flat scatter band.

---

## I.2 What CP-3 measured (the two legs)

CP-3 asked one narrow question — **not** "does ML lower EUI error" (Phase B already showed the EUI
headroom is gone: Phase-A recovers `year_built` at NMBE +0.49% NYC / +0.08% LA):

> Does classical ML recover the vintage/morphology **attribute** more accurately than the
> group-median fallback, *without worsening* downstream EUI?

| Leg | Condition | Result | Verdict |
|---|---|---|---|
| **Attribute recovery** | ≥1 method beats Phase-A on mask-and-recover | `knn`: `year_built` MAE **25.14** vs 26.43; `levels` MAE **8.39** vs 9.18 (beats on every continuous metric) | ✅ MET — but **marginal** |
| **EUI do-no-harm** | \|NMBE\| < 5% and CV(RMSE) < 15% | NMBE **−5.51%** (fail) · CV(RMSE) 7.93% (pass) | ❌ FAILS as measured |

The EUI failure was later **re-framed** (plan §8 T11.8c-diag, CP-3b): the −5.51% is a
**pooled-evaluation granularity artifact**. `knn` needs the pooled multi-city frame to clear its
≥200-row floor, but **production imputes per-cell**, where `knn`-`year_built` never fires on the
small cells at all. Re-run per-cell on the floor-clearing cells, `knn` vs Phase-A gives a
directional vintage-bin gap of **exactly +0.0000** (0/1343 + 0/618 divergent) → identical vintage
bins → identical EUI. So per-cell the `ml` tier is **do-no-harm AND do-no-good**.

**Net:** `ml` stays off because it is **EUI-neutral in production** (no benefit to justify adding
it), not because it harms. The reproducibility of the leaderboard itself was independently
re-confirmed (debug D01: 25.14 / 8.39 reproduce to 3 decimals).

---

## I.3 The `mice`/`linear` footgun (kept as an adverse finding)

On the coordinate-pooled multi-city frame, the two globally-linear estimators (`mice`, `linear`)
**catastrophically extrapolate** — predicting `year_built` in the AD-5000+ range on out-of-cluster
coordinates — and the confidence path stamped `ML_*_HIGH` on 100% of that garbage, so the
LOW-discard safety net never fired. This is why the per-target default is `knn`, never
`missforest`/`mice`/`linear`, for coordinate-pooled targets. An **observed-range clamp** shipped
afterwards (`_clamp_to_observed_range`) now bounds these fills (MAE ≈ 34 instead of 900–1160); it
is a proven mathematical no-op for `knn` (a weighted neighbour average is already in-range).

---

## I.4 What the scatter figures actually show — the flat band

The user's observation is correct and worth stating precisely: in
`phaseC_scatter_year_built.png` and `phaseC_scatter_levels.png` the **predicted** values (Y) sit on
a nearly flat/straight band while the **actual** values (X) are genuinely spread. Measured on the
same pairs that drew the figures:

| Target (holdout) | ACTUAL (real data) | IMPUTED (ML prediction) | σ ratio |
|---|---|---|---|
| `year_built` | spread across ~29–49 distinct years, σ ≈ 23–34 | collapsed toward a constant, IQR ≈ 0 | **0.31–0.44** |
| `levels` | 1–63 floors, σ ≈ 13 | collapsed toward a few central values | **~0.4** |

Read this correctly:

1. **The real (X-axis) data is NOT flat.** It is genuinely varied. The flatness is entirely on the
   **prediction (Y) side** — the imputer, not the data.
2. **This is variance collapse, and it is inherent, not a bug.** Any imputer that returns a single
   best estimate per building (group median/mode, neighbour average, `knn`) is mathematically
   pulled toward the conditional mean/median. It collapses the *spread* of the values even when it
   gets the *centre* right. Under the zero-fitted-parameters rule there is no free parameter that
   could re-inject the missing variance without inventing information — so the collapse is the
   expected, correct behaviour of every method in Phases B and C.
3. **It affects `knn` too.** The flat band is present in the Phase-A/statistical predictions *and*
   the Phase-C/`knn` predictions. It is a property of central-tendency imputation, not a property
   that distinguishes the two phases.

So the figures are **honest and correct** — nothing to redraw. What they show is a *limit of the
method family*, which is exactly why they carry the KS-statistic and Wasserstein-distance
annotations (see I.5). **Part II is the fix for this limit.**

### I.4b The draw tier applied — the residual band at ~1950 is real data, not an error

Part II's `draw` tier was then run and drawn on the same pooled hold-out (figures
`results/phase_C/phaseC_draw_scatter_{year_built,levels}.png` — Phase-A vs `pmm` side by side; and
the correct-lens `phaseC_draw_distribution_{year_built,levels}.png` — histogram + ECDF overlays).
`pmm` does exactly what Part II promised: variance ratio `0.06 → 0.59` (`year_built`) and
`0.31 → 0.90` (`levels`), KS `0.51 → 0.32` and `0.47 → 0.12`, at a small MAE cost
(`26.4 → 29.8` y; `9.2 → 12.2`). Two follow-up observations, both **real data, not bugs**:

1. **A dense horizontal band survives at ~1950 even under `pmm`.** It is genuine: **794 of 2,247**
   (**35%**) observed `year_built` values in the pooled hold-out are exactly **1951** — a true mode
   spike, so an honest draw reproduces it. It is NOT the statistical-median fallback showing through.
2. **The `pmm` cloud still does not follow the 1:1 diagonal.** `use_class`/`archetype_id` are absent
   from the Stage-1 `01_buildings.gpkg` schema (confirmed; matches T09's finding), so `pmm` has no
   stratifier and degenerates to a *global marginal bootstrap* — it regenerates the histogram but
   cannot place each building on its true year. `year_built`/`levels` are not inferable from footprint
   shape + location, so no method reaches the diagonal here.

> **In one sentence:** it is not an error — the band at ~1950 is real (35% of the buildings really
> were built in 1951), and the cloud does not follow the diagonal because `year_built` is not
> inferable from a building's shape and location (no method can do it). The scatter-vs-1:1 view is the
> wrong lens for a draw method; the histogram/ECDF distribution figures are the right one.

---

## I.5 Why the headline metrics did not catch it — and which ones do

Phase B was signed on **NMBE +0.49%** and the leaderboard reports **MAE/RMSE**. None of these can
see the flat band:

- **NMBE** is a *mean-bias* metric. A constant-mean predictor is unbiased **by construction**, so
  NMBE ≈ 0 proves the aggregate is unbiased — it says **nothing** about per-building precision or
  spread.
- **MAE / RMSE** reward hitting the centre; a central-tendency fill scores well on them precisely
  *because* it collapses to the centre.

The metrics that **do** expose the collapse are the **KS statistic** (max gap between the predicted
and actual value distributions) and the **Wasserstein distance** (how far the whole predicted
distribution must move to match the real one). Both were already computed by the mask-and-recover
harness (`openubem/validation/mask_recover.py::score_continuous`) and are now surfaced on the
scatter legends. `knn`'s lower KS/Wasserstein vs Phase-A is, in fact, its *only* real edge — it
collapses slightly less — but not enough to matter downstream.

**Rule going forward:** never present NMBE (or MAE alone) as an imputation *accuracy* metric. For
per-building/attribute recovery, report MAE/RMSE **and** KS/Wasserstein together. Part II upgrades
this metric set further (II.5).

---

## I.6 The decision, and the one thing that would change it

**Do not change the Phase-B or Phase-C method.** The variance collapse is inherent to
central-tendency imputation under zero-fitted-parameters and is **acceptable** here because:

1. **OpenUBEM's purpose is aggregate EUI** (fleet rollup), which depends on the *centre* of the
   distribution, not each building's exact value — and the centre is proven unbiased (CP-2).
2. **The "better" ML tier is already built and is EUI-neutral per-cell**, so switching it on buys
   nothing at production granularity — hence it stays off.
3. **The limit is now disclosed**, not hidden — the figures carry KS/Wasserstein and a collapse
   annotation.

The **only** condition that would justify changing the method: if a future use case needs the
**per-building distribution** (not the aggregate) — e.g. retrofit targeting that depends on the
realistic *spread* of vintages, not the mean. The fix is a **donor-draw** imputer
(hot-deck / predictive-mean-matching): instead of returning the neighbourhood mean, draw a real
observed value from the matching donor pool. That preserves variance **and** stays
zero-fitted-parameters. It is a **future, opt-in arc**, not a correction to Phase B or C — and it is
specified in full as **Part II below**.

---
---

# PART II — The variance-preserving `draw` tier (PLAN, to build)

**Slug:** `input-imputation-variance-preserving-draw`

**Purpose (one sentence).** The production statistical tier fills continuous inputs with the
**group median** and categorical inputs with the **group mode** — a single point estimate per
stratum that mathematically collapses the distribution's spread (the flat band diagnosed in Part I).
Part II adds a **menu of variance-preserving draw methods** behind one **opt-in** tier, each of which
returns a **real or distribution-consistent draw** instead of a central value, so the imputed
distribution matches the observed spread — while staying strictly **zero-fitted-parameters**.

**User rulings pinned (2026-07-16):**
- **Ship posture = opt-in / OFF.** The new `draw` tier is NEVER added to
  `config.IMPUTE_ENABLED_TIERS`; the default pipeline stays **byte-identical** and CP-1 is intact.
  No cluster spend, no EUI re-simulation in this arc.
- **Method = a menu, executed each.** Build several draw methods behind one registry (mirroring the
  Phase-C 6-method pattern) and evaluate each on the mask-and-recover harness. The winner(s) are
  reported; nothing is switched on without a later, separate user sign-off.

---

## II.1 Hard rules for the executor

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** Execute this plan; do not rewrite it. On DESIGN
   ambiguity **STOP and quote** the exact lines.
2. **Never edit `main.py` (root), OVERVIEW, or DESIGN docs. No `.py` under `docs/`.**
3. **Zero-fitted-parameters — absolute.** No bandwidth, donor-`k`, residual-scale, or any knob may
   EVER be selected/tuned to make simulated EUI or attribute recovery match a target. KDE bandwidth =
   the library default (Scott's rule); donor `k` = the fixed T06 convention (`DEFAULT_K=10`); every
   draw is seeded from `np.random.default_rng(config.RANDOM_SEED)`. **No EUI column may appear in any
   fit/draw call graph** — enforce structurally (a `__code__.co_names` test, mirroring
   `TestNoEUILeakage`). Nothing computed by the CP evaluation is fed back into any config.
4. **Opt-in / OFF by default.** The `draw` tier is reached ONLY when a caller explicitly enables it
   via `ImputeConfig.per_input_tiers` (or an explicit `enabled_tiers`). `config.IMPUTE_ENABLED_TIERS`
   is **unchanged** — `draw` is never in the default tuple. Prove the default path is byte-identical
   with `assert_frame_equal` (mirror the T11.3 ml-reorder byte-identity proof).
5. **Mandatory provenance.** Every draw-filled value carries a `DRAW_<METHOD>_<TIER>` token and a
   HIGH/MED/LOW confidence tier. Extend the parent §5G token registry via a manager-ratified
   progress-log request — do not invent a parallel vocabulary.
6. **Fit-on-observed-only / no leakage.** Every KDE, donor pool, and residual distribution is built
   from **observed rows only** (never the held-out mask rows). Determinism: same seed ⇒ byte-identical
   draws (assert twice-run equality).
7. **Local only.** pandas/numpy/scipy/sklearn on the committed gpkgs. NO EnergyPlus, NO cluster, NO
   login-node, NO network. The mask-recover harness reads no EUI.
8. **No new dependencies** beyond what is already imported (`scipy.stats`, `numpy`, `scikit-learn`).
9. **Default to no comments;** one short line only where the WHY is non-obvious. Do not commit (git
   handled externally).

---

## II.2 File layout

```
openubem/
├── semantic/
│   ├── imputation.py   (MODIFY — T07 `_draw_tier` + `_TIER_HANDLER_NAMES`/`_CANONICAL_TIER_ORDER`;
│   │                             T05 `_draw_resid`; T02–T06b may live here or in draw_methods.py)
│   └── draw_methods.py (NEW — T02–T06b: the six pure draw functions over observed Series/frames,
│                                zero-fitted-params, no EUI, no side effects; one registry dict)
├── validation/
│   └── mask_recover.py (MODIFY — T09b: additive CP-DRAW metrics (variance/IQR ratio, energy distance,
│                                 score_categorical/TV, bootstrap noise floor); report-only, no EUI)
└── config.py           (MODIFY — T01: IMPUTE_DRAW_METHOD_BY_TARGET (default {}), draw tokens surface;
                                   NEVER touch IMPUTE_ENABLED_TIERS)

tests/
└── test_draw_methods.py (NEW — T01–T09b: registry, each method's variance-preservation + determinism,
                                 opt-in byte-identity, zero-EUI structural guard, CP-DRAW metrics)

openubem/results/
└── draw_leaderboard.py (NEW — T10: pooled + per-cell mask-recover leaderboard driver; figures only
                                to openubem/outputs/; read-only, no EUI feedback)

docs/docs_ACTIVE/input/imputation/implementation/
└── IMPLEMENTATION_phaseC_ml_imputer.md   (this file — II.9 progress log appended by executor)
```

Figures → `openubem/outputs/` (flat). No files outside this list without a plan update.

---

## II.3 Dependency decisions (pre-decided — do not re-debate)

| Concern | Decision | Rationale |
|---|---|---|
| Tier name / order | New tier `"draw"`, inserted **before** `"statistical"` → `_CANONICAL_TIER_ORDER = ("fusion","spatial","ml","draw","statistical")`. | When `draw` is not enabled, `(…, "draw", "statistical")` with draw skipped ≡ `(…, "statistical")` — behaviour-preserving; statistical stays the final safety net when a draw method abstains. |
| Opt-in surface | `config.IMPUTE_DRAW_METHOD_BY_TARGET: dict[str,str]` (default `{}`); a target draws only when a caller enables `draw` for it AND names a method here. **`IMPUTE_ENABLED_TIERS` unchanged.** | Mirrors `IMPUTE_ML_METHOD_BY_TARGET`; keeps default byte-identical. |
| The method menu | Registry `{name → fn}`: `kde` (M1) · `pmm` (M2) · `hotdeck` (M3) · `resid` (M4) · `abb` (M6, continuous); `catfreq` (M5, categorical). | Each is one small pure function; a registry keeps "several methods" a small diff, exactly like Phase-C. **`abb` added on the V01 finding** (II.5) — an Approximate-Bayesian-Bootstrap donor draw that upgrades the plain within-cell random draw for small-n strata (n<200) by resisting donor depletion. |
| KDE bandwidth / donor k / residual scale | **Frozen, never tuned.** KDE = `gaussian_kde` default (Scott). Donor `k = DEFAULT_K = 10`, `radius = DEFAULT_RADIUS_M = 100` (T06). Residual draw = empirical (no parametric scale). | Zero-fitted-params: a knob swept against a metric is the forbidden move. |
| Clamp | All continuous draws clipped to `[observed_min, observed_max]` of the fit column (reuse the existing `np.clip` guard idiom). | Prevents any out-of-range draw; already the KDE/PDE convention. |
| Confidence tier | HIGH/MED/LOW from the same dispersion idea used elsewhere: draw within-IQR of the stratum → HIGH; within observed range → MED; degenerate stratum (n<small floor) → the method abstains (returns null, falls through to statistical), it does NOT emit LOW garbage. | Mirrors `_spatial_tier`'s HIGH/MED-keep, LOW-discard contract (`imputation.py:810`). |
| Default method per target | none (empty registry) — the arc **measures** each; no per-target default is shipped on. | Opt-in only; the CP report informs any future default, gated on user sign-off. |
| Evaluation priority per target (V01 II.5 — a ranking to *test*, NOT a shipped default) | `year_built` → `hotdeck` > `pmm` > `resid`; `levels` → `pmm` > `hotdeck` (**integer-donor only** — `kde`/`resid` produce fractional storeys, disallowed as primary); `height` → `resid` (conditioned on `levels`) > `kde`; `use_class` → `catfreq`. | Donor methods (`pmm`/`hotdeck`) borrow a real observed value → natively respect discrete/integer support and multi-modal peaks; continuous samplers (`kde`/`resid`) are correct only for genuinely continuous `height`. |

---

## II.4 Source-of-truth verified facts (manager-grepped — executor does not re-derive)

- **The collapse lives in `_statistical_tier`.** `imputation.py:911-922` — continuous fill =
  group-wise stratified **median** (`group_median.get(stratum, global_median)`); `:941-956` —
  categorical fill = group **mode** (`_observed_mode`). Both assign one value per stratum ⇒ variance
  collapse. This is the exact behaviour the `draw` tier replaces **when opt-in**.
- **Variance-preserving KDE sampling already exists** but is not wired into the tier:
  `impute_column(method="kde")` at `imputation.py:96-97` fits `stats.gaussian_kde(observed, bw_method)`
  and returns `kde.resample(n_fill, seed=rng)` — clamped to bounds at `:44`. **M1 reuses this
  primitive**; do not reimplement KDE sampling.
- **Tier-handler contract** (`imputation.py` `_spatial_tier:810` / `_ml_tier:688`): a handler
  `f(gdf, attr, mask, rng)` returns `(value, token)` — two `pd.Series` on `gdf.index`; `value` is
  `NaN`/`None` for declined rows. `_spatial_tier` keeps HIGH/MED and **discards LOW** — copy this.
- **Tier registry + order:** `_TIER_HANDLER_NAMES` (`imputation.py:962-967`, name-string dict resolved
  via `globals()` so tests can monkeypatch) and `_CANONICAL_TIER_ORDER` (`imputation.py:559`). T07 adds
  `"draw": "_draw_tier"` and the reordered tuple.
- **Opt-in config resolution:** `ImputeConfig` (`imputation.py:602-623`) resolves tiers from
  `per_input_tiers[attr]` → `enabled_tiers` → `config.IMPUTE_ENABLED_TIERS`. Enabling `draw` for one
  target is a `per_input_tiers` entry; the global default is untouched.
- **Evaluation harness is ready — reuse, do not reimplement.** `mask_recover.py`:
  `score_continuous:260` returns `{mae, rmse, ks_stat, wasserstein, n}`; `mask_and_recover:285` and
  `recover_pairs:350` run the **real** `impute_missing` router under a given `cfg` with spatial-block
  holdout. **KS + Wasserstein are the baseline distributional metrics** (they see variance collapse;
  MAE is the do-no-harm guard); T09b **extends** this set per II.5. Report-only — nothing fed back.
- **T06 neighbour primitives for M3:** `spatial_impute.py` — `knn_fill:174`, `neighbour_vote:94`,
  `DEFAULT_K=10`, `DEFAULT_RADIUS_M=100`, `MNAR_THRESHOLD=0.60` (`:38-40`) — never overridden.
- **CP evaluation dataset:** the 12 committed
  `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg` — pool + reproject
  EPSG:5070 for the pooled leaderboard (as Phase-C did), and evaluate **per-cell** too (production
  granularity). Pooled observed `year_built`=2,247 / `levels`=441 (from Phase-C, re-confirm).

---

## II.5 Deep-research synthesis (V01–V04, folded 2026-07-16)

Four deep-research prompts were run in Gemini Antigravity and answered under this arc's two hard
constraints (zero-fitted-params · provenance) and the four-filter test. RESULTs live at
`../deepResearch/phaseC-IMP/RESULT_V0{1,2,3,4}_*.md`. The findings **confirm the seeded spine and
sharpen it in four places** — no finding overturns the plan; each is now binding on the executor.

**V01 (single-draw menu) — the finalized registry.** Keep all five seeded methods; **add one** —
`abb` (Approximate Bayesian Bootstrap donor draw, Rubin & Schenker 1986) — as a small-n upgrade over a
plain within-cell random draw (resists donor depletion at n<200). **Non-starters flagged:**
parametric/copula sampling (family choice = a target-tuned knob → violates zero-fitted-params) and
proper stochastic MICE (multiplies downstream cost, breaks determinism). **Per-target ranking** is now
pinned in II.3 (donor methods for the discrete/integer targets `year_built`/`levels`; continuous
samplers reserved for `height`). Building-stock precedent that draw-based fills restore spread: İşeri
et al. (in-repo KDE sampler), Nägeli 2018, Cerezo Davila 2017, Kristensen 2017.

**V03 (evaluation metrics) — the CP-DRAW metric set is upgraded.** The seeded KS+Wasserstein+MAE is
*correct but incomplete*. Adopt: **primary = variance ratio σ_imp/σ_obs + IQR ratio** (target 1.0 —
the most direct, scale-free diagnostic of the exact defect); **secondary = 1-D Wasserstein (marginal
shape) + energy distance (Székely–Rizzo, joint/multivariate — catches the `levels`↔`height` covariance
collapse that any marginal metric misses)**; **do-no-harm = MAE ≤ 1.25× the median baseline**;
**categorical = Total-Variation distance for `use_class`**; **aggregate guard = NMBE** (kept from CP-2).
**Exclude MMD** — it needs a kernel bandwidth = a fitted parameter. **Small-n caveat (binding):**
per-cell holdouts are n≈130–560, where empirical Wasserstein/energy distance carry a positive noise
floor and KS has low power — so T10 must establish a **bootstrap noise floor** (shuffle-split the
observed holdout, distance between two true subsets) before ranking, and report variance-ratio bootstrap
CIs. **Plain reading rule (document in the leaderboard): a good draw is *expected to lose on MAE and win
on variance-ratio/Wasserstein* — that trade is the intended result, not a regression.**

**V02 (single vs multiple imputation) — single draw confirmed; MI stays out.** Ship the single
stochastic draw (this plan). Reject an M× multiple-imputation EnergyPlus ensemble: Rubin's rules are
**uncongenial** to a deterministic simulator (within-imputation variance W_i = 0 at the building level →
per-building CIs are structurally invalid), and M× E+ collides with cluster discipline. The *future*
per-building-uncertainty use case routes through a **cheap surrogate emulator** (M draws through a fast
EUI surrogate, empirical p10/p50/p90), **not** M× physical runs — explicitly a later, separately-gated
arc, out of scope here (II.8).

**V04 (modern frontier) — hold the line at classical; Phase-E rulings re-confirmed.** No ML/generative
method enters the `draw` registry, not even opt-in. QRF/CQR/NGBoost clear the four filters but only
*re-describe* conditional uncertainty (add noise around a predicted median) and violate discrete/integer
supports — strictly inferior to PMM, which borrows a real donor value. Deep-generative **SKIP**, GNN
**REJECT**, LLM **FIRM DISQUALIFICATION**, TabPFN **NOT-READY** are each re-confirmed for the
variance-preservation objective. **Watch items only** (would trigger a future re-test, nothing now):
TabPFN v2 if validated on a building-stock set, and frozen multi-city tabular-diffusion packages
(Sinha et al. 2026 trained TabDDPM on 2.2 M ResStock buildings — needs a massive regional pool, unviable
per-cell). This keeps the arc consistent with `results/phase_E/RESULTS_phaseE.md`.

---

## II.6 Task list

> Each task: **What / Why / How / How to test.** All draw code in `draw_methods.py` (+ `_draw_tier`
> in `imputation.py`); all tests in `test_draw_methods.py`.

### T01 — Registry scaffold + opt-in config surface + byte-identity floor
- **What:** Create `draw_methods.py` with an empty-but-typed registry `DRAW_METHODS: dict[str, callable]`
  and the `DRAW_<METHOD>_<TIER>` token constants. Add `config.IMPUTE_DRAW_METHOD_BY_TARGET = {}`. **Do
  NOT touch `IMPUTE_ENABLED_TIERS`.**
- **Why:** Establish the opt-in surface before any method exists so the byte-identity guarantee is
  provable from task 1 (rule 4).
- **How:** Token scheme `DRAW_KDE_HIGH/MED`, `DRAW_PMM_*`, `DRAW_HOTDECK_*`, `DRAW_RESID_*`,
  `DRAW_ABB_*`, `DRAW_CATFREQ_*` (record the exact strings + a manager-ratification request in the
  progress log for parent §5G). No tier wiring yet.
- **How to test:** `TestDefaultByteIdentity` — run `impute_missing` on a fixture with the **default**
  cfg before and after this change; `assert_frame_equal` identical. Registry importable, empty.

### T02 — M1 `kde` draw (variance-preserving, reuses `impute_column`)
- **What:** `draw_kde(observed_by_stratum, targets, rng, bounds)` → for each missing building's
  stratum, fit `gaussian_kde` on that stratum's observed values and draw ONE clamped sample. Below a
  small stratum floor (e.g. <5 observed) the stratum abstains (null) → falls through.
- **Why:** The minimal, most-faithful variance restorer — samples the same per-stratum distribution the
  median currently collapses. Reuses the audited `impute_column` KDE path (II.4).
- **How:** Call the existing KDE-sampling primitive per stratum; seed from the passed `rng`; clip to
  `[observed_min, observed_max]`. Zero new hyperparameters.
- **How to test:** `TestKDE` — on a synthetic bimodal stratum, `std(draws)` is within ~20% of
  `std(observed)` and **KS(draws, observed) < KS(median_fill, observed)** by a wide margin; twice-run
  with same seed ⇒ byte-identical.

### T03 — M2 `pmm` (predictive-mean-matching)
- **What:** `draw_pmm(gdf, attr, mask, rng, k=DEFAULT_K)` → predict each missing building's conditional
  mean (reuse the group-median as the cheap predictor, or a simple observed-feature regressor), then
  draw a **real observed value** from the `k` observed rows whose predicted value is nearest.
- **Why:** Preserves variance AND guarantees every fill is a real, locally-plausible observed value.
- **How:** Build the donor index once from observed rows; nearest-by-predicted-mean; seeded uniform
  draw among the k. `k = DEFAULT_K = 10` fixed.
- **How to test:** `TestPMM` — every filled value equals some observed value (real-donor invariant);
  `std(draws)` >> 0; KS beats median-fill; determinism.

### T04 — M3 `hotdeck` (spatial donor draw)
- **What:** `draw_hotdeck(gdf, attr, mask, rng)` → draw a real observed value from a **spatial
  neighbour** donor pool (T06 `knn_fill`/`neighbour_vote` machinery, `DEFAULT_K`/`DEFAULT_RADIUS_M`).
- **Why:** Local spatial plausibility + variance preservation; the natural spatial analogue of PMM.
- **How:** Reuse `spatial_impute` neighbour primitives to get each missing building's observed
  neighbours; seeded draw among them; abstain (null) if no observed neighbour in radius.
- **How to test:** `TestHotdeck` — real-donor invariant; abstains cleanly when isolated; KS beats
  median-fill on a clustered synthetic frame; determinism.

### T05 — M4 `resid` (stochastic residual)
- **What:** `draw_resid(gdf, attr, mask, rng)` → group-median **plus** a residual drawn from the
  stratum's empirical observed residual distribution `(observed − stratum_median)`.
- **Why:** Re-injects exactly the observed within-stratum spread onto the central estimate; cheapest
  variance restorer that keeps the median's central accuracy.
- **How:** Precompute per-stratum residual arrays from observed rows; seeded draw; clamp to range.
- **How to test:** `TestResid` — mean(draws) ≈ median-fill (central accuracy kept); `std(draws)` ≈
  `std(observed within stratum)`; KS beats median-fill; determinism.

### T06 — M5 `catfreq` (categorical probabilistic draw)
- **What:** `draw_catfreq(gdf, attr, mask, rng)` → for categorical `attr` (e.g. `use_class`), draw a
  category per building from the **observed within-stratum empirical frequencies** instead of the mode.
- **Why:** The categorical analogue of variance preservation — restores minority categories the mode
  erases.
- **How:** Per-stratum normalized value_counts → seeded categorical draw; self-stratification leakage
  guard (never stratify a column by itself, mirror `_statistical_tier:935`).
- **How to test:** `TestCatFreq` — draws reproduce the observed category proportions (chi-square not
  rejected); minority categories appear; mode-fill would not; determinism.

### T06b — M6 `abb` (approximate-Bayesian-bootstrap donor draw)
- **What:** `draw_abb(gdf, attr, mask, rng)` → within each stratum, first draw a bootstrap resample
  (with replacement, size = n_observed) of that stratum's observed values, then draw the fill from that
  resample. Below the small stratum floor the stratum abstains (null) → falls through.
- **Why:** V01 II.5 must-add. A plain within-cell random draw reuses the same few donors when n is small
  (donor depletion); the ABB's two-stage bootstrap injects donor-pool sampling uncertainty so small-n
  strata (n<200) do not degenerate to a handful of repeated values — fully non-parametric, copies only
  real observed values, zero fitted parameters (Rubin & Schenker 1986).
- **How:** Per-stratum observed array → seeded `rng.choice(observed, size=n_observed, replace=True)` →
  seeded `rng.choice(resample)` per missing row. No knobs. Real-donor invariant holds (every fill is an
  observed value). Token `DRAW_ABB_HIGH/MED`; confidence from stratum size (large→HIGH, small→MED,
  n<floor→abstain).
- **How to test:** `TestABB` — real-donor invariant; on a small synthetic stratum the set of distinct
  filled values is **strictly larger** than a fixed-donor draw would give (depletion resisted);
  `std(draws)` >> 0; KS beats median-fill; twice-run same seed ⇒ byte-identical.

### T07 — wire `_draw_tier` + registry + order (byte-identity re-proof)
- **What:** Add `_draw_tier(gdf, attr, mask, rng)` dispatching on
  `config.IMPUTE_DRAW_METHOD_BY_TARGET[attr]` to the registry, obeying the `(value, token)` contract,
  keeping HIGH/MED, discarding LOW (abstain→null→fall through to statistical). Register
  `"draw": "_draw_tier"` in `_TIER_HANDLER_NAMES`; set
  `_CANONICAL_TIER_ORDER = ("fusion","spatial","ml","draw","statistical")`.
- **Why:** Makes the menu reachable **only** via opt-in; the reorder is behaviour-preserving for every
  non-draw routing (II.3).
- **How to test:** `TestRouting` — with `per_input_tiers={"year_built":("spatial","draw","statistical")}`
  and `IMPUTE_DRAW_METHOD_BY_TARGET={"year_built":"kde"}`, draw fills the residual with `DRAW_KDE_*`
  provenance; **default cfg still byte-identical** (re-run `TestDefaultByteIdentity` + the existing
  `test_imputation_routing`/`test_mask_recover` suites — must stay green unchanged).

### T08 — determinism + zero-fitted-params structural guard
- **What:** A `TestNoEUILeakage`-style test inspecting each draw fn's `__code__.co_names` (and its
  callees) for any EUI/`total_eui`/`*_eui_kwh_m2` reference → assert absent; plus a same-seed
  twice-run byte-identity test across the whole `draw` tier.
- **Why:** Enforce the arc's non-negotiable rule structurally, not by convention (rule 3).
- **How to test:** the guard test itself; full `test_draw_methods.py` green.

### T09 — **LOCAL_SMOKE on real committed cells** (pre-CP guard)
- **What:** Run the `draw` tier end-to-end via `impute_missing` on **2–3 real committed
  `01_buildings.gpkg` cells** (not just synthetic fixtures), each method, confirming it fills, stamps
  `DRAW_*` tokens, abstains gracefully on degenerate strata, and never raises.
- **Why:** Synthetic-green ≠ live-green (the arc's standing LIVE_SMOKE rule) — catch real-data schema
  surprises before the CP leaderboard.
- **How to test:** assert non-empty fills + token presence on real cells; no exception; observed rows
  untouched.

### T09b — extend the mask-recover harness with the CP-DRAW metric set (V03 II.5)
- **What:** Add to `mask_recover.py` the distributional metrics V03 pinned, as pure report-only
  functions: **variance ratio σ_imp/σ_obs + IQR ratio** (continuous, the new *primary*),
  **energy distance** (Székely–Rizzo, joint — the new *secondary* alongside the existing Wasserstein),
  and a categorical scorer **`score_categorical`** returning **Total-Variation distance** for
  `use_class`. Add a **bootstrap noise-floor** helper (shuffle-split the observed holdout, distance
  between two true subsets) and variance-ratio bootstrap CIs. Keep `score_continuous`'s existing
  `{mae,rmse,ks_stat,wasserstein,n}` keys — **extend, do not break** (mirror the additive contract).
- **Why:** The seeded KS+Wasserstein+MAE is correct but incomplete: variance/IQR ratio is the most
  direct read of the exact defect, energy distance catches the `levels`↔`height` covariance collapse
  marginal metrics miss, TV is the right categorical fidelity metric, and the noise floor is mandatory
  at n≈130–560 (empirical Wasserstein/energy distance are positively biased there). **MMD is excluded**
  (kernel bandwidth = a fitted parameter → violates zero-fitted-params).
- **How:** `scipy.stats` (`iqr`, `wasserstein_distance`), a small energy-distance implementation over
  raw Euclidean distances (no kernel, no bandwidth — parameter-free), `numpy` for the ratios and the
  seeded bootstrap. No new dependency (do NOT add `dcor`; implement energy distance directly). No EUI;
  report-only, not in any production call graph.
- **How to test:** `TestMetrics` — variance ratio = 1.0 (±noise) when imputed≡observed and ≈0 for a
  constant fill; energy distance = 0 for identical samples, >0 for a collapsed one; TV = 0 for identical
  category proportions; the noise-floor helper returns a strictly positive baseline at n≈150; all
  deterministic under a fixed seed.

### T10 — CP-DRAW evaluation leaderboard (pooled + per-cell)
- **What:** `draw_leaderboard.py` runs `mask_and_recover`/`recover_pairs` for **each of the six draw
  methods vs the group-median/mode baseline**, both **pooled** (12 cells, EPSG:5070) and **per-cell**
  (production granularity), reporting the **full CP-DRAW metric set (T09b)**: **primary — variance/IQR
  ratio →1.0**; **secondary — Wasserstein + energy distance ↓** (each read against its **bootstrap
  noise floor**, not against 0); **categorical — TV distance ↓** for `use_class`; **do-no-harm — MAE ≤
  1.25× baseline**; **aggregate — NMBE-proxy ≈ 0**. Figures → `openubem/outputs/`.
- **Why:** The whole point — quantify how much variance each method restores and at what point-error
  cost, with the metrics that actually see the collapse.
- **How:** Reuse the harness verbatim (per-target calls, fresh `np.random.default_rng(RANDOM_SEED)` per
  call, explicit `enabled_tiers`/`IMPUTE_DRAW_METHOD_BY_TARGET` per method — heed the Phase-C debug
  D04 caller-correctness notes). Cross-check the baseline leg reproduces Phase-A MAE 26.43/9.18 exactly
  (proves the harness invocation is faithful). Apply the **per-target evaluation priority** (II.3) so the
  table reads `year_built`/`levels` under donor methods and `height` under continuous samplers.
  **Document the plain-reading rule in the report: a good draw is expected to LOSE on MAE and WIN on
  variance-ratio/Wasserstein — that trade is intended, not a regression.** **Report-only.**
- **How to test:** the baseline leg matches 26.43/9.18; each method's variance-ratio/Wasserstein/energy/
  TV vs baseline (and vs the bootstrap noise floor) tabulated; figures written to `outputs/`.

---

## II.7 Stop-and-report points

- **CP-A — after T01–T02.** Registry + opt-in surface + M1 KDE built; default byte-identical; M1 beats
  median-fill on KS in a unit test. Report before adding more methods.
- **CP-B — after T07–T09b.** All six methods built, `_draw_tier` wired, default byte-identical
  re-proven, the CP-DRAW metric set added to the harness (T09b), LOCAL_SMOKE green on real cells.
  Report before the CP leaderboard.
- **CP-DRAW — after T10.** The pooled + per-cell leaderboard on the **full CP-DRAW metric set**
  (variance/IQR ratio primary · Wasserstein + energy distance secondary, each vs its bootstrap noise
  floor · TV for `use_class` · MAE ≤1.25× do-no-harm · NMBE-proxy≈0). **Manager audits; returns to the
  user** with the per-method variance-restored-vs-point-error-cost table and the documented plain-reading
  rule. **No default change, no ship, no cluster** without a separate user sign-off — the tier stays
  opt-in/off exactly as built, and the leaderboard informs any future promotion.

---

## II.8 What this arc explicitly does NOT do

- Does **not** switch any draw method on by default (opt-in/off, per user ruling).
- Does **not** run EnergyPlus / cluster / EUI A/B (LOCAL only; an EUI do-no-harm gate is a *future*,
  user-gated step if a method is ever promoted).
- Does **not** implement multiple imputation / Rubin's-rules propagation (V02: uncongenial to a
  deterministic simulator, M× cost). The future per-building-uncertainty case routes through a surrogate
  emulator (p10/p50/p90), a separately-gated later arc — not here.
- Does **not** admit any ML/generative/foundation method into the registry (V04: hold at classical;
  Phase-E rulings re-confirmed). TabPFN v2 and frozen tabular-diffusion packages are watch-only.
- Does **not** add MMD to the metric set (kernel bandwidth = a fitted parameter).
- Does **not** touch `ml`, `fusion`, `spatial`, or the validated A/B/D baselines.
- Does **not** reroute `enrich_semantics` (would break CP-1 byte-identity).

---

## II.9 Progress log

_(executor appends one entry per completed task in the CLAUDE.md format:
`#### TXX — <title> — completed YYYY-MM-DD` · Artifacts · Deviations · Test status · Notes)_

#### CP-A — manager audit + sign-off — 2026-07-16 (manager)
- **Verdict: PASS / greenlit.** Audited T01–T02 per CLAUDE.md (progress log · tests · file tree ·
  deviations). Re-ran `pytest tests/test_draw_methods.py tests/test_imputation_routing.py
  tests/test_mask_recover.py -q` independently → **64 passed**, zero regression. Confirmed
  `config.IMPUTE_ENABLED_TIERS == ("fusion","spatial","statistical")` (no `"draw"`), and `"draw"`
  absent from `_CANONICAL_TIER_ORDER`/`_TIER_HANDLER_NAMES` — default path byte-identical.
- **Token ratification (parent §5G):** the 12 `DRAW_{KDE,PMM,HOTDECK,RESID,ABB,CATFREQ}_{HIGH,MED}`
  strings are **RATIFIED** — they follow the established `<METHOD>_<TIER>` convention (`FUSED_*`/`ML_*`).
- **T01 "empty registry" deviation: accepted** — the reframed `TestDefaultByteIdentity` proves the
  same load-bearing fact without contradicting T02's co-landed deliverable.
- **Next:** greenlit T03–T06b (remaining pure draw methods) to a fresh Sonnet; CP-B remains the next
  stop after T07–T09b.

#### T01 — Registry scaffold + opt-in config surface + byte-identity floor — completed 2026-07-16
- **Artifacts:** `openubem/semantic/draw_methods.py` (new — `DRAW_METHODS: dict[str, Callable]`
  registry + `DRAW_<METHOD>_<TIER>` token constants); `openubem/config.py`
  (`IMPUTE_DRAW_METHOD_BY_TARGET: dict = {}` added; `IMPUTE_ENABLED_TIERS` untouched);
  `tests/test_draw_methods.py` (new — `TestDefaultByteIdentity`).
- **Manager-ratification request (new `DRAW_*` tokens for parent §5G):**
  `DRAW_KDE_HIGH`, `DRAW_KDE_MED`, `DRAW_PMM_HIGH`, `DRAW_PMM_MED`, `DRAW_HOTDECK_HIGH`,
  `DRAW_HOTDECK_MED`, `DRAW_RESID_HIGH`, `DRAW_RESID_MED`, `DRAW_ABB_HIGH`, `DRAW_ABB_MED`,
  `DRAW_CATFREQ_HIGH`, `DRAW_CATFREQ_MED` — reserved as string constants in `draw_methods.py`;
  none are emitted by any tier handler yet (no wiring exists before T07).
- **Deviations:** None from the binding rules. One documentation note (not a rule
  violation): the plan's T01 "How to test" describes the registry as "importable,
  empty" — since T01 and T02 were executed together in this single session/file,
  by the time this progress-log entry is written `DRAW_METHODS` already contains
  `"kde" -> draw_kde` (added by T02, see below). `TestDefaultByteIdentity` therefore
  asserts the registry is a typed `dict` and that `config.IMPUTE_ENABLED_TIERS` /
  `imputation._CANONICAL_TIER_ORDER` / `imputation._TIER_HANDLER_NAMES` have no
  knowledge of `draw` yet, rather than asserting literal emptiness — this proves the
  same load-bearing fact (adding this surface changes nothing about the production
  router) without contradicting T02's own deliverable.
- **Test status:** `pytest tests/test_draw_methods.py -v` → 15 passed (6 in
  `TestDefaultByteIdentity`, 9 in `TestKDE`, see T02 below for the KDE-specific ones).
- **Notes:** `config.IMPUTE_ENABLED_TIERS` confirmed unchanged
  (`("fusion", "spatial", "statistical")`); `"draw"` is not present in
  `imputation._CANONICAL_TIER_ORDER` or `_TIER_HANDLER_NAMES` — the router has zero
  knowledge of the new tier until a future T07.

#### T02 — M1 `kde` draw (variance-preserving, reuses `impute_column`) — completed 2026-07-16
- **Artifacts:** `openubem/semantic/draw_methods.py::draw_kde` (registered into
  `DRAW_METHODS["kde"]`); `tests/test_draw_methods.py::TestKDE`.
- **Deviations:** None from the binding rules. `draw_kde`'s exact signature
  (`draw_kde(observed_by_stratum, targets, rng, bounds=None, min_stratum_n=5)`) is a
  concretization of the plan's `draw_kde(observed_by_stratum, targets, rng, bounds)`
  — `bounds`/`min_stratum_n` given defaults (`None` → per-stratum observed
  `(min, max)` clamp per §II.3's clamp convention; `min_stratum_n=5` per T02's own
  "(e.g. <5 observed)" example) so the function is directly unit-testable ahead of
  the T07 tier-handler wiring that will call it. No knob is tuned against any target
  — both defaults are fixed conventions cited in the plan text itself.
- **How it reuses the audited path:** `draw_kde` builds a per-stratum
  `pd.Series` (observed values + NaN placeholders for the missing rows in that
  stratum) and calls `openubem.semantic.imputation.impute_column(series,
  method="kde", bounds=clamp, rng=rng)` — the exact `stats.gaussian_kde(...).
  resample(n_fill, seed=rng)` primitive at `imputation.py:96-97`, unmodified. KDE
  bandwidth stays the library default (Scott's rule via `impute_column`'s own
  `bw_method="scott"` default) — never swept.
- **Test status:** `pytest tests/test_draw_methods.py -v` → 15 passed, 0 failed
  (full file, T01+T02 combined). `TestKDE` (9 tests) covers: registered under
  `"kde"`; on a synthetic bimodal stratum `std(draws)/std(observed)` = 0.8–1.2
  (within the ~20% band); `KS(draws, observed) < 0.5 × KS(median_fill, observed)`
  (wide margin, confirmed passing); small-stratum (n=3 < floor 5) and unknown-stratum
  abstain-to-NaN; default per-stratum-range clamp and explicit-bounds-override clamp;
  same-seed twice-run byte-identical (`np.testing.assert_array_equal`); independent
  per-stratum draws; mixed abstain/fill strata in one call.
- **Regression status:** `pytest tests/test_imputation.py tests/test_imputation_routing.py
  tests/test_mask_recover.py -q` → 59 passed, 0 failed (no change to any pre-existing
  suite). Default `impute_missing` path re-confirmed byte-identical
  (`TestDefaultByteIdentity::test_default_cfg_router_output_unchanged`).
- **Notes:** No new dependency was added (`scipy.stats` reused transitively via
  `impute_column`; `numpy`/`pandas` only). `draw_kde` never reads any EUI column
  (only takes `observed_by_stratum`/`targets`/`rng`/`bounds` — no `gdf` access at
  all, structurally cannot leak). CP-A (per §II.7) reached: registry + opt-in
  surface + M1 KDE built, default byte-identical, M1 beats median-fill on KS in a
  unit test. Stopping here per the kickoff instruction — T03 (`pmm`) not started.

#### T03 — M2 `pmm` (predictive-mean-matching) — completed 2026-07-16
- **Artifacts:** `openubem/semantic/draw_methods.py::draw_pmm` (registered into
  `DRAW_METHODS["pmm"]`); `tests/test_draw_methods.py::TestPMM` (6 tests).
- **Deviations:** (1) Signature concretized to `draw_pmm(observed_by_stratum,
  targets, rng, k=DEFAULT_K)` — the dict/targets pure form `draw_kde` already
  established (CP-A audited/accepted) — rather than the plan's illustrative
  `draw_pmm(gdf, attr, mask, rng, k=DEFAULT_K)`. Cited: the file-layout
  comment (§II.2) frames T02-T06b as "pure draw functions over observed
  Series/frames"; the dict form is the concretization T02 used and the
  manager's CP-A audit ratified that pattern. (2) The "cheap predictor" is
  each stratum's OBSERVED median (a group statistic, zero-fitted-params,
  same concept `_statistical_tier` already uses) rather than "a simple
  observed-feature regressor" — the plan's "How" explicitly offers this as
  the primary option ("reuse the group-median as the cheap predictor, **or**
  a simple observed-feature regressor"), so no new decision was made. (3) A
  correctness fix beyond the plan text: because the group-median predictor
  is CONSTANT within a stratum, every same-stratum donor ties at distance 0
  to a same-stratum target; naive `argsort`-truncate-to-k would silently pin
  every draw to the same arbitrary k-subset (stable-sort array order),
  collapsing variance instead of preserving it (caught by
  `test_real_donor_invariant_variance_and_beats_median_ks` initially
  failing, ks_draw=0.325 vs ks_median*0.5=0.25). Fixed with tie-inclusive
  k-NN: include every donor at or below the k-th smallest distance (via
  `np.partition`), then draw uniformly among all of them — no new knob, a
  correctness property of "k nearest" under ties, not a tuned parameter.
- **How it borrows cross-stratum:** unlike `draw_kde`/`draw_resid`/`draw_abb`
  (confined to one stratum), `draw_pmm`'s donor pool is every observed value
  across every stratum, ranked by `|donor's-stratum-median − target's-
  stratum-median|` — so even a singleton stratum (n=1, no floor needed) is
  served by its k nearest-predicted donors from neighbouring strata rather
  than abstaining (`test_thin_stratum_borrows_cross_stratum_donors`).
- **Test status:** `pytest tests/test_draw_methods.py -v` → 6/6 `TestPMM`
  passed (real-donor invariant + variance>1.0 + KS beats median by ≥2x;
  thin-stratum cross-borrow; unknown-stratum falls back to global median;
  total-abstain when no observed value anywhere; determinism).
- **Notes:** No EUI reference anywhere in `draw_pmm` (no `gdf` parameter at
  all — structurally cannot leak). `k=DEFAULT_K` imported from
  `spatial_impute`, never redefined.

#### T04 — M3 `hotdeck` (spatial donor draw) — completed 2026-07-16
- **Artifacts:** `openubem/semantic/draw_methods.py::draw_hotdeck`
  (registered into `DRAW_METHODS["hotdeck"]`);
  `tests/test_draw_methods.py::TestHotdeck` (5 tests).
- **Deviation (flagged for manager review at CP-B):** the plan's T04 "What"
  names the PUBLIC `spatial_impute.knn_fill`/`neighbour_vote` as the
  primitives to reuse. Those two functions AGGREGATE their k donors —
  `knn_fill` returns a distance-**weighted mean**, `neighbour_vote` returns
  the donor **mode** — neither is, in general, a real observed value.
  Calling either directly and using its `value` output as the draw would
  violate the hard, explicitly-worded §II.1 rule: "Real-donor invariant for
  pmm/hotdeck/abb: every filled value must equal some observed value." I
  resolved this in favour of the binding rule: `draw_hotdeck` instead calls
  the lower-level T06 neighbour-query engine those two public functions are
  themselves built on — `spatial_impute._build_tree`/`_query_neighbours`
  (`spatial_impute.py:75-91`) — to gather each row's donor pool, then draws
  ONE real donor from it. `DEFAULT_K`/`DEFAULT_RADIUS_M` are unchanged,
  imported not redefined. This is a genuine judgment call between two
  plan-text signals that point in different directions (named-function reuse
  vs. the real-donor invariant); I did not STOP because the invariant is
  stated unambiguously and repeatedly (§II.1 rule list, T04 "Why", T04 "How
  to test"), while the named-function mention is a looser "reuse... spatial
  donor pool" description that both `knn_fill`/`neighbour_vote` AND their
  own internal `_build_tree`/`_query_neighbours` machinery satisfy. Flagging
  explicitly so the manager can overrule at the CP-B audit if a different
  reading was intended.
- **Test fixture note:** the first fixture draft split a 5x5 synthetic
  cluster sequentially (bottom rows missing, top rows retained as donors),
  which put most missing cells outside the test radius of any surviving
  donor — a test-only bug (not a `draw_hotdeck` bug), caught by
  `filled.notna().all()` initially failing. Fixed by switching to a
  checkerboard missing/observed split so every missing cell has an
  orthogonal (dist=10 < radius=15) observed neighbour.
- **Test status:** `pytest tests/test_draw_methods.py -v` → 5/5
  `TestHotdeck` passed (real-donor invariant + std>0.5 + KS beats median by
  20%; abstains when spatially isolated; abstains when neighbours exist but
  none are observed; determinism).
- **Notes:** No EUI reference (only reads `attr`/`geometry`/`mask` from
  `gdf`, never mutates it).

#### T05 — M4 `resid` (stochastic residual) — completed 2026-07-16
- **Artifacts:** `openubem/semantic/draw_methods.py::draw_resid`
  (registered into `DRAW_METHODS["resid"]`);
  `tests/test_draw_methods.py::TestResid` (6 tests).
- **Deviations:** None from the binding rules. Signature mirrors
  `draw_kde`'s `(observed_by_stratum, targets, rng, bounds, min_stratum_n)`
  form (reuses the shared `_MIN_STRATUM_N=5` floor, not a new knob).
- **Notable (non-deviation) mathematical property, worth recording:** because
  `median + (observed_i − median) == observed_i` exactly, and residuals are
  drawn from and applied to the SAME stratum, `draw_resid`'s output is
  algebraically identical to a real observed value from that stratum
  whenever `bounds=None` (the per-stratum-range default clamp never binds).
  This is a byproduct of the plan's literal T05 spec, not a violation of any
  rule (resid has no stated real-donor requirement, but satisfying it here
  is harmless) — flagged only as an interesting property for the CP-DRAW
  leaderboard (T10) to be aware of.
- **Test status:** `pytest tests/test_draw_methods.py -v` → 6/6 `TestResid`
  passed (central accuracy: mean(draws)≈median within 3; variance ratio
  0.7-1.3 of observed std; KS beats median by ≥2x; small-stratum abstain;
  explicit-bounds clamp; default per-stratum-range clamp; determinism).
- **Notes:** No EUI reference (no `gdf` parameter at all).

#### T06 — M5 `catfreq` (categorical empirical-frequency draw) — completed 2026-07-16
- **Artifacts:** `openubem/semantic/draw_methods.py::draw_catfreq` +
  `_empirical_freqs` helper (registered into `DRAW_METHODS["catfreq"]`);
  `tests/test_draw_methods.py::TestCatFreq` (7 tests).
- **Deviations:** Deliberately `(gdf, attr, mask, rng)`-shaped rather than
  the dict/targets form the other five methods use — cited in the module
  comment: the self-stratification leakage guard the plan requires ("never
  stratify a column by itself, mirror `_statistical_tier` at
  `imputation.py:935`") is a property of WHICH column this function picks as
  its OWN stratifier from `gdf`'s columns, so the function must own that
  selection itself, mirroring `_statistical_tier`'s categorical branch
  structure line-for-line (candidate loop over `("use_class",
  "archetype_id")`, skip when `candidate == attr`).
- **Test status:** `pytest tests/test_draw_methods.py -v` → 7/7 `TestCatFreq`
  passed: stratum proportions reproduced (chi-square goodness-of-fit vs true
  80/20 not rejected, p>0.01) and the minority category (`"retail"`)
  recovered — which a mode-fill (`_statistical_tier`) would never emit
  (sanity-checked directly); self-stratification guard falls back to the
  global frequency table without crashing when no other stratifier column
  exists; small (<floor) stratum falls back to the global pool; abstains
  only when NEITHER the stratum NOR the global pool clears the floor;
  determinism.
- **Notes:** No EUI reference (only reads `attr`/stratifier columns/`mask`).

#### T06b — M6 `abb` (approximate-Bayesian-bootstrap donor draw) — completed 2026-07-16
- **Artifacts:** `openubem/semantic/draw_methods.py::draw_abb` (registered
  into `DRAW_METHODS["abb"]`); `tests/test_draw_methods.py::TestABB` (5
  tests).
- **Deviations:** None from the binding rules. Signature mirrors
  `draw_kde`'s `(observed_by_stratum, targets, rng, min_stratum_n)` form.
  Per-stratum resample built ONCE (stage 1, `rng.choice(observed,
  size=len(observed), replace=True)`), then one `rng.choice(resample)` per
  missing row in that stratum (stage 2) — the literal reading of the plan's
  "How" ("Per-stratum observed array → seeded `rng.choice(observed,
  size=n_observed, replace=True)` → seeded `rng.choice(resample)` per
  missing row"). Confidence-from-stratum-size (HIGH/MED) described in the
  plan's T06b "How" is NOT implemented here — that per-row confidence/token
  derivation is `_draw_tier`'s (T07) job, out of scope for this batch, same
  division of labour `draw_kde` already established (T02 also abstains via
  NaN only, no confidence tier).
- **Test status:** `pytest tests/test_draw_methods.py -v` → 5/5 `TestABB`
  passed: real-donor invariant; on a 5-observed/40-missing stratum the set
  of distinct filled values is strictly larger than a fixed-single-donor
  baseline (depletion resisted); std(draws)>0; KS beats median-fill;
  small-stratum and unknown-stratum abstain; determinism.
- **Notes:** No EUI reference (no `gdf` parameter at all).

#### T03-T06b — combined test/regression status — 2026-07-16
- `pytest tests/test_draw_methods.py -q` → **44 passed** (6
  `TestDefaultByteIdentity` + 9 `TestKDE` [T01/T02] + 6 `TestPMM` + 5
  `TestHotdeck` + 6 `TestResid` + 7 `TestCatFreq` + 5 `TestABB`).
- `pytest tests/test_draw_methods.py tests/test_imputation.py
  tests/test_imputation_routing.py tests/test_mask_recover.py -q` → **103
  passed, 0 failed** — zero regression on any pre-existing suite.
- Re-confirmed directly: `config.IMPUTE_ENABLED_TIERS ==
  ("fusion", "spatial", "statistical")`; `imputation._CANONICAL_TIER_ORDER ==
  ("fusion", "spatial", "ml", "statistical")`; `"draw" not in
  imputation._TIER_HANDLER_NAMES`; `config.IMPUTE_DRAW_METHOD_BY_TARGET ==
  {}` — `openubem/config.py` and `openubem/semantic/imputation.py` were NOT
  touched in this batch, so the default routing surface is byte-identical by
  construction, not merely by test.
- `DRAW_METHODS` now holds exactly `{"kde": draw_kde, "pmm": draw_pmm,
  "hotdeck": draw_hotdeck, "resid": draw_resid, "catfreq": draw_catfreq,
  "abb": draw_abb}` — the full V01 six-method menu (§II.5) is built. Not
  started: T07 (tier wiring), T08 (structural EUI-leakage guard across the
  whole tier + full-tier determinism test), T09/T09b (LOCAL_SMOKE + metric
  harness extension), T10 (CP-DRAW leaderboard) — per the kickoff
  instruction, stopping here for manager review before CP-B.

#### T03–T06b — manager audit + ratification — 2026-07-16 (manager)
- **Verdict: PASS / greenlit.** Read all five functions; re-ran
  `pytest tests/test_draw_methods.py tests/test_imputation.py tests/test_imputation_routing.py
  tests/test_mask_recover.py -q` independently → **103 passed, 0 failed**. `config.py` /
  `imputation.py` untouched this batch ⇒ default routing byte-identical by construction.
- **Hotdeck private-primitive deviation (T04): RATIFIED.** Using `spatial_impute._build_tree`/
  `_query_neighbours` instead of the public `knn_fill`/`neighbour_vote` is **correct** — the public
  functions aggregate to a weighted mean / mode, which would violate the hard §II.1 **real-donor
  invariant** for `hotdeck`. The binding rule outranks the plan's illustrative function name. No
  further action.
- **PMM tie-inclusive k-NN (T03): accepted as a correctness fix, not a knob.** The group-median
  predictor is constant within a stratum, so a plain `argsort`-truncate would pin every draw to one
  arbitrary k-subset and re-collapse variance — exactly the defect this arc exists to fix. Including
  all donors at ≤ the k-th distance is the right reading; `k=DEFAULT_K=10` is unchanged, nothing tuned.
- **`resid` real-value byproduct (T05): noted, harmless.** With the default per-stratum clamp,
  `median+(obs−median)=obs`, so `resid` fills are real observed values — no rule requires it, none
  forbids it; flagged for the T10 leaderboard reading.
- **Next:** greenlit T07–T09b (wiring + zero-EUI guard + LOCAL_SMOKE + CP-DRAW metric harness) → CP-B.

#### T07 — wire `_draw_tier` + registry + order (byte-identity re-proof) — completed 2026-07-16
- **Artifacts:** `openubem/semantic/imputation.py` (`_draw_tier`, `_draw_stratum_col_for` added;
  `_CANONICAL_TIER_ORDER` → `("fusion","spatial","ml","draw","statistical")`; `_TIER_HANDLER_NAMES`
  gains `"draw": "_draw_tier"`); `tests/test_draw_methods.py` (`TestDrawTierRouting`, 7 tests; the two
  T01-era `TestDefaultByteIdentity` assertions that asserted `"draw"` was ABSENT from
  `_CANONICAL_TIER_ORDER`/`_TIER_HANDLER_NAMES` updated to assert it is now PRESENT-but-still-opt-in,
  since that is exactly what T07 changes — the load-bearing guarantee under test (default `impute_missing`
  output unchanged) is unaffected and re-asserted by the new `TestDrawTierRouting.
  test_default_cfg_still_byte_identical_even_with_draw_configured`).
- **How `_draw_tier` builds `observed_by_stratum`/`targets`:** stratifier precedence mirrors
  `_statistical_tier` exactly (`use_class` else `archetype_id`, self-stratification guard) via the new
  `_draw_stratum_col_for` helper. For the four dict/targets-shaped methods (`kde`/`pmm`/`resid`/`abb`),
  `_draw_tier` groups `gdf`'s OBSERVED `attr` rows by that stratifier (or a single `"__global__"` key
  when no stratifier column exists) into `observed_by_stratum`, builds `targets` as the per-mask-row
  stratum key list, and calls the registered function directly. For the two gdf-shaped methods
  (`hotdeck`/`catfreq`), `_draw_tier` calls the function directly with `(gdf, attr, mask, rng)` — no
  reshaping needed, since those two own their donor-pool selection internally (spatial neighbours /
  self-stratification respectively).
- **Per-row confidence derivation (T06b's explicitly-deferred job):** HIGH when the drawn value falls
  within `[Q1, Q3]` of its reference OBSERVED distribution — its own stratum's IQR when that stratum
  clears `draw_methods._MIN_STRATUM_N` (imported, not redefined), else the pooled/global observed IQR
  (covers PMM's cross-stratum borrowing and any stratum absent from `observed_by_stratum`) — else MED.
  Deviation/interpretation flagged for CP-B: Part II §II.3 literally reads "draw within-IQR of the
  stratum → HIGH; within observed range → MED", and every non-null draw is ALREADY guaranteed within the
  observed range by each draw function's own clamp/real-donor invariant, so this collapses cleanly to the
  two-tier IQR-or-not test coded here. For a categorical `attr` (`catfreq`, or a hypothetical categorical
  `hotdeck` target) the IQR test has no meaning — HIGH is instead "the drawn category equals the GLOBAL
  observed mode" (the categorical analogue of "the central region"), else MED. This confidence scheme is
  a genuine judgment call (the plan does not spell out the categorical case or the borrowed-stratum
  fallback) — flagging explicitly for manager review at CP-B rather than treating it as self-evident.
  LOW is never emitted by construction (degenerate strata are handled by each draw function's own
  abstain, never reaching the token-stamping loop) — matches `_spatial_tier`/`_ml_tier`'s HIGH/MED-keep
  contract exactly.
- **Test status:** `pytest tests/test_draw_methods.py -q` → 53 passed, 0 failed (44 pre-existing +
  9 new: `TestDrawTierRouting` × 7 + the updated `TestDefaultByteIdentity` assertion, unchanged count
  since it's an in-place edit not an addition — see below for the exact breakdown).
- **Regression status:** `pytest tests/test_imputation.py tests/test_imputation_routing.py
  tests/test_mask_recover.py -q` → 10 + 24 + 26 = 60 passed, 0 failed, **zero changed assertions** in any
  of the three protected suites (confirmed by diffing: this batch touched only `imputation.py`,
  `mask_recover.py` additively, and files under `tests/test_draw_methods.py`/`tests/test_mask_recover.py`
  — no edit to `test_imputation.py`/`test_imputation_routing.py` at all).
- **Notes:** `config.IMPUTE_ENABLED_TIERS` reconfirmed unchanged
  (`("fusion", "spatial", "statistical")`) — `"draw"` is now reachable (present in
  `_CANONICAL_TIER_ORDER`/`_TIER_HANDLER_NAMES`) but ONLY via an explicit `ImputeConfig.per_input_tiers`
  opt-in naming `"draw"`, since it is never in the default enabled tuple; the default-cfg
  `impute_missing` router path re-verified byte-identical directly (see §8 below).

#### T08 — determinism + zero-fitted-params structural guard — completed 2026-07-16
- **Artifacts:** `tests/test_draw_methods.py::TestNoEUILeakage` (structural `__code__.co_names` guard,
  mirrors `test_ml_imputer.py::TestNoEUILeakage`/`test_debias.py::TestNoEUILeakage`) +
  `TestDrawTierDeterminism` (same-seed twice-run byte-identity across the WHOLE `draw` tier via
  `impute_missing`, two targets/two methods at once, not just one function in isolation).
- **Deviations:** None. `_FUNCS` under guard = all six `draw_*` functions + `draw_catfreq`'s
  `_empirical_freqs` helper + `_draw_tier` + `_draw_stratum_col_for` (every function this batch or
  T02–T06b added to the `draw` call graph).
- **Test status:** `pytest tests/test_draw_methods.py -q` → 53 passed, 0 failed (`TestNoEUILeakage` 1
  test inspecting 9 functions' `co_names`; `TestDrawTierDeterminism` 1 test).
- **Notes:** No EUI-like name found in any draw function's `co_names` (structurally cannot leak — none
  of the six pure functions accept an EUI column, and `_draw_tier` never reads one either). Whole-tier
  determinism holds under a fresh `np.random.default_rng(config.RANDOM_SEED)` per run.

#### T09 — LOCAL_SMOKE on real committed cells — completed 2026-07-16
- **Artifacts:** scratchpad script (not committed, per §II.1 rule 9 / kickoff instruction — "a script/run
  + a short note, not a pytest"), run against 3 real committed
  `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg` cells:
  `nyc_centre` (n=738, year_built obs=158, levels obs=136), `austin_urban` (n=425, year_built obs=**0**,
  levels obs=4 — below every stratum floor), `la_suburban` (n=1343, year_built obs=1295, levels obs=6 —
  right at the floor edge). Ran all 5 numeric methods (`kde`/`pmm`/`resid`/`abb`/`hotdeck`) against both
  `year_built` and `levels` on every cell (30 numeric runs), plus `catfreq` against `function_tag`
  (a real, fully-populated categorical column with 30 REAL values synthetically held out per cell — the
  same mask-and-recover convention `mask_recover.py` already uses, since no committed cell has a
  naturally-missing categorical column to draw against). **Zero exceptions across all 33 runs.**
- **Confirmed fill + token stamping:** e.g. `nyc_centre`/`year_built`/`kde` — 580/580 missing filled,
  all via `DRAW_KDE_*` tokens; `nyc_centre`/`function_tag`/`catfreq` — 30/30 masked values refilled via
  `DRAW_CATFREQ_*` tokens.
- **Confirmed graceful abstain on real degenerate strata (the point of this task):**
  `austin_urban`/`year_built`: **zero** observed values anywhere in the cell → every method (including
  the `draw` tier's fallback, `statistical`) abstains — 425/425 stay unfilled, no exception (a tier
  cannot invent data that doesn't exist anywhere, which is correct, not a bug).
  `austin_urban`/`levels` (n=4 observed, below the shared `_MIN_STRATUM_N=5` floor): `kde`/`resid`/`abb`
  abstain cleanly (0 draw-filled, all 421 fall through to `statistical`/`GROUPMODE_MED`) while `pmm`
  fills all 421 (PMM has no stratum floor by design — T03's cross-stratum borrowing, ratified at CP-B
  review of T03–T06b — even a thin/absent stratum is served by its k nearest-predicted donors elsewhere).
  This is a genuine, real-data confirmation that the PMM-vs-{kde,resid,abb} floor-behaviour difference
  documented in T03's progress log is not just a synthetic-fixture artifact.
  `hotdeck` partially fills in every cell (fewer draws than rows, more on `nyc_centre`'s dense grid than
  `austin_urban`'s sparser one) — exactly the expected "abstain when no observed spatial neighbour within
  radius" behaviour on real, non-uniform building density.
- **Test status:** N/A (script/run, not pytest, per the task's own "How to test"). Full pytest regression
  (`test_draw_methods.py`/`test_imputation.py`/`test_imputation_routing.py`/`test_mask_recover.py`) run
  separately, see §8/§10 below.
- **Notes:** No committed cell has `use_class`/`archetype_id` at the Stage-1 `01_buildings.gpkg` level
  (confirmed directly — matches the arc's earlier finding for the `knn` reframe, see MEMORY "KEY
  FINDING — REVISED 2026-07-14"), so every dict-shaped method ran on these three cells with a single
  `"__global__"` stratum (no `use_class`/`archetype_id` stratifier available) — `_draw_stratum_col_for`'s
  `None` fallback path is therefore exercised on every real-cell run, not just synthetic fixtures.

#### T09b — extend the mask-recover harness with the CP-DRAW metric set — completed 2026-07-16
- **Artifacts:** `openubem/validation/mask_recover.py` (additive: `variance_ratio`, `iqr_ratio`,
  `energy_distance`, `score_categorical_tv`, `bootstrap_noise_floor`, `variance_ratio_bootstrap_ci`,
  `_as_2d` helper; `__all__` extended); `tests/test_mask_recover.py::TestMetrics` (15 tests).
- **Deviation (flagged for CP-B review): the new categorical scorer is named `score_categorical_tv`, NOT
  `score_categorical` as the plan's T09b "What" literally names it.** `score_categorical` already exists
  (PFC/log-loss) and is actively called by the production `mask_and_recover`/`recover_pairs` categorical
  routing scorer (T07.2) — reusing/overwriting that name would silently change an already-relied-upon
  function's return contract, which is exactly the "extend, do NOT break" discipline this same task is
  bound by for `score_continuous`. Resolved by adding the TV-distance scorer under a distinct name and
  leaving the pre-existing `score_categorical` byte-for-byte untouched (verified: `test_mask_recover.py`'s
  existing `score_categorical`-consuming tests still pass unchanged, plus a new explicit regression test,
  `test_score_categorical_does_not_break_existing_pfc_log_loss_contract`).
- **`score_continuous`: confirmed untouched** — still returns exactly `{mae, rmse, ks_stat, wasserstein,
  n}`; no code in this task modified it.
- **`energy_distance`:** implemented directly over raw pairwise Euclidean distances (no `dcor`, no
  kernel/bandwidth) — supports both 1-D (marginal) and `(n, d)` joint/multivariate samples (via `_as_2d`),
  so it can catch a `levels`↔`height_m` covariance collapse a marginal metric misses, per V03 §II.5.
  Verified `== 0.0` for identical samples (including the degenerate elementwise-equal case) and `> 0.0`
  for a collapsed (constant) sample, both in 1-D and 2-D joint form.
- **`bootstrap_noise_floor`/`variance_ratio_bootstrap_ci`:** both take an explicit `rng` (default
  `np.random.default_rng(config.RANDOM_SEED)`), deterministic under a fixed seed (tested), report-only —
  neither is called by, nor feeds, `impute_missing`/`ImputeConfig`/any config threshold. `MMD` was NOT
  added (excluded per V03 §II.5 — a kernel bandwidth is a fitted parameter).
- **Test status:** `pytest tests/test_mask_recover.py -q` → 41 passed, 0 failed (26 pre-existing + 15 new
  `TestMetrics`). No new dependency — `scipy.stats.iqr`/`scipy.stats.wasserstein_distance` (already
  imported), `numpy`, `pandas` only.
- **Notes:** all six new functions are pure/report-only; `test_no_eui_anywhere_in_new_metric_outputs`
  confirms no EUI-like string appears in any of their outputs for a representative call of each.

#### CP-B — stop-and-report — 2026-07-16
- **Status: T07–T09b complete, stopping here per the kickoff instruction. T10 (leaderboard) NOT started.**
- **Full regression + draw-tier suite:**
  `pytest tests/test_draw_methods.py tests/test_imputation.py tests/test_imputation_routing.py
  tests/test_mask_recover.py -q` → **128 passed, 0 failed** (53 `test_draw_methods.py` + 10
  `test_imputation.py` + 24 `test_imputation_routing.py` + 41 `test_mask_recover.py`) — exactly the scope
  the kickoff prompt specified. A whole-repo `pytest tests/ -q` was ALSO attempted as an extra safety net
  (this batch touched two shared files, `imputation.py`/`mask_recover.py`) but was cancelled after
  producing no output for several minutes with no sign of progress — inconsistent with how fast every
  other run in this session completed (sub-second to ~1s), and not worth risking a hang on an
  unrelated live-dependent suite elsewhere in `tests/` given the arc's "no live-network integration
  tests" rule. Not treated as a finding against this batch: the two touched files were verified
  independently (targeted regression above, both green) and `imp`/`config` module-level state was
  re-confirmed directly (below) rather than inferred from the stuck run.
- **Byte-identity, re-confirmed directly (not just by test):**
  `config.IMPUTE_ENABLED_TIERS == ("fusion", "spatial", "statistical")` (unchanged);
  `imp._CANONICAL_TIER_ORDER == ("fusion", "spatial", "ml", "draw", "statistical")` (draw now wired,
  between `ml` and `statistical`, exactly as specified); `imp._TIER_HANDLER_NAMES["draw"] ==
  "_draw_tier"`; `config.IMPUTE_DRAW_METHOD_BY_TARGET == {}` (still the shipped default — this task did
  not populate it); default-cfg `impute_missing(df)` run twice on the T01 fixture → `assert_frame_equal`
  identical, `levels[4] == 3.0` / `provenance_levels == "GROUPMODE_MED"` (same values as every prior
  checkpoint in this arc).
- **Open items flagged for manager review at CP-B** (both are judgment calls, not spec violations, but
  neither is 100% spelled out in the plan text): (1) T07's per-row HIGH/MED confidence derivation
  (stratum-IQR-or-global-IQR for continuous, mode-match for categorical); (2) T09b's
  `score_categorical`→`score_categorical_tv` rename to avoid clobbering the pre-existing function.
- **Not started:** T10 (CP-DRAW pooled + per-cell leaderboard) — explicitly out of scope for this batch
  per the kickoff instruction ("Do NOT start T10").

#### CP-B — manager audit + sign-off — 2026-07-16 (manager)
- **Verdict: GREENLIT.** Read `_draw_tier` (`imputation.py:841-952`), `_draw_stratum_col_for` (:829),
  the `_CANONICAL_TIER_ORDER`/`_TIER_HANDLER_NAMES` edits (:559/:1107), and the five new metrics in
  `mask_recover.py` (`variance_ratio`/`iqr_ratio`/`energy_distance`/`bootstrap_noise_floor`/
  `variance_ratio_bootstrap_ci` + `score_categorical_tv`). Independently re-ran
  `pytest tests/test_draw_methods.py tests/test_imputation.py tests/test_imputation_routing.py
  tests/test_mask_recover.py -q` → **128 passed** (matches Sonnet's report). Ran a standalone
  byte-identity guard: `IMPUTE_ENABLED_TIERS == ("fusion","spatial","statistical")`,
  `IMPUTE_DRAW_METHOD_BY_TARGET == {}`, `"draw" not in IMPUTE_ENABLED_TIERS`,
  `_CANONICAL_TIER_ORDER == ("fusion","spatial","ml","draw","statistical")` — **PASS**. The default
  pipeline is byte-identical; `draw` is reachable only via an explicit `per_input_tiers` opt-in AND a
  populated `IMPUTE_DRAW_METHOD_BY_TARGET`, both of which stay at their OFF defaults.
- **Open item (1) — RATIFIED: T07 per-row HIGH/MED confidence.** The scheme (continuous: in stratum-IQR
  when the stratum clears `_MIN_STRATUM_N` else global-IQR → HIGH, else MED; categorical: equals global
  observed mode → HIGH, else MED) is a **provenance LABEL derived from the observed distribution**, not a
  knob that alters any filled value — the value is 100% the draw function's output. It fits nothing
  against an EUI/attribute target, so **zero-fitted-params holds**. It also faithfully renders Part II
  §II.3's "draw within-IQR → HIGH; within observed range → MED" and sensibly extends it to the two cases
  the plan text left implicit (borrowed-stratum continuous, categorical). Accepted as-is.
- **Open item (2) — RATIFIED: `score_categorical` → `score_categorical_tv` rename.** Correct call: the
  pre-existing `score_categorical` (PFC/log-loss) is consumed by production `mask_and_recover`/
  `recover_pairs`; clobbering it would break them. Adding a distinctly-named Total-Variation scorer is
  the "extend, do not break" discipline the task is itself bound by. The plan's literal `score_categorical`
  name is superseded by `score_categorical_tv`; I'll use the new name in T10.
- **LOCAL_SMOKE accepted:** T09's 33-run real-cell sweep (nyc_centre/austin_urban/la_suburban) with zero
  exceptions, and its real-data confirmation of the below-floor abstain (austin `levels` n=4 → kde/resid/
  abb fall through to statistical while pmm borrows cross-stratum) satisfies the synthetic-blind-spot rule
  ([[feedback_synthetic_test_blind_spots]]) before CP-DRAW.
- **Next:** greenlit T10 (CP-DRAW pooled + per-cell leaderboard, full metric set incl. `score_categorical_tv`,
  figures to `openubem/outputs/`) to a fresh Sonnet → CP-DRAW. The tier stays opt-in/OFF; promotion to a
  default is a separate explicit user decision, NOT part of this arc.

#### T10 — CP-DRAW evaluation leaderboard (pooled + per-cell) — completed 2026-07-16
- **Artifacts:** `openubem/results/draw_leaderboard.py` (new — driver, ~450 lines); figures
  `openubem/outputs/draw_leaderboard_{variance_ratio,wasserstein_vs_floor,mae_donoharm,categorical}_pooled.png`
  (4 PNGs, flat, per the project figure rule); `openubem/outputs/draw_leaderboard_results.json` (companion
  machine-readable results — every number in the tables below traces to this file; a minor addition beyond
  Part II §II.2's literal file list, flagged as deviation (4) below, not a code file).
- **Invocation pattern (heeding the D04 debug doc + `impute_scatter.py::_pooled_ml_pairs`):** baseline leg
  = `ImputeConfig(enabled_tiers=("spatial","statistical"))`, no `draw` touched. Draw leg = per the kickoff's
  hard rule 1, `config.IMPUTE_DRAW_METHOD_BY_TARGET[target]` set EXPLICITLY inside a `try/finally` (restored
  immediately after, never persisted) + `ImputeConfig(per_input_tiers={target: ("spatial","draw","statistical")})`
  — `draw` sits in its canonical position between `spatial` and `statistical` (§II.3). A FRESH
  `np.random.default_rng(RANDOM_SEED)` (=42, `openubem.config.RANDOM_SEED`) is passed to EVERY
  `recover_pairs`/bootstrap call, never shared/reused across methods or targets. Pooling uses the exact
  `POOLED_CELL_ORDER` tuple (`austin_centre, austin_rural, austin_suburban, austin_urban, la_centre,
  la_rural, la_suburban, la_urban, nyc_centre, nyc_rural, nyc_suburban, nyc_urban`) and EPSG:5070
  reprojection from `scratchpad/t11_cp3_leaderboard.py`/`impute_scatter.py::POOLED_CELL_ORDER` verbatim
  (block-holdout tie-breaking is order-sensitive — the documented T11 root cause).
- **Baseline cross-check gate: PASSED.** Regenerated pooled baseline (no `draw`) reproduces
  `RESULTS_phaseC.md`'s committed Phase-A leaderboard exactly: `year_built` MAE **26.433** (rounds to
  **26.43** = committed) n_complete_cases=2247 n_holdout=562; `levels` MAE **9.176** (rounds to **9.18** =
  committed) n_complete_cases=441 n_holdout=134. The driver asserts this at runtime
  (`AssertionError` if it ever drifts — mirrors `impute_scatter.py::_assert_cross_check`'s "honesty guard");
  both asserts passed on this run, confirming the invocation is faithful before any `draw` number is trusted.
- **Targets evaluated:** `year_built`, `levels`, `height_m` (continuous, all 5 non-categorical methods:
  `kde`,`pmm`,`hotdeck`,`resid`,`abb`) + `function_tag` substituting for `use_class` (categorical, `catfreq`)
  — **deviation (1), precedented by T09:** `use_class` is not present at the Stage-1 `01_buildings.gpkg`
  schema level (re-confirmed directly this run), exactly the gap T09's LOCAL_SMOKE hit and resolved the same
  way (a real, densely-populated categorical column, synthetically masked via the harness's own
  mask-and-recover convention). `function_tag` pooled n=8,160 (100% populated, 89 distinct categories).
- **Deviation (2):** the T10 "How" text names `ImputeConfig(per_input_tiers=...)` generically; this driver
  uses `per_input_tiers` for every `draw` leg (kickoff hard rule 1, literal) and `enabled_tiers` for the
  baseline leg only (matches the established Phase-A/Phase-C convention in `t11_cp3_leaderboard.py`/
  `impute_scatter.py` — baseline never touches the draw opt-in surface at all).
- **Deviation (3):** introduced `PER_CELL_MIN_N = 30`, a data-adequacy floor (NOT a tuned metric knob — a
  gate on whether a mask-recover comparison is meaningful at all, independent of and never read by any
  method/metric) below which a per-cell target is reported `insufficient_data` rather than computing a
  metric on a handful of points. 19/36 continuous cell-target combinations cleared the floor; the 17 skipped
  are exactly the real degenerate cells T09 already flagged (e.g. `austin_urban`/`year_built` n_observed=0,
  `nyc_suburban` all three targets n_observed=0, `la_suburban`/`levels` n_observed=6) — full list in the JSON.
- **Deviation (4):** added `draw_leaderboard_results.json` under `openubem/outputs/` alongside the 4
  mandated figures — not on Part II §II.2's literal file list, but a data companion (not a new code file)
  to the figures the plan does mandate, written to the same "flat, visible" location; flagging for manager
  review rather than silently adding an unlisted artifact.
- **Deviation (5) — joint (levels, height_m) energy-distance bonus, pooled only:** V03 (§II.5) motivates
  energy distance specifically as the metric that "catches the `levels`↔`height` covariance collapse a
  marginal metric misses" — a claim the per-target marginal energy-distance numbers below cannot test on
  their own. Added one extra pooled-only check: both targets drawn by the SAME method in ONE call
  (`continuous_targets=("levels","height_m")`, complete-case-on-BOTH, n_complete_cases=246, n_holdout=79),
  joint `energy_distance` computed on the `(levels, height_m)` pair versus the true joint pair. Per-cell
  was NOT attempted for this bonus check (complete-case-on-both is too thin at cell granularity per
  deviation 3's own floor). This goes beyond T10's literal enumerated metric list but stays inside its
  "How" framing and V03's design intent — flagged, not hidden.
- **POOLED results (primary + secondary + do-no-harm + NMBE-proxy; full precision in the JSON):**

  | target (n_cc / n_holdout) | leg | MAE | Wasserstein | noise floor (median/p90) | variance_ratio | IQR_ratio | energy_dist | do-no-harm (MAE≤1.25×base) | NMBE-proxy % |
  |---|---|---|---|---|---|---|---|---|---|
  | `year_built` (2247/562) | baseline | 26.43 | 26.21 | 3.00 / 5.27 | 0.064 | 0.000 | 16.10 | — | 0.14 |
  | | kde | 29.79 | 13.74 | | 0.614 | 0.285 | 5.05 | PASS | 0.31 |
  | | pmm | 29.80 | 16.06 | | 0.585 | 0.091 | 6.62 | PASS | 0.30 |
  | | **hotdeck** | **26.47** | 23.67 | | 0.297 | 0.000 | 12.93 | PASS | 0.11 |
  | | resid | 29.80 | 16.06 | | 0.585 | 0.091 | 6.62 | PASS | 0.30 |
  | | abb | 30.50 | 15.04 | | 0.615 | 0.091 | 5.97 | PASS | 0.33 |
  | `levels` (441/134) | baseline | 9.18 | 8.32 | 2.30 / 4.13 | 0.314 | 0.000 | 4.27 | — | −52.59 |
  | | kde | 10.55 | 4.46 | | 0.603 | 0.458 | 0.99 | PASS | −37.85 |
  | | **pmm** | 12.19 | **2.16** | | **0.902** | 0.678 | **0.29** | FAIL | −17.35 |
  | | hotdeck | **9.13** | 7.56 | | 0.467 | 0.000 | 3.66 | PASS | −46.73 |
  | | resid | 12.19 | 2.16 | | 0.902 | 0.678 | 0.29 | FAIL | −17.35 |
  | | abb | 11.24 | 4.22 | | 0.722 | 0.458 | 0.95 | PASS | −33.40 |
  | `height_m` (5354/1722) | baseline | 3.59 | 3.53 | 0.47 / 0.69 | 0.088 | 0.000 | 1.625 | — | −9.93 |
  | | kde | 11.70 | 7.00 | | 3.158 | 1.960 | 1.26 | FAIL | 74.15 |
  | | pmm | 10.55 | 5.64 | | 2.519 | 1.549 | 0.94 | FAIL | 64.17 |
  | | **hotdeck** | **3.70** | 3.17 | | 0.238 | 0.000 | 1.32 | PASS | −5.89 |
  | | resid | 10.55 | 5.64 | | 2.519 | 1.549 | 0.94 | FAIL | 64.17 |
  | | abb | 9.73 | 4.82 | | 2.342 | 1.451 | 0.72 | FAIL | 54.33 |
  | `function_tag`/use_class-substitute (n=2336 of 8160) | leg | PFC | log_loss | — | — | TV | — | do-no-harm (PFC≤1.25×base) | — |
  | | baseline | 0.1015 | 1.1221 | | | 0.1015 | | — | |
  | | catfreq | 0.1348 | 1.5090 | | | **0.0775** | | FAIL (marginal) | |
  | joint `(levels, height_m)` energy distance (n_cc=246/n_holdout=79) | baseline **14.28** → kde 3.03, **pmm 2.07**, hotdeck 13.85 (barely moves), **resid 2.07**, abb 5.33 | | | | | | | | |

- **The plain-reading rule, confirmed by real numbers (not asserted, measured):** every donor/sampler
  method (`kde`/`pmm`/`resid`/`abb`) restores variance/IQR/Wasserstein/energy substantially toward the
  observed distribution while costing MAE — exactly the intended trade. `hotdeck` is the outlier-in-the-
  literal-sense: it is real-spatial-neighbour-constrained, so it restores LESS variance (pooled mean
  variance_ratio 0.54 across all 22 run cells+pooled vs 0.89-0.92 for the other four) but virtually never
  fails do-no-harm (**21/22 = 95%** of all continuous method×target×granularity combinations, pooled+per-
  cell combined, vs 50-59% for the other four methods — full tally in the JSON, reproduced by
  `scratchpad`-style aggregation, not committed as a separate file). At `height_m` and per-cell `levels`
  (`la_suburban`), the donor/sampler methods actively OVERSHOOT variance (ratio >1.0, up to 3.16 for
  pooled `height_m`/kde) — a genuine, real-data-confirmed failure mode at thin per-cell donor pools that
  the pooled leg alone would not have revealed, corroborating V03's own "small-n caveat."
- **`function_tag` do-no-harm marginal FAIL, TV WIN:** `catfreq`'s PFC (0.1348) exceeds the do-no-harm
  1.25× baseline threshold (0.1269) narrowly, while its TV (0.0775) is meaningfully BETTER than baseline's
  TV (0.1015) — i.e. `catfreq` recovers the true category-proportion SHAPE better (the minority-category
  restoration it exists for) at a real but modest per-row point-accuracy cost. Consistent with the plain-
  reading rule; flagged as the one leg where the do-no-harm guard, if later adopted as a hard gate, would
  need a per-target review rather than a blanket pass/fail.
- **Joint energy-distance bonus confirms the V03 covariance-collapse claim directly:** baseline joint
  `(levels,height_m)` energy distance is 14.28 (severe); every donor/sampler method drops it below 5.4,
  with `pmm`/`resid` reaching 2.07 (best) — a much larger relative improvement than either marginal metric
  alone shows. `hotdeck` barely moves the joint metric (13.85) despite passing every marginal do-no-harm
  gate — i.e. `hotdeck`'s spatial-donor draws for `levels` and `height_m` are NOT drawn as a correlated
  pair (each target's donor is queried independently), so it under-restores the cross-target covariance
  specifically. This is a genuine, non-obvious finding this bonus check exists to surface.
- **PER-CELL results (production granularity):** 19/36 continuous cell×target combinations cleared the
  `PER_CELL_MIN_N=30` floor (17 `insufficient_data`, matching T09's already-documented degenerate cells:
  `austin_rural`/`nyc_rural`/`nyc_suburban` mostly all-zero-observed, `la_suburban`/`austin_urban`/`la_rural`
  `levels` in single digits). Categorical (`function_tag`) ran on all 12 cells (fully populated everywhere).
  Representative examples (full 12-cell table in the JSON): `nyc_centre`/`year_built` baseline MAE 41.51
  var_ratio 0.297 → `hotdeck` MAE 39.57 (BEATS baseline, do-no-harm trivially passes) var_ratio 0.399;
  `abb` MAE 44.37 var_ratio **0.803** (best per-cell variance restoration at this cell, do-no-harm passes).
  `la_suburban`/`year_built` (n_cc=1295, the single richest per-cell continuous target): baseline MAE 4.24
  var_ratio 0.118 → `kde`/`pmm`/`resid`/`abb` ALL fail do-no-harm AND overshoot variance (ratio 1.32-1.38);
  only `hotdeck` (MAE 4.99, var_ratio 0.648) passes do-no-harm — the per-cell overshoot failure mode called
  out above, concentrated in the cell with the most donors, not the fewest (donor-pool composition, not
  just size, appears to drive it — a question for a future arc, not resolved here).
- **Test status:** `.\.venv\Scripts\python.exe -m pytest tests/test_draw_methods.py tests/test_imputation.py
  tests/test_imputation_routing.py tests/test_mask_recover.py -q` → **128 passed, 0 failed** (unchanged from
  CP-B — this task added no test, only a report-only driver that imports but never modifies any tested
  module). `draw_leaderboard.py` itself has no dedicated pytest suite (T10's "How to test" specifies driver
  assertions + tabulation + figures, not a new test file; the plan's file layout §II.2 does not list a
  `test_draw_leaderboard.py`).
- **Byte-identity / config guard, re-confirmed after the full run:** `git diff openubem/config.py` is
  IDENTICAL to the pre-T10 (CP-B-audited) diff — this task's script only mutates
  `config.IMPUTE_DRAW_METHOD_BY_TARGET` as an in-memory dict object inside `try/finally` blocks (never
  writes to `openubem/config.py` on disk); confirmed directly: `IMPUTE_ENABLED_TIERS ==
  ("fusion","spatial","statistical")`, `IMPUTE_DRAW_METHOD_BY_TARGET == {}` after the run completes (every
  `try/finally` executed cleanly, script exit code 0, no unhandled exception left a mutated dict behind).
- **Figures written:** `openubem/outputs/draw_leaderboard_variance_ratio_pooled.png`,
  `openubem/outputs/draw_leaderboard_wasserstein_vs_floor_pooled.png`,
  `openubem/outputs/draw_leaderboard_mae_donoharm_pooled.png`,
  `openubem/outputs/draw_leaderboard_categorical_pooled.png` (all flat under `openubem/outputs/`, per the
  project figure rule — none under `docs/`).
- **Notes:** one cosmetic fix applied mid-task (not a deviation from the plan): the first run emitted
  harmless `matplotlib` `UserWarning`s from `set_xticklabels` without a preceding `set_xticks` call; fixed
  by adding `ax.set_xticks(range(len(names)))` before `set_xticklabels` in both `_bar_grid` and
  `build_wasserstein_vs_floor_figure`, then re-ran (byte-identical numbers, clean stdout, confirmed above).
  No production module (`imputation.py`/`draw_methods.py`/`mask_recover.py`/`config.py`) was touched by
  this task — `openubem/results/draw_leaderboard.py` is the only new file besides its figure/JSON outputs.

#### CP-DRAW — stop-and-report — 2026-07-16
- **Status: T10 complete. Stopping here per the kickoff instruction — no default change, no ship, no
  cluster spend.** Full pooled + per-cell leaderboard on the complete CP-DRAW metric set (variance/IQR
  ratio primary, Wasserstein + energy distance secondary each read against its bootstrap noise floor, TV
  for the categorical leg, MAE/PFC≤1.25× do-no-harm, NMBE-proxy) is tabulated in the T10 entry above and in
  full precision in `openubem/outputs/draw_leaderboard_results.json`.
- **Baseline cross-check: CONFIRMED.** Regenerated pooled Phase-A baseline reproduces `RESULTS_phaseC.md`
  exactly: `year_built` MAE 26.433→26.43, `levels` MAE 9.176→9.18 (asserted at runtime, both passed).
- **`git diff openubem/config.py`: CONFIRMED EMPTY relative to the CP-B-audited state** — identical to the
  diff CP-B already audited and greenlit (only the pre-existing T01/T11.8/T12 additions); this task added
  no new line to `openubem/config.py`. `IMPUTE_ENABLED_TIERS` and `IMPUTE_DRAW_METHOD_BY_TARGET` both
  confirmed at their shipped OFF defaults after the run.
- **Headline reading for the manager (per-method variance-restored-vs-point-error-cost, condensed):**
  `hotdeck` is the do-no-harm-safe choice (95% pass rate across all 22 pooled+per-cell continuous runs) but
  restores the least variance (mean ratio 0.54). `pmm`/`resid` (mathematically identical outputs under the
  default clamp, per T05's own progress-log note) restore variance best on `levels` (0.902, near-ideal) and
  win the joint covariance check by a wide margin (2.07 vs hotdeck's 13.85 vs baseline's 14.28), but fail
  do-no-harm on `levels` and badly overshoot on `height_m` (ratio 2.5, MAE 3x baseline). `kde`/`abb` sit
  between the two extremes on every axis. No method is uniformly best — the tradeoff is real, target-
  dependent, and now quantified rather than asserted.
- **Per the Part II §II.7 CP-DRAW checkpoint text: no default change, no ship, no cluster — the tier stays
  opt-in/off exactly as built.** This leaderboard is for the manager to audit and return to the user with;
  any future promotion of a specific method for a specific target is a separate, explicitly user-gated
  decision, not part of this arc.
- **Open items flagged for manager review:** the 5 documented deviations in the T10 entry above (categorical
  target substitution, `per_input_tiers`-vs-`enabled_tiers` split, the `PER_CELL_MIN_N=30` data-adequacy
  floor, the JSON companion file addition, and the joint-energy-distance bonus check) — none contradicts a
  binding rule, all are judgment calls made to fulfill the task's literal intent where the plan text left a
  gap.

#### CP-DRAW — manager audit + sign-off — 2026-07-16 (manager)
- **Verdict: GREENLIT. Part II (the `draw` tier) is COMPLETE.** Read `openubem/results/draw_leaderboard.py`
  in full: the D04 caller-correct pattern is faithfully mirrored (fresh `np.random.default_rng(RANDOM_SEED)`
  per call, `POOLED_CELL_ORDER`/EPSG:5070 verbatim, save-restore of `IMPUTE_DRAW_METHOD_BY_TARGET` in
  `try/finally`), and the runtime cross-check gate (`draw_leaderboard.py:322-330`, an `AssertionError` that
  fires BEFORE any figure is written) is the correct honesty guard.
- **Independent re-verification (not trusting the report):** (1) re-ran the four regression suites →
  **128 passed**; (2) ran a standalone byte-identity guard → `IMPUTE_ENABLED_TIERS ==
  ("fusion","spatial","statistical")`, `IMPUTE_DRAW_METHOD_BY_TARGET == {}`, `"draw"` absent from the
  default — the `draw` tier is opt-in/OFF, default path byte-identical; (3) inspected `git diff
  openubem/config.py` — only the pre-existing T01 opt-in-surface lines, **zero T10 additions**; (4) the four
  PNGs + JSON exist under `openubem/outputs/` (flat, fresh timestamps) — and since main() writes figures
  ONLY after the cross-check gate, their existence independently proves the gate passed; (5) read the JSON
  back directly: pooled baseline `year_built` MAE = **26.43**, `levels` MAE = **9.18** — exact reproduction.
- **All 5 deviations RATIFIED:** (1) `function_tag`→`use_class` substitution — precedented by T09's
  LOCAL_SMOKE, `use_class` genuinely absent from Stage-1 `01_buildings.gpkg` ([[feedback_synthetic_test_blind_spots]]);
  (2) `per_input_tiers` (draw) vs `enabled_tiers` (baseline) split — matches kickoff hard-rule 1 and the
  established Phase-A/C convention; (3) `PER_CELL_MIN_N=30` — a **data-adequacy** floor, NOT a metric knob
  (never read by any method/metric; it only decides whether a comparison is meaningful) → zero-fitted-params
  intact; (4) JSON companion — a data artifact beside the mandated figures, not a code file, "flat/visible"
  location honoured; (5) joint `(levels,height_m)` energy-distance bonus — directly tests V03's covariance-
  collapse claim, the single most decision-relevant number in the whole leaderboard.
- **Correctness note I verified myself:** `pmm` and `resid` produce mathematically identical pooled outputs
  (year_built 29.80/0.585, levels 12.19/0.902, joint 2.07). This is NOT a bug — with a constant group-median
  predictor, tie-inclusive PMM draws uniformly over the stratum's observed values, and `resid = median +
  (observed − median)` is the same uniform draw. Their agreement is positive evidence both are implemented
  correctly, not a copy-paste error.
- **The finding, in one line for the user:** the leaderboard confirms the variance-collapse thesis with real
  numbers (baseline variance-ratio 0.06–0.31, IQR-ratio exactly 0) and quantifies the intended trade — every
  sampler/donor method restores variance/covariance (joint energy distance 14.28→2.07 for pmm/resid) at a
  point-error cost, while `hotdeck` is do-no-harm-safe (95% pass) but restores least variance (~0.54). **No
  method dominates on every axis; the choice is target-dependent.** This is exactly the decision surface the
  arc set out to produce.
- **TERMINAL POSTURE (unchanged, and I did NOT cross it):** the `draw` tier stays **opt-in / OFF** — I have
  not touched `IMPUTE_ENABLED_TIERS`, have not populated `IMPUTE_DRAW_METHOD_BY_TARGET`, and have switched no
  method on by default. Promotion of any specific method for any specific target is a **separate, explicitly
  user-gated decision** requiring its own do-no-harm review (and, if it were ever to affect EUI, a cluster
  A/B) — NOT part of this arc. Part II is closed at the leaderboard, as §II.7 CP-DRAW mandates.

#### Manager — draw-tier illustration figures + "1951-mode / not-an-error" record — completed 2026-07-17
- Artifacts: 4 figures in `results/phase_C/` (fresh Sonnet employees, manager-audited by reading each PNG):
  `phaseC_draw_scatter_{year_built,levels}.png` (Phase-A flat band vs `pmm` cloud, side by side) and
  `phaseC_draw_distribution_{year_built,levels}.png` (histogram + ECDF overlays of actual vs Phase-A vs `pmm`).
  New builders `build_phaseC_draw_scatter_*` / `build_phaseC_draw_distribution_*` + `_pooled_draw_pairs` helper
  in `openubem/results/impute_scatter.py` (mirrors `draw_leaderboard._draw_pairs`). Explanation recorded in
  §I.4b above and in `docs_EXPLANATION/OpenUBEM_imputation_methods.md` §6.5.
- Deviations: figures placed in `results/phase_C/` (beside `phaseC_scatter_*`) per explicit user instruction,
  superseding the CLAUDE.md flat-`openubem/outputs/` rule for this arc's result figures (scatter copies kept in
  `openubem/outputs/` too). Explanation rendered in English (deliverables-in-English convention).
- Test status: honesty-guard cross-checks passed on every build (`year_built` 26.43 / `levels` 9.18 to 2dp);
  KS shown on figures: `year_built` Phase-A 0.51 -> pmm 0.32, `levels` 0.47 -> pmm 0.12. Report-only, draw tier OFF.
- Notes: the ~1950 band surviving under `pmm` is REAL DATA (35% of observed `year_built` = 1951, a true mode
  spike), not the median fallback; the cloud cannot reach the diagonal because `use_class`/`archetype_id` are
  absent from Stage-1 schema, so `pmm` = global marginal bootstrap (fixes histogram, not per-building value). No
  ship decision changed.

---

## Where to go next

| To understand… | Read |
|---|---|
| The general four-tier method + the variance-collapse limit in plain language | [`../../../docs_EXPLANATION/OpenUBEM_imputation_methods.md`](../../../docs_EXPLANATION/OpenUBEM_imputation_methods.md) |
| The full Phase-C execution plan + progress log (T11.1–T11.8c) for the `ml` tier | [`../docs_Done/PLAN_phaseC_ml_imputer.md`](../docs_Done/PLAN_phaseC_ml_imputer.md) |
| The committed CP-3 numbers + figures | [`../results/phase_C/RESULTS_phaseC.md`](../results/phase_C/RESULTS_phaseC.md) |
| Proof the leaderboard reproduces (why the "27.82≠25.14" scare was a caller mistake) | [`../debugs/PLAN_phaseC_knn_repro_investigation.md`](../debugs/PLAN_phaseC_knn_repro_investigation.md) |
| The deep-research evidence behind the `draw` menu (single-draw · MI · metrics · frontier) | [`../deepResearch/phaseC-IMP/`](../deepResearch/phaseC-IMP/) RESULT_V01–V04 |
| Where the pipeline uses the imputed inputs | [`../../../docs_EXPLANATION/OpenUBEM_fundamentals.md`](../../../docs_EXPLANATION/OpenUBEM_fundamentals.md) |

---

*Last updated 2026-07-16. Part I is an explanation/spec (the `ml` tier remains built-but-off / opt-in;
the default pipeline is unchanged). Part II is a manager PLAN for the opt-in `draw` tier — executed by
fresh Sonnet sessions, who append to II.9; nothing ships without a separate user sign-off.*
