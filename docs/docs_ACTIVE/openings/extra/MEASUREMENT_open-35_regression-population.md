# MEASUREMENT — OPEN-35 run-4 regression: one building or a population?

> T04 of `implemenation/PLAN_twenty-items-2026-08-19.md`. Script:
> `scripts/analysis/open35_regression_population_2026-08-19.py`. Output:
> `openubem/outputs/comparisons/open35_regression_population_2026-08-19.csv` (9 rows). Sources:
> `%LOCALAPPDATA%/Temp/open48_run4/<cell>.log` (repair census, read directly from pipeline log
> lines — not inferred), `openubem/outputs/comparisons/open35_fallback_agreement_scope.csv`
> (`changed_scope_b == True`, the 21-building set whose `levels` the OPEN-35 fix imputes),
> run-4 `results/05_results.csv` all twelve cells (matched control).

## Control (must pass before the finding is trusted)

Required: the repair census must recover exactly the buildings named in `nyc_centre`'s own log
line `Repaired and resimulated: [...]` — no more, no fewer.

Log line (`open48_run4/nyc_centre.log:3044`), de-duplicated: `way_260180778, way_265302168,
way_266034056, way_266149332, way_266170756, way_266170765, way_288448678` — **7 buildings.**

This task's independently parsed census for `nyc_centre` (from the same log's `zero-area surfaces
stripped` / `rerouted to one_zone_per_floor` / `still failed after reroute` lines, parsed with a
regex written for this task, not copied from the summary line): **the same 7, exactly — no more,
no fewer.** Control passes.

## Answer: it is a population, not one building — but the population is small, structured, and mostly survives

**The regression building, `nyc_centre / way/266034056`, is not the only one at risk, but it is the
only one that actually failed to complete.** Three separate facts, none of which alone settles the
question:

### 1. Fleet-wide repair census: 9 buildings needed repair, only 2 were dropped

| cell | osm_id | stripped | rerouted | dropped after reroute |
|---|---|:-:|:-:|:-:|
| la_centre | way/319507579 | yes | yes | no |
| la_urban | way/402215469 | yes | yes | **yes** |
| nyc_centre | way/260180778 | yes | yes | no |
| nyc_centre | way/265302168 | yes | yes | no |
| nyc_centre | way/266034056 | yes | yes | **yes** |
| nyc_centre | way/266149332 | yes | yes | no |
| nyc_centre | way/266170756 | yes | yes | no |
| nyc_centre | way/266170765 | yes | yes | no |
| nyc_centre | way/288448678 | yes | yes | no |

`way/402215469` (la_urban) is **not** an OPEN-35 building — it is the known OPEN-42/OPEN-56
Warehouse placeholder building (pre-existing `footprint_area_m2 = 200.0` in the baseline too, per
F8 and the register's OPEN-56 retraction note). Its drop is unrelated and excluded from what
follows.

### 2. Of the 21 Scope-B (imputed-levels) buildings, 4 needed repair and 1 (4.8 %) was dropped

Cross-tabulating the repair census against `open35_fallback_agreement_scope.csv`'s 21-building
`changed_scope_b` set:

| | n | needed repair | repair rate | dropped |
|---|---:|---:|---:|---:|
| **Scope-B buildings (imputed `levels`)** | 21 | 4 | **19.0 %** | 1 (`way/266034056`) |
| Matched control — non-Scope-B, real (observed) `levels ≥ 10` | 414 | 4 | **0.97 %** | 0 |

**The Scope-B population's repair rate is ~20× the matched-control rate.** This is a real,
measured elevation, not noise — the fix's interaction with tall imputed geometry is a genuine
population effect, not a one-building fluke, matching the register's own qualitative claim
("marginal interaction across that group, not a one-off").

### 3. But the elevated risk is not spread across all imputed-tall buildings — it is concentrated in one archetype/cell/storey-count cell

| Scope-B subset | n | needed repair | rate |
|---|---:|---:|---:|
| `nyc_centre`, `LargeHotel`, imputed to **19** storeys | 8 | 4 | **50.0 %** |
| everywhere else in Scope-B (`austin_centre` `HighriseApartment`/`LargeHotel` at 45/5 storeys, `la_urban` `MidriseApartment` at 7, `nyc_urban` `MidriseApartment` at 6) | 13 | 0 | **0.0 %** |

**`austin_centre`'s imputed buildings reach 45 storeys — more than double `nyc_centre`'s 19 — and
have a 0 % repair rate.** So "how tall the imputed building is" does not predict risk by itself;
storey count alone is not the mechanism. The risk is specific to the `nyc_centre` /
`LargeHotel`-at-19-storeys cell of the cross-tab.

**And it is not simply "`nyc_centre` is a risky cell."** `nyc_centre`'s own background repair rate,
measured on the 292 *real* (non-imputed) `nyc_centre` buildings with `levels ≥ 10` in the matched
control, is **1.03 % (3/292)** — statistically indistinguishable from the fleet-wide control rate
of 0.97 %. The 50 % rate inside the 8-building Scope-B `nyc_centre` subset is not explained by
`nyc_centre` buildings being risky in general.

## What this means for the ID the director owes the user

**The population is 8 buildings (`nyc_centre`, `LargeHotel`, imputed to 19 storeys), not 1 and not
21.** Within that 8, the outcome splits 4 clean / 3 repaired-and-completed / 1 dropped — so even
inside the at-risk cell, three of four affected buildings self-heal via the pipeline's existing
zero-area-surface-strip-and-reroute safety net. **Only 1 of 8 (12.5 %), and 1 of 21 fleet-wide
(4.8 %), actually fails to produce a result.** This is a **recommendation, not an action** (T04
does not open, close, or assign an ID): the regression should be scoped and recorded against the
`nyc_centre` / `LargeHotel` / 19-storey population (n = 8, of which 1 currently drops), not against
`way/266034056` alone and not against the full 21-building Scope-B set.

## Output

This document; `openubem/outputs/comparisons/open35_regression_population_2026-08-19.csv` (9 rows,
the fleet-wide repair census with `in_scope_b` flag).
