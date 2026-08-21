# MEASUREMENT — OPEN-15 / OPEN-16 / OPEN-17: the imputation-tier decision brief

**Task:** N10, `PLAN_no-compute-queue-2.md` §6. **Read at:** git HEAD `bca92d0a6cdc33923bea8424f1b86ab0f94d82d9`
(2026-08-05), single local branch `main`, tracking `origin/main`, working tree clean for every file cited
below (`git status --short -- <path>` empty in every case checked). **Document assembly and code-state
verification only — nothing was run, fitted, or imputed to produce this brief.**

> **This document assembles a decision. It does not take one, and it does not recommend one.** Every
> "what it would cost" section below is a description of mechanism, not an argument for or against.

---

## 0. The one decision behind three register items

Register §5, verbatim: *"These are one decision, not three: **does this project want a non-deterministic
input tier at all?**"* (`docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md:948`). The three
items are OPEN-15 (Phase E frontier methods), OPEN-16 (`ml` tier), OPEN-17 (`draw` tier) — three rungs of
the same imputation arc, all currently off, all requiring the same underlying ruling before any one of
them could move.

**A fact load-bearing enough to state before any of the three, because it changes what "turning on" means
for all three:** the router that hosts fusion/spatial/ml/statistical/(draw) — `impute_missing()` in
`openubem/semantic/imputation.py:889` — is **not called anywhere in the production Stage-2 pipeline**.
`enrich_semantics()` (`openubem/semantic/__init__.py:273`) resolves vintage via `resolve_vintage()`
(`openubem/semantic/construction_sets.py:126`, imported at `openubem/semantic/__init__.py:17`, called at
`:305`) — a separate, older, monolithic fallback chain, not `impute_missing`. Confirmed by grep: neither
`construction_sets.py` nor `building_classifier.py`'s `_impute_levels()` (`:123`) call `impute_missing`,
`_fusion_tier`, `_ml_tier`, `_spatial_tier`, or `_statistical_tier` anywhere. `impute_missing()`'s own
docstring states this is deliberate, not a gap: *"Does **not** reroute `enrich_semantics` (T07 PINNED
CONTRACT scope boundary) — this is a new entry point for the T08/T09 validation harness to call directly"*
(`openubem/semantic/imputation.py:900-902`). Every caller of `impute_missing` repo-wide is a
validation/test module (`openubem/validation/mask_recover.py`, `openubem/validation/eui_impact.py`,
`openubem/results/draw_leaderboard.py`, `openubem/results/impute_scatter.py`, and the `tests/` suite) —
**none is the production fleet pipeline.**

**Consequence for every "cost to turn on" question below:** flipping any config default inside the
`impute_missing` router changes what the *validation harness* measures. It does **not**, by itself, change
a single value in an actual fleet run (`05_results.gpkg`), because production never calls that router.
Making any of these three tiers affect an actual fleet result would additionally require the
`enrich_semantics` reroute — itself a separate, deferred, unscoped task (recorded in project memory as
`enrich_semantics` reroute — "would break CP-1 byte-identity" — never attempted). This is true even for the
tiers already described elsewhere as "shipped enabled-by-default" (fusion/spatial/statistical): that
default lives inside the harness's `IMPUTE_ENABLED_TIERS` tuple
(`openubem/config.py:100`), not inside the production call graph.

---

## 1. OPEN-15 — Phase E (deep-generative / GNN / LLM / TabPFN frontier)

**What was built.** Nothing executable. Phase E is documentation-only by its own header:
*"Phase E is **documentation, not execution**"* (`docs/docs_DONE/INPUTS/imputation/results/phase_E/RESULTS_phaseE.md:16`).
No frontier-method code exists in `openubem/` — a repo-wide search for `TabPFN`/`GAIN`/`MIWAE`/`TabDDPM`/
`SpatialGNN` returns exactly one hit, a plot-label string (`"TabPFN": "NOT READY"`) in
`openubem/results/impute_figures.py:186`, not a code path.

**Current switch state: unreachable — there is no switch.** Not opt-in, not off-by-default: there is
nothing in `openubem/` to opt into. The four families were evaluated and ruled out/quarantined entirely
in documentation.

