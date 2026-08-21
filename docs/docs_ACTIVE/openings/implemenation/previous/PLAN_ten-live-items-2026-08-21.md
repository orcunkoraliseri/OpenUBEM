# PLAN — ten live items, pass of 2026-08-21

> **Slug:** `ten-live-items-2026-08-21`
> **Date opened:** 2026-08-21 (director)
> **Register in force:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md`
> (16 live / 46 retired / 62 total, next free `OPEN-63`)
> **Specs:** `docs/docs_main/` — read-only, never edited by this plan.
> **Predecessor pass:** `implemenation/previous/PLAN_ten-live-items-2026-08-20-evening.md` (T01–T11).
> This plan picks up exactly where §4 of the register leaves off: every task below is the *next*
> step named there, or the measurement that turns a "waiting on the user" item into a decidable one.

---

## 1. What this pass is, in one paragraph

Ten live items each get **one bounded measurement**, run from data that is already on this machine.
**No cluster job is submitted. No fleet re-simulation is run. No item is closed by an executor and no
published number is restated by an executor.** Six of the ten tasks are re-aggregation of CSVs that
already exist; three read files from the E02 harvest; one reads the input gpkgs. The purpose of the
pass is to convert six "unsized" or "waiting on a ruling" items into items with a number attached,
so the user can rule on them.

---

## 2. Hard rules for the executor

1. **Measure. Do not remediate.** No production file under `openubem/` is edited by this plan.
   Every task writes a *standalone* script under `scripts/analysis/` and a *measurement doc* under
   `docs/docs_ACTIVE/openings/extra/`. If a task tempts you to fix something, write the fix down in
   the measurement doc under a heading `Remedy shape (NOT applied)` and move on.
2. **Never run compute on the Speed login node.** No task here needs the cluster at all. If you
   think one does, you have misread it — stop and quote the line.
3. **Do not invent a number.** If a control fails or a file is absent, report the absence as the
   result. A task that reports "unmeasurable, because X" is a completed task. A task that
   substitutes a proxy silently is a failed one.
4. **If a plan line names a column, a signature or a path that does not exist, STOP and quote the
   conflict.** This happened twice in the predecessor pass and both times it was the right call.
5. **Python is `.venv/Scripts/python.exe`** from the repo root. Bare `python` is a Windows Store
   stub and will fail.
6. **Outputs:** CSVs go to `openubem/outputs/comparisons/`, figures (if any) to `openubem/outputs/`
   flat. **No `.py` file is ever written under `docs/`.**
7. **Do not commit.** Git is handled outside this session.
8. **Register every error you hit** in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` in the
   house format, before you call the task done. Search that file *first* when something breaks.
9. **Append one progress-log entry per completed task** to §8 of this file. Re-read the file
   immediately before appending — other executors are appending to the same section concurrently.
   If your append collides, re-read and retry once.
10. **Cap your own output.** Use `head`, `--stat`, `-c`. Never print a whole CSV into your context.

---

## 3. File layout

| Kind | Where |
|---|---|
| Analysis scripts | `scripts/analysis/<taskslug>_2026-08-21.py` |
| CSV outputs | `openubem/outputs/comparisons/<taskslug>_2026-08-21.csv` |
| Measurement docs | `docs/docs_ACTIVE/openings/extra/MEASUREMENT_<item>_<slug>.md` |
| Progress log | §8 of this file |

---

## 4. Dependency decisions (pinned)

- **Fleet inputs** = `evidence/open48_refleet4/<cell>/01_buildings.gpkg`, twelve cells
  (`austin|la|nyc` x `centre|rural|suburban|urban`). Columns confirmed present by the director on
  2026-08-21: `osm_id, crs_utm, building_tag, function_tag, levels, height_m, year_built, postcode,
  underground, roof_shape, roof_height_m, footprint_area_m2, perimeter_m, surplus_tags,
  provenance_levels, provenance_height_m, provenance_year_built, provenance_building_tag,
  provenance_function_tag, provenance_postcode, provenance_geometry, data_quality_flag, geometry`.
- **Fleet results** = `evidence/open48_refleet4/<cell>/results/05_results.csv` (38 columns, incl.
  `osm_id, levels, height_m, archetype_id, zoning_strategy, total_eui_kwh_m2, floor_area_m2,
  floor_area_provenance, simulation_status, iod`) and `results/dropped_buildings.csv`.
- **Fleet census** = `openubem/outputs/comparisons/open61_census_fleet.csv`, **8,160 rows**, with the
  full `parsed_*` end-use block and the `dh_*` district-heating block. This is the OPEN-61 census.
- **Storey census** = `openubem/outputs/comparisons/open03_storey_census_zfix.csv`, 8,160 rows, with
  `source_storey_count, auto_storey_count, layout_assign_storey_count,
  layout_assign_storey_count_naive, layout_assign_storey_count_floor, auto_attic_zone_count,
  layout_assign_z_origin_collapse_risk, agree, diff_layout_assign_minus_auto`.
