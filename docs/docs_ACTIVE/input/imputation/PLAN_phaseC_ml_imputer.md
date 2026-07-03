# PLAN — Phase C: Classical-ML Imputer (`build_ml_imputer` / §3E ML tier)

**Slug:** `input-imputation-phaseC-ml-imputer`
**Date:** 2026-07-03
**Arc:** Input-Parameter Imputation ("OpenUBEM AI"). This is the **detailed execution plan for
task T11** of the parent plan
`docs/docs_ACTIVE/input/imputation/PLAN_input_imputation_implementation.md` (§6 T11, §7 CP-3). The
parent plan's §0 tracker + §8 progress log remain the binding arc record; this doc decomposes T11
into executable sub-tasks T11.1–T11.7 and pins the load-bearing decisions.
**Binding contract:** OpenUBEM Stage-2.2 DESIGN §3E (ML tier, lines 116–140) —
`docs/docs_main/docs_step-2-2/DESIGN_step-2-2-enrich-every-classified-building-with-constructions-loads-schedules-and.md`.
**This plan may not contradict the DESIGN; on any conflict the executor STOPS and quotes the exact
lines** — except where §5 below has already ratified an apparent conflict (read §5-A first).

**Scope decision (user, 2026-07-03):** build the **full M04 six-method sklearn menu** (not
MissForest-only) behind one pluggable estimator registry, per-target complete-case floors, all gated
identically at CP-3. EUI "does-not-worsen" check = **local IDF field-diff primary, cluster A/B only
on material fill divergence** (the CP-1 method the user ratified — strictly stronger, zero cluster
cost). **Ships opt-in only.**

---

## 0. Status at a glance

> Legend: `[x]` done · `[~]` in progress · `[ ]` not started · `[!]` blocked/needs decision.
> **Last updated:** 2026-07-03 (**CP-3 CLOSED — NOT fully MET; USER ACCEPTED built-but-off ["keep it"]**: attribute-leg marginal `knn` win, EUI-leg fails do-no-harm −5.51 % NMBE; ML tier kept opt-in/off, per-target registry preserved, arc PARKED; T11.7 not pursued).

- [x] **T11.1** — `build_ml_imputer` core + 6-method estimator registry (complete-case fit, per-target floors)
- [x] **T11.2** — dispersion→confidence per method family + `ML_<METHOD>_<TIER>` tokens (**ratified into parent §5G 2026-07-03**)
- [x] **T11.3** — wire `_ml_tier` to the tier contract + reorder `_CANONICAL_TIER_ORDER` (ml before statistical) + opt-in config
- [x] **T11.4** — reconcile `impute_column` to §3E `method='auto'` + `model_path` (close §5A drift); KDE/PDE byte-identical
- [x] **T11.5** — joblib persistence + frozen-reload determinism (all methods)
- [x] **CP-3a** *(stop-checkpoint)* — **MET 2026-07-03** — imputer built, wired, `test_ml_imputer.py` 40/40 green, no-ML path byte-identical, matrix-family feature-dependence VERIFIED by manager probe (not mean-fill)
- [x] **T11.6** — CP-3 gate: pooled mask-and-recover leaderboard (all 6 methods vs Phase-A) + EUI do-no-harm — **EXECUTED 2026-07-03**: leaderboard done (winner = `knn`, beats Phase-A on `year_built` + `levels`); local field-diff found material vintage-bin divergence (168/738 nyc_centre) → escalated to cluster A/B, jobs **1064373** (Phase-A) / **1064406** (Phase-C/knn) submitted standard-priority, **NOT harvested** (no-babysit stop)
- [x] **CP-3** *(gate)* — **CLOSED, NOT fully MET (2026-07-03, manager-audited).** Attribute-recovery condition MET-but-marginal (winner `knn`); **EUI do-no-harm condition FAILS** — jobs 1064373/1064406 harvested clean (EPW 725053 confirmed via `.eio`, 167/167 both branches, byte-identical footprints), paired **NMBE −5.51 % (breaches <5 %), CV(RMSE) 7.93 % (passes)**; all 167 buildings shift downward (systematic bias). ML does NOT clear the ship bar as-is.
- [!] **T11.7** — *(NOT unblocked — was gated on CP-3 PASS; USER-SIGN-OFF only)* ship wiring + `enrich_semantics` byte-identity reconcile. **Awaiting user: accept built-but-off, OR authorize an observed-range/vintage-bin clamp-and-retry.**

---

## 1. What Phase C delivers (and what CP-2 already settled)

CP-2 proved the **Phase-A statistical tier** recovers `year_built` with near-perfect *downstream-EUI*
impact on real OSM cities: nyc_centre N=32 **NMBE +0.49% / CV(RMSE) 1.71%**, la_urban N=124 **+0.08% /
0.61%** (both PASS 5%/15%). So Phase C is **not** chasing an EUI win — the EUI headroom is already
gone. Phase C answers a narrower, sharper question:

> **Does a classical-ML imputer recover the vintage bin / morphology attribute *more accurately at the
> attribute level* (T08 mask-and-recover MAE/PFC) than the group-median/mode fallback, without
> worsening the downstream-EUI check?**

On nyc_centre the statistical tier got **19/32 exact vintage bins**; 11/32 were mis-recovered by
group-mode. The Phase-C hypothesis is that MissForest-family models using geometry + `use_class` +
spatial-lag features recover more of those 11. CP-3 is therefore an **attribute-recovery** gate with an
EUI **do-no-harm** guard, not an EUI-improvement gate. This framing drives every task below: the
headline CP-3 number is the T08 recovery delta; the EUI check only has to *not regress*.

**Reality check the plan is honest about:** the per-target complete-case **floors** (RF ≥ 1,000; kNN ≥
200; §4) are hard to clear on single-city stock (the CP-2 inventory: observed `year_built` per cell —
la_suburban 1295, la_urban 542, nyc_centre 158; observed `levels` max 136). So (a) CP-3 is evaluated on
a **pooled multi-city complete-case frame** where the RF floor is genuinely cleared, and (b) on any
single small stock the ML tier will legitimately **fall back to Phase-A below floor** — a documented,
correct outcome, not a failure. The shipped feature is **opt-in**; the default run is unchanged.

---

## 2. Hard rules for the executor

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** Execute this plan; do not rewrite it. On DESIGN
   ambiguity **STOP and quote** — except the §5-A ratified point (do not STOP on the "MICE rejected" line).
2. **Never edit `main.py` (root), OVERVIEW, or DESIGN docs. No `.py` under `docs/`.**
3. **Zero-fitted-parameters — the whole point of the arc.** No model hyperparameter, floor, feature, or
   threshold may EVER be selected/tuned to make simulated EUI match a validation anchor. Every estimator
   fits **only** on observed building attributes; **no EUI column may appear anywhere in a fit call
   graph.** The T09/CP-3 EUI number is a *reported evaluation*, never fed back. (DESIGN §3E "nothing is
   trained"; parent §2 rule 4.) Enforce this **structurally** (a test inspecting `__code__.co_names`,
   mirroring `eui_impact.TestNoImputerFeedback`).
4. **Mandatory provenance.** Every ML-filled value carries an `ML_<METHOD>_<TIER>` token **and** a
   HIGH/MED/LOW confidence tier. Extend the parent §5G registry — do not invent a parallel vocabulary.
5. **Fit-on-complete-case-only / no leakage.** Estimators fit from observed rows of the training split
   only; never from the held-out mask rows, and (for pooled multi-city work) the spatial-block holdout
   keeps whole blocks out of the fit (parent §5F / Rule 6). Determinism: all randomness through
   `np.random.default_rng(config.RANDOM_SEED)` and `random_state=config.RANDOM_SEED` on every sklearn
   estimator — same seed ⇒ byte-identical model + fills.
6. **Additive & opt-in — do NOT reroute `enrich_semantics` in T11.1–T11.6.** The ML tier is reached only
   through `impute_missing` when a caller explicitly enables `ml` for an attribute. The default
   `config.IMPUTE_ENABLED_TIERS = ("spatial", "statistical")` is **unchanged** — `ml` is never in the
   default. The production enrichment path (`openubem/semantic/__init__.py` §3B→§3G) is untouched until
   T11.7, which is USER-SIGN-OFF-gated.
7. **Hard target exclusions (unchanged from parent §6 T11).** ML **never** fits
   `cooling_cop`/`heating_efficiency`/U-values/`SHGC`/load densities/setpoints — they have no
   attribute-side signal and stay on the PDE-from-standards path. ML targets are **morphology/semantic
   only:** `year_built` (primary), `levels`, `height` (continuous), `use_class` (categorical).
8. **No new dependencies beyond `scikit-learn` + `joblib`** (parent §4). No `xgboost`/`lightgbm`/`missingpy`.
9. **Default to no comments.** One short line only where the WHY is non-obvious.

---

## 3. File layout

```
openubem/
├── semantic/
│   └── imputation.py    (MODIFY — T11.1 build_ml_imputer + registry; T11.2 confidence/tokens;
│                                  T11.3 _ml_tier wiring + _CANONICAL_TIER_ORDER; T11.4 impute_column auto/model_path)
└── config.py            (MODIFY — T11.3: ML opt-in surface — per-target method + floors constants; ml NOT added to default enabled tiers)

tests/
└── test_ml_imputer.py   (NEW — T11: all sub-tasks; the parent §3 file layout already reserves this file)

docs/docs_ACTIVE/input/imputation/
├── PLAN_phaseC_ml_imputer.md               (this file — §8 progress log appended by executor)
└── PLAN_input_imputation_implementation.md (parent — §0/§8 T11 lines updated by manager only)

scratchpad/  (throwaway — CP-3 evaluation drivers; NEVER under docs/)
└── t11_cp3_*.py   (pooled mask-recover leaderboard + local IDF field-diff — read-only, no EUI feedback)
```

**No files outside this list without a plan update.** Figures (if any) → `openubem/outputs/` (flat).

---

## 4. Dependency decisions (pre-decided — do not re-debate)

