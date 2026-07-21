# DEBUG PLAN — Phase-C knn attribute-leaderboard reproducibility investigation

**Slug:** `phaseC-knn-repro-investigation`
**Date:** 2026-07-15
**Arc:** Input-Parameter Imputation ("OpenUBEM AI") — re-opens the CLOSED+SIGNED Phase C for a **diagnosis only** (no fix without manager sign-off).
**Trigger:** The figures follow-up (§9 of `../implementation/PLAN_figures_implementation.md`, T11) tried to draw the Phase-C predicted-vs-actual scatter from **real regenerated pairs** and hit the mandatory cross-check gate: the live `ml`/knn tier no longer reproduces `RESULTS_phaseC.md`'s committed leaderboard.

---

## 0. The discrepancy (established facts — do not re-litigate)

Re-running the exact §5-C protocol (pool all 12 committed `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg`, reproject EPSG:5070, spatial-block 80/20, seed `RANDOM_SEED=42`, via the new `openubem.validation.mask_recover.recover_pairs`):

| target | n_complete | n_holdout | Phase-A MAE (committed) | knn MAE (committed) |
|---|---|---|---|---|
| `year_built` | 2,247 ✓ | 562 ✓ | **26.43 = 26.43 ✓ (exact)** | **27.82 ≠ 25.14 ✗** |
| `levels` | 441 ✓ | 134 ✓ | **9.18 = 9.18 ✓ (exact)** | **10.10 ≠ 8.39 ✗** |

**What this proves already:**
- The pooling, CRS reprojection (mandatory — pooling without it raises a hard geopandas error), spatial-block holdout, complete-case counts, and the **Phase-A (`spatial`,`statistical`) baseline all reproduce EXACTLY.** The harness is faithful.
- The divergence is **isolated to the `ml`/knn tier**, and it is in the **wrong direction** — current knn scores *worse* than Phase-A, contradicting `RESULTS_phaseC.md`'s "knn beats Phase-A on every continuous metric."
- The `_clamp_to_observed_range` guard (added 2026-07-13) is a **proven no-op for knn** (weighted-neighbour-average is inherently in-range) — already ruled out.
- `git log -- openubem/semantic/imputation.py` shows a **single squashed commit `0df422e`** and nothing after → git-diff cannot isolate a post-run change to that file. Either the committed `imputation.py` already differs from the 2026-07-03 working copy, or the drift lives outside `imputation.py`.

**Scope reassurance (state it in the report):** no *shipped energy result* is affected. The `ml` tier is OFF / opt-in, never in the default `IMPUTE_ENABLED_TIERS`; baselines A/B/D and the CP-1 byte-identity are untouched. What is in question is a **documentation claim** in a signed RESULTS doc and the Phase-C scatter figure.

---

## 1. Hard rules for the executor

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** No other CWD.
2. **This is a DIAGNOSIS, not a fix.** Produce a root-cause report. **Do NOT edit production code, `RESULTS_phaseC.md`, or any config to "make it pass"** without stopping for manager sign-off. Propose the fix in writing; do not apply it.
3. **Zero-fitted-params is absolute.** NEVER tune knn hyperparameters / features / floors to hit 25.14. The target of this investigation is *why the number moved*, not *how to recover it*. If the honest answer is "25.14 is not reproducible from any committed state," that is a valid, acceptable finding — report it plainly.
4. **Local compute only.** pandas/sklearn on the committed gpkgs, seed 42, deterministic. NO EnergyPlus, NO cluster, NO login-node, NO network. `mask_recover` reads no EUI.
5. **No new simulation.** All inputs already exist.
6. **Report, do NOT tune:** nothing you compute feeds back into any `ImputeConfig`/threshold/bound.
7. Default to no comments; do not commit (git handled externally).

---

## 2. Source-of-truth to read first

