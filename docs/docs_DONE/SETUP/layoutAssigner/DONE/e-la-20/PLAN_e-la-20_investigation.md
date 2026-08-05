# LayoutAssigner — E-LA-20 Root-Cause Investigation Plan (v1.0)

**Slug:** layout-assigner-e-la-20-investigation · **Date:** 2026-07-24 · **Binding contract:** this plan + the E-LA-20 and CP-E entries in the CLOSED structural-fixes plan's own error/progress log (`docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/structural-fixes/PLAN_structural-fixes_implementation.md`, lines 559-586, dated 2026-07-24). Executor: a fresh Sonnet session, or an autonomous director session per `prompt/DIRECTOR_PROMPT_e-la-20-investigation.md`. Manager: audits, never writes feature code.

## Executive Summary

The structural-fixes plan (CLOSED, CP-E signed **WITH CAVEAT** 2026-07-24) fixed all 4 of its targeted defects at fleet scale (E-LA-12, E-LA-11, E-LA-09/E-LA-13, E-LA-07-class-2/E-LA-08), but the E-LA-07-class-2/E-LA-08 fix — defaulting `thermal_mass=True` in `envelope_patcher.patch_envelope()` — directly unmasked a new, previously-invisible defect: **candidate E-LA-20**, a CTF calculation-convergence Fatal on `Construction="LA_ROOF_CONSTRUCTION"`, 100% concentrated in `nyc_rural` `SmallOffice` (150/154 buildings newly Fatal, 97.4% of that cell/archetype combination). This single failure mode costs more buildings (150) than the structural-fixes plan recovered across all 4 of its own fixes combined (64). It was invisible in every local retest sample across both the debug-fixes and structural-fixes plans (≤28-building samples each) and surfaced only via the full T11 12-cell/8,160-building cluster harvest.

**This plan is investigation-only.** It root-causes E-LA-20 with real local EnergyPlus reproductions before any fix is designed or implemented — mirroring how the debug-fixes plan investigated (but deliberately did not fix) E-LA-11/E-LA-07-class-2/E-LA-09 before those became the structural-fixes plan's own pre-decided, cited fix designs. This plan does **not** implement a fix and does **not** touch `openubem/` production code. It ends at a single manager checkpoint (CP-INV) where the findings are synthesized and candidate fix shapes are proposed for a follow-up implementation plan — that follow-up plan is new scope, authored later, not by this plan or its executor.

**Explicitly out of scope:**
- Implementing any fix to `envelope_patcher.py`, `builder.py`, or `layout_assigner.py`. Diagnostic-only probes on copies are allowed (I05); production code is not touched.
- Re-investigating E-LA-11, E-LA-09/E-LA-13, E-LA-07-class-2/E-LA-08, or E-LA-12 — all CLOSED, verified fixed at fleet scale, unchanged disposition.
- E-LA-14/E-LA-19 (`CheckWarmupConvergence` prevalence) and E-LA-16 (`TallBuilding` residual gap) — already-logged, cosmetic/non-blocking or OPEN-BLOCKED, unchanged disposition, not touched here.
- Any cluster (`sbatch`) compute — this plan is entirely local-repro scale (≤30 real buildings), no fleet-wide re-sweep.

---

## 0. Status checklist (tick as you go)

> Executor: flip `[ ]` → `[x]` when a task's progress-log entry (§7) is written; use `[~]` for in-progress. The checkpoint is ticked by the **manager only**, after audit/synthesis.

- [x] **I01** — Reproduce E-LA-20 locally on a representative sample of the 150 affected `nyc_rural` `SmallOffice` buildings
- [x] **I02** — Isolate the mechanism: scaled-only vs. patched-without-thermal-mass vs. patched-with-thermal-mass, same buildings, to confirm `thermal_mass=True` is the actual trigger (not a confound)
- [x] **I03** — Characterize the numeric regime: correlate scale factor S and `u_roof_w_m2k` (and the material properties they drive) against pass/fail, across all 154 `nyc_rural` `SmallOffice` buildings plus a cross-cell `SmallOffice` control sample
- [x] **I04** — Determine why `nyc_rural` `SmallOffice` specifically — compare `u_roof_w_m2k`/scale-factor distributions across cells×archetypes to distinguish a genuine numeric outlier from an incidental concentration of extreme-S buildings
- [x] **I05** — Diagnostic-only mitigation probes (not a fix decision) to pre-vet candidate fix shapes for a future implementation plan
- [x] 🔶 **CP-INV** — investigation checkpoint: root cause confirmed (or best-evidence hypothesis), candidate fix shapes proposed (manager) — **investigated, findings recorded; plan stays OPEN, no fix implemented**

---

## 1. Hard rules for the executor

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** Never edit `main.py` at the project root. Never edit OVERVIEW/DESIGN docs or any CLOSED plan's own §7/§8 entries (`implementation_plan.md`, `debug/PLAN_debug_implementation.md`, `structural-fixes/PLAN_structural-fixes_implementation.md`) — all frozen historical records; cite them, do not edit them.
2. **No fix implementation, no scope creep.** This plan investigates only. Do not edit `openubem/geometry/envelope_patcher.py`, `openubem/geometry/layout_assigner.py`, or `openubem/idf/builder.py`. Diagnostic variant builds (I02, I05) must be done via explicit keyword-argument overrides at call time or scratch copies — never by changing a default or committing a production-code change. If a task reveals this investigation needs to touch a 4th mechanism not named here, STOP and report rather than freelancing.
3. **No `.py` files under `docs/`.** Any diagnostic scripts go under `scratchpad/` (session-local). Any comparison plots/tables produced for I03/I04 go to `openubem/outputs/` (flat) **and** `docs_ACTIVE/simulation-Resolution/layoutAssigner/e-la-20/figures/`.
4. **Never edit a raw baseline IDF file directly** (`C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231`) — shared infrastructure across every arc.
5. **Default to no comments** in any diagnostic script. One short line max when the WHY is genuinely non-obvious.
6. **No cluster compute of any kind for this plan.** All repro/diagnostic runs are local, real EnergyPlus 23.1, on individually-picked real buildings (≤30 total). If local hardware cannot keep up, reduce the sample size and say so — do not fall back to `sbatch`.
7. **Git handled externally** — never commit, never offer to.
8. **For any claim about a `.err`/`.eio` signature or a pass/fail outcome, quote the actual raw file text** — do not paraphrase or assume EnergyPlus's message from memory.
9. **This plan does not close.** It ends OPEN at CP-INV, handed back to the manager (a human-available session) for scoping a follow-up implementation plan. Do not mark §0 items "done" in the sense of "fixed" — only in the sense of "investigated, findings recorded."

## 2. File layout to create

```
docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/e-la-20/
├── PLAN_e-la-20_investigation.md   (this file)
└── figures/                        (I03/I04 diagnostic plots, if produced)
```

No new files under `openubem/` or `tests/` — this plan writes no production code or unit tests. Diagnostic scripts (I01-I05) live under `scratchpad/e-la-20-investigation/` and are not required to survive past this plan's own completion report (their outputs/findings are what matters, captured in §7).

## 3. Dependency decisions (pre-decided, do not re-debate)

1. **I01 must run before I02/I03/I04** — need a confirmed local repro before isolating mechanism or characterizing the regime.
2. **I02 gates I03/I04** — only characterize the numeric regime once `thermal_mass=True` is confirmed as the actual trigger (not a confound of "envelope patching in general" or "small S in general"). If I02 shows the pre-existing `thermal_mass=False` variant *also* fails, STOP per §6 — this would mean E-LA-20 predates the structural-fixes plan's own fix and the entire framing above is wrong.
3. **Building sample source:** pull real buildings from `openubem/outputs/comparisons/t19_layout_assign_eui.csv`, filtered to `cell=="nyc_rural" and archetype_id=="SmallOffice" and status!="success"` (150 rows after excluding the 2 known carryovers below). Use real buildings throughout — do not invent synthetic scale factors.
4. **Exclude 2 known-carryover exceptions** from every I01-I05 sample: `way/965718400` (already-logged E-LA-17, unrelated persistent-divergence signature) and `way/965718401` (already-logged E-LA-15, unrelated sizing-phase signature) — both confirmed via direct `.err` re-inspection in the structural-fixes plan's own E-LA-20 entry to retain their original, different signatures. Including them would contaminate the sample with two unrelated failure modes.
5. **I05's probes are diagnostic-only, never a fix decision.** Whichever probe(s) look most promising get written up as *candidate* fix shapes in the completion report for a future implementation plan's own §3 — this investigation does not implement, adopt, or partially wire in any of them.

## 4. Source-of-truth verified facts (manager-verified, cited)

- **Exact Fatal signature** (structural-fixes plan, E-LA-20 entry, lines 563-569), confirmed via a full 152-file programmatic `.err` scan, not a spot-check — 150/150 matching, 2/152 are the known carryovers above:
  ```
  ** Severe  ** CTF calculation convergence problem for Construction="LA_ROOF_CONSTRUCTION".
  **   ~~~   ** ...with Materials (outside layer to inside)
  **   ~~~   ** (outside)="LA_ROOF_ASSEMBLY"
  ...
  **  Fatal  ** Program terminated for reasons listed (InitConductionTransferFunctions)
  ```
  Fires during `InitConductionTransferFunctions`, before Warmup or Sizing begins (Elapsed Time ≈0.12 sec).