| Concern | Decision | Rationale |
|---|---|---|
| ML library | **`scikit-learn` only**, persisted with `joblib`. | Parent §4; DESIGN §3E line 138 ("sklearn pipeline persisted with joblib"). |
| The six methods | One **registry** `{name → sklearn estimator factory}`: `missforest` = `IterativeImputer(RandomForestRegressor/Classifier)`; `mice` = `IterativeImputer(BayesianRidge)`; `knn` = `KNNImputer`; `rf` = `RandomForestRegressor/Classifier` (single-target); `histgbm` = `HistGradientBoostingRegressor/Classifier`; `linear` = `Ridge`/`LogisticRegression`. | Parent §6 T11 menu. A registry keeps "6 methods" a small diff — each is one sklearn constructor behind a shared `Pipeline`(`StandardScaler`+optional `OneHotEncoder`) wrapper. |
| Per-target complete-case floor (N observed after holdout) | `missforest`/`rf`/`linear` **≥ 1,000**; `histgbm` **≥ 5,000** (M04 Table 4); `knn`/`mice` **≥ 200**. **Below floor ⇒ estimator refuses ⇒ `_ml_tier` returns all-null ⇒ routing falls through to statistical.** | M04 §4 "below floor → Phase-A fallback." Floors are **fixed conventions, never swept.** |
| Hyperparameters | **Frozen, never tuned.** `n_estimators=100`, `max_depth=None`, `IterativeImputer(max_iter=10, random_state=RANDOM_SEED)`, `KNNImputer(n_neighbors=5, weights="distance")`, defaults otherwise. `random_state=config.RANDOM_SEED` on every estimator. | Zero-fitted-params: a hyperparameter sweep against EUI is exactly the forbidden move. Frozen defaults are auditable. |
| Feature set (EUI-free) | Geometry-derived only: `footprint_area_m2`, `centroid_x`, `centroid_y`, one-hot `use_class`/`archetype_id`; for `year_built` add a **spatial-lag neighbour vintage** (mean observed year over T06 neighbours). **No EUI, no downstream sim column.** Missing feature cells handled inside `IterativeImputer` or median-filled pre-fit. | M04 §3; parent §6 T11. The structural no-EUI test guards this. |
| Default method per target | `year_built`→`missforest`; `levels`/`height`→`missforest` (below-floor auto-fallback to `knn` ≥200, then stats); `use_class`→`missforest` (classifier). Overridable via config per-target. | MissForest is the M04 primary; others are the documented alternatives selectable per-target within the same class. |

---

## 5. Source-of-truth verified facts (manager-grepped — executor does not re-derive)

