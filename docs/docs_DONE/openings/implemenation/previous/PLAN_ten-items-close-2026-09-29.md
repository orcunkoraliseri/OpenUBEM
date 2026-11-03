# PLAN — close ten of the twelve live items — 2026-09-29

## 1. Header

- **Slug:** `ten-items-close-2026-09-29`
- **Date:** 2026-09-29. **Author:** director (manager session).
- **Authority:** user, 2026-09-29, verbatim: *"select 10 items to close, i am execute solve, update the
  artifact"*. Read as: the user selects nothing, authorises execution, and wants the boards updated.
  This includes the OPEN-65 CPU-only re-parse the START HERE box of
  `prompts/DIRECTOR_PROMPT_openings.md` was waiting on. **It does not include adopting a new published
  number** — adoption (CP-1 below) stays the user's alone.
- **DESIGN pointer:** `docs/docs_main/` P5 integrity gates as implemented at
  `openubem/results/parser.py:850` (`check_building_integrity`); register
  `docs/docs_DONE/openings/INVESTIGATION_open-items-register-II.md` §4 and §6.

**The ten.** OPEN-65, OPEN-61, OPEN-63 (one re-parse), OPEN-66, OPEN-38, OPEN-58 (executor work);
OPEN-03, OPEN-19, OPEN-53, OPEN-59 (director closures, accepted limitations, no executor task).
**Left open on purpose:** OPEN-35 and OPEN-62 — both are "what is a storey" rulings the user owns.

## 2. Hard rules for the executor

1. Execute your task(s) only. Do not propose alternatives. If this plan or a cited line is wrong, STOP
   and quote the conflict.
2. **No compute on the Speed login node.** Login node = `mkdir`, `scp`, `tar`, `squeue`, `sacct`,
   `ls`. Every remote command goes through a `_ssh()` wrapper that runs `bash -lc` (port it from
   `scripts/cluster/t08_harvest_results.py:102`).
3. **Simulations never run sequentially and never locally by default.** Any EnergyPlus run → one
   `sbatch --array=1-N%32 --time=7-00:00:00` on Speed. Local CPU work (parsing) ≤ 10 processes.
4. **Never delete by exclusion** in any live folder. Never touch another project's cluster job.
5. No code comments. No `.py` under `docs/`. Figures/CSVs → `openubem/outputs/comparisons/` (flat).
6. Never edit root `main.py`, OVERVIEW or DESIGN docs.
7. Append **one** progress-log entry per task under §8, in the placeholder for your task only.
8. After fixing any error, add one entry to `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` in
   house format; drop `[OPEN]` from the OPEN-65 entry (§8) only when T03 lands.
9. No published number is adopted by an executor. Output of T02 is a **candidate**.

## 3. File layout

| Path | Task | Kind |
|---|---|---|
| `implemenation/previous/PLAN_accuracy-restatement-2026-09-09.md` | T01 | move |
| `scripts/analysis/open65_reparse_2026-09-29.py` | T02 | new |
| `openubem/outputs/comparisons/open65_reparse_fleet_eui_2026-09-29.csv` | T02 | new |
| `openubem/outputs/comparisons/open65_reparse_summary_2026-09-29.json` | T02 | new |
| `scripts/cluster/t08_harvest_results.py`, `scripts/cluster/t07_harvest_results.py` | T03 | edit |
| `tests/test_harvest_uses_production_parser.py` | T03 | new |
| `openubem/idf/builder.py` | T04 | edit |
| `tests/test_builder_zero_zone_flag.py` | T04 | new |
| `openubem/outputs/comparisons/open66_zoneless_diagnosis_2026-09-29.csv` | T04 | new |
| `openubem/outputs/comparisons/open38_rerun_2026-09-29.csv` | T05 | new |
| `scripts/analysis/open56_zone_volume_experiment.py` | T06 | edit |

## 4. Dependency decisions (pinned)

- **D1 — harvest scripts may not keep a parser of their own** (director, answering the question OPEN-65
  left). Every fleet harvest that produces a published number calls
  `openubem.results.parser.parse_building()`. Historical one-off copies
  (`scripts/cluster/t19_harvest_layout_assign.py:180`, `t20_harvest_layout_assign.py:180`, and their
  importers `scripts/analysis/b05e_measure_energy_delta.py:39`, `b08b_measure_energy_delta.py:41`,
  `c01_storey_matching_regression.py:44`) are **not** edited — none feeds a live number.
- **D2 — `abups_ok` is wired as a reported gate, not a filter.** Each re-parsed building carries
  `abups_ok` from `check_building_integrity()` (`openubem/results/parser.py:850`); failures are counted
  and listed, not dropped. `meter_ok` and `gas_zero` stay unwired (register: `meter_ok` mis-specified).