**The document that deferred it, and its reason (quoted).** `RESULTS_phaseE.md:1-5,35-42`: deep-generative
methods fail the **data-scale filter** (need n≈10k-30k+; OpenUBEM cells are hundreds to low-thousands);
spatial GNN fails the **zero-fitted-parameters filter** (adds thousands of fitted weights — "the spatial
signal is already captured" by the neighbour-vote/kNN tier folded into Phase A, at zero fitted weights);
LLM fails reproducibility/provenance and is disqualified on **hallucination risk**; TabPFN alone passes
the first three filters (zero-fitted-params via synthetic-SCM prior, reproducible, provenance-emitting)
but is ruled **"NOT READY"** — *"no peer-reviewed study validating zero-shot foundation-model imputation
for building attributes in a physics-based UBEM"* (`RESULTS_phaseE.md:40`) — permitted only as an isolated,
non-default experimental track, never built.

**Evidence for/against.** For: none of the four families has been implemented or tested against this
project's data — the ruling is a literature-based admissibility screen, not a measured result on
OpenUBEM's own buildings. Against: the arc's own closing argument (`RESULTS_phaseE.md:48-55`) is that
Phase A/B already recover `year_built` near-perfectly on real cities (NYC +0.49%, LA +0.08% NMBE) and
Phase C's classical-ML tier, the "smarter recovers better" test one rung down from Phase E, already found
no attribute-accuracy headroom worth the do-no-harm risk (see §2 below) — so there is little EUI-shaped
motivation on record for reaching further up the complexity ladder.

**What it would cost to turn on.** There is nothing to turn on; turning any Phase-E family on would mean
building it from zero — a full implementation task, not a config flip, and (per §0) would additionally
need the `enrich_semantics` reroute before it could touch a real fleet run.

---

## 2. OPEN-16 — the `ml` tier

**What was built (`path:line` at HEAD).** A 6-method classical-ML imputer registry (`missforest`, `mice`,
`knn`, `rf`, `histgbm`, `linear`) wired into the `impute_missing` router:
- `_ml_tier()` — `openubem/semantic/imputation.py:685`
- registered in `_TIER_HANDLER_NAMES["ml"] = "_ml_tier"` — `openubem/semantic/imputation.py:885`
- included in `_CANONICAL_TIER_ORDER = ("fusion", "spatial", "ml", "statistical")` — `openubem/semantic/imputation.py:543`
- per-target method override, read lazily via `getattr(config, "IMPUTE_ML_METHOD_BY_TARGET", {})` —
  `openubem/semantic/imputation.py:674`, default table at `openubem/config.py:105-111`
- per-method complete-case floors, read lazily via `getattr(config, "IMPUTE_ML_FLOORS", _ML_FLOORS)` —
  `openubem/semantic/imputation.py:414`, default table at `openubem/config.py:112-119`

**Current switch state — verified in code, not carried from the register.** `ml` is **absent** from the
default `IMPUTE_ENABLED_TIERS = ("fusion", "spatial", "statistical")` (`openubem/config.py:100`) — so the
default `impute_missing()` call never touches it. It **is** reachable, but only two conditions removed
from a real fleet run: (1) an explicit caller of `impute_missing()` must pass
`ImputeConfig(per_input_tiers={"<target>": ("spatial", "ml", "statistical")})` (or similar) — mechanically
possible today, no missing code; **and** (2) per §0, that caller must be the validation harness, because
`enrich_semantics` never calls `impute_missing` at all. **The register's phrase "permanently off" is
stronger than what the code shows: the tier is off-by-default-but-code-reachable inside the harness, and
entirely unreachable from the production pipeline regardless of any config value**, since production
doesn't call the router that hosts it.

**Evidence for and against — the reattribution, and a live document disagreement.**
Two committed documents give different headline verdicts for the same number, and this brief reports both
rather than picking one (§2 rule 13 of the governing plan):
- `docs/docs_DONE/INPUTS/imputation/results/phase_C/RESULTS_phaseC.md:41,98` (status header:
  **"CLOSED"**, no date given on the file itself beyond the arc's general 2026-07 timeframe): **NMBE
  −5.51% FAILS** the do-no-harm gate (\|NMBE\| < 5%); CV(RMSE) 7.93% PASSES; verdict recorded as "kept
  built-but-off" on the basis of this failing NMBE leg.
- `docs/docs_DONE/INPUTS/imputation/docs_Done/PLAN_phaseC_ml_imputer.md:39-43,680-708`, dated **2026-07-14**
  (later than the file above): the same −5.51% figure is **reattributed** as a **pooled-evaluation
  granularity artifact**. Production imputes per-cell; `knn`'s complete-case floor (≥200) cannot be
  cleared by `nyc_centre` alone (158 obs), so the original CP-3 measurement pooled all 12 cities to fit,
  then scored on `nyc_centre` — a cell that in real per-cell production would never reach `knn` at all. A
  follow-up diagnostic (T11.8c-diag, `:687-696`) re-ran `knn` at true per-cell granularity on two
  floor-clearing cells (`la_suburban`, `la_urban`): **directional vintage-bin gap = 0/1343 and 0/618
  divergent rows — exactly 0.0000 on both.** Since EUI flows through the vintage bin, zero divergence means
  identical EUI by construction. Terminal finding (`:700-701`, 2026-07-14): **`ml`-`year_built` at
  production granularity is EUI-neutral — do-no-harm *and* do-no-good** — kept off because there is no
  benefit case, not because it harms. **This brief does not adjudicate which document is the current
  status; it reports that they disagree and gives both dates.**

**What it would cost to turn on.** Per-target, mechanically: point `config.IMPUTE_ML_METHOD_BY_TARGET` at
a target and add `"ml"` to that target's enabled tiers for a caller of `impute_missing()` — no missing
code. To affect an actual fleet result: the `enrich_semantics` reroute (§0) would need to exist first;
that reroute is recorded in memory as deferred specifically because it "would break CP-1 byte-identity"
and has never been scoped or attempted.

---

## 3. OPEN-17 — the `draw` tier

**What was built.** Six pure, zero-fitted-parameter draw/resampling functions exist and are registered:
`openubem/semantic/draw_methods.py` — `DRAW_METHODS` registry (`:56`), `kde` (`:129`), `pmm` (`:217`),
`hotdeck` (`:298`), `resid` (`:359`), `catfreq` (`:454`), `abb` (`:513`). These are real, tested, importable
functions.

**Current switch state — verified in code, and this is the load-bearing finding of this brief.**
`draw_methods.py`'s own module docstring states the tier is reached *"by nothing in the default
`impute_missing` call graph until a future task (T07) wires `_draw_tier` into
`openubem/semantic/imputation.py`'s `_CANONICAL_TIER_ORDER` / `_TIER_HANDLER_NAMES`. Until then, importing
this file or setting `config.IMPUTE_DRAW_METHOD_BY_TARGET` has zero effect"* (`draw_methods.py:5-9`). At
HEAD, **that wiring does not exist**:
- `openubem/semantic/imputation.py` (966 lines, read in full): `_CANONICAL_TIER_ORDER = ("fusion",
  "spatial", "ml", "statistical")` (`:543`) — **no `"draw"` entry.** `_TIER_HANDLER_NAMES` (`:881-886`)
  holds exactly `{"fusion", "spatial", "statistical", "ml"}` — **no `"draw"` key, no `_draw_tier` function
  anywhere in the file** (confirmed: a case-insensitive search for `draw` in the entire file returns one
  unrelated docstring word, `imputation.py:906`).
- `openubem/config.py` (163 lines, read in full): **`IMPUTE_DRAW_METHOD_BY_TARGET` is not defined
  anywhere.**
- `git log --all -p -- openubem/config.py | grep IMPUTE_DRAW_METHOD_BY_TARGET` and the equivalent search
  on `openubem/semantic/imputation.py` for `_draw_tier` both return **zero hits, across every commit on
  every branch** (repo has one local branch, `main`, tracking `origin/main`).

Yet `openubem/results/draw_leaderboard.py:174,176,181-182,190,193,197-198` and
`openubem/results/impute_scatter.py:235,237,243-244` reference `config.IMPUTE_DRAW_METHOD_BY_TARGET`
directly (not via `getattr`), and `tests/test_draw_methods.py:75` asserts
`config.IMPUTE_DRAW_METHOD_BY_TARGET == {}` as a bare attribute access. **As committed at HEAD, any of
these code paths would raise `AttributeError` if executed**, because `openubem.config` has no such
attribute. This brief does not run them to confirm the traceback (running code is out of scope for this
task) — the absence is established statically, by reading the complete file and its complete git history.

**This directly contradicts the arc's own closing sign-off.** The archived implementation record
(`docs/docs_DONE/INPUTS/imputation/implementation/IMPLEMENTATION_phaseC_ml_imputer.md:849-857`) has a
progress-log entry, **"T07 — wire `_draw_tier` + registry + order — completed 2026-07-16,"** claiming
exactly this wiring was added (`_CANONICAL_TIER_ORDER → ("fusion","spatial","ml","draw","statistical")`,
`_TIER_HANDLER_NAMES` gains `"draw"`) and that `pytest tests/test_draw_methods.py -q` passed 53/53
afterward; the manager audit entry at `:1206-1243` (dated 2026-07-16) independently re-asserts
`IMPUTE_DRAW_METHOD_BY_TARGET == {}` as a passing runtime check. **Two possibilities, and this brief
reports both without adjudicating which: either the T07 commit was never actually merged to the branch
this repository now serves from, or it existed at the time of that audit and was later reverted by a
commit that touched neither file's substantive content in a way `git log -S` would miss (not found in
search — no such commit exists in history for either file, on either search term).** What is certain,
because it was read directly rather than inferred: **the wiring is absent from the file at HEAD, and has
never existed in the git history of either file, on the only branch this repository has.**

**Consequence for "current switch state": not opt-in/off — unreachable, and possibly non-functional in the
committed test suite if it were run.** The register's and memory's shared description — "6
variance-preserving draw-tier imputers built opt-in/OFF... awaiting a promotion decision" — describes a
tier that is reachable-but-declined. What is actually on disk at HEAD is a tier whose component functions
exist and are presumably individually correct (each is a standalone pure function, importable and
testable on its own), but whose **router-level integration is missing**, contradicting the arc's own
2026-07-16 closure record.

**Evidence for/against (as recorded, independent of the wiring gap above).** The CP-DRAW leaderboard (§4)
was run and its numbers are real — but per the `draw_leaderboard.py` code inspection above, the driver
script that produced them references a config attribute absent from the committed `config.py`. **This
brief cannot determine, by reading alone, whether `draw_leaderboard_results.json` was generated by a
version of the repository that had the T07 wiring in place at the time (later lost) or by some other
mechanism** — that determination would require re-running the driver, which this task is forbidden from
doing. The JSON and its host document are reported below as the arc's own record, with this uncertainty
stated plainly rather than silently trusted.

**What it would cost to turn on.** Under the arc's own account, "turn on" would have meant setting
`config.IMPUTE_DRAW_METHOD_BY_TARGET[target]` plus an `ImputeConfig.per_input_tiers` opt-in. **Given the
finding above, that account does not match what is on disk now** — before anything could be "turned on,"
the T07 wiring itself would first need to be (re-)written and (re-)verified against
`tests/test_draw_methods.py`'s existing assertions (which already encode the expected post-wiring shape,
e.g. `:56-57`'s `_CANONICAL_TIER_ORDER`/`_TIER_HANDLER_NAMES` expectations). This is a code-restoration
task, not a flag flip — on top of the same `enrich_semantics` reroute cost described in §0 that would
still separately gate any effect on an actual fleet run.

---

## 4. The CP-DRAW leaderboard, reproduced in full

**Source artifact:** `openubem/outputs/draw_leaderboard_results.json` (3,285 lines; not re-executed for
this brief — read as committed). Companion narrative table committed at
`docs/docs_DONE/INPUTS/imputation/implementation/IMPLEMENTATION_phaseC_ml_imputer.md:1091-1114`, which this
brief reproduces verbatim below (the JSON is the machine-readable source; this table is the arc's own
human-readable rendering of the same numbers, cross-checked against the JSON's `pooled` block for the
values spot-checked — `year_built` baseline MAE 26.43/hotdeck MAE 26.47, `levels` baseline MAE 9.18/pmm
variance_ratio 0.902, `height_m` baseline variance_ratio 0.088 — all match the JSON exactly).

**Real column names, as they appear in the JSON's `pooled` block** (per continuous target, per leg —
baseline or one of the 5 non-categorical methods): `mae`, `rmse`, `ks_stat`, `wasserstein`, `n`,
`variance_ratio`, `iqr_ratio`, `energy_distance`, `variance_ratio_ci90` (a 2-element CI), `nmbe_proxy_pct`,
`do_no_harm_mae_pass`, `eligible_primary`, `priority_rank` — plus `n_complete_cases`/`n_holdout` at the
target level and a `noise_floor` sub-block (`wasserstein`/`energy`, each with `floor_mean`, `floor_median`,
`floor_p90`, `n_splits`, `n_observed`). For the categorical target (`function_tag`, substituting for
`use_class` — deviation (1), `IMPLEMENTATION_phaseC_ml_imputer.md:1062-1065`): `pfc`, `log_loss`, `n`, `tv`,
`do_no_harm_pfc_pass`, `eligible_primary`, `priority_rank`. A separate `joint_energy_distance` block
(`levels_height_m` key) holds `n_complete_cases`, `n_holdout`, `baseline_joint_energy_distance`, and a
`methods` dict of five scalars.