- **`patch_envelope()`'s roof-material assignment mechanism** (`openubem/geometry/envelope_patcher.py`):
  - Line 29: `_K = 0.12` (W/m·K, "light structural" constant).
  - Line 93-97: loop creates `LA_Roof_Assembly`/`LA_Wall_Assembly`/`LA_Floor_Assembly`, `r_val = 1.0 / float(row[u_col])` (line 98).
  - Lines 99-111: if `thermal_mass=True` → `MATERIAL` with `Thickness=max(0.01, r_val * _K)` (line 104), `Conductivity=_K` (line 105), `Density=800.0` (line 106), `Specific_Heat=1000.0` (line 107). If `False` → `MATERIAL:NOMASS` with `Thermal_Resistance=r_val` (line 117), no thickness/density/specific-heat at all.
  - Lines 122-126: `CONSTRUCTION` object `Name="LA_Roof_Construction"` (roof case), single `Outside_Layer` (single-layer construction — no multi-layer assembly).
  - **Note the material properties above are a function of `row["u_roof_w_m2k"]` only — the scale factor S does not appear anywhere in this function.** If the Fatal is genuinely correlated with small S (as the structural-fixes plan's E-LA-20 entry hypothesizes, "informational, not investigated further"), the causal path from S to the Fatal must run through something this plan has not yet confirmed — e.g. an interaction with the roof surface's own scaled dimensions (set elsewhere, in `layout_assigner.py`'s `_GEOMETRY_SURFACE_CLASSES` scaling), or the correlation may in fact be with `u_roof_w_m2k` itself (which could vary systematically by cell/archetype independent of S). **I02/I03/I04 exist specifically to resolve this — do not assume the "small S" framing is correct going in.**
- **Affected-building criteria and exact counts** (structural-fixes plan, CP-E entry, lines 579-582): 150/154 `nyc_rural` `SmallOffice` buildings newly Fatal in T19 vs. success in both T17 and T18; independently re-derived by the manager directly from the raw `t17_`/`t18_`/`t19_layout_assign_eui.csv` files via a `(cell, archetype_id, osm_id)` join — exact match to the employee's claimed count, zero discrepancy.
- **Raw harvest data available for this plan:** `openubem/outputs/comparisons/t19_layout_assign_eui.csv` (8,160 rows, includes `osm_id`, `floor_area_m2`, `status`, `has_fatal` columns per building) — use directly to build the I01/I03/I04 building lists. **Never overwrite this file or `t17_*`/`t18_*`** — this plan only reads them.

## 5. Task list

#### I01 — Reproduce E-LA-20 locally
- **What to do:** Build (via the real `layout_assign` path, envelope-patched, `thermal_mass=True` — today's actual default) and run real EnergyPlus 23.1 on a sample of at least 10 of the 150 confirmed-failing `nyc_rural`/`SmallOffice` buildings, chosen to span the full range of scale factor S present in that set (min, a few mid-range, max) — not just the first N rows of the CSV.
- **Why:** §4/Exec Summary — no prior local retest sample in either the debug-fixes or structural-fixes plan happened to include this exact cell+archetype+S combination (confirmed: T02/T04/T05/T10's samples were all ≤28 buildings and never covered `nyc_rural` `SmallOffice`). Must confirm the failure reproduces locally, in this codebase, before investigating further — not a cluster-environment-only artifact.
- **How:** Query `openubem/outputs/comparisons/t19_layout_assign_eui.csv` for `cell=="nyc_rural" and archetype_id=="SmallOffice" and status!="success"`, drop `way/965718400` and `way/965718401` (§3.4), sort by `floor_area_m2`/derive scale factor S the same way the sweep script does, pick the sample spanning that range. Build each locally through the normal `layout_assign` pipeline (same code path as the T19 cluster sweep — do not hand-construct IDFs).
- **How to test:** local `.err` for every sampled building shows the exact §4-cited signature (quote it, do not paraphrase); record each building's `osm_id`, floor_area_m2, derived S, and `u_roof_w_m2k` in the §7 entry.

#### I02 — Isolate the mechanism
- **What to do:** For 3-5 of I01's repro buildings, build three variants and run all three through real EnergyPlus: (a) scaled-only, no envelope patch at all (pre-envelope-patcher baseline envelope); (b) envelope-patched with `thermal_mass=False` explicitly (the pre-structural-fixes-plan behavior, `MATERIAL:NOMASS`); (c) envelope-patched with `thermal_mass=True` explicitly (today's default — the failing case, same as I01).
- **Why:** §3.2 — must confirm `thermal_mass=True` specifically (not "envelope patching" in general, not "small S" alone) is the proximate trigger before treating the structural-fixes plan's T03 fix as the causal driver.
- **How:** Call `envelope_patcher.patch_envelope(idf, row, thermal_mass=...)` directly with explicit overrides for variants (b)/(c) on the same scaled IDF — this is a read-only diagnostic call-site override, not a change to any default in `builder.py`.
- **How to test:** (a) and (b) are expected to complete successfully (matching pre-structural-fixes-plan/T18-era behavior); (c) is expected to reproduce the Fatal. **If (b) also fails, STOP per §6 immediately** — that would mean thermal_mass is not the sole trigger and the entire investigation framing needs to be revisited with the manager before continuing to I03/I04.

#### I03 — Characterize the numeric regime
- **What to do:** For all 154 `nyc_rural` `SmallOffice` buildings (150 failing + 4 passing) plus a cross-cell `SmallOffice` control sample (≥20 buildings from other cells, chosen to span a similar range of scale factor S), tabulate: S, `u_roof_w_m2k`, the resulting `r_val`/`Thickness`/`Conductivity`/`Density`/`Specific_Heat` per lines 98-107 of `envelope_patcher.py`, and pass/fail. Look for a numeric threshold or ratio (e.g., a minimum `Thickness`, a Biot-number-like `Density×Specific_Heat×Thickness / Conductivity` ratio) that separates pass from fail.
- **Why:** EnergyPlus's own diagnostic text (quoted in the structural-fixes plan's E-LA-20 entry) names "very thin, highly conductive materials" and "highly resistive layers alternated with high-mass layers" as known CTF-instability triggers — need the actual numbers to know whether this is a `nyc_rural` `SmallOffice`-specific `u_roof_w_m2k` outlier (would recur deterministically) or a generic small-S numeric edge case that could surface elsewhere later.
- **How:** Pull `u_roof_w_m2k` from the same Step-2 semantic-enrichment output `patch_envelope()` itself reads (per-building row); compute the derived material properties using the exact formulas at §4's cited lines. Do not re-derive S from scratch if it is already a column/derivable field in the T19 harvest CSV or the enrichment output — use the authoritative source.
- **How to test:** Produce a simple correlation table/plot (e.g., thickness or the Biot-like ratio vs. pass/fail) as a scratch diagnostic script (§2) — not a new production file. State plainly in §7 whether a clean numeric threshold emerged or not.

#### I04 — Why `nyc_rural` `SmallOffice` specifically
- **What to do:** Compare `u_roof_w_m2k` distributions for `SmallOffice` across all 12 cells, and for `nyc_rural` across all archetypes, to determine whether `nyc_rural` `SmallOffice` is a genuine numeric outlier (e.g., an unusually low or high `u_roof_w_m2k` relative to `SmallOffice` elsewhere) versus simply having a much higher concentration of extreme-S buildings than other cells' `SmallOffice` population.
- **Why:** 150/154 (97.4%) is a near-total wipeout of one specific cell/archetype combination, not a scattered tail — need to know if this is inherent to that cell's climate-zone/archetype semantic-enrichment output (would recur identically every time `layout_assign` is re-run) or an incidental concentration of extreme scale factors in this particular OSM population.
- **How:** Query the T19 harvest CSV / underlying semantic-enrichment output for `u_roof_w_m2k` and scale-factor (`floor_area_m2`-derived) distributions, grouped by `(cell, archetype_id)`.
- **How to test:** A comparison table/plot (scratch-only, §2) with enough summary statistics (median/min/max `u_roof_w_m2k` and S per group) to support a clear yes/no answer in §7 — do not leave this as "inconclusive" without at least reporting what was tried.

#### I05 — Diagnostic-only mitigation probes
- **What to do:** On 2-3 of I01's repro buildings, try the following as read-only diagnostic experiments — record pass/fail per probe, do **not** treat any probe as an adopted fix:
  (a) Split `LA_Roof_Assembly` into 2+ thinner sub-layers of the same total R-value/thermal mass, instead of one single-layer `MATERIAL`.
  (b) Where feasible without touching shared production code, test EnergyPlus's `HeatBalanceAlgorithm` set to `ConductionFiniteDifference` instead of the default CTF, scoped to a standalone diagnostic copy of the IDF (never changing the default for any other archetype/build).
  (c) A minimum-`Thickness` clamp higher than the current `max(0.01, r_val * _K)` floor, to test whether the current 0.01 m floor is itself part of the trigger for `nyc_rural` `SmallOffice`'s specific `u_roof_w_m2k` values.
- **Why:** Gives a future implementation plan pre-vetted candidate fix shapes to cite in its own §3 dependency decisions, mirroring how the structural-fixes plan's T06/T08 each had 2 pre-authorized candidates ready before that plan was even written — rather than starting the next plan from zero.
- **How:** All probes are manual diagnostic IDF edits on scratch copies, or explicit call-time parameter overrides — never a change to `envelope_patcher.py`/`builder.py`/`layout_assigner.py` themselves (§1.2).
- **How to test:** For each probe, on each of the 2-3 buildings: does the Fatal disappear? Record a simple pass/fail table in §7. Explicitly flag which probe(s), if any, look most promising and why — but do not recommend one as "the" fix; that decision belongs to the follow-up plan's own manager-authored task list.

## 6. Stop-and-report points

1. **After I02** — if the `thermal_mass=False` variant (b) also reproduces the Fatal, STOP immediately. This would falsify the "T03's fix is the trigger" framing this entire plan is built on and requires a manager decision on how to re-scope before I03/I04/I05 proceed (their designs assume I02 confirms thermal_mass as the trigger).
2. **After CP-INV** (final) — synthesis complete, handed back to the manager.

## 7. Progress log

#### I01 — Reproduce E-LA-20 locally — completed 2026-07-25
- Artifacts:
  - `scratchpad/e-la-20-investigation/i01/select_sample.py` (sample selection from t19 CSV)
  - `scratchpad/e-la-20-investigation/i01/all_150_with_S.csv` (all 150 rows with derived S, sorted)
  - `scratchpad/e-la-20-investigation/i01/sample_buildings.csv` (11-row sample selection)
  - `scratchpad/e-la-20-investigation/i01/build_and_sim.py` (real Step2+Step3 build + real EnergyPlus 23.1 run)
  - `scratchpad/e-la-20-investigation/i01/sample_meta_authoritative.csv` (per-building S/u_roof/derived material props, pipeline-authoritative values)
  - `scratchpad/e-la-20-investigation/i01/step3_manifest.csv` (real `run_step3` manifest for the sample)
  - `scratchpad/e-la-20-investigation/i01/sim_results.csv` (pass/fail per building)
  - `scratchpad/e-la-20-investigation/i01/run_log.txt` (full console log of the run)
  - `scratchpad/e-la-20-investigation/i01/work/step3/idfs/*.idf` (11 real generated IDFs)
  - `scratchpad/e-la-20-investigation/i01/way_<osm_id>/eplusout.err` (+ `.end`/`.eio`/etc, 11 dirs, real EnergyPlus 23.1 output)
- Deviations: none. S was derived using the pipeline's own authoritative formula — `real_area = footprint_area_m2 * derive_num_floors(row)` (the same `layout_assigner.assign_baseline_layout`/`builder.py` line 476 computation) and `layout_assigner.calculate_scaling_factor(real_area, baseline_area)` called directly (read-only import, no production edit) against the enriched Step-2 `gdf` row, rather than a hand-rolled approximation from the flat CSV alone — matches plan §5/I01 "How" instruction to use the pipeline's own authoritative values. `u_roof_w_m2k` was read directly from the same enriched `gdf` row `patch_envelope()` itself consumes.
- Test status: 11/11 sampled buildings reproduced the exact §4-cited Fatal signature (verified via direct `.err` re-read + grep, not paraphrase). Sample spans the true min (S=0.0428) to true max (S=2.7789) of the 150-row filtered set, with 9 intermediate points:

  | osm_id | floor_area_m2 | S (area_scale_ratio) | u_roof_w_m2k | derived Thickness (m) | pass/fail | `.err` signature |
  |---|---|---|---|---|---|---|
  | way/772627076 | 21.87 | 0.0428 (min) | 0.119 | 1.008403 | FATAL (repro) | CTF conv. problem, LA_ROOF_CONSTRUCTION, Fatal InitConductionTransferFunctions |
  | way/772627064 | 65.55 | 0.1283 | 0.119 | 1.008403 | FATAL (repro) | same signature |
  | way/772627041 | 94.91 | 0.1857 | 0.119 | 1.008403 | FATAL (repro) | same signature |
  | way/772627030 | 113.39 | 0.2219 | 0.119 | 1.008403 | FATAL (repro) | same signature |
  | way/772627037 | 127.21 | 0.2489 | 0.119 | 1.008403 | FATAL (repro) | same signature |
  | way/772627017 | 147.11 | 0.2879 | 0.119 | 1.008403 | FATAL (repro) | same signature |
  | way/772626981 | 171.11 | 0.3349 | 0.119 | 1.008403 | FATAL (repro) | same signature |
  | way/772627078 | 201.27 | 0.3939 | 0.119 | 1.008403 | FATAL (repro) | same signature |
  | way/772627020 | 262.71 | 0.5141 | 0.119 | 1.008403 | FATAL (repro) | same signature |
  | way/772627089 | 357.77 | 0.7001 | 0.119 | 1.008403 | FATAL (repro) | same signature |
  | way/270445755 | 1420.04 | 2.7789 (max) | 0.119 | 1.008403 | FATAL (repro) | same signature |

  Exact raw `.err` text (identical across all 11, e.g. `way/270445755` and `way/772627076`, both quoted verbatim):
  ```
  ** Severe  ** CTF calculation convergence problem for Construction="LA_ROOF_CONSTRUCTION".
  **   ~~~   ** ...with Materials (outside layer to inside)
  **   ~~~   ** (outside)="LA_ROOF_ASSEMBLY"
  ...
  **  Fatal  ** Program terminated for reasons listed (InitConductionTransferFunctions)
  ...Summary of Errors that led to program termination:
  ..... Reference severe error count=1
  ..... Last severe error=CTF calculation convergence problem for Construction="LA_ROOF_CONSTRUCTION".
  ```
  Real generated IDF `LA_Roof_Assembly` MATERIAL block (`way_270445755.idf`, lines 2220-2229), confirmed to match the formulas exactly (`u_roof_w_m2k=0.119` → `r_val=8.4034` → `Thickness=max(0.01, 8.4034*0.12)=1.008403`):
  ```
  MATERIAL,
      LA_Roof_Assembly,         !- Name
      MediumRough,              !- Roughness
      1.0084033613445378,       !- Thickness
      0.12,                     !- Conductivity
      800,                      !- Density
      1000,                     !- Specific Heat
      0.9,                      !- Thermal Absorptance
      0.7,                      !- Solar Absorptance
      0.7;                      !- Visible Absorptance
  ```
- Notes: 100% reproduction (11/11), no partial-repro cases to report — no need to invoke the "report non-reproducing buildings explicitly" contingency. All 11 sampled buildings share the identical `u_roof_w_m2k=0.119` value (construction-set value is a function of `(archetype_id, climate_zone)` only, not of building geometry/S — confirms §4's note that S does not appear in `patch_envelope()`'s formula) — this is a strong early signal for I04 that within `nyc_rural` `SmallOffice`, `u_roof_w_m2k` itself does not vary with S; any correlation with S would have to run through a different mechanism (scaled roof surface dimensions), consistent with §4's open question. Side finding (not a new defect, not logged to §8): the T19 harvest CSV's `has_fatal` column reads `False` for all 150 affected rows even though `n_severe=1` and `status="failed"` for every one — the harvest script's `"** Fatal **" in err` substring check (single space) does not match the real EnergyPlus text `"**  Fatal  **"` (double space each side), so `has_fatal` under-reports for this failure mode. This did not affect I01 (the plan's own filter uses `status!="success"`, not `has_fatal`), but is worth flagging for whoever eventually revisits the harvest script. EnergyPlus local runtime per building was fast (~0.26-0.31s, fails at `InitConductionTransferFunctions` before Sizing/Warmup even starts) — no sample-size reduction was needed; all 11 ran well within the plan's local-hardware allowance.

#### I02 — Isolate the mechanism — completed 2026-07-25
- Artifacts:
  - `scratchpad/e-la-20-investigation/i02/build_and_sim_i02.py` (real Step2 + 3-variant BuildingIDF/build() + real EnergyPlus 23.1 run driver)
  - `scratchpad/e-la-20-investigation/i02/results_i02.csv` (12-row pass/fail table)
  - `scratchpad/e-la-20-investigation/i02/run_log_i02.txt` (full console log)
  - `scratchpad/e-la-20-investigation/i02/work/step3_a_scaled_only_nopatch/idfs/*.idf` (4 real generated IDFs, variant a)
  - `scratchpad/e-la-20-investigation/i02/work/step3_b_patched_mass_false/idfs/*.idf` (4 real generated IDFs, variant b)
  - `scratchpad/e-la-20-investigation/i02/work/step3_c_patched_mass_true/idfs/*.idf` (4 real generated IDFs, variant c)
  - `scratchpad/e-la-20-investigation/i02/a_scaled_only_nopatch/way_<osm_id>/eplusout.{err,end,eio,...}` (4 dirs, real EnergyPlus 23.1 output)
  - `scratchpad/e-la-20-investigation/i02/b_patched_mass_false/way_<osm_id>/eplusout.{err,end,eio,...}` (4 dirs)
  - `scratchpad/e-la-20-investigation/i02/c_patched_mass_true/way_<osm_id>/eplusout.{err,end,eio,...}` (4 dirs)
- Deviations: **director-authorised methodological deviation** for variant (a) — `openubem.geometry.envelope_patcher.patch_envelope` was monkeypatched at runtime, inside `build_and_sim_i02.py` only, to `lambda idf, row, thermal_mass=False: idf` for the duration of variant (a)'s 4 builds, then restored to the original function object (captured before any patch) in a `finally` block before variant (b) ran. This is a scratch-script runtime attribute swap on the module object — no file on disk was edited, no default in `builder.py`/`envelope_patcher.py` was changed — per plan §1.2 "explicit keyword-argument overrides at call time or scratch copies" (the runtime monkeypatch is the scratch-copy-equivalent mechanism explicitly authorised by the director for variant (a), since `patch_envelope()` itself has no keyword to suppress its own invocation from `builder.py` line 487). Variant (b) used a plain call-time keyword override (`BuildingIDF(row, thermal_mass=False, ...)`), no monkeypatch, per plan §1.2 directly. No other deviations.
- Test status: all 12 real EnergyPlus 23.1 runs completed (4 buildings × 3 variants). Result exactly matches the plan's expectation — (a) PASS, (b) PASS, (c) FATAL — **no STOP condition met**.

  | osm_id | S | variant | roof material object actually present (quoted params) | pass/fail | quoted `.err`/`.end` |
  |---|---|---|---|---|---|
  | way/772627076 | 0.0428 (min) | (a) scaled-only, no patch | no `LA_Roof`/`LA_ROOF` object of any kind (grep count=0); roof surface `Attic_roof_north` `Construction_Name="AtticRoofDeck"` → native baseline `CONSTRUCTION,AtticRoofDeck` with layers `F12 Asphalt shingles`/`G02 16mm plywood` | PASS | `EnergyPlus Completed Successfully-- 490284 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  7.85sec` |
  | way/772627076 | 0.0428 (min) | (b) patched, thermal_mass=False | `MATERIAL:NOMASS,LA_Roof_Assembly,MediumRough,8.403361344537815,...` (1 occurrence, no `MATERIAL` version) | PASS | `EnergyPlus Completed Successfully-- 260066 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  6.14sec` |
  | way/772627076 | 0.0428 (min) | (c) patched, thermal_mass=True | `MATERIAL,LA_Roof_Assembly,MediumRough,1.0084033613445378,0.12,800,1000,...` | FATAL (repro) | `EnergyPlus Terminated--Fatal Error Detected. 9 Warning; 1 Severe Errors; Elapsed Time=00hr 00min  0.09sec` |
  | way/772627017 | 0.2879 | (a) scaled-only, no patch | grep count=0 for `LA_Roof`/`LA_ROOF` | PASS | `EnergyPlus Completed Successfully-- 535446 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  8.48sec` |
  | way/772627017 | 0.2879 | (b) patched, thermal_mass=False | `MATERIAL:NOMASS,LA_Roof_Assembly,MediumRough,8.403361344537815,...` (1 occurrence, no `MATERIAL` version) | PASS | `EnergyPlus Completed Successfully-- 260366 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  6.14sec` |
  | way/772627017 | 0.2879 | (c) patched, thermal_mass=True | `MATERIAL,LA_Roof_Assembly,MediumRough,1.0084033613445378,0.12,800,1000,...` | FATAL (repro) | `EnergyPlus Terminated--Fatal Error Detected. 5 Warning; 1 Severe Errors; Elapsed Time=00hr 00min  0.08sec` |
  | way/772627020 | 0.5141 | (a) scaled-only, no patch | grep count=0 for `LA_Roof`/`LA_ROOF` | PASS | `EnergyPlus Completed Successfully-- 547902 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  8.87sec` |
  | way/772627020 | 0.5141 | (b) patched, thermal_mass=False | `MATERIAL:NOMASS,LA_Roof_Assembly,MediumRough,8.403361344537815,...` (1 occurrence, no `MATERIAL` version) | PASS | `EnergyPlus Completed Successfully-- 263269 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  6.27sec` |
  | way/772627020 | 0.5141 | (c) patched, thermal_mass=True | `MATERIAL,LA_Roof_Assembly,MediumRough,1.0084033613445378,0.12,800,1000,...` | FATAL (repro) | `EnergyPlus Terminated--Fatal Error Detected. 5 Warning; 1 Severe Errors; Elapsed Time=00hr 00min  0.08sec` |
  | way/270445755 | 2.7789 (max) | (a) scaled-only, no patch | grep count=0 for `LA_Roof`/`LA_ROOF` | PASS | `EnergyPlus Completed Successfully-- 567822 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  9.06sec` |
  | way/270445755 | 2.7789 (max) | (b) patched, thermal_mass=False | `MATERIAL:NOMASS,LA_Roof_Assembly,MediumRough,8.403361344537815,...` (1 occurrence, no `MATERIAL` version) | PASS | `EnergyPlus Completed Successfully-- 269244 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  6.28sec` |
  | way/270445755 | 2.7789 (max) | (c) patched, thermal_mass=True | `MATERIAL,LA_Roof_Assembly,MediumRough,1.0084033613445378,0.12,800,1000,...` | FATAL (repro) | `EnergyPlus Terminated--Fatal Error Detected. 5 Warning; 1 Severe Errors; Elapsed Time=00hr 00min  0.08sec` |

  All 4 (c) `.err` files carry the identical §4-cited signature verbatim (quoted for `way/772627076`, matches `way/772627017`/`way/772627020`/`way/270445755` byte-for-byte apart from the underground-floor-area warning lines and Sizing warning counts):
  ```
  ** Severe  ** CTF calculation convergence problem for Construction="LA_ROOF_CONSTRUCTION".
  **   ~~~   ** ...with Materials (outside layer to inside)
  **   ~~~   ** (outside)="LA_ROOF_ASSEMBLY"
  **   ~~~   ** The Construction report will be produced. This will show more details on Constructions and their materials.
  **   ~~~   ** Attempts will be made to complete the CTF process but the report may be incomplete.
  **   ~~~   ** Constructs reported after this construction may appear to have all 0 CTFs.
  **   ~~~   ** The potential causes of this problem are related to the input for the construction
  **   ~~~   ** listed in the severe error above.  The CTF calculate routine is unable to come up
  **   ~~~   ** with a series of CTF terms that have a reasonable time step and this indicates an
  **   ~~~   ** error.  Check the definition of this construction and the materials that make up
  **   ~~~   ** the this->  Very thin, highly conductive materials may cause problems.
  **   ~~~   ** This may be avoided by ignoring the presence of those materials since they probably
  **   ~~~   ** do not effect the heat transfer characteristics of the this->  Highly
  **   ~~~   ** conductive or highly resistive layers that are alternated with high mass layers
  **   ~~~   ** may also result in problems.  After confirming that the input is correct and
  **   ~~~   ** realistic, the user should contact the EnergyPlus support team.
  **  Fatal  ** Program terminated for reasons listed (InitConductionTransferFunctions)
  ...Summary of Errors that led to program termination:
  ..... Reference severe error count=1
  ..... Last severe error=CTF calculation convergence problem for Construction="LA_ROOF_CONSTRUCTION".
  ```
- Notes: **Confirms plan §3.2's expected framing — no re-scope needed.** `thermal_mass=True` is the sole and sufficient proximate trigger: 4/4 (c) builds Fatal, 4/4 (a) and 4/4 (b) builds pass clean (0 Severe Errors, "Completed Successfully") across the full S range (0.0428 to 2.7789), all sharing the identical `u_roof_w_m2k=0.119`/`Thermal_Resistance=8.403361344537815`/`Thickness=1.0084033613445378` values (consistent with I01's finding that these are archetype/climate-zone-invariant-to-S). All three variants were verified by direct object inspection, not just inferred from pass/fail: (c) IDFs contain exactly the `MATERIAL,LA_Roof_Assembly` block with the exact cited params in all 4 buildings; (b) IDFs contain exactly one `LA_Roof_Assembly` object, typed `MATERIAL:NOMASS`, no co-existing `MATERIAL` version, in all 4 buildings; (a) IDFs contain zero occurrences of `LA_Roof`/`LA_ROOF` (case-sensitive substring grep) in all 4 buildings, and their roof `BuildingSurface:Detailed` objects still reference the native baseline `Construction_Name="AtticRoofDeck"` (2-layer `F12 Asphalt shingles`/`G02 16mm plywood`, unrelated to any LA_-prefixed construction). This clears I02's gate for I03/I04 to proceed under the "thermal_mass=True is the trigger, not a confound of envelope-patching-in-general or small-S-in-general" framing — I03/I04 are next scope's, not this dispatch's, to execute. No unexpected failure signatures encountered (no Sizing-phase failure for (a), no different-mechanism failure for any variant) — all pass/fail outcomes matched the plan's stated expectation exactly.