- **D3 — route for the re-parse: fetch, then parse locally** (the route T08 proved on 2026-09-10:
  12 per-cell batches, `ssh … tar czf - --ignore-failed-read -T -` with the file list on stdin). CPU
  only, ≤ 10 local processes. Fetch only `eplusout.sql` and `eplusout.eio`.
- **D4 — denominator is held fixed.** Floor area per building must equal the T08 CSV value; the
  re-parse changes the numerator only.
- **D5 — OPEN-66 fix scope.** The flag fix is mandatory. The root-cause fix is in scope only if it is
  one function and ≤ 30 changed lines; otherwise it is recorded `[OPEN]` in the debug references and
  the item still closes on the flag.

## 5. DESIGN / repository facts with citations

- F1. Production parser: `parse_building(sql_path, csv_path, manifest_row)` at
  `openubem/results/parser.py:964`; district heating read by `_read_abups_district_heating_rows`
  (`:158`); floor area by `resolve_simulated_floor_area` (`:542`) / `parse_eio_zone_area` (`:371`).
- F2. Meter-only copy that computed the adopted figure: `scripts/cluster/t08_harvest_results.py:163`
  (`_parse_sql`), reused by T08 of the archived plan (its T08 log entry).
- F3. Carbon: `openubem/results/carbon.py:32` `compute_gwp()`; district-heat factor
  `openubem/config.py:127` `GWP_DISTRICT_HEATING_KGCO2_KWH = 0.226`.
- F4. Adopted run: Speed job `1315099`, results
  `/speed-scratch/o_iseri/openubem/fleets/t07_resim_2026-09-09/out/<stem>/`; 8,139 successes, 13
  failed indices listed in the archived plan's T07 entry. Adopted table:
  `openubem/outputs/comparisons/t08_restated_fleet_eui_2026-09-10.csv` (8,139 rows) and
  `t08_restated_fleet_summary.json` — **153.9501 kWh/m², 881,743.09 t CO₂e**. ⚠ superseded 2026-09-30: adopted 172.41 kWh/m² and 981,720 t CO₂e over the same 8,139 buildings (153.95 / 881,743 missed district heating and double-counted cooking + refrigeration in 129 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_ten-items-close-2026-09-29.md CP-1). ⚠ superseded 2026-09-30 (three rulings): adopted 171.38 kWh/m² and 1,146,454 t CO₂e over the same 8,139 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_three-rulings-2026-09-30.md CP-B.
- F5. Rebuild manifests (no `floor_area_m2` column):
  `%TEMP%\ubem_validation\t06_rebuild_2026-09-09\<cell>\step3\03_idf_manifest.parquet`.
- F6. Subset measurement (OPEN-65 §6): 2,741 buildings, pooled 159.27 → 179.24 kWh/m²; expect the
  fleet delta near +20 kWh/m².
- F7. Builder success path: `openubem/idf/builder.py:582-592` (`layout_assign`) and the general
  status at `:714`; existing failure statuses at `:642`, `:655`, `:676` (`failed_no_extruded_zones`).
- F8. OPEN-66 population: 8 buildings, listed in register §6 "OPEN-66".
- F9. OPEN-38 population and causes: `extra/MEASUREMENT_open-38_fatal-cause-census.md`,
  `openubem/outputs/comparisons/open38_fatal_causes_2026-08-20.csv`; rebuild recipe precedent:
  `extra/MEASUREMENT_open-38_five-fatals-rebuild.md`.
- F10. OPEN-58: `scripts/analysis/open56_zone_volume_experiment.py:150` `run_ep()` runs EnergyPlus
  without `cwd=outdir`; the isolated pattern is
  `scripts/analysis/open35_storey_intervention_2026-08-19.py:95-110`.

## 6. Tasks

### T01 — Archive the 2026-09-09 plan and sweep its citations *(executor, docs)*

