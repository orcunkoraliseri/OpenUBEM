# RESUME PROMPT — T11 Phase-E 8,160-building re-run (fresh manager / Opus session)

> **Purpose.** Paste-to-resume briefing so a fresh **Opus manager** session can take over monitoring
> and finishing task **T11** (fold the E-R3-3 classifier fix into the closed Phase-E baseline) without
> re-deriving anything. You are the *manager* (plan/audit/validation-analysis + gate decisions), not an
> executor — cluster ops run in a **Sonnet** employee.
> **Authored:** 2026-07-01 by the dispatching Opus session. **User is away** and authorized autonomous
> handling of the *process* up to — but **not including** — baseline promotion (see §7, the hard gate).

---

## 0. TL;DR — where things stand

- **T11 is GREENLIT + RUNNING.** User un-parked it 2026-07-01 ("go go go" → confirmed "un-park & run T11").
- A **Sonnet cluster employee** (agentId `a1be68fe17bb0e21e`) is re-running all 12 Phase-E cells (8,160
  buildings) on Speed with the corrected classifier, **geometry frozen**, output to a **fresh throwaway
  tree** `phaseE_er33` (baseline never touched).
- Structure: **pilot `la_centre` first → self-verify 5 checks → auto-launch the other 11 cells** (~7–8 h).
- **Your job when the fleet lands:** run the CP-3 before/after validation compare (§6), append the T11
  progress-log entry, and **STOP at the user-sign-off gate** (§7). Do NOT promote the baseline.

---

## 1. Situation (one paragraph)

Phase-E is the 🔒 adopted OpenUBEM baseline (8,160 buildings = 3 cities × 4 density rings). Erratum
**E-R3-3** corrected three archetype classifier cut-points (office total-floor-area bins `<500/<4000` →
`<2322/<9290 m²`; hotel Small/Large `≥4` → `≥5` levels; school Primary/Secondary by level count). At CP-2
(Boston 483 fleet) the fix was **accepted** and proven neutral-to-beneficial on validation (isolated effect:
CV/KS improve, R² unchanged, NMBE slightly more negative from office down-tiering). T11 folds that fix into
the full Phase-E baseline *properly* — a clean classifier isolation re-run — instead of silently. Binding
spec: `docs/docs_ACTIVE/misclassification/PLAN_archetype_threshold_fix_E-R3-3.md` **§6 T11** (read it; it has
Verified mechanics M1–M6 + Execution recipe T11.1–T11.7).

---

## 2. What is running + IDs (as of 2026-07-01 dispatch)

| Thing | ID / path |
|---|---|
| Sonnet cluster employee (resume via SendMessage `to: <id>`) | `a1be68fe17bb0e21e` |
| Employee's tracked completion wait (pilot) | bash job `bwpzi8szt` |
| Manager-side backstop watch (pilot terminal artifact / hang) | bash job `b6d1yw5af` |
| Explore agent that mapped the machinery (done) | `a5931c23a9009b4b4` |
| Output subdir (fresh, throwaway) | `phaseE_er33` |
| Remote fleet dirs (fresh per cell) | `/speed-scratch/o_iseri/fleets/phaseE_er33_<cell>` |

If those background jobs have expired by the time you read this, re-derive state from disk (§4) and, if the
employee is dead, either resume it (`SendMessage to: a1be68fe17bb0e21e`) or drive the remaining cells
yourself by dispatching a **new Sonnet** cluster employee against §6 of the plan.

---

## 3. The method — why this is a clean, non-destructive isolation

