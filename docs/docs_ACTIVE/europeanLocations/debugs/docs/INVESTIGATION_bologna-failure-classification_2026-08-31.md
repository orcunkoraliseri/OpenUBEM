# INVESTIGATION — classify Bologna's 190 Speed-failed rows (`D-EU-45`)

- **Arc**: European locations × Step 8, `EU-16`. **Plan**: `implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`.
- **Trigger**: manager recommendation, 2026-08-31 (Bologna is the largest unclassified failure population in
  the arc — never touched since wave-1, unlike Madrid/Lyon/London whose failures are root-caused as
  `FINDING 210` / `D-EU-43`).
- **Scope**: **classification only. No fix, no rebuild, no IDF change, no `sbatch` submission.** This is a
  read-only measurement task, same shape as the step that first split Madrid/Lyon/London's wave-1 failures
  into `FINDING 210` vs zero/negative-surface-area (`RESULTS_EU-11.md` §"`D-EU-42`/`D-EU-43` recovery").
- 🔴 **Do NOT edit** `content/walkthrough_progress_log.csv`, `implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`,
  or `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. Write findings only to this file's own report
  section below (or a fresh file next to it if you need one). The manager folds results into the shared docs.

## What is already known — use it, do not re-derive

- Job `1299947` (`IT-BOL-GALVANI2`, wave 1, 2026-08-30): 1,014 `COMPLETED` / 177 `FAILED` / 13 `TIMEOUT` / 1,204
  total (`RESULTS_EU-11.md` line 46-47).
- Results tree: `/speed-scratch/o_iseri/fleets/EU11_IT-BOL-GALVANI2/out/<stem>/` (`eplusout.sql`, `eplusout.eio`,
  `eplusout.end`, `eplusout.err`). Local manifest already on disk:
  `openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2/<slug>_manifest.csv`.
- Madrid/Lyon/London's `FAILED` rows split into exactly two signatures: `FINDING 210` (vertex-size-mismatch at
  `GetSurfaceData`, before warmup — see `OpenUBEM_debug_References.md` "European locations EU-16" chapter) and
  zero/negative-surface-area (`D-EU-43`). Lyon's 9 residual `TIMEOUT`s show `eplus_return_code=0`,
  `severe_errors=0`, `fatal_errors=0`, blank `heating_kwh`, no `task.rc` (SLURM killed mid-run,
  `RESULTS_EU-11.md` lines 207-212) — use this as the reference shape for what a genuine timeout looks like.

## Task

1. From the local manifest, list the 177 `FAILED` + 13 `TIMEOUT` Bologna stems (building_id / stem / task
   index).
2. For every `FAILED` stem, read `eplusout.err` (first ~20 lines is enough) — from local harvest if already
   present, otherwise fetch remotely (lightweight only: `scp`/`tar` from the Speed login node, **never**
   `srun`/`ssh … python`, per the arc's standing cluster rules). Bucket every stem into an exact error-message
   signature (e.g. `FINDING 210`'s literal `Vertex size mismatch...`, or something else entirely — do not
   assume it is `FINDING 210` until the message is read).
3. For every `TIMEOUT` stem, check for the same signature as Lyon's 9 (blank `task.rc`, EnergyPlus working
   files present, no severe/fatal in what output exists) or something different (e.g. a genuinely larger
   building needing more walltime).
4. Report a table: signature → count → one verbatim `.err`/log excerpt per signature → a one-line root-cause
   hypothesis (no fix). State explicitly whether any bucket exactly matches `FINDING 210`'s existing gate scope
   (which would mean the existing fix, unmodified, likely recovers it) or is a genuinely new failure mode.

## Report back (to the manager, not into shared docs)

Signature table with counts; one excerpt per signature; hypothesis per signature; explicit statement of
whether `FINDING 210`'s existing fix plausibly covers any bucket. Under 300 words. Do not propose or take any
remediation step.