- `docs/docs_ACTIVE/input/imputation/docs_Done/PLAN_phaseC_ml_imputer.md` **§8 progress log** — the binding record of the EXACT 2026-07-03 protocol/config: the entries "T11.1 build_ml_imputer", "T11.6 — CP-3 gate", "T11.6 attribute leaderboard". Extract every load-bearing knn detail: which `feature_cols`, whether the neighbour-vintage `_spatial_lag` feature was on, `n_neighbors`, `weights`, the `family` selection (KNNImputer "matrix" vs `KNeighborsClassifier` estimator), the per-target floors, and the tier order `("spatial","ml","statistical")`.
- `docs/docs_ACTIVE/input/imputation/results/phase_C/RESULTS_phaseC.md` — the committed leaderboard numbers (26.43→25.14; 9.18→8.39; n_holdout 562/134; "re-run twice, byte-identical").
- `openubem/semantic/imputation.py` — current `build_ml_imputer`, `_ml_tier`, `_spatial_lag`, `_estimator_for`, the `MLImputer` dataclass, `family` selection, `_knn_dispersion`, `_clamp_to_observed_range`.
- `openubem/config.py` — `IMPUTE_ML_FLOORS`, `IMPUTE_ML_METHOD_BY_TARGET`, the default `feature_cols`/feature set, `RANDOM_SEED`.
- `openubem/results/impute_scatter.py` — the module docstring already records this block (audit trail).

---

## 3. Investigation tasks

### D01 — Independently confirm the discrepancy
- **What:** Using `recover_pairs`, reproduce the table in §0 from scratch (pool 12 cells → EPSG:5070 → seed 42). Confirm Phase-A = 26.43/9.18 exact and knn = 27.82/10.10 (or report whatever you actually get). Print `n_complete`/`n_holdout` to confirm 2,247/562 and 441/134.
- **Why:** Never build a root-cause on a second-hand number. Establish the discrepancy under your own hand first.
- **Test:** the Phase-A leg must reproduce 26.43/9.18 exactly (proves your harness invocation is faithful); attach the printed values.

### D02 — Reconstruct the documented 2026-07-03 knn configuration
- **What:** From `PLAN_phaseC_ml_imputer.md` §8 + `RESULTS_phaseC.md`, write down the exact knn config that produced 25.14: feature set, spatial-lag on/off, `family` (matrix vs estimator), `n_neighbors`, `weights`, floors, tier order. Then read the CURRENT code path for `method="knn"` on `year_built` and record the SAME parameters as they resolve today.
- **Why:** The root cause is almost certainly a delta between these two columns. Make the delta explicit.
- **Test:** a two-column "2026-07-03 documented vs current-code" table for every knn-affecting parameter, each current value cited to a code line.

### D03 — Bisect the cause across the non-`imputation.py` surface
- **What:** Since `imputation.py` is a single squashed commit, look OUTSIDE it. `git log -p -- openubem/config.py` and any spatial/tree primitive file (`openubem/semantic/spatial_impute.py` or wherever `_build_tree`/`neighbour_vote` live) for changes after the ml imputer landed. Check whether the **default feature set**, the **spatial-lag radius/k** (`_spatial_lag` k=10/radius=100), the **`family` selection heuristic**, or the **floors** differ from the documented Phase-C run. Also verify the 12 committed gpkgs themselves are the same inputs the leaderboard used (column set, `year_built`/`levels` observed counts per cell summing to 2,247/441).
- **Why:** If the code that computes features or selects the knn family changed, knn's MAE moves even though the top-level "knn" label is unchanged.
- **Test:** identify the single change (or the smallest set) that, when reverted *in an isolated local experiment* (scratch copy — do NOT modify tree files in place), moves knn back toward 25.14; OR conclude no committed state reproduces it.

### D04 — Classify the root cause + recommend (no fix applied)
- **What:** Land one of these verdicts, with evidence:
  - **(a) Recoverable regression** — a specific, zero-fitted-params code/config change degraded knn; reverting it restores ~25.14 without any tuning. Propose the exact one-line fix (do NOT apply).
  - **(b) Non-reproducible-from-committed** — 25.14 was produced by working-copy code lost to the squash; no committed state reproduces it without fitting. Recommend annotating `RESULTS_phaseC.md` with a reproducibility caveat (manager/user call).
  - **(c) Harness/feature subtlety** — the number depends on a non-pinned detail (e.g. sklearn version, a `family` heuristic tied to pool size); document it.
