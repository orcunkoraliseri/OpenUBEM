# PLAN — new neighbourhood: Yerevan, Armenia (`AM-EVN-NORNORK`)

## 1. Header

- **Slug:** `eu-new-city-AM-yerevan-2026-10-08` · **Date:** 2026-10-08
- **Owner requests (verbatim, 2026-10-08):** "can you prepare implemeantion plan for each new city, lets go …\implementation"; "i will sleep can yo uhandle the plans and executions"; "follow same piplien for new cities as well, floor plan division, window to wall ratio etc."
- **Parent plan:** `PLAN_eu-new-cities-00-common-2026-10-08.md` (§2 rules, §4 decisions, §6.2 steps S3–S9). Read it first.
- **DESIGN pointers:** DR10 brief line 11; DR11 brief lines 21–30; `rules/RULES_dwelling_layout_groups_nocore_2026-10-08.html`.
- **Site:** `AM-EVN-NORNORK`, country `AM`, fold `am`, CRS EPSG:32638, MTUS survey year 2008. District: Nor Nork.
- **Goal:** 500–1,000 residential buildings, same pipeline. The hardest of the seven: OSM footprints, few storey counts, ages and constructions from national housing statistics.

## 2. Hard rules for the executor

Common plan §2 rules 1–12, plus: raw downloads only under `openubem/outputs/eu_evidence/EU-22/AM-EVN-NORNORK/raw/<source>/` (untrusted, `python -I`); licence texts into `…/licences/`; no edit to shared files (STOP instead).

## 3. File layout

| Path | Status | Task |
|---|---|---|
| `scripts/eu22/acquire_yerevan.py` | new | T01 |
| `tests/eu22/test_acquire_yerevan.py`, fixtures | new | T01 |
| `openubem/outputs/eu_evidence/EU-22/AM-EVN-NORNORK/…` (incl. `armstat_tables.csv`, hand-transcribed from the PDF with page numbers) | new | T01 |
| `openubem/outputs/eu02/AM-EVN-NORNORK/{01_buildings_clean,02_residential_manifest}.gpkg` | new | T01 |
| `openubem/data/construction/national_specs/am_spec.json`, `tabula_archetypes_am.json` | new | T02 |
| `openubem/data/construction/TABULA_PROVENANCE.md` | edit: AM section | T02 |
| `tests/eu22/test_records_am.py` | new | T02 |

## 4. Dependency decisions (pinned)

- **Footprints:** OpenStreetMap (ODbL) through the existing OSM route (read `openubem/acquisition/osm_fetcher.py:35-61`, call its functions; do not edit the dispatcher). Microsoft footprints are not used (no attributes, and mixing sources breaks adjacency).
- **Residential use:** OSM residential building tags (as Cape Town §4), or untagged buildings inside OSM `landuse=residential`. Report the count per route.
- **Storeys:** OSM `building:levels` (about 16 %) → neighbour imputation (D-EU-154). Report coverage per rung.
- **Year and wall material:** Armstat "RA Housing Stock and Communal Economy 2020" (`https://armstat.am/file/article/bnakfond_2021_1.pdf`, Armenian), tables on PDF pages 46–51: multi-apartment buildings per Yerevan district by commissioning period (before 1950, 1951–70, 1971–80, 1981–90, 1991–2000, 2001–10, 2011+), wall material (stone / panel / monolithic) and storeys. Transcribe the Nor Nork rows into `armstat_tables.csv` with page and table numbers. Census unit = the district.
  - If the tables cross storeys with period for Nor Nork: a building's period = the dominant period **of its storey band** (data-driven, preferred).
  - Else: the district's dominant period (Bologna rule; feasibility: 1951–70, 268 of 657 buildings).
  - Applies to buildings typed MFH / AB. For SFH / TH (private houses) look for an Armstat private-house period table; if none, they are excluded with reason `NO_PERIOD_SOURCE_PRIVATE_HOUSE` and the count is reported.