**Row count.** The JSON has two top-level halves: `pooled` (the leaderboard proper) and `per_cell` (12
cells' worth of the same structure, many entries replaced by an `"insufficient_data (n_observed=N < floor
30)"` string rather than a metrics dict when `PER_CELL_MIN_N=30` is not cleared — 17 of 36 continuous
cell×target combinations are exactly this, per `IMPLEMENTATION_phaseC_ml_imputer.md:1140-1143`). The
**pooled leaderboard table** reproduced below has **20 data rows** (3 continuous targets × 6 rows each
[baseline + 5 methods] = 18, + 1 categorical target × 2 rows [baseline + catfreq] = 2) **plus 1 summary
row** for the joint `(levels, height_m)` energy-distance bonus check (baseline + 5 methods condensed to
one line in the source table) = **21 lines in the pooled table as committed.**

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

**The plain-reading summary the arc itself drew, quoted, not endorsed:** *"No method dominates on every
axis; the choice is target-dependent."* `hotdeck` is do-no-harm-safe (95% pass rate, per
`IMPLEMENTATION_phaseC_ml_imputer.md:1188-1195`) but restores the least variance (mean ratio ~0.54);
`pmm`/`resid` restore variance/covariance best (joint energy distance 14.28→2.07) but fail do-no-harm on
`levels` and overshoot variance on `height_m` (ratio 2.5, MAE 3× baseline).