- **Why:** The manager + user need a crisp verdict to rule on: fix, annotate the doc, or drop the Phase-C scatter.
- **Test:** the report names the verdict, the evidence, and — for (a) — the exact proposed diff, explicitly NOT applied.

---

## 4. Stop-and-report

**CP-D1 — after D01–D04.** Report: the confirmed discrepancy table (D01), the documented-vs-current config table (D02), the bisection result (D03), and the classified verdict + recommendation (D04). **Do not apply any fix or doc edit.** Manager audits, then returns to the user to rule on: fix the regression / annotate the doc / drop the Phase-C scatter — before the figures follow-up (§9 T11–T12) resumes.

---

## 5. Progress log

_(executor appends one entry per D0x in the CLAUDE.md format)_

#### D01 — Independently confirm the discrepancy — completed 2026-07-15
- Artifacts: re-ran the surviving, UNMODIFIED T11.6 driver `scratchpad/t11_cp3_leaderboard.py` (still on
  disk, untouched since 2026-07-03) against today's full working tree (git status: `openubem/config.py` +
  `openubem/semantic/imputation.py` + `openubem/validation/mask_recover.py` all carry UNCOMMITTED changes
  on top of the squashed commit `0df422e`); also wrote an independent `recover_pairs`-based repro script
  (`scratchpad/d01_repro.py`) mirroring the same protocol.
- **Result — Phase-A reproduces exactly (as already established):** `year_built` MAE 26.433 / RMSE
  32.355 / KS 0.5089 / Wasserstein 26.210, n_complete_cases=2247, n_holdout=562. `levels` MAE 9.176 /
  RMSE 15.063 / KS 0.4701, n_complete_cases=441, n_holdout=134. Pooled n=8160 across 12 cells; observed
  raw N `year_built`=2247, `levels`=441 — both sum-checks match §0/RESULTS_phaseC.md exactly.
