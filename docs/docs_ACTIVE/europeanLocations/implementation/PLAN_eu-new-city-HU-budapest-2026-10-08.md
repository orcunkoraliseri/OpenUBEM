# PLAN — new neighbourhood: Budapest, Hungary (`HU-BUD-ERZSEBETVAROS`)

## 1. Header

- **Slug:** `eu-new-city-HU-budapest-2026-10-08` · **Date:** 2026-10-08
- **Owner requests (verbatim, 2026-10-08):** "can you prepare implemeantion plan for each new city, lets go …\implementation"; "i will sleep can yo uhandle the plans and executions"; "follow same piplien for new cities as well, floor plan division, window to wall ratio etc."
- **Parent plan:** `PLAN_eu-new-cities-00-common-2026-10-08.md` (§2 rules, §4 decisions, §6.2 steps S3–S9). Read it first.
- **DESIGN pointers:** DR10 brief line 11; DR11 brief lines 21–30; `rules/RULES_dwelling_layout_groups_nocore_2026-10-08.html`.
- **Site:** `HU-BUD-ERZSEBETVAROS`, country `HU`, fold `hu`, CRS EPSG:32634, MTUS survey year 2009. District: VII Erzsébetváros.
- **Goal:** 500–1,000 residential buildings, same pipeline. No open official footprints with heights or ages exist: footprints from OpenStreetMap (as Madrid and London), storeys partly observed, year from the census per district (as Bologna).

## 2. Hard rules for the executor

Common plan §2 rules 1–12, plus: raw downloads only under `openubem/outputs/eu_evidence/EU-22/HU-BUD-ERZSEBETVAROS/raw/<source>/` (untrusted, `python -I`); licence texts into `…/licences/`; no edit to shared files (STOP instead).

## 3. File layout

| Path | Status | Task |
|---|---|---|
| `scripts/eu22/acquire_budapest.py` | new | T01 |
| `tests/eu22/test_acquire_budapest.py`, fixtures | new | T01 |
| `openubem/outputs/eu_evidence/EU-22/HU-BUD-ERZSEBETVAROS/…` | new | T01 |
| `openubem/outputs/eu02/HU-BUD-ERZSEBETVAROS/{01_buildings_clean,02_residential_manifest}.gpkg` | new | T01 |
| `openubem/data/construction/tabula_archetypes_hu.json` | new | T02 |
| `openubem/data/construction/TABULA_PROVENANCE.md` | edit: HU section | T02 |
| `tests/eu22/test_records_hu.py` | new | T02 |
| `scripts/eu22/merge_prepare_parts.py` | new | T03s |
| `tests/eu22/test_merge_prepare_parts.py` | new | T03s |
| `openubem/outputs/eu_evidence/EU-11/HU-BUD-ERZSEBETVAROS_dw_2026-10-09_parts/p1…p6/` | new | T03s |
| `openubem/outputs/eu_evidence/EU-11/HU-BUD-ERZSEBETVAROS_dw_2026-10-09_single_stopped/` | renamed from the stopped single run | T03s |

## 4. Dependency decisions (pinned)

- **Footprints:** OpenStreetMap (ODbL) through the existing OSM route of the acquisition package (read `openubem/acquisition/osm_fetcher.py:35-61` and call its functions from the city script; do not edit the dispatcher). Provenance as the existing OSM sites.
- **Storeys:** OSM `building:levels` (observed, about 23 % in the feasibility count) → else Copernicus Urban Atlas Building Height 2012 (10 m raster; median of the cells inside the footprint, `round(h / 3.0)`, provenance `UA_BUILDING_HEIGHT_2012_MEASURED`) if it can be downloaded without an account; if it needs a login, skip this rung and say so → else neighbour imputation (D-EU-154). Report coverage per rung.
- **Year:** OSM `start_date` when it is a year (observed) → else the census route: KSH Census 2011, Budapest volume (`https://www.ksh.hu/docs/hun/xftp/idoszaki/nepsz2011/nepsz_03_01_2011.pdf`), table 3.3.2.1, occupied dwellings by construction period per district. The census unit is the district (VII), periods before 1946, 1946–60, 1961–70, 1971–80, 1981–90, 1991–2000, 2001–05, 2006–11; reference year per label as Vienna §4. In VII about 90 % of dwellings are from before 1946, so nearly every building gets that period. Look for a Census 2022 table by smaller area (nepszamlalas2022.ksh.hu); if one exists with construction periods, use it instead and say so.
- **Type:** OSM tags `apartments` / `detached` / `terrace` → else the storey rule (D-EU-154).
- **Sub-unit:** VII's two parts (Belső-Erzsébetváros first, then Külső-Erzsébetváros) from OSM `admin_level=10` boundaries; D-EU-151.
- **Construction:** TABULA HU from the pinned workbook (D-EU-153), 16 rows, via `generate_country_registry("HU", …)`. Cross-check against the TABULA HU brochure (BME 2014, `https://episcope.eu/fileadmin/tabula/public/docs/brochure/HU_TABULA_TypologyBrochure_BME.pdf`): e.g. MFH before 1944 wall U 1.10, window U 3.00 — print the workbook values next to the brochure values; differences go in the log, the workbook wins.