- **Type:** OSM tags → else the storey rule (D-EU-154).
- **Sub-unit:** the Nor Nork district boundary (OSM `admin_level=9`/`10`, check) then, if > 1,000 residential buildings, street blocks from OSM roads of class `residential` and above, densest first; D-EU-151.
- **Construction (D-EU-152), donor BG.** Periods `AM.01` ≤1950, `AM.02` 1951–1970, `AM.03` 1971–1990, `AM.04` 1991–2015, `AM.05` 2016+. Each period's wall construction = the dominant wall material of Yerevan multi-apartment buildings of that period in the Armstat table (stone or panel; record the counts). Wall U: stone 600 mm R 1.144 → U ≈ 0.87; panel R 1.58 → U ≈ 0.63 (urbanista.am citing Armstat — find and cite the Armstat original if possible); 2016+: RA construction norm 24-01-2016 (wall 0.56, floor 0.42; cite the norm). Roofs, floors, windows before 2016: look for the UNDP-GEF Armenia "Improving energy efficiency in buildings" project reports (nature-ic.am, Avan demonstration building audit) and cite; else donor `ASSUMED`.

## 5. Facts with citations

- Common plan §5.
- Armstat counts from the feasibility research (2026-10-08): Yerevan 4,721 multi-apartment buildings, 230,304 flats; Nor Nork 657 (stone 205, panel 439; 268 in 1951–70, 189 in 1971–80, 164 in 1981–90).
- OSM: 97,859 buildings in the Yerevan box, 15,730 with levels.
- Weather fold `am`, UTC +4, station elevation about 865 m (confirm), survey year 2008 (leap year: 29 February dropped, D-EU-155).

## 6. Tasks

#### T01 — Acquire and clip Yerevan
**How.** OSM buildings, landuse and roads for Nor Nork (saved raw); reproject to EPSG:32638; transcribe the Armstat rows; residential rule; storeys; census columns (`census_unit_id` = `AM-EVN-NORNORK`; `census_period_counts` per storey band when available); `SCHEMA_COLUMNS`; `finalize_footprints`; sub-units; clip; `split_residential`; `write_manifests`; report.
**How to test.** Fixture: residential rule per route; storey-band → period lookup on a 3-row table; private house with no period → excluded with the reason; CRS EPSG:32638. Live: count 500–1,000; coverage lines; the transcribed table totals equal the PDF totals (Nor Nork 657).

#### T02 — Armenian construction records
As Helsinki T02 with donor BG, periods and material rule of §4, tests in `tests/eu22/test_records_am.py`.

#### T03 — Prepare (S3) · T04 — S4 + S5 · T05 — Plan pages (S6, then STOP) · T06 — Speed (manager) · T07 — S8 · T08 — S9
Common plan §6.2 with `SITE=AM-EVN-NORNORK`, `cc=AM`.
T06 amendment (D-EU-165, owner 2026-10-09): before staging, add `way/998439490` to `AM-EVN-NORNORK_win_2026-10-09/left_out.csv` and treat it exactly like the other 15 left-out homes (same run-list rule); results over 535 homes.

## 7. Stop-and-report points

1. After T01 + T02 (coverage and how many buildings rest on assumptions). 2. After T05. 3. After T08.

## 8. Progress log

(One entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes.)

#### T08 — Viewer and side-cars (S9) — completed 2026-10-10