- **Result — knn ALSO reproduces exactly (contradicts §0's "27.82≠25.14" established-fact line):**
  `year_built` `knn` MAE **25.141** / RMSE 31.909 / KS 0.3434 / Wasserstein 18.046 / exact-vintage-bin
  **449/562** — matches `RESULTS_phaseC.md` (25.14) to 3 decimals. `levels` `knn` MAE **8.388** / RMSE
  12.982 — matches (8.39) to 3 decimals. All 6 methods' numbers (missforest/mice/knn/rf/histgbm/linear)
  reproduce the full committed leaderboard exactly, including the `mice`/`linear` AD-5000+ footgun
  (MAE 34.0/33.8) and the histgbm below-floor fallback (byte-identical to Phase-A).
- **Headline of D01: I could NOT reproduce the reported discrepancy.** Under my own hand, using the
  CURRENT working-tree code as-is (uncommitted T11.8/T11.8b/T12 changes included, nothing reverted),
  calling either the original `mask_and_recover`-based driver or the new `recover_pairs` wrapper via the
  documented protocol (pool 12 cells → EPSG:5070 → per-target call → `config.IMPUTE_ML_METHOD_BY_TARGET
  [target]="knn"` set explicitly → `ImputeConfig(enabled_tiers=("spatial","ml","statistical"))` →
  freshly-seeded `rng=np.random.default_rng(42)` per call) reproduces the committed leaderboard
  byte-for-byte to 3 decimals on every metric, for every method, on both targets. See D03 for the
  bisection of what invocation pattern instead produces a worse-than-Phase-A number.
- Test status: n/a (evaluation re-run, not a pytest suite); raw console output captured in
  `scratchpad/rerun_t11_cp3_leaderboard.log` and `scratchpad/t11_cp3_leaderboard_results.json`
  (overwritten by this re-run, byte-identical in content to the 2026-07-03/07-14 versions except JSON
  key ordering).

#### D02 — Reconstruct the documented 2026-07-03 knn configuration vs current code — completed 2026-07-15
- Artifacts: read `docs_Done/PLAN_phaseC_ml_imputer.md` §8 (T11.1/T11.3/T11.6 entries) +
  `results/phase_C/RESULTS_phaseC.md` for the documented config; cross-referenced against
  `openubem/semantic/imputation.py` (current working tree, uncommitted changes included) by line number.

| Parameter (year_built/levels, `knn`) | 2026-07-03 documented (PLAN §8 T11.1/T11.3) | Current code (cited) | Match? |
|---|---|---|---|
| `family` selection | `"matrix"` for `knn`+regression target (T11.1 deviation 1) | `imputation.py:458` `family = "matrix" if (method in ("missforest","mice","knn") and not is_classifier) else "supervised"` | ✅ identical |
| Matrix estimator | `KNNImputer(n_neighbors=5, weights="distance")` (PLAN parent §4 hyperparameter table, frozen) | `imputation.py:493` `estimator = KNNImputer(n_neighbors=5, weights="distance")` | ✅ identical |
| `year_built` spatial-lag feature | ON — `_spatial_lag(gdf,"year_built",k=10,radius=100)` wired inside `_ml_tier`, injected as `__ml_year_built_spatial_lag__` (T11.3 log) | `imputation.py:192` `_spatial_lag(gdf, col, k: int = 10, radius: float = 100.0)`; wired at `imputation.py:740` `work[_YEAR_BUILT_SPATIAL_LAG_COL] = _spatial_lag(gdf, "year_built")` inside `_ml_tier`, unconditional on `attr=="year_built"` | ✅ identical (defaults `k=10`/`radius=100` unchanged) |
| Feature set (`_DEFAULT_ML_FEATURE_COLS`) | EUI-free geometry/morphology set (plan §4) + the spatial-lag column | `imputation.py:146` `_DEFAULT_ML_FEATURE_COLS` tuple, resolved via `_ml_feature_cols_for`/`imputation.py:682` `[c for c in _DEFAULT_ML_FEATURE_COLS if c in gdf.columns and c != attr]` | ✅ identical — constant untouched by the uncommitted diff |
| Per-target floor (`knn`) | `IMPUTE_ML_FLOORS["knn"] = 200` | `config.py` `IMPUTE_ML_FLOORS = {..., "knn": 200, ...}` — this dict is NOT in the uncommitted diff (unchanged since T11.1) | ✅ identical |
| Default per-target method | T11.6's driver explicitly set `config.IMPUTE_ML_METHOD_BY_TARGET[target] = method` inside its 6-method sweep loop — never relied on the bare default | **Shipped default is `"missforest"` for every target** (`config.py:94-99` `IMPUTE_ML_METHOD_BY_TARGET = {"year_built": "missforest", "levels": "missforest", ...}`) — NOT `"knn"` | ⚠️ same as documented IF the caller explicitly overrides it (T11.6 always did); a caller that skips the explicit override silently gets `missforest`, not `knn` — flagged as the leading D03 hypothesis |
| Tier order / `enabled_tiers` | `ImputeConfig(enabled_tiers=("spatial","ml","statistical"))` passed explicitly (T11.6 §8) | Same explicit override available and used in my D01 repro; `config.IMPUTE_ENABLED_TIERS` DEFAULT changed from `("spatial","statistical")` (committed) to `("fusion","spatial","statistical")` (uncommitted T12-ship diff) — but this is the *default* only, irrelevant whenever `cfg=ImputeConfig(enabled_tiers=...)` is passed explicitly as T11.6/D01 both do | ✅ identical when the caller passes explicit `enabled_tiers` (as documented); the changed *default* only matters if a caller relies on it implicitly (not what T11.6 did) |
| `_clamp_to_observed_range` (uncommitted, new) | Not present 2026-07-03; added later (T11.6-era plan cites "2026-07-13") | `imputation.py:279-315` clips `MLImputer.predict()` output to `[target_observed_min, target_observed_max]` = `[min(train_y), max(train_y)]` | Present in current code but **proven a mathematical no-op for the matrix-family `knn` path** — see D03 |
| `IMPUTE_DEBIAS_NEWERSKEW` hook (uncommitted, new, T11.8/T11.8b) | Not present 2026-07-03; built 2026-07-14, default all-`False` | `imputation.py:751-790` — gated behind `debias_targets.get(attr)` truthy check; default dict in `config.py` is all-`False` for every target | Present in current code but **inert by construction when the flag is unset** (never touched by D01/D02) — see D03 |

- Deviations: none (read-only reconstruction).
- Test status: n/a (documentation cross-check).
- Notes: the ONE real, load-bearing gap found is the shipped default `IMPUTE_ML_METHOD_BY_TARGET` value
  (`missforest`, not `knn`) — T11.6's own driver never depended on the default (it always set the dict
  explicitly per method in its sweep), so this is not a regression, but it is a real trap for any new,
  ad-hoc reproduction script that assumes "the `ml` tier with `enabled_tiers` containing `ml`" means knn.