**Caveat on provenance (repeated from §3):** this brief cannot confirm, by static reading alone, that the
script which produced this JSON is executable against the `imputation.py`/`config.py` committed at HEAD
today, because the config attribute it depends on (`IMPUTE_DRAW_METHOD_BY_TARGET`) does not exist in
either file at HEAD or anywhere in their git history.

---

## 5. The zero-fitted-parameters guarantee — what it means here, and what would touch it

**The guarantee's own operative definition, quoted from the imputation arc itself**
(`docs/docs_DONE/INPUTS/imputation/results/phase_E/RESULTS_phaseE.md:24`): *"Zero-fitted-parameters —
never tuned against an EUI (or any downstream) target. Non-negotiable across the whole project."* This is
narrower than a plain-English reading of "no model ever fits a parameter to data" — it specifically means
no parameter is **tuned against the downstream EUI target**.

**Per tier, under that operative definition:**
- **Phase E (frontier):** not applicable — nothing exists to promote (§1).
- **`ml` tier:** the six estimators (`missforest`/`mice`/`knn`/`rf`/`histgbm`/`linear`) do fit statistical
  parameters (tree splits, regression coefficients, kernel weights) **to the observed input features**
  — but per the arc's own closing record (`docs/docs_DONE/INPUTS/imputation/docs_Done/PLAN_phaseC_ml_imputer.md:701`),
  none of that fitting is against EUI; `TestNoEUILeakage` (`IMPLEMENTATION_phaseC_ml_imputer.md:140`, a
  structural `__code__.co_names` guard) exists specifically to make an EUI-referencing fit
  structurally impossible. **Under the arc's own narrow definition, turning `ml` on would not touch the
  guarantee.** Under a plainer reading of "zero fitted parameters" as meaning zero fitted model
  coefficients anywhere in the pipeline, turning it on plainly **would** introduce fitted parameters that
  do not exist in the shipped default path (which uses only group-median/mode fallbacks and neighbour
  votes, none of them fit in the statistical-model sense). **This brief states both readings and does not
  choose between them** — which reading governs is exactly the kind of question the plan says only the
  user can settle.