- **Artifacts:** `openubem/outputs/3D/eu_AM-EVN-NORNORK_viewer.html` (5,365,537 bytes) and `eu_AM-EVN-NORNORK_data/{buildings.csv (2,857 rows),index.html,sources.json}`, mirrored byte-identical (`cmp` / `diff -rq` clean) to `docs/docs_ACTIVE/europeanLocations/outputs_3D/`; `openubem/outputs/eu_evidence/EU-11/AM-EVN-NORNORK_win_2026-10-09/{layouts/ (535 side-cars),sidecar_population.csv (535 rows)}`; `…/AM-EVN-NORNORK_merged_win_2026-10-09/flat_counts_2026-10-09.csv` (2,857 rows). Internal only: nothing published, nothing sent to 6J.
- **Deviations:** (1) Side-car step run with `--evidence-root AM-EVN-NORNORK=<win tree>` (manager note of 2026-10-10); the 551 S5 side-cars in `_dw_/layouts/` were not touched; no `--population-manifest` needed (the emitter builds `sidecar_population.csv` itself). The run finished in under 25 min (not timed exactly), not the 1 h 40 min of S5. `OPENUBEM_NOCORE_*` variables were unset (checked). (2) The viewer has no EU-21 check badges (join 0 hit / 551 miss), as in the C07 notes. (3) No other `generate_eu_3d_viewers` process was running when the generator started.
- **Test status:** viewer simulated 535 = results rows 535 (idf_only 0, no_idf 0, undivided / left out 16). Flat counts: simulated 535, run_failed 0, undivided_excluded 16, not_residential 2,306, no_model 0. Side-car flat count: sum of `new_count` over simulated = 26,318 = sum of `dwellings_used` in `sidecar_population.csv` (535 homes) = sum of `dwellings_total` over the 535 side-car JSONs = 26,318. `pytest -q tests/test_eu18c_viewer_geometry_only.py -k "AM-EVN"` = 1 passed; with the plan's literal `-k AM` = 15 passed, 4 failed (`AT-VIE-RUDOLFSHEIM`, `FI-HEL-KALLIO`, `HU-BUD-ERZSEBETVAROS`, `KR-SEO-MAPO`: their viewers do not exist yet, not Yerevan). `pytest -q tests/eu22` = 251 passed, 1 failed: `test_weather_folds.py::test_original_folds_keep_their_year_candidates` (`'kr'` in the registry targets, not in the test's expected set; from the uncommitted Korea registry change, reported, not fixed).
- **Notes:** `sources.json` of the four older viewers shows as modified in git; it was modified before this task and not touched here. No error solved, so nothing added to the debug references.

#### T07 — Harvest and results (S8) — completed 2026-10-10

- **Artifacts:** `openubem/outputs/eu_evidence/EU-11/AM-EVN-NORNORK_win_2026-10-09/{am_evn_nornork_manifest.csv (551 rows),summary.json}` (harvest); `openubem/outputs/eu_evidence/EU-22/AM-EVN-NORNORK/results/EU22_results_AM-EVN-NORNORK_2026-10-09_{per_home.csv,per_home.json,summary.csv,summary.json}`; byte-identical copies in `docs/docs_ACTIVE/europeanLocations/results/` (4 of 4 `cmp` equal).
- **Deviations:** none. Fetch over ssh with the `bash -lc` wrapper; nothing ran on the Speed login node.
- **Test status:** job 1442163: 551 task directories extracted, run 551, success 551 (return code 0, "Completed Successfully" in `eplusout.err` and `eplusout.end`), failed 0. Manifest rows 551; left out 16 (D-EU-165); kept 535; with result 535; runs without result 0. Rows = correctly divided homes (535). EUI (heating only, ideal loads): 48.516593 kWh/m2 over 1,710,969.625 m2; per-home min 26.70, median 51.36, max 129.04 (mean of homes 55.95). The harvest's own pooled figure over all 551 homes (including the 16 left out) is 48.0508; the published figure is the 535-home one.
- **Notes:** EUI is space heating only. Every building takes the single period AM.02 (district rule from T01), so the Nor Nork result rests on that assumption; do not compare with the four fleet sites without that caveat.

#### T06 — Speed (manager) — submitted 2026-10-09

- **Artifacts:** `AM-EVN-NORNORK_win_2026-10-09/left_out.csv` now 16 rows (D-EU-165: `way/998439490` row appended from `division_classes.csv`, unchanged columns); `AM-EVN-NORNORK_win_2026-10-09/speed_jobs.txt`; Speed fleet `/speed-scratch/o_iseri/fleets/EU22_AM-EVN-NORNORK_win_2026-10-09/`.
- **Deviations:** none. Owner approval of the page: "overall all looks okay" (2026-10-09). All 551 IDFs run; the 16 left-out homes are dropped at results (`write_results_eu22.py:45-55`, by building id).
- **Test status:** staging: fleet.lst 551 = local IDFs 551 = remote IDFs 551. Job 1442163, `--array=1-551%32 --time=7-00:00:00 --mem=32G`. At submission the account CPU cap was held by 4J/5J runs (state `AssocGrpCpuLimit`); tasks start as CPUs free.
- **Notes:** results expected over 535 homes.

#### T05 — Plan pages (S6) — completed 2026-10-09