**A. ⚠️ RATIFIED NON-CONFLICT — do NOT STOP on the DESIGN "MICE rejected" line.** DESIGN §3E line 140
says *"MICE rejected for MAR violation, deep generative rejected for insufficient rows."* That ruling is
**scoped to the physics-parameter KDE/PDE doctrine** (envelope U-values, SHGC, load densities,
setpoints — the columns §3E's KDE/PDE tier fills), which Phase C **hard-excludes from ML** (rule 7).
The §3E **ML tier itself** — `build_ml_imputer`, described at line 138 as *"sklearn StandardScaler +
regressor pipeline, persisted with joblib … the documented Phase-2 interface"* — is a **separate,
explicitly deferred interface for morphology/semantic targets**, and MissForest =
`IterativeImputer(RandomForestRegressor/Classifier)` is a valid instantiation of that "regressor
pipeline." The parent plan §4 already pinned this dependency. **Manager ruling: no DESIGN conflict; the
executor implements the menu without stopping.** (If a *different* conflict surfaces, still STOP.)

**B. The T11 hook is live and already reachable.**
- `imputation.py:75-89` — `build_ml_imputer(gdf, target_col, feature_cols)` raises `NotImplementedError`
  (labelled *"Phase-2 feature (DESIGN §3E / F12)"*). **This is what T11.1 implements.**
- `imputation.py:184-188` — `_ml_tier(gdf, attr, mask, rng)` currently just calls
  `build_ml_imputer(gdf, attr, [])` and lets the `NotImplementedError` propagate. **T11.3 rewrites this to
  return the `(value, token)` two-Series tier contract** (see D).
- `imputation.py:104` — `_CANONICAL_TIER_ORDER = ("fusion", "spatial", "statistical", "ml")`. **ml is
  LAST**, so today it only ever sees rows the group-median already left null (≈ none) — under the current
  order ML would **never fire**. **T11.3 reorders to `("fusion", "spatial", "ml", "statistical")`** so ML
  is the primary morphology tier and group-median becomes its below-floor/abstain fallback. This reorder
  is **behaviour-preserving for every non-ml routing** (when `ml ∉ tiers`, `(spatial, ml, statistical)`
  with ml skipped ≡ `(spatial, statistical)`); it changes behaviour **only** for attributes that
  explicitly enable `ml`. Prove this with a byte-identity assertion.

**C. §3E code drift T11.4 must close.** Live `impute_column(series, method="kde", bounds, rng, bw_method)`
has **no `auto` routing and no `model_path`** (`imputation.py:14-72`). DESIGN §3E line 122-128 specs
`impute_column(series, method='auto', bounds, model_path, rng)` with AUTO→KDE (0<miss<100%)→PDE (100%
miss)→ML (`model_path` given, joblib pipeline). T11.4 adds `method='auto'` + `model_path` **without
changing** `method='kde'`/`method='pde'` output (byte-identical — a regression here breaks CP-1's
instrumentation-only guarantee).

**D. The tier-handler contract every tier obeys** (`imputation.py:414-427`): a handler
`f(gdf, attr, mask, rng)` returns **`(value, token)`** — two `pd.Series` aligned to `gdf.index`; `value`
is `NaN`/`None` for rows it declines; `token` is the provenance token for filled rows. `impute_missing`
fills `remaining & value.notna()`, stamps `provenance_{attr}`, appends flags via
`prov.append_flag(out, tok_value, mask=...)`, and shrinks `remaining`. `_spatial_tier` is the precedent
to copy: it **accepts HIGH/MED confidence only and discards LOW** (`imputation.py:216-224`) so
low-confidence fills fall through to the safe fallback. **T11.3's `_ml_tier` mirrors this exactly** —
HIGH/MED ML fills win; LOW-confidence ML predictions are discarded and fall through to statistical.

**E. Evaluation harness entry points already exist (T08/T09) — reuse, do not reimplement.**
- `validation/mask_recover.py:284` — `mask_and_recover(gdf, continuous_targets=(), categorical_targets=(),
  block_col=None, n_grid=4, holdout_frac=..., cfg=None, rng=None)` → runs the **real** `impute_missing`
  router under `cfg`, spatial-block holdout, returns `{"continuous": {attr: {mae, rmse, ks_stat,
  wasserstein, n}}, "categorical": {attr: {pfc, log_loss, n}}}`. **CP-3 = run it twice: `cfg` with
  `("spatial","statistical")` (Phase-A baseline) vs `("spatial","ml","statistical")` (Phase-C), same
  seed/holdout, compare per-attribute recovery.** It is **report-only** (parent §2 rule; nothing returned
  is fed back).
- `validation/eui_impact.py:127` `eui_impact_report(observed, imputed, ...)` (paired NMBE/CV(RMSE), gates
  **5%/15%**) and `:167` `compare_ab(gdf_observed, gdf_imputed, schedule_library, out_dir, *,
  simulate_fn=None, ...)` (Stage-3→5 A/B, read-only-on-imputer). The CP-3 EUI check reuses these **only if
  the local field-diff shows material divergence** (see §6 T11.6).
- T06 primitives for features/spatial-lag: `spatial_impute.py:174` `knn_fill`, `:94` `neighbour_vote`;
  fixed `DEFAULT_K=10` / `DEFAULT_RADIUS_M=100` / `MNAR_THRESHOLD=0.60` (`:38-40`) — never overridden.

**F. Parent §5G token registry** (the vocabulary T11.2 extends, not replaces): `HOTDECK_NEIGHBOR_HIGH/MED`
(spatial), `GROUPMODE_MED` (statistical), etc. **T11.2 appends new rows** `ML_MISSFOREST_HIGH/MED/LOW`,
`ML_MICE_*`, `ML_KNN_*`, `ML_RF_*`, `ML_HISTGBM_*`, `ML_LINEAR_*` (or a single generic `ML_<METHOD>_<TIER>`
scheme — executor picks one, records it in the parent §5G table via a manager-approved edit request in the
progress log). Confidence rides in the suffix per M09 §3A.

**G. CP-3 evaluation dataset (pooled real-city complete-case frame).** Build from the committed
`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg` (all 12 cells;
**23-col schema that carries `year_built`** — confirmed at CP-2, supersedes the stale 5-col RESUME_T11
read). Pool the cells' observed-`year_built` complete cases (thousands of rows ⇒ RF floor cleared),
reproject to a common CRS or keep per-city and let `n_grid` blocking separate cities. This is a **LOCAL,
no-cluster, no-EUI** attribute-recovery evaluation.

---

## 6. Task list

> Each task: **What / Why / How / How to test.** All ML code lands in `imputation.py`; all tests in
> `test_ml_imputer.py`. Sub-tasks are ordered; stop at CP-3a after T11.5.

### T11.1 — `build_ml_imputer` core + 6-method estimator registry
- **What:** Replace the `NotImplementedError` stub with a real, fittable imputer factory:
  `build_ml_imputer(gdf, target_col, feature_cols, *, method="missforest", rng=None)` → returns a fitted
  estimator object (a small wrapper exposing `.predict(X)` and, from T11.2, `.confidence(X)`), or **raises
  `BelowFloorError`** (new, subclass of `ValueError`) when observed complete cases < the target's floor.
  Registry maps the six method names (§4) to sklearn constructors, each wrapped in a shared
  `Pipeline([StandardScaler (numeric), OneHotEncoder (categorical features)])` → estimator.
- **Why:** DESIGN §3E line 138 (the deferred Phase-2 ML interface); parent §6 T11 (the six-method menu).
- **How:** Fit **only** on `gdf[gdf[target_col].notna()]` (complete-case). `random_state=RANDOM_SEED` on
  every estimator; frozen hyperparameters (§4) — **no tuning code path exists.** Regressor vs classifier
  chosen by `pd.api.types.is_numeric_dtype(gdf[target_col])`. `feature_cols` default = the EUI-free set
  (§4); **assert no EUI/`total_eui`/`*_eui_kwh_m2` column is in `feature_cols`** and raise if so.
  `BelowFloorError` carries `(method, n_observed, floor)`.
- **How to test:** `test_ml_imputer.py::TestBuildImputer` — (a) fits on a ≥1,000-row synthetic frame and
  predicts finite values; (b) a 50-row frame raises `BelowFloorError` for `missforest`; (c) passing a
  frame with a `total_eui_kwh_m2` feature raises (no-EUI guard); (d) each of the 6 method names constructs
  and fits.

### T11.2 — dispersion → confidence + `ML_<METHOD>_<TIER>` tokens
- **What:** A per-row confidence from model dispersion: tree std across `estimators_` (RF/MissForest/
  single-RF), posterior std (`return_std` — MICE/BayesianRidge), neighbour dispersion (kNN), quantile
  spread (HistGBM), residual std (linear); classifier → top-class vote/proba share. Map to HIGH/MED/LOW by
  **fixed, published-convention cut-points** (e.g. classifier vote-share ≥0.8→HIGH, ≥0.5→MED; regressor
  coefficient-of-dispersion analogue) — **cited, never swept.** Emit `ML_<METHOD>_<TIER>` tokens.
- **Why:** Mandatory provenance (rule 4) + M04 §3 (confidence from model dispersion). Mirrors how T06
  turns neighbour agreement into HIGH/MED/LOW.
- **How:** Add `.confidence(X) → pd.Series[str]` to the T11.1 wrapper. Register the new tokens by
  **requesting a manager edit** to parent §5G (record the exact token strings + cut-points in this task's
  progress-log entry so the manager can ratify + add the row — executor does not edit parent §5G directly).
- **How to test:** `TestConfidence` — a clean/separable synthetic target yields mostly HIGH; a noisy one
  yields more LOW; tokens match `ML_<METHOD>_<TIER>` and the tier suffix agrees with the confidence Series.

### T11.3 — wire `_ml_tier` + reorder canonical order + opt-in config
- **What:** Rewrite `_ml_tier(gdf, attr, mask, rng)` to: check floor → on `BelowFloorError` return all-null
  `(value, token)` (fall through); else `build_ml_imputer(...).predict/​confidence`, **fill HIGH/MED only,
  discard LOW** (D), stamp `ML_<METHOD>_<TIER>`. Reorder
  `_CANONICAL_TIER_ORDER = ("fusion", "spatial", "ml", "statistical")` (B). Add `config.py` opt-in surface:
  `IMPUTE_ML_METHOD_BY_TARGET: dict[str,str]` and `IMPUTE_ML_FLOORS: dict[str,int]` — **do NOT add `ml` to
  `IMPUTE_ENABLED_TIERS`** (opt-in only via `ImputeConfig.per_input_tiers`).
- **Why:** Without the reorder ML can never precede the group-median fallback and never fires (B). Opt-in
  keeps the default run and CP-1 byte-identity intact (rule 6).
- **How:** Keep the return-contract identical to `_spatial_tier`. The reorder is behaviour-preserving for
  non-ml routing — **assert** it (run the existing `test_imputation_routing` + `test_mask_recover` suites;
  they must stay green unchanged).
- **How to test:** `TestRouting` — with `per_input_tiers={"year_built":("spatial","ml","statistical")}` on a
  ≥floor frame, ML fills the residual and `provenance_year_built` shows `ML_*` on those rows; group-median
  fills only what ML declined; with a sub-floor frame ML is skipped and fills are 100% `GROUPMODE_MED`
  (proves the fallback). Full CP-1 gate suite still green.

### T11.4 — reconcile `impute_column` to §3E `method='auto'` + `model_path`
- **What:** Extend `impute_column` signature to
  `impute_column(series, method="kde", bounds=None, rng=None, bw_method="scott", model_path=None)` and add
  `method="auto"` routing (0<miss<100%→KDE, 100% miss→PDE, `model_path` given→ML joblib-load+predict), per
  DESIGN §3E line 122-128. **`method="kde"` and `method="pde"` outputs stay byte-identical.**
- **Why:** Closes the parent §5A code-vs-DESIGN drift; completes the §3E interface.
- **How:** Purely additive branches; the ML branch loads a T11.5 joblib artifact. Do not change the
  existing KDE/PDE code paths.
- **How to test:** `TestImputeColumnAuto` — `method="kde"`/`"pde"` byte-identical to pre-change (golden
  arrays); `method="auto"` routes correctly by missingness; `model_path` loads a persisted imputer and fills.

### T11.5 — joblib persistence + frozen-reload determinism
- **What:** `save_ml_imputer(imputer, path)` / `load_ml_imputer(path)` via joblib; a reloaded model
  produces **byte-identical** predictions to the in-memory model (frozen weights).
- **Why:** DESIGN §3E line 138 ("persisted with joblib"); reproducibility (rule 5).
- **How:** Persist the whole fitted `Pipeline` + metadata (method, target, feature_cols, floor). Reload +
  predict must equal pre-persist predict under the same seed.
- **How to test:** `TestPersistence` — fit → save → load → assert `predict` arrays equal and `confidence`
  equal; round-trips all 6 methods.

> ### 🛑 CP-3a — stop-and-report (after T11.5)
> The imputer is built, wired, and unit-green **before** any evaluation effort is spent. **Gate:**
> `test_ml_imputer.py` fully green; `test_imputation_routing` + `test_mask_recover` + the CP-1 gate suite
> green **unchanged** (no-ML path byte-identical); the `_CANONICAL_TIER_ORDER` reorder proven
> behaviour-preserving. Executor appends §8 entries and **waits for manager audit** before T11.6.

### T11.6 — CP-3 gate: attribute-recovery leaderboard + EUI do-no-harm
- **What:** Two read-only evaluations, both scripted in `scratchpad/` (throwaway, no EUI feedback):
  1. **Attribute recovery (headline).** On the pooled real-city complete-case frame (§5G), run
     `mask_and_recover` for **Phase-A** `cfg=("spatial","statistical")` vs **Phase-C**
     `cfg=("spatial","ml","statistical")` per method in the menu, **same seed + same holdout**. Produce a
     leaderboard: per target (`year_built` primary; `levels`/`use_class` secondary) × method →
     MAE/RMSE/KS (continuous) or PFC/log-loss (categorical) + **exact-vintage-bin recovery count**, each
     vs the Phase-A baseline row. Report which methods (if any) **beat** Phase-A and by how much; report
     below-floor fall-backs honestly.
  2. **EUI do-no-harm (guard) — LOCAL IDF field-diff primary.** For the winning config, materialize the
     Phase-A vs Phase-C imputed frames on the gate cell (nyc_centre), build IDFs for both (toggling **only**
     the imputed `year_built`/derived vintage, everything else common-mode — the CP-1 method), and
     **field-diff**. If the ML fills produce **identical vintage bins** on EUI-relevant rows ⇒ EUI Δ is
     provably ~0, **no cluster needed.** **Escalate to a cluster A/B** (reuse the T09-CC sbatch machinery,
     `compare_ab`, standard priority, Sonnet, never touch other runs) **only if** fills diverge materially
     (a vintage-bin flip on ≥1 EUI-relevant building).
- **Why:** CP-3 (parent §7): ML ships only if it beats Phase-A on mask-and-recover AND does not worsen the
  EUI check. §1: recovery is the headline, EUI is do-no-harm. Local field-diff is the ratified
  cost-disciplined EUI method (CP-1 precedent).
- **How:** `mask_and_recover` is report-only; **never** feed its output back into `cfg`. Pin seed = 42,
  `n_grid`/`holdout_frac` = the T08 defaults, so the A/B differ **only** in the `ml` tier. If a cluster
  escalation fires, the employee submits standard-priority + reports job IDs + STOPS (no babysit); manager
  harvests per the T09-CC recipe.
- **How to test:** covered by the evaluation itself (it *is* the gate). Determinism: re-running the
  leaderboard with seed 42 reproduces the table.

> ### 🛑 CP-3 — the gate (after T11.6)
> **Ships only if** ≥1 menu method **beats** the Phase-A baseline on T08 mask-and-recover for ≥1 morphology
> target **AND** the EUI field-diff/A-B shows **no worsening** (within the 5%/15% do-no-harm gates).
> Otherwise the ML tier stays built-but-opt-in-off (a legitimate "no attribute-level win at this scale"
> outcome — still a shippable, documented capability). **Report the leaderboard + EUI result to the user
> and STOP.** Interpretation + the ship decision are the user's (T11.7).

### T11.7 — ship wiring + `enrich_semantics` byte-identity reconcile — 🔴 USER-SIGN-OFF ONLY
- **What:** *(Only after CP-3 passes AND the user accepts.)* Turn the ML tier from harness-only into a
  selectable production tier and **re-establish the CP-1 byte-identity guarantee** for the enrichment path:
  the parent's logged carry-forward — the generic `impute_missing` vintage/levels path *may bin differently
  than the monolithic `resolve_vintage`/`_impute_levels`* — must be reconciled **here**, when/if
  `enrich_semantics` is allowed to route through `impute_missing` with ml enabled.
- **Why:** Parent CP-2 carry-forward (memory + parent §8): byte-identity must be re-established when Phase C
  reroutes `enrich_semantics`. Promotion of a default-run behaviour is a load-bearing, hard-to-reverse change.
- **How:** Deferred design — scope T11.7's exact tasks **after** the CP-3 numbers exist and the user rules.
  Options range from "ship opt-in only, `enrich_semantics` untouched" (zero byte-identity risk) to "route the
  production vintage path through the ML tier" (requires a fresh byte-identity field-diff like CP-1). **Do
  not start T11.7 without the user's explicit go.**
- **How to test:** defined at T11.7 scoping; minimally a repeat of the CP-1 IDF byte-identity field-diff if
  the production path changes.

---

## 7. Stop-and-report checkpoints

- **CP-3a — after T11.5.** Imputer built + wired + unit-green + no-ML path byte-identical, *before* spending
  evaluation effort. (Catches a broken tier contract / a non-behaviour-preserving reorder before it
  contaminates the gate numbers.)
- **CP-3 — after T11.6.** The gate. Report the recovery leaderboard + EUI do-no-harm result; **STOP** for
  the user's ship decision. Do not enable `ml` in any default path.
- **🔴 T11.7 USER-SIGN-OFF gate.** No production wiring / `enrich_semantics` reroute / default-run change
  without the user's explicit acceptance of the CP-3 numbers. (Mirrors the E-R3-3 T11.7 baseline-promotion
  gate: producing the comparison is authorized; changing the shipped default is not.)