## 5. Facts with citations

- Common plan §5.
- Workbook HU: 16 rows, period tokens 01, 01-03, 02, 03, 04, 04-05, 05 (measured 2026-10-08).
- OSM count in the feasibility box 72,126 buildings, 17,021 with levels (2026-10-08 research).

## 6. Tasks

#### T01 — Acquire and clip Budapest
**How.** OSM buildings for VII (saved raw), reproject to EPSG:32634, storeys and year per §4, census columns (`census_unit_id` = `HU-BUD-VII`, `census_period_counts` from the table), `SCHEMA_COLUMNS`, `finalize_footprints`, sub-units, clip, `split_residential`, `write_manifests`, report.
**How to test.** Fixture: `building:levels` "4", "4;5", "" → 4, missing (record the rule used for "4;5"), missing; `start_date` "1898" vs "c1900" (only a plain year is observed); census columns; CRS EPSG:32634. Live: count 500–1,000; coverage per rung.

#### T02 — Hungarian construction records
As Vienna T02 with `HU` (16 rows), plus the brochure comparison table.

#### T03 — Prepare (S3) · T04 — S4 + S5 · T05 — Plan pages (S6, then STOP) · T06 — Speed (manager) · T07 — S8 · T08 — S9
Common plan §6.2 with `SITE=HU-BUD-ERZSEBETVAROS`, `cc=HU`.

#### T03s — Prepare in 6 parts, then join (amendment 2026-10-09, owner: "yes split it")
**What.** Replaces the single S3 process for this site only. The single run (started 10:55, PID 53220) did 33 of 805 buildings in 50 min (about 15 h left).
**Why.** Budapest's courtyard blocks give 1–3.5 MB models; one process is too slow. `prepare` already takes `--only-ids` (`scripts/run_eu_s2_district_campaign.py:1381-1386`); the filter is applied per building after the district-wide context and median height are computed over all rows (`:1150-1192`), so a part should give the same model for each building as one run. No join tool exists.
**How.**
1. New `scripts/eu22/merge_prepare_parts.py --parts P1 … PN --out OUT`. `OUT` must not exist (else exit with an error). Copy `idfs/*` and `schedules/*` of every part into `OUT`; a name in two parts is an error. `weather/`: all parts byte-equal, copy once, else error. `prepared_buildings.csv`, the `*_manifest.csv`, `fleet.lst`: concatenate in the order the parts are given, header once. `excluded_buildings.csv`: concatenate, then drop exact duplicate rows, keeping first order (district-wide exclusions repeat in every part). `summary.json`: every key except `population_prepared`, `blocker_exclusions` and `context_height_fallback_census` must be equal across parts (else error naming the key); `population_prepared` = sum; `context_height_fallback_census` (a per-building `Counter` dict, `run_eu_s2_district_campaign.py:1189,1302`) = per-key sum over parts, keys sorted (amendment 2026-10-09 after the step-2 stop: Cape Town A 79 = B1 36 + B2 43); `blocker_exclusions` = count of the joined `excluded_buildings.csv` by `blocker`, sorted; written as `prepare` writes it (`:1305`, `indent=2, sort_keys=True` + newline). Any other file in a part → error naming it. Never edits or deletes a part.
2. Test, Cape Town (no network): take the first 12 `building_id` of `ZA-CPT-WOODSTOCK_dw_2026-10-09/prepared_buildings.csv`. Run `prepare --district ZA-CPT-WOODSTOCK --only-ids <12>` into a temp folder A; run it twice more with ids 1–6 and 7–12 into B1, B2; join B1, B2 into B. Every file in A and B must be byte-equal (list each file and the result). Any difference → STOP and report the file and the first differing line or key; do not touch Budapest. Also `tests/eu22/test_merge_prepare_parts.py` on small fake parts: the duplicate-name error, the weather mismatch error, duplicate exclusion rows dropped, counts summed.
3. Budapest: stop PID 53220 only (check first that its command line is the Budapest prepare). Rename `HU-BUD-ERZSEBETVAROS_dw_2026-10-09` to `HU-BUD-ERZSEBETVAROS_dw_2026-10-09_single_stopped` (keep it). Take `building_id` of `openubem/outputs/eu02/HU-BUD-ERZSEBETVAROS/02_residential_manifest.gpkg` in file order, cut into 6 contiguous parts, write each list as a one-column `building_id` CSV next to the parts. Start 6 `prepare --only-ids` processes in the background into `…_dw_2026-10-09_parts/p1…p6` (6 local processes; S3 command otherwise unchanged). When all 6 exit 0, join p1…p6 into `HU-BUD-ERZSEBETVAROS_dw_2026-10-09`. Then run the S3 test of the common plan §6.2 on the joined tree and continue with T04, T05.
**How to test.** Step 2 byte-equality; the fake-part tests; joined `population_prepared` + unique excluded buildings covers all 805.