- **`draw` tier:** the arc's own label for these methods is *"6 zero-fitted-params draw methods"*
  (project memory, `project_variance_preserving_draw_arc.md`). Four of the six (`pmm`, `hotdeck`, `resid`,
  `abb`, `catfreq`) draw or resample directly from observed values with no fitted coefficients; `kde`
  fits a kernel bandwidth, which is a plug-in statistical rule rather than a target-tuned parameter.
  **None of the six is tuned against EUI** by the same `TestNoEUILeakage`-style structural guard
  documented for the tier (`IMPLEMENTATION_phaseC_ml_imputer.md:897-903`, `TestNoEUILeakage` under T08).
  Under either reading (narrow or plain), the draw tier's individual methods do not appear to touch the
  guarantee — **but per §3, the tier is currently unreachable regardless**, so this is a statement about
  the component functions, not about a tier that can currently be switched on.

**If you cannot tell, say so — stated plainly:** whether "zero fitted parameters" as the user has stated
it elsewhere means the narrow EUI-tuning definition the arc itself uses, or the broader "no fitted model
coefficients anywhere" reading, **is not determinable from any document read for this brief.** Both
readings are internally consistent with different documents in this repository; nothing found resolves
which one the guarantee was originally meant to enforce.

---

## 6. The decision, stated as a question with consequences — no recommendation