- **E02 harvest** = `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest\<cell>_<mode>\<stem>\`,
  five modes (`auto, building, fast_zone, floor, layout_assign`) x twelve cells. Each directory
  holds `eplusout.err`, `eplusout.eio`, `eplusout.end`, `eplusout.sql` — **and no `.idf`.**
- **Staged IDFs** (auto arm of the adopted run) = `evidence/open48_refleet4/<cell>/fleet_staging/idfs/<stem>.idf`.
- **Err census** = `openubem/outputs/comparisons/open56_open09_run4_err_census_2026-08-20.csv`
  (8,160 rows; `n_volstub, has_volstub, n_converge, has_converge, n_severe, n_fatal`).
- **Fatal census** = `openubem/outputs/comparisons/open38_fatal_causes_2026-08-20.csv` (44 rows;
  `cell, mode, stem, severe_class, raw_first_severe_line`).
- **Gate census** = `openubem/outputs/comparisons/open60_fleet_integrity_gate_2026-08-20.csv`
  (7,860 rows). ⚠️ **Its `sql_path` column points into a deleted scratchpad — the SQL files it read
  no longer exist on this machine.** Any task needing SQL must use the E02 harvest instead, and must
  expect meter-only files (see §5 F4). Verified absent by the director, 2026-08-21.
- **Stem ↔ osm_id convention:** harvest stems are `way_472960972` / `relation_13781131`; the results
  CSVs use the same underscore form. IDF zone names use the slash form (`WAY/472960972_F0_PERIM1`).
  Normalise by lowercasing and replacing `/` with `_` before joining.

---

## 5. Facts with citations — read these before writing code

- **F1 — `meter_ok` is mis-specified, and here is exactly how.**
  `openubem/results/parser.py:648-671`: the numerator sums only
  `Zone Lights Electricity Energy` + `Zone Electric Equipment Electricity Energy` (hourly), and the
  denominator is `Electricity:Facility` (Run Period). A **subset** is compared against a **total**,
  so the check fails for any building with fans, pumps, cooling or DHW electricity — which is why it
  fires on 99.9 % and why its only 6 passes are buildings that produced no electricity at all.
  `abups_ok` (`parser.py:620-644`) compares like with like and is sound.
- **F2 — the OPEN-35 fallback is already wired, and its population is token-identified.**
  `openubem/geometry/footprint.py:58-88` (`derive_num_floors`) returns, in order: `levels` if
  present; `ceil(height_m / 3.5)` if present; the classifier's group-/global-median **only when
  `_archetype_consumed_group_median(row)` is true** (`footprint.py:90-95`, testing for the
  `GROUPMEDIAN_LEVELS_MED` token in `archetype_source`); otherwise **1**. The wiring is
  `openubem/idf/builder.py:162-176` (`_derive_num_floors_wired`). **The undecided half of OPEN-35 is
  which of the last two branches is correct, and nobody has counted how many buildings sit on that
  branch fleet-wide.**
- **F3 — production geometry reads `Z_Origin` correctly; only the analysis parser did not.**
  `openubem/geometry/layout_assigner.py:471` and `:491-493`. The analysis-side gap was fixed and
  re-run: `open03_storey_census_zfix.csv` is the post-fix census. **What remains on OPEN-62 is a
  definition, not a defect** — and a definition is the user's to give, so T06 below builds the table
  they need and stops.
- **F4 — the E02 harvest `.sql` files look meter-only.** Director scouting, 2026-08-21: ten files
  sampled at random across ten different `<cell>_<mode>` directories all return **0 rows** for
  `TabularDataWithStrings` / `AnnualBuildingUtilityPerformanceSummary` / `End Uses`, **0** dictionary
  entries matching `Zone %`, and only 9–10 `ReportDataDictionary` rows in total.
  `Electricity:Facility` **is** present. **This is a ten-file scout, not a census** — T01 is the
  census, and T01 may overturn it.
- **F5 — `.eio` carries per-zone volume even for runs that died fatal.** Verified on
  `la_rural_auto/way_472960972` (a member of the 44): 58 `Zone Information` rows, each with
  `Volume {m3}` populated (e.g. `190.65`). **So the OPEN-56 volume question can be asked of the 44
  fatals without re-simulating anything.**
- **F6 — OPEN-09's non-convergence population is 16/8,160, all in LA**
  (`la_centre 2, la_rural 10, la_suburban 3, la_urban 1`), signature
  `Inside surface heat balance did not converge`
  (`scripts/analysis/open09_fleet_err_taxonomy.py:42`). **`CheckWarmupConvergence` matches 0
  buildings — do not use it.**
- **F7 — the 44 fatals are 86 % one family:** 21 `Temperature (high) out of bounds`, 17
  `CalcHeatBalanceInsideSurf`, 5 `Temperature (low) out of bounds`, 1 shadowing/non-convex.

---

## 6. Tasks

Each task is independent. **Any task may be run before any other.**

---

### T01 — OPEN-53: is "meter-only" a property of the 874, or of the whole harvest? *(executor)*

**What.** Census the SQL contents of every directory in the E02 harvest.

**Why.** OPEN-53's first question is "re-fetch the 874, or leave them". The 20-file sample said the
missing files parse to nothing usable. If the *whole corpus* is meter-only, then the 874 are not
special, re-fetching buys custody and nothing else, and the item's second question (a meter-only
fallback in `parse_building()`) becomes the only live one. **This is the single measurement that
decides the shape of the item.**

**How.**
1. Walk `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest\*\*\`. For each directory record:
   `cell`, `mode`, `stem`, `has_sql`, `has_end`, `has_err`, `has_eio`, `sql_bytes`.
2. For each existing `eplusout.sql`, open read-only (`sqlite3.connect(f"file:{p}?mode=ro", uri=True)`)
   and record: `n_dict_rows` (`SELECT COUNT(*) FROM ReportDataDictionary`), `n_zone_keys`
   (`... WHERE Name LIKE 'Zone %'`), `n_abups_enduse_rows` (`SELECT COUNT(*) FROM
   TabularDataWithStrings WHERE ReportName='AnnualBuildingUtilityPerformanceSummary' AND
   TableName='End Uses'`), `has_elec_facility`, `has_gas_facility`. Wrap each file in
   `try/except` and record `sql_open_error` rather than crashing the walk.
3. Write `open53_harvest_sql_census_2026-08-21.csv`, one row per directory.
4. Report, in the doc: total directories; how many have `.sql`; how many have **any** ABUPS End-Uses
   row; how many have **any** zone key; the cross-tab by `mode` and by `cell`; and the count of
   directories missing `.end` (OPEN-53's population) **split by whether their `.sql` is present**.

**How to test.**
- **C1** — the `.end`-missing count reproduces **875** (the predecessor's F8/T04 number) within ±2.
  If it does not, stop and report the discrepancy — do not adjust.
- **C2** — re-open three files by hand and confirm the census's per-file numbers match.
- **C3** — state explicitly whether F4's ten-file scout is confirmed or overturned.

---

### T02 — OPEN-53: what would a meter-only EUI actually cost? *(executor)*

**What.** For the auto-arm harvest buildings, compute an EUI from the facility meters alone and
compare it against the adopted run's published `total_eui_kwh_m2` for the same building.

**Why.** OPEN-53's second question, verbatim from the register §4: *"should `parse_building()` fall
back to a meter-only EUI when zone keys are absent?"* Nobody has measured the error that fallback
would introduce. **This task measures it, on buildings where both answers exist.** The answer is
what makes the fallback adoptable or not — and it is worth far more than the 874 files.

**How.**
1. Population: `<cell>_auto` harvest directories whose `.sql` opens. Join by normalised stem to
   `evidence/open48_refleet4/<cell>/results/05_results.csv` on `osm_id`. Keep only rows where the
   adopted run has `simulation_status == 'success'`, a non-null `total_eui_kwh_m2` and
   `floor_area_m2 > 0`.
2. Meter-only EUI: sum `Electricity:Facility` + `NaturalGas:Facility` at
   `ReportingFrequency='Run Period'` from `ReportData` joined to `ReportDataDictionary`; convert
   J → kWh (`/3.6e6`); divide by the adopted run's `floor_area_m2`. **Use the adopted floor area —
   the point is to isolate the numerator, not to re-open the denominator (OPEN-01 is settled).** If
   any other `*:Facility` Run-Period meter is present (district heating/cooling), include it and say
   so; report which meters were found, as a count by meter name.
3. Write `open53_meter_only_eui_2026-08-21.csv` with `cell, osm_id, archetype_id, meter_only_eui,
   published_eui, diff, pct_diff, meters_used`.
4. Report: n compared; median and IQR of `pct_diff`; the pooled figure both ways (Σ energy ÷ Σ area,
   never a mean of ratios — OPEN-43's ruling); the count and identity of buildings where
   `|pct_diff| > 10 %`; and a per-archetype breakdown.

**How to test.**
- **C4** — the join loses fewer than 5 % of the auto population; report the loss and its cause.
- **C5** — for three buildings, recompute the meter sum with a second, independently written query
  and confirm agreement to 6 significant figures.
- **C6** — if the pooled meter-only figure lands within 1 % of **153.8231 kWh/m²**, say so plainly
  and say plainly that it is *not* a validation of the census (both read the same simulations).

---

### T03 — OPEN-17: how much does each imputation target actually need filling? *(executor)*

**What.** A fleet-wide null census, per target, from the twelve input gpkgs.

**Why.** Register §4 A.4: the imputation machinery *covers one target out of seven*
(`year_built` 5,913/5,913; `levels`, `function_tag`, `postcode`, `building_tag`, `height_m` zero).
**That says what the machinery reaches. It does not say what the fleet needs.** The user is being
asked to rule on imputation without knowing the size of the hole. This task states the hole.

**How.**
1. Read all twelve `01_buildings.gpkg`. For each of `levels, height_m, year_built, function_tag,
   postcode, building_tag, roof_shape` count nulls per cell and fleet-wide. **If the register's
   seventh target is not `roof_shape`, quote the conflict and use the register's list.**
2. Cross-tab each target's null count against its `provenance_*` column where one exists, so an
   imputed value is not counted as observed.
3. Join to `05_results.csv` on `osm_id` and split each null count by whether that building was
   simulated successfully in the adopted run — a null on a dropped building costs nothing.
4. Write `open17_target_null_census_2026-08-21.csv` (`cell, target, n_total, n_null,
   n_null_simulated, pct_null, provenance_breakdown`).
5. Report the fleet table, and one sentence per target on whether the existing tier could reach it.

**How to test.**
- **C7** — total building count across the twelve gpkgs is reported and compared against **8,160**;
  any difference is explained (dropped buildings, geometry failures), not smoothed over.
- **C8** — `year_built`'s coverage is consistent with the known `5,913/5,913` tier result; if it is
  not, that inconsistency is the finding and must be reported rather than reconciled.

---

### T04 — OPEN-14: what does the null-`height_m` hole look like across all twelve cells? *(executor)*

**What.** Extend the predecessor's `nyc_centre`-only fusion-yield result to the whole fleet.

**Why.** Register §4 A.3: with the gate opened in a sandbox the tier fills **106 of 121 (87.6 %)** of
`nyc_centre`'s null `height_m`; the blocker is custody of eleven slices. **The acquisition decision
needs the size of the other eleven cells, and nobody has stated it.** No slice is fetched here — this
is the sizing, not the acquisition.

**How.**
1. From the twelve gpkgs: per cell, `n_buildings`, `n_null_height`, `pct_null_height`, and of the
   nulls, how many also have null `levels` (the ones that fall to `derive_num_floors`'s last branch —
   F2; this is the direct link to OPEN-35 and to T05).
2. Read `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-14_fusion-yield.md` and
   `open14_fusion_yield_nyc_centre_2026-08-20.csv`. Take the **measured** `nyc_centre` fill rate as
   given; do **not** re-derive it.
3. Apply that rate as a *bound*, clearly labelled as an extrapolation and not a measurement, to
   report a range for what the eleven missing slices could fill. State the assumption in one line.
4. Write `open14_null_height_by_cell_2026-08-21.csv`.
5. Report: which cells dominate the hole; whether the hole is concentrated (so a partial acquisition
   would do) or spread (so it is all or nothing).

**How to test.**
- **C9** — `nyc_centre`'s null-`height_m` count reproduces **121**. If it does not, stop: the
  populations differ and the extrapolation is void.
- **C10** — every extrapolated number in the doc carries the word "extrapolated" in the same
  sentence.

---

### T05 — OPEN-35: how many buildings sit on the undecided branch? *(executor)*

**What.** Count, fleet-wide, the buildings whose storey count comes from the group-/global-median
fallback rather than from data — and what they would be under the alternative.

**Why.** Register §4 A.5 calls OPEN-35's remaining half **the oldest undecided item on the list**,
and it is undecided on a 21-building, 42-simulation sample. **A ruling on 21 buildings is a
different decision if the branch carries 40 buildings than if it carries 2,000.** This task supplies
that number and nothing else — it does not pick a fallback.

**How.**
1. Reproduce `_archetype_consumed_group_median` (F2, `footprint.py:90-95`) over the fleet: for each
   of the 8,160, does `archetype_source` carry the `GROUPMEDIAN_LEVELS_MED` token? The
   `archetype_source` column lives in the classifier's output — locate it (start with
   `fleet_staging/` and `04_simulation_manifest.parquet`); **if no on-disk artifact carries
   `archetype_source`, stop and report that as the finding** rather than re-running the classifier.
2. For each building in that population, record `levels`, `height_m`, the storey count under the
   **current** (Scope B, median) branch and under the **pre-OPEN-35** branch (`return 1`), and the
   resulting `floor_area_m2` under each.
3. Write `open35_fallback_population_2026-08-21.csv`.
4. Report: n on the branch; the fleet floor area at stake under each rule; and the pooled EUI
   denominator shift the two rules imply (**denominator only — do not restate the headline**).

**How to test.**
- **C11** — the population is a subset of the buildings with **both** `levels` and `height_m` null;
  assert it and report the assertion's result.
- **C12** — the 21 buildings of the existing OPEN-35 sample
  (`extra/MEASUREMENT_open-35_regression-population.md`) are all inside the population you found, or
  the difference is explained.

---

### T06 — OPEN-62: the storey-definition decision table *(executor)*

**What.** Under each candidate definition of "a storey", state what OPEN-03's fleet storey
disagreement becomes.

**Why.** Register §4 A.6: *"what a storey IS for a prototype with an attic, a plenum or a high bay —
a definition question, not a measurement, and explicitly not an executor's."* **Correct — so this
task does not choose.** It lays the answers side by side so that choosing takes one minute instead of
a re-run. The columns already exist in the post-fix census; nobody has aggregated them.

**How.**
1. Read `open03_storey_census_zfix.csv` (8,160 rows).
2. For each of the three storey definitions already in the file —
   `layout_assign_storey_count` (Z_Origin-corrected), `layout_assign_storey_count_naive`,
   `layout_assign_storey_count_floor` — and for an **attic-excluded** variant built by subtracting
   `auto_attic_zone_count` where it applies, compute against `auto_storey_count` and
   `source_storey_count`: the agreement rate, the mean and max signed difference, fleet-wide and
   **per archetype**.
3. Report the six archetypes flagged `layout_assign_z_origin_collapse_risk` separately from the rest,
   since they are the only ones where the definitions can disagree materially.
4. Write `open62_storey_definition_table_2026-08-21.csv` and put the headline table in the doc.
5. End the doc with a section **`The question for the user`** stating the candidate definitions in
   one line each, with their fleet agreement rate beside them. **Recommend nothing.**

**How to test.**
- **C13** — the census reproduces the **30.0 % / 70.0 %** split the register quotes for OPEN-03
  (`layout_assign` represents the real storey count for 30.0 % of the fleet). If it does not, the
  census file you opened is not the one the register cites — stop.
- **C14** — row count is exactly 8,160.

---

### T07 — OPEN-38 x OPEN-56: are the 44 fatals volume-anomalous? *(executor)*

**What.** Read per-zone volumes out of the `.eio` files of the 44 fatal buildings and of a matched
control, and test whether the fatals are volume-anomalous.

**Why.** Register §4 B.7 names this as the next step: *"whoever scopes OPEN-56's remedy should run
the cheap test — re-run a few of the 44 with `Zone.Volume` written."* **It turns out no re-run is
needed** (F5): the `.eio` already carries `Volume {m3}` per zone, even for runs that died fatal. So
the cheap test is cheaper than the register thought, and it can be run on all 44 instead of a few.

**How.**
1. From `open38_fatal_causes_2026-08-20.csv` take the 44 `(cell, mode, stem)` triples. For each,
   parse `eplusout.eio`'s `Zone Information` rows and record per zone: `zone_name`, `volume_m3`,
   `floor_area_m2`, `multiplier`, `ceiling_height_m`. The header line `! <Zone Information>,...`
   gives the column order — **parse the header, do not hard-code positions.**
2. Control: 200 non-fatal directories drawn from the same `(cell, mode)` distribution as the 44,
   `random.seed(2026)`. Same parse.
3. Flag a zone as **volume-degenerate** if `volume_m3 <= 0`, or if
   `abs(volume_m3 - floor_area_m2 * ceiling_height_m) / volume_m3 > 0.01`.
4. Join both groups to `open56_open09_run4_err_census_2026-08-20.csv` on `(cell, stem)` and report
   whether `has_volstub` co-occurs with fatality (2x2 table, with the caveat that the err census is
   auto-arm only — say so where the join drops non-auto rows).
5. Write `open38_open56_zone_volumes_2026-08-21.csv` (one row per zone) and a per-building summary.
6. Report: the 2x2; the volume distribution of the 44 vs the control; and whether the 86 % family
   (F7) is distinguishable from the rest on volume alone.

**How to test.**
- **C15** — all 44 `.eio` files are found and parsed, or the missing ones are named individually.
- **C16** — for one building, hand-check three zones' volumes against the raw `.eio` text.
- **C17** — the control is drawn without replacement and contains **zero** of the 44.

---

### T08 — OPEN-18: is the small-cold-cell sample reachable from what we already have? *(executor)*

**What.** Count how many fleet buildings satisfy the "small footprint, cold climate" condition
OPEN-18's √S test needs, and state whether the test can be run on the existing corpus.

**Why.** Register §4 C.11 lists OPEN-18 as **unsized — "needs a purpose-built small-cold-cell
sample"**. An unsized item cannot be prioritised. This task sizes it and, more usefully, answers
whether "purpose-built" is even necessary: if the existing 8,160 already contain a few hundred small
cold buildings, the test is a filter away rather than a simulation campaign away.

**How.**
1. Read `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-18-20_method-bounds.md` and
   `MEASUREMENT_open-03-18_untrimmed-sample.md` and extract, **quoting them with file:line**, the
   exact criteria the √S test needs (footprint size band, climate condition, storey range). **If the
   criteria are not stated numerically anywhere, say so and propose a band in the doc as an explicit
   assumption, flagged as the executor's, not the record's.**
2. Apply the criteria to the fleet: per cell, count qualifying buildings among the successfully
   simulated. State which EPW each cell used (`02a_climate_epw.parquet`) rather than assuming the
   climate from the city name.
3. Write `open18_small_cold_population_2026-08-21.csv`.
4. Report: n qualifying, per cell and per archetype; whether n clears whatever minimum the criteria
   doc states; and one sentence on whether new simulation is needed.

**How to test.**
- **C18** — every criterion used is either quoted from a doc with a file:line, or labelled as the
  executor's assumption. No unlabelled criterion.
- **C19** — the qualifying set is drawn only from `simulation_status == 'success'`.

---

### T09 — OPEN-19: is LA still running hot on the adopted run, and by how much? *(executor)*

**What.** Restate the LA offset at fleet scale on run 4, and inventory what code-year / climate-zone
representation exists in the pipeline at all.

**Why.** OPEN-19 has sat as *"LA runs ~+40 % hot — Title 24 vs ASHRAE 90.1"* since long before the
adopted run existed. **The +40 % is a legacy number from a smaller population, and the register
itself says the hypothesis is "not currently representable".** Two cheap things are owed before the
item can be prioritised: (a) does the offset survive at 8,160, and (b) is there any field in the
codebase where a code year could even be carried.

**How.**
1. From the twelve `05_results.csv`, pooled EUI (Σ energy ÷ Σ area — never a mean of ratios) by city
   and by cell, restricted to `simulation_status == 'success'`. Report LA vs Austin vs NYC.
2. Because archetype mix differs by city, also report the **archetype-matched** comparison: for each
   archetype present in all three cities, the per-city pooled EUI and the LA offset. **The mix-free
   number is the one that speaks to OPEN-19; say which is which.**
3. Report the heating vs cooling split of the LA offset (`heating_eui_kwh_m2`,
   `cooling_eui_kwh_m2`) — a Title 24 envelope story and a weather story predict different splits.
4. Inventory: grep the codebase for any field carrying a code year, standard, or climate zone
   (`STD2022`, `climate_zone`, `code_year`, `ashrae`, `title24`, case-insensitive) and report
   file:line for each hit, with one line on whether it is per-building or per-archetype.
5. Write `open19_city_offset_2026-08-21.csv`. **Do not restate the fleet headline.**

**How to test.**
- **C20** — the pooled figure over all twelve cells reproduces **153.8231 kWh/m²** over **8,153**
  buildings (the adopted number). If it does not, stop and report the mismatch — that would be a
  bigger finding than OPEN-19.
- **C21** — the archetype-matched comparison names the archetypes it used and the n behind each.

---

### T10 — OPEN-09 x OPEN-38: are the non-convergent 16 and the fatal 44 the same story? *(executor)*

**What.** Join the two populations and test for overlap.

**Why.** F6 says OPEN-09's 16 non-convergent buildings are **all in LA**. F7 says 86 % of the 44
fatals are an inside-surface heat-balance temperature divergence, and the register notes the
`la_rural` concentration is *entirely* `Warehouse`. **`Inside surface heat balance did not converge`
and `CalcHeatBalanceInsideSurf: The temperature of <NUM> C` are the same solver, one warning and one
fatal.** If the two populations are the same buildings at different severities, that is one item and
not two — and the register carries them as two.

**How.**
1. Population A: the 16, from `open56_open09_run4_err_census_2026-08-20.csv` where `has_converge`
   is true. Population B: the 44, from `open38_fatal_causes_2026-08-20.csv`.
2. Normalise stems, then report: |A ∩ B| by stem; |A ∩ B| restricted to `mode == 'auto'` (the only
   mode where the err census applies); and the archetype and cell of every member of A and of
   A ∩ B — 16 rows is small enough to print in full.
3. For each member of A **not** in B, record whether that building nonetheless carries any
   `CalcHeatBalanceInsideSurf` line in its auto-arm `.err` (grep the raw file), which tests the
   "same mechanism, different severity" reading directly rather than by ID overlap alone.
4. Write `open09_open38_overlap_2026-08-21.csv`.
5. Report the verdict in one sentence: same population, overlapping population, or disjoint. **Do not
   propose a merge of the two items — that is the director's call.**

**How to test.**
- **C22** — |A| is exactly **16** and its cell split is `la_centre 2, la_rural 10, la_suburban 3,
  la_urban 1`. If not, stop.
- **C23** — |B| is exactly **44**.

---

## 7. Stop-and-report points

- **CP-A — after T01, T02, T03.** The OPEN-53 pair and the OPEN-17 census. Report the three docs and
  the answer to "is the harvest meter-only".
- **CP-B — after T04, T05, T06.** The three sizing tasks. Report the numbers, not the method.
- **CP-C — after T07, T08.**
- **CP-D — after T09, T10.** Final.

At every checkpoint the **director** — not the executor — updates the register, the checklist, the
director prompt and the board.

---

## 8. Progress log

*(one entry per completed task; executors append here, newest at the bottom)*

#### T01 — OPEN-53: is "meter-only" a property of the 874, or of the whole harvest? — completed 2026-08-21

**Artifacts:** `scripts/analysis/open53_harvest_sql_census_2026-08-21.py`;
`openubem/outputs/comparisons/open53_harvest_sql_census_2026-08-21.csv` (40,800 rows);
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-53_harvest-sql-census.md`.