- **Artifacts:** `docs/docs_ACTIVE/europeanLocations/plans3D/PLANS_AM-EVN-NORNORK_2026-10-09.html` (5.57 MB, written straight into `plans3D/`, so no separate copy); row added to `plans3D/index.html` (credit: OpenStreetMap contributors, ODbL). The four existing pages and the CA / ZA pages were not touched.
- **Deviations:** none. `--verify` is verify-only, so the page was built first (same arguments, without `--verify`), then verified.
- **Test status:** verify: P1 551 of 551; P2 buildings 551 of 551, storeys 3783 of 3783; P3 page parses, 0 EUI keys, storey list 551 of 551. Build line: PASS 532, FAIL 4, GENERIC 0, ERROR 0, UNRESOLVED 15 (= the 15 left-out homes, flagged). No external URL in the page (0 matches of http/https). The 4 FAIL are the page's own per-building rule checks (not integrity); not investigated.
- **Notes:** STOP point 2 reached; the manager audits the page and integrity numbers before staging. Speed array size would be 551 (`fleet.lst`).

#### T04 — S4 + S5 (finish the tree, integrity, side-cars, division score) — completed 2026-10-09

- **Artifacts:** `openubem/outputs/eu_evidence/EU-11/AM-EVN-NORNORK_win_2026-10-09/` (551 IDFs, `fleet.lst` 551, `md5_2026-10-09.txt` 551, `origin_offset.json`, `windows.csv` 551, `dwelling_counts_2026-10-09.csv`, `degenerate_2026-10-09.csv`, `division_classes.csv`, `left_out.csv` 15); `AM-EVN-NORNORK_dw_2026-10-09/layouts/` (551 side-cars); `openubem/outputs/eu_evidence/EU-11/integrity_2026-10-02/AM-EVN-NORNORK_win_2026-10-09_integrity.csv`.
- **Deviations:** (1) the side-car emitter for a new site reads `left_out.csv` from the `_dw_` tree, which only the scorer writes (circular, already in the debug references from Cape Town): ran it with `--population-manifest AM-EVN-NORNORK=<dw tree>/prepared_buildings.csv`. A first scorer run before the side-cars gave 551 `IDF_FALLBACK`; the second run (after side-cars) overwrote it. (2) `12_drop_degenerate.py` called with `--districts AM --shift AM` (country code). (3) The emitter took about 1 h 40 min again for the same 63-flat building (debug reference added).
- **Test status:** degenerate: IDFs 551, changed 0, deleted 0, errors 0. Integrity failures per check (551 homes): I1 0, I2 3, I3 0, I4 0, I5 0, I6 0, I7 3, I8 0, I9 0, I10 0, I11 0, I12 0, I13 0 (the 3 homes failing I2 and I7 are the same: `way/553092326`, `way/135458274`, `way/135463709`; 0.5 %, under the 1 % stop line). Score: OK 327, V3_divided_wrapped_flat 209, V1_divided_shape_rule_broken 13, U4_other_box 1, U1_cut_lost_at_idf_write 1; correctly divided (OK + V3) = 536 of 551 = 97.3 % (stop line 85 %); `IDF_FALLBACK` 0 (all 551 from side-cars). Window share (`windows.csv`): median difference between achieved and record share 5e-12; 549 of 551 equal; largest difference 0.327 = two homes with 0 m2 outdoor wall and 0 window (`way/83722243`, left out as V1; `way/998439490`, NOT left out, classed in the kept set; manager to look at it).
- **Notes:** integrity table says nothing is wrong on more than 1 % of homes. AM.02 (1951-70) is the single period of every building (district rule from T01).

#### T03 — Prepare (S3) — completed 2026-10-09