- **Driver:** `python scripts/validation/v12_cell_pipeline.py <cell> --output-subdir phaseE_er33` runs a
  whole cell end-to-end: EPW → step1 (fetch/**cache**) → step2 classify (E-R3-3) → step3 IDF gen →
  live_smoke → ship → `sbatch --array=1-N%32` → `poll_cluster` (local 90 s squeue loop) → fetch →
  verify_and_repair → step5 → copy final. (`v12_cell_pipeline.py:946-1087`.)
- **Frozen geometry (THE correctness guard):** `step1_fetch` (`:137-150`) loads
  `%TEMP%/ubem_validation/phaseE_er33/<cell>/01_buildings.gpkg` from cache if present, else re-fetches live
  OSM. The employee **pre-seeded** each cell's work dir with the committed baseline footprints
  (`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg` — raw
  pre-classification OSM: osm_id/function_tag/levels/footprint_area_m2/geometry, no archetype_id). So the
  re-run uses the **exact same buildings** and only the classifier changes. A re-fetch would confound the
  fix with OSM drift — the CP-2 lesson — so **if any cell logs "fetching OSM buildings" instead of "loading
  cached GDF", that cell is INVALID; STOP and report.**
- **Non-destructive:** `--output-subdir phaseE_er33` keys BOTH `final_dir`
  (`docs/validations/overAll/results/phaseE_er33/<cell>/` — note `docs/validations` is a *new* top-level
  tree; the committed baseline is under `docs/docs_VALIDATION/…`) AND `remote_fleet_dir`
  (`phaseE_er33_<cell>`, fresh → the `_remote_results_complete` reuse probe at `:927` can't short-circuit to
  stale baseline sims). The committed `phaseE` baseline is never written.
- `OPENUBEM_RECONSTRUCT_SERVICE_LOADS=0` (already the default at `config.py:81`; set explicitly anyway).
- **Do NOT edit `v12_cell_pipeline.py`** (feature code; the `docs/validations` path staleness is expected and
  harmless — it just makes a fresh tree).

---

## 4. Monitoring — how to read state from disk

The 12 cells: `nyc_centre nyc_urban nyc_suburban nyc_rural la_centre la_urban la_suburban la_rural
austin_centre austin_urban austin_suburban austin_rural`.

- **A cell is DONE** when `docs/validations/overAll/results/phaseE_er33/<cell>/v12_<cell>_gates_report.txt`
  and `05_results.csv` exist (copy_final_deliverables runs last). That gates report contains the archetype
  mix + CBECS gates + headline EUI for the cell.
- **Cluster status (login-node I/O only — never compute there):**
  `ssh o_iseri@speed.encs.concordia.ca "bash -lc 'squeue -u o_iseri'"` and
  `sacct -j <jobid> --format=JobID,State,ExitCode`. Job names are `openubem_<cell>`.
  **Never cancel/touch non-`openubem_` jobs** (e.g. `3J_8C_office`, `t08_*` — other projects).
- **Baseline N per cell** (target sim-success ≈ these): nyc_centre≈737, nyc_urban≈1779, nyc_suburban≈1589,
  nyc_rural≈198, la_centre≈225, la_urban≈617, la_suburban≈1343, la_rural≈142, austin_centre≈413,
  austin_urban≈425, austin_suburban≈437, austin_rural≈245. Total 8,160.
- **Cluster discipline:** `sbatch` only; poll from local, ≥30-min self-checks (prefer event-driven);
  the pipeline's internal 90 s local squeue poll is fine (it's the harvest trigger).

**The pilot's 5 self-verify checks** (must all pass before the 11-cell fan-out): (1) step1 logged "loading
cached GDF" not an OSM fetch; (2) step2 archetype dist shows office **down-tier** (SmallOffice↑,
Medium/LargeOffice↓); (3) live_smoke PASS + array drained; (4) output in `phaseE_er33/la_centre/` and the
committed `docs/docs_VALIDATION/…/phaseE/la_centre/` baseline unchanged; (5) remote dir was
`phaseE_er33_la_centre`.

---

## 5. Recovery — if the employee stalled or died

- **Passive-wait failure mode (watch for it):** this employee already once ended its turn as an untracked
  "I'll resume when notified" wait — nothing woke it. If it goes silent with the run unfinished, resume it
  (`SendMessage to: a1be68fe17bb0e21e`) and insist it arm a **tracked** wait (Bash `run_in_background` until-loop
  that exits on success OR failure markers) before ending a turn.
- **Cells are resumable/idempotent:** re-running `v12_cell_pipeline.py <cell> --output-subdir phaseE_er33`
  regenerates IDFs and, if the remote fleet already holds complete results, `_remote_results_complete`
  skips re-sim and just harvests. Re-seed the frozen `01_buildings.gpkg` first if `%TEMP%` was wiped.
- **Never run E+/Python compute on the login node.** If you must drive cells yourself, dispatch a **Sonnet**
  employee — do not run the cluster loop in the Opus manager session.

---

## 6. CP-3 validation compare (T11.6) — YOUR manager deliverable when the fleet lands

Goal: a **before/after** table, `phaseE_er33` (after) vs the committed `phaseE` baseline (before), on the
same metrics as `REPORT_phaseE_final.md`. This is validation analysis → do it in the **Opus manager
session** (like the CP-2 diagnostic). Do **not** just run `scripts/validation/phaseE_rescore.py` — it
hardcodes the `phaseE` baseline path and would overwrite `REPORT_phaseE_final.md`.

**Inputs:**
- After: `docs/validations/overAll/results/phaseE_er33/<cell>/05_results.csv` × 12.
- Before: `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/05_results.csv` × 12 (committed).
- CBECS regional refs: `inputs/reports/cbecs_2018_middle_atlantic_eui.csv` (nyc→middle_atlantic),
  `…_pacific_eui.csv` (la→pacific), `…_west_south_central_eui.csv` (austin→west_south_central).
- Gate math: `from openubem.results import compute_validation_gates` — call per city with
  `compute_validation_gates(results_gdf, reference_path=<region_csv>)` → returns cbecs_nmbe / cbecs_r2 /
  cbecs_cv_rmse / cbecs_ks_d. (Same helper used in CP-2; excludes apartments+data centers from all gates,
  OpenUBEMUnknown from R² only.)

**Author a small read-only compare script** (scratchpad; mirror the CP-2 `diag_cbecs_drift.py` idiom). For
each city compute, before vs after: (a) **city Overall median total EUI** (success rows, exclude
OpenUBEMUnknown) and delta% vs the measured anchor; (b) the **4 CBECS gates**; (c) the **archetype-mix
shift** (value_counts of `archetype_id`, focus offices — SmallOffice / MediumOffice / LargeOffice and #
flipped). Print a before/after table; save any figure to `openubem/outputs/` (flat).

**Baseline "before" numbers to reproduce/beat (REPORT_phaseE_final §3b/§6/§9):**

| City | Overall median EUI | measured | delta% | R² | CBECS NMBE | CV(RMSE) | KS_D |
|---|---|---|---|---|---|---|---|
| NYC (middle_atlantic) | 165.7 | 219.2 | −24.4% | 0.895 | −10.6% | 38.0% | 0.2563 |
| LA (pacific) | 107.2 | 113.6 | −5.6% | 0.924 | −20.5% | 60.6% | 0.2376 |
| Austin (west_south_central) | 120.4 | 162.0 | −25.7% | 0.718 | −11.9% | 47.5% | 0.3018 |

Segment anchors (before): NYC Office 147.0/183.9 (−20.1%), NYC Multifamily 204.5/226.2 (−9.6%); LA Office
131.8/121.5 (+8.5%), LA Multifamily 105.5/115.8 (−8.9%), LA Warehouse 20.5/33.9 (−39.6%); Austin Office
116.4/162.3 (−28.3%).

**Expected direction (from the CP-2 isolation):** offices down-tier to the lower-intensity SmallOffice DOE
template → city median EUI a touch lower → NMBE slightly more negative; R² ~flat-to-up; CV/KS ~flat-to-tighter.
**Interpretation rule:** zero-fitted-params holds and CBECS gates are **report-only** (V-R5-5 / M-R2-4) — a
correct classifier fix is **not vetoed** by CBECS movement. NMBE/R² are the hard gates; the story is the
distribution shape + the office reclassification, not chasing the CBECS mean.

Present the before/after table to the user for the T11.7 decision. **Then STOP.**

---

## 7. 🔴 HARD GATE — T11.7 promotion is USER-SIGN-OFF ONLY

Do **NOT**, without the user's explicit acceptance of the CP-3 deltas:
- overwrite / promote `phaseE_er33` into the committed `phaseE` baseline (`docs/docs_VALIDATION/…`),
- regenerate `REPORT_phaseE_final.md` or its figures against the new run,
- update the Phase-E memory/checklist to say the baseline moved.

Promotion overwrites the 🔒 adopted baseline — hard to reverse and load-bearing. The user going out and
saying "handle the process" authorizes running the sim + producing the comparison; it does **not** authorize
replacing the baseline. Park at the sign-off gate and wait.

---

## 8. Bookkeeping duties (do these as you go)

- **Progress log:** append/finalize the **T11** entry in
  `docs/docs_ACTIVE/misclassification/PLAN_archetype_threshold_fix_E-R3-3.md` **§8** (format per its
  template). An interim "IN PROGRESS" T11 entry is already there — finalize it when the fleet lands + CP-3
  is done (sim success counts, archetype before/after, CBECS before/after table, deviations, user ruling).
- **§0 checklist:** the T11 line is `GREENLIT + DISPATCHED`; flip to reflect fleet-complete / CP-3-reported
  when true (leave unticked until user sign-off).
- **Memory:** update `…/memory/project_archetype_threshold_E-R3-3.md` (already has the T11 dispatch block) +
  the `MEMORY.md` index line when the state materially changes. Do NOT mark the arc closed until the user
  accepts and (if accepted) the baseline is promoted.
- **`docs/PROJECT_CHECKLIST.md`:** keep the E-R3-3 sub-arc block current (user's monitoring surface).
- **Figures → `openubem/outputs/`** (flat). **No `.py` under `docs/`.** Git handled externally (never commit).

---

## 9. Pointers

- Binding spec: `docs/docs_ACTIVE/misclassification/PLAN_archetype_threshold_fix_E-R3-3.md` §6 **T11** + §2.
- Baseline report: `docs/docs_DONE/hvac-ServiceLoads/REPORT_phaseE_final.md` (§3b/§6/§9 = the "before").
- Pipeline driver: `scripts/validation/v12_cell_pipeline.py` (`run_cell` :946-1087; `CELL_CONFIGS` :45-106).
- Rescore (reference only — do NOT run against baseline): `scripts/validation/phaseE_rescore.py`.
- Cluster runbook: `scripts/cluster/README.md`. Gate math: `openubem/results/__init__.py:209` (`compute_validation_gates`).
- Arc memory: `…/memory/project_archetype_threshold_E-R3-3.md`. CP-2 diag idiom to mirror:
  `…/scratchpad/diag_cbecs_drift.py`.

---

## 10. Kick-off line for the fresh session (what to tell the user / yourself)

> "Resuming T11 (Phase-E 8,160 re-run, E-R3-3). Read `docs/RESUME_T11_fresh_manager_session.md` and the plan
> §6 T11. Check fleet state on disk (§4) + cluster (`squeue -u o_iseri`). If cells still running, monitor
> event-driven (≥30-min). When all 12 land, run the CP-3 before/after compare (§6), report the table, and
> STOP at the user-sign-off gate (§7) — do not promote the baseline. Cluster ops via a Sonnet employee only;
> never login-node compute."

*OpenUBEM — manager handoff. E-R3-3 / T11. 2026-07-01.*