## 7. Stop-and-report points

1. After T01 + T02. 2. After T05. 3. After T08.

## 8. Progress log

(One entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes.)

#### T02 — Hungarian construction records — completed 2026-10-08

- **Artifacts:** `openubem/data/construction/tabula_archetypes_hu.json` (16 records); HU section in `openubem/data/construction/TABULA_PROVENANCE.md`; `tests/eu22/test_records_hu.py`; shared fixture `tests/eu22/fixtures/tabula_period_years_at_hu.json`.
- **Deviations:** (1) Brochure comparison: no network was allowed, so the TABULA HU brochure (BME 2014) was not downloaded. Only the two values quoted in the plan are compared: workbook `HU.N.MFH.01.Gen.ReEx.001.001` wall U 1.10 (brochure 1.10, equal), window U 3.50 (brochure 3.00, differs by 0.50). Workbook wins; full brochure table comparison remains open for a networked run. (2) Tiling test: HU has no gaps or overlaps for MFH and SFH (periods 01-05); AB has only ReEx period 05 (2006+) plus the range row `HU.N.AB.01-03` (SyAv); there is no AB period 04. (3) Range rows (`SyAv`) carry first token only in `construction_period`.
- **Test status:** `pytest -q tests/eu22/test_records_hu.py` passes (9 tests; 16 records, key set equals IT, MD5 `c99ddc9ffcb6dc0ae7391273d9619e37`). Window share per record: min 0.0907, median 0.1265, max 0.2813 (all inside 0.05-0.50).
- **Notes:** `_TABULA_PERIODS["HU"]` tuple for C03 to paste (from the MFH and SFH ReEx rows, identical across both):
  `"HU": ((0, 1944, "HU.01"), (1945, 1979, "HU.02"), (1980, 1989, "HU.03"), (1990, 2005, "HU.04"), (2006, 9999, "HU.05"))`.

#### T01 — Acquire and clip Budapest — completed 2026-10-08