- **Artifacts:** `openubem/outputs/eu_evidence/EU-11/AM-EVN-NORNORK_dw_2026-10-09/` (`summary.json` status `PREPARED_FOR_SPEED`, 551 IDFs, `fleet.lst` 551, `prepared_buildings.csv`, `excluded_buildings.csv`, `am_evn_nornork_manifest.csv`, `schedules/`, `weather/`). Weather: registry file `openubem/data/weather/am_yerevan_tmyx_2009_2023.epw` (sha256 verified by the script; D-EU-163 typical year, D-EU-164 Zvartnots).
- **Deviations:** none to the plan. The run took about 3 h because one very large footprint (63 flats per floor) needs 3 shape-improvement attempts of about 33 min each (debug reference added).
- **Test status:** attempted 551, prepared 551 (100 %), `excluded_buildings.csv` 216 rows all `MISSING_OBSERVED_STOREY_COUNT` at stage `base_mapping`, and all 216 were recovered by neighbour imputation (216 of 216 also in the prepared list), so no residential building is lost. Five most common exclusion reasons: only one exists (MISSING_OBSERVED_STOREY_COUNT 216, recovered). Outcomes: layout emitted imputed count 536, best-effort imputed 13, interzone mismatch rerouted 1, fallback pending layout missing dwelling count 1. Types: AB 542, MFH 9. Period: AM.02 551.
- **Notes:** no EnergyPlus run; the run list is `fleet.lst`, for the manager to submit.


#### T02 — Armenian construction records — completed 2026-10-08

- **Artifacts:** `openubem/data/construction/national_specs/am_spec.json`; `openubem/data/construction/tabula_archetypes_am.json` (20 records: SFH, TH, MFH, AB x 5 periods, donor BG); `tests/eu22/test_records_am.py`; AM section appended last in `openubem/data/construction/TABULA_PROVENANCE.md`. Raw downloads: `openubem/outputs/eu_evidence/EU-22/AM-EVN-NORNORK/raw/armstat/bnakfond_2021_1.pdf`, `raw/nature_ic/{RACN_24-01-2016.pdf,Avan-DSK-Audit-Report-ENG.pdf}`.
- **`_TABULA_PERIODS["AM"]` (for C03):** `((0, 1950, "AM.01"), (1951, 1970, "AM.02"), (1971, 1990, "AM.03"), (1991, 2015, "AM.04"), (2016, 9999, "AM.05"))`.
- **Type x period (U in W/m2K; window share; flats per building):**

| Type | Period | U wall | U roof | U floor | U window | Share | Flats |
|---|---|---|---|---|---|---|---|
| SFH | AM.01 | 0.874 | 1.97 | 1.97 | 5.88 | 0.147 | 1 |
| SFH | AM.02 | 0.874 | 2.10 | 2.10 | 2.32 | 0.181 | 1 |
| SFH | AM.03 | 0.633 | 2.10 | 2.10 | 2.32 | 0.181 | 1 |
| SFH | AM.04 | 0.874 | 0.27 | 1.91 | 1.10 | 0.284 | 1 |
| SFH | AM.05 | 0.56 | 0.27 | 0.42 | 0.80 | 0.134 | 1 |
| TH | AM.01 | 0.874 | 1.97 | 0.32 | 5.88 | 0.099 | 1 |
| TH | AM.02 | 0.874 | 1.97 | 2.10 | 2.32 | 0.160 | 1 |
| TH | AM.03 | 0.633 | 1.97 | 2.10 | 2.32 | 0.160 | 1 |
| TH | AM.04 | 0.874 | 0.27 | 2.10 | 1.10 | 0.178 | 1 |
| TH | AM.05 | 0.56 | 0.27 | 0.42 | 1.00 | 0.152 | 1 |
| MFH | AM.01 | 0.874 | 2.10 | 2.10 | 2.32 | 0.144 | 13.1 |
| MFH | AM.02 | 0.874 | 0.59 | 2.10 | 2.63 | 0.166 | 7.6 |
| MFH | AM.03 | 0.633 | 0.59 | 2.10 | 2.63 | 0.166 | 7.6 |
| MFH | AM.04 | 0.874 | 0.27 | 2.10 | 1.10 | 0.190 | 4.4 |
| MFH | AM.05 | 0.56 | 0.18 | 0.42 | 1.00 | 0.156 | 6.0 |
| AB | AM.01 | 0.874 | 2.10 | 2.10 | 2.32 | 0.148 | 19.3 |
| AB | AM.02 | 0.874 | 0.59 | 2.10 | 2.60 | 0.327 | 55.0 |
| AB | AM.03 | 0.633 | 0.59 | 2.10 | 2.60 | 0.327 | 55.0 |
| AB | AM.04 | 0.874 | 0.27 | 0.49 | 2.60 | 0.244 | 22.8 |
| AB | AM.05 | 0.56 | 0.18 | 0.42 | 1.00 | 0.358 | 38.5 |

