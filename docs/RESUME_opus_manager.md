# RESUME — Opus Manager (Phase-E fan-out in progress)

> Hand-off for a fresh Opus **manager** session. Read this, then act.
> **Updated:** 2026-06-27 ~13:10.

## State in one line
Phase-E "full realism" (physical HVAC + DHW/cooking/refrigeration; old reconstruction RETIRED).
CP-D2 pilot PASSED, user ruled **Accept + fan out**. The **11-cell fan-out is RUNNING** — cell 1 of 11
(`nyc_centre`) cluster array COMPLETED 12:22; rest run sequentially (~8h total). **NO monitoring.**
When it finishes: check each cell's results, then prep **T18 (final report) — HELD for the user.**

## Who you are
Manager: read specs, write/audit plans, make validation + DESIGN calls, keep `PROJECT_CHECKLIST.md`
current. Fresh Sonnets run E+ / bulk work. **Exception** ([[feedback_opus_writes_delicate_code]]): manager
writes delicate/load-bearing code (HVAC dispatcher, cooking emitter, gate specs, fan-out plumbing) itself.

## Your first action — when the fan-out finishes
The fan-out is bg bash log `…/f4548…/scratchpad/phaseE_fanout.log` (driver `phaseE_fanout.sh`), one SLURM
array at a time, NO monitoring — one completion notification fires at the end. When done, for each of the
11 cells (`nyc_*`, `la_centre/suburban/rural`, `austin_*`):
1. Confirm `docs/validations/overAll/results/phaseE/<cell>/05_results.gpkg` exists.
2. Read its `dropped_buildings.csv` (expect ≤ tolerance = `max(5,1%)`, mostly degenerate Warehouses).
3. Sanity-check archetypes (schools ~175–240, no heating runaway).
4. In the log, a cell that hard-stopped shows `FANOUT END … exit=2` (B2 systematic failure) and does NOT
   abort the loop → re-run just that one cell (needs a staging clear first, see Gotchas).

Then **prep T18** (final 3-city + national CBECS re-score + figures + `REPORT_phaseE_final`) — **HELD for
the user; do not finalize without them.** Lead the narrative with **R² ≈ 0.9 + real-data city anchors
(EBEWE/LL84)**; report the CBECS NMBE residual honestly (below).

## CP-D2 result (the accepted zero-fitted-params baseline)
- CBECS **NMBE −17.6%**, **R² 0.91** (was 0.40), CV(RMSE) 58% (report-only). **EBEWE LA −8.6%.** G2 PASS.
- The under-prediction is a **structural DOE-prototype-vs-CBECS office offset, NOT a bug.** Offices
  (112/161 commercial buildings) sit below CBECS Office 154 — SmallOffice 98 (`equipment_w_m2=6.78`),
  Medium/Large ~135–138 (`10.76`); those are the DOE prototype values themselves in
  `doe_prototype_loads.json`. Same residual STOP-decided at R6-4B, confirmed V16–V19. Phase-E already
  halved the gap (−39%→−16%). Closing further = fitting office loads to the benchmark = breaks
  zero-fitted-params → **accept-and-report.** (The CP-D −3.1% "centered!" was a school/exhaust **bug
  artifact**; fixing the bugs revealed the honest mean.)

## Frozen code — do NOT edit (proven correct on-disk, no re-sim needed)
`openubem/idf/cooking.py` + `data/loads/cooking_by_archetype.json` (kitchen-exhaust fix — scaled exhaust
on 5am–1am schedule; killed the PrimarySchool runaway 609→179 / 2175→243), `openubem/idf/hvac.py`
(single-zone PSZ guard + Warmest SAT reset), and their tests.

## Gotchas
- **Staging-poison (re-runs only):** re-running an already-run cell can ship STALE IDFs. Before any cell
  *re-run* clear under `…/Temp/ubem_validation/phaseE/<cell>/`: `fleet_staging`, `sim_out`, `step3`,
  `04_simulation_manifest.parquet`, `results` — PRESERVE `01_buildings.gpkg`, `02a_climate_epw.parquet`,
  `weather/`. Fresh cells are safe.
- **B2 is the sole fail-tolerance authority** (`v12_cell_pipeline.py` `run_cell` ~line 1039);
  `verify_and_repair` no longer hard-exits (logs + defers). A *systematic* failure (>max(5,1%)) makes B2
  `exit 2` that cell — that's correct, investigate don't suppress.
- CV(RMSE)/KS shape gates fail structurally (archetype-deterministic UBEM) → report-only, never tune.
- The E+ 10 m³ volume clamp is universal & benign — don't re-chase it.

## Standing governance
- **Never git commit/add** (external tool auto-commits). Never edit OVERVIEW/DESIGN, root `main.py`, or
  gate/core-math. No `.py` under `docs/`. Figures → `openubem/outputs/` flat.
- **Cluster ABSOLUTE:** never run blocking compute on the Speed login node; `sbatch` fire-and-forget;
  one array in queue at a time.
- Model-cost: Sonnet/Haiku for execution+monitoring (≥30-min, prefer event-driven); Opus for reasoning.
- Stop-and-ask on ambiguity. **T18 is HELD for the user.**

## Pointers
- Plans: `docs/docs_ACTIVE/hvac-ServiceLoads/PLAN_phaseE_full_realism.md` (parent T16/T17/T18),
  `…/PLAN_phaseE_CPD_remediation.md` (§8–§11 = decision record incl. CP-D2 ruling).
- Harness: `scripts/validation/v12_cell_pipeline.py` (`run_cell`, `--output-subdir phaseE`, 12-cell
  `CELL_CONFIGS` ~line 45), `scripts/validation/phaseE_pilot.py` (single-cell la_urban).
- Results: `docs/validations/overAll/results/phaseE/<cell>/` · Checklist: `docs/PROJECT_CHECKLIST.md` §E
- Memory: `project_phaseE_full_realism` (live thread).
