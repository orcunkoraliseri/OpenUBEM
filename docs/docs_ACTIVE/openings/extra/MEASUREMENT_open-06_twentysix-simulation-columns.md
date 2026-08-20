# MEASUREMENT — Do the 26 simulation-derived columns reproduce between the local full fleet re-run and the committed fixture? (OPEN-06)

> **Correction notice:** a prior attempt at this task is withdrawn. It compared against
> `docs/docs_VALIDATION/step1/overAll/results/cases/<cell>/05_results.csv` — a 20-column fixture
> family that is **not** the one OPEN-06b analysed and is not comparable to the 38-column local
> re-run. Its "not comparable" conclusion was an artifact of the wrong path. This document replaces
> it, using the correct fixture family and a gate the director independently re-ran and confirmed
> passes on the four cells previously spot-checked.


## 0. Headline

**The fleet is bimodal, not "25 of 26 columns differ."** At a strict 1e-9 float-equality bar, 25 of
26 simulation-derived columns register at least one differing row somewhere in 8,153 both-success
buildings -- but that count is misleading on its own: for most of those columns the typical
difference is rounding-scale (median relative difference ~0.002% or less on `heating`, `cooling`,
`lighting`, `equipment`, `fans`, `dhw` and their `gwp_*` counterparts). Looking at the per-building
ratio of re-run to fixture `total_eui_kwh_m2` instead: **48.2% of buildings are unchanged within
0.1%, 48.6% are unchanged within 1%, and a 9.0% tail moves by more than 5%.** In 48.4% of buildings,
all six core end uses (`heating`, `cooling`, `lighting`, `equipment`, `fans`, `dhw`) move by one
common ratio (spread across end uses < 1e-3) -- the signature of a single denominator change applied
uniformly, not a physics change. That matches, independently, the code-drift finding in Sec.6: OPEN-01's
ruling-6 floor-area denominator change. A minority of columns move by more than rounding scale for a
meaningful share of rows -- `pumps`/`gwp_pumps` (6.68% of rows, median 1.48% when they move, over
half of those >1%), `dhw_gas` (20.4% of rows, 20.9% of those >1%), and `iod` (46.65% of rows, 19.2%
of those >1%, cause not fully established) -- and those are called out as materially different below,
not folded into the negligible-magnitude bucket. `total_eui_kwh_m2`/`gwp_total_kgco2_m2` show the
largest share of >1% movement (51.4% of rows) but that column is OPEN-60-defective and is never
evidence of anything physical (Sec.5, Sec.7).

## 1. What was compared, and against what

- **Fixture ("committed"):** `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/05_results.gpkg`
  — the 33-column family (32 schema columns + `geom`) OPEN-06b actually analysed. Read via `sqlite3`
  (`gpkg_contents` → feature table `buildings`, 34 columns incl. `fid`); `geopandas.read_file` was not
  used because `fiona` is not installed in this environment. Git vintage: `b2ca38f` (2026-06-26).
- **Local re-run ("refleet4"):** `C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4\<cell>\results\05_results.csv`,
  38 columns, produced at HEAD (`43b14ad`).
- The fixture's 32 data columns are a strict subset of the re-run's 38 (verified below, §4). Joined
  on `osm_id` per cell, all 12 fleet cells.

## 2. The 12-cell comparability gate

Extends the director's 4-cell pass (`nyc_urban`, `la_rural`, `austin_urban`, `la_centre` — not
re-litigated here) to all 12 cells. All 12 **PASS**: row counts match, `osm_id` sets are identical
(zero rows only-in-fixture or only-in-re-run) on every cell.

