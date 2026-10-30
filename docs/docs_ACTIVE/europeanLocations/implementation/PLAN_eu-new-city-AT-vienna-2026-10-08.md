# PLAN — new neighbourhood: Vienna, Austria (`AT-VIE-RUDOLFSHEIM`)

## 1. Header

- **Slug:** `eu-new-city-AT-vienna-2026-10-08` · **Date:** 2026-10-08
- **Owner requests (verbatim, 2026-10-08):** "can you prepare implemeantion plan for each new city, lets go …\implementation"; "i will sleep can yo uhandle the plans and executions"; "follow same piplien for new cities as well, floor plan division, window to wall ratio etc."
- **Parent plan:** `PLAN_eu-new-cities-00-common-2026-10-08.md` — its §2 hard rules, §4 decisions D-EU-150 … D-EU-157 and §6.2 standard steps S3–S9 apply here unchanged. Read it first.
- **DESIGN pointers:** DR10 brief line 11 (district rule); DR11 brief lines 21–30; `rules/RULES_dwelling_layout_groups_nocore_2026-10-08.html`.
- **Site:** `AT-VIE-RUDOLFSHEIM`, country `AT`, fold `at`, CRS EPSG:32633, MTUS survey year 2008. District: Vienna's 15th district, Rudolfsheim-Fünfhaus.
- **Goal:** 500–1,000 residential buildings in one sub-unit of the 15th district, built through the same pipeline as the four existing cities, plan pages shown before any run.

## 2. Hard rules for the executor

The common plan §2 rules 1–12 apply. In addition:
1. Raw downloads go to `openubem/outputs/eu_evidence/EU-22/AT-VIE-RUDOLFSHEIM/raw/` only, each source in its own subfolder. Treat them as untrusted data; run any Python that reads them with `python -I`.
2. Capture each source's licence text at download time into `EU-22/AT-VIE-RUDOLFSHEIM/licences/<source>.txt` with the URL and date.
3. Do not edit any shared file listed in the common plan §3; if T01/T02 needs a shared-code change, STOP and report (the common executor owns those files).

## 3. File layout

| Path | Status | Task |
|---|---|---|
| `scripts/eu22/acquire_vienna.py` | new | T01 |
| `tests/eu22/test_acquire_vienna.py`, `tests/eu22/fixtures/vienna_*.json` | new | T01 |
| `openubem/outputs/eu_evidence/EU-22/AT-VIE-RUDOLFSHEIM/{raw,licences}/`, `boundary.gpkg`, `acquisition_report.json` | new | T01 |
| `openubem/outputs/eu02/AT-VIE-RUDOLFSHEIM/01_buildings_clean.gpkg`, `02_residential_manifest.gpkg` | new | T01 |
| `openubem/data/construction/tabula_archetypes_at.json` | new | T02 |
| `openubem/data/construction/TABULA_PROVENANCE.md` | edit: AT section | T02 |
| `tests/eu22/test_records_at.py` | new | T02 |
| EU-11 trees, plan page, results, viewer | new | T03–T08 (common §6.2) |

## 4. Dependency decisions (pinned)