---

## 8. Progress log

*(Executor appends one entry per completed sub-task — format per CLAUDE.md §"Plan doc structure". Manager
may append audit notes. The binding arc record remains the parent plan §8; cross-reference entries there.)*

#### Manager — Phase-C plan authored — 2026-07-03
- Artifacts: `PLAN_phaseC_ml_imputer.md` (this doc); pointer added to parent `PLAN_input_imputation_implementation.md` §6 T11 + §0.
- Deviations: none (planning only). Scope set by user 2026-07-03: full M04 six-method menu behind one estimator registry; EUI check = local IDF field-diff primary, cluster on divergence.
- Test status: n/a (plan doc).
- Notes: Decomposed parent T11 into T11.1–T11.7 with two stop-checkpoints (CP-3a build-complete, CP-3 gate) + the T11.7 user-sign-off gate. Pinned the load-bearing architecture: (1) reorder `_CANONICAL_TIER_ORDER` to `(fusion, spatial, ml, statistical)` so ML is the primary morphology tier with group-median as its below-floor/abstain fallback — proven behaviour-preserving for all non-ml routing; (2) `_ml_tier` obeys the `(value, token)` tier contract and accepts HIGH/MED confidence only (LOW discarded, mirrors `_spatial_tier`); (3) CP-3 headline = **attribute-recovery** delta (CP-2 already exhausted the EUI headroom — nyc +0.49%/1.71%, la +0.08%/0.61%), EUI check is do-no-harm; (4) ratified the DESIGN "MICE rejected" non-conflict (§5-A) so the executor doesn't STOP; (5) evaluation on a **pooled** real-city complete-case frame to clear the RF≥1000 floor, with honest below-floor fallback on single-city stock. Opt-in only; `enrich_semantics`/default run untouched until the T11.7 user-sign-off. Carry-forward preserved: re-establish `enrich_semantics` byte-identity at T11.7 (parent CP-2 carry-forward).

#### Manager — Phase-C DISPATCHED to Sonnet executor (T11.1→CP-3a) — 2026-07-03
- Artifacts: none yet (dispatch only). Fresh Sonnet employee launched (background) with the standard OpenUBEM kickoff, scoped to **T11.1 → T11.5 then hard-stop at CP-3a**; explicitly barred from starting T11.6 (the CP-3 evaluation gate) until manager audit.
- Deviations: none.

#### T11.1 — `build_ml_imputer` core + 6-method estimator registry — completed 2026-07-03
- Artifacts: `openubem/semantic/imputation.py` (`BelowFloorError`, `_ML_METHOD_NAMES`, `_ML_FLOORS`, `_DEFAULT_ML_FEATURE_COLS`, `_assert_no_eui_leakage`, `_build_supervised_estimator`, `MLImputer` dataclass, `build_ml_imputer`); `pyproject.toml` (added `scikit-learn` to `[project] dependencies` — installed 1.9.0 into `.venv`); `tests/test_ml_imputer.py::TestBuildImputer` (12 tests incl. a 6-way parametrization over every method name, all green).
- Deviations (both empirically verified, not guessed — see the two probe scripts run before implementation):
  1. **Registry family split.** Plan §4 maps `missforest`/`mice`→`IterativeImputer`, `knn`→`KNNImputer` uniformly. Empirically, `IterativeImputer(estimator=RandomForestClassifier(...))` **crashes** (`ValueError: Unknown label type: continuous`) the moment the joint feature+target matrix mixes continuous feature columns with a classifier estimator, because IterativeImputer applies ONE estimator class across every column in the matrix, including the continuous features. Since sklearn has no supported way to give IterativeImputer a per-column estimator, classification targets for `missforest`/`mice`/`knn` fall back to the natural single-target supervised classifier instead (`RandomForestClassifier` / `LogisticRegression` / `KNeighborsClassifier` respectively) — regression targets still use the genuine `IterativeImputer`/`KNNImputer` matrix family exactly as specified. `family = "matrix"` only when `method in (missforest,mice,knn) and not is_classifier`; else `"supervised"`.
  2. **Fit/predict split for the matrix family confirmed correct by direct empirical test** (not assumed): fit `IterativeImputer`/`KNNImputer` ONCE on a matrix where `target_col` retains its real observed/complete-case pattern (zero missing at fit time, since we fit only on `gdf[target_col].notna()` rows); `.transform()` on a NEW matrix with `target_col=NaN` correctly recovers the feature→target relationship (verified: predicted ≈ `3*x1 - 2*x2` on held-out rows after fitting on a fully-observed matrix). This is the standard, no-leakage-safe IterativeImputer/KNNImputer usage pattern and satisfies "fit only on complete cases" literally.
  3. **Categorical features inside the matrix family are ordinal-encoded** (fit-time category→int map, `__UNKNOWN__` fallback code for unseen categories at predict time), not one-hot — one-hot expansion inside a jointly-imputed numeric matrix has no clean inverse and isn't how MissForest-style tools handle factors in practice; ordinal coding is the standard simplification (R's `missForest` handles factors natively, sklearn's `IterativeImputer` does not). The supervised family (rf/histgbm/linear + all classifiers) uses a proper `ColumnTransformer(StandardScaler + OneHotEncoder(handle_unknown="ignore"))` inside a `Pipeline`, per plan §4.
  4. `pyproject.toml` is not listed in plan §3's file layout, but §4's dependency table explicitly sanctions `scikit-learn` as the (only) new dependency — added it so the dependency is reproducible via `pip install -e .`, not just present in this session's venv.
- Test status: `TestBuildImputer` 7/7 green (fits + finite predictions on a >=6000-row synthetic fixture; `BelowFloorError` on a 50-row frame; EUI-column guard raises for both feature-side and target-side leakage; all 6 method names construct+fit; unknown method raises; classifier target (`use_class`) predicts >70% accuracy on a footprint-correlated synthetic signal).
- Notes: Floors read from `config.IMPUTE_ML_FLOORS` at call time (lazy import, falls back to the in-module `_ML_FLOORS` default if the config key is absent) so tests can monkeypatch. `feature_cols=[]`/`None` defaults to `_DEFAULT_ML_FEATURE_COLS` filtered to columns present in `gdf` (excluding `target_col`).

#### T11.2 — dispersion → confidence + `ML_<METHOD>_<TIER>` tokens — completed 2026-07-03
- Artifacts: `openubem/semantic/imputation.py` (`_tier_from_score`, `MLImputer.confidence`/`_rf_tree_dispersion`/`_mice_dispersion`/`_knn_dispersion`); `tests/test_ml_imputer.py::TestConfidence` (4 tests, all green).
- **Tokens chosen (requesting manager ratification into parent §5G):** single generic scheme `ML_<METHOD>_<TIER>` (the plan's "or" option, not six parallel per-method families) — literal strings emitted: `ML_MISSFOREST_HIGH`, `ML_MISSFOREST_MED`, `ML_MICE_HIGH`, `ML_MICE_MED`, `ML_KNN_HIGH`, `ML_KNN_MED`, `ML_RF_HIGH`, `ML_RF_MED`, `ML_HISTGBM_HIGH`, `ML_HISTGBM_MED`, `ML_LINEAR_HIGH`, `ML_LINEAR_MED` (`<METHOD>` = `method.upper()`, `<TIER>` = `HIGH`/`MED`; `LOW` is never stamped — discarded per the `_spatial_tier` precedent, D). Confidence cut-points (fixed, cited, never swept): **classifier** — top-class `predict_proba` share, `>=0.8`→HIGH, `>=0.5`→MEDIUM, else LOW (plan's own literal example). **Regressor** — coefficient-of-dispersion analogue `score = 1/(1+cv)` with `cv = |dispersion/prediction|`, same `>=0.8`/`>=0.5` cut-points — **identical formula and thresholds to `spatial_impute._confidence_tier`/`knn_fill`** (T06), reused rather than invented. Per-method dispersion source: RF/MissForest — std across `estimators_` tree predictions (mean = ensemble mean); MICE/BayesianRidge — `predict(X, return_std=True)` posterior std; kNN (matrix family) — a dedicated `NearestNeighbors(n_neighbors=5)` fit on the training feature matrix, weighted-mean/weighted-std over the neighbours' true target values (mirrors `spatial_impute.knn_fill`'s pattern); HistGBM/linear (no native per-row uncertainty API) — **global in-sample residual std** (`|y_train - in_sample_predict|.std()`) divided by each row's own predicted magnitude (a documented simplification of the plan's "quantile spread (HistGBM)" — HistGBM's native quantile-spread would need 3 separately-fit quantile models per target, which conflicts with "frozen hyperparameters, no extra fit calls"; flagging for manager review, not a hard blocker since it is a report-only confidence estimate, never fed back).
- Deviations: the HistGBM "quantile spread" simplification above (residual-std fallback instead of a 3-quantile-model spread) — cited, not swept, but not literally what M04 §3 describes; the plan's `_MED_THRESHOLD`/`_HIGH_THRESHOLD` example values were adopted verbatim rather than independently re-derived (matches the plan's own worked example, "cited, never swept").
- Test status: `TestConfidence` 4/4 green. Verified empirically before committing to the design: for `year_built` (large baseline ~1950-2020), the `cv=std/|mean|` formula is essentially insensitive (always HIGH) because a realistic std (tens of years) is tiny relative to the ~2000 baseline — this is inherited from `spatial_impute`'s identical formula (pre-existing, accepted pattern for T06, not a new defect). The `TestConfidence` "noisy signal -> more LOW" test therefore targets `levels` (small integer magnitude), where the formula is responsive (empirically confirmed: clean signal -> 100% HIGH; noisy/unrelated-to-features signal -> 0% HIGH, mix of MEDIUM/LOW) — this is a test-design choice, not a code change; the `year_built` insensitivity is unchanged/inherited behaviour worth the manager's awareness at CP-3a.
- Notes: `MLImputer.confidence(X)` always runs `_prep(X)` (median/mode gap-fill) first, exactly like `.predict(X)`, so confidence and the corresponding predicted value are computed off the identical feature row.

