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
> **Last updated:** 2026-07-14 (**RE-OPENED (scoped) 2026-07-14 on user go — the §9.2 "knn newer-skew de-bias" backlog item is now the executable task T11.8.** Prior state preserved: CP-3 CLOSED NOT-fully-MET (attribute-leg marginal `knn` win, EUI-leg fails do-no-harm −5.51 % NMBE), ML tier opt-in/off, `T11.7` WILL-NOT-PURSUE. T11.8 adds a **reusable, opt-in, zero-fitted-params newer-skew de-bias corrector** (stratified quantile-mapping) whose whole purpose is to flip the failed EUI do-no-harm leg without regressing attribute-recovery; it is re-gated at **CP-3b**. Default pipeline stays byte-identical until/unless CP-3b passes AND the user signs off. Everything before T11.8 remains as the 2026-07-03 user ruling left it.)

- [x] **T11.1** — `build_ml_imputer` core + 6-method estimator registry (complete-case fit, per-target floors)
- [x] **T11.2** — dispersion→confidence per method family + `ML_<METHOD>_<TIER>` tokens (**ratified into parent §5G 2026-07-03**)
- [x] **T11.3** — wire `_ml_tier` to the tier contract + reorder `_CANONICAL_TIER_ORDER` (ml before statistical) + opt-in config
- [x] **T11.4** — reconcile `impute_column` to §3E `method='auto'` + `model_path` (close §5A drift); KDE/PDE byte-identical
- [x] **T11.5** — joblib persistence + frozen-reload determinism (all methods)
- [x] **CP-3a** *(stop-checkpoint)* — **MET 2026-07-03** — imputer built, wired, `test_ml_imputer.py` 40/40 green, no-ML path byte-identical, matrix-family feature-dependence VERIFIED by manager probe (not mean-fill)
- [x] **T11.6** — CP-3 gate: pooled mask-and-recover leaderboard (all 6 methods vs Phase-A) + EUI do-no-harm — **EXECUTED 2026-07-03**: leaderboard done (winner = `knn`, beats Phase-A on `year_built` + `levels`); local field-diff found material vintage-bin divergence (168/738 nyc_centre) → escalated to cluster A/B, jobs **1064373** (Phase-A) / **1064406** (Phase-C/knn) submitted standard-priority, **NOT harvested** (no-babysit stop)
- [x] **CP-3** *(gate)* — **CLOSED, NOT fully MET (2026-07-03, manager-audited).** Attribute-recovery condition MET-but-marginal (winner `knn`); **EUI do-no-harm condition FAILS** — jobs 1064373/1064406 harvested clean (EPW 725053 confirmed via `.eio`, 167/167 both branches, byte-identical footprints), paired **NMBE −5.51 % (breaches <5 %), CV(RMSE) 7.93 % (passes)**; all 167 buildings shift downward (systematic bias). ML does NOT clear the ship bar as-is.
- [x] **T11.7** — **RESOLVED as WILL-NOT-PURSUE 2026-07-03.** Was gated on a CP-3 PASS (USER-SIGN-OFF only); CP-3 did not pass and the user accepted built-but-off ("keep it"), so ship wiring + `enrich_semantics` byte-identity reconcile are **not pursued**. `ml` stays outside `IMPUTE_ENABLED_TIERS`; committed baseline untouched. Candidate future revisit (documented, not scheduled): observed-range/vintage-bin clamp then re-run the A/B.
- [x] **T11.8** — **reusable newer-skew de-bias corrector (stratified quantile-mapping) + local skew proof** — **BUILT 2026-07-14**, `test_debias.py` 12/12, full suite 190/0, no-debias path byte-identical. Corrector unit-proven on synthetic strata; **structural no-op on the real fixture** (stratifier columns absent).
- [x] **T11.8b** — **global (unstratified) qmap fallback in `_ml_tier`** — **BUILT 2026-07-14** (192/0). **Re-proof: skew WORSENED (+0.4593→+0.6016, −31 %) + attribute-recovery regressed below Phase-A** — global donor pool is LA-dominated (wrong, non-local reference for nyc_centre). Corrector kept built-but-inert; no cluster spend.
- [x] **CP-3b-local** *(stop-checkpoint)* — **NOT MET under either de-bias variant (2026-07-14).** Manager reframe: the −5.5 % is a **pooled-eval granularity artifact** — knn needs pooling to clear its ≥200 fit floor (nyc_centre alone = 158 obs), but production imputes **per-cell**, where knn-year_built never fires on nyc_centre at all. De-bias line **set aside**; replaced by a production-granularity validity diagnostic (below).
- [x] **T11.8c-diag** — **per-cell (production-granularity) raw-knn vs Phase-A do-no-harm diagnostic on a floor-clearing cell (la_suburban)** — **EXECUTED 2026-07-14** (`la_urban` also run). knn fires per-cell (29/48 + 4/76 field-fill; 202/260 + 74/113 holdout). Directional vintage-bin gap = **+0.0000 on both cells** (zero skew, vs pooled nyc_centre's +0.4593). Attribute-recovery ties Phase-A on `la_suburban` (exact-bin 247/260 both) and shows one isolated regression on `la_urban` (exact-bin 96/113 vs 100/113; every other metric on that cell favors knn). Hard-STOPPED for manager decision.
- [x] **T11.8-EUI** — cluster A/B re-gate — **WITHDRAWN as unnecessary (2026-07-14).** The per-cell diagnostic shows **0/1343 + 0/618 vintage-bins diverge** vs Phase-A → identical U-values → identical EUI by construction; a cluster A/B would confirm NMBE≈0 by foregone conclusion. No cluster spend warranted.
- [x] **CP-3b** *(gate)* — **CLOSED, RESOLVED (2026-07-14, manager terminal decision).** The CP-3 −5.51 % NMBE is now understood as a **pooled-eval granularity artifact**, not a production do-no-harm failure: at production (per-cell) granularity raw knn is EUI-indistinguishable from Phase-A (0 vintage-bin divergence) — do-no-harm **but also do-no-good**. **ml tier stays built-but-off / opt-in** (unchanged from the 2026-07-03 user ruling) — kept off because it is EUI-neutral (zero benefit to justify adding ML to the default), NOT because it harms. De-bias corrector (T11.8/T11.8b) kept built + opt-in + byte-identical-off, documented as unnecessary at production granularity. **Whole de-bias/CP-3b line CLOSED.**

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
│   ├── imputation.py    (MODIFY — T11.1 build_ml_imputer + registry; T11.2 confidence/tokens;
│   │                              T11.3 _ml_tier wiring + _CANONICAL_TIER_ORDER; T11.4 impute_column auto/model_path;
│   │                              T11.8: opt-in de-bias hook inside _ml_tier — no-op when disabled)
│   └── debias.py        (NEW — T11.8: reusable, tier-agnostic newer-skew corrector — stratified quantile-mapping;
│                                pure functions over Series, zero-fitted-params, no EUI, no side effects)
└── config.py            (MODIFY — T11.3: ML opt-in surface; T11.8: IMPUTE_DEBIAS_NEWERSKEW per-target flag, default all-False)

tests/
├── test_ml_imputer.py   (NEW — T11: all sub-tasks; the parent §3 file layout already reserves this file)
└── test_debias.py       (NEW — T11.8: qmap marginal-match, rank-preservation, thin-stratum skip, determinism,
                                  no-op-when-disabled byte-identity, zero-EUI structural guard)

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

### T11.8 — reusable newer-skew de-bias corrector (stratified quantile-mapping) + local skew proof

> **Why this exists.** CP-3's EUI do-no-harm leg failed at **NMBE −5.51 %** because the winning method
> `knn` neighbour-averages `year_built` toward the denser/**newer** urban-core stock — a one-directional
> systematic bias (all 167/167 nyc_centre buildings shifted downward), *not* scatter (CV(RMSE) 7.93 %
> passed). The §9.2 clamp does **not** touch this: `knn` predicts strictly *within* the observed range, so
> an observed-range clip is a no-op for it. The genuine fix is to correct the **shape** of the imputed
> marginal, which is what this task builds.

- **What:** A new module `openubem/semantic/debias.py` exposing a **pure, tier-agnostic** corrector:
  - `debias_newer_skew(raw_fills: pd.Series, observed_donors: pd.Series, *, rng, min_donors=30) -> pd.Series`
    — empirical **quantile-mapping**: for each raw fill `f`, compute its rank within the raw-fill set
    (`ECDF_fills(f)`) and return the same quantile of the observed-donor distribution
    (`Quantile_observed(ECDF_fills(f))`), linear interpolation. This transports the fills onto the observed
    marginal while **preserving the neighbour vote's rank order** (the signal `knn` *did* capture) and
    simultaneously undoes both the newer-shift and the variance-compression of averaging.
  - `debias_stratified(raw_fills, observed_donors, strata: pd.Series, *, rng, min_donors=30) -> pd.Series`
    — applies `debias_newer_skew` **within each stratum** (the same stratifier the fill used:
    `use_class` if present, else `archetype_id`). A stratum with `< min_donors` observed donors is
    **skipped** (raw fill kept unchanged) — never fabricate a transform from a handful of points.
  Then an **opt-in hook in `_ml_tier`** (`imputation.py`): when `config.IMPUTE_DEBIAS_NEWERSKEW.get(attr)`
  is truthy AND the tier is `knn` (the only target the flag ships for), pass the raw per-row ML fills through
  `debias_stratified` **before** re-binning / confidence / token-stamping. Provenance: the corrected row
  keeps its `ML_KNN_<TIER>` token **and** additionally appends a `DEBIAS_NEWERSKEW_QMAP` flag to
  `data_quality_flag`; a skipped-thin-stratum row appends `DEBIAS_SKIPPED_THINSTRATUM`. **Add
  `config.IMPUTE_DEBIAS_NEWERSKEW: dict[str,bool]` defaulting to all-False** (so every existing run,
  including opt-in-`ml` runs that do not set the flag, is byte-identical).
- **Why:** §9.2 backlog "knn newer-skew de-bias" — the actual blocker to a shippable ML tier. Quantile
  mapping is the standard **zero-fitted-params** distribution bias-correction (determined entirely by two
  empirical CDFs of *observed* data — no free parameter, nothing reads EUI). It enforces the same
  **MAR-within-stratum** assumption the whole Phase-A statistical tier already relies on (group-mode /
  group-median), applied to the ML fills that violated it — so it adds no new epistemic risk; the CP-3b A/B
  is what proves it actually helps.
- **How:**
  - **Zero-fitted-params / determinism (hard).** No parameter, `min_donors` floor, or interpolation
    convention may be selected against EUI. `min_donors=30` is a **fixed convention, never swept**. All
    tie-breaks/interp through `np.random.default_rng(config.RANDOM_SEED)`; fixed linear quantile interp.
    Mirror `test_ml_imputer.py::TestNoEUILeakage` with a structural `__code__.co_names` test proving
    `debias.py` never references an EUI column.
  - **Additive & opt-in (hard).** Default `IMPUTE_DEBIAS_NEWERSKEW` all-False ⇒ `_ml_tier` behaviour is
    byte-identical to today for every run (prove with an assertion: opt-in-`ml` run with the flag unset ≡
    pre-T11.8). `enrich_semantics` / default `IMPUTE_ENABLED_TIERS` **untouched** (parent CP-1 intact).
  - **Operate on raw year, then re-bin.** Correct the continuous `year_built`, then bin via the existing
    `_YEAR_BINS`/`_YEAR_LABELS` — the vintage **bin** is what drives U-values/EUI.
  - **Expected tension, stated up front:** quantile-mapping matches the *marginal*, so it may *raise*
    per-row MAE while improving KS/Wasserstein and killing the EUI bias. That trade is acceptable — CP-3b's
    ship-blocker is EUI do-no-harm; attribute-recovery need only **not fall below Phase-A**.
  - **Method pivot needs a manager STOP, not a silent switch.** Quantile-mapping is the **pinned** method.
    If the CP-3b-local proof shows it (a) does **not** materially reduce the newer-skew, or (b) drops
    `year_built` attribute-recovery **below the Phase-A baseline**, **STOP and report** — do not silently
    substitute a moment-matching (mean-shift + variance-restore) fallback; the manager rules on the pivot.
  - **Local proof (this is the CP-3b-local deliverable, no cluster).** Re-use the T11.6 machinery
    (`scratchpad/` throwaway, report-only): (1) pooled `mask_and_recover` — de-biased-`knn` vs raw-`knn` vs
    Phase-A on `year_built`/`levels` (MAE/RMSE/KS + exact-bin), same seed 42 / same holdout; (2) the
    nyc_centre pooled-fit **vintage-bin field-diff** (the exact T11.6 §2 local check): report how the
    per-bin distribution and the mean directional vintage-bin gap vs Phase-A move — **the newer-skew
    collapsing toward 0 is the go/no-go signal** for the cluster leg.
- **How to test:** `tests/test_debias.py` — (a) `debias_newer_skew` output marginal matches the observed
  donor marginal (KS ≈ 0 on a hand-built frame) while Spearman rank vs the raw fills ≈ 1 (rank preserved);
  (b) a newer-skewed synthetic fill set (fills drawn ~2010, donors ~1960–2010) is pulled older after
  correction (mean moves toward the donor mean); (c) a stratum with `< min_donors` donors is returned
  unchanged + tagged `DEBIAS_SKIPPED_THINSTRATUM`; (d) determinism — same seed ⇒ byte-identical corrected
  Series; (e) **no-op byte-identity** — `impute_missing` with `ml` opt-in but `IMPUTE_DEBIAS_NEWERSKEW`
  unset equals the pre-T11.8 result; (f) structural no-EUI guard on `debias.py`. Plus: the full CP-1 gate
  suite + `test_ml_imputer.py` + `test_mask_recover.py` stay green **unchanged**.
- **New tokens for manager ratification (record in the §8 progress-log entry; do NOT edit parent §5G
  directly):** `DEBIAS_NEWERSKEW_QMAP` (flag, no confidence tier — rides alongside the `ML_KNN_<TIER>`
  token to mark a corrected value) and `DEBIAS_SKIPPED_THINSTRATUM` (flag — correction declined, raw ML
  fill kept). The manager adds the parent §5G rows on ratification.

### T11.8b — global (unstratified) qmap fallback in `_ml_tier` (manager pivot, 2026-07-14)

- **What to do.** In `_ml_tier` (imputation.py — the SAME single file-scope touch as T11.8, no new files),
  add a **global fallback branch** to the existing de-bias hook: when the flag is enabled + `method == "knn"`
  but **no stratifier column** (`use_class`/`archetype_id`) is present, instead of the current no-op, apply
  the **already-built, already-unit-tested** `debias.debias_newer_skew(preds, observed_donors, rng=rng)`
  primitive **globally** (one pool, no strata) onto the full observed-donor marginal. Tag the corrected rows
  with a NEW flag `DEBIAS_NEWERSKEW_QMAP_GLOBAL` (distinct from the stratified `DEBIAS_NEWERSKEW_QMAP`) so the
  two regimes stay queryable-apart. Then **re-run the CP-3b-local proof** (the same two throwaway scratchpad
  drivers T11.8 already built) and report whether the −5.5 % directional vintage-bin gap now collapses.
- **Why.** CP-3b-local's 1st proof (§8) showed the stratified hook structurally no-ops on the real Stage-1
  `01_buildings.gpkg` (no `use_class`/`archetype_id`). But the failure being fixed — CP-3's −5.51 % NMBE — is
  a **global one-directional marginal shift** (all 167/167 nyc_centre buildings moved DOWN; knn's whole
  `year_built` marginal pulled newer). A global quantile-map transports that shifted marginal straight back
  onto the observed-donor marginal, targeting the exact failure mode **without** needing any stratifier.
  This is **not a method pivot** (still empirical quantile-mapping — global = a single all-inclusive stratum),
  so it stays inside the T11.8 pinned method; the manager is authorizing a *stratification-granularity
  fallback*, not a switch to moment-matching. It reuses the tested primitive (zero new method risk), needs
  **no** upstream Stage-2 pre-classification (rejected: archetype needs `year_built` — the very thing being
  imputed — and `use_class` is unreliable on dense already-mapped stock per Phase-D CP-4).
- **How.** The `strat_col is None` path in `_ml_tier` (imputation.py:741-745) currently falls through and
  leaves `preds` untouched. Extend it: `strat_col is not None` → `debias_stratified` (unchanged T11.8 path,
  tag `_QMAP`/`_SKIPPED_THINSTRATUM`); `strat_col is None` **AND** `observed_donors` clears `min_donors=30`
  → `debias_newer_skew(preds, observed_donors, rng=rng)` globally, tag every corrected row `_QMAP_GLOBAL`;
  `strat_col is None` AND donors `<min_donors` → keep the current no-op. Same in-place `data_quality_flag`
  mutation mechanism T11.8 already established (do NOT re-architect the tier-handler contract — that stays a
  separate manager decision if/when this ships). `observed_donors = gdf.loc[gdf[attr].notna(), attr]` exactly
  as the stratified path builds it. **Zero-fitted-params preserved** — global qmap is still two empirical
  CDFs of OBSERVED data; nothing reads EUI (the `__code__.co_names` guard already covers `debias_newer_skew`).
- **Expected tension (flagged, not a blocker).** Global qmap forces the imputed marginal onto the *observed*
  marginal — valid under MAR. If missingness is MNAR (genuinely-newer buildings missing), it could
  over-correct. **This is precisely what the re-run CP-3b-local field-diff TESTS**: does the directional gap
  collapse toward 0 (good) or overshoot past 0 to a + gap (over-correction)? Either way the cluster spend
  stays gated behind the local proof. Per-row MAE may rise while the marginal/EUI improves — acceptable
  (same tension already ratified for T11.8; EUI do-no-harm is the ship-blocker, attribute-recovery need only
  not fall below Phase-A).
- **How to test.** (a) Extend `tests/test_debias.py` with a `_ml_tier`-level test: enabled + `knn` + **no**
  `use_class`/`archetype_id` column present → `debias_newer_skew` is invoked once globally and corrected rows
  carry `DEBIAS_NEWERSKEW_QMAP_GLOBAL`; (b) default-off (`IMPUTE_DEBIAS_NEWERSKEW` unset) still never enters
  the block — byte-identical to pre-T11.8 (re-assert the existing spy test still passes); (c) global-donors
  `<min_donors` → no-op, no flag; (d) full suite (CP-1 gate + `test_ml_imputer` + `test_mask_recover` +
  `test_debias`) stays green-unchanged. **Then the CP-3b-local re-proof** (report-only, scratchpad, NO
  cluster): re-run `t11_8_cp3b_local_field_diff.py` + `_leaderboard.py` and report the new directional
  vintage-bin gap vs Phase-A (was +0.4593) and `year_built` attribute-recovery vs Phase-A.

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
- **CP-3b-local — after T11.8's local proof (no cluster).** De-bias module unit-green; no-debias path
  byte-identical; the nyc_centre vintage-bin field-diff shows the −5.5 % newer-skew **materially collapses**
  (directional vintage-bin gap vs Phase-A → ≈0) *without* dropping `year_built` attribute-recovery below
  Phase-A. Executor appends §8 entries and **STOPS** for manager audit before the cluster leg is authorized.
  If the skew does **not** collapse (or attribute-recovery regresses below Phase-A), STOP and report — the
  method pivot is the manager's call, not a silent switch.
- **CP-3b — after T11.8-EUI (the cluster re-gate).** Ships `knn`+de-bias for `year_built` into a per-target
  default **only if** the paired cluster A/B now clears |NMBE|<5 % ∧ CV(RMSE)<15 % **and** attribute-recovery
  did not regress below Phase-A. Otherwise the tier stays built-but-off (de-bias preserved as opt-in). Any
  default-run change remains **user-sign-off** (inherits the T11.7 gate).

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

#### Manager — Phase-C RESULTS doc + explanatory figures — 2026-07-13
- Artifacts: `results/phase_C/RESULTS_phaseC.md` (NEW — self-contained results doc, symmetric to `phase_A/RESULTS_phaseA.md` + `phase_B/RESULTS_phaseB.md`, all values verbatim from this §8 log) + 4 embedded PNGs written ONLY to `results/phase_C/` (per the user's standing "figures live only in the results folder" constraint — not `openubem/outputs/`): `phaseC_cp3_verdict.png`, `phaseC_leaderboard.png`, `phaseC_eui_donoharm.png`, `phaseC_footgun.png`. Figure generator (throwaway): `scratchpad/make_phaseC_figures.py`.
- Deviations: none — documentation only, NO code/engineering. Arc stays CLOSED / built-but-off exactly as the 2026-07-03 user ruling left it; no re-open, no clamp-retry, no ship wiring. User request 2026-07-13 was explicitly "document the results like phases A/B" (clarified via AskUserQuestion, since the Phase-C code was already fully executed + closed).
- Test status: n/a (no code touched). Figures render from the recorded CP-3 numbers (leaderboard `knn` win, EUI NMBE −5.51% / CV(RMSE) 7.93%, mice/linear footgun).
- Notes: `results/` now holds three symmetric self-contained phase folders — `phase_A/` (safe, CP-1), `phase_B/` (accurate, CP-2), `phase_C/` (ML built-but-off, CP-3 not fully met). Figures generated by a dispatched Sonnet employee; manager to verify the 4 PNGs on completion.

#### Manager — T11.8 authored + Phase-C scoped RE-OPEN — 2026-07-14
- Artifacts: this plan — §0 status line + 4 new checklist rows (T11.8 / CP-3b-local / T11.8-EUI / CP-3b), §3 file layout (`semantic/debias.py`, `tests/test_debias.py`, `_ml_tier` hook, `config.IMPUTE_DEBIAS_NEWERSKEW`), §6 T11.8 task, §7 CP-3b-local + CP-3b checkpoints. Parent plan §9.2 pointer updated to reference T11.8.
- Deviations: none (planning only). Scope set by user 2026-07-14 ("attaque le design du de-bias newer-skew ... correcteur réutilisable oui"): a **reusable, tier-agnostic** corrector, not a `knn`-only patch.
- **Load-bearing design pinned** (so the executor does not re-debate): (1) method = **stratified empirical quantile-mapping** — transports raw neighbour-averaged fills onto the observed-donor marginal *within stratum*, rank-preserving; corrects both the newer-shift and the variance-compression; **zero-fitted-params** (two empirical CDFs of observed data, nothing reads EUI). (2) Reusable primitive in a **new `debias.py`**, pure functions over Series, consumed by `_ml_tier` via an **opt-in `IMPUTE_DEBIAS_NEWERSKEW` flag defaulting all-False** ⇒ every existing run (incl. opt-in-`ml`) byte-identical, Phase-A / CP-1 / CP-2 untouched. (3) `min_donors=30` thin-stratum skip, fixed convention never swept. (4) Provenance: corrected value keeps `ML_KNN_<TIER>` + a queryable `DEBIAS_NEWERSKEW_QMAP` flag (or `DEBIAS_SKIPPED_THINSTRATUM` when declined) — tokens manager-ratified into parent §5G on report. (5) **Local proof gates the cluster spend** — CP-3b-local requires the nyc_centre vintage-bin field-diff to show the −5.5 % skew collapsing toward 0 *before* any A/B is submitted (the §9.2 note that a clamped-`knn` re-A/B would just re-confirm −5.51 % is exactly the cluster-waste this checkpoint prevents). (6) Quantile-mapping is the **pinned** method; a method pivot to moment-matching is a manager STOP, never a silent switch. Expected tension flagged: qmap may raise per-row MAE while fixing the marginal/EUI — acceptable, EUI do-no-harm is the ship-blocker, attribute-recovery need only not fall below Phase-A.
- Test status: n/a (plan doc).
- Notes: **DISPATCHING a fresh Sonnet executor scoped T11.8 → hard-STOP at CP-3b-local.** The cluster leg (T11.8-EUI) is explicitly withheld until the manager audits the local skew-collapse proof. Cross-referenced into parent `PLAN_input_imputation_implementation.md` §9.2.

#### T11.8 — reusable newer-skew de-bias corrector (stratified quantile-mapping) — completed 2026-07-14
- Artifacts: `openubem/semantic/debias.py` (NEW — `debias_newer_skew`, `debias_stratified`, `_thin_strata`); `openubem/semantic/imputation.py` (MODIFY — `_ml_tier` opt-in hook only, per plan §3 file-scope; `_DEBIAS_NEWERSKEW_QMAP`/`_DEBIAS_SKIPPED_THINSTRATUM` module constants); `openubem/config.py` (MODIFY — `IMPUTE_DEBIAS_NEWERSKEW: dict` all-False default for `year_built`/`levels`/`height`/`height_m`/`use_class`); `tests/test_debias.py` (NEW — 12 tests covering the (a)-(f) "How to test" list); `scratchpad/t11_8_cp3b_local_leaderboard.py` + `scratchpad/t11_8_cp3b_local_field_diff.py` (NEW, throwaway — CP-3b-local proof drivers, reuse `t11_cp3_leaderboard.py`'s `load_pooled`/`run_one`/`exact_bin_recovery` verbatim).
- **Method exactly as pinned:** `debias_newer_skew(raw_fills, observed_donors, *, rng, min_donors=30)` — rank each raw fill within the raw-fill set (`pandas.rank(method="average", pct=True)`, deterministic average tie-break, no free/random component) and linearly interpolate (`np.interp`) that percentile onto the sorted observed-donor array. `debias_stratified` applies this per-stratum (stratifier = `use_class` if present else `archetype_id`, resolved inside `_ml_tier` exactly mirroring `construction_sets.resolve_vintage`'s own stratifier-selection precedent); a stratum with `<min_donors` observed donors is skipped (raw fill kept). `rng` is accepted (API symmetry with every other tier handler / the project's determinism convention) but not consumed — the transform has no random component, so it is deterministic by construction, not merely "seeded."
- **`_ml_tier` hook (imputation.py, the ONLY file-scope touch per plan §3):** fires only when `not imputer.is_classifier and method == "knn"` and `config.IMPUTE_DEBIAS_NEWERSKEW.get(attr)` is truthy and a stratifier column is present; replaces `preds` with the `debias_stratified` output BEFORE the confidence/token/fill loop, so `ML_KNN_<TIER>` provenance and HIGH/MED-only acceptance are completely unaffected. **Deviation (flagging for manager awareness, not a plan violation):** rule 4 requires the corrected row to *also* carry a `DEBIAS_NEWERSKEW_QMAP` (or `DEBIAS_SKIPPED_THINSTRATUM`) flag on `data_quality_flag`, but the shared `(value, token)` tier-handler contract (imputation.py §5-D, used by every tier) has no channel for a tier handler to emit a SECOND, independent flag. Resolved by having `_ml_tier` mutate `gdf["data_quality_flag"]` **in place** for filled+tagged rows only, using `provenance.append_flag_token` (idempotent `|`-append) directly on the SAME `gdf` object `impute_missing` holds as `out` (Python passes the DataFrame by reference; `impute_missing`'s own later `out = prov.append_flag(out, tok_value, ...)` call takes `.copy()` of whatever is already on `out`, so the in-place edit survives correctly into the final frame). This is a new pattern for this codebase (every other tier handler is read-only on `gdf`) — confirmed safe (no other tier reads `data_quality_flag` for routing decisions) and confirmed byte-identical for the default-off path (see test below), but flagging explicitly since it departs from the established read-only-handler convention and the manager may prefer a different mechanism if/when this ships.
- **New tokens for manager ratification (plan §6 T11.8, not yet added to parent §5G):** `DEBIAS_NEWERSKEW_QMAP` (flag, rides on `data_quality_flag` alongside `ML_KNN_<TIER>` — no independent confidence tier) and `DEBIAS_SKIPPED_THINSTRATUM` (flag — correction declined, raw ML fill kept unchanged).
- **Zero-fitted-params / determinism:** `tests/test_debias.py::TestNoEUILeakage` mirrors `test_ml_imputer.py::TestNoEUILeakage`'s `__code__.co_names` structural inspection over `debias_newer_skew`/`debias_stratified`/`_thin_strata` — no EUI-like name anywhere in the call graph. `min_donors=30` is a literal, uncommented default parameter, never read from config, never swept. `TestDeterminism` proves the output is identical regardless of which `rng` (or `None`) is passed — the strongest form of the determinism requirement (not just "same seed", but "no dependency on `rng` at all").
- **Additive & opt-in:** `TestMlTierDebiasHook::test_disabled_by_default_never_calls_debias` monkeypatches `debias.debias_stratified` with a call-counting spy and asserts it is **never invoked** when `config.IMPUTE_DEBIAS_NEWERSKEW` is left at its shipped all-False default (even with `ml`/`knn` opt-in enabled) — proves the conditional block is never entered, so `_ml_tier`'s control flow (and therefore its output) is byte-identical to pre-T11.8 for every existing run. `TestImputeMissingDefaultOff` adds a second, public-API-level determinism cross-check via `impute_missing` directly.
- Test status: `tests/test_debias.py` **12/12 passed**. Full combined suite `pytest tests/test_ml_imputer.py tests/test_imputation.py tests/test_imputation_routing.py tests/test_mask_recover.py tests/test_tierB_provenance.py tests/test_vintage_donor.py tests/test_levels_groupwise.py tests/test_spatial_impute.py tests/test_provenance.py tests/test_debias.py -q` → **190 passed, 0 failed** in 81.06s (CP-1 gate + `test_ml_imputer.py` + `test_mask_recover.py` all green-unchanged; the T11.8 addition introduces zero regressions).
- Deviations: (a) the in-place-mutation mechanism above (necessitated by the tier-handler contract's `(value, token)` shape — no other way to add a second, independent flag while touching only `_ml_tier`); (b) no others — method, signatures, `min_donors=30`, stratifier selection, and provenance token strings are exactly as pinned in plan §6 T11.8.

#### CP-3b-local — proof executed: skew does NOT collapse on the real evaluation dataset — 2026-07-14
- Artifacts: `scratchpad/t11_8_cp3b_local_leaderboard.py` + `scratchpad/t11_8_cp3b_local_leaderboard_results.json` (pooled mask-and-recover: Phase-A vs raw-knn vs de-biased-knn, `year_built`+`levels`, seed 42, T08-default holdout — reuses `t11_cp3_leaderboard.run_one`/`exact_bin_recovery` verbatim); `scratchpad/t11_8_cp3b_local_field_diff.py` (nyc_centre pooled-fit vintage-bin field-diff, mirrors `t11_cp3_eui_field_diff.py`'s exact local-check method, extended with a signed mean-bin-rank "directional gap" metric).
- **Finding (both scripts agree, run 2026-07-14):** the de-bias hook **never fires** on the real pooled 12-cell evaluation dataset (`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg`, n=8160). Confirmed by direct column inspection (`use_class` in columns: **False**; `archetype_id` in columns: **False** — the Stage-1 `01_buildings.gpkg` schema, pre-classification, has neither) AND numerically: raw-knn vs de-biased-knn predictions are **byte-identical on every one of the 562 `year_built` holdout rows and every one of the 134 `levels` holdout rows** in the leaderboard, and **byte-identical on all 738 nyc_centre rows** in the field-diff (`RAW vs DEBIASED vintage-bin rows that differ from EACH OTHER: 0/738`).
- **The `-5.5%`-causing newer-skew is UNCHANGED:** vintage-bin divergence vs Phase-A stays **168/738** for both raw and de-biased knn (identical to the original T11.6 CP-3 number); mean directional vintage-bin gap vs Phase-A stays **+0.4593** bin-rank units (positive = newer) for both — **0.0% collapse toward zero.** `year_built` leaderboard numbers (MAE 25.141, RMSE 31.909, KS 0.3434, Wasserstein 18.046, exact-bin 449/562) are unchanged from the original T11.6 report (also a useful no-regression cross-check on the unmodified-baseline code paths).
- **Root cause, not a code defect:** checked `function_tag` (680/738 blank) and `building_tag` (581/738 the generic value `"yes"`) as possible near-substitute categorical columns present in the real schema — neither has adequate non-degenerate donor pools to serve as a stratifier at any reasonable `min_donors`. The pinned stratifier (`use_class` else `archetype_id`, T11.8 "How") is architecturally correct and **is proven to work** in isolation: `tests/test_debias.py`'s synthetic unit tests (`TestDebiasNewerSkewMarginalAndRank`, `TestDebiasPullsNewerSkewTowardDonorMean`, `TestMlTierDebiasHook::test_enabled_corrects_non_thin_stratum_and_skips_thin_stratum`) demonstrate the corrector collapses a materially sharper synthetic newer-skew (KS statistic driven from a real divergence down to <0.10 against the donor marginal; a constant severely-skewed raw fill of 2015 pulled to ~1960, matching the donor stratum's median) when a stratifier with adequate per-stratum donor counts is present. **The gap is entirely a data-availability one: the real evaluation frame this whole arc pools from (Stage-1, pre-classification `01_buildings.gpkg`) was never enriched with `use_class`/`archetype_id` before this evaluation runs**, and T11.6's own log already recorded the same root symptom from a different angle ("no categorical -- use_class/archetype_id absent from this schema" — the reason `mice`/`linear` extrapolated catastrophically in the original CP-3 leaderboard).
- **Per plan §7 CP-3b-local checkpoint's own explicit language: "If the skew does not collapse ... STOP and report — the method pivot is the manager's call, not a silent switch."** That condition is met here. **No silent substitution attempted** (did not wire `function_tag`/`building_tag` as a stand-in stratifier; did not add a Stage-2 classification/enrichment pre-step to populate `use_class` before pooling — both would be undocumented scope/method decisions the plan reserves for the manager).
- Test status: n/a (evaluation run, not a pytest suite) — both scripts' output captured verbatim above; `t11_8_cp3b_local_leaderboard_results.json` holds the full machine-readable leaderboard.
- **HARD-STOPPING HERE per kickoff instructions.** T11.8-EUI (the cluster A/B leg) is NOT started — it was already gated on a skew-collapse that did not occur, so submitting it now would just re-confirm the original -5.51% NMBE at cluster cost, exactly the waste CP-3b-local was designed to prevent. Awaiting manager audit + pivot decision: candidate options for the manager to weigh (not decided/executed here) — (1) accept the corrector as built-but-provably-inert on the current real fixture, park T11.8 alongside the existing built-but-off ML tier; (2) authorize a scoped upstream change so the pooled evaluation frame carries `use_class`/`archetype_id` (e.g. running Stage-2 classification before the pool, or fusing in an external land-use source) before re-attempting CP-3b-local; (3) authorize a different/broader stratifier fallback for the real-data case specifically (a method-pivot decision, not made here).

#### Manager — CP-3b-local AUDIT + PIVOT to T11.8b (global qmap fallback) — 2026-07-14
- **Audit verdict: the STOP is CORRECT and well-reasoned — greenlit as a clean structural stop, not a method failure.** Verified both load-bearing claims at code level (did not trust the report): (1) `imputation.py::_ml_tier` lines 736-756 — the de-bias branch fires only when `strat_col is not None`; when neither `use_class` nor `archetype_id` is a column the block is a genuine no-op (confirmed by direct read). (2) The real Stage-1 `01_buildings.gpkg` (pre-classification) carries neither column — consistent with T11.6's own independent "no categorical" finding. So the 0.0 % collapse is a data-availability structural inertness, exactly what CP-3b-local exists to catch **before** any cluster spend. Code quality: `debias.py` is clean, pure, zero-fitted-params (rank→`np.interp` onto sorted observed donors, `rng` unconsumed — deterministic by construction); `test_debias.py` 12/12 + full suite 190/0 with the no-EUI `co_names` guard and the default-off spy byte-identity test both present. The in-place `data_quality_flag` mutation deviation (executor-flagged) is **accepted as-built** for now (it is the only way to emit a second flag under the shared `(value, token)` contract while touching only `_ml_tier`; proven byte-identical when off; no other tier reads that column for routing) — a cleaner tier-handler-contract redesign is deferred to an eventual ship, not required now.
- **Tokens RATIFIED into parent §5G (2026-07-14):** `DEBIAS_NEWERSKEW_QMAP` + `DEBIAS_SKIPPED_THINSTRATUM` (from T11.8) **plus** the new `DEBIAS_NEWERSKEW_QMAP_GLOBAL` (T11.8b) — added as one `DEBIAS_NEWERSKEW_*` row after the `FUSED_*` row, with a Phase-C de-bias ratification note (flags, no independent tier, ride alongside `ML_KNN_<TIER>`, no `provenance.py` change).
- **DECISION — PIVOT to option (3) done RIGHT = a GLOBAL (unstratified) qmap fallback (new task T11.8b), NOT options (1) or (2).** Reasoning: the −5.5 % failure is a **global one-directional marginal shift** (all 167/167 downward), and the primitive that fixes a global shift — `debias_newer_skew`, already built + unit-tested — needs **no stratifier**. Applying it globally when no stratifier column is present targets the exact failure mode, reuses tested code, and is **within the pinned method** (global = one all-inclusive stratum, so NOT the moment-matching pivot the plan reserves for a manager STOP). **Rejected option 2** (upstream Stage-2 pre-classification to populate the stratifier): chicken-and-egg — archetype needs `year_built`, the very field being imputed — and `use_class` is unreliable on dense already-mapped stock (Phase-D CP-4 showed ~0 % Overture `use_class` fill in Manhattan); too heavy, uncertain payoff. **Rejected option 1** (park inert): delivers zero actual progress on the −5.5 %.
- **Cluster spend STAYS GATED.** T11.8b re-runs the SAME cheap local CP-3b-local field-diff; the cluster A/B (T11.8-EUI) remains withheld until the local proof shows the directional gap (was **+0.4593**) collapsing toward 0 *without* over-correcting past 0 and *without* dropping `year_built` attribute-recovery below Phase-A. If global qmap over-corrects (gap overshoots to a negative/newer-opposite) or doesn't move, that is again a manager STOP.
- Test status: n/a (audit + planning). Parent §5G edited; §0 checklist + §6 T11.8b + this entry added.
- Notes: **DISPATCHING a fresh Sonnet executor scoped T11.8b → hard-STOP at the re-run CP-3b-local.** Same discipline as the T11.8 dispatch: single file-scope touch (`_ml_tier` + a `test_debias.py` case), zero-fitted-params structural guard intact, no cluster leg.

#### T11.8b — global (unstratified) qmap fallback in `_ml_tier` — completed 2026-07-14
- Artifacts: `openubem/semantic/imputation.py` (MODIFY, single file-scope touch per plan §6 T11.8b — added the `_DEBIAS_NEWERSKEW_QMAP_GLOBAL` module constant next to the existing `_DEBIAS_NEWERSKEW_QMAP`/`_DEBIAS_SKIPPED_THINSTRATUM`; extended `_ml_tier`'s `strat_col is None` branch, which previously fell through untouched, to apply `debias.debias_newer_skew` globally when the full `gdf`-wide observed-donor pool clears `min_donors=30`; docstring updated); `tests/test_debias.py` (MODIFY — 2 new cases in `TestMlTierDebiasHook`: `test_global_fallback_fires_when_no_stratifier_column_present` and `test_global_fallback_noop_below_min_donors`). No other files touched — `debias.py`, `config.py`, `enrich_semantics`, `IMPUTE_ENABLED_TIERS` all untouched per the kickoff's binding rule 2.
- **Implementation exactly as pinned (plan §6 T11.8b "How"):** the `strat_col is not None` path (T11.8's stratified `debias_stratified` call + `_QMAP`/`_SKIPPED_THINSTRATUM` tagging) is byte-unchanged. The new `else` branch (`strat_col is None`) computes `observed_donors = gdf.loc[gdf[attr].notna(), attr]` (identical construction to the stratified path, just not grouped by stratum) and: if `len(observed_donors.dropna()) >= debias.DEFAULT_MIN_DONORS` (30, imported not re-declared), calls `debias.debias_newer_skew(preds, observed_donors, rng=rng)` once over the WHOLE `rows` set and tags every row `DEBIAS_NEWERSKEW_QMAP_GLOBAL` via the same in-place `data_quality_flag` mutation mechanism T11.8 established (no tier-handler-contract change); else (below 30 donors) leaves `debias_tag` at its pre-initialized all-`None` and `preds` untouched — the exact pre-T11.8b no-op. Reused the already-built, already-unit-tested `debias_newer_skew` primitive verbatim — no new method code, per rule 6 ("stratification-granularity fallback, NOT a method pivot").
- **Zero-fitted-params preserved:** `min_donors=30` is `debias.DEFAULT_MIN_DONORS`, the same literal constant T11.8 pinned — not re-declared, not swept. `debias_newer_skew` is the same primitive `tests/test_debias.py::TestNoEUILeakage`'s `__code__.co_names` structural guard already covers; no new code path reads an EUI-like name.
- **Additive & opt-in confirmed:** `test_disabled_by_default_never_calls_debias` (unmodified, still asserts `debias.debias_stratified` — the stratified spy — is never invoked with the flag at its shipped all-False default) continues to pass; the new global branch is gated behind the SAME `debias_targets.get(attr)` truthy check, so it is equally inert by default. `TestImputeMissingDefaultOff::test_opt_in_ml_without_debias_flag_matches_two_runs` (unmodified) still passes, reconfirming public-API byte-identity for opt-in-`ml`-without-the-flag runs.
- Test status: `tests/test_debias.py` **14/14 passed** (12 pre-existing + 2 new T11.8b cases). Full combined suite `pytest tests/test_ml_imputer.py tests/test_imputation.py tests/test_imputation_routing.py tests/test_mask_recover.py tests/test_tierB_provenance.py tests/test_vintage_donor.py tests/test_levels_groupwise.py tests/test_spatial_impute.py tests/test_provenance.py tests/test_debias.py -q` → **192 passed, 0 failed** in 111.65s (190 T11.8-era + 2 new; zero regressions, CP-1 gate suite unaffected).
- Deviations: none — signatures, constant reuse, branch placement, and tagging exactly as plan §6 T11.8b "How" specifies. Tier-handler `(value, token)` contract untouched.

#### CP-3b-local RE-PROOF (T11.8b global fallback) — executed 2026-07-14 — skew does NOT collapse; attribute-recovery regresses below Phase-A
- Artifacts: re-ran the SAME two T11.8 throwaway drivers, unmodified (`scratchpad/t11_8_cp3b_local_field_diff.py`, `scratchpad/t11_8_cp3b_local_leaderboard.py` — both already enable `config.IMPUTE_DEBIAS_NEWERSKEW["year_built"] = True` internally for their "DEBIASED" branch, so no driver edits were needed); `scratchpad/t11_8_cp3b_local_leaderboard_results.json` overwritten with the new run's numbers.
- **The global hook DOES fire this time** (confirmed: `use_class`/`archetype_id` still absent from the pooled Stage-1 frame — `use_class in columns: False`, `archetype_id in columns: False` — but the global observed-`year_built`-donor pool across all 12 cells is thousands of rows, far above `min_donors=30`). RAW vs DEBIASED predictions differ on 163/738 nyc_centre rows (field-diff) and are NOT identical on any of the 562 `year_built` holdout rows (leaderboard) — a real, active correction, not a structural no-op.
- **Directional vintage-bin gap vs Phase-A (nyc_centre, n=738) — DID NOT COLLAPSE, IT WORSENED:** RAW knn was **+0.4593** (unchanged from the T11.8 1st proof, confirming the unmodified-baseline cross-check). DEBIASED (global) knn is **+0.6016** — MORE positive, i.e. the newer-skew got **larger**, not smaller. `collapse toward 0 = -31.0%` (the field-diff script's own metric — a negative number means the gap grew, not shrank). This is neither a clean collapse-to-0 nor an overshoot-past-0-to-negative; it is a straight **amplification in the same (newer) direction**. Vintage-bin divergence vs Phase-A also worsened: RAW 168/738 → DEBIASED 248/738.
- **`year_built` attribute-recovery leaderboard (pooled, n_holdout=562) — REGRESSES BELOW PHASE-A:** Phase-A MAE 26.433 / exact-bin 456/562. Raw-knn MAE 25.141 / exact-bin 449/562 (T11.8's own unchanged cross-check, confirmed identical to the original T11.6 CP-3 report). **DEBIASED (global) knn: MAE 25.746 / exact-bin 425/562** — exact-bin recovery is now BELOW both Phase-A (456) and raw-knn (449). MAE stays close to raw-knn (mid-way between raw and Phase-A, as the plan's "expected tension" flagged is tolerable), but exact-bin — the plan's own headline CP-3 attribute-recovery metric — drops materially below the Phase-A floor, which plan §7's CP-3b-local checkpoint explicitly treats as a stop condition on its own. (`levels` also shown for completeness: Phase-A MAE 9.176, raw-knn MAE 8.388, debiased MAE 8.953 — debiased sits between the two, no categorical exact-bin metric applies to `levels`.)
- **Root-cause hypothesis (reported, not investigated further — outside this task's scope):** the global donor pool is built from `gdf.loc[gdf[attr].notna(), attr]` over the FULL pooled 12-cell, 8,160-row multi-city frame (exactly as plan §6 T11.8b "How" pins it), not scoped to nyc_centre. nyc_centre's own true `year_built` marginal is overwhelmingly `DOERefPre1980` (683/738 = 92.5%, per the Phase-A distribution above), while the pooled cross-city donor marginal is dominated by the much larger la_suburban/la_urban observed stocks (1,295 + 542 observed rows vs nyc_centre's 158, per plan §1's CP-3 inventory), which skew newer. Quantile-mapping nyc_centre's raw knn fills onto that pooled, LA-dominated marginal pulls them toward a distribution that is a worse match for nyc_centre specifically than the raw (already newer-skewed) knn fills were — i.e., the "global" fallback's donor pool is representative of the POOLED evaluation frame, not of the LOCAL cell being corrected. This is a plausible, non-speculative explanation consistent with every number above, but it was **not tested or acted on** (no per-city donor scoping was attempted) — that would be a method/architecture change reserved for the manager.
- Test status: n/a (evaluation run, not a pytest suite) — both scripts' console output captured verbatim above; `t11_8_cp3b_local_leaderboard_results.json` holds the full machine-readable leaderboard for the manager's own inspection.
- **VERDICT: NO — the −5.5 % directional skew does NOT materially collapse toward 0 under the T11.8b global qmap fallback.** It instead grows by ~31% in the same (newer) direction, and `year_built` attribute-recovery (exact-bin 425/562) drops below both Phase-A (456/562) and raw-knn (449/562). Both of plan §7 CP-3b-local's pass conditions fail simultaneously. **HARD-STOPPING HERE per the kickoff instructions — T11.8-EUI (the cluster A/B leg) is NOT started.** No tuning, parameter sweep, or silent method change was attempted to try to make this pass (that would violate zero-fitted-params and the plan's explicit "method pivot is the manager's call" rule). Awaiting manager audit + pivot decision — candidate options for the manager to weigh (not decided/executed here): (1) accept both T11.8 and T11.8b as built-but-provably-ineffective-or-harmful on the real fixture, park the whole de-bias corrector alongside the existing built-but-off ML tier, no further engineering; (2) authorize a scoped per-city (rather than global-pooled) donor-scoping variant as a distinct fallback tier (a method/architecture decision reserved for the manager, consistent with the root-cause hypothesis above); (3) some other pivot the manager judges appropriate. This report intentionally states the negative result plainly rather than searching for a configuration that passes.

#### Manager — CP-3b-local AUDIT (both de-bias variants) + REFRAME to a granularity-validity diagnostic — 2026-07-14
- **Audit: both negative results VERIFIED and accepted.** T11.8b is clean, in-scope (single `_ml_tier` touch + 2 tests, 192/0), reuses the tested primitive, zero-fitted-params intact, byte-identical off. The re-proof numbers are trustworthy and the executor's root-cause hypothesis is confirmed by the inventory it cites: the global qmap reference is the pooled 12-cell marginal, dominated by la_suburban (1295 obs) + la_urban (542 obs) vs nyc_centre's 158 — so it transports nyc_centre's fills (true marginal 92.5 % pre-1980) toward an LA-newer distribution, amplifying rather than collapsing the skew. Neither de-bias variant works on the real fixture (stratified = structural no-op, columns absent; global = wrong-reference amplification).
- **REFRAME — the decisive finding is a granularity mismatch, not a missing de-bias.** The original CP-3 −5.51 % was measured on a **pooled** fit (all 12 cells → 2247 obs `year_built`, needed because knn's complete-case floor is ≥200 and **nyc_centre alone has only 158 obs → cannot clear its own floor**) and then sliced to nyc_centre. But production imputes **per-cell** (`enrich_semantics`/`impute_missing` runs on one cell's gdf; `build_ml_imputer` fits on that gdf's complete cases only). Therefore **in real per-cell production, knn-`year_built` never even fires on nyc_centre** — it falls through to the CP-2-validated Phase-A spatial imputer. The −5.5 % harm signal was evaluated at a granularity production never uses, on a cell that would not fire, with a cross-city donor pool — it is **not a valid production do-no-harm signal**. This also explains why de-bias couldn't help: it was fighting a pooling artifact, not a production behaviour.
- **DECISION — set the de-bias line ASIDE (do NOT run a T11.8c city-local qmap); run ONE cheap production-granularity validity diagnostic instead.** A city-local qmap (option 2) was considered and REJECTED as not decision-relevant: (i) even a clean pass would not change the ship outcome, because per-cell production can't fit knn on small cells like nyc_centre anyway (floor), so ml-year_built there is Phase-A regardless; and (ii) a successful city-local qmap's endpoint — transport knn fills onto the cell's own observed marginal — essentially reconstructs what the already-validated Phase-A spatial imputer does, at far more complexity, for a target where Phase-A is already CP-2-perfect (+0.49 %). Spending a cluster A/B (or more local iterations) on that is exactly the validation-chasing the arc's zero-fitted-params culture forbids. **Instead**, the one genuinely open + decision-relevant question is: at **production (per-cell) granularity, on a cell that DOES clear the knn floor (la_suburban, 1295 obs), does raw knn (no de-bias) do harm vs Phase-A at all?** That was never tested. If per-cell raw-knn's vintage-bin directional gap ≈ 0 (attribute-recovery ≥ Phase-A) → the −5.5 % was purely an eval artifact and ml is likely production-safe where it fires; if it still materially skews → ml genuinely harms even at production granularity and the tier stays built-but-off for good. Either outcome is a defensible terminal conclusion.
- Test status: n/a (audit + planning). §0 checklist updated (T11.8b done-negative, CP-3b-local NOT-MET, T11.8c-diag added); §5G tokens already ratified.
- Notes: **DISPATCHING a fresh Sonnet for T11.8c-diag** — local, no cluster, no new production code, NO de-bias flag. Impute la_suburban (and la_urban if quick) **alone** (production granularity), Phase-A vs raw-knn, report the per-cell EUI-relevant vintage-bin directional gap + `year_built` attribute-recovery, hard-STOP for the manager's terminal decision. This is a validity check on the original CP-3 signal, not a new de-bias attempt.

#### T11.8c-diag — per-cell production-granularity raw-knn do-no-harm diagnostic — executed 2026-07-14
- Artifacts: `scratchpad/t11_8c_diag_percell_field_diff.py` (adapted from `t11_8_cp3b_local_field_diff.py`: subsets `pooled` to ONE cell BEFORE calling `impute_missing`, instead of pooling-then-slicing-after — this reproduces production granularity, where `build_ml_imputer` only ever sees one cell's own complete cases); `scratchpad/t11_8c_diag_percell_leaderboard.py` (adapted from `t11_cp3_leaderboard.py`'s `run_one`/`exact_bin_recovery`, reused verbatim/imported — same subset-cell-first change) + `scratchpad/t11_8c_diag_percell_leaderboard_results.json`. Both cells run: `la_suburban` (1295 obs, clears knn's ≥200 floor) and `la_urban` (542 obs, also clears). `IMPUTE_DEBIAS_NEWERSKEW` asserted all-False at the top of both scripts (never touched); no `openubem/**` file modified.
- **Does knn fire per-cell? YES, on both cells, confirmed by `ML_KNN_HIGH` provenance tokens.** Field-diff (whole-cell impute, actually-missing rows only): `la_suburban` 29/48 missing `year_built` rows filled by knn; `la_urban` 4/76. Mask-and-recover (holdout-based, larger N because it masks additional *observed* rows to score against ground truth): `la_suburban` 202/260 holdout rows; `la_urban` 74/113. **This directly refutes the premise that knn structurally can't fire per-cell** — both cells clear the floor and knn fires materially, not marginally.
- **Directional vintage-bin gap vs Phase-A (field-diff, the EUI-relevant signal): `la_suburban` = +0.0000 (0/1343 divergent rows); `la_urban` = +0.0000 (0/618 divergent rows).** Zero skew, exact bin-for-bin agreement between raw-knn's actual fills and Phase-A's fills on every row of both cells — a sharp contrast with the pooled nyc_centre number (+0.4593, 168/738 divergent) that drove the original CP-3 EUI failure.
- **Attribute-recovery (mask-and-recover, `year_built`, seed 42, T08-default holdout) vs Phase-A:**
  - `la_suburban` (n_holdout=260): Phase-A mae=4.236 rmse=10.725 ks=0.1654 wass=3.726 exact_bin=247/260. Raw-knn mae=4.279 rmse=9.620 ks=0.2846 wass=2.328 exact_bin=247/260. Exact-bin **ties** Phase-A exactly; MAE is +0.043y worse (negligible); RMSE and Wasserstein both **better** than Phase-A; KS worse.
  - `la_urban` (n_holdout=113): Phase-A mae=20.570 rmse=26.330 ks=0.3540 wass=15.142 exact_bin=100/113. Raw-knn mae=20.580 rmse=25.718 ks=0.2743 wass=6.532 exact_bin=96/113. MAE is +0.01y worse (negligible, i.e. essentially tied); RMSE, KS, and Wasserstein all **better** than Phase-A; exact-bin **regresses** by 4 rows (96 vs 100, −3.5 pp) — the one metric on the one cell that dips below Phase-A.
- Test status: n/a (evaluation run, not a pytest suite) — both scripts' console output captured verbatim above; `t11_8c_diag_percell_leaderboard_results.json` holds the full machine-readable leaderboard.
- **VERDICT (report-only, no tuning attempted to improve these numbers): at production (per-cell) granularity, raw knn (no de-bias) does NOT reproduce the pooled −5.5 % directional skew on either floor-clearing cell — the directional vintage-bin gap is exactly 0.0000 on both `la_suburban` and `la_urban`.** Attribute-recovery is essentially at parity with Phase-A: one exact tie (`la_suburban` exact-bin 247/260 both) and one small, isolated regression (`la_urban` exact-bin −4/113, with every other metric on that same cell equal-or-better than Phase-A). This confirms the manager's REFRAME (§8 2026-07-14): the original CP-3 −5.51 % NMBE was a **pooled-evaluation granularity artifact**, not a signal that reproduces under production's actual per-cell imputation behaviour. **HARD-STOPPING HERE per kickoff instructions — no cluster leg started, no de-bias touched, no `openubem/**` file modified.** Awaiting the manager's terminal decision on T11.8-EUI / CP-3b / ship status.
- Notes for the manager: the field-diff (directional-gap) result is the cleanest, most decision-relevant number — it is literally zero on both cells, both directions. The attribute-recovery leg is the only place any regression appears at all, and it is confined to a single metric (exact-bin) on a single cell (`la_urban`), while RMSE/Wasserstein/KS on that same cell all favor knn — i.e. knn's `la_urban` errors are smaller/tighter in aggregate even though it landed in the wrong discrete bin on 4 more holdout rows than Phase-A's group-mode fallback.

#### Manager — CP-3b TERMINAL DECISION: −5.5 % RESOLVED as an eval artifact; de-bias line CLOSED; ml stays built-but-off — 2026-07-14
- **Diagnostic AUDITED + ACCEPTED (verified the numbers, not just the summary).** The subset-cell-BEFORE-impute construction is the correct production-granularity reproduction (`build_ml_imputer` sees one cell's complete cases only, exactly as `enrich_semantics` runs per cell). Both floor-clearing cells fire knn materially (la_suburban 202/260 holdout, la_urban 74/113), so the result is not a no-op-in-disguise. The de-bias flag was asserted OFF and no `openubem/**` file was touched — a clean raw-knn-vs-Phase-A measurement.
- **TERMINAL FINDING: the CP-3 −5.51 % NMBE was a POOLED-EVALUATION GRANULARITY ARTIFACT, not a production do-no-harm failure.** At production (per-cell) granularity the directional vintage-bin gap is **exactly +0.0000 on both cells (0/1343 + 0/618 rows divergent)**. Because EUI flows through the vintage BIN (→ U-values), zero bin divergence means **raw knn and Phase-A produce identical EUI per-cell by construction** — knn-`year_built` at production granularity is do-no-harm **and** do-no-good (EUI-indistinguishable from the validated Phase-A). The pooled −5.5 % arose only because the eval had to pool 12 cities to clear knn's ≥200 fit floor, which (a) let the fit borrow cross-city structure and (b) was then scored on nyc_centre — a cell that in production would fall through to Phase-A (158 obs < 200) and never see knn at all.
- **DECISION — CP-3b CLOSED / RESOLVED. ml tier STAYS built-but-off / opt-in (status quo since the 2026-07-03 user ruling), but the RATIONALE is corrected:** it is held off because at production granularity it is **EUI-neutral** (zero benefit to justify adding an sklearn fit + complexity to the default pipeline), **NOT** because it harms. This exonerates the Phase-C ML design — the earlier "systematic −5.5 % bias" verdict is superseded as a methodology artifact. Per-target flexibility preserved (`IMPUTE_ML_METHOD_BY_TARGET`): the tier remains available opt-in for a future target/data regime where it might add real value.
- **T11.8-EUI (cluster A/B) WITHDRAWN — not run, by design.** With per-cell vintage-bin divergence at exactly 0, a cluster EUI A/B would return NMBE≈0 by foregone conclusion; spending cluster budget to confirm an analytically-certain result is exactly the waste CP-3b-local exists to prevent. **No cluster spend.**
- **De-bias corrector (T11.8 stratified + T11.8b global) — KEPT as built** (clean, unit-tested 14/14, opt-in, byte-identical off, zero-fitted-params, §5G-ratified tokens) but **documented as UNNECESSARY at production granularity** — there is no per-cell skew to correct. Harmless to retain; removes nothing from the default. No further de-bias engineering.
- **la_urban exact-bin −4/113 caveat: accepted, non-disqualifying.** It is one discrete-bin metric on one cell; RMSE/KS/Wasserstein on that same cell all favor knn (tighter aggregate error), and it does not move the directional gap off 0. Not a do-harm signal.
- **Zero-fitted-params honored throughout:** the terminal conclusion was reached by measuring at the correct granularity and reporting the result, never by tuning any imputer setting to pass a gate. No parameter was swept; the de-bias line was closed on evidence, not forced through.
- **Manager self-signs this CLOSE** (arc-momentum convention): it keeps the status-quo the user already ratified (ml off) — no new default-run change, so no fresh user-sign-off required. Surfacing the corrected understanding to the user for awareness; a *ship* of ml into the default would still be user-sign-off, but I am not recommending one (no benefit case). **Phase-C ML arc returns to CLOSED / built-but-off, now with the −5.5 % failure correctly re-attributed.**
- Test status: n/a (terminal decision). §0 checklist finalized (T11.8-EUI withdrawn, CP-3b closed-resolved); parent `PLAN_input_imputation_implementation.md` §9.2 updated.
- Notes: no further executor dispatch. The three throwaway diagnostic scripts remain under `scratchpad/` for reproducibility; `debias.py` + its tests stay in-tree as opt-in capability.