**The question, verbatim from the register:** does this project want a non-deterministic input tier at
all, for any of missing `year_built` / `levels` / `height_m` / `use_class`?

**If the answer is yes**, for any of the three items above, the concrete prerequisites are, in order:
1. For `draw` specifically: the T07 router wiring must first be (re-)written — it is not merely off, it
   does not exist at HEAD (§3).
2. For any of the three to touch a real fleet run at all: the `enrich_semantics` reroute (§0) must be
   built — a task never scoped, explicitly deferred, and recorded as risking the CP-1 byte-identity
   guarantee that keeps the current default pipeline provably unchanged from its validated baseline.
3. A ruling on which reading of "zero fitted parameters" governs (§5), since the `ml` tier's answer
   depends on it.

**If the answer is no**, the register can close OPEN-15/16/17 as a standing decision not to pursue
non-deterministic imputation, and the `draw` tier's missing wiring (§3) can be recorded as moot rather than
as an open defect to fix.

**What becomes undecidable either way:** whether `draw_leaderboard_results.json` (§4) was ever produced by
code that matches what is committed at HEAD, since the config attribute its own driver depends on has
never existed in this repository's history on this branch (§3). That question is not resolved by this
brief and would require either locating the commit/branch that produced it, or re-running the driver —
both out of scope for a measurement-only task.

---

## How to test — results

**(a) Each of the three items carries a HEAD `path:line` for its code and a document citation for its
evidence.** PASS — see §1 (Phase E: `RESULTS_phaseE.md`, no code), §2 (`ml`: `imputation.py:685,885,543`,
`config.py:100,105-111,112-119`; evidence `RESULTS_phaseC.md` + `PLAN_phaseC_ml_imputer.md`), §3 (`draw`:
`draw_methods.py:56` registry + per-method line numbers; wiring absence confirmed against
`imputation.py`'s full 966 lines and `config.py`'s full 163 lines, plus `git log --all -p -S` on both
search terms).

**(b) The CP-DRAW leaderboard is reproduced with its real column names and row count stated.** PASS —
§4: column names listed exactly as they appear as JSON keys; row count stated as 20 pooled data rows + 1
joint-bonus summary row = 21, with the caveat that the underlying JSON also carries a `per_cell` block for
12 cities not fully reproduced here (referenced, not tabulated).

**(c) The brief contains zero recommending sentences — reread and confirm explicitly.** Confirmed by
re-reading this document in full after drafting: every "what it would cost" and "evidence for/against"
section states mechanism and record only; §5 and §6 explicitly decline to choose between competing
readings/outcomes; no sentence anywhere advises turning any tier on or off, adopting one metric definition
over another, or trusting one of the two disagreeing OPEN-16 documents over the other.

**(d) The NMBE/variance-collapse constraint appears with its measured 0.06-0.31 range.** PASS — §4's
leaderboard table shows the three baseline `variance_ratio` values directly: `year_built` 0.064, `levels`
0.314, `height_m` 0.088 — i.e., the 0.06-0.31 range is these three exact numbers, re-derived from
`draw_leaderboard_results.json`'s `pooled.continuous.<target>.baseline.variance_ratio` fields, not carried
from the register as a pre-summarized range.