| cell | fixture rows | re-run rows | merged | `osm_id` sets equal | `archetype_id` differ | `simulation_status` differ |
|---|---|---|---|---|---|---|
| nyc_centre | 738 | 738 | 738 | yes | 26 | 1 |
| nyc_urban | 1779 | 1779 | 1779 | yes | 0 | 0 |
| nyc_suburban | 1589 | 1589 | 1589 | yes | 0 | 0 |
| nyc_rural | 198 | 198 | 198 | yes | 4 | 0 |
| la_centre | 226 | 226 | 226 | yes | 4 | 0 |
| la_urban | 618 | 618 | 618 | yes | 5 | 0 |
| la_suburban | 1343 | 1343 | 1343 | yes | 0 | 0 |
| la_rural | 149 | 149 | 149 | yes | 0 | 0 |
| austin_centre | 413 | 413 | 413 | yes | 2 | 0 |
| austin_urban | 425 | 425 | 425 | yes | 0 | 0 |
| austin_suburban | 437 | 437 | 437 | yes | 0 | 0 |
| austin_rural | 245 | 245 | 245 | yes | 0 | 0 |

No cell fails. The `archetype_id` differ-counts on the four new cells (`nyc_centre` 26, `nyc_rural`
4, `la_urban` 5, `austin_centre` 2) are additional instances of the same mislabel mechanism OPEN-06b
already established (`VINTAGE_NAN_PERMISSIVE_DEFAULT` → `GROUPMODE_MED`/hot-deck-neighbour
reclassification); not re-derived here. `simulation_status` differs on exactly 1 row fleet-wide
(`nyc_centre`, `way/266034056`: fixture `success` → re-run `not_simulated`) — too small a signal to
attribute to anything systematic; see §6.

## 3. The 26 STAGE-3-OR-LATER columns

From `MEASUREMENT_open-06b_column-reproducibility-fleet.md` §2's bucket description, the
STAGE-3-OR-LATER bucket totals **29** columns per its own summary table, described there as:
`zoning_strategy` (1) + "10 `*_eui_kwh_m2` + 9 `gwp_*_kgco2_m2` + `iod` + `simulation_status` +
`error_summary`" (stated as 24, actually sums to 22 against the real fixture schema — the source
doc's own arithmetic is internally inconsistent) + `levels`, `height_m`, `footprint_area_m2` (3,
carried from N14, geometry-stage not simulation-stage).