#### D03 — Bisect the cause across the non-`imputation.py` surface — completed 2026-07-15
- Artifacts: `scratchpad/d01_repro.py`, `scratchpad/d01_repro2.py` (throwaway, isolated hypothesis tests,
  no `openubem/**` file touched); `git log --oneline --all -- openubem/semantic/imputation.py
  openubem/config.py openubem/semantic/spatial_impute.py` (all three cited to confirm the only touching
  commit is the squashed `0df422e`, 2026-07-03; `spatial_impute.py` has ZERO uncommitted changes and its
  last-touching commit `67ede73` predates T11.6 entirely — ruled out); `git diff HEAD -- openubem/
  config.py openubem/semantic/imputation.py openubem/validation/mask_recover.py` (full uncommitted diff
  read line-by-line, reproduced in D02 above).
- **Non-`imputation.py` surface checked and ruled out:** `spatial_impute.py` unchanged since before T11.6
  (commit `67ede73`, 2026-06-01 era). `config.py`'s uncommitted diff only *adds* new all-inert-by-default
  keys (`IMPUTE_DEBIAS_NEWERSKEW`, `FUSION_*`) and flips the *default* `IMPUTE_ENABLED_TIERS` tuple (adds
  `fusion`, a no-op fall-through per its own docstring) — neither is reachable when `enabled_tiers` is
  passed explicitly, which every faithful T11.6-style reproduction does. The 12 committed
  `01_buildings.gpkg` cells are git-clean (`git status --short` empty) and their pooled observed counts
  (2247/441) match §0/RESULTS_phaseC.md exactly (already confirmed in D01) — ruled out as a data-drift
  cause.
- **`imputation.py`'s own uncommitted diff (`_clamp_to_observed_range` + T11.8/T11.8b debias hook)
  proven INERT on the standard knn path, two independent ways:**
  1. **Analytically:** `_clamp_to_observed_range` (imputation.py:279) clips to
     `[target_observed_min, target_observed_max] = [min(train_y), max(train_y)]` where `train_y` is the
     SAME complete-case target column the `KNNImputer` matrix family was fit on. `KNNImputer.transform()`
     for the matrix family (used for `knn` regression targets) imputes each missing cell as a
     distance-weighted average of the fitted TRAINING matrix's own neighbours' target values — a weighted
     average of values drawn from `train_y` is mathematically guaranteed to already lie within
     `[min(train_y), max(train_y)]`. The clamp cannot change a single prediction for this method/family.
     The debias hook (imputation.py:751) is gated behind `config.IMPUTE_DEBIAS_NEWERSKEW.get(attr)`,
     default `False` for every target — the block is skipped entirely unless a caller sets the flag, which
     no D01/D02 reproduction path does.
  2. **Empirically:** D01 already re-ran the byte-identical, never-edited T11.6 driver against the FULL
     current working tree (uncommitted diff included, nothing stashed or reverted) and got exact
     agreement with the committed leaderboard on every metric, every method. If the clamp/debias diff had
     any effect on the standard path, this re-run would have diverged from the 2026-07-03/07-14 numbers —
     it did not.