**Deviations:** none.

**Test status:** C1 PASS (`.end`-missing = 875, exact match). C2 PASS (3 hand-checked files matched
census rows exactly). C3 — F4 confirmed at full-census scale, not overturned: **all 39,926**
directories with a readable `.sql` have 0 ABUPS End-Uses rows and 0 zone-level keys — meter-only is a
property of the whole harvest, not of the 874 missing files.

**Notes:** the 874 missing `.sql` are entirely in `austin_suburban`'s `fast_zone`/`floor` arms (437
each); `auto`, `building`, `layout_assign` are 100 % complete (8,160/8,160 each). Re-fetching the 874
would buy custody only, not zone/ABUPS detail — every other file lacks that detail too. This narrows
OPEN-53 to its second question, measured in T02.

#### T02 — OPEN-53: what would a meter-only EUI actually cost? — completed 2026-08-21

**Artifacts:** `scripts/analysis/open53_meter_only_eui_2026-08-21.py`;
`openubem/outputs/comparisons/open53_meter_only_eui_2026-08-21.csv` (8,153 rows);
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-53_meter-only-eui-cost.md`.

**Deviations:** none.

**Test status:** C4 PASS (join lost 0/8,160, 0.000 %). C5 PASS (3 buildings, independent re-query
agreed to full float precision). C6 — pooled meter-only EUI (151.28 kWh/m²) is **not** within 1 % of
153.8231 kWh/m² (gap 1.66 %); stated explicitly in the doc that this would not have been a validation
of the census either way.

**Notes:** median `pct_diff` ~0 %, IQR −2.29 % to 0 %; 548/8,153 (6.7 %) exceed ±10 %, concentrated in
the `OpenUBEMUnknown` archetype (n=650, median +33.9 %) and a scatter of individual buildings, not a
whole archetype family. Only two meters found fleet-wide (`Electricity:Facility`,
`NaturalGas:Facility`) — no district heating/cooling meter present in the auto arm.

#### T06 — OPEN-62: the storey-definition decision table — completed 2026-08-21

**Artifacts:** `scripts/analysis/open62_storey_definition_table_2026-08-21.py`;
`openubem/outputs/comparisons/open62_storey_definition_table_2026-08-21.csv` (184 rows);
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-62_storey-definition-table.md`.