- **Artifacts:** `scripts/eu22/acquire_budapest.py`; `tests/eu22/test_acquire_budapest.py` with fixtures `budapest_osm_buildings.json`, `budapest_relation.json`, `budapest_ksh2011_vii_page.txt`; `openubem/outputs/eu02/HU-BUD-ERZSEBETVAROS/{01_buildings_clean,02_residential_manifest}.gpkg` (+ excluded manifest, counts, source sidecar); `openubem/outputs/eu_evidence/EU-22/HU-BUD-ERZSEBETVAROS/{acquisition_report.json,boundary.geojson,boundary.sha256,licences/,raw/}`; one entry in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (Overpass 406 / saved 429 page).
- **Deviations:** (1) Year: the shared parser `_parse_year` turns `C19` into 1850 and `1898-1900` into 1898 and marks both observed; the script re-parses `start_date` and accepts only a plain four-digit year (1500-2026); everything else is missing. Shared files untouched (`_flatten_tags` imported, not edited). (2) `building:levels` "4;5" is missing (shared parser does not read lists); it falls to the next rung. (3) Reference year for "before 1946" is 1945 (plan rule: upper year of the open-ended class). 1945 falls in the T02 band `HU.02` (1945-1979), not `HU.01` (to 1944), so ~90 % of buildings would map to HU.02: manager decision needed before T03. (4) OSM has no Belső-/Külső-Erzsébetváros boundary (only relation 3229918 "Erzsébetváros", level 10, beside relation 1606102 "VII. kerület", level 9; name search empty), so the sub-unit rule was not needed: the whole district holds 805, inside 500-1,000. (5) Residential = the Madrid/London crosswalk on `building_tag` (`openubem/data/osm_to_use_class.json`): 783 `building=yes` footprints in the district are unknown and excluded, as at the other OSM sites.
- **Test status:** `pytest -q tests/eu22/test_acquire_budapest.py` 12 passed (levels "4" / "4;5" / "" / "0"; year "1898" vs "c1900", "C19", range; census columns; CRS EPSG:32634; census page parse; relation polygon; unit-range rule). Live run `python -I scripts/eu22/acquire_budapest.py` OK; manifest CRS EPSG:32634, `osm_id` unique, 25 columns (23 schema + 2 census).
- **Notes:** Units used with running counts: `VII. kerület (OSM relation 1606102)` 805, running total 805 (whole district, one unit). Residential count 805 (clean 5,490; clipped 1,707; unknown 783; non-residential 119). OSM data timestamp 2026-10-09T03:35:14Z. Coverage of the 805: storeys observed (OSM `building:levels`) 442 = 54.91 %; Urban Atlas Building Height 2012 skipped (CLMS download answers 401 Unauthorized without an EU Login token, probe saved); OSM `height` tag adds 0 further; 363 = 45.09 % left for neighbour imputation. Year observed (OSM plain `start_date`) 17 = 2.11 %; 788 take the census period. Type from tag 798 = 99.13 % (`apartments` 798, `residential` 3, `house` 3, `dormitory` 1). Census unit = district VII (`census_unit_id` `HU-BUD-VII`, 805 = 100 %), source KSH Census 2011 table 3.3.2.1 (PDF, sha256 in report): before 1946 26,529; 1946-60 458; 1961-70 473; 1971-80 53; 1981-90 202; 1991-2000 102; 2001-05 726; 2006-11 1,001; total 29,544 (89.8 % before 1946). Census 2022: only district/county level carries construction period (no table smaller than district), static tables are county level, so 2011 stays. Reference years in `acquisition_report.json` `period_years`: 1945, 1953, 1965, 1975, 1985, 1995, 2003, 2008. Licences captured at download time under `licences/` (OSM ODbL, KSH CC BY 4.0 for 2011 and 2022 pages, Copernicus not downloaded).

#### T01 (amended) — oldest census class year — completed 2026-10-08

- **Artifacts:** `scripts/eu22/acquire_budapest.py` (new constant `OLDEST_CLASS_YEAR = 1944`, used for "before 1946"); `tests/eu22/test_acquire_budapest.py` (new `test_oldest_class_year_follows_hu01`, ties the year to the HU.01 end in `tabula_period_years_at_hu.json`); regenerated `openubem/outputs/eu_evidence/EU-22/HU-BUD-ERZSEBETVAROS/acquisition_report.json` and `openubem/outputs/eu02/HU-BUD-ERZSEBETVAROS/` files.
- **Deviations:** (1) Existing `test_period_years` asserted 1945 for "before 1946"; changed to 1944 in the same file. (2) Rerun used `python -I scripts/eu22/acquire_budapest.py` without `--refresh`: all raw inputs reused, nothing downloaded.
- **Test status:** `pytest -q tests/eu22/test_acquire_budapest.py` 13 passed. `period_years["before 1946"] == 1944` confirmed in the report; other seven years unchanged. `census_period_counts` of the residential and excluded manifests identical before and after (805 and 902 rows, same checksums).
- **Notes:** Rule applied as D-EU-154 amendment: HU.01 ends 1944, inside "before 1946", so the class takes 1944. The year is a constant, not computed from the TABULA table at run time.