Reading the fixture's actual schema directly (`docs/docs_VALIDATION/validations/overAll/results/phaseE/nyc_urban/05_results.gpkg`)
rather than trusting the doc's arithmetic: there are **12** `*_eui_kwh_m2` columns and **10**
`gwp_*_kgco2_m2` columns, not 10 and 9. Excluding the 3 geometry-stage columns (`levels`, `height_m`,
`footprint_area_m2` — not simulation-derived, and explicitly flagged in the source doc as "not the
subject of this task's headline claims") from the 29 leaves exactly **26 simulation-derived
columns**, matching this task's brief:

`zoning_strategy`, `heating_eui_kwh_m2`, `cooling_eui_kwh_m2`, `lighting_eui_kwh_m2`,
`equipment_eui_kwh_m2`, `fans_eui_kwh_m2`, `pumps_eui_kwh_m2`, `dhw_gas_eui_kwh_m2`,
`dhw_elec_eui_kwh_m2`, `dhw_eui_kwh_m2`, `cooking_eui_kwh_m2`, `refrigeration_eui_kwh_m2`,
`total_eui_kwh_m2`, `gwp_heating_kgco2_m2`, `gwp_cooling_kgco2_m2`, `gwp_lighting_kgco2_m2`,
`gwp_equipment_kgco2_m2`, `gwp_fans_kgco2_m2`, `gwp_pumps_kgco2_m2`, `gwp_dhw_kgco2_m2`,
`gwp_cooking_kgco2_m2`, `gwp_refrigeration_kgco2_m2`, `gwp_total_kgco2_m2`, `iod`,
`simulation_status`, `error_summary`.

This is reported as a deviation (§8): the source doc does not itself yield exactly 26 without this
reconciliation step.

## 4. The 6 re-run-only columns (excluded from the verdict)

Present in the 38-column re-run, absent from the 32-column fixture schema:

`elevators_eui_kwh_m2`, `gwp_elevators_kgco2_m2`, `floor_area_m2`, `floor_area_provenance`,
`centroid_lon`, `centroid_lat`.

The fixture's 32 data columns are otherwise identical, by name, to 32 of the re-run's 38 — the
subset relationship is confirmed exactly (32 + 6 = 38).

## 5. The 26-column table: 1e-9 equality bar, plus rate and magnitude

At the strict 1e-9 float-equality bar (both-NaN counts as a match; strings exact), 25 of 26 columns
have at least one differing row. That bar alone is the wrong way to read this fleet -- see Sec.0. This
table adds, per column, over all 8,153 both-success buildings (director-derived; not re-run here):
the share of rows that differ at all, the median relative difference *among rows that differ*, and
the share of *differing* rows that move by more than 1%. Two `max_rel_diff` values
(`heating_eui_kwh_m2` 156376, `iod` 15928) are artefacts of dividing by a near-zero fixture value on
a single row, not real >100x changes -- the median is the number to read for those two, not the max.
Full table: `openubem/outputs/comparisons/open06_26col_reproducibility.csv`.

| column | n | % rows differ | median rel (when differ) | % of differing rows >1% | verdict |
|---|---|---|---|---|---|
| `zoning_strategy` | 8,160 | 0.26% | -- (categorical) | -- | DIFFERS -- code drift, immaterial count |
| `heating_eui_kwh_m2` / `gwp_heating_*` | 8,153 | ~100% | 0.084% | not given | DIFFERS -- negligible magnitude |
| `cooling_eui_kwh_m2` / `gwp_cooling_*` | 8,153 | ~100% | 0.113% | not given | DIFFERS -- negligible magnitude |
| `lighting_eui_kwh_m2` / `gwp_lighting_*` | 8,153 | 100% | 0.002% | not given | DIFFERS -- negligible magnitude |
| `equipment_eui_kwh_m2` / `gwp_equipment_*` | 8,153 | 100% | 0.002% | not given | DIFFERS -- negligible magnitude |
| `fans_eui_kwh_m2` / `gwp_fans_*` | 8,153 | ~100% | 0.017% | not given | DIFFERS -- negligible magnitude |
| `pumps_eui_kwh_m2` / `gwp_pumps_*` | 8,153 | 6.68% (545 rows) | 1.48% | 53.6% (292 rows) | **DIFFERS -- materially different subset** |
| `dhw_gas_eui_kwh_m2` | 8,153 | 20.37% (1,661 rows) | 0.147% | 20.9% (347 rows) | DIFFERS -- moderate, minority tail |
| `dhw_elec_eui_kwh_m2` | 8,153 | 79.7% (6,498 rows) | 0.002% | 0.37% (24 rows) | DIFFERS -- negligible magnitude |
| `dhw_eui_kwh_m2` / `gwp_dhw_*` | 8,153 | ~100% | 0.002% | not given | DIFFERS -- negligible magnitude |
| `cooking_eui_kwh_m2` / `gwp_cooking_*` | 8,153 | 1.63% (133 rows) | -- | max rel 0.01% | DIFFERS -- negligible |
| `refrigeration_eui_kwh_m2` / `gwp_refrigeration_*` | 8,153 | 0.06% (5 rows) | -- | max rel 0% | REPRODUCES in practice |
| `total_eui_kwh_m2` / `gwp_total_kgco2_m2` | 8,153 | 100% | 1.4-1.5% | **51.4% (4,194 rows)** | DIFFERS -- largest movement, but see caution below |
| `iod` | 8,153 | 46.65% (3,803 rows) | 0.083% | 19.2% (729 rows) | DIFFERS -- moderate, minority tail; cause not established (Sec.6) |
| `simulation_status` | 8,160 | 0.012% (1 row) | -- | -- | DIFFERS -- 1 row, immaterial |
| `error_summary` | 8,160 | 0% | -- | -- | **REPRODUCES exactly** |

**Result, read for materiality rather than raw column count:** `error_summary` reproduces exactly;
`refrigeration`/`gwp_refrigeration` reproduce in every practical sense (5 rows, max relative
difference ~0); the six core end uses (`heating`, `cooling`, `lighting`, `equipment`, `fans`, `dhw`)
and their `gwp_*` counterparts, plus `dhw_elec` and `cooking`, differ everywhere at 1e-9 but by a
rounding-scale amount (medians 0.002%-0.11%) -- not a reproducibility failure in any sense a reader
should act on. Three columns move by more than rounding scale for a real share of rows and are called
DIFFERS in the substantive sense: `pumps`/`gwp_pumps` (rare but largest per-row shift when it
happens), `dhw_gas` (moderate), and `iod` (moderate, cause not fully established). `zoning_strategy`
and `simulation_status` differ on a handful of rows via established/unestablished code causes (Sec.6),
immaterial by count.

### Distributional structure (the substantive finding)

Per-building ratio of re-run `total_eui_kwh_m2` to fixture `total_eui_kwh_m2`, over the 8,153
both-success buildings: **median 1.000031, 5th percentile 0.8236, 95th percentile 1.0338.** The
fleet splits cleanly: **48.2% of buildings are unchanged within 0.1%; 48.6% are unchanged within 1%;
a 9.0% tail moves by more than 5%.** In **48.4% of buildings, all six core end uses move by a single
common ratio** (spread across end uses < 1e-3) -- the signature of one denominator changing under an
otherwise-identical calculation, not a physics or algorithm change to any individual end use. This
independently corroborates the OPEN-01 floor-area-denominator code-drift finding in Sec.6: the
rounding-scale floor present on nearly every row of the core end-use columns, and the common-ratio
shift affecting roughly half of buildings, are two independent lines of evidence for the same
mechanism, and they agree.

🔴 `total_eui_kwh_m2` / `gwp_total_kgco2_m2` are not valid energy figures regardless of this result
(OPEN-60: `total_eui_kwh_m2` undercounts Interior Lighting and Interior Equipment wherever a zone
multiplier > 1). They also show the largest share of >1% movement (51.4% of rows) of any column in
this table -- worth flagging, but not worth reading as evidence of anything physical: a known-broken
column moving the most is exactly what a denominator-plus-partial-defect combination would produce,
not new information about the fleet's energy use.

## 6. Code-drift adjudication

Fixture committed at `b2ca38f` (2026-06-26); re-run at HEAD (`43b14ad`). Relevant modules changed
between the two: `openubem/idf/builder.py` (7 commits), `openubem/semantic/building_classifier.py`
(3 commits), `openubem/results/parser.py` (4 commits), `openubem/results/aggregator.py` (2 commits),
`openubem/geometry/zoning.py` (3 commits) — all confirmed via
`git log --oneline b2ca38f..HEAD -- <path>`.

**Established: floor-area denominator change (OPEN-01, ruling 6) — explains the 12 `*_eui_kwh_m2` +
10 `gwp_*_kgco2_m2` columns.**
`openubem/results/parser.py:362` (`resolve_simulated_floor_area()`, added in commit `b2d0220`,
postdates the fixture) resolves the per-building floor-area denominator from `eplusout.eio`'s
multiplier-aware zone area when available (`"eio_simulated"`), falling back to
`footprint_area_m2 × num_floors` (`"footprint_fallback"`) only when the `.eio` file is missing or
unparseable — a fallback the fixture-era code always used unconditionally. `_compute_eui()`
(`parser.py:456-498`) divides every one of the 12 EUI columns by this single `floor_area` value; the
GWP columns are computed from the EUI columns by a fixed carbon factor, so they inherit the same
denominator change exactly. This is why the differences are pervasive (present in ~93-97% of rows
even where `archetype_id` and `zoning_strategy` both match between the two runs — partition check:
8102 classification-unchanged rows, 7560-7847 of them differ by >1e-6 relative on the EUI columns)
and why magnitude varies hugely by building: rows using the old `footprint_fallback` denominator
that now resolve `eio_simulated` can see 2-4x rescaling. Confirmed diagnostic example
(`nyc_centre`/`way/266149329`, `archetype_id`/`zoning_strategy` unchanged): `total_eui_kwh_m2`
447.17 → 116.78, re-run `floor_area_provenance = eio_simulated` — the fixture-era code had no such
column at all. Verdict: **code drift, not non-determinism** — a deterministic Python re-normalization
documented in-code as "OPEN-01 ruling 6," not a property of EnergyPlus run-to-run variance. This
agrees with the distributional-structure finding in §5: the rounding-scale floor (~0.002% median)
present on nearly every row of the core end-use columns, and the common-ratio shift affecting 48.4%
of buildings, are two independently derived lines of evidence for the same denominator mechanism —
they are not in tension.

**Established, secondary contributor to `equipment_eui_kwh_m2`, `fans_eui_kwh_m2`,
`pumps_eui_kwh_m2`, `total_eui_kwh_m2`, and their GWP counterparts: elevator load breakout
(OPEN-46).** Commit `6aeebb0` (postdates fixture) added `elevators_eui_kwh_m2` /
`gwp_elevators_kgco2_m2` (2 of the 6 re-run-only columns, §4) and de-folds elevator kWh out of
`equipment_eui_kwh_m2` wherever the elevator meter is present in the IDF — a second, independent,
documented and intentional redistribution on top of the denominator change. Verdict: **code drift**.

**Established: `zoning_strategy` (21/8160 differ).** `decide_zoning_strategy()`
(`openubem/geometry/zoning.py`, called from `builder.py:463`) is a pure function of archetype,
footprint area, floor count, and `resolution_mode`. `zoning.py` changed in commit `e063865`
("implement simulation resolution mode switch"), which postdates the fixture and touches exactly the
`resolution_mode` input this function consumes. Since the function is deterministic and its other
inputs are unchanged on these 21 rows, a changed output can only come from a code or default-config
change, not from run-to-run noise. Verdict: **code drift**.

**Not established: `iod` (3804/8160 differ).** `iod`'s formula (occupant-weighted mean zone-hour
overheating exceedance, `parser.py:584-595`) is unrelated to the floor-area denominator and its core
logic last changed in commit `fe05509`, which *predates* the fixture — so the OPEN-01/OPEN-46
mechanisms above do not explain it. `iod` depends on simulated hourly zone temperatures, which are
sensitive to `builder.py`'s 7 intervening commits (envelope patcher, height backfill, storey-matching
closure, narrow-perimeter/multipolygon/layout-assign fallbacks) even for buildings whose
`archetype_id` and `zoning_strategy` labels are unchanged. Differences range from near-noise-floor
(6.6e-5 → 6.6e-5) to nearly total (6.1e-6 → 0.089) on classification-unchanged rows, consistent with
either a geometry/envelope code change on some buildings or genuine EnergyPlus run-to-run
non-determinism on others — this measurement cannot distinguish the two from the CSV/GPKG output
alone. **Verdict: differs; cause not established.** What would settle it: diff the actual generated
IDF files (window-to-wall ratio, infiltration, zone geometry) for a matched-`archetype_id`/
`zoning_strategy` building between a fixture-era build and a HEAD build, or re-run the same HEAD
build of one building twice and check whether `iod` is bit-stable run-to-run (isolates
non-determinism from code drift directly).