**Deviations:** the attic-excluded variant could not be built as a numerically distinct column.
`auto_attic_zone_count` exists in `open03_storey_census_zfix.csv` as specified, but is **0 for all
8,160 rows**, so `layout_assign_storey_count_floor − auto_attic_zone_count` is identical, row for
row, to `layout_assign_storey_count_floor` on this census. Reported as a finding in the doc rather
than routed around; no substitute column was invented.

**Test status:** C13 PASS — `layout_assign_match_storeys_status` gives `identity` 1,226 + `applied`
502 + `no_baseline_fallback_auto` 718 = 2,446/8,160 = 29.9755 % → 30.0 %, complement 70.0245 % →
70.0 %, both matching the register's quoted split. C14 PASS — row count exactly 8,160.

**Notes:** fleet-wide agreement rate vs `auto_storey_count`: `layout_assign_storey_count`
(Z_Origin-corrected) 29.07 %, `_naive` 39.78 %, `_floor` 23.75 %, attic-excluded (= `_floor`) 23.75 %;
none reaches 50 %, and ranking is unchanged whether `auto_storey_count` or `source_storey_count` is
used as baseline (the two track each other closely fleet-wide). On the six collapse-risk archetypes
(2,983/8,160 = 36.6 %, matching the register), the corrected and floor readers agree far less often
than on the rest of the fleet (11.5–11.7 % vs 30.7–39.2 %), confirming these archetypes are where the
definitions diverge materially; the naive reader is the outlier, agreeing slightly *more* on the
flagged population because both it and `auto_storey_count` are pulled low by `MidriseApartment`
(2,818 of the 2,983 flagged rows). No definition recommended, per the plan.