**What.** `git mv` `implemenation/PLAN_accuracy-restatement-2026-09-09.md` into `implemenation/previous/`,
then repair every citation to it.
**Why.** START HERE box: archive first; the plan is complete (T01–T09, CP-1–CP-4).
**How.** `grep -rl "PLAN_accuracy-restatement-2026-09-09" --include=*.md --include=*.html --include=*.py`
over the repo (exclude `.git`). Resolve by filename, not path-prefix rewrite. Repoint each to
`implemenation/previous/PLAN_accuracy-restatement-2026-09-09.md` (relative form matching the citing
file's style). Do not touch this plan file's own citations in §1–§7.
**How to test.** Same grep afterwards: every hit carries `previous/`; report count before / after.
`ls implemenation/` shows only this plan and `previous/`.

### T02 — Re-parse the adopted run with the production parser *(executor, fetch + CPU)*

**What.** Produce the candidate restated EUI and carbon for the same 8,139 buildings with
`parse_building()`.
**Why.** OPEN-65 / OPEN-61 / OPEN-63: the adopted figure never saw district heating.
**How.**
1. Build the list of 8,139 stems from F4's T08 CSV. Fetch `eplusout.sql` + `eplusout.eio` per cell (D3)
   into `%TEMP%\ubem_validation\open65_reparse_2026-09-29\<cell>\<stem>\`. Report fetched count.
2. Script `scripts/analysis/open65_reparse_2026-09-29.py`: for each building build a `manifest_row`
   from the F5 manifest row (+ `footprint_area_m2`, `levels` from the upstream step parquet of the same
   cell; if absent, STOP and report), call `parse_building()`, then `compute_gwp()` with the same
   state/eGRID inputs T08 used, then `check_building_integrity()` for `abups_ok`. Pool
   `sum(total_kWh)/sum(floor_area_m2)`. `multiprocessing.Pool(10)` at most.
3. Per building, reconcile total energy against ABUPS `Total Site Energy`; any gap > 0.5 % is listed
   with the end use that explains it.
4. Write the CSV and JSON in §3. JSON carries: n, pooled EUI, carbon total, adopted values side by
   side (same population, so the delta **is** computable and must be stated), per-archetype delta,
   `abups_ok` fail count, reconciliation gap count.
**How to test.** (a) floor area equals T08 CSV for 8,139 / 8,139 (D4); (b) with district-heat columns
zeroed, pooled EUI reproduces 153.9501 to ≤ 0.01; (c) the 2,741-building subset of F6 reproduces ⚠ superseded 2026-09-30: adopted 172.41 kWh/m² and 981,720 t CO₂e over the same 8,139 buildings (153.95 / 881,743 missed district heating and double-counted cooking + refrigeration in 129 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_ten-items-close-2026-09-29.md CP-1). ⚠ superseded 2026-09-30 (three rulings): adopted 171.38 kWh/m² and 1,146,454 t CO₂e over the same 8,139 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_three-rulings-2026-09-30.md CP-B.
179.24 to ≤ 0.1; (d) `abups_ok` fail count and list reported.

### T03 — Harvest scripts call the production parser; `abups_ok` reported *(executor, code)*

**What.** Replace `_parse_sql` use in `scripts/cluster/t08_harvest_results.py` and
`scripts/cluster/t07_harvest_results.py` with `parse_building()`; add an `abups_ok` column (D1, D2).
**How.** Delete the local `_parse_sql` bodies; route through `parse_building()` and
`check_building_integrity()`. Keep CLI and output column names; add `abups_ok` and the district-heat
columns.
**How to test.** New `tests/test_harvest_uses_production_parser.py`: (1) neither script defines
`_parse_sql`; (2) on a golden `.sql` with district-heated hot water
(`tests/fixtures/golden_archetype_enduse/`), the harvest's total EUI equals `parse_building()`'s.
Run the new test plus `tests/test_parser_open61_district_heating.py` and
`tests/test_parser_open60_multiplier.py`; report pass counts. Update the OPEN-65 debug entry (drop
`[OPEN]`, cite file:line).

### 🛑 CP-1 — adoption checkpoint (USER ONLY). Stop after T02 + T03.

**Signed 2026-09-30 by the user, verbatim:** *"ok yes continue to the end, update the artficat as well"*
— adopts **172.41 kWh/m² over 8,139 buildings, 981,720 t CO₂e** (T02 candidate), replacing 153.95 / ⚠ superseded 2026-09-30: adopted 172.41 kWh/m² and 981,720 t CO₂e over the same 8,139 buildings (153.95 / 881,743 missed district heating and double-counted cooking + refrigeration in 129 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_ten-items-close-2026-09-29.md CP-1). ⚠ superseded 2026-09-30 (three rulings): adopted 171.38 kWh/m² and 1,146,454 t CO₂e over the same 8,139 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_three-rulings-2026-09-30.md CP-B.
881,743. Same population (8,139), same denominator (D4); only the numerator changed. ⚠ superseded 2026-09-30: adopted 172.41 kWh/m² and 981,720 t CO₂e over the same 8,139 buildings (153.95 / 881,743 missed district heating and double-counted cooking + refrigeration in 129 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_ten-items-close-2026-09-29.md CP-1). ⚠ superseded 2026-09-30 (three rulings): adopted 171.38 kWh/m² and 1,146,454 t CO₂e over the same 8,139 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_three-rulings-2026-09-30.md CP-B.

### T04 — OPEN-66: the zero-zone IDF must not be flagged `success` *(executor, code, local, no simulation)*

**What.** (1) Regenerate the 8 IDFs of F8 locally with current production code and name the cause of
the missing `Zone` objects per building. (2) Make the builder report
`generation_status = "failed_no_zones"` when the written IDF contains zero `Zone` objects (F7).
(3) Fix the root cause only under D5.
**How to test.** `tests/test_builder_zero_zone_flag.py` feeds a builder path that yields zero zones and
asserts the status. Regenerating the 8 gives either 8 × `failed_no_zones` or (if the cause is fixed)
IDFs with ≥ 1 zone. Write `open66_zoneless_diagnosis_2026-09-29.csv` (osm_id, cell, archetype, cause,
new status). Add a debug-references entry.

### T05 — OPEN-38: re-run the 44 `layout_assign` fatals with current production *(executor, Speed)*

**What.** Rebuild the 44 IDFs of F9 with current production code (volume fix in) and run them as one
Speed array.
**How.** Rebuild locally (generation only). Upload; `sbatch --array=1-44%32 --time=7-00:00:00` with
`submit_fleet_t07.sbatch`. State case count and width before submitting. Apply the CLAUDE.md
dead-task check (no writes for ~10 min + `sstat` AveCPU flat) before cancelling anything.
**How to test.** Every one of 44 has a terminal state. CSV `open38_rerun_2026-09-29.csv`: osm_id,
cell, old cause, new status, new fatal message (first line) or EUI.

### T06 — OPEN-58: isolate the scratch helper's working directory *(executor, code)*

**What.** In `scripts/analysis/open56_zone_volume_experiment.py:150`, run EnergyPlus with
`cwd=str(outdir)` (F10).
**How to test.** `python -m py_compile` passes; `grep -n "cwd=" ` shows the line; importers
(`grep -rl "open56_zone_volume_experiment" scripts/`) still import. No simulation.

### Director only (no executor) — close OPEN-03, OPEN-19, OPEN-53, OPEN-59 as accepted limitations

Closing notes in the register §6, one line each in §4, and a known-limitations line each in
`docs/docs_EXPLANATION/` §18 snapshot.

### T07 — Sweep every artifact quoting the old figure *(director, after CP-1)*

**What.** Put the 2026-09-30 supersession marker beside every quote of the old figure (superseded 2026-09-30) in `.md` and `.py`
under `docs/`, `scripts/`, `openubem/`, `tests/`; update the register (§1 state row, §2 rows OPEN-61/63/65,
§4 head, §6 closing note, §7 entry), the director prompt START HERE box, both boards (republished in place),
the two memory files, and the status field of the re-parse summary JSON.
**Why.** *A restated number invalidates every artifact downstream of its source* (CLAUDE.md, Finishing work).
**How to test.** A repo-wide scan finds zero lines quoting the old figure without the marker; both boards
the same; each board's script passes `node --check`.

## 7. Stop-and-report points

- **CP-1 (user)** after T02 + T03: adopt the re-parsed figure or not.
- **CP-2 (director)** after T04–T06: audit and close OPEN-66, OPEN-38, OPEN-58.
- ~~**T07 (after CP-1 only, not yet written):**~~ written and done 2026-09-30 (§6 T07, §8 T07). sweep every artifact quoting 153.95 / 881,743. ⚠ superseded 2026-09-30: adopted 172.41 kWh/m² and 981,720 t CO₂e over the same 8,139 buildings (153.95 / 881,743 missed district heating and double-counted cooking + refrigeration in 129 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_ten-items-close-2026-09-29.md CP-1). ⚠ superseded 2026-09-30 (three rulings): adopted 171.38 kWh/m² and 1,146,454 t CO₂e over the same 8,139 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_three-rulings-2026-09-30.md CP-B.

## 8. Progress log

#### T01 — Archive the 2026-09-09 plan and sweep its citations — completed 2026-09-29

- **Artifacts:** `git mv` of `implemenation/PLAN_accuracy-restatement-2026-09-09.md` to `implemenation/previous/`.
  52 files repointed by filename (perl lookbehind `(?<!previous/)`, `.md`/`.html`/`.py`, `.git` excluded):
  every bare `PLAN_accuracy-restatement-2026-09-09` became `previous/PLAN_accuracy-restatement-2026-09-09`
  and every `implemenation/PLAN_...` path gained `previous/`. Zero `.html` and zero `.py` files cited it.
- **Deviations:** none. This plan file's own §1-§7 citations (2 occurrences, lines 105 and 108) were left
  untouched as instructed; lines 41 and 110 already carried `previous/`.
- **Test status:** occurrences before 329 (2 with `previous/`, both in this plan); after 329, of which 327
  carry `previous/` and the 2 without are this plan's own §6 lines. No `previous/previous/` doubles.
  `ls implemenation/` shows only this plan and `previous/`.
- **Notes:** most citations were bare filenames in the "superseded 2026-09-10" banner, so no path form
  existed to preserve; `previous/` was prefixed to make them resolvable. The moved plan's own banner
  self-citations were repointed too.

#### T02 — Re-parse the adopted run with the production parser — completed 2026-09-29

**Artifacts.** `scripts/analysis/open65_reparse_2026-09-29.py`; `openubem/outputs/comparisons/open65_reparse_fleet_eui_2026-09-29.csv` (8,139 rows); `openubem/outputs/comparisons/open65_reparse_summary_2026-09-29.json`. Fetched `eplusout.sql` + `eplusout.eio` for 8,139 / 8,139 stems (12 per-cell batches, `tar czf - -T -` fed over stdin, nothing computed on the login node) into `%TEMP%\ubem_validation\open65_reparse_2026-09-29\<cell>\<stem>\`. Parsed with `parse_building()` + `compute_gwp()` (NY / CA / TX) + `check_building_integrity()`, `multiprocessing.Pool(10)`.

**Result (CANDIDATE, not adopted).** n = 8,139, all `parse_status == success`, all areas `eio_simulated`. Pooled EUI **172.4075 kWh/m2** (adopted 153.9501, delta +18.4574). Carbon **981,720.01 t CO2e** (adopted 881,743.09, delta +99,976.92). District heat alone adds +19.7091 kWh/m2. ⚠ superseded 2026-09-30: adopted 172.41 kWh/m² and 981,720 t CO₂e over the same 8,139 buildings (153.95 / 881,743 missed district heating and double-counted cooking + refrigeration in 129 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_ten-items-close-2026-09-29.md CP-1). ⚠ superseded 2026-09-30 (three rulings): adopted 171.38 kWh/m² and 1,146,454 t CO₂e over the same 8,139 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_three-rulings-2026-09-30.md CP-B.

**Deviations.** (1) F5 is wrong: the T06 rebuild folder `%TEMP%\ubem_validation\t06_rebuild_2026-09-09\` is empty (temp purge), so the `03_idf_manifest.parquet` files no longer exist. `manifest_row` was built instead from the run-4 frozen evidence: `evidence/open48_refleet/<cell>/step3/03_idf_manifest.parquet` (osm_id, num_zones, data_quality_flag, resolution_mode = "auto" on every row) and `evidence/open48_refleet/<cell>/01_buildings.gpkg` (footprint_area_m2, levels, height_m). All 8,139 osm_ids resolved in both. These fields cannot move any number here (area came from the `.eio` on 8,139 / 8,139); they only feed the zone-integrity check, which passed for all. (2) The reconciliation compares per-building `total_kWh` with ABUPS `Total Site Energy`; the explaining end use is the ABUPS End Uses row with the largest gap.

**Test status.** (a) PASS: floor area equals the T08 CSV on 8,139 / 8,139. (b) FAIL as written: with district-heat columns zeroed the pooled EUI is 152.6985, not 153.9501 (-1.2516). Fully explained, and the fault is in the adopted number, not the candidate: on 129 buildings (QuickServiceRestaurant 50, FullServiceRestaurant 32, LargeHotel 27, SecondarySchool 9, SuperMarket 5, Hospital 4, PrimarySchool 2) the adopted meter-only parser added `Cooking:InteriorEquipment:Electricity` + `Refrigeration:InteriorEquipment:Electricity` on top of `InteriorEquipment:Electricity`, which already contains them (double count; on 6 sampled buildings the two sub-meters equal the difference to the kWh). The other 8,010 buildings match to 0.000 kWh. The 129 explain all of the -1.2516, and the candidate matches ABUPS on them. (c) NOT RUNNABLE: the 2,741-building subset was defined by `.sql` files under `fleet06b_local_2026-09-18/out/baseline` that no longer exist, and no stem list was kept. Proxy: district-heat-only delta on all 8,139 is +19.71 kWh/m2, against +19.97 on the subset (F6 expects near +20). (d) `abups_ok` fail count **0** of 8,139 (none null). ⚠ superseded 2026-09-30: adopted 172.41 kWh/m² and 981,720 t CO₂e over the same 8,139 buildings (153.95 / 881,743 missed district heating and double-counted cooking + refrigeration in 129 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_ten-items-close-2026-09-29.md CP-1). ⚠ superseded 2026-09-30 (three rulings): adopted 171.38 kWh/m² and 1,146,454 t CO₂e over the same 8,139 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_three-rulings-2026-09-30.md CP-B.

**Notes.** Reconciliation against ABUPS `Total Site Energy`: 5 buildings (all LargeOffice) exceed 0.5 %, all between -0.50 % and -0.51 %, all explained by ABUPS `Heat Rejection` (not in the parser total). Per-archetype deltas are in the JSON (MidriseApartment +31.76 on n = 2,818, TallBuilding +38.27, SuperTallBuilding +36.01; QuickServiceRestaurant -350.89 and FullServiceRestaurant -282.15 because the double count disappears). The `test_b_explained` and `test_c` keys in the JSON were added after the run, from the CSV. New `[OPEN]` entry (the double count) added to the debug references. Adoption is CP-1, user only.

#### T03 — Harvest scripts call the production parser; `abups_ok` reported — completed 2026-09-29

**Artifacts.** `scripts/cluster/t08_harvest_results.py`: local `_parse_sql`, meter constants and the `sqlite3` import deleted; new `parse_production()` (`:141`, calls `parse_building()` + `check_building_integrity()`, raises `ValueError` carrying the production status when the parse is not `success`), `_production_row()` (`:157`, keeps the legacy `*_eui` column names, adds `abups_ok`, parser `floor_area_m2`, `elevators_eui_kwh_m2` and the district-heat columns), `_manifest_row()` (`:181`); `build_cell_info()` now carries `footprint_area_m2` and `levels`. `scripts/cluster/t07_harvest_results.py`: local `_parse_sql` and meter constants deleted; imports `parse_production` from the t08 module (`:97`), writes the production columns plus `abups_ok`. New `tests/test_harvest_uses_production_parser.py`. `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`: OPEN-65 entry lost `[OPEN]`, fix cited at file:line.

**Deviations.** (1) The plan cites `tests/fixtures/golden_archetype_enduse/` for the golden `.sql`; that folder holds only CSVs. The test uses `tests/fixtures/golden_sql/r1_single_zone.sql`, copied to a temp file with its Water Systems / District Heating cell set to 50 GJ (`UPDATE TabularData ... TabularDataIndex=216`), because no golden `.sql` carries district-heated hot water. (2) Behaviour change to record: a `.sql` from a `trim_outputs=True` IDF has no hourly zone variables, so `parse_building()` returns `failed_parse` and the harvest writes `parse_error` instead of a number (the old meter-only parser did read those). No live number depends on it.

**Test status.** `tests/test_harvest_uses_production_parser.py`: 4 passed (no `_parse_sql` in either script, 2 cases; harvest total equals `parse_building()` total on the district-heated copy; failed parse raises). `tests/test_parser_open60_multiplier.py`: all passed. `tests/test_parser_open61_district_heating.py`: 1 failed, rest passed. Combined run of the three files: 22 passed, 1 failed. The failure, `TestDistrictHeatingServingSpaceHeatingFoldedIntoHeating::test_r1_district_heating_serving_heating_folds_into_heating_and_total`, reads heating 335.70 against a golden 167.85 (factor 2); `openubem/results/parser.py` is unmodified, so T03 did not cause it. Both scripts pass `py_compile`; the T08 pipeline was not re-run end to end (no fleet in scope).

**Notes.** CP-1 (adoption) is next and belongs to the user.

- **Director audit 2026-09-29 (T02 + T03): PASS, CP-1 reached.** Summary JSON re-read: n = 8,139, all success, candidate 172.4075 / 981,720.01 t, adopted recomputed on the same population 153.9501 / 881,743.09, `abups_ok` fails 0. Test (b) failing as written is accepted: the -1.2516 is a double count in the adopted parser (129 buildings), so it strengthens the case for adoption rather than weakening it. Test (c) not runnable (subset `.sql` purged) — proxy +19.71 vs +19.97 accepted. The failing `test_r1_district_heating_serving_heating_folds_into_heating_and_total` is **not** a district-heat double count: re-run by the director, `parse_building()` now divides by the simulated area 196 m² (`floor_area_provenance = sql_simulated`, the OPEN-60 denominator fix) while `golden_expected.json` still carries 392 m² (footprint × 2 floors). Stale golden, pre-dating this plan; it does not touch the fleet figure (all 8,139 areas are `eio_simulated` and equal T08). Deviations T02-(1)/(2) and T03-(1)/(2) accepted. **Waiting on the user: adopt 172.41 kWh/m² / 981,720 t or not. T07 sweep not started.** ⚠ superseded 2026-09-30: adopted 172.41 kWh/m² and 981,720 t CO₂e over the same 8,139 buildings (153.95 / 881,743 missed district heating and double-counted cooking + refrigeration in 129 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_ten-items-close-2026-09-29.md CP-1). ⚠ superseded 2026-09-30 (three rulings): adopted 171.38 kWh/m² and 1,146,454 t CO₂e over the same 8,139 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_three-rulings-2026-09-30.md CP-B.

#### T04 — OPEN-66: zero-zone IDF no longer flagged success, root cause fixed — completed 2026-09-29

- **Artifacts:** `openubem/idf/builder.py` (+11: `failed_no_zones` return when `idf.idfobjects["ZONE"]` is empty, before Zone.Volume/loads); `openubem/idf/surfaces.py` (+2, root cause, inside `extrude_geometry` only); `tests/test_builder_zero_zone_flag.py` (3 tests); `openubem/outputs/comparisons/open66_zoneless_diagnosis_2026-09-29.csv` (8 rows); debug-references entry (chapter 4).
- **Cause (all 8 identical):** `perimeter_core` buildings; `intersect_match` raised (`NotImplementedError` for 7, `IndexError` for `la_centre/way_425993506`); the `match()`-alone retry then ran `_purge_idf_geometry` (removes every ZONE) and re-extruded only `valid_zones`, which skips the core/perim zones already flagged `extruded`. IDF ended with 0 Zone / 0 surfaces, yet `extruded_zones` stayed non-empty so the builder said `success`. Reproduced locally for all 8 (0 Zone, People counts 33-385 matching the register).
- **Fix (D5, one function, 2 lines):** skip that retry when any zone is already `extruded`, so the existing one_zone_per_floor reroute runs. Regenerated 8/8: zones now 9, 13, 4, 7, 3, 3, 8, 4 (all >= 1), status `success`. The flag check would give `failed_no_zones` if it ever recurs.
- **Deviations:** none from plan. Regeneration used a scratchpad script (not committed) that ran Steps 1-2 per cell from the frozen `evidence/open48_refleet` gpkg, then `BuildingIDF.build` on the 8 rows. Manifest `zoning_strategy` still says `perimeter_core` after this reroute (cosmetic, recorded in debug entry). Adopted 8,139 population unchanged; these 8 were not re-simulated.
- **Test status:** new file 3 passed; the 2 core/perim cases fail without the `surfaces.py` fix (verified by stash) and pass with it. Builder-related batch (11 files): 183 passed, 69 skipped, 2 failed: `test_prep_gate.py::test_flag_default_is_false` (fails identically without my changes, pre-existing) and `test_generation_drop_rescue.py::test_raising_building_isolated_serial` (passes alone and in its own file, 9/9; order-dependent flake in the batch).
- **Notes:** the same purge-then-re-extrude retry also sits in the room_layout path; untouched here (not extruded-flagged, so not affected).
- **Director audit 2026-09-29: PASS.** Diff is builder.py +11 / surfaces.py +2 (13 lines, one function each — inside D5); `surfaces.py` was not in §3 but D5 authorises the root-cause fix, so not a deviation. New test file re-run by the director: 3 passed. Diagnosis CSV has 8 rows + header.

#### T05 — OPEN-38: re-run of the 44 recorded fatals on current production — completed 2026-09-29

- **Artifacts:** `scripts/analysis/open38_rerun_2026-09-29.py` (rebuild + upload; local scratch `%TEMP%/ubem_validation/open38_rerun_2026-09-29/`); `openubem/outputs/comparisons/open38_rerun_2026-09-29.csv` (44 rows: osm_id, cell, mode, old_cause, new_status, task_rc, first Severe line, EUI, n_severe); Speed dir `/speed-scratch/o_iseri/openubem/fleets/open38_rerun_2026-09-29`, job **1401699** (`--array=1-44%32 --time=7-00:00:00`, 44 cases, width 32).
- **Result:** 44 of 44 terminal. 6 completed (la_rural/la_urban/nyc_centre stems: 3 auto, 2 fast_zone, 1 floor; EUI 17.6-23.4 kWh/m2, meter totals over `.eio` area), 37 EnergyPlus fatals, 1 OUT_OF_MEMORY at 6G (`la_centre` auto `way_319507579`, the shadowing-severe building, no `.err` written).
- **Fatal causes (first Severe line):** inside-surface heat-balance divergence 36 of 37 (`Temperature (low) out of bounds` 17, `CalcHeatBalanceInsideSurf ... C` 17, `Temperature (high) out of bounds` 2); 1 non-convex shadowing severe. All 7 `layout_assign` still die in zone `LAUNDRYROOMFLR1` (`CalcHeatBalanceInsideSurf`), unchanged by the volume fix. `floor` 7 of 8 and `fast_zone` 16 of 18 still fatal.
- **Deviations:** (1) The plan calls the 44 "layout_assign fatals"; the source CSV holds 44 fatals across four modes (layout_assign 7, auto 11, fast_zone 18, floor 8). Each was rebuilt in its own recorded mode; case names are `<mode>__<cell>__<stem>` because 15 stems repeat across modes. (2) Rebuild source is the frozen `evidence/open48_refleet/<cell>/01_buildings.gpkg`, classify + enrich on the whole cell, `BuildingIDF(...).build()` per target with the full cell as neighbour context. (3) The default baseline library path no longer exists; the first build silently fell back to no-baseline for the `SmallHotel` rows, so it was discarded and regenerated with `OPENUBEM_BASELINE_IDF_DIR=C:/Users/o_iseri/Desktop/NEXA-desktop/Content/00.BaselineBuildings_NUs_v231` (existing switch, `openubem/config.py:50`); all 44 built `success`. (4) EPWs are the same files the adopted run used (copied from the t07 fleet dir on Speed). (5) EUI for the 6 completions is a meter-total check, not `parse_building()`.
- **Test status:** every one of 44 has a terminal state (sacct: 6 COMPLETED, 37 FAILED = rc 1, 1 OUT_OF_MEMORY); nothing cancelled, no dead-task check needed; other jobs of the account untouched.
- **Notes:** the census hypothesis that writing `Zone.Volume` might cure the divergence is answered: it does not for 37 of 44. For CP-2: the OOM building needs more than 6G.
- **Director audit 2026-09-29: PASS on the task, OPEN-38 does NOT close.** Submission verified in the script: one array `1-44%32`, `--time=7-00:00:00`, `bash -lc` wrapper. CSV re-tallied by the director: 44 rows — 6 completed, 37 fatal, 1 OOM. Deviations 1–3 accepted (1 corrects the plan's wording; 2 is a correct repair; 3 is harmless, the EUIs are not used). `scripts/analysis/open38_rerun_2026-09-29.py` was not in §3 — accepted as the reproducibility record. **CP-2 verdict: current production still kills 38 of 44 (86 %); the item stays open, now as a remedy question (no-HVAC laundry zone + inside-surface divergence), not a measurement question. The ten becomes nine.**

#### T06 — Isolate the scratch helper's working directory — completed 2026-09-29

Artifacts: `scripts/analysis/open56_zone_volume_experiment.py` modified (line 153: `cwd=str(outdir)` added; comment lines 152–155 removed).

Test status: `python -m py_compile` passes; `grep -n "cwd="` confirms line 153; all 5 importers compile.

Notes: No changes to function logic or behavior; only subprocess isolation fixed (EnergyPlus ExpandObjects step now scoped to output directory).

Director audit 2026-09-29: PASS on the fix. Deviation reversed — the executor deleted the four-line `-x` explanation comment (unplanned); the director restored it. Net diff is one line (`cwd=str(outdir)`).

#### T07 — Sweep every artifact quoting the old figure — completed 2026-09-30

**Artifacts.** Marker (verbatim): "⚠ superseded 2026-09-30: adopted 172.41 kWh/m² and 981,720 t CO₂e over the same 8,139 buildings (153.95 / 881,743 missed district heating and double-counted cooking + refrigeration in 129 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_ten-items-close-2026-09-29.md CP-1)." Applied by a scratchpad script (one marker per line, appended; inside table rows before the closing `|`; never inside code fences — 0 such lines): 258 markers in 55 `.md`/`.py` files, then 76 more in the register, the director prompt and this plan after their heads were rewritten by hand. Boards: short HTML marker on 16 + 17 lines; numbers board gained a 2026-09-30 stamp; open-items board gained a new header, counts (3 live / 63 closed / 0 plans / 0 blocking rulings), a 2026-09-30 note, and OPEN-61/63/65 cards marked closed. Republished in place: numbers board version 23, open-items board version 24. Memory: `project_current_baseline.md`, `MEMORY.md`. `open65_reparse_summary_2026-09-29.json` `status` now reads ADOPTED. Register: 3 live / 63 retired / 66 total, next free OPEN-67. ⚠ superseded 2026-09-30 (three rulings): adopted 171.38 kWh/m² and 1,146,454 t CO₂e over the same 8,139 buildings — see docs/docs_DONE/openings/implemenation/previous/PLAN_three-rulings-2026-09-30.md CP-B.

**Deviations.** (1) Done by the director, not a Sonnet dispatch — mechanical, scriptable, and checked in one pass. (2) Found and fixed a pre-existing break on the live numbers board: a raw `"` inside a script string (`WP` row `S03`) stopped the whole task list from rendering (`SyntaxError: Unexpected identifier 'you'`); escaped to `&quot;`, debug-references entry added in §11. (3) `OpenUBEM_debug_References.md` double-count entry: `[OPEN]` dropped (T03 + adoption close it).

**Test status.** Repo-wide scan (`docs/`, `scripts/`, `openubem/`, `tests/`, `.md` + `.py`): **0** unmarked lines across 58 files with hits. Numbers board: 0 unmarked, 16 markers, `node --check` PASS. Open-items board: 0 unmarked, 17 markers, no script. Register state row reads 3 live / 63 retired / 66 total.

**Notes.** Not swept, on purpose: coincidental matching digits in `.geojson`, EU plan `.json`/`.html` and 3D viewer `.html` (coordinates, not the fleet figure); historical data files `t08_restated_fleet_summary.json` and `open61_census_fleet.csv.pre-statusfix`; `scripts/analysis/open65_reparse_2026-09-29.py` (it computes the comparison). `scripts/analysis/fleet06a_campaign_2026-09-18.py` got the marker in its docstring; `py_compile` PASS.

- **Director audit 2026-09-30: PASS. Plan complete (T01–T07, CP-1, CP-2).** Live items left: OPEN-35, OPEN-38, OPEN-62 — each waits on a user ruling, none touches the published figure.
