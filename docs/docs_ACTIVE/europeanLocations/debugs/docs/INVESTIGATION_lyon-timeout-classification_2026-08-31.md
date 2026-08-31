# INVESTIGATION — classify Lyon's 9 residual `TIMEOUT` failures (`D-EU-46`)

- **Arc**: European locations × Step 8, `EU-16`. **Plan**: `implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`.
- **Trigger**: manager recommendation, 2026-08-31. Lyon's `FINDING 210`/`D-EU-43` casualties are fully
  recovered (0 residual); the 9 remaining failures are wave-1 `TIMEOUT`s, already partly diagnosed
  (`RESULTS_EU-11.md` lines 207-212: `eplus_return_code=0`, `severe_errors=0`, `fatal_errors=0`, blank
  `heating_kwh`, no `task.rc` — SLURM killed the task before its own cleanup step, working-dir files still
  present).
- **Scope**: **classification/diagnosis only. No fix, no rebuild, no `sbatch` submission.** Confirm and extend
  the existing partial diagnosis; do not resubmit.
- 🔴 **Do NOT edit** `content/walkthrough_progress_log.csv`, `implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`,
  or `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. Write findings only to this file's own report
  section (or a fresh file next to it). The manager folds results into the shared docs.

## What is already known — use it, do not re-derive

- Job `1299945` (`FR-LYO-HAUTCOEURPENTES`, wave 1): 262 `COMPLETED` / 26 `FAILED` / 9 `TIMEOUT` (297 total).
  The 26 `FAILED` are fully recovered under `D-EU-42`/`D-EU-43`. The 9 `TIMEOUT`s are untouched.
- Results tree: `/speed-scratch/o_iseri/fleets/EU11_FR-LYO-HAUTCOEURPENTES/out/<stem>/`. Local manifest:
  `openubem/outputs/eu_evidence/EU-11/FR-LYO-HAUTCOEURPENTES/<slug>_manifest.csv`.
- Submission script: `scripts/cluster/submit_fleet_t08.sbatch` (or its EU-11 equivalent — locate the exact
  script that fired job `1299945` and read its `--time=` / walltime setting).
- Cluster hard rules apply: lightweight-only on the login node (`scp`/`tar`/`squeue`/`sacct`), never
  `srun`/`ssh … python`, never compute there.

## Task

1. Identify the exact 9 Lyon stems (building_id / stem / task index) from the manifest.
2. Confirm, for each, the same signature already reported (blank `task.rc`, EnergyPlus working files present
   — `in.idf`, `expanded.idf`, `Energy+.idd`, `epluszsz.csv` — no severe/fatal). Flag any stem that does *not*
   match this signature.
3. Find the walltime the array was submitted with (`sacct -j 1299945 --format=JobID,Timelimit,Elapsed -X` for
   the specific task indices, plus the sbatch script's `--time=`) and report how close each timed-out task got
   to the limit, if that is recoverable from `sacct`.
4. Characterize what is different about these 9 buildings vs the 262 that completed normally — building
   footprint area, storey count, zone count, or IDF size (`wc -l` on the built IDF, or read from the
   manifest/prepared_buildings.csv) — to test the hypothesis that they are simply larger/more complex, not a
   defect.
5. State a recommendation (walltime bump to X, or something else) — **recommendation only, do not submit.**

## Report back (to the manager, not into shared docs)

The 9 stem IDs; confirmed/not-confirmed signature per stem; elapsed-vs-limit if available; the
size/complexity comparison; one recommended fix with rationale. Under 250 words. Do not take any remediation
step.