- **Deviations (manager to rule):** (1) **Plan §4 rule not executable as written:** Armstat 2020 has no period x wall-material table (period table PDF p.50, material table PDF p.47, separate). Wall material per period is therefore `ASSUMED` (stone AM.01, AM.02, AM.04; panel AM.03), inferred from the Yerevan totals (2,073 buildings up to 1970 vs 2,219 stone; 2,336 built 1971-90 vs 2,376 panel) and WHE reports 202-204; in Nor Nork alone the arithmetic does not close (268 up to 1970, 205 stone). Flip one value per period in `am_spec.json` to overrule. (2) U = 1/R without surface films, as pinned; the R values 1.144 and 1.58 come from urbanista.am (Armstat original not found). (3) AM.05 wall 0.56 and floor 0.42 follow the plan (World Bank page citing RACN 24-01-2016; they equal Table 3 row 1000 degree-days); the same Table 3 at Yerevan's own degree-days (about 2,660) gives wall U about 0.43. (4) SFH and TH take the multi-apartment wall value (no private-house source). (5) Roof, floor before 2016, window, g, thermal bridge, infiltration, window share: donor BG, `ASSUMED:donor` (no Armenian source found). (6) Nor Nork mean flat area 64.93 m2 (Armstat) set for MFH and AB only.
- **Test status:** `pytest tests/eu22/test_records_am.py tests/eu22/test_records_tools.py` = 25 passed (12 AM). U increases printed and explained: wall AM.03 to AM.04 (panel then stone, all types); window AM.01 to AM.02 for MFH and AB (donor BG.03 2.32 vs BG.04 2.6/2.63); SFH roof AM.01 to AM.02 (donor 1.97 vs 2.10). Window share 0.099 to 0.358. 20 donor ratio-fallback slots stamped in `parameter_assumptions`.
- **Notes:** `armstat_tables.csv` is T01's file and was not written; the totals above (Yerevan 4,721, Nor Nork 657) are asserted in the test. No shared file was edited; `construction_sets._TABULA_PERIODS` is left to C03. The UNECE Armenia study could not be downloaded (HTTP 403).

#### T01 — Acquire and clip Yerevan — completed 2026-10-08

