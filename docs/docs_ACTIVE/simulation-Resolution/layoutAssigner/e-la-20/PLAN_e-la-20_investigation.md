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

- [ ] **I01** — Reproduce E-LA-20 locally on a representative sample of the 150 affected `nyc_rural` `SmallOffice` buildings
- [ ] **I02** — Isolate the mechanism: scaled-only vs. patched-without-thermal-mass vs. patched-with-thermal-mass, same buildings, to confirm `thermal_mass=True` is the actual trigger (not a confound)
- [ ] **I03** — Characterize the numeric regime: correlate scale factor S and `u_roof_w_m2k` (and the material properties they drive) against pass/fail, across all 154 `nyc_rural` `SmallOffice` buildings plus a cross-cell `SmallOffice` control sample
- [ ] **I04** — Determine why `nyc_rural` `SmallOffice` specifically — compare `u_roof_w_m2k`/scale-factor distributions across cells×archetypes to distinguish a genuine numeric outlier from an incidental concentration of extreme-S buildings
- [ ] **I05** — Diagnostic-only mitigation probes (not a fix decision) to pre-vet candidate fix shapes for a future implementation plan
- [ ] 🔶 **CP-INV** — investigation checkpoint: root cause confirmed (or best-evidence hypothesis), candidate fix shapes proposed (manager)

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

_(empty — append one entry per completed task, per the standard format: `#### IXX — <title> — completed YYYY-MM-DD` / `- Artifacts:` / `- Deviations:` / `- Test status:` / `- Notes:`)_

## 8. Error log

_(empty — continue defect numbering from the structural-fixes plan; if this investigation surfaces a genuinely new, distinct defect beyond E-LA-20 itself, it starts at **E-LA-21**. E-LA-20 itself stays logged in the structural-fixes plan's own §8 — this plan's job is to advance its `Root cause`/`Resolution` fields via findings recorded here, not to duplicate its entry.)_