#### T07 — OPEN-38 x OPEN-56: are the 44 fatals volume-anomalous? — completed 2026-08-21

**Artifacts:** `scripts/analysis/open38_open56_zone_volumes_2026-08-21.py`;
`openubem/outputs/comparisons/open38_open56_zone_volumes_2026-08-21.csv` (2,040 zone rows);
`openubem/outputs/comparisons/open38_open56_zone_volumes_by_building_2026-08-21.csv` (70 building
rows); `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-38-56_fatal-zone-volumes.md`.

**Deviations:** F5 ("`.eio` carries per-zone volume even for runs that died fatal") does not
generalise past the one building it verified. A plain existence walk of the whole E02 harvest
(40,800 directories) found only **145 (0.36 %)** have an `eplusout.eio` at all. Consequences,
reported rather than hidden: only **23 of the 44** fatal buildings could be read (52.3 %); the
control's `(cell, mode)`-proportional target of 200 could not be met from `.eio`-present candidates
alone (several required combos had 0–1 available) — **47 controls were drawn, every eligible
`.eio`-present candidate in the required combos, none left unsampled.**

**Test status:** C15 — 23/44 read, 21/44 named individually as missing (no `.eio` file, not a parse
failure). C16 PASS — `la_rural_auto/way_472960972`, 3 zones hand-checked against raw `.eio` text,
exact match. C17 PASS — control drawn without replacement, seed 2026, 0 overlap with the 44.