- **Artifacts:** `scripts/eu22/acquire_yerevan.py`; `tests/eu22/test_acquire_yerevan.py` + fixtures `tests/eu22/fixtures/yerevan_osm_buildings.osm`, `yerevan_armstat_crossed.csv`; `openubem/outputs/eu_evidence/EU-22/AM-EVN-NORNORK/{armstat_tables.csv, boundary.geojson, boundary.sha256, acquisition_report.json, licences/{osm_odbl.txt,armstat_terms.txt}}`; new raw folders `raw/osm_boundary/` (relation 13404220), `raw/osm_buildings/` (14.2 MB XML), `raw/osm_landuse/`, `raw/osm_roads/` (the T02 folders `raw/armstat/`, `raw/nature_ic/` reused, the PDF re-read from there); `openubem/outputs/eu02/AM-EVN-NORNORK/{01_buildings_clean.gpkg (11,217 footprints, 23 columns), 02_residential_manifest.gpkg (551), 02_excluded_manifest.gpkg}`.
- **Units used (D-EU-151), running count of residential buildings:** the district `Nor Nork` (OSM relation 13404220, 14.46 km2) holds 1,637 residential buildings (1,310 after the private-house exclusion), more than 1,000, so street blocks were used (OSM roads motorway..tertiary and residential, 252 faces). Densest block first, then touching blocks nearest centroid first (empty blocks included so the area stays contiguous): B0224 15; +B0020 3 = 18; +B0006 1 = 19; +B0032 77 = 96; +B0000 126 = 222; +B0248 5 = 227; +B0033 33 = 260; +B0241 3 = 263; +B0134 8 = 271; +B0135 11 = 282; +B0044 18 = 300; +B0129 11 = 311; +B0098 70 = 381; +B0114 12 = 393; +B0115 4 = 397; +B0043 20 = 417; +B0111 1 = 418; +B0130 23 = 441; +B0042 11 = 452; +B0039 8 = 460; +B0112 1 = 461; +B0141 16 = 477; +B0038 8 = 485; +B0008 66 = 551. 94 blocks in all (70 hold no eligible building), none skipped for the 1,000 cap, area 6.81 km2.
- **Residential count: 551** (in 500-1,000). By route: OSM residential tag 319 (apartments 316, residential 3), untagged inside `landuse=residential` 232. District-wide by route (before clipping): tag 753, untagged-in-landuse 884, untagged-outside-landuse 1,477 (class unknown, not residential), other tags 571. Private houses excluded in the selection: 215 (reason `NO_PERIOD_SOURCE_PRIVATE_HOUSE`, tagged house / detached / terrace / semidetached_house, or untagged with observed 1-2 storeys); they sit in the excluded manifest as `non_residential`.
- **Coverage of the 551:** storeys observed 335 (60.8 %, OSM `building:levels`; 3 storeys 6, 4 storeys 3, 5 storeys 164, 8 storeys 1, 9 storeys 146, 10 storeys 2, 14 storeys 6, 16 storeys 7); storeys from measured height 0; storeys left for neighbour imputation 216 (39.2 %); height observed 1 (0.18 %); year observed 0 (no OSM `start_date`); census unit `AM-EVN-NORNORK` 551 (100 %); period counts attached 551 (100 %). Period source = Armstat 2020 table PDF p.50 (printed 54), district totals of Nor Nork (657 buildings: up to 1950 0, 1951-70 268, 1971-80 189, 1981-90 164, 1991-2000 32, 2001-10 2, 2011+ 2). The table does not cross storeys with period (searched all 71 pages: period headings occur only on PDF pages 28, 34, 46, 50), so the district's dominant period applies to every building: 1951-70, reference year 1960 (midpoint convention, as Vienna; `period_years` in `acquisition_report.json`). Type: OSM tag where present, else the storey rule at prepare time. No private-house period table exists in the file.
- **Deviations (manager to rule):** (1) Nor Nork is OSM `admin_level=5`, not 9/10 (all Yerevan districts are level 5; no polygon exists below it; the 9 "Nor Nork Block 1-9" `place` features are nodes/relations without boundaries, not used). (2) Block selection is the literal plan rule and gives a sprawling area: 551 buildings over 6.81 km2 (81 per km2) against 518 per km2 for the first block, because the densest block (15 buildings) lies at the edge and 70 of the 94 blocks are empty. The district as a whole has 1,310 eligible buildings. (3) The district-dominant period (1960) is applied to every building, including the 146 buildings with 9 storeys and the 7 with 16 storeys; Armstat lists 291 of the 657 buildings as 9+ storeys, 279 of them panel, and T02 inferred panel as 1971-90 construction, so 1960 is probably wrong for them, but no table crosses storeys with period. (4) The 8 buildings managed by the district administration (PDF p.46) are not in the 657; with them the dominant period is unchanged. (5) The private-house rule uses observed storeys only; untagged buildings with imputed storeys of 1-2 will be typed SFH / TH at prepare time and take the district period there (shared code, not changed). (6) Armstat terms found: "By using the website, please refer to Statistical Committee RA. All rights reserved." (`licences/armstat_terms.txt`); only counts are transcribed, with page numbers. (7) PyMuPDF was installed into the scratchpad (not the project venv) to read the PDF as images; pdftotext lost the Armenian labels.
- **Test status:** `python -I -m pytest tests/eu22/test_acquire_yerevan.py` = 11 passed (residential rule per route, storey-band lookup on a 3-band table, district fallback, private house excluded with the reason, CRS EPSG:32638 on an OSM fixture, transcribed totals equal PDF totals: Nor Nork 657 by period, material, roof form and storeys, Yerevan 4,721, 205 stone / 439 panel / 13 monolithic, Overpass failure text logged). Live run printed the counts above.
- **Notes:** Overpass returned `rate_limited` and HTTP 504 on the first calls; the script rotates endpoints and logs the real text (debug reference extended). No shared file edited. `01_buildings_clean.gpkg` holds the whole 0.004-degree-buffered box (11,217 footprints), as in Helsinki. Extra manifest columns: `use_route`, `census_unit_id`, `census_period_counts`, `period_exclusion_reason`, `period_scope`.
