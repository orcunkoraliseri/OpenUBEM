# MEASUREMENT — OPEN-09 T13: non-convergence population re-derived on run 4

**Date:** 2026-08-19 · **Task:** T13 of `PLAN_twenty-items-2026-08-19.md`

## 1. What was measured

Fleet-wide `Inside surface heat balance did not converge` warning census over run 4
(`open48_refleet4`, F1/F2 — 8,160 buildings, `auto` mode, `<cell>/sim_out/<stem>/eplusout.err`),
using the same regex the project's own OPEN-09 census scripts use
(`scripts/analysis/open09_fleet_err_taxonomy.py:42`, `scripts/analysis/open56_fleet_cost_stratified.py:60`).
Script: `scripts/analysis/open09_run4_rederivation_2026-08-19.py`. Output:
`openubem/outputs/comparisons/open09_run4_perbuilding.csv` (8,160 rows).

## 2. Result: unchanged, exactly

| | run 2 (prior measurement) | run 4 (this task) |
|---|---:|---:|
| buildings with >=1 non-convergence warning | 16 / 8,160 (0.1961 %) | **16 / 8,160 (0.1961 %)** |
| by cell | la_centre 2, la_rural 10, la_suburban 3, la_urban 1, all others 0 | **identical, cell for cell** |

**The population and the rate are byte-identical to run 2.** Neither the OPEN-55 Unknown-donor
screen nor the OPEN-35 storey-imputation change moved this population at all — both changes touch
different buildings than OPEN-09's 16.

## 3. X03 anchor (hard rule: reproduce the control or the join is wrong)

The 10 X03 control buildings (`la_centre` way_427817687/way_428015178; `la_suburban`
way_442633387/way_442634081/way_442634778; `la_rural` way_472961043/way_472961089/way_472961090/
way_472961093/way_472961164) — all found, all `success`, all carrying exactly **15** warnings each
in run 4. **Sum = 150, matching the run-2 anchor exactly.** The join is verified correct.

## 4. The 6 OPEN-56/OPEN-42 face-(ii) Warehouse fatal buildings, checked in run 4

All 6 (`la_rural` way_472960972/way_472961034/way_472961088/way_472961091/way_472961171,
`la_urban` way_402215469) are present in run-4's `sim_out` and are **still `not_simulated`
(fatal)** — the OPEN-56 remedy is unauthorised and unapplied, so this is the expected, unchanged
result, not a regression. New observation, not previously recorded: each of the 6 also carries
exactly **15** `Inside surface heat balance did not converge` warnings in its `.err`, the same count
as the 10 successful X03 buildings — i.e. these buildings sit inside OPEN-09's population by the
same signature, they simply fail for the separate, already-established OPEN-56 reason before that
matters operationally.

## 5. 16-building overlap: still 16

Union of the 10 X03 buildings and the 6 Warehouse fatals = 16 distinct buildings. All 16 are present
in run 4; all 16 still carry >=1 non-convergence warning. **The overlap the register records
("OPEN-09 and OPEN-56 are independent defects that overlap on 16 buildings") reproduces exactly on
run 4 — 16, not more, not fewer.**

## 6. What this does and does not settle

**Settled:** OPEN-09's population, rate, and its overlap with OPEN-56 are unchanged by run 4. The
64 % vs 5.3 % matched-control figure from C06 is a separate, fixture-specific controlled experiment
(`thermal_mass=True` vs `False` on a 150-row `nyc_rural`/`SmallOffice` population), not a fleet
incidence rate, and this task does not re-run it — that experiment's own population is unrelated to
which fleet run is current.

**Not attempted, and not needed for this task:** re-deriving the ≈3.66 % fleet EUI projection
(register's consequence (a)) — that remains a projection, out of scope here as it was before.

## Artifacts

- `scripts/analysis/open09_run4_rederivation_2026-08-19.py`
- `openubem/outputs/comparisons/open09_run4_perbuilding.csv`