#### I04 — Why `nyc_rural` `SmallOffice` specifically — completed 2026-07-25
- Artifacts:
  - `scratchpad/e-la-20-investigation/i04/run_step2_all_cells.py` (real Step2 semantic enrichment, all 12 cells' raw OSM fixtures from `docs_VALIDATION/.../phaseE/<cell>/01_buildings.gpkg` — same fixture family I01 used for `nyc_rural` — with a dummy `epw_path` string since `enrich_semantics()` only requires it non-null, `openubem/semantic/__init__.py` lines 86-93; no network EPW fetch needed for this task)
  - `scratchpad/e-la-20-investigation/i04/fleet_enriched_all_cells.csv` (7,510-row real Step-2 output, all 12 cells, non-`OpenUBEMUnknown` archetypes, with `climate_zone`/`vintage_standard`/`u_roof_w_m2k`/`S`/`derived_thickness_m` per building)
  - `scratchpad/e-la-20-investigation/i04/cell_climate_zone_summary.csv` (Part 2 per-cell resolved climate zone)
  - `scratchpad/e-la-20-investigation/i04/build_part1_matrix.py` + `part1_full_matrix_u_roof.csv` (3,248-row full 29-archetype × 16-zone × 7-vintage matrix, direct from the bundled table) + `part1_smalloffice_matrix_u_roof.csv` / `part1_smalloffice_pivot_u_roof.csv` (SmallOffice subset/pivot)
  - `scratchpad/e-la-20-investigation/i04/analyze_i04.py` + `part3_smalloffice_by_cell.csv` (Part 3a-d, SmallOffice × 12 cells) + `part3_nycrural_by_archetype.csv` (Part 3, `nyc_rural` × all archetypes) + `part4_la_urban_failures.csv` (Part 4) + `part5_fleet_risk_ranking.csv` (Part 5, all 120 (cell,archetype) groups ranked)
  - `scratchpad/e-la-20-investigation/i04/part3_vintage_provenance_check.py` + `part3_vintage_provenance_4nyc_cells.csv` (director-requested deep-dive: traces `resolve_vintage()`'s own donor-tier provenance for the 4 NYC cells' `SmallOffice` stratum)
  - `scratchpad/e-la-20-investigation/i04/make_figures.py` producing, in **both** `openubem/outputs/` and `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/e-la-20/figures/`:
    - `e_la_20_i04_smalloffice_uroof_vs_S_by_cell.png` (u_roof outlier vs. S non-outlier, 12 cells)
    - `e_la_20_i04_fleet_risk_thickness_ranking.png` (Part 5 ranking)
- Deviations: none from the plan's own task text. One **methodological choice** made to satisfy Part 3/4's fleet-scale data requirement without any cluster compute: rather than re-deriving `u_roof_w_m2k`/`climate_zone`/`vintage_standard` per building from the (columns-absent) T19 harvest CSV, real Step-2 semantic enrichment (`BuildingClassifier.classify()` → `assign_climate_zones()` → `enrich_semantics()`, the exact real pipeline, no synthetic shortcuts) was re-run locally on all 12 cells' own raw OSM fixtures already present in the repo at `docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg` (same 8,160-building population T17/T18/T19 all drew from — row counts matched exactly per cell). This is real-pipeline, real-data, zero-cluster, zero-network-EPW computation, consistent with plan §1.6/§1.3 ("real EnergyPlus 23.1... All repro/diagnostic runs are local" — Step 2 alone needs no EnergyPlus at all; §5/I04's own "How" already anticipated pulling from "the underlying semantic-enrichment output"). Director-cited Part 1 instruction ("you do not need to run Step 2... build the matrix directly from the module's own bundled table") was followed literally for Part 1's matrix (`build_part1_matrix.py` reads only `ashrae_90_1_2019.json` + `VINTAGE_U_FACTORS`, no Step 2 call) — Step 2 was run only for Parts 2-4's real fleet distributions, which cannot be derived from the bundled table alone (they need each real building's own resolved `climate_zone`/`vintage_standard`).
- Test status:
  - **Part 1 (mechanism, cited):** `get_construction_set()` (`openubem/semantic/construction_sets.py` lines 266-355) merges `gdf[["archetype_id","climate_zone"]]` against the flattened `ashrae_90_1_2019.json` table on `(archetype_id, climate_zone)` (lines 287-299), then for each row multiplies `u_roof_w_m2k`/`u_wall_w_m2k`/`u_window_w_m2k`/`u_floor_w_m2k` by `VINTAGE_U_FACTORS[vintage_standard]` and rounds to 3 decimals (lines 332-337). `VINTAGE_U_FACTORS` (lines 27-35): `DOERefPre1980=1.6`, `DOERef1980to2004=1.583`, `90.1-2007=1.309`, `90.1-2010=1.309`, `90.1-2013=1.0`, `90.1-2016=1.0`, `90.1-2019=1.0` (baseline). The full 3,248-row matrix confirms the bundled table's `SmallOffice` roof base value is **banded, not continuous**, across the 16-zone vocabulary: `0.153` (zones 1A-3C), `0.119` (zones **4A-6B**), `0.097` (zones 7-8) — `nyc_rural`'s 6A and the 3 other NYC cells' 4A share the identical `0.119` base. Only vintage tiers with factor `1.0` (`90.1-2013`/`2016`/`2019`) leave that base value unmultiplied; every older vintage inflates it (e.g. `DOERefPre1980` → `0.119*1.6=0.190`).
  - **Part 2 (12-cell climate zone table, via real `assign_climate_zones()` on each cell's own real building population, not a single centroid point):

    | cell | state | resolved climate_zone | n_distinct_zones |
    |---|---|---|---|
    | nyc_centre | NY | 4A | 1 |
    | nyc_urban | NY | 4A | 1 |
    | nyc_suburban | NY | 4A | 1 |
    | **nyc_rural** | NY | **6A** | 1 |
    | la_centre | CA | 3B | 1 |
    | la_urban | CA | 3B | 1 |
    | la_suburban | CA | 3B | 1 |
    | la_rural | CA | 3B | 1 |
    | austin_centre | TX | 2A | 1 |
    | austin_urban | TX | 2A | 1 |
    | austin_suburban | TX | 2A | 1 |
    | austin_rural | TX | 3A | 1 |

    **Yes** — `nyc_rural` resolves to 6A, strictly colder than the other 3 NYC cells' 4A (and than every LA/Austin cell). Every cell resolves to a single, unmixed zone (no multi-zone-neighbourhood warning fired).
  - **Part 3a/b/c/d (SmallOffice across 12 cells, real Step-2 output, `n=` real buildings/cell):**

    | cell | n | u_roof (med) | Thickness (med, m) | S min–med–max | pass_rate |
    |---|---|---|---|---|---|
    | **nyc_rural** | 150 | **0.119** | **1.008403** | 0.043–0.288–**2.779** | **0/150 (0%)** |
    | nyc_centre | 255 | 0.190 | 0.632 | 0.063–1.844–4.985 | 255/255 (100%) |
    | nyc_suburban | 316 | 0.190 | 0.632 | 0.058–0.229–4.057 | 316/316 (100%) |
    | nyc_urban | 1460 | 0.190 | 0.632 | 0.041–0.574–**7.606** | 1460/1460 (100%) |
    | la_centre | 41 | 0.245 | 0.490 | 0.073–0.923–5.649 | 41/41 (100%) |
    | la_urban | 54 | 0.245 | 0.490 | 0.083–1.291–5.711 | 54/54 (100%) |
    | la_suburban | 38 | 0.242 | 0.496 | 0.040–0.418–5.654 | 38/38 (100%) |
    | la_rural | 106 | 0.245 | 0.490 | 0.055–0.272–5.863 | 106/106 (100%) |
    | austin_centre | 167 | 0.245 | 0.490 | 0.062–0.539–6.408 | 167/167 (100%) |
    | austin_urban | 356 | 0.245 | 0.490 | 0.041–0.657–6.755 | 356/356 (100%) |
    | austin_suburban | 377 | 0.245 | 0.490 | 0.040–0.643–6.241 | 377/377 (100%) |
    | austin_rural | 177 | 0.245 | 0.490 | 0.068–0.675–3.687 | 177/177 (100%) |

    `nyc_rural`'s S range (max 2.779) is one of the **narrowest** of all 12 — 8 of the 11 other cells have a wider max-S (up to 7.606, 2.7× wider), all 100% passing. **This directly disproves "incidental extreme-S concentration."** `u_roof=0.119` is unique to `nyc_rural` among all 12 cells' `SmallOffice` populations even though the *base* table value (Part 1) is identically 0.119 for 4A too — the difference is **vintage**, confirmed by direct `resolve_vintage()` re-derivation (`part3_vintage_provenance_4nyc_cells.csv`): `nyc_rural` SmallOffice = 100% `vintage_standard="90.1-2013"` (factor 1.0) vs. `nyc_centre`/`nyc_suburban`/`nyc_urban` SmallOffice = 100% `"DOERefPre1980"` (factor 1.6, → 0.119×1.6=0.190). `nyc_rural` `SmallOffice` by archetype (`part3_nycrural_by_archetype.csv`): every other archetype in that cell sits at a different, non-failing `u_roof` (`Courthouse`/`MidriseApartment`/`SmallHotel`/etc. at 0.291/Thickness=0.412; `FullServiceRestaurant`/`QuickServiceRestaurant` at 0.190/Thickness=0.632) — `SmallOffice` is the only `nyc_rural` archetype landing on the failing value, and 100% of its 150 real buildings do, at 100% fail rate (0/150).
  - **Root-cause deep-dive on the vintage difference (director-relevant, goes beyond the plan's literal ask but directly resolves "genuine vs incidental"):** re-ran `resolve_vintage()` directly (read-only) on all 4 NYC cells' `SmallOffice` stratum. Real observed `year_built` completeness: `nyc_centre` 2/255, `nyc_urban` **0/1460**, `nyc_suburban` **0/316**, `nyc_rural` **1/150**. `nyc_urban`/`nyc_suburban` (zero real observations) fall straight to the **Tier-3 legacy default** `DOERefPre1980` (`vintage_prov="VINTAGE_NAN_PERMISSIVE_DEFAULT"`, 100%). `nyc_centre`'s 2 real observations both bin to pre-1980, and their **Tier-2 group-wise mode** (`GROUPMODE_MED`) then propagates `DOERefPre1980` to the other 253. `nyc_rural`'s **single** real observation (`year_built=2011`, binning to `90.1-2013`) is the *only* observed value in that stratum, so the Tier-2 mode is unanimously `90.1-2013` by default, and propagates via `GROUPMODE_MED` to the other 149. **The entire 150-building failing population's vintage — and therefore its `u_roof=0.119`/Thickness=1.008403 — traces to exactly one real OSM building's `year_built` tag**, via `construction_sets.resolve_vintage()`'s Tier-2 group-wise-mode fallback (lines 214-243, Input-Imputation arc T04). This is fully deterministic and reproducible (fixed `RANDOM_SEED`, no live randomness) — it is **not** noise or sampling luck — but it is evidentially thin: a single differently-tagged building, or one additional real observation in that stratum, could flip the mode and eliminate the failure entirely without any code change.
  - **Part 4 (`la_urban` `SmallOffice` near-miss, director addition):** real T19 label count confirmed: 57 total, 55 success + **2 failed** (`way/428846131`, `relation/6374725`) — matches the director's own re-derivation exactly. **No raw `.err` files survive locally for the T19 harvest** — confirmed by direct search: `scratchpad/t19_t11_work/` contains only `t19_harvest.log`/`t19_submit.log`/comparison scripts/CSVs, zero `.err`/`.eio`/etc. files (stated plainly per the honesty requirement, not assumed). Fell back to the plan's own specified alternative: read-only T17/T18 CSV lookup for these exact 2 `osm_id`s —

    | osm_id | T17 status | T17 n_severe | T18 status | T18 n_severe |
    |---|---|---|---|
    | way/428846131 | failed | 1 | failed | 1 |
    | relation/6374725 | failed | 1 | failed | 1 |

    Both were **already `status="failed"` in T17 and T18** — i.e. before the structural-fixes plan's `thermal_mass=True` default (T19-only) ever existed. Since I02 already confirmed `thermal_mass=True` is the sole proximate trigger for E-LA-20 (§7/I02), a failure present identically in T17/T18 **cannot be E-LA-20** by construction — these are **pre-existing, unrelated defects**, structurally identical in kind to `nyc_rural`'s own 2 known carryovers (§3.4). Corroborating (found via `grep`, not re-executed/re-verified this dispatch, informational only): `scripts/diagnostics/t06_validate_relation6374725.py` documents a **pre-existing, already-addressed interior-ring vertex-mismatch geometry defect** on `relation/6374725` from an earlier (pre-this-plan-lineage) T06 diagnostic — consistent with it being a chronically complex-geometry building, unrelated to CTF/roof-material convergence. **Verdict: `la_urban`'s 55/57 is NOT E-LA-20.** The structural-fixes plan's "100% concentrated in `nyc_rural`" claim holds up under this check.
  - **Part 5 (fleet-risk ranking, full 120-group table in `part5_fleet_risk_ranking.csv`, top 10 by `|Thickness_min - 1.008403|`):**

    | rank | cell / archetype | n | u_roof (med) | Thickness (med, m) | dist to cliff (m) | pass_rate |
    |---|---|---|---|---|---|---|
    | 1 | nyc_rural / SmallOffice | 150 | 0.119 | 1.008403 | **0.000** | 0% |
    | 2 | nyc_centre / HighriseApartment | 1 | 0.182 | 0.659 | 0.349 | 100% |
    | 3 | nyc_centre / SmallOffice | 255 | 0.190 | 0.632 | 0.377 | 100% |
    | 3 | nyc_rural / FullServiceRestaurant | 6 | 0.190 | 0.632 | 0.377 | 100% |
    | 3 | nyc_centre / QuickServiceRestaurant | 5 | 0.190 | 0.632 | 0.377 | 100% |
    | 3 | nyc_centre / FullServiceRestaurant | 4 | 0.190 | 0.632 | 0.377 | 100% |
    | 3 | nyc_rural / QuickServiceRestaurant | 3 | 0.190 | 0.632 | 0.377 | 100% |
    | 3 | nyc_suburban / SmallOffice | 316 | 0.190 | 0.632 | 0.377 | 100% |
    | 3 | nyc_urban / SmallOffice | 1460 | 0.190 | 0.632 | 0.377 | 100% |
    | 11 | austin_centre / TallBuilding | 16 | 0.221 | 0.543 | 0.465 | 68.75% (pre-existing E-LA-16 residual, unrelated, out of scope) |

    There is a clear **~0.35 m gap** between `nyc_rural`/`SmallOffice` (at the cliff) and the next-closest group — no other group is currently near-failing. The structural at-risk condition is the `(climate_zone ∈ {4A..6B}) × (vintage ∈ {90.1-2013,2016,2019})` matrix cell (Part 1): the other 3 NYC cells' `SmallOffice` populations sit in the *same* 4A-6B zone band and are only safe today because their real/imputed vintage mix is 100% pre-1980 — a real-world or imputation-driven shift toward modern vintage in any 4A-6B cell/archetype population would land it on the identical 1.008403 m cliff.
  - **Direct verdict on the plan's question:** **Genuine numeric outlier — not incidental extreme-S concentration.** Evidence: (1) S is empirically not even the most extreme among the 12 cells (Part 3c); (2) `u_roof=0.119` is a fully deterministic function of `(climate_zone, vintage_standard)`, invariant to S/geometry (I01/I02 already showed this; Part 3/1 reconfirm it at fleet scale); (3) it is fully reproducible on every re-run given the fixed `RANDOM_SEED` and the same input data — not sampling noise. Caveat volunteered per the honesty requirement: the *reason* `nyc_rural` specifically lands in the failing matrix cell is evidentially thin — a single real OSM building's `year_built` tag, propagated via Tier-2 group-wise-mode imputation to 149 siblings (see deep-dive above) — so while the outlier is genuine and deterministic, it is not a robust/intentional archetype-climate design outcome; it is fragile to any change in that one building's tag or in the imputation logic.
- Notes: (1) The 41 archetype-classification mismatches surfaced between this dispatch's real Step-2 re-run and the T19 CSV's own archetype labels (`analyze_i04.py` output, e.g. `way/965718400-403` reclassified `SmallHotel` vs. T19's `SmallOffice`) are **not a new defect** — they are exactly the same 4 buildings already named in plan §3.4 as known carryovers/exceptions (2 failing carryovers `way/965718400`/`way/965718401`, plus 2 successes `way/965718402`/`way/965718403`), now independently corroborated: this dispatch's own fresh classification run disagrees with T19's archetype label for these exact 4 buildings, consistent with them being genuinely ambiguous/edge-case buildings. Not logged as a new error — a classification-determinism question for the classifier is out of this plan's and this task's scope. (2) `austin_centre`/`TallBuilding`'s 68.75% pass rate in the Part 5 table is the already-logged, out-of-scope `E-LA-16` residual (plan §1's exclusion list) — surfaced only as ranking context, not investigated further here. (3) All Step-2 runs were real-pipeline (`BuildingClassifier`, `assign_climate_zones`, `enrich_semantics`), zero synthetic/hand-rolled data, zero cluster compute, zero network calls (EPW fetch bypassed with a dummy string since not needed for these computations) — fully consistent with plan §1.6.

#### I03 — Characterize the numeric regime — completed 2026-07-25
- Artifacts:
  - `scratchpad/e-la-20-investigation/i03/enrich_all154_nyc_rural.py` + `all154_nyc_rural_smalloffice.csv` (real Step-2 enrichment, all 154 T19-recorded `nyc_rural`/`SmallOffice` rows, `u_roof_w_m2k`/`vintage_standard`/`climate_zone`/S/derived material props per row)
  - `scratchpad/e-la-20-investigation/i03/part1_passers.py` + `part1_manifest_*.csv` + `part1_results.csv` + `A_as_classified_today/way_96571840{2,3}/eplusout.*` + `B_as_recorded_in_t19_SmallOffice/way_96571840{2,3}/eplusout.*` (real Step2+Step3+EnergyPlus, 2 variants × 2 buildings)
  - `scratchpad/e-la-20-investigation/i03/control_sample_enrich.py` + `control_sample_30.csv` (real Step-2 enrichment, 6 cross-cell cells × 5 real `SmallOffice` buildings = 30 rows)
  - `scratchpad/e-la-20-investigation/i03/control_sample_sim.py` + `control_sim_results.csv` + `control_sim/<cell>/way_<id>/eplusout.*` (real Step2+Step3+EnergyPlus, 6 of the 30 control buildings simulated)
  - `scratchpad/e-la-20-investigation/i03/part4_bisection.py` + `part4_coarse_results.csv` + `part4_bisect_results.csv` + `part4_bisection/runs/*/eplusout.*` (real Step2 once + 25 real `BuildingIDF.build()`+EnergyPlus runs on `way/772627020` with `u_roof_w_m2k` overridden in-memory only)
  - `scratchpad/e-la-20-investigation/i03/make_plot.py` + `i03_master_regime_table.csv`
  - `openubem/outputs/e_la_20_i03_thickness_threshold.png` + `e_la_20_i03_master_regime_table.csv` + `e_la_20_i03_part4_coarse_results.csv` + `e_la_20_i03_part4_bisect_results.csv` (and identical copies under `docs/docs_ACTIVE/simulation-Resolution/layoutAssigner/e-la-20/figures/`)
- Deviations:
  1. **Director count-correction ruling (pre-work):** the plan's §0/I03 line ("154 = 150 failing + 4 passing") is superseded by the director's independent re-derivation from `t19_layout_assign_eui.csv`: **154 = 152 failed + 2 success** (`way/965718402`, `way/965718403`), where 152 failed = 150 true CTF-signature rows + the 2 already-excluded carryovers (`way/965718400` E-LA-17, `way/965718401` E-LA-15, per plan §3.4). Independently reconfirmed this dispatch via a direct `pd.read_csv` filter — exact match, zero discrepancy.
  2. **Director Part-4 bisection authorisation:** per the director's explicit instruction, `u_roof_w_m2k` was overridden on the in-memory enriched `pd.Series` row only (`row2 = row.copy(); row2["u_roof_w_m2k"] = u`), immediately before `BuildingIDF(row2, ...)` construction, never touching any file under `openubem/`. This is an authorised extension of I03's own "look for a numeric threshold" How-to-test (plan §5/I03) — it overrides nothing plan-level and does not conflict with plan §3.3's "do not invent synthetic scale factors" (that clause is about S; this overrides `u_roof` on a real building's row, on director's explicit instruction).
  3. **Process-management correction (mid-task, director-directed):** the employee initially ended a turn stating it would wait for a backgrounded process's own notification rather than continuing to poll from within the same turn. Per the director's correction, all subsequent waits in this dispatch were done via active, in-turn polling (direct `Get-Process`/file-timestamp checks, synchronous foreground `Bash` calls with long timeouts) rather than ending the turn idle. The one process that was genuinely stuck (see Part 1 below) was identified via this active polling (CPU climbing with zero file writes for 90+ seconds) and killed rather than left to run indefinitely.
  4. **Part 1 methodological addendum (not director-pre-authorised, but a direct, minimal extension needed to execute the director's own instruction):** because a fresh, unmodified Step-2 classification of `way/965718402`/`way/965718403` yields `archetype_id="SmallHotel"` (see Part 1 finding below), literally "building those 2 buildings" through the unmodified pipeline does not exercise the `SmallOffice`/`layout_assign` path the T19 CSV records at all. To still test "the 2 T19-recorded passers" as `SmallOffice`, `archetype_id` was force-overridden to `"SmallOffice"` on an in-memory copy of the classified row, immediately after `BuildingClassifier().classify()` and before `enrich_semantics()` — mirroring, at the classification stage, the same in-memory-row-mutation-only, no-file-touched pattern the director explicitly authorised for `u_roof_w_m2k` in Part 4. This is reported as a finding, not smoothed over (see below).
- Test status (honesty requirement: **a clean, sharp, monotonic numeric threshold exists** — see Part 4; the two "T19-recorded passers" do **not** reproduce as passes under a straightforward `SmallOffice` reconstruction — see Part 1):

  **Part 1 — the 2 T19-recorded passers.**
  - Fresh, unmodified, current-HEAD `BuildingClassifier().classify()` on `way/965718402`/`way/965718403` (both real OSM `building_tag="hotel"`, confirmed by direct read of the raw fixture) returns `archetype_id="SmallHotel"`, **not** `"SmallOffice"` as recorded in `t19_layout_assign_eui.csv` — a genuine drift between whatever code/data state produced the T19 harvest and current git HEAD. This is the same discrepancy I04 independently surfaced (its Notes (1)) for these exact 4 buildings; this dispatch adds the following deeper layer.
  - **Variant A (`archetype_id` left as freshly classified, i.e. `SmallHotel`; thermal_mass=True, resolution_mode=layout_assign; real Step2+Step3+EnergyPlus):** `way/965718402` — u_roof=0.291, thickness=0.412371 — **PASS**, quoted `.end` verbatim: `EnergyPlus Completed Successfully-- 60039839 Warning; 0 Severe Errors; Elapsed Time=00hr 04min 10.71sec` (60 million warnings, 4min10s runtime — an extreme, out-of-scope HVAC/PTAC warning-flood pathology on the `SmallHotel` prototype, unrelated to the CTF/roof Fatal under investigation; `.err` tail shows repeated `SimHVAC: Maximum iterations (20) exceeded for all HVAC loops` and `CalcDoe2DXCoil ... Air-cooled condenser inlet dry-bulb temperature below 0 C` warnings, not `CheckWarmupConvergence`/E-LA-14/19 — a distinct, previously-unseen warning source, informational only, not investigated further). `way/965718403` — same variant — was **killed by the investigator** after active in-turn polling showed EnergyPlus CPU climbing (85.8s → 141.9s) while every output file's `LastWriteTime` stayed frozen for 90+ seconds (confirmed via direct `Get-Item`/`Get-ChildItem` timestamp checks) — genuinely stuck in the same warning-flood pathology as its sibling, not a hang in the CTF/roof mechanism (no `LA_ROOF`/`LA_ROOF_CONSTRUCTION` text present at all in this variant, confirmed by I02's own established zero-occurrence pattern for no-patch/non-`layout_assign`-envelope builds — actually here the patch IS applied since `resolution_mode="layout_assign"`, but the flood is HVAC-side, not envelope-side); recorded plainly as a stuck/killed run, not silently dropped.
  - **Variant B (`archetype_id` force-overridden to `"SmallOffice"` immediately post-classify, before `enrich_semantics()`; thermal_mass=True, resolution_mode=layout_assign; real Step2+Step3+EnergyPlus):** for both `way/965718402` and `way/965718403`, the re-run `enrich_semantics()` resolved `vintage_standard="90.1-2013"` (Tier-2 `GROUPMODE_MED` donor — the dominant vintage among the in-memory `SmallOffice` stratum, i.e. the same vintage as the 150 real failures) — **not** `"DOERefPre1980"` as the T19 CSV's own recorded `data_quality_flag` token (`VINTAGE_NAN_PERMISSIVE_DEFAULT`, Tier-3) implies actually happened at harvest time. This is a **second, compounding drift** beyond the archetype mismatch: even forcing the archetype back to `SmallOffice` does not reproduce the CSV's own recorded vintage-donor tier locally. Consequently both buildings resolved to `u_roof_w_m2k=0.119`, `thickness=1.008403` — identical to the 150 real failures — and both **FATAL**, quoted `.end` verbatim (byte-identical for both): `EnergyPlus Terminated--Fatal Error Detected. 5 Warning; 1 Severe Errors; Elapsed Time=00hr 00min  0.09sec`, with the same §4-cited `CTF calculation convergence problem for Construction="LA_ROOF_CONSTRUCTION"` / `Fatal Program terminated ... (InitConductionTransferFunctions)` signature confirmed present in both `.err` files verbatim.
  - **Reconciling with what the T19 CSV's own flag implies:** if `archetype_id="SmallOffice"` AND `vintage_standard="DOERefPre1980"` (matching the CSV's own literal recorded token) are both honoured, the implied `u_roof_w_m2k = round(0.119*1.6, 3) = 0.190`, `thickness=0.631579` — and Part 4's bisection sweep (below) directly tested `u_roof=0.19` on a different real repro building (`way/772627020`) and confirmed **PASS** (`EnergyPlus Completed Successfully-- ... 0 Severe Errors ...`); I01/I02 already established the Fatal/pass outcome is invariant to which specific building carries a given `u_roof`/thickness (S ranged 0.0428-2.7789 with no change in outcome at fixed `u_roof`), so this is sufficient evidence without a third separate build. **Conclusion: the T19 CSV's "2 passers" are real but evidentially fragile** — their PASS status depends entirely on which vintage-donor tier gets assigned to them, exactly the same class of fragility I04 found for the 150-row failing population as a whole (traced to a single OSM building's `year_built` tag). A naive "rebuild these 2 IDs as SmallOffice today" reproduces **FATAL**, not PASS, because the vintage donor computation is itself unstable for these specific rows across re-runs/code-states.

  **Part 2 — cross-cell `SmallOffice` control sample.** 30 real buildings enriched (6 cells × 5 buildings, `austin_rural`/`austin_urban`/`la_rural`/`la_urban`/`nyc_centre`/`nyc_urban`, all T19 `status=="success"`, S spanning 0.041-7.606 — wider than `nyc_rural`'s own 0.0428-2.7789 range). Real Step-2 enrichment found exactly 2 distinct `u_roof_w_m2k` values across the whole 30-row sample: **0.245** (`austin_rural`/`austin_urban`/`la_rural`/`la_urban`, climate zones 2A/3A/3B, vintage 100% `DOERefPre1980`) and **0.190** (`nyc_centre`/`nyc_urban`, climate zone 4A, vintage 100% `DOERefPre1980`) — both fully consistent with I04's own Part 3a/b/c/d table. 6 of the 30 were built and simulated through the real Step2+Step3+EnergyPlus pipeline (`resolution_mode=layout_assign`, `thermal_mass=True`), chosen to span both `u_roof` values and a wide S range (0.041 to 7.606): **6/6 PASS**, each quoted `.end` verbatim:
    | cell | osm_id | u_roof | S | `.end` (quoted) |
    |---|---|---|---|---|
    | austin_rural | way/1480414370 | 0.245 | 0.068 | `EnergyPlus Completed Successfully-- 146619 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  5.40sec` |
    | la_rural | way/472960943 | 0.245 | 5.863 | `EnergyPlus Completed Successfully-- 184651 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  6.28sec` |
    | austin_urban | way/381824514 | 0.245 | 1.119 | `EnergyPlus Completed Successfully-- 169495 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  5.85sec` |
    | nyc_centre | way/265320251 | 0.190 | 0.063 | `EnergyPlus Completed Successfully-- 153219 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  5.66sec` |
    | nyc_urban | way/241836701 | 0.190 | 7.606 | `EnergyPlus Completed Successfully-- 178350 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  5.95sec` |
    | nyc_urban | way/280621507 | 0.190 | 0.387 | `EnergyPlus Completed Successfully-- 166239 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  5.78sec` |

    All 6 real-build confirmations match T19's recorded `status=="success"` exactly. No CTF/roof Fatal in any control-sample run.

  **Part 3 — numeric regime characterisation.** Real `Timestep` object read directly from a generated IDF this session (`part4_bisection/idfs/coarse_05_u0.119/idfs/way_772627020.idf` line 41-42): `TIMESTEP, 4; !- Number of Timesteps per Hour` → Δt = 900 s (**not** assumed 1 hour). Thermal diffusivity of the fixed `LA_Roof_Assembly` material properties (`Conductivity=0.12`, `Density=800`, `Specific_Heat=1000`, invariant across every building/S per I01/I02): α = 0.12/(800×1000) = 1.5×10⁻⁷ m²/s. Fourier number Fo = α·Δt/Thickness² computed for the key regimes:

    | regime | u_roof | thickness (m) | Fo | outcome |
    |---|---|---|---|---|
    | `nyc_rural` real failing population (150/150) | 0.119 | 1.008403 | 1.328×10⁻⁴ | FATAL |
    | bisection FATAL-side boundary | 0.137813 | 0.870745 | 1.781×10⁻⁴ | FATAL |
    | bisection PASS-side boundary | 0.138125 | 0.868778 | 1.789×10⁻⁴ | PASS |
    | other 3 NYC cells' `SmallOffice` (2031/2031, per I04) | 0.190 | 0.631579 | 3.384×10⁻⁴ | PASS |
    | LA/Austin control sample (4/4) | 0.245 | 0.489796 | 5.627×10⁻⁴ | PASS |

    EnergyPlus's own CTF diagnostic text, quoted verbatim from this dispatch's own real `.err` files (identical across every FATAL run, e.g. `bisect_04_u0.137813/eplusout.err`):
    ```
    **   ~~~   ** the this->  Very thin, highly conductive materials may cause problems.
    **   ~~~   ** This may be avoided by ignoring the presence of those materials since they probably
    **   ~~~   ** do not effect the heat transfer characteristics of the this->  Highly
    **   ~~~   ** conductive or highly resistive layers that are alternated with high mass layers
    **   ~~~   ** may also result in problems.
    ```
    This construction is neither literally "thin" (thickness 0.87-1.24 m is an extremely thick single roof layer) nor "highly conductive" (`Conductivity=0.12` W/m·K is a moderate, unremarkable value) in the everyday sense — it sits in the **second named regime**: a single homogeneous layer that is simultaneously high-mass (fixed `Density=800`/`Specific_Heat=1000`, scaling with thickness) **and** highly resistive (R=Thickness/Conductivity grows unbounded as `u_roof`→0, since `_K=0.12` is held fixed regardless of the target R-value — `envelope_patcher.py` line 29/104), which is what actually depresses the Fourier number, not raw conductivity. **A clean, sharp, monotonic Fo/thickness threshold exists**, empirically bracketed to `Fo ∈ (1.781, 1.789)×10⁻⁴`, `thickness ∈ (0.868778, 0.870745)` m, `u_roof ∈ (0.137813, 0.138125)` — a bracket width of only 0.002 m / 0.0003 W/m²K, i.e. resolved to within ~0.2% of the boundary value. No non-monotonicity was observed anywhere in the 20-point coarse sweep (`u_roof` 0.05→1.0) or the 5-step bisection refinement — every point below the boundary FATALs, every point above it passes, with no exceptions.

  **Part 4 — director-authorised bisection on `way/772627020` (S=0.5141).** Coarse sweep (20 points, `u_roof` 0.05→1.0, real Step2 run once + 20 real `BuildingIDF.build()`+EnergyPlus runs, `u_roof_w_m2k` overridden only on the in-memory row):
    | u_roof | thickness (m) | outcome | elapsed |
    |---|---|---|---|
    | 0.05 – 0.13 (9 points) | 2.400 – 0.923 | **FATAL** (all 9) | ~0.26-0.27s each |
    | 0.14 – 1.0 (11 points) | 0.857 – 0.120 | **PASS** (all 11) | ~5.9-6.3s each |

    Binary-search refinement (5 steps, stopping at bracket width < 0.0005 in `u_roof`):
    | step | u_roof | thickness (m) | outcome |
    |---|---|---|---|
    | 0 | 0.135 | 0.888889 | FATAL |
    | 1 | 0.1375 | 0.872727 | FATAL |
    | 2 | 0.13875 | 0.864865 | PASS (quoted `.end`: `EnergyPlus Completed Successfully-- 173111 Warning; 2 Severe Errors; Elapsed Time=00hr 00min  5.70sec` — the 2 Severe Errors are `CheckWarmupConvergence: ... did not converge after 25 warmup days` on 2 zones, the already-logged, out-of-scope E-LA-14/E-LA-19-class residual per plan §1's exclusion list, unrelated to the CTF/roof Fatal; run still counts as PASS for E-LA-20 purposes since no `LA_ROOF_CONSTRUCTION`/CTF/Fatal text is present) |
    | 3 | 0.138125 | 0.868778 | PASS |
    | 4 | 0.137813 | 0.870745 | FATAL (quoted `.end`: `EnergyPlus Terminated--Fatal Error Detected. 5 Warning; 1 Severe Errors; Elapsed Time=00hr 00min  0.09sec`) |

    **Final located boundary: `u_roof ∈ (0.137813, 0.138125)` W/m²K, `thickness ∈ (0.868778, 0.870745)` m.** This sits **much closer to the failing `nyc_rural` value (thickness=1.008403, distance 0.138-0.140 m) than to the passing NYC-cells value (thickness=0.631579, distance 0.237-0.239 m)** in absolute thickness terms — i.e. `nyc_rural`'s real value is only ~14-16% past the cliff, while the other NYC cells sit with a much larger (~37%) safety margin above it. In `u_roof` terms the boundary (0.138) is about 27% of the way from the failing value (0.119) to the passing value (0.190) — closer to the failing side.
- Notes: Per the honesty requirement — **yes, a clean, sharp, monotonic numeric threshold was found** (Part 3/4), located to a tight bracket (`u_roof≈0.1380±0.0002`, `thickness≈0.8698±0.001` m, `Fo≈1.785×10⁻⁴±0.004×10⁻⁴`), with zero non-monotonic flips across 25 real local EnergyPlus runs spanning the full failing-to-passing range. Separately, Part 1's honesty finding is that the T19 CSV's own "2 passing" rows are **not robustly reproducible as passes** under any straightforward current-HEAD rebuild (fresh classification gives a different archetype entirely; forcing the archetype back gives a different vintage-donor tier than the CSV's own recorded flag; only forcing *both* archetype AND the CSV-implied vintage/`u_roof` reproduces PASS) — this is reported plainly, not smoothed into "confirmed passing," and is evidentially the same fragility-of-imputation mechanism I04 traced for the 150-row failing population (a single OSM building's `year_built` tag, propagated by `GROUPMODE_MED`). This does not change I01/I02's established mechanism (`thermal_mass=True` + a specific `u_roof`/thickness regime is the proximate trigger) — it sharpens exactly where the boundary sits and confirms it is a real, physically-motivated Fourier-number cliff (not a fuzzy/noisy correlation), directly usable by a future implementation plan to set a numeric guard (e.g. a minimum `thickness`/maximum implied-R clamp comfortably above ~0.87-0.90 m, or equivalently a Fourier-number floor around 2×10⁻⁴, for the `thermal_mass=True` `MATERIAL` path specifically).

#### I05 — Diagnostic-only mitigation probes — completed 2026-07-25
- Artifacts:
  - `scratchpad/e-la-20-investigation/i05/build_baselines.py` (real Step2 + real `run_step3(resolution_mode="layout_assign", trim_outputs=True)`, `thermal_mass=True` default, on the 3 director-selected buildings)
  - `scratchpad/e-la-20-investigation/i05/sample_meta.csv` (S/`u_roof_w_m2k`/`floor_area_m2` per building, confirms exact match to I01's own values)
  - `scratchpad/e-la-20-investigation/i05/work/step3_baseline/idfs/*.idf` (3 real generated baseline IDFs, thermal_mass=True, unmodified — the "input" every probe scratch-copies from)
  - `scratchpad/e-la-20-investigation/i05/run_probes.py` (probe-application + EnergyPlus-run driver; each probe loads a fresh `GeomIDF` off the real baseline .idf, edits only the `LA_Roof_Assembly` MATERIAL / `LA_Roof_Construction` CONSTRUCTION objects in memory via eppy, `.saveas()`s to a new scratch path, never touches `openubem/` or the baseline .idf itself)
  - `scratchpad/e-la-20-investigation/i05/rerun_a_split_bugfix.py` (bugfix rerun for `a_split_n2`/`a_split_n4`, see Deviations)
  - `scratchpad/e-la-20-investigation/i05/idfs/way_<osm_id>/<probe_id>.idf` (30 scratch-copy IDFs, one per building×probe)
  - `scratchpad/e-la-20-investigation/i05/runs/way_<osm_id>/<probe_id>/eplusout.{err,end,sql,...}` (30 real EnergyPlus 23.1 output dirs)
  - `scratchpad/e-la-20-investigation/i05/probe_results.csv` (final merged 30-row pass/fail/EUI table)
- Deviations:
  1. **Director ruling replacing probe (c), recorded verbatim per the director's own instruction:** the plan's §5/I05(c) text ("a minimum-`Thickness` clamp higher than the current `max(0.01, r_val*_K)` floor") was ruled inapplicable before this dispatch began — the failing thickness is 1.008403 m, ~100x *above* the 0.01 m floor, so raising a minimum floor cannot affect a value already 100x past it; the 0.01 m floor is not part of this trigger. Substituted per the director's explicit replacement: **(c1) R-preserving thickness cap** (`Thickness=T_cap`, `Conductivity=T_cap/r_val`, R held exactly constant, mass drops with T_cap, tested at 0.5/0.3/0.2/0.1 m) and **(c2) hybrid thin-mass + NOMASS residual** (one real `MATERIAL` of modest thickness T1 at unchanged k/ρ/cp carrying R1=T1/k, plus one `MATERIAL:NOMASS` carrying the residual R=r_val−R1, two-layer `CONSTRUCTION`, total R preserved exactly; tested T1=0.20/0.10 m). Both bound the layer from above instead of from below, per the director's stated reasoning.
  2. **Self-caught scripting bug, fixed in-session, reported per the honesty requirement rather than smoothed over:** the first run of probe (a) at N=2 and N=4 produced a **different failure signature**, not the CTF Fatal: `** Severe ** Did not find matching material for Construction LA_ROOF_CONSTRUCTION, missing material = ` (×6 for N=2, repeated per unused trailing `Layer_N` field) → `** Fatal ** GetSurfaceData: Errors discovered, program terminates.` Root cause: `run_probes.py`'s original `probe_a_split()` explicitly set the unused trailing `Layer_3..Layer_8` CONSTRUCTION fields to `""` (empty string) rather than leaving them genuinely unset; eppy then emitted literal blank trailing fields in the saved .idf, which EnergyPlus's extensible-field CONSTRUCTION reader parsed as real-but-blank material references rather than absent fields (confirmed: N=8, which fills every available field and leaves none blank, passed cleanly on the first try with the same code path). Fixed by only ever setting the N-1 fields actually needed and leaving the rest untouched (a freshly-loaded baseline .idf already has them unset). Reran N=2/N=4 for all 3 buildings via `rerun_a_split_bugfix.py`; all 6 reruns now PASS cleanly. This was a bug in this dispatch's own diagnostic script, not an EnergyPlus or `openubem/` finding — flagged here per the plan's own §1.8/honesty-requirement instruction to report exactly what happened rather than silently re-running until green. The buggy first-attempt `.err`/`.end` files are preserved for audit at `scratchpad/e-la-20-investigation/i05/runs/way_772627076/a_split_n2/` (overwritten by the successful rerun in the same path — the pre-fix text is quoted verbatim below from this session's terminal capture, in `scratchpad/e-la-20-investigation/i05/run_probes_log.txt`).
  3. No other deviations. All probes were scratch-copy IDF edits or explicit call-time parameter overrides (`run_step3`'s own default `thermal_mass=True` for baseline generation only, per plan §3.3/I01's own established pattern) — `envelope_patcher.py`/`builder.py`/`layout_assigner.py` were read for reference (established facts, §4) but never edited. `git status --short openubem/ tests/` confirmed clean (see Test status).
- Test status: **30/30 probe runs (3 buildings × 10 probe variants) PASS after the N=2/N=4 bugfix — zero probe variant reproduces the CTF Fatal on any of the 3 buildings.** Full pass/fail table (`elapsed_s` = EnergyPlus wall-clock, `total_eui` = same 9-meter formula as `t19_harvest_layout_assign.py::_parse_sql`, reused verbatim):

  | probe | way/772627076 (S=0.0428) | way/772627020 (S=0.5141) | way/270445755 (S=2.7789) |
  |---|---|---|---|
  | (a) split N=2 | PASS, 5.78s, EUI=149.008 | PASS, 6.06s, EUI=79.525 | PASS, 5.89s, EUI=69.297 |
  | (a) split N=4 | PASS, 5.87s, EUI=149.004 | PASS, 6.05s, EUI=79.527 | PASS, 6.05s, EUI=69.294 |
  | (a) split N=8 | PASS, 5.84s, EUI=149.004 | PASS, 6.15s, EUI=79.527 | PASS, 6.10s, EUI=69.294 |
  | (b) ConductionFiniteDifference | PASS, **112.06s**, EUI=149.579 | PASS, **124.15s**, EUI=79.518 | PASS, **116.62s**, EUI=69.243 |
  | (c1) T_cap=0.5m | PASS, 5.61s, EUI=149.640 | PASS, 6.05s, EUI=79.768 | PASS, 6.08s, EUI=69.480 |
  | (c1) T_cap=0.3m | PASS, 5.67s, EUI=149.773 | PASS, 6.09s, EUI=79.829 | PASS, 6.19s, EUI=69.521 |
  | (c1) T_cap=0.2m | PASS, 5.70s, EUI=149.807 | PASS, 6.26s, EUI=79.833 | PASS, 5.95s, EUI=69.524 |
  | (c1) T_cap=0.1m | PASS, 5.71s, EUI=149.845 | PASS, 6.23s, EUI=79.839 | PASS, 5.97s, EUI=69.518 |
  | (c2) hybrid T1=0.20m | PASS, 5.94s, EUI=149.849 | PASS, 6.04s, EUI=79.826 | PASS, 6.16s, EUI=69.524 |
  | (c2) hybrid T1=0.10m | PASS, 5.86s, EUI=149.775 | PASS, 6.15s, EUI=79.831 | PASS, 6.09s, EUI=69.500 |

  **Baseline FATAL, quoted verbatim (I01's own `way/772627076` repro, unchanged, for contrast)** — `scratchpad/e-la-20-investigation/i01/way_772627076/eplusout.err`:
  ```
  ** Severe  ** CTF calculation convergence problem for Construction="LA_ROOF_CONSTRUCTION".
  **   ~~~   ** ...with Materials (outside layer to inside)
  **   ~~~   ** (outside)="LA_ROOF_ASSEMBLY"
  ...
  **  Fatal  ** Program terminated for reasons listed (InitConductionTransferFunctions)
  ```
  `.end`: `EnergyPlus Terminated--Fatal Error Detected. 9 Warning; 1 Severe Errors; Elapsed Time=00hr 00min  0.09sec`

  **One probe PASS, quoted verbatim** (`(a) split N=2`, `way/772627076`) — `scratchpad/e-la-20-investigation/i05/runs/way_772627076/a_split_n2/eplusout.end`:
  ```
  EnergyPlus Completed Successfully-- 153191 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  5.59sec
  ```

  **Pre-fix FAIL for the record** (probe-script bug, not an EnergyPlus/`openubem/` finding — see Deviations #2), quoted verbatim from `run_probes_log.txt`/the then-current `eplusout.err` for `a_split_n2`/`way/772627076` before the fix:
  ```
  ** Severe  ** Did not find matching material for Construction LA_ROOF_CONSTRUCTION, missing material =
  ... (×6, one per unused blank trailing Layer_N field)
  ** Severe  ** Errors found in creating the constructions defined with Ffactor or Cfactor method
  **  Fatal  ** GetSurfaceData: Errors discovered, program terminates.
  ```
  This is a **distinct signature from the CTF Fatal** — exactly the kind of "trades the CTF Fatal for a different failure" case the plan's honesty requirement calls out; it was traced to this dispatch's own script (not EnergyPlus, not `openubem/`) and fixed before being counted in the table above.

  **CondFD (probe b) is not silent about severity even though it PASSes**: all 3 CondFD runs carry non-zero `Severe Errors` in their `.end` line (2/3/4 respectively) — confirmed, per-building, to be exclusively the already-logged, out-of-scope `CheckWarmupConvergence: Loads Initialization, Zone="<name>" did not converge after 25 warmup days` signature (E-LA-14/E-LA-19-class, plan §1's exclusion list), one per zone that fails to converge (`ATTIC` only for the smallest/S=0.0428 building, up to `ATTIC`+`CORE_ZN`+2×`PERIMETER_ZN` for the largest/S=2.7789). No `LA_ROOF`/CTF/InitConductionTransferFunctions text appears in any CondFD `.err`. The same signature (with smaller, sometimes-zero counts) also appears in a handful of the (a)/(c1)/(c2) CTF-based passing runs for the two larger buildings (`way/772627020`, `way/270445755`) — e.g. `c1_tcap_0.3` on `way/270445755` shows 4 such severe errors — confirmed identical signature by direct grep, not a new mechanism, and unrelated to which probe shape is used (present or absent essentially at random across probe variants on the same building, consistent with a pre-existing marginal-convergence zone unrelated to the roof-material choice).

  **CondFD runtime cost:** ~112-124s per building vs. ~5.6-6.3s for every CTF-based passing probe on the same building — **~19-21x slower**, consistent across all 3 buildings (smallest: 112.06s vs 5.6-5.9s ≈20x; largest: 116.62s vs 5.9-6.2s ≈19-20x). This is the full annual-simulation cost difference for these small `SmallOffice` buildings; the relative penalty would need re-checking at larger floor areas/zone counts by a future plan, but on this evidence CondFD is a real, non-trivial fleet-scale cost if ever adopted at 150+ buildings.

  **EUI comparison (required physical-plausibility check).** `thermal_mass=False` (`MATERIAL:NOMASS`) EUI for the same 3 buildings, read directly from I02's own `b_patched_mass_false/way_<id>/eplusout.sql` (same 9-meter formula, no new simulation run needed — I02's 4-building sample already includes all 3 of I05's buildings):

  | osm_id (S) | thermal_mass=False EUI (I02) | I05 probes' EUI range | probes' internal spread | probes vs. NOMASS |
  |---|---|---|---|---|
  | way/772627076 (0.0428) | 153.212 | 149.004 – 149.849 | 0.57% | probes 2.2–2.75% *lower* than NOMASS |
  | way/772627020 (0.5141) | 81.108 | 79.518 – 79.839 | 0.40% | probes 1.57–1.96% *lower* than NOMASS |
  | way/270445755 (2.7789) | 70.251 | 69.243 – 69.524 | 0.41% | probes 1.03–1.44% *lower* than NOMASS |

  No ground truth exists here (per plan instruction, not claiming any probe "most accurate"): the 10 probe variants agree with **each other** to within a fraction of a percent (0.4-0.6% spread) on every building — i.e. the *shape* of the fix (split vs. cap vs. hybrid vs. algorithm change) barely matters to the annual EUI answer. All 10 probes differ from the pre-structural-fixes-plan `thermal_mass=False` baseline by a **consistent, small, one-directional** 1-3% (lower), which narrows as S grows (2.2-2.75% at S=0.04 down to 1.0-1.4% at S=2.78) — this is a real, non-negligible but modest EUI effect of *any* thermal_mass=True-preserving fix shape relative to the old no-mass behaviour, not a 20%-scale divergence.
- Notes: **Candidates for a future implementation plan (none adopted, no ranking as "the" fix — decision belongs to that plan's own manager):**
  - **(a) split, even N=2,** clears the Fatal on all 3 buildings with the smallest structural change (same single material object, referenced twice) and *exactly* preserves both R and thermal mass by construction (not an approximation) — the two other CTF-preserving candidates ((c1)/(c2)) only preserve R exactly while trading away some mass. Worth a future plan's attention as the most "faithful to intent" shape, precisely because it changes nothing about the physical assembly EnergyPlus reports, only how it's split into CTF layers.
  - **(c1)/(c2)** also clear the Fatal at every tested cap/split value (down to the smallest tested, 0.1 m), giving a future plan a wide margin of headroom rather than a single point solution — but both deliberately reduce total thermal mass relative to the current `thermal_mass=True` intent (which is exactly why the structural-fixes plan introduced `thermal_mass=True` in the first place, per this plan's Executive Summary) to varying degrees; (c2) preserves more real (masked) mass than (c1) at the same nominal thickness since (c1) also lowers conductivity, an interaction a future plan should weigh explicitly rather than just picking the smallest passing cap.
  - **(b) ConductionFiniteDifference** clears the Fatal too, but at a ~20x runtime cost and while surfacing (not necessarily causing — see Notes above) additional `CheckWarmupConvergence` severe errors; a future plan should treat this as the most expensive and least-vetted-for-side-effects of the three shapes, only worth it if (a)/(c1)/(c2) turn out to have some other blocking problem at fleet scale that this investigation's 3-building sample didn't surface.
  - All three shapes are numerically indistinguishable at the EUI level (sub-1% apart) on this 3-building, S-spanning sample — a future plan should not expect the choice among (a)/(c1)/(c2)/(b) to materially change fleet EUI results, only implementation complexity, fidelity-to-original-intent, and runtime cost.
  - `git status --short openubem/ tests/` returned clean (only pre-existing untracked I03/I04 PNG/CSV files under `openubem/outputs/`, none from I05) — confirmed at the end of this dispatch.

#### CP-INV — investigation synthesis — completed 2026-07-25 (director)

- **Scope:** I01–I05, all five executed, all five independently audited by the director (raw `.err`/`.end` files re-opened directly on disk for I01, I02, I03's two bisection boundary runs, and I05's probe runs — never trusting an employee's printed summary for a load-bearing pass/fail claim). `git status --short openubem/ tests/` clean at every checkpoint: **zero production-code changes across the whole investigation.**

- **Finding — root cause, confirmed (not hypothesized):**
  `patch_envelope()` builds each opaque assembly by holding conductivity fixed at `_K = 0.12 W/m·K` and letting **thickness absorb the entire target R-value**: `Thickness = max(0.01, (1/u) * 0.12)`. That inversion is harmless while the layer is `MATERIAL:NOMASS` (a pure resistance — EnergyPlus never needs a CTF series for it). The structural-fixes plan's T03 fix switched `layout_assign` to `thermal_mass=True`, which turns the same geometry into a real `MATERIAL` with `Density=800`, `Specific_Heat=1000`. For a well-insulated roof this produces a single homogeneous slab **over a metre thick** carrying ~800 kg/m² — a thermal time constant far beyond what EnergyPlus's CTF series solver can expand at the model's 900 s timestep, so `InitConductionTransferFunctions` fails before Warmup or Sizing.
  The controlling group is the Fourier number `Fo = α·Δt/L²` with `α = k/(ρ·cp) = 0.12/(800·1000) = 1.5e-7 m²/s` and `Δt = 900 s` (4 timesteps/hour, read from a real generated IDF, not assumed).
  **This is the thick/high-mass branch of EnergyPlus's own CTF diagnostic, not the "very thin, highly conductive" branch** the structural-fixes plan's E-LA-20 entry leaned toward.

- **The "small scale factor S" framing inherited from the structural-fixes plan is falsified, definitively.** I01 reproduced the Fatal on 11/11 buildings spanning a **65× range of S** (0.0428 → 2.7789) at an *identical* `u_roof_w_m2k = 0.119`. S does not appear anywhere in `patch_envelope()`, and it does not appear in the failure either. Any future plan citing "small-S buildings" as the affected population is citing a disproved claim.

- **Threshold, sharply located (I03, 25 real EnergyPlus runs, fully monotonic, no fuzziness):**
  fails iff `u_roof < ~0.1380 W/m²K`, i.e. iff `Thickness > ~0.8698 m`, i.e. iff `Fo < ~1.785e-4`. Bracket: FATAL at `u=0.137813` (`Thickness=0.870745`), PASS at `u=0.138125` (`Thickness=0.868778`) — a ~0.2% bracket, both boundary runs re-read from raw `.end`/`.err` by the director.

- **Why `nyc_rural` `SmallOffice` (I04) — vintage, not climate zone, and not S.** `SmallOffice`'s base roof U is *banded*: 0.153 (zones 1A-3C), **0.119 (4A-6B)**, 0.097 (7-8). `nyc_rural` (6A) and `nyc_centre`/`urban`/`suburban` (4A) therefore share the **same** 0.119 base — the climate zone is not the discriminant. What differs is `VINTAGE_U_FACTORS`: the 150 `nyc_rural` buildings resolve to `90.1-2013` (factor **1.0** → u=0.119 → 1.0084 m → FATAL) while the other three NYC cells resolve to `DOERefPre1980` (factor **1.6** → u=0.190 → 0.6303 m → PASS). I04 traced the vintage further: `nyc_rural` has exactly **one** real observed `year_built` among the 150, propagated to the other 149 by Tier-2 group-mode imputation. The defect is deterministic and fully reproducible, but its evidential basis is a single OSM tag.

- **Director's own fleet-exposure derivation (the finding no single task was scoped to produce).** Applying I03's threshold to the bundled construction table across every `(archetype_id, climate_zone, vintage)` combination: **204 of 3,248 combinations (6.3%) fall below `u_roof = 0.138` and would Fatal under `thermal_mass=True`** — spanning **6 archetypes** (`SmallOffice`, `SmallOfficeDetailed`, `FullServiceRestaurant`, `QuickServiceRestaurant`, `SmallDataCenterHighITE`, `SmallDataCenterLowITE`), **10 climate zones** (4A-8) and **5 vintages** (90.1-2007 through 90.1-2019). E-LA-20 is therefore **not** a `nyc_rural` curiosity: it is a latent, structural exposure that the 12-cell validation fleet happened to expose in exactly one cell, because that fleet contains almost no modern-vintage buildings in cold zones. Any future fleet with modern-vintage small commercial buildings in zones 4-8 hits the same Fatal.
  Corollary that revises I04's own risk ranking: I04 measured "distance to the cliff" against the *failing* value (1.0084 m) rather than the *threshold* (0.8698 m). Measured correctly, the nearest currently-passing population is **not** comfortable — zones 4A-6B at vintage `90.1-2007`/`90.1-2010` sit at u=0.1558 → 0.7703 m, only **~11% below the cliff**.

- **Scope correction to E-LA-20 itself (see §8 E-LA-22):** the affected population is **150/150 = 100%** of the genuine `nyc_rural` `SmallOffice` buildings, not "150/154 = 97.4%". The 4 exceptions are exactly the 4 `building_tag="hotel"`, fully-data-poor buildings in that cell, which classify as `SmallHotel` at current HEAD; 2 of them are the already-documented E-LA-17/E-LA-15 carryovers. The "4 survivors" were never evidence of a passing sub-regime.

- **Candidate fix shapes (from I05 — 30/30 probe runs PASS, none adopted, ranked for a future plan to decide):**
  1. **(a) multi-layer split, N=2** — splits the slab into N identical sub-layers, preserving total R **and** total mass exactly by construction. Smallest structural change, most faithful to the intent of the `thermal_mass=True` fix. N=2 already suffices.
  2. **(c2) hybrid thin-mass + NOMASS residual** — one modest real `MATERIAL` layer plus a `MATERIAL:NOMASS` layer carrying the residual R. Preserves R exactly, keeps genuine (reduced) mass, and removes the pathological geometry outright.
  3. **(c1) R-preserving thickness cap** — cap thickness, lower conductivity to hold R. Works across all tested caps (0.5/0.3/0.2/0.1 m) but trades away real thermal mass.
  4. **(b) ConductionFiniteDifference** — works, but ~20× runtime (112-124 s vs ~6 s) and least vetted for side effects. Fallback only.
  All four are numerically indistinguishable at the EUI level (<1% spread among probes; a consistent 1-3% below the old `MATERIAL:NOMASS` behaviour). **The choice is about fidelity, complexity and runtime — not about the answer.**

- **Open questions carried forward (not resolved by I01-I05):**
  1. The exact causal chain behind E-LA-22's archetype/vintage divergence at current HEAD (dates and file paths implicate the 2026-07-25 semantic-imputation commit; the chain itself is unproven).
  2. Whether the 204 at-risk combinations should be fixed at the material-construction level (probes above) or upstream, by questioning whether a single-layer `Thickness = R·k` inversion is the right envelope model at all once mass is real. That is a DESIGN-level question this investigation deliberately did not open.
  3. Whether `E-LA-14/E-LA-19` `CheckWarmupConvergence` severes seen alongside several passing probes are surfaced or caused by them — I05 flagged the distinction honestly and did not resolve it.

- **Disposition: investigation complete, findings synthesized, awaiting manager scoping of a follow-up implementation plan.** This plan does **not** close and no fix has been implemented. E-LA-20 stays logged OPEN in the structural-fixes plan's own §8 (frozen, not edited); its `Root cause` is now confirmed by the evidence recorded here. Two new defects logged in this plan's §8: **E-LA-21** (dead `has_fatal` column, reporting-layer, no simulation impact) and **E-LA-22** (T19 archetype/vintage non-reproducibility for data-poor buildings, material for any future cross-generation comparison).

## 8. Error log

#### E-LA-21 — `has_fatal` column is dead fleet-wide in the T17/T18/T19 harvest scripts (reporting-layer defect, no simulation impact) — OPEN, informational — 2026-07-25 (director, during I01 audit)

- **Task:** surfaced as a side finding by the I01 employee; independently re-derived and widened by the director before logging.
- **Symptom:** `scripts/cluster/t19_harvest_layout_assign.py` line 259 tests `has_fatal = "** Fatal **" in err` — single spaces. Real EnergyPlus 23.1 `.err` text is `**  Fatal  **` (two spaces each side), confirmed by direct read of a raw local `.err` this session (`scratchpad/e-la-20-investigation/i01/way_772627076/eplusout.err`). The substring therefore never matches.
- **Scope (director's own independent re-derivation, not the employee's claim):** the employee reported this as affecting the 150 E-LA-20 rows. It is in fact **fleet-wide and total** — `has_fatal.sum() == 0` across all **8,160** rows of `t19_layout_assign_eui.csv`, despite 170 non-success rows. The column carries zero information in every cell and every archetype, not just for this failure mode. `t17_*`/`t18_*` share the same harvest-script lineage and are expected to be identically affected (not re-verified here — out of this plan's scope).
- **Root cause:** string-literal mismatch in the harvest parser. No simulation, IDF, or EUI impact whatsoever — `status`, `n_severe`, and all EUI columns are derived independently and are unaffected.
- **Why it matters anyway:** any past or future analysis that filters or counts on `has_fatal` silently returns nothing. Every E-LA-20 finding in this plan's lineage was reached via `status != "success"` and `n_severe`, so no existing conclusion in the structural-fixes plan or this one rests on it.
- **Resolution:** not attempted — out of this plan's scope (investigation-only, and the file is a `scripts/cluster/` harvest script, not one of the three production modules under investigation). Logged for whoever next touches the harvest scripts.
- **Files touched:** none.

#### E-LA-22 — the 4 `building_tag="hotel"` buildings in `nyc_rural` are recorded as `SmallOffice` in the T19 harvest but classify as `SmallHotel` at current HEAD — local repro of T19 is not archetype-faithful for data-poor buildings — OPEN, material — 2026-07-25 (director, during I03 audit)

- **Task:** surfaced by the I03 employee (Part 1) and cross-noted by I04; independently re-derived and scoped by the director before logging.
- **Symptom:** `t19_layout_assign_eui.csv` records `archetype_id="SmallOffice"` for all **154** `nyc_rural` rows in that group. A fresh `BuildingClassifier().classify()` run at current HEAD assigns `SmallHotel` to 4 of them. Re-enriching one of those 4 with the archetype force-overridden back to `SmallOffice` also resolves a **different vintage** than T19 recorded (`GROUPMODE_MED` → `90.1-2013`, vs. T19's own `data_quality_flag` of `VINTAGE_NAN_PERMISSIVE_DEFAULT`), which flips it from pass to Fatal.
- **Director's own independent re-derivation, directly from the raw fixture** (`docs/docs_VALIDATION/validations/overAll/results/phaseE/nyc_rural/01_buildings.gpkg`), not from any employee artifact: exactly **4** of the cell's 198 buildings carry `building_tag="hotel"`, and they are precisely `way/965718400`, `way/965718401`, `way/965718402`, `way/965718403` — all 4 with `levels=NaN` and `year_built=NaN`. The remaining `SmallOffice` population is `building_tag="yes"` (157 rows). So the 4 anomalous buildings in this whole investigation — plan §3.4's 2 excluded carryovers (E-LA-17, E-LA-15) **and** the 2 "passers" — are exactly the 4 hotel-tagged, fully-data-poor buildings. This is not a coincidence and was not previously noticed.
- **Consequence for E-LA-20's own scope (important, and a *strengthening* of the finding):** the affected population is not "150 of 154 `SmallOffice` (97.4%)". The 4 exceptions are not genuine `SmallOffice` buildings at all at current HEAD. E-LA-20's real scope is **150/150 = 100% of the genuine `nyc_rural` `SmallOffice` population**, with the 4 hotel-tagged buildings being a separate, differently-classified population whose 2 failures are the already-documented E-LA-17/E-LA-15. The "4 survivors" never constituted evidence of a passing sub-regime.
- **Root cause:** not proven, and deliberately not chased — out of this plan's scope. Evidence the director did verify: `openubem/semantic/building_classifier.py` is unchanged since commit `0df422e` (2026-07-03), i.e. it did **not** change between the T19 run (2026-07-24) and now; but `openubem/semantic/imputation.py` (+53 lines) and `openubem/semantic/spatial_impute.py` (+36 lines) **did** change in commit `3a925f9` (2026-07-25, "…height backfill…"), which landed *after* T19 ran. Since all 4 affected buildings are exactly the ones with `levels=NaN`/`year_built=NaN` — i.e. the ones whose classifier inputs come from imputation rather than from real OSM data — the leading hypothesis is that the post-T19 imputation change altered the imputed inputs feeding both classification and vintage resolution for data-poor buildings. **This is a hypothesis supported by dates and file paths, not a demonstrated causal chain.**
- **Why it matters beyond E-LA-20:** any local reproduction of a T19/T18/T17 result at current HEAD may silently diverge for data-poor buildings, in archetype *and* in vintage. Every I01-I05 conclusion in this plan rests on the 150 `building_tag="yes"` buildings, which have real OSM tags and reproduced exactly (I01: 11/11), so **no finding in this investigation is undermined by this** — but a future plan that re-runs fleet comparisons across these generations needs to know. It also connects to the already-carried-forward classification-accuracy drift noted in the input-framework arc.
- **Resolution:** not attempted — investigation-only plan, and this sits in `openubem/semantic/`, outside the three modules under investigation. Logged for a future, separately-scoped plan.
- **Files touched:** none.

_(continue defect numbering from the structural-fixes plan; if this investigation surfaces a genuinely new, distinct defect beyond E-LA-20 itself, it starts at **E-LA-21**. E-LA-20 itself stays logged in the structural-fixes plan's own §8 — this plan's job is to advance its `Root cause`/`Resolution` fields via findings recorded here, not to duplicate its entry.)_

#### E-LA-20 — disposition update: FIXED, verified — 2026-07-25 (appended by F12 of `PLAN_e-la-20_multilayer-fix.md`, this folder)

- **Status change:** `Root cause` (this plan) → **`Resolution: FIXED`**, per the follow-on fix plan in this same folder, `PLAN_e-la-20_multilayer-fix.md`. This entry advances the `Root cause`/`Resolution` fields this investigation's own closing note (above) reserved for future updates; it does not duplicate or edit the original E-LA-20 log entry, which remains in the structural-fixes plan's own §8.
- **Mechanism.** `patch_envelope()` and `builder.py::assign_constructions()` held conductivity fixed (`_K = 0.12 W/m·K`) and let thickness absorb the whole target R (`Thickness = R × _K`), harmless under `MATERIAL:NOMASS` but producing a slab over a metre thick — CTF-unstable — once `thermal_mass=True`. The fix caps the mass layer at a frozen `T_MASS_MAX = 0.35 m` above a frozen engagement threshold `T_ENGAGE = 0.868 m`, carrying the shed R as a `MATERIAL:NOMASS` residual so `U` is preserved exactly. This candidate (c2) shape is **not** this investigation's own I05 recommendation (the mass-preserving multi-layer split, I05 probe (a)) — that candidate was independently re-tested at the fleet's true worst case by the follow-on plan and found to fail at every split count (`F03-R`/fact F-14): splitting preserves total R and mass exactly, hence preserves the total `R·C` the CTF solver actually responds to, so it cannot clear the case that mattered. (c2) was this investigation's own pre-registered reserve candidate, promoted on that measurement.
- **Verified by:** `PLAN_e-la-20_multilayer-fix.md` Phase C — `F08` (11/11 real-EnergyPlus regression on this investigation's own I01/I02 Fatal reproduction set), `F09` (144/144 synthetic sweep, all distinct `(u_roof, timestep)` pairs the construction library can produce), `F10` (adopted simulation baseline proven untouched by construction — it runs `thermal_mass=False` on every built row), `F11-N` (150/150 — the entire fleet population above the engagement threshold — through the real production path, `thermal_mass=True`, 0 CTF Fatal), `F11-N-b` (matched `thermal_mass=False` control over the same 150, also 0 CTF Fatal). Full detail, all raw-artifact citations, and two new non-blocking defects surfaced in the process (`E-LA-23`, warmup-non-convergence; `E-LA-24`, a reporting-only stale-reference bug) are in `COMPLETION_REPORT_e-la-20-multilayer-fix.md`, this folder.
- **This investigation's own two open defects (E-LA-21, E-LA-22, above) were explicitly out of scope for the fix plan and remain OPEN, unchanged by this disposition.**
- **Files touched:** none (this entry is documentation only, appended per the fix plan's F12 task; the fix plan's own progress log and error log, not this file, are the record of the production-code changes).