**Notes:** zone-level volume-degenerate rate is higher in the fatal group (19.19 % vs 4.18 %) but the
per-building any-degenerate rate is not (26.09 % vs 34.04 %) — the two readings disagree because
fatal buildings carry very different zone counts. Fatal zone volumes skew far smaller at the median
(41.9 m³ vs 453.2 m³) but with a heavier large-volume tail (max 78,552.81 m³ vs 15,072.61 m³). F7's
"86 % family" resolved precisely: 21 `Temperature (high) out of bounds` + 17
`CalcHeatBalanceInsideSurf` = 38/44 = 86.4 %; on the 19 of those 38 that were readable, median
per-building volume (34.45 m³) is far smaller than the other 4 readable fatals (249.40 m³), but the
degenerate-zone rate is nearly identical between the two (26.3 % vs 25.0 %) — volume alone does not
cleanly separate the mechanism family from the rest. The OPEN-56 join (`has_volstub`) is auto-arm
only per its own scope and covers just 20 of the 70 readable buildings (6 fatal, 14 control); on
that small join, `has_volstub = True` fires for **every** building in both groups — it does not
discriminate fatal from non-fatal here.

#### T08 — OPEN-18: is the small-cold-cell sample reachable from what we already have? — completed 2026-08-21

**Artifacts:** `scripts/analysis/open18_small_cold_population_2026-08-21.py`;
`openubem/outputs/comparisons/open18_small_cold_population_2026-08-21.csv` (130 rows, one per
`cell x archetype_id`); `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-18_small-cold-population.md`.

**Deviations:** no doc on disk states a numeric footprint band, cold-climate threshold or storey
range for the √S test (searched `MEASUREMENT_open-18-20_method-bounds.md` and
`MEASUREMENT_open-03-18_untrimmed-sample.md` in full). Per the plan's own fallback instruction, an
explicit executor-proposed band was used instead, flagged as such in the doc: "small" = footprint
area at or below the per-cell 35th percentile among `simulation_status == 'success'` buildings
(reusing the only precedent on disk); "cold" = ASHRAE climate zone 5+ (a standard external
definition, not drawn from any OpenUBEM doc).

**Test status:** C18 PASS — every criterion is either quoted with file:line or labelled
`EXECUTOR-PROPOSED`. C19 PASS — qualifying set drawn only from `simulation_status == 'success'`.

**Numbers:** fleet success population 8,153. Per-cell footprint p35 filter alone: 2,855 buildings.
Cross-checking each cell's climate zone against `02a_climate_epw.parquet` found the register's own
"coldest cells" proxy (`nyc_rural`/`nyc_centre`) is **not climatically uniform** — `nyc_centre` is
ASHRAE 4A (same as `nyc_suburban`/`nyc_urban`), only `nyc_rural` is 6A. Under the zone-5+ definition,
**n = 69**, entirely in `nyc_rural`: `SmallOffice` 56, `MidriseApartment` 7, `OpenUBEMUnknown` 5,
`SmallHotel` 1. No new simulation is needed for a first cut at this n=69 (all already `auto`-mode
`success` rows); a broader or archetype-balanced sample would need new runs.