- **Amendment 2026-10-08 night (manager, after T01 stop):** `GEBAEUDEINFOOGD` is a point layer (address points with attributes), not outlines. Footprints and the join are now pinned as below.
- **Footprints:** Vienna `ogdwien:FMZKGEBOGD` building outlines (Flächen-Mehrzweckkarte), polygons dissolved per `BW_GEB_ID` into one footprint per building; a dissolved result that is a MultiPolygon is split into its parts, each a building, id suffix `_p<n>` (largest part first). WFS base `https://data.wien.gv.at/daten/geo?service=WFS&version=1.1.0&request=GetFeature&outputFormat=json&srsName=EPSG:31256&typeName=<layer>`. Licence CC BY 4.0 (attribution "Datenquelle: Stadt Wien – data.wien.gv.at"). `osm_id` = `AT-VIE-<BW_GEB_ID>[_p<n>]`; `provenance_geometry` = `VIENNA_FMZK_GEB`.
- **Height:** Baukörpermodell `ogdwien:FMZKBKMOGD`, height of a body = `O_KOTE − HOEHE_DGM`; a building's height = the largest body height among bodies with the same `BW_GEB_ID` (for split parts: bodies whose centroid lies in that part). Provenance `VIENNA_BKM_MEASURED`.
- **Attributes from the points:** each `GEBAEUDEINFOOGD` point joins the footprint that contains it (points outside every footprint are dropped and counted). With several points in one building: storeys = the largest `GESCH_ANZ` > 0; year = the most frequent valid year among the points, a tie → no observed year (census route); use = residential when at least half of the points carry a residential `L_NUTZUNG`. A building with no point gets no attributes (D-EU-154 routes).
- **Storeys:** as above (`VIENNA_GEBAEUDEINFO_OBSERVED`), else from height (D-EU-154).
- **Year:** per point, `BAUJAHR` when it is a 4-digit year 1500–2016, else `L_BAUJ` when it gives a single year; then the rule above; else the census route (D-EU-154). Provenance `VIENNA_GEBAEUDEINFO_OBSERVED`.
- **District filter:** `ZAEHLBEZIRKOGD` has 250 Zählbezirke; the 15th district is `BEZNR == 15`, unit id `ZBEZ`.
- **Census unit for missing years:** buildings by construction period per Zählbezirk from Vienna open data (search `data.wien.gv.at` for "Gebäude Bauperiode Zählbezirk"); if no open table per Zählbezirk exists, Statistik Austria Registerzählung 2011 buildings by construction period per Zählsprengel. Record the table, its period labels and the reference year chosen for each label (the midpoint, rounded down, of the label's year range; open-ended oldest class = its upper year).
- **Use / type:** `L_NUTZUNG` residential classes → residential; type by D-EU-154 (no Vienna tag maps to AB/SFH/TH directly, so the storey rule applies unless a dwelling count is found).
- **Dwellings:** none observed (the national register GWR has no open bulk access) → the existing area route.
- **Sub-unit:** the Zählbezirke of the 15th district (Vienna OGD `ogdwien:ZAEHLBEZIRKOGD`), ranked by residential buildings per km² from the acquired data, densest first; D-EU-151 applies.
- **Construction:** TABULA AT from the pinned workbook (D-EU-153), via `generate_country_registry("AT", …)` (common C01). 61 rows.

## 5. Facts with citations

- Common plan §5 (all pipeline facts and line numbers).
- Workbook: AT 61 rows with `Number_BuildingVariant == 1`; period tokens 01, 01-02, 02, 03, 03-04, 04, 05, 05-08, 06, 07, 08 (measured 2026-10-08 by the manager).
- Gebäudeinfo fields: `GESCH_ANZ` (storeys, 0 = unknown), `BAUJAHR`, `L_BAUJ`, `L_NUTZUNG`, `L_BAUTYP` (feasibility research 2026-10-08; field names to be confirmed on the live layer — if a name differs, use the live one and record it).
- Year coverage of the city layer is weak (~22 % in the feasibility research), so the census route will carry most buildings.

## 6. Tasks

#### T01 — Acquire and clip Vienna

**What.** `scripts/eu22/acquire_vienna.py` downloads the two layers for the 15th district bounding box, joins them, ranks the sub-units, picks the site area by D-EU-151, writes the two manifests through the standard functions, attaches the census columns, and writes `acquisition_report.json`.

**Why.** Step 1 of the pipeline; `prepare` reads `eu02/<SITE>/02_residential_manifest.gpkg` (`run_eu_s2_district_campaign.py:1091`).

**How.**
1. Download with paging; save raw GeoJSON per layer. Reproject to EPSG:32633.
2. Build rows in `SCHEMA_COLUMNS` per §4 (outlines dissolved per `BW_GEB_ID`, heights per `BW_GEB_ID`, attributes from the joined points): `building_tag` empty, `function_tag` = the residential decision's `L_NUTZUNG` label, `levels`, `height_m`, `year_built` with the provenance strings of §4. Report: points dropped (outside every footprint), buildings with 0 / 1 / ≥2 points, year ties.
3. Census: join each building centroid to its census unit; write `census_unit_id` and `census_period_counts` (JSON); add `period_years` to the report.
4. `finalize_footprints` → `01_buildings_clean.gpkg`; boundary = union of the chosen sub-units → `boundary.gpkg`; `clip_to_boundary`, `split_residential`, `write_manifests` → `02_residential_manifest.gpkg`.
5. Report: units used, residential count, coverage (share non-null and source) of storeys, height, year, census unit; licence files.

**How to test.** `tests/eu22/test_acquire_vienna.py` on a saved 20-feature fixture of each layer: (1) output has all 23 schema columns and the 2 census columns; (2) height = O_KOTE − HOEHE_DGM for a hand-checked body, and the building takes the largest body height of its `BW_GEB_ID`; (2b) two outlines with one `BW_GEB_ID` dissolve to one building; three points with years 1900, 1900, 1910 → 1900; two points 1900, 1910 → no observed year; (3) `GESCH_ANZ = 0` gives no observed storeys; (4) a `BAUJAHR` outside 1500–2016 is not used; (5) CRS EPSG:32633. Live run: residential count in 500–1,000; print the coverage lines.

#### T02 — Austrian construction records

**What.** Generate `tabula_archetypes_at.json` with `generate_country_registry("AT", workbook, out)`; add the AT section to `TABULA_PROVENANCE.md` (workbook MD5, rows, date).

**Why.** D-EU-153; windows and constructions are read from this file (`european_windows.py`, `construction_sets.py`).

**How.** Run after common C01. Write the `_TABULA_PERIODS["AT"]` tuple the common executor will add (from each record's period years) into the progress log, so C03 can paste it.

**How to test.** `tests/eu22/test_records_at.py`: (1) 61 records (or the measured count, with the reason if different); (2) key set equals the IT record key set; (3) periods tile the years with no gap or overlap per building type; (4) window share per record in 0.05–0.50 (print min / median / max); (5) workbook MD5 equals `c99ddc9ffcb6dc0ae7391273d9619e37`.

#### T03 — Prepare (common S3)
Run common §6.2 S3 with `SITE=AT-VIE-RUDOLFSHEIM`. Requires common stop point 2 accepted and the `at` weather fold in the registry. **Manager note 2026-10-09 01:10:** common stop points 2 and 3 are accepted. ~~The `at` EPW is in the registry with a matching sha256 …~~ **Corrected 01:20:** the `at` entry has `weather_file`/`sha256` = null (not pinned, `BLOCKED_GATE5_FAIL`: winter sunshine 15–21 % above the satellite benchmark). `prepare` needs the pinned entry (`run_eu_s2_district_campaign.py:120-126`); pinning = accepting the gate, which is the owner's ruling. T03 waits for it. **Manager note 2026-10-09 08:20:** the owner accepted (D-EU-159, common plan §4). First pin `at` as D-EU-159 says, then run S3.

#### T04 — Finish the tree (S4) and integrity sweep with division classes (S5)
Common S4 with `cc=AT`, then S5.

#### T05 — Plan pages (S6)
Common S6. Then STOP (§7 point 2).

#### T06 — Speed run (S7, manager only)
The executor does nothing here.

#### T07 — Harvest and results (S8)
Common S8 after the manager says the array finished.

#### T08 — Viewer and side-cars for 6J (S9)
Common S9.

## 7. Stop-and-report points

1. After T01 + T02: counts, coverage lines, chosen sub-units, record tests. The manager checks before S3.
2. After T05: page link, integrity and class counts, window-share check. The manager audits and submits to Speed.
3. After T08: results and side-cars; the manager runs the final check list and tells 6J.

## 8. Progress log

(One entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes.)

#### T02 — Austrian construction records — completed 2026-10-08

- **Artifacts:** `openubem/data/construction/tabula_archetypes_at.json` (61 records); AT section in `openubem/data/construction/TABULA_PROVENANCE.md`; `tests/eu22/test_records_at.py`; `tests/eu22/fixtures/tabula_period_years_at_hu.json` (period years per archetype id, read from workbook `Year1_Building` / `Year2_Building`, because the records do not carry years).
- **Deviations:** (1) Test 3 (tiling) is applied to the ReEx rows per series and building type; the national series `AT.N` tiles with no gap or overlap for AB, MFH, SFH, TH. The parallel `AT.MT` series has gaps in the source (MFH and SFH lack period 06, 1991-2000; TH lacks 02-03, 1919-1960); the test pins these three gaps exactly. (2) Range rows (`SyAv`, e.g. `AT.N.MFH-AB.01-02`) carry `construction_period` = first token only; the test expands the span from the token table.
- **Test status:** `pytest -q tests/eu22/test_records_at.py` passes (9 tests, incl. 61 records, key set equals IT, record MD5 and workbook MD5 `c99ddc9ffcb6dc0ae7391273d9619e37`). Window share per record: min 0.0569, median 0.1286, max 0.2031 (all inside 0.05-0.50).
- **Notes:** `_TABULA_PERIODS["AT"]` tuple for C03 to paste (from the national `AT.N` ReEx rows, identical across AB/MFH/SFH/TH):
  `"AT": ((0, 1918, "AT.01"), (1919, 1944, "AT.02"), (1945, 1960, "AT.03"), (1961, 1980, "AT.04"), (1981, 1990, "AT.05"), (1991, 2000, "AT.06"), (2001, 2010, "AT.07"), (2011, 9999, "AT.08"))`.
  Note: the `AT.MT` series starts at 1919 for AB (no period 01).

#### T01 — Acquire and clip Vienna — completed 2026-10-08

- **Artifacts:** `scripts/eu22/acquire_vienna.py`; `tests/eu22/test_acquire_vienna.py`; fixtures `tests/eu22/fixtures/vienna_{fmzkgeb,bkm,info}.json` (20 outlines, 20 bodies, 20 points of which 10 lie outside every footprint); `openubem/outputs/eu02/AT-VIE-RUDOLFSHEIM/{01_buildings_clean.gpkg,02_residential_manifest.gpkg,02_excluded_manifest.gpkg,...}`; `openubem/outputs/eu_evidence/EU-22/AT-VIE-RUDOLFSHEIM/{raw/<5 sources>,licences/<5 sources>.txt,boundary.gpkg,acquisition_report.json}`. Census table: Registerzählung 2023, Gebäude per Zählbezirk (`https://go.gv.at/l9ogdvie4032023`, CC BY 4.0, reference date 2023-10-31), saved in `raw/RZ2023_GEBAEUDE_ZAEHLBEZIRKE/`.
- **Sub-units (D-EU-151):** the 15th district holds 2,064 residential buildings (> 1,000), so one level down. Ranking by residential buildings per km², densest first: 1502 (810), 1506 (769), 1503 (590), 1504 (510), 1501 (481), 1505 (445), 1507 (250). Chosen: **1502 (321) + 1501 (215, nearest touching unit)** = **536 residential**.
- **Coverage of the 536 residential:** storeys 100 % (`VIENNA_GEBAEUDEINFO_OBSERVED`), height 100 % (`VIENNA_BKM_MEASURED`), year 4.5 % (24 buildings, `VIENNA_GEBAEUDEINFO_OBSERVED`; the rest take the census route), census unit 100 %.
- **Build counts (bounding box of the 15th):** 23,729 outlines → 5,657 buildings → 5,674 footprint parts; 4,931 points, 142 dropped outside every footprint; buildings with 0 / 1 / ≥2 points: 1,894 / 3,332 / 448; year ties: 1. Chosen area: 702 footprints after cleaning = 536 residential + 49 non-residential + 117 with no point (use unknown, excluded).
- **Deviations / choices not fixed by the plan:**
  1. 1,722 outlines have no `BW_GEB_ID` (layers Sonstiges Bauwerk 1,622 and Stationseinrichtung 100): not buildings, dropped. Outlines of Überbauung / Flugdach / Glashaus that carry a `BW_GEB_ID` are dissolved into their building as the plan says.
  2. A building with no `GEBAEUDEINFOOGD` point has no use, so it is "unknown" and not residential (117 in the chosen units, 1,894 in the bounding box). Residential count therefore equals buildings with a residential point.
  3. Residential label set = {`Wohnnutzung`}; unknown = {empty, `keine Angabe`}. `L_BAUJ` holds only ranges in the live layer ("1848 -1918", "nach 1945" …), so it never gives a single year; only `BAUJAHR` does.
  4. Census reference years (midpoint rounded down): Vor 1919 → 1918; 1919–1944 → 1931; 1945–1960 → 1952; 1961–1970 → 1965; 1971–1980 → 1975; 1981–1990 → 1985; 1991–2000 → 1995; 2001–2005 → 2003 (the 2023 file's class 8; older files use 2001–2011); 2006–2011 → 2008; 2012 and later → 2012 (the plan fixes only the oldest open class; this one is my choice). `period_years` is in `acquisition_report.json`.
  5. Body height kept only when `O_KOTE − HOEHE_DGM > 0`; for split parts, bodies are matched by centroid within the part.
  6. `validate_schema` accepts exactly 23 columns, so the two census columns are attached after `finalize_footprints`: `01_buildings_clean.gpkg` has the 23 columns, `02_*_manifest.gpkg` has 25. `function_tag` is the split key (`Wohnnutzung` → residential).
  7. The WFS layer was reachable with field names as in the plan; ZBEZ ↔ census `SUB_DISTRICT_CODE` is "9" + ZBEZ. No shared file touched.
- **Test status:** `python -m pytest tests/eu22/test_acquire_vienna.py` → 9 passed (schema 23 + 2 census columns; height = O_KOTE − HOEHE_DGM and largest body; dissolve and `_p<n>`; 1900/1900/1910 → 1900, 1900/1910 → none; GESCH_ANZ 0 → none; year outside 1500–2016 unused; points dropped counted; CRS EPSG:32633; provenance strings). Live run: 536 residential, inside 500–1,000.
- **Notes:** live script run takes ~15 s from saved raw files (`--download` re-fetches). Raw SHA-256s are in the report.

#### T02 (amended) — Austrian construction records, national series only — completed 2026-10-08

- **Artifacts:** `openubem/data/construction/tabula_archetypes_at.json` regenerated (38 records, `exclude_prefixes=("AT.MT.",)`); AT section of `openubem/data/construction/TABULA_PROVENANCE.md` (38 rows, AT.MT excluded, reason: parallel series with period gaps); `tests/eu22/test_records_at.py` (`EXPECTED_COUNT = 38`, `KNOWN_GAPS = {}`); `tests/eu22/fixtures/tabula_period_years_at_hu.json` (AT.MT entries removed, 38 AT ids equal the record ids).
- **Deviations:** none; `tabula_registry.py` untouched. Supersedes the 61-record entry above (D-EU-153 amendment 2026-10-08 night).
- **Test status:** `pytest -q tests/eu22/test_records_at.py tests/eu22/test_records_hu.py` gives 18 passed; national series tile with no gap or overlap. Window share of the 38: min 0.0569, median 0.1094, max 0.1892 (all inside 0.05-0.50).
- **Notes:** the `_TABULA_PERIODS["AT"]` tuple above is unchanged (it came from the national rows).

#### T03 — Prepare (S3) — STOPPED 2026-10-09 (not completed)

- **Artifacts:** none. `openubem/outputs/eu_evidence/EU-11/AT-VIE-RUDOLFSHEIM_dw_2026-10-09` was not created.
- **Deviations:** none. Command run as given (the script has no workers flag; one process).
- **Test status:** failed at once with `TypeError: unsupported operand type(s) for /: 'WindowsPath' and 'NoneType'` at `scripts/run_eu_s2_district_campaign.py:122` (`_registry_weather`, called from `prepare` line 1157). Cause: in `openubem/data/weather/weather_registry.json` the `at` target (line ~229) has `weather_file: null` and `sha256: null` (status `RULED_NOT_PINNED`, `acquisition_status: BLOCKED_GATE5_FAIL`; file mtime 2026-10-09 01:04:21). This differs from the manager note ("the `at` EPW is in the registry with a matching sha256"). The EPW file exists as `openubem/data/weather/at_vienna_2007_2008_y2008.epw` (sha256 `4e0b116c774e0e9fee4d9d969c75262d3a938823cc070f4806ffba98fd6c010f`) but is not registered. `--epw` cannot bypass it: line 124 compares the file hash with the registry `sha256`, which is null.
- **Notes:** no entry in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` matched. Fix lies in a shared file (the registry or `_registry_weather`), so no edit made and nothing registered. Waiting on the manager to pin `weather_file` and `sha256` for `at`, then S3 reruns unchanged.

#### Step 0 — Pin the `at` weather fold (D-EU-159) — completed 2026-10-09

- **Artifacts:** `openubem/data/weather/weather_registry.json` (`at` entry only); gate report `openubem/outputs/eu_evidence/EU-07/t06_at_2008_six_gates.json` rewritten by the script.
- **Deviations:** the dry run (`--fold at`) prints only `STOP at GATE5_FAIL`, not the months; the failing months were read from `ew.evaluate_monthly_benchmark_gate` on the same EPW and benchmark at 10 % tolerance: months 1, 3, 11 (Jan +21.2 %, Mar +16.7 %, Nov +15.2 %); all three are in Oct–Mar, none in Apr–Sep, so no STOP.
- **Test status:** `python scripts/run_eu_t06_weather_promotion.py --fold at --approve-gate5-exception at:2008 1 3 11 --commit` printed `PROMOTED at 2008`. `at` entry now: status `RULED_PINNED_EXCEPTION`, `weather_file` `openubem/data/weather/at_vienna_2007_2008_y2008.epw`, sha256 `4e0b116c774e0e9fee4d9d969c75262d3a938823cc070f4806ffba98fd6c010f`, gates 1–4 and 6 PASS, gate 5 `PASS_WITH_DOCUMENTED_EXCEPTION`. JSON compare before/after: es, uk, it, fr, kr, ca, fi, za, hu, am entries and all top-level keys identical; only `at` changed.
- **Notes:** the registry `at` entry does not carry a `gate5_exception` block (the script writes that block only for D-EU-18 grants); the months are recorded here and in D-EU-159.

#### T03 — Prepare (S3) — completed 2026-10-09

- **Artifacts:** `openubem/outputs/eu_evidence/EU-11/AT-VIE-RUDOLFSHEIM_dw_2026-10-09/` (`idfs/` 536, `schedules/`, `weather/`, `prepared_buildings.csv`, `excluded_buildings.csv` empty, `summary.json`, `fleet.lst`, `at_vie_rudolfsheim_manifest.csv`).
- **Deviations:** none. One process, about 4 h 10 min (one building stalled the loop for about 45 min but finished).
- **Test status:** `summary.json`: attempted 536, prepared 536 (100 %), status `PREPARED_FOR_SPEED`, no blocker exclusions, imputation recovered 0 / refused 0. `excluded_buildings.csv` has 0 rows, so there are no exclusion reasons to rank. Types: MFH 388, AB 137, TH 11. Year provenance: 512 `IMPUTED_CENSUS_UNIT_CONSTRUCTION_PERIOD`, 24 observed. Geometry outcomes: 450 `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT`, 83 `..._BEST_EFFORT_IMPUTED_COUNT`, 2 `FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT`, 1 `..._INTERZONE_MISMATCH_REROUTED`.
- **Notes:** none.

#### T04 — Finish the tree (S4) and integrity sweep with division classes (S5) — STOPPED at the S5 gate 2026-10-09 (S4 completed; S5 measured, share below 85 %)

- **Artifacts:** `openubem/outputs/eu_evidence/EU-11/AT-VIE-RUDOLFSHEIM_win_2026-10-09/` (`idfs/` 536, `windows.csv`, `origin_offset.json`, `md5_2026-10-09.txt`, `fleet.lst`, `degenerate_2026-10-09.csv`, `division_classes.csv`, `left_out.csv`); `AT-VIE-RUDOLFSHEIM_dw_2026-10-09/layouts/` (536 side-cars); `openubem/outputs/eu_evidence/EU-11/integrity_2026-10-02/AT-VIE-RUDOLFSHEIM_win_2026-10-09_integrity.csv` and `summary_win_2026-10-09.csv`.
- **Deviations:** (1) `13_model_integrity.py --tree win_2026-10-09` takes the tree name without the leading underscore (with `_win_...` it looks for `AT-VIE-RUDOLFSHEIM__win_...`). (2) Side-cars: used `--population-manifest AT-VIE-RUDOLFSHEIM=<dw>/prepared_buildings.csv` (known circular `left_out.csv` problem, already in the debug references); it took about 4 h 40 min, single process. (3) `13_model_integrity.py` always writes `summary_<tree>.csv` into the shared folder `integrity_2026-10-02/`; the Vienna run overwrote `summary_win_2026-10-09.csv`, which may have held CA/ZA rows written earlier the same day (their per-district integrity CSVs are intact; re-run the summary for CA/ZA if that file is needed).
- **Test status:** S4: 536 IDFs, `fleet.lst` and `md5_2026-10-09.txt` both equal the 536 IDF set, `origin_offset.json` present (dx 598000, dy 5338000, EPSG:32633), degenerate count 0 (changed 0, deleted 0, shift max area difference 0.0, errors 0). S5 integrity failures (of 536): I1 0, I2 1, I3 1, I4 0, I5 1, I6 1, I7 1, I8 1 (of 533), I9–I13 0 (I13 not applicable for new sites); all 5 failures are the same home, stem `6df558531da11477` (5 storeys, 30 zones), 0.19 % so under the 1 % limit. `IDF_FALLBACK` 0 (class source `LAYOUT_SIDECAR` for 536). Classes: OK 235, V3_divided_wrapped_flat 213, V1_divided_shape_rule_broken 83, V2_divided_unbalanced 2, U4_other_box 2, U1_cut_lost_at_idf_write 1. **Correctly divided = 448 / 536 = 83.6 %, below the 85 % limit, so STOP (manager decides; rules stay frozen).** Window share, achieved vs record: median difference 0.00012, largest 0.139 (one home with no window placed; 536 rows, 0 errors); record shares 0.095–0.139.
- **Notes:** T05 (S6 plan pages) not started. Left-out homes: 88 (83 V1, 2 V2, 2 U4, 1 U1).

#### T05 — Plan pages (S6) — completed 2026-10-11 (done under the division-fix plan, `PLAN_eu-division-fix-3cities-2026-10-10.md` §8 T05p)
- Artifacts: `plans3D/PLANS_AT-VIE-RUDOLFSHEIM_2026-10-11.html`, link row in `plans3D/index.html`; tree `AT-VIE-RUDOLFSHEIM_win_2026-10-10` (517 of 536 correctly divided, 19 left out; target 509 met).
- Deviations: none here; see the division-fix plan.
- Test status: see the division-fix plan §8 T05p.
- Notes: owner saw the pages and approved runs 2026-10-11.

#### T06 — Speed run (S7, manager) — submitted 2026-10-11
- Artifacts: `/speed-scratch/o_iseri/fleets/EU22_AT-VIE-RUDOLFSHEIM_win_2026-10-10/` (staged by `stage_eu22_site.sh`, remote IDF count 536 = fleet.lst, 536 schedule folders); job **1451888**, `--array=1-536%9 --mem=32G --time=7-00:00:00`, `speed_jobs.txt` written.
- Deviations: throttle 9, not 32: the three cities share our 32 CPUs (Helsinki 10 + Vienna 9 + Budapest 13, by size); raise the others when one array empties. `--export=ALL,FLEET_DIR=...` added (the job file needs it; the common S7 line omits it). All 536 homes run, left-out ones included; S8 drops them (D-EU-149).
- Test status: 32 of our tasks RUNNING right after submission.
- Notes: S8 harvest only after `sacct` shows all 536 COMPLETED; gate on "EnergyPlus Completed Successfully".

#### T07 — Harvest and results (S8) — completed 2026-10-12
- Artifacts: `EU-11/AT-VIE-RUDOLFSHEIM_win_2026-10-10/{at_vie_rudolfsheim_manifest.csv,summary.json}` (`speed_jobs.txt` already existed, unchanged); `EU-22/AT-VIE-RUDOLFSHEIM/results/EU22_results_AT-VIE-RUDOLFSHEIM_2026-10-10_{per_home.csv,per_home.json,summary.csv,summary.json}`, copied byte-identical (cmp, 4 of 4) to `docs/docs_ACTIVE/europeanLocations/results/`.
- Deviations: none.
- Test status: `sacct -j 1451888`: 536 COMPLETED (confirmed by manager). Harvest: run 536, success 536, failed 0 (gate: return code 0 + "EnergyPlus Completed Successfully"), 536 task folders, manifest 536 rows, pooled EUI 75.72 kWh/m2 (all 536, left-out included; not the published number). Results: 536 - 19 left out (`left_out.csv`) = 517 rows, 517 with result, 0 runs without result. EUI = sum heating / sum area = 77.578 kWh/m2 over 933,129 m2 (heating only); per home min 43.03, median 81.40, mean 79.53, max 120.86. `pytest tests/eu22/test_c07_harvest_results.py` 12 passed.
- Notes: Viewer (T08) reads the copied per_home.csv and `left_out.csv`. Helsinki and Budapest trees untouched.

#### T08 — Viewer and side-cars (S9) — completed 2026-10-12
- Artifacts: `openubem/outputs/3D/eu_AT-VIE-RUDOLFSHEIM_viewer.html` (3,372,178 bytes) and `eu_AT-VIE-RUDOLFSHEIM_data/{buildings.csv (702 rows),index.html,sources.json}`, mirrored byte-identical (`cmp`, `diff -rq` clean) to `docs/docs_ACTIVE/europeanLocations/outputs_3D/` (the generator mirrors by itself); `openubem/outputs/eu_evidence/EU-11/AT-VIE-RUDOLFSHEIM_win_2026-10-10/{layouts/ (517 side-cars),sidecar_population.csv (517 rows)}`; `.../AT-VIE-RUDOLFSHEIM_merged_win_2026-10-10/flat_counts_2026-10-10.csv` (702 rows). Internal only: nothing published, nothing sent to 6J.
- Deviations: (1) Side-car step run with `--evidence-root AT-VIE-RUDOLFSHEIM=<win_2026-10-10 tree>` (manager note of 2026-10-10); the 536 S5 side-cars in `_dw_2026-10-10/layouts/` were not touched (0 files newer than the viewer). (2) The viewer has no EU-21 check badges (join 0 hit / 536 miss), as in the C07 notes. (3) Side-car step took about 67 min (three cities running in parallel). No FI or HU file touched; the generator wrote only per-site files.
- Test status: viewer simulated 517 = results rows 517 (idf_only 0, no_idf 0, undivided / left out 19). Flat counts: simulated 517, run_failed 0, undivided_excluded 19, not_residential 166, no_model 0. Side-car flat count: sum of `new_count` over simulated = 10,506 = sum of `dwellings_used` in `sidecar_population.csv` (517 homes) = sum of `dwellings_total` over the 517 side-car JSONs = 10,506. `pytest -q tests/test_eu18c_viewer_geometry_only.py -k AT` = 10 passed (9 deselected). `pytest -q tests/eu22` = 251 passed, 1 failed: `test_weather_folds.py::test_original_folds_keep_their_year_candidates` (`'kr'` in the registry targets, not in the test's expected set; from the uncommitted Korea registry change, reported, not fixed).
- Notes: no error solved, so nothing added to the debug references.

#### Step W — Vienna typical-year weather file (D-EU-169) — completed 2026-10-24
- Artifacts: `openubem/data/weather/at_vienna_tmyx_2009_2023.epw` (copy of the Climate.OneBuilding TMYx file, md5 779e59f8796483bd67f84b31c0fffd82 matched, sha256 602a077d41c1669180909686589fde854bbb2b989e8219e690f3ac59433f0bab); `openubem/outputs/eu_evidence/EU-22/weather/tmyx_at_gates_2026-10-24.json`; eight `tmyx_*` keys added at the end of the `at` entry in `openubem/data/weather/weather_registry.json`.
- Deviations: none. The pinned ERA5 survey-year file, its sha256, status, validation and ruling are unchanged. Gate 4 solar closure replaced by the annual sun balance per D-EU-164; gate 5 run with no D-EU-18 pre-authorisation. The licence note uses the default wording (no OneBuilding licence text exists under EU-22).
- Test status: gates 1-4 and 6 PASS; annual sun balance 0.99326 (inside 0.97-1.03); gate 5 FAIL, recorded only (D-EU-163). Registry tests: 10 passed, 3 failed (`test_registry_is_explicitly_ruled_not_pinned_and_has_three_targets`, `test_committed_registry_preserves_template_targets_and_records_lyon_promotion`, `test_weather_folds.py::test_original_folds_keep_their_year_candidates`); all three fail on the `kr` entry in the target list, not on the `at` entry or the new keys.
- Notes: no error solved, so nothing added to the debug references.