#### T11.3 — wire `_ml_tier` + reorder canonical order + opt-in config — completed 2026-07-03
- Artifacts: `openubem/semantic/imputation.py` (`_CANONICAL_TIER_ORDER` reordered to `("fusion","spatial","ml","statistical")`; `_ml_method_for`, `_ml_feature_cols_for`, `_spatial_lag`, rewritten `_ml_tier`); `openubem/config.py` (`IMPUTE_ML_METHOD_BY_TARGET`, `IMPUTE_ML_FLOORS` — **`ml` NOT added to `IMPUTE_ENABLED_TIERS`**, confirmed unchanged: `("spatial","statistical")`); `tests/test_ml_imputer.py::TestRouting` (4 tests) + `TestOptInOnly` (2 tests), all green.
- **`year_built` spatial-lag feature implemented** (plan §4): `_spatial_lag(gdf, "year_built")` reuses T06's private `_build_tree`/`_query_neighbours` KD-tree primitives (already self-excluding by construction) to compute, for every row, the distance-weighted mean of NEIGHBOURS' observed `year_built` (never the row's own value) — safe as a training feature for `year_built` itself (no self-leakage). Wired only when `attr == "year_built"` and `geometry` is present; injected as an extra column (`__ml_year_built_spatial_lag__`) on a **copy** of `gdf` passed to `build_ml_imputer`, never mutating the caller's frame.
- Deviations: none from the plan's explicit T11.3 spec. **However, flagging a load-bearing consequence for CP-3a** (see "Existing-test conflicts" below): implementing `_ml_tier` exactly as specified (catch `BelowFloorError` -> return all-null, no propagation) necessarily changes the force-enabled-`ml` skeleton-stub behaviour that two PRE-EXISTING tests assert.
- Test status: `TestRouting` 4/4 green, incl. a dedicated byte-identity proof that the `_CANONICAL_TIER_ORDER` reorder is behaviour-preserving for non-ml routing (`test_canonical_order_reorder_is_behaviour_preserving_for_non_ml_routing`: `pd.testing.assert_frame_equal` between the new order and the pre-T11.3 order `("fusion","spatial","statistical","ml")` via monkeypatch, both restricted to `enabled_tiers=("spatial","statistical")` — byte-identical). `TestOptInOnly` 2/2 green (`"ml" not in config.IMPUTE_ENABLED_TIERS`; a monkeypatched `_ml_tier` spy proves the default `impute_missing()` call never invokes it). The dedicated "ML fills the residual spatial declines" test required constructing an isolated MNAR pocket (a tight cluster of 80 rows placed far from the main synthetic grid, all masked together) to force T06's MNAR guard to decline them — on the main dense/uniform synthetic grid, `_spatial_tier` always finds high-confidence neighbours and would consume 100% of any random mask, never leaving ML a residual to fill; this is a test-fixture necessity, not a code change.
- **Existing-test conflicts found (2, both OUT of this task's file scope — `tests/test_imputation_routing.py` and `tests/test_imputation.py` are not in plan §3's file layout, so NOT edited):**
  1. `tests/test_imputation_routing.py::TestForceEnabledSkeletonStubs::test_ml_force_enabled_raises_not_implemented` (lines 181-185) asserts `impute_missing(df, cfg=ImputeConfig(enabled_tiers=("ml",)))` raises `NotImplementedError` when `ml` is force-enabled. This test locks in the PRE-T11 skeleton-stub contract, documented in the parent plan itself at `PLAN_input_imputation_implementation.md:518-520`: *"ML tier if force-enabled: `build_ml_imputer` still raises `NotImplementedError` (Phase C not built) — do NOT catch-and-swallow into a silent fallback; let it surface (honest: the tier isn't built)."* T11.3's own explicit spec (`PLAN_phaseC_ml_imputer.md` T11.3 "What", line 246-248) requires the OPPOSITE now that Phase C IS built: *"Rewrite `_ml_tier`... to: check floor -> on `BelowFloorError` return all-null `(value, token)` (fall through)."* These two contracts are mutually exclusive for a 1-row all-NaN frame — implementing T11.3 as specified necessarily makes this pre-existing test fail (confirmed: `DID NOT RAISE <class 'NotImplementedError'>`). I did not edit this file (out of scope); implemented `_ml_tier` exactly per the T11.3 spec.
  2. `tests/test_imputation.py::test_ml_imputer_stub_raises` (lines 87-90) asserts `build_ml_imputer(df, "a", ["b"])` raises `NotImplementedError` matching `"Phase-2"` on a 1-row frame. Same root cause: T11.1 replaces the Phase-2 stub with a real implementation, so this specific 1-row/2-column input now correctly raises `BelowFloorError` (a `ValueError` subclass, not `NotImplementedError`) instead. Confirmed failing; not edited (out of scope).
  - **Both are the sole 2 failures across the full imputation-relevant suite** (169 passed / 2 failed when run together with `test_ml_imputer.py`); every other pre-existing test, including the full CP-1 75/76-test gate suite and `test_mask_recover.py` (22/22, untouched — default `cfg` never reaches `ml`), is green and unchanged. Recommend the manager authorize a narrow, targeted update to these 2 assertions (they test a now-superseded "Phase C not built" premise) in a follow-up outside this task's file scope.

#### T11.4 — reconcile `impute_column` to §3E `method='auto'` + `model_path` — completed 2026-07-03
- Artifacts: `openubem/semantic/imputation.py` (`impute_column` signature extended with `model_path=None`; `method="auto"` routing: `model_path is not None`→`"ml"`, `nan_mask.all()`→`"pde"`, else→`"kde"`; new `method="ml"` branch); `tests/test_ml_imputer.py::TestImputeColumnAuto` (7 tests, all green).
- **KDE/PDE byte-identity proof method:** rather than diffing against the pre-change file (not mechanically available inside a test), `test_kde_output_matches_independent_reference`/`test_pde_output_matches_independent_reference` independently re-derive the expected array from scratch (a fresh `scipy.stats.gaussian_kde(...).resample(...)` / `rng.uniform(...)` call under the same seed, bypassing `impute_column` entirely) and assert exact (`np.testing.assert_array_equal`, not `approx`) equality against `impute_column`'s output — proves the existing KDE/PDE code bodies were not touched (confirmed by inspection: the new branches are inserted strictly BEFORE the existing `if method == "kde":`/`if method == "pde":` blocks, whose bodies are byte-identical to pre-T11.4).
- **`method="ml"` architectural note (flagging for manager awareness, not a DESIGN conflict):** DESIGN §3E's `impute_column` signature (line 122-124) takes only a single `series` — no feature-frame parameter — so the ML branch here cannot supply per-row features the way `_ml_tier`/`build_ml_imputer` do directly. Implemented as: load the persisted `MLImputer`, build an all-NaN feature frame shaped to the imputer's own `feature_cols` (so `MLImputer._prep`'s stored per-feature median/mode fill applies uniformly to every missing row), and predict. This is a documented, honest degeneration (constant/typical-feature prediction, not a personalized one) forced by DESIGN's own single-`series` signature — real per-row-feature ML imputation goes through `_ml_tier`/`build_ml_imputer` directly (the actual `impute_missing` production path), never through this low-level primitive. `impute_column(method="auto"/"ml")` is exercised only by the T11.4 unit tests at this checkpoint; no caller in the codebase invokes it yet.
- Test status: `TestImputeColumnAuto` 7/7 green (kde/pde golden-array cross-checks; auto routes to kde for partial missingness and pde for total missingness, both byte-identical to the direct call; `model_path` loads a persisted imputer and fills, including exact passthrough of the 2 already-observed values in the test series; `method="ml"` without `model_path` raises; unknown method still raises).
- Deviations: none from plan text; the feature-frame limitation above is an inherent consequence of DESIGN's own signature, not a deviation from it.

#### T11.5 — joblib persistence + frozen-reload determinism — completed 2026-07-03
- Artifacts: `openubem/semantic/imputation.py` (`save_ml_imputer`, `load_ml_imputer`); `tests/test_ml_imputer.py::TestPersistence` (7 tests: 6 methods parametrized + 1 classifier round-trip), all green.
- Deviations: none. `MLImputer` is a plain (non-frozen) `@dataclass` wrapping only joblib-picklable members (sklearn `Pipeline`/`IterativeImputer`/`KNNImputer`/`NearestNeighbors` objects, dicts, tuples, floats) — `joblib.dump`/`joblib.load` operate on the whole instance directly, no custom `__getstate__`/`__setstate__` needed.
- Test status: `TestPersistence` 7/7 green — for every one of the 6 methods (`missforest`, `mice`, `knn`, `rf`, `histgbm`, `linear`), fit → predict/confidence → save → load → predict/confidence again asserts exact equality (`np.testing.assert_array_equal` on predictions, `Series.equals`-style `==`-all on confidence tiers); a dedicated classifier round-trip (`use_class`) confirms string-label predictions survive the round-trip exactly.

#### T11 (T11.1-T11.5) — CP-3a reached — 2026-07-03
- Artifacts: `openubem/semantic/imputation.py`, `openubem/config.py`, `pyproject.toml` (added `scikit-learn`), `tests/test_ml_imputer.py` (NEW, 40 tests: `TestBuildImputer` 12 + `TestConfidence` 4 + `TestRouting` 4 + `TestImputeColumnAuto` 7 + `TestPersistence` 7 + `TestNoEUILeakage` 4 + `TestOptInOnly` 2 = 40).
- **CP-3a gate status:**
  1. `test_ml_imputer.py` fully green: **40/40 passed** (60.8s, includes 6000-row synthetic fixtures across 6 sklearn methods).
  2. `test_imputation_routing.py` + `test_mask_recover.py` + the CP-1 gate suite (`test_tierB_provenance`/`test_vintage_donor`/`test_levels_groupwise`/`test_spatial_impute`/`test_provenance`, 76 tests): green **except the ONE pre-existing test documented under T11.3** (`test_ml_force_enabled_raises_not_implemented`) — every other test in these files, including all of `test_mask_recover.py` (22/22) and the full CP-1 76-test gate, is unchanged and green.
  3. `test_imputation.py`: green except the ONE pre-existing test documented under T11.3 (`test_ml_imputer_stub_raises`).
  4. No-ML-path byte-identical: proven both structurally (`TestOptInOnly`, default `impute_missing()` never calls `_ml_tier`; `"ml" not in config.IMPUTE_ENABLED_TIERS`) and via the dedicated reorder byte-identity test (`test_canonical_order_reorder_is_behaviour_preserving_for_non_ml_routing`).
  - **Combined tally, whole imputation-relevant suite run together:** `pytest tests/test_ml_imputer.py tests/test_imputation_routing.py tests/test_mask_recover.py tests/test_imputation.py tests/test_tierB_provenance.py tests/test_vintage_donor.py tests/test_levels_groupwise.py tests/test_spatial_impute.py tests/test_provenance.py -q` → **169 passed, 2 failed** in 63.82s. The 2 failures are the exact, pre-identified, plan-vs-existing-test conflicts documented under T11.3 — no other regression. A full-repo sweep (`pytest tests/ -q -m "not slow and not energyplus"`, 1349 tests collected cleanly, zero import/collection errors) was also run to rule out any wider blast radius from the `pyproject.toml`/`config.py` changes; see the follow-up log entry for its result.
- Deviations: summarized per-task above; the two headline items for manager ratification are (a) the T11.2 token/threshold choices (this entry's T11.2 section) and (b) the 2 existing-test conflicts (T11.3 section) needing a manager-authorized narrow test update outside this task's file scope.
- Notes: **STOPPING HERE per the executor's kickoff instructions — CP-3a reached, T11.6/CP-3 NOT started.** Awaiting manager audit.
- Test status: n/a (pending executor report).
- Notes: Kickoff embedded the §2 hard rules verbatim — zero-fitted-params structural test (`__code__.co_names`, mirror `eui_impact.TestNoImputerFeedback`); additive/opt-in (no `enrich_semantics` reroute, `ml` NOT in default `IMPUTE_ENABLED_TIERS`); the `_CANONICAL_TIER_ORDER` reorder must be proven byte-identity behaviour-preserving with existing `test_imputation_routing`/`test_mask_recover`/CP-1 suites green-unchanged; KDE/PDE golden-array byte-identity through T11.4; §5-A ratified non-conflict (do not STOP on "MICE rejected"). Executor instructed to record the T11.2 tokens+cut-points in its progress log for manager §5G ratification (not edit parent §5G directly). Awaiting the CP-3a build-complete report + pytest summary for audit.

#### Manager — CP-3a AUDIT: MET — greenlit T11.6 — 2026-07-03
- Artifacts audited: `openubem/semantic/imputation.py`, `openubem/config.py`, `tests/test_ml_imputer.py`, `pyproject.toml`; probe `scratchpad/probe_missforest.py` (throwaway, local, no-cluster, no-EUI).
- **Verdict: CP-3a MET.** Read the full load-bearing file + tests rather than trusting the report. All four gate conditions confirmed: (1) `test_ml_imputer.py` 40/40; (2) `test_mask_recover.py` 22/22 + CP-1 76-test gate green-unchanged — the only 2 imputation-suite failures are the pre-Phase-C stub-contract assertions (`test_imputation.py::test_ml_imputer_stub_raises`, `test_imputation_routing.py::test_ml_force_enabled_raises_not_implemented`), both legitimately superseded by the T11.1/T11.3 spec and both confirmed by direct read to assert the *old* "Phase-C not built" premise; (3) no-ML path byte-identical (reorder swaps only the `ml`↔`statistical` pair, order-preserving for every non-ml tier set — verified in the routing loop + the executor's byte-identity test); (4) opt-in confirmed (`ml` ∉ `config.IMPUTE_ENABLED_TIERS`; default `impute_missing` never calls `_ml_tier`).
- **Load-bearing correctness check the executor's tests did NOT cover — manager ran it directly:** no test asserts matrix-family (missforest/mice/knn-reg) predictions are *feature-dependent* (finite-only asserts would pass on a constant mean-fill). Probe result: all six methods track an injected `1900+footprint/5` signal — missforest lo/hi-footprint preds 1912.15/1996.98 (|Δ|=84.8), 200-row spread 25.5 ≈ target std 26.1 (mean-fill would give Δ≈0, spread≈0); `imputation_sequence_` carries a target triplet so `_matrix_target_estimator`/`confidence` are safe. **Mean-fill risk REFUTED; matrix-family fit is sound.**
- Deviations ratified: (a) T11.2 `ML_<METHOD>_<TIER>` token scheme + cut-points → **added to parent §5G** (manager edit, with the `year_built` all-HIGH confidence caveat recorded there for CP-3); (b) registry family split (classification uses single-target supervised, not IterativeImputer — empirically forced, sound); (c) `pyproject.toml` scikit-learn add (sanctioned by §4; plan §3 file-list should have listed it — noted); (d) HistGBM confidence = global-residual-std fallback (accepted simplification, report-only, non-discriminative — CP-3 note). Trivial: `impute_missing` docstring line ~848 still says `spatial→statistical→ml` (stale; code uses the reordered `_CANONICAL_TIER_ORDER` correctly) — fold the one-line doc fix into T11.6.
- Test status: manager probe green (6/6 feature-dependent); executor tally 169 passed / 2 failed accepted (the 2 = documented superseded stubs). T11.6 executor to reconcile the 2 stub assertions to the shipped contract as step 0, then re-confirm the whole imputation suite green.
- Notes: **CP-3a GREENLIT → T11.6 dispatched** (fresh Sonnet, local pooled mask-recover leaderboard + local IDF field-diff EUI do-no-harm). Hard-STOP at CP-3 for the user's ship decision; T11.7 remains user-sign-off-gated.

#### T11.6 STEP 0 — pre-gate test reconciliation (manager-authorized) — completed 2026-07-03
- Artifacts: `tests/test_imputation.py` (`test_ml_imputer_stub_raises` → `test_ml_imputer_below_floor_raises`, now asserts `BelowFloorError` not `NotImplementedError`; import added); `tests/test_imputation_routing.py` (`test_ml_force_enabled_raises_not_implemented` → `test_ml_force_enabled_below_floor_falls_through`, now asserts `impute_missing` does NOT raise and the sub-floor `levels` row stays `NaN`); `openubem/semantic/imputation.py` (`impute_missing` docstring line ~848: `fusion -> spatial -> statistical -> ml` → `fusion -> spatial -> ml -> statistical`, comment-only, code unchanged).
- Deviations: none — exactly the 3 manager-authorized edits (a)/(b)/(c) from the kickoff, nothing else touched in either test file.
- Test status: `pytest tests/test_ml_imputer.py tests/test_imputation.py tests/test_imputation_routing.py tests/test_mask_recover.py tests/test_tierB_provenance.py tests/test_vintage_donor.py tests/test_levels_groupwise.py tests/test_spatial_impute.py tests/test_provenance.py -q` → **171 passed, 0 failed** in 67.7s. The full imputation-relevant suite is now fully green (the 2 CP-3a-audited stub-contract failures are resolved).
- Notes: none beyond the kickoff spec.

#### T11.6 — CP-3 gate: pooled attribute-recovery leaderboard + EUI do-no-harm — completed 2026-07-03 (EUI harvest PENDING)
- Artifacts: `scratchpad/t11_cp3_leaderboard.py` (pooled mask-and-recover leaderboard driver, reuses `mask_recover.mask_and_recover`/public primitives) + `scratchpad/t11_cp3_leaderboard_results.json` + `_run1.log`/`_run2.log` (determinism proof, byte-identical); `scratchpad/t11_cp3_eui_field_diff.py` + `_run1.log` (standalone pooled-fit vintage-bin field-diff on the gate cell, reuses `construction_sets.resolve_vintage` verbatim); `scratchpad/t11_cp3_eui_cluster_prep.py` + `_run1.log` (full-production-path IDF build for both branches, reuses `scripts/validation/v12_cell_pipeline.step2_classify_enrich`/`step3_generate`, i.e. the real `enrich_semantics`/`run_step3`); `scratchpad/t11cc_work/{phaseA,phaseC}/step3/idfs/*.idf` (167+167 real IDFs) + `manifest_a.parquet`/`manifest_c.parquet` + `diverge_osm_ids.txt`.
- **1. Pooled attribute-recovery leaderboard (headline).** Pooled all 12 committed phaseE `01_buildings.gpkg` cells (n=8160), reprojected to a common CRS (EPSG:5070, Conus Albers — avoids cross-UTM-zone KNN/spatial-tier corruption across NYC/LA/Austin's 3 different native UTM zones; `centroid_x`/`centroid_y` derived post-reprojection). **Pooled observed N: `year_built` = 2247 (clears the RF/missforest/rf/linear ≥1000 floor comfortably; train split after 80/20 spatial-block holdout ≈1797, still clears 1000 but NOT histgbm's ≥5000); `levels` = 441 (clears the kNN/MICE ≥200 floor only — NOT missforest/rf/linear/histgbm).** `use_class` could NOT be evaluated — it is not a column in the Stage-1 `01_buildings.gpkg` 23-col schema (only populated by Stage-2 classification); this is a data-availability scope note, not a missed step. Ran `mask_and_recover` (T08 harness, reused verbatim — a cross-check assertion proves the driver's own replicated call sequence produces byte-identical numbers to calling `mask_and_recover` directly) with seed=42, `n_grid`/`holdout_frac` = T08 defaults (4 / 0.20), Phase-A `cfg=("spatial","statistical")` vs Phase-C `cfg=("spatial","ml","statistical")` swept across all 6 methods via `config.IMPUTE_ML_METHOD_BY_TARGET` override. **Re-run twice, byte-identical (determinism confirmed).**
  - **`year_built` (n_holdout=562). Phase-A: MAE 26.433 / RMSE 32.355 / KS 0.5089 / Wasserstein 26.210 / exact-vintage-bin 456/562 (81.1%).**
    - **`knn` BEATS Phase-A on every continuous metric:** MAE 25.141 (−1.29) / RMSE 31.909 (−0.45) / KS 0.3434 (−0.166, much better distributional fit) / Wasserstein 18.046 (−8.16); exact-bin 449/562 (79.9%, ~flat, slightly below A).
    - `missforest`/`rf`: worse MAE/RMSE (+5.1/+6.5) but better KS/Wasserstein (better distributional shape) and worse exact-bin (379–382/562) — a genuine trade-off, not a clean win.
    - `mice`/`linear`: **catastrophic blowup** (MAE 1161 / 903 respectively) — root-caused (not a code bug): both are globally-linear estimators (BayesianRidge/Ridge) fit on a pool spanning 3 geographically disjoint UTM-scale-different cities with only 4 numeric features (footprint/centroid_x/y/spatial-lag, no categorical — `use_class`/`archetype_id` absent from this schema); they extrapolate a spurious global linear coordinate→year trend and predict values like AD 5000+ on out-of-cluster coordinate combinations. **Confirms the CP-3a audit note directly: the T11.2 HistGBM/linear confidence fallback (global in-sample residual std, non-per-row) is non-discriminative — it stamped `ML_LINEAR_HIGH`/`ML_MICE_HIGH` on 100% of these catastrophically wrong fills, HIGH confidence never dropping to LOW.**
    - `histgbm`: floor not cleared (train ≈1797 < 5000) → 0/562 ml-fired, byte-identical to Phase-A (correct, documented fallback).
  - **`levels` (n_holdout=134). Phase-A: MAE 9.176 / RMSE 15.063 / KS 0.4701.**
    - `knn` fires on 117/134 (rest fall to spatial/statistical): MAE 8.388 (−0.79) / RMSE 12.982 (−2.08) / KS 0.4254 (better) — clear win.
    - `mice` fires MED-only on 13/134: small improvement (MAE −0.22/RMSE −0.34), no blowup at this smaller feature-count scale.
    - `missforest`/`rf`/`histgbm`/`linear`: floor not cleared (train ≈353 < 1000/5000) → 0/134 ml-fired, byte-identical to Phase-A — honest, documented below-floor fallback.
  - **Winner: `knn` is the only method that cleanly beats Phase-A on BOTH `year_built` and `levels`, on every continuous metric, with no catastrophic failure mode.** Used as "the winning config" for the EUI check below.
- **2. EUI do-no-harm.** Standalone pooled-fit vintage-bin check on the gate cell (nyc_centre, N=738): filled the REAL missing `year_built` gaps (not a synthetic holdout) on the full pool via Phase-A vs Phase-C(`knn`), sliced to nyc_centre, diffed the production `construction_sets.resolve_vintage` bin (reused verbatim, not reimplemented — provably a pure `pd.cut` no-op-donor path since both frames are fully filled). **Result: 168/738 rows diverge at the vintage-bin level (raw year_built differs on 542/738) — MATERIAL divergence, tripping the plan's own escalation trigger** ("a vintage-bin flip on ≥1 EUI-relevant building"). Confirmed at the full-production-path level: ran nyc_centre (reloaded fresh, native CRS, byte-identical geometry, `_INPUT_SCHEMA_COLUMNS` order preserved) with ONLY `year_built`/`provenance_year_built` spliced from the Phase-A vs Phase-C(`knn`) pooled fills through the REAL `step2_classify_enrich`(`enrich_semantics`) on the full 738-row cell for both branches — **common-mode confirmed: every enriched column except `vintage_standard` + 4 U-value columns (`u_roof/wall/window/floor_w_m2k`) is 100% identical between branches (archetype, geometry, HVAC selection, schedules, climate zone all untouched); 167/738 rows show EUI-relevant divergence** (1-row shift from the standalone check is a boundary-rounding artifact between the reprojected-pool computation and the natively-reloaded production path, not a discrepancy of concern).
  - **Escalated to a cluster A/B** (T09-CC sbatch machinery reused — the specific prior driver scripts no longer exist locally per a research check, but the generic infrastructure does: `scripts/cluster/submit_fleet.sbatch` unmodified, `scripts/validation/v12_cell_pipeline.step2_classify_enrich`/`step3_generate`, i.e. real `enrich_semantics`/`run_step3`, not reimplemented). Built 167 real IDFs per branch (334 total, 167/167 + 167/167 generation success) using the real cached NYC Central Park EPW (station 725053, `~/.openubem/epw/USA_NY_New.York-Central.Park...725053_TMYx...epw` — avoiding the exact Chicago-placeholder mistake the manager caught during the original T09-CC run). Packaged 2 fleets (`idfs/`, `weather/`, `fleet.lst`), shipped via `scp` to `/speed-scratch/o_iseri/openubem/fleets/t11cc_nyc_centre_{phaseA,phaseC}`, submitted 2 **standard-priority** sbatch arrays (no `--nice`/QOS bump — confirmed via `squeue` the queue was empty pre-submission and no other project's job was touched):
    - **Phase-A (baseline-imputed) branch: job `1064373`, `--array=1-167%32`.**
    - **Phase-C(`knn`-imputed) branch: job `1064406`, `--array=1-167%32`.**
    - `squeue` confirmed clean FIFO state post-submit: `1064373` 32/167 tasks RUNNING (rest PD on `JobArrayTaskLimit`, normal throttle), `1064406` PD on `AssocGrpCpuLimit` (queued behind `1064373`, same user, no priority tampering).
  - **NOT harvested — per the "no babysit" instruction, submitted + reported job IDs + STOPPED.** Harvest recipe for the manager: fetch `eplusout.{sql,err,end}` from `<fleet_dir>/out/<safe_osm_id>/` for both branches (`fleet.lst` identical between A/C → clean pairing by osm_id), parse `total_eui_kwh_m2`, feed to `eui_impact.py`'s `nmbe`/`cv_rmse` (gates \|NMBE\|<5%, CV(RMSE)<15%) — same math as the T09-CC CP-2 recipe, applied here to a Phase-A-fill-vs-Phase-C-fill comparison rather than observed-vs-recovered.
- Deviations: (a) reprojected the pooled 12-city frame to a common CRS (EPSG:5070) before running `mask_and_recover`/`_ml_tier` — not explicitly specified by the plan beyond "reproject to a common CRS or keep per-city," chose reprojection because the 3 cities sit in 3 different native UTM zones (32611/32614/32618) and raw-coordinate pooling would let the `spatial` tier's 100m-radius KNN silently cross-contaminate donors between geographically distant cities; (b) restricted the cluster A/B simulation batch to the 167 EUI-relevant-diverging buildings only (not all 738), mirroring the T09-CC precedent's "simulate the held-out block only" cost discipline — Stage-2 enrichment itself ran on the full 738-row cell for both branches so group-context/classification is unaffected, only the (already provably byte-identical-elsewhere) Stage-3 IDF build + cluster sim was subset; (c) could not literally reuse a T09-CC driver file (confirmed gone from `scratchpad/` by a research check) — rebuilt the fleet-prep driver from the surviving generic machinery (`submit_fleet.sbatch` + `v12_cell_pipeline` functions) instead of a turnkey script.
- Test status: n/a (evaluation run, not a pytest suite) — determinism proof = byte-identical leaderboard re-run (see run1/run2 log diff, empty).
- Notes: **CP-3 attribute-recovery condition MET** (`knn` beats Phase-A on both `year_built` and `levels`, all continuous metrics). **CP-3 EUI do-no-harm condition PENDING** — local field-diff showed material divergence (not "identical bins," so the no-cluster-needed shortcut did not apply), cluster A/B submitted (jobs 1064373/1064406) but not yet harvested. **CP-3 cannot be fully ratified until the manager harvests the two arrays and computes held-out NMBE/CV(RMSE).** Per kickoff instruction, hard-STOP here — no T11.7 work started, no ship decision made.

#### Manager — CP-3 AUDIT (T11.6): attribute-leg MET but MARGINAL/MIXED; EUI-leg harvest dispatched — 2026-07-03
- Artifacts audited: §8 T11.6 entry + the executor's leaderboard/field-diff/cluster-prep drivers under `scratchpad/`. Cluster jobs 1064373 (Phase-A) / 1064406 (Phase-C-knn) confirmed in-flight.
- **Verdict: STEP-0 clean (171/0). Attribute-recovery leg MET but I am recording it honestly as a MARGINAL, MIXED win, not a slam-dunk:** the winner is `knn` (not the flagship `missforest`, which does NOT beat Phase-A). On `year_built` `knn` improves raw-year MAE 26.4→25.1 (~4.9%) + distributional fidelity (KS −0.17, Wasserstein −8.2) but is **slightly WORSE on exact-vintage-bin recovery (456→449/562)** — and the vintage BIN, not raw year, is what drives downstream U-values/EUI, so the attribute win may not translate to any EUI movement (the pending A/B will show this). `levels` is a cleaner `knn` win (MAE 9.18→8.39, fires 117/134) but only clears the kNN≥200 floor on N=441. `use_class` not evaluable (absent from the Stage-1 23-col schema — honest scope note).
- **Valuable adverse finding, ratified: `mice`/`linear` catastrophically extrapolate** (MAE 903–1161, predicting AD 5000+) on the coordinate-pooled multi-city frame, AND the non-discriminative confidence fallback **stamps `ML_*_HIGH` on 100% of these garbage fills** — a real footgun that DIRECTLY CONFIRMS the CP-3a audit caveat (year_built cv-insensitivity → LOW-discard never protects). **T11.7 design inputs (for the user's ship decision):** (1) if shipped, the default `IMPUTE_ML_METHOD_BY_TARGET` must be `knn` (the only winner), NOT `missforest`; (2) `mice`/`linear` must be barred (or hard-bounded) for coordinate-pooled year_built; (3) an observed-range clamp on ML fills (like `impute_column`'s `bounds`) would neutralize the extrapolation footgun — worth scoping into T11.7.
- Deviations ratified: (a) EPSG:5070 pooling (sound — prevents cross-UTM 100m-KNN contamination); (b) 167-row EUI-relevant subset for the cluster sim (T09-CC cost-discipline precedent; Stage-2 enrichment ran full 738-row for both branches, common-mode proven — only `vintage_standard`+4 U-values differ); (c) driver reconstructed from surviving generic machinery (`submit_fleet.sbatch` + `v12_cell_pipeline`) since turnkey T09-CC scripts are gone locally — **I will verify the A/C osm_id pairing + NYC-EPW correctness at harvest** (the reconstruction is the one fan-out-critical risk here; the original T09-CC had a Chicago-placeholder-EPW defect I caught, so the harvester re-checks EPW station 725053 on both branches before trusting any number). Cluster hygiene confirmed: standard priority, empty queue pre-submit, no other project's job touched (memory rule honoured).
- Test status: STEP-0 suite 171 passed / 0 failed; leaderboard determinism byte-identical on re-run (seed 42).
- Notes: **EUI-leg harvest DISPATCHED to a Sonnet employee** (cluster jobs never harvested from the Opus manager session; login-node lightweight ops only; ≥30-min poll; metrics computed LOCALLY, never on the login node). CP-3 stays **PARTIALLY MET** (attribute ✓ / EUI pending) until the paired NMBE/CV(RMSE) lands within the 5%/15% do-no-harm gates. The ship decision + all T11.7 work remain the user's.

#### T11.6 EUI-leg — cluster harvest (Sonnet employee) — completed 2026-07-03
- **Jobs final state:** BOTH arrays fully **COMPLETED** — `sacct -j 1064373,1064406 -X` = 334/334 COMPLETED, 0 FAILED/CANCELLED/TIMEOUT. Per-branch success: Phase-A (`1064373`) **167/167** `EnergyPlus Completed Successfully` in `eplusout.end`, **0** `**FATAL**` in `eplusout.err`, 167/167 `eplusout.sql`+`eplustbl.htm` present; Phase-C-knn (`1064406`) **167/167** success, **0** FATAL, 167/167 outputs present. (1064406 waited out `AssocGrpCpuLimit` behind 1064373 as expected — no priority tampering, no other project's job touched.)
- **EPW/pairing verification: PASS (no placeholder defect).** Both branches' `weather/` hold the identical real NYC file `USA_NY_New.York-Central.Park...725053_TMYx.2011-2025.epw`; EPW header LOCATION line = station **725053, LAT 40.77889, LON −73.96917**; and — the load-bearing check the manager flagged after the T09-CC Chicago-placeholder defect — E+'s own `eplusout.eio` `Site:Location` record confirms E+ actually **consumed** it: `New.York-Central.Park...WMO#=725053, 40.78, −73.97`. Both branches' `fleet.lst` are **byte-identical in order** (167 osm_ids, same order → clean pairing by osm_id, `relation_3565283`…`way_702073638`).
- **Harvest method (LOCAL compute only):** streamed `eplustbl.htm`+`.end`+`.err`+`.mtr` (not the 3.8 GB/branch sql — only the small ABUPS report needed) as gzipped tars to local scratch (~9.8 MB each), parsed with `.venv` python: `total_eui_kwh_m2` = ABUPS **End Uses** 8 project rows (Heating, Cooling, Interior Lighting, Interior Equipment[incl. cooking gas], Fans, Pumps, Water Systems[DHW, incl. its district-heating column], Refrigeration) summed across energy cols → GJ×277.778 ÷ ABUPS **Total Building Area**. Area is **byte-identical A vs C** (max |Δarea| = 0.0000 m²) → confirms clean isolation (only `vintage_standard`+4 U-values differ, geometry/archetype/HVAC untouched, per the T11.6 common-mode proof). Paired A-vs-C by osm_id, fed to `openubem/validation/eui_impact.py::eui_impact_report`. 167/167 paired with valid EUI in both.
- **Paired do-no-harm result (Phase-A reference vs Phase-C-knn):**
  - **NMBE = −5.51 %** → **FAILS** the |NMBE| < 5 % gate (marginally over).
  - **CV(RMSE) = 7.93 %** → **PASSES** the CV(RMSE) < 15 % gate.
  - Cross-check vs E+ **Total Site Energy** EUI: NMBE −5.51 %, CV(RMSE) 7.93 % (matches the 8-row parse to 3 d.p. — exterior end-uses ≈ 0, parse is robust).
  - **All 167/167 buildings moved, every one DOWNWARD** (systematic bias, not scatter): mean EUI 149.87→141.61 kWh/m² (MBE −8.26 kWh/m²); ΔEUI min −35.26 / median −7.17 / max −0.20 kWh/m²; Δ% min −15.85 / median −5.86 / max −0.11; abs-Δ% mean 5.65, p90 13.24, max 15.85. Top movers −14…−16 % (e.g. `way_319773436` 204.7→172.3, −15.85 %).
- **Interpretation (factual, no ship decision):** `knn`-imputed `year_built` assigns systematically **newer/better vintages** than the Phase-A baseline spatial-imputer, lowering heating-dominated EUI across the whole cell. The shift is one-directional and just clears the CV(RMSE) tolerance but **breaches the |NMBE|<5 % do-no-harm bound by 0.51 pp**.
- Test status: harvest is report-only (no code/tests changed); `eui_impact_report` used verbatim. Paired CSV at `scratchpad/t11cc_harvest/paired_eui.csv`.
- **One-line condition statement: EUI do-no-harm is NOT fully MET — Phase-C(`knn`) does not worsen EUI *scatter* (CV(RMSE) 7.93 % < 15 % PASS) but introduces a systematic −5.5 % EUI *bias* vs the validated Phase-A baseline (NMBE −5.51 % breaches the <5 % gate).** Ship/accept decision + T11.7 remain the user's.

#### Manager — CP-3 AUDIT (EUI-leg): harvest verified clean; **CP-3 NOT fully MET** — 2026-07-03
- **Harvest audited, not trusted (reconstructed driver was the fan-out-critical risk):** (1) **Real EPW confirmed the deep way** — not just the fleet `weather/` file but E+'s own `eplusout.eio` `Site:Location` = `WMO# 725053, 40.78, −73.97`, i.e. EnergyPlus actually *consumed* real NYC Central Park (the exact check that catches the old T09-CC Chicago-placeholder class of defect). (2) **Clean isolation** — both `fleet.lst`s byte-identical in order + floor areas byte-identical A-vs-C (max |Δ| = 0.0000 m²) ⟹ the EUI delta is purely the vintage/U-value imputation effect, nothing else moved. (3) **334/334 COMPLETED, 0 FATAL, 167/167 per branch.** (4) Total-Site-Energy cross-check matches the 8-row ABUPS parse to 3 d.p. Result is trustworthy.
- **VERDICT: CP-3 NOT fully MET.** Attribute-recovery leg = MET but MARGINAL/MIXED (winner `knn` only; flagship `missforest` loses; `mice`/`linear` dangerous). EUI do-no-harm leg = **FAILS** — `knn` shifts all 167/167 nyc_centre buildings DOWNWARD (systematic −5.51 % NMBE bias, breaching the <5 % gate by 0.51 pp; CV(RMSE) 7.93 % passes). The **shape** of the miss matters more than the 0.51 pp: it is a one-directional bias, not scatter — `knn`'s neighbour-averaging regresses vintages toward the denser/newer urban-core stock, and since Phase-A is CP-2-validated as near-perfect vs *observed* EUI (nyc_centre +0.49 %), a −5.5 % departure from Phase-A = −5.5 % away from ground truth = harm by the gate's definition. The mechanism is real and explainable (not a bug).
- **Manager recommendation to the user (decision is theirs — T11.7): keep the ML tier BUILT-BUT-OFF; do not wire it into the default pipeline.** Even the single best method fails do-no-harm with a systematic city-wide bias — the more concerning failure mode for a UBEM. The capability, six-method leaderboard, `mice`/`linear` footgun, and this EUI result are all preserved for a future revisit (candidate fix: observed-range / vintage-bin clamp on ML fills to kill the newer-skew, per the T11.7 design inputs). Holding the do-no-harm line keeps the whole validation credible (zero-fitted-params culture — don't move the goalposts to pass).
- **Arc state:** CP-3 CLOSED as NOT-MET (attribute-marginal / EUI-fail). Phase C stays opt-in, `ml` ∉ default tiers; committed baseline untouched. **T11.7 (ship wiring) is NOT unblocked** — it was gated on CP-3 PASS. Awaiting user's call on whether to (a) accept built-but-off, or (b) authorize a clamp-and-retry before any ship consideration.

#### Manager — USER DECISION: accept built-but-off ("keep it") — 2026-07-03
- **User ruling (2026-07-03):** *"one method does not need to cover all input parameters, no worries, keep it."* ⟹ **accept the ML tier BUILT-BUT-OFF (opt-in), no clamp-retry, no retirement.** Arc PARKED, not shipped-to-default.
- **Framing the user surfaced (and the architecture already honours):** the estimator registry is **per-target** (`config.IMPUTE_ML_METHOD_BY_TARGET`), so ML need not be one global method — each parameter selects its own imputer. The CP-3 do-no-harm miss was specifically `knn`-on-`year_built` (the EUI-relevant target) on real NYC stock; it does not condemn the tier for other parameters/targets a future user may point it at. Keeping it opt-in preserves that flexibility at zero cost to the default pipeline.
- **No further Phase-C engineering.** `ml` remains outside `IMPUTE_ENABLED_TIERS`; committed baseline untouched; T11.7 production wiring stays USER-SIGN-OFF-only and is NOT being pursued. Candidate future revisit (if ever shipped for `year_built`): observed-range / vintage-bin clamp to neutralise the newer-skew, then re-run the A/B — documented, not scheduled.