#### T09 — OPEN-19: is LA still running hot on the adopted run, and by how much? — completed 2026-08-21

**Artifacts:** `scripts/analysis/open19_city_offset_2026-08-21.py`;
`openubem/outputs/comparisons/open19_city_offset_2026-08-21.csv` (60 rows: 3 city, 12 cell, 45
archetype-matched); `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-19_city-offset-fleet-scale.md`.

**Deviations:** none from the plan's steps. One scope clarification recorded in the doc's §0: the
historic "+38.8 %" figure is LA-simulated-vs-LA-measured (no benchmark data exists in this corpus,
so it cannot be re-derived here); this task restates the simulated-vs-simulated city comparison the
plan actually specifies, which is a different number answering a different question.

**Test status:** C20 — n reproduces exactly (8,153). Pooled figure reproduces to **153.8304** against
the adopted **153.8231**, 0.0047 % relative, not bit-for-bit; per-cell gaps up to 0.18 kWh/m²
(`austin_suburban` 159.02 here vs 159.20 in `MEASUREMENT_fleet-restatement-2026-08-19.md`) were found
against that doc's per-cell table and are reported, not adjusted or root-caused — both sides use the
identical Σ(EUI×area)/Σ(area) definition over the same on-disk files. Judged not to rise to "a bigger
finding than OPEN-19" given the fleet-level closeness, but flagged as an open, unexplained
discrepancy. C21 PASS — archetype-matched comparison names all 15 shared archetypes and each city's n.

**Numbers:** city pooled EUI (mix-included): austin 161.00, **la 128.13**, nyc 165.27 — **LA is the
lowest of the three, not the highest** (LA vs Austin −20.41 %, LA vs NYC −22.47 %). Archetype-matched
(15 shared archetypes): austin 154.94, la 129.09, nyc 172.77 (LA vs Austin −16.68 %, LA vs NYC
−25.28 %) — same sign, mix does not explain it away. Heating/cooling split does not show an
envelope-story or weather-story signature favouring the +40 % hypothesis. Independent re-grep of
`openubem/` for `STD2022|climate_zone|code_year|ashrae|title.?24` (109 hits) confirms zero Title
24/CALGreen/CEC references anywhere; `climate_zone` reaches only `get_construction_set()` (wired to
the `OpenUBEMUnknown` synthetic path only) and the dead `economizer_db_limit_c` data field
(`openubem/data/loads/hvac_systems_by_archetype.json`, never read by `openubem/idf/hvac.py`'s 6
hardcoded economizer sites).

#### T10 — OPEN-09 x OPEN-38: are the non-convergent 16 and the fatal 44 the same story? — completed 2026-08-21

**Artifacts:** `scripts/analysis/open09_open38_overlap_2026-08-21.py`;
`openubem/outputs/comparisons/open09_open38_overlap_2026-08-21.csv` (16 rows);
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-09_open-38_overlap.md`.

**Deviations:** none from the plan's steps. One error hit and registered per hard rule 8:
`UnicodeEncodeError` printing `∩` on the Windows cp1252 console — fixed by replacing the glyph;
entry extended in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` §13.

**Test status:** C22 PASS — |A| = 16 exactly, cell split `la_centre 2, la_rural 10, la_suburban 3,
la_urban 1` matches F6. C23 PASS — |B| = 44 exactly.