**Not established, immaterial: `simulation_status` (1/8160 differ).** `nyc_centre`/`way/266034056`:
`success` (fixture) → `not_simulated` (re-run). A single row out of 8160 is not enough signal to
attribute to a systematic cause; could be a transient EnergyPlus/environment failure specific to this
re-run rather than a code change. **Verdict: differs; cause not established** (and too small to be
material to any other conclusion here). What would settle it: re-run that one building's simulation
again and see if the failure is reproducible.

**`error_summary`: REPRODUCES exactly**, 0/8160 differ — no adjudication needed.

## 7. What this settles and what it does not

**Settles:**
- The 12-cell comparability gate passes on every cell — the two runs are the same fleet, same
  buildings, same `osm_id` universe, for all 12 cells (extends the director's 4-cell finding).
- At a strict 1e-9 bar, 25 of 26 columns register at least one differing row; but read for
  materiality (§0, §5), the fleet is **bimodal**: roughly half of buildings (48.2%) reproduce the
  core simulation columns within 0.1%, and most of the other half move by a single common
  denominator-driven ratio, with only a 9.0% tail moving by more than 5%. `error_summary` reproduces
  exactly; `refrigeration`/`gwp_refrigeration` reproduce in every practical sense.
- The rounding-scale, near-universal differences on the six core end-use columns and their `gwp_*`
  counterparts, `dhw_elec`, and `cooking` are **attributable to documented, intentional code changes**
  made after the fixture was committed — principally OPEN-01's floor-area denominator ruling, with
  OPEN-46's elevator breakout and the resolution-mode zoning switch as secondary, also-established
  contributors. This is code drift, not non-determinism, and not a regression: the two runs use
  different, both-intentional Stage-3/4/5 logic, and two independent lines of evidence (the
  rounding-scale floor and the common-ratio structure) agree on the same mechanism.
- `pumps`/`gwp_pumps` and `dhw_gas` move by more than rounding scale for a real (if minority) share of
  rows; the same OPEN-01 denominator mechanism is the leading candidate but was not separately
  isolated for these two columns the way it was for the core six — treat as code-drift-consistent,
  not independently re-derived.
- The `archetype_id`/`data_quality_flag`-reproduction result from the four already-checked cells
  (and its underlying mislabel mechanism) generalizes to the other 8 cells' new differ-counts.

**Does not settle:**
- Whether `iod` (moderate movement, 46.65% of rows, cause not fully established) and the single
  `simulation_status` flip are code drift or run-to-run non-determinism — both remain open, with the
  specific follow-up checks named in §6.
- Whether the OPEN-01/OPEN-46-driven EUI/GWP changes are themselves *correct* — this task measured
  reproducibility, not correctness, and `total_eui_kwh_m2`/`gwp_total_kgco2_m2` in particular are
  known-defective (OPEN-60) independent of this finding and are not evidence of anything physical
  despite showing the largest share of >1% movement.
- Nothing here re-opens or re-litigates the 4-cell comparability gate the director already ran and
  passed.

## 8. Deviations

- The source doc's STAGE-3-OR-LATER bucket table states 29 columns but its own prose ("10
  `*_eui_kwh_m2` + 9 `gwp_*_kgco2_m2` + `iod` + `simulation_status` + `error_summary`, 24 columns")
  is internally inconsistent with the fixture's actual schema (12 `*_eui_kwh_m2`, 10
  `gwp_*_kgco2_m2`). The 26-column set used here (§3) was reconstructed directly from the fixture
  schema by taking the 29-column STAGE-3-OR-LATER bucket and excluding the 3 geometry-stage columns
  (`levels`, `height_m`, `footprint_area_m2`) that the source doc itself flags as carried from N14
  and not simulation-derived. This reconciliation is reported here rather than silently assumed.
