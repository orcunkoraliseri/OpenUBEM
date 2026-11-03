# MEASUREMENT — OPEN-56/OPEN-09: fleet `.err` census on the adopted run (run 4)

**Date:** 2026-08-20 · **Task:** T03 (amended) of `PLAN_ten-live-items-2026-08-20-evening.md`
**Population:** all 8,160 `auto`-mode buildings in run 4 (`open48_refleet4`, D1), one row per
`<cell>/sim_out/<stem>/eplusout.err`. **Denominator: 8,160** throughout (D5).

## 1. What was measured

Every run-4 `.err` file scanned once for four independent signals: `Indicated Zone Volume <= 0.0`
(OPEN-56 volume-stub warning), `Inside surface heat balance did not converge` (OPEN-09 — **not**
`CheckWarmupConvergence`, which has 0 occurrences in the auto corpus per the task's amendment),
`** Severe **`, and `**  Fatal  **` (two-space form), the last two via the shared
whitespace-tolerant matchers `openubem.results.err_parse.SEVERE_RE` / `FATAL_RE` (E-LA-21/OPEN-45).
Archetype joined from `openubem/outputs/comparisons/open61_census_fleet.csv` on
`(cell, osm_id)`; 8,152/8,160 joined, 8 unjoined (that census has 8,152 rows, run 4 has 8,160).

Script: `scripts/analysis/open56_open09_run4_err_census_2026-08-20.py`. Output:
`openubem/outputs/comparisons/open56_open09_run4_err_census_2026-08-20.csv` (8,160 rows).

## 2. Results

- **C7 — file count:** 8,160 / 8,160 scanned, no short cells.
- **C8 — OPEN-56 volume-stub, run 4 vs run 2:** run 4 **8,160 / 8,160 (100.0000 %)**; run 2 (prior)
  8,160 / 8,160 (100.00 %). **Unchanged** — the stub is present in every run-4 building too.
- **C9 — OPEN-09 non-convergence, must reproduce 16/8,160:** run 4 reproduces **16 / 8,160
  (0.1961 %)** exactly, cell split **la_centre 2, la_rural 10, la_suburban 3, la_urban 1, all
  others 0** — byte-identical to `extra/MEASUREMENT_open-09_run4-rederivation.md` §2. **PASS.**
- **Severe:** 26 / 8,160 buildings carry ≥1 `** Severe **` line.
- **Fatal (two-space):** 7 / 8,160 buildings carry ≥1 `**  Fatal  **` line — `la_rural`
  way_472960972/way_472961034/way_472961088/way_472961091/way_472961171, `la_urban`
  way_402215469, `nyc_centre` way_266034056.
- **C10 — fatal reconciliation:** 7 fatal buildings vs 7 non-`success` rows in run 4's
  `05_results.csv` — **equal, reconciles exactly.**

## 3. Per-cell and per-archetype breakdown

Per-cell counts (volstub / converge / severe / fatal, out of the cell's own total) and
per-archetype counts are both in the CSV and in the script's stdout; volume-stub is 100 % in
every cell (all 12/12). Non-convergence and severe/fatal concentrate in `la_rural` (Warehouse
archetype: 10/32 non-convergence, 1 severe, 0 fatal at the join level — the 5 `la_rural` fatals
are Warehouse buildings per the OPEN-56/OPEN-42 face-(ii) set) and are otherwise sparse.

## 4. What this does and does not settle

**Settled:** OPEN-56's 100 % volume-stub rate holds on the adopted run, at full census, not just
run 2 or an intervention sample. OPEN-09's 16-building population and cell split reproduce exactly
on run 4, independently confirming T13. The severe/fatal census on run 4 has never been taken
before this task; it now exists and reconciles with the recorded `simulation_status`.

**Not attempted:** no remedy is proposed for OPEN-56 or OPEN-09 here (rule 1). No cause is assigned
to the 7 fatals or 26 severes beyond what T04/OPEN-38 already covers for the fatal set.

## Artifacts

- `scripts/analysis/open56_open09_run4_err_census_2026-08-20.py`
- `openubem/outputs/comparisons/open56_open09_run4_err_census_2026-08-20.csv`