- **Bisection of what invocation pattern WOULD produce a worse-than-Phase-A knn number** (isolated,
  in-memory experiments only, no repo file touched — `scratchpad/d01_repro.py`/`d01_repro2.py`):
  - (a) *Default method not overridden* (`config.IMPUTE_ML_METHOD_BY_TARGET` left at its shipped
    `"missforest"` default while `enabled_tiers` includes `"ml"`) → `year_built` MAE **31.545** (worse
    than Phase-A, consistent DIRECTION with the reported drift, but not the reported magnitude/value).
  - (b) *Shared, not-reset `rng` object* passed across sequential Phase-A→knn calls, or across
    sequential year_built→levels calls → `year_built` MAE **44.9** / n_holdout **696** (n_holdout no
    longer matches the established 562 — falsifiable against §0's own "n_holdout=562 exact" fact, ruled
    out as the actual mechanism).
  - (c) *Both targets pooled into ONE `recover_pairs(continuous_targets=("year_built","levels"))` call*
    (collapses `complete_cases` to rows where BOTH are observed, n≈170, under `knn`'s 200-row floor) →
    Phase-A AND knn BOTH collapse to the identical wrong number (MAE 41.9, n=34) — falsifiable against
    §0's "Phase-A reproduces exactly, only knn diverges" (this mechanism breaks BOTH legs equally), ruled
    out.
  - (d) *Unreprojected pooling* (native per-city CRS, 3 different UTM zones) → hard `ValueError: Cannot
    determine common CRS for concatenation inputs` at `pd.concat` time — confirms §0's own note, ruled
    out as a silent-corruption mechanism (it fails loudly, not silently).
  - **None of (a)-(d) reproduces 27.82/10.10 exactly while ALSO preserving both invariants the original
    investigation itself reported (Phase-A exact AND n_holdout exact).** (a) is the closest directional
    match (worse-than-Phase-A, real, easy-to-make caller mistake) but does not hit the exact reported
    number either.
- **The original figures-follow-up script that produced 27.82/10.10 no longer exists anywhere in the
  repository.** `openubem/results/impute_scatter.py`'s module docstring (lines 24-38) is the ONLY
  surviving record of the attempt ("knn ~27.8-28.1 across several feature-set variants... referencing a
  'T09-CC report' for the full diagnostic") — a targeted repo-wide grep for `T09-CC`, `feature-set / CRS
  / clamp isolation`, and the literal numbers `27.8`/`28.1` found no such report, no such driver script,
  and no progress-log entries for T09/T10/T11 in `PLAN_figures_implementation.md` (its §8 progress log
  stops at "CP-F1 + CP-F2 audited & SIGNED", before Follow-up round 2 / T08-T12 even begins). The
  generating script was evidently run ad hoc, never saved to `scratchpad/`, and never logged.
- Test status: n/a (isolated in-memory experiments, no pytest changes); `pytest tests/test_mask_recover.py
  -q` → **25 passed** (see below), confirming the harness itself (including the new `recover_pairs`
  tests) is fully green and unmodified in behaviour.
- Notes: repo working tree left exactly as found — no `openubem/**`, `tests/**`, or data file was edited
  by this investigation; only this debug plan doc's §5 was appended to, and two throwaway scratch scripts
  were added under `scratchpad/` (`d01_repro.py`, `d01_repro2.py`) alongside the pre-existing, unedited
  `t11_cp3_leaderboard_results.json`/`.log` which were merely re-run (content unchanged, only regenerated).

#### D04 — Classified verdict + recommendation — completed 2026-07-15
- **Verdict: (c) harness/invocation subtlety in the (lost) prior reproduction script — NOT a code
  regression, and NOT non-reproducible-from-committed either.** The current production code — including
  every uncommitted change (`_clamp_to_observed_range`, the T11.8/T11.8b debias hooks, the T12 fusion
  tier, the `IMPUTE_ENABLED_TIERS` default flip) — reproduces the committed `RESULTS_phaseC.md` leaderboard
  **exactly** (25.141/8.388, matching 25.14/8.39 to 3 decimals) when exercised via the documented protocol,
  proven two independent ways (re-running the untouched original driver verbatim, and an independent
  `recover_pairs`-based script). 25.14 IS reproducible from the current committed+uncommitted state —
  the "27.82 ≠ 25.14" premise in this plan's §0 does not hold up under an independent, from-scratch
  reproduction.
- **Evidence summary:** D01 — exact match on both Phase-A and knn, all metrics, both targets. D02 — every
  knn-affecting parameter (family, KNNImputer hyperparameters, spatial-lag, feature set, floor) is
  byte-identical between the 2026-07-03 documentation and current code, cited by line. D03 — the
  uncommitted diff is proven inert on the standard path both analytically (clamp is a mathematical no-op
  for a weighted-neighbour-average estimator; debias hook is default-off/gated) and empirically (verbatim
  re-run matches); the only concretely-reproducible way to GET a worse-than-Phase-A "knn" number is a
  caller mistake — most plausibly forgetting to set `config.IMPUTE_ML_METHOD_BY_TARGET[target]="knn"`
  before calling (shipped default is `"missforest"`), or reusing a single `rng` object across sequential
  calls instead of freshly seeding `np.random.default_rng(RANDOM_SEED)` per call as `t11_cp3_leaderboard.
  py::run_one` deliberately does.
- **No fix is proposed or applied because none is needed** — there is nothing to revert in
  `openubem/**`; the production `ml`/`knn` path is unregressed and matches its own documentation exactly.
- **Recommendation to the manager (not applied):** when T11 (`phaseC_scatter_year_built.png` /
  `phaseC_scatter_levels.png`) is re-attempted, instruct the executor to call `recover_pairs` PER TARGET
  (never combining `continuous_targets=("year_built","levels")` in one call — that alone collapses the
  complete-case pool below the knn floor) with a FRESH `np.random.default_rng(RANDOM_SEED)` passed to
  EVERY call (never a shared/reused rng object across Phase-A-vs-knn or cross-target calls), and with
  `config.IMPUTE_ML_METHOD_BY_TARGET[target] = "knn"` set explicitly before each call (the shipped default
  is `"missforest"`, not `"knn"`) — mirroring `scratchpad/t11_cp3_leaderboard.py::run_one` exactly. Cite
  this debug report (D01's exact-match result) as proof the cross-check gate WILL pass once the
  reproduction script itself is written correctly. No `RESULTS_phaseC.md` edit, no doc caveat, and no
  retirement of the Phase-C scatter figures are warranted — the committed 25.14/8.39 numbers stand as
  reproducible.
- Test status: `pytest tests/test_mask_recover.py -q` → **25 passed, 0 failed** (green, as required by
  the kickoff).
- Notes: this reframes the CP-D1 question from "why did the number move" to "the number never moved" —
  the apparent regression was an artifact of an ad hoc, unsaved reproduction attempt, not of any commit or
  uncommitted change to `openubem/**`. Recommend the manager also note, separately from this diagnosis,
  that `openubem/semantic/imputation.py` + `openubem/config.py` + `openubem/validation/mask_recover.py`
  currently carry substantial UNCOMMITTED changes (T11.8/T11.8b de-bias corrector, T12 fusion tier
  ship, T09 `recover_pairs`) sitting on top of the single squashed `0df422e` commit — orthogonal to this
  diagnosis's verdict, but worth flagging since git-based auditing of `imputation.py` will keep hitting
  the "single squashed commit, nothing after" wall until these are committed.