#### T03s — Prepare in 6 parts, then join — completed 2026-10-09

- **Artifacts:** `scripts/eu22/merge_prepare_parts.py` (updated: `context_height_fallback_census` summed per key, keys sorted); `tests/eu22/test_merge_prepare_parts.py` (8 tests); `openubem/outputs/eu_evidence/EU-11/HU-BUD-ERZSEBETVAROS_dw_2026-10-09_parts/{ids_p1..p6.csv,p1..p6,p*.log}`; joined `HU-BUD-ERZSEBETVAROS_dw_2026-10-09/`; stopped single run kept as `HU-BUD-ERZSEBETVAROS_dw_2026-10-09_single_stopped/`.
- **Deviations:** (1) The manifest has no `building_id` column; the id lists use `osm_id`, which is the `building_id` that `new_country_rows` assigns (`openubem/semantic/new_country_rules.py:223`). 805 ids, unique, cut 134/134/134/135/134/134 in file order. (2) Cape Town test folders were reused from the scratchpad `cpt\` of session 74dad075 (the session id in the kickoff, c49e97f6, held none).
- **Test status:** `pytest -q tests/eu22/test_merge_prepare_parts.py` 8 passed. Cape Town B1+B2 joined into B: 34 files in A, 34 in B, 34 byte-equal, 0 different (`summary.json` census `height_m` 79 = 36 + 43). PID 53220 command line was the Budapest single prepare; only it was stopped. All 6 parts exit 0; joined `population_prepared` 805, `prepared_buildings.csv` ids equal the manifest `osm_id` set (805), 805 IDFs, `fleet.lst` 805. Excluded rows 363, all `MISSING_OBSERVED_STOREY_COUNT`, all 363 recovered by neighbour imputation (so prepared + excluded union = 805; none lost). Prepared share 100 %. Most common exclusion reasons: one (above).
- **Notes:** Part wall time about 2 h 40 min (p4 and p6 slowest, large courtyard blocks).

#### T04 — S4 + S5 — STOPPED 2026-10-09 (correctly divided share 75.7 % < 85 %)

- **Artifacts:** `HU-BUD-ERZSEBETVAROS_win_2026-10-09/` (805 IDFs, `fleet.lst` 805, `md5_2026-10-09.txt` 805, `origin_offset.json`, `windows.csv` 805, `dwelling_counts_2026-10-09.csv`, `degenerate_2026-10-09.csv`, `division_classes.csv`, `left_out.csv`); `HU-BUD-ERZSEBETVAROS_dw_2026-10-09/layouts/` (805 side-cars, all parse); `integrity_2026-10-02/HU-BUD-ERZSEBETVAROS_win_2026-10-09_integrity.csv`.
- **Deviations:** (1) Side-car emitter run with `--population-manifest HU-BUD-ERZSEBETVAROS=<dw>/prepared_buildings.csv` (same as Cape Town; otherwise it reads the not-yet-written `left_out.csv`). (2) The emitter is single-process and ran at about 1 home per minute on the courtyard blocks, so I added emitters on disjoint subsets (pop1..pop6, tail4..6, scratchpad `hu_pop\`), 6 to 8 at once; outputs are per-home files, identical in content. Three redundant own emitter processes were stopped after all 805 files existed; all 805 JSON files parse. (3) `integrity_2026-10-02/summary_win_2026-10-09.csv` is one shared file per date and was rewritten by this run.
- **Test status:** drop-degenerate: 805 IDFs, changed 0, deleted 0, errors 0. Integrity fails of 805: I1 0 (of 442), I2 6, I3 2, I4 0, I5 3, I6 3, I7 8, I8 1 (of 802), I9-I12 0, I13 not applicable new site; largest is 8 = 0.99 %, not above 1 %. Division: OK 192, V3 417, V1 190, V2 3, U4 3; class source LAYOUT_SIDECAR 805, IDF_FALLBACK 0; left out 196 (V1 + V2 + U4), correctly divided 609 of 805 = 75.65 %, below the 85 % limit. Window share achieved vs record share: median difference 6e-12, largest 0.2813 (one home with no window).
- **Notes:** STOP at the S5 rule (rules stay frozen; manager decides). T05 (plan pages) not started.