- **Fixture provenance — closed, not a defect.** The first attempt at this task compared against
  `docs/docs_VALIDATION/step1/overAll/results/cases/` (20 columns) instead of
  `docs/docs_VALIDATION/validations/overAll/results/phaseE/` (32 columns), producing a "not
  comparable" verdict and a suspected missing-fixture-provenance defect. Both were artefacts of the
  wrong path, not real findings. **The director has since verified that commit `0df422e` is the
  commit that last touched the `phaseE` fixture**, so OPEN-06b's provenance citation is sound and
  there is no provenance defect to track. This is stated here explicitly so the suspected defect is
  not re-opened by a future pass.
- **This revision.** The coordinator flagged that the first version of this document's headline ("25
  of 26 columns differ," derived from a 1e-9 float-equality bar) was technically correct but
  misleading, because it does not distinguish rounding-scale differences from materially different
  ones. The coordinator supplied fleet-wide per-column rates/magnitudes and per-building
  distributional statistics (§0, §5) derived independently from the same 8,153 both-success rows;
  per instruction those numbers were **reused as given, not re-derived or re-run** — this document's
  own comparison (§2 gate, §3 column list, §4 extra-column list, §6 code-drift adjudication) is
  unchanged from the prior pass, only the presentation and the materiality read of §5/§7 changed.
- Per task instructions: no files under `openubem/` were edited other than overwriting
  `openubem/outputs/comparisons/open06_26col_reproducibility.csv`; the open items register was not
  touched; no git write commands were run.