**Numbers:** |A ∩ B| any mode = 11; restricted to `mode == 'auto'` (the comparable population) = 6.
The overlap splits cleanly by archetype: all 6 null-`archetype_id` buildings in A are also
`auto`-mode fatals in B (100 %), all 10 `Warehouse` buildings in A are never `auto`-mode fatals in B
(0 %, though 5 of the 10 do go fatal in `fast_zone`/`floor` mode). The 6 auto-mode overlaps are all
`Temperature (high) out of bounds` (F7's 21-building family); none of A's 5 fully-non-overlapping
Warehouse members carry a `CalcHeatBalanceInsideSurf` line in their auto `.err` (0/5, hand-grepped).
**Verdict: overlapping population, not the same and not disjoint** — the overlap tracks a variable
already in hand (null vs `Warehouse` archetype). No merge of the two items proposed, per the plan.

---

#### T03 — OPEN-17: how much does each imputation target actually need filling? — completed 2026-08-21

**Artifacts:** `scripts/analysis/open17_target_null_census_2026-08-21.py`;
`openubem/outputs/comparisons/open17_target_null_census_2026-08-21.csv` (84 rows = 12 cells x 7
targets); `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-17_target-null-census.md`.

**Deviations:** the plan's placeholder seventh target `roof_shape` is wrong, per the plan's own
fallback instruction ("if the register's seventh target is not `roof_shape`, quote the conflict and
use the register's list"). `01_buildings.gpkg` has no `provenance_roof_shape` column, and the
register's own OPEN-17 citation (`extra/MEASUREMENT_open-17_tier-census.md`) names the seven targets
as `building_tag, function_tag, geometry, height_m, levels, postcode, year_built`. Used that list
(with `geometry` in place of `roof_shape`) — not a stop, since the plan named exactly this
contingency and its resolution.

**Test status:** C7 PASS — 8,160 across the twelve gpkgs, exact. C8 PASS/consistent — `year_built`'s
raw-null count (5,913) matches the known `5,913/5,913` tier-fill figure exactly.

**Notes:** fleet-wide needs-a-value counts (provenance-based, not raw null):
`levels` 7,719 (94.6 %), `function_tag` 7,741 (94.9 %), `year_built` 5,913 (72.5 %, filled 100 %),
`postcode` 4,183 (51.3 %), `building_tag` 4,105 (50.3 %), `height_m` 2,806 (34.4 %), `geometry` 0.
**`function_tag` and `building_tag` are never raw-`NaN`** — `function_tag` is `OSM_MISSING` as a
placeholder string and `building_tag` is present-but-generic (`OSM_GENERIC`, e.g. `"yes"`); a
null-only census would have missed both, and they turn out to be the second- and fourth-largest
holes on the list. Only `year_built` has a wired production imputer; the 5-tier `impute_missing`
machinery exists but is never called from the fleet-build path for any other target.

---

#### T04 — OPEN-14: what does the null-`height_m` hole look like across all twelve cells? — completed 2026-08-21

**Artifacts:** `scripts/analysis/open14_null_height_by_cell_2026-08-21.py`;
`openubem/outputs/comparisons/open14_null_height_by_cell_2026-08-21.csv` (12 rows);
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-14_null-height-by-cell.md`.

**Deviations:** none.

**Test status:** C9 PASS — `nyc_centre`'s null-`height_m` count reproduces 121 exactly. C10 PASS —
every extrapolated figure in the doc carries "extrapolated" in the same sentence.

**Notes:** fleet-wide 2,806/8,160 (34.4 %) null `height_m`. The hole is concentrated, not spread:
`austin_rural`, `nyc_rural`, `nyc_suburban` are **100 % null** and together carry 2,032/2,806
(72.4 %) of the fleet total; `nyc_suburban` alone is 1,589/2,806 (56.6 %), more than every other
cell combined. Applying `nyc_centre`'s measured fusion-tier fill rate (106/121 = 87.60 %) to the
other eleven cells' 2,685 nulls as a labelled extrapolation (not a measurement): ~2,352 would fill,
~333 would remain. Null `height_m` and null `levels` co-occur at ≥65 % in every cell with a
non-trivial hole — the direct link to OPEN-35/T05 below.

---

#### T05 — OPEN-35: how many buildings sit on the undecided branch? — completed 2026-08-21

**Artifacts:** `scripts/analysis/open35_fallback_population_2026-08-21.py`;
`openubem/outputs/comparisons/open35_fallback_population_2026-08-21.csv` (39 rows);
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-35_fallback-population.md`.

**Deviations:** none. `archetype_source` is not persisted in the adopted run's own artifacts
(`04_simulation_manifest.parquet`, `step3/03_idf_manifest.parquet` — both checked, neither carries
it), but an on-disk artifact does carry it fleet-wide
(`openubem/outputs/comparisons/open35_fallback_agreement_scope.csv`, 2026-08-19), verified to be the
identical population to `evidence/open48_refleet4` before use (same `osm_id` sets and null-`height_m`
counts for `austin_centre`, spot-checked). Reused rather than re-running the classifier, per the
plan's own instruction.

**Test status:** C11 PASS — all 39 have both `levels` and `height_m` null, 0 counter-examples. C12
PASS — all 21 buildings of the existing OPEN-35 sample are inside this task's 39; no difference to
explain.

**Notes:** the undecided branch carries **39 buildings** (six cells: `austin_rural` 17, `nyc_centre`
8, `austin_centre` 5, `nyc_urban` 5, `la_urban` 3, `austin_suburban` 1) — nearly double the
21-building sample OPEN-35's regression work has been reasoning about. 38 of the 39 were simulated
successfully; the 39th is the known dropped `nyc_centre / way/266034056` regression building.
Denominator-only stake (headline not restated, per the plan): swapping just these 38 buildings from
the current group-/global-median branch to the pre-OPEN-35 `return 1` branch would take the fleet
floor-area denominator from 24,333,586.4 m² to 23,553,430.3 m² — a **-3.21 %** shift.

---

## 9. Director sign-off — 2026-08-21

All ten tasks executed by four concurrent Sonnet executors; ten progress entries appended to §8 with
no collisions. Audit per CLAUDE.md: progress entries present → control output checked → file set
compared against §3 → citations checked for every unplanned decision. **Only the planned files were
touched** (11 scripts under `scripts/analysis/`, 12 CSVs under `openubem/outputs/comparisons/`, 10
`MEASUREMENT_*.md` under `openings/extra/`, and §8 of this doc). Nothing was committed.

**CP-A — T01, T02, T03. SIGNED.** C1–C8 reported. Director re-derived T02's pooled figures
independently (151.2765 / 153.8304, reproducing the executor) and found the divergence is
archetype-deterministic, not smooth, with the elevator adder carrying ≈88 % of the pooled gap.
Recorded as a director addendum in `extra/MEASUREMENT_open-53_meter-only-eui-cost.md`. **The
executor's numbers stand; its interpretation was narrowed.**

**CP-B — T04, T05, T06. SIGNED, with one arithmetic basis clarified.** T05 reported the fleet
denominator moving 24,333,586.4 → 23,553,430.3 m² (−3.21 %). The director's first re-derivation, using
the script's own recomputed `current_floor_area_m2` column over all 39 rows, gave −2.96 %. **The
executor's basis is the correct one** — it used the published `floor_area_m2` from `05_results.csv`,
which *is* the fleet denominator, over the 38 simulated buildings; the fleet total 24,333,586.4 was
confirmed exactly against all twelve cells. The two bases differ on 13 buildings, dominated by
`relation/7480583` (published 301,996.35 vs recomputed 242,204.26 m²). **−3.21 % stands.** Director
addition: the top five buildings carry ~71 % of the delta and `relation/7480583` alone is 1.24 % of
the whole fleet floor area.

**CP-C — T07, T08. SIGNED, with the director's own error recorded against the task.** T07's coverage
shortfall is not an executor failure — it is a failure of **F5 in §5 of this plan**, which asserted
that `.eio` survives fatal runs on the evidence of one building. Independently reproduced: **145 of
40,800 harvest directories (0.36 %) contain an `.eio`.** T07's findings are sound for what it could
read and **must not be quoted at fleet scale**. T08's labelled assumption is accepted as plan rule 4
required, and its correction of the register's `nyc_centre` "cold cell" proxy is adopted.

**CP-D — T09, T10. SIGNED.** C20–C23 reported. T09's LA result reverses the expected sign and the
executor correctly refused to conflate a sim-vs-sim city comparison with the historic sim-vs-measured
+38.8 %. ⚠️ **C20's 153.8304-vs-153.8231 gap is not closed** — the director's independent CP-A
re-derivation returned 153.8304 as well. Two recomputations from the adopted evidence do not return
the adopted number exactly (0.005 %). Immaterial to every conclusion here; **the adopted baseline is
unchanged at 153.8231 pooled over 8,153**, and the discrepancy is recorded in the register as an open
loose end rather than resolved by adjustment.

**Outcome of the pass: no item closed, no item opened, no published number moved, no ruling taken.**
Six items now hold a measurement they lacked this morning; three of the pass's findings contradict
something the register previously asserted (OPEN-53's sampling, OPEN-35's population, OPEN-18's
climate proxy), and one contradicts a fact in this plan (F5).
