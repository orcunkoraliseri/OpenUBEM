# PLAN — new neighbourhood: Montréal, Canada (`CA-MTL-PLATEAU`)

## 1. Header

- **Slug:** `eu-new-city-CA-montreal-2026-10-08` · **Date:** 2026-10-08
- **Owner requests (verbatim, 2026-10-08):** "can you prepare implemeantion plan for each new city, lets go …\implementation"; "i will sleep can yo uhandle the plans and executions"; "follow same piplien for new cities as well, floor plan division, window to wall ratio etc."
- **Parent plan:** `PLAN_eu-new-cities-00-common-2026-10-08.md` (§2 rules, §4 decisions, §6.2 steps S3–S9). Read it first.
- **DESIGN pointers:** DR10 brief line 11; DR11 brief lines 21–30; `rules/RULES_dwelling_layout_groups_nocore_2026-10-08.html`.
- **Site:** `CA-MTL-PLATEAU`, country `CA`, fold `ca`, CRS EPSG:32618, MTUS survey year 2010. District: the Plateau-Mont-Royal borough.
- **Goal:** 500–1,000 residential buildings (mostly plexes), same pipeline as the four cities. OpenUBEM has no Canadian site; this is a new build (our reply to 6J §2).

## 2. Hard rules for the executor

Common plan §2 rules 1–12, plus: raw downloads only under `openubem/outputs/eu_evidence/EU-22/CA-MTL-PLATEAU/raw/<source>/` (untrusted, `python -I`); licence texts into `…/licences/`; no edit to shared files (STOP instead).

## 3. File layout

| Path | Status | Task |
|---|---|---|
| `scripts/eu22/acquire_montreal.py` | new | T01 |
| `tests/eu22/test_acquire_montreal.py`, fixtures | new | T01 |
| `openubem/outputs/eu_evidence/EU-22/CA-MTL-PLATEAU/…` | new | T01 |
| `openubem/outputs/eu02/CA-MTL-PLATEAU/{01_buildings_clean,02_residential_manifest}.gpkg` | new | T01 |
| `openubem/data/construction/national_specs/ca_spec.json`, `tabula_archetypes_ca.json` | new | T02 |
| `openubem/data/construction/TABULA_PROVENANCE.md` | edit: CA section | T02 |
| `tests/eu22/test_records_ca.py` | new | T02 |

## 4. Dependency decisions (pinned)

- **Footprints:** Ville de Montréal "Bâtiments 2D" (donnees.montreal.ca, dataset `batiment-2d`, GPKG, 2016 vintage), CC BY 4.0. Source CRS MTM zone 8 (EPSG:32188 — confirm in the file).
- **Attributes:** Montréal property roll "Unités d'évaluation foncière" (donnees.montreal.ca, open), fields `ANNEE_CONSTRUCTION`, `ETAGE_HORS_SOL`, `NOMBRE_LOGEMENT`, and the use code (`CODE_UTILISATION` / CUBF; residential = codes 1000–1999). `-1`, `0` (for storeys and dwellings), `9999` and years before 1600 mean missing. Provenance `MTL_ROLE_OBSERVED`.
- **Join:** the roll is per lot polygon. A building takes the lot that holds its footprint centroid. Year, storeys and use are copied. The lot's dwelling count is split over the residential buildings of that lot in proportion to footprint area × storeys, largest-remainder rounding, each ≥ 1; stamp `dwellings_source = observed_split` (the Madrid rule, `run_eu_s2_district_campaign.py:171-185`). A building whose centroid is in no lot → no attributes (D-EU-154 routes).
- **Amendment 2026-10-08 night (manager, after T01): split roofs at lot lines.** `batiment-2d` merges attached plexes into block roofs (1,330 of 1,841 roofs span several lots). Each roof is cut by the roll's lot polygons: one building = one roof ∩ lot piece. Pieces under 15 m² are dropped and counted. `osm_id` = `CA-MTL-<roof record no.>-<lot id>`; `provenance_geometry` = `MTL_BATIMENT2D_SPLIT_BY_LOT`. Each piece takes its own lot's year, storeys, use and dwellings. If a lot holds several pieces (several roofs), the area × storeys split above applies within the lot. Height is not in the layer, so storeys come from the roll (D-EU-154). Shared edges between pieces are party walls, handled by the normal adjacency step. The census-tract choice is then redone on the piece count under D-EU-151 (one tract first, then touching tracts until ≥500, never >1,000). Test: a roof over 3 lots gives 3 buildings whose areas sum to the roof area within 0.5 %, and the site's dwelling total is within 10 % of the roll's residential dwellings inside the boundary (report both).
- **Type:** roll use codes for one dwelling → `detached` when not touching another building, else `terrace`; everything else typed by D-EU-154 (the two-signal rule works here because dwellings are observed). Record the code → tag table.
- **Sub-unit:** Statistics Canada 2021 census tracts (boundary file, Open Government Licence – Canada) inside the borough, ranked by residential buildings per km², densest first; D-EU-151.
- **Construction (D-EU-152), donor SE.** Periods: `CA.01` ≤1945, `CA.02` 1946–1960, `CA.03` 1961–1977, `CA.04` 1978–1983, `CA.05` 1984–2011, `CA.06` 2012+ (Québec energy regulation of 1983; Québec Construction Code chapter I.1 Part 11 from 2012). Existing-stock U-values by vintage for Québec from the CHREM / CSDDRD archetype work (Swan, Ugursal et al., Canadian Single-Detached Dwelling Database and its multi-unit extension) or NRCan's housing-stock studies; new-build values from the Québec regulations. Cite each. Mean flat area per type from the Statistics Canada 2021 census or the roll itself (floor area ÷ dwellings, median per type and period — this one is measured, so prefer it and say so).

## 5. Facts with citations

- Common plan §5.
- Roll fields and the −1 null marker from the feasibility research (2026-10-08); confirm on the live file.
- `_catastro_dwelling_overrides` split precedent `run_eu_s2_district_campaign.py:171-185`.

## 6. Tasks

#### T01 — Acquire and clip Montréal

**What / Why.** One script, raw saved, footprints joined to the roll, standard manifests, report.

**How.** Download both datasets (borough only), reproject to EPSG:32618, join per §4, write `SCHEMA_COLUMNS` (`osm_id` = `CA-MTL-<building id>`) plus `observed_dwellings`, `dwellings_source`; `finalize_footprints`; sub-units by D-EU-151; clip; `split_residential`; `write_manifests`. Report: buildings with no lot, lots with several buildings, coverage of year / storeys / dwellings / use.

**How to test.** Fixture of 3 lots × 1–3 buildings: the split gives the hand-computed counts and sums to the lot count; −1 / 9999 handling; centroid-in-no-lot → empty; CRS EPSG:32618. Live: count in 500–1,000; coverage lines.

#### T02 — Canadian construction records

**What.** `national_specs/ca_spec.json`, `tabula_archetypes_ca.json` via `national_records.build_records`, CA section in `TABULA_PROVENANCE.md`.

**How / test.** As Helsinki T02 (donor SE, same test file shape `tests/eu22/test_records_ca.py`). Print the type × period table.

#### T03 — Prepare (S3) · T04 — S4 + S5 · T05 — Plan pages (S6, then STOP) · T06 — Speed (manager) · T07 — S8 · T08 — S9
Common plan §6.2 with `SITE=CA-MTL-PLATEAU`, `cc=CA`. Weather fold `ca` uses the negative-offset raw window (common D-EU-155).

## 7. Stop-and-report points

1. After T01 + T02. 2. After T05 (pages before runs). 3. After T08.

## 8. Progress log

(One entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes.)

#### T01 — Acquire and clip Montréal — completed 2026-10-08 (code and tests done; live data result NOT accepted, see Notes)

- **Artifacts:** `scripts/eu22/acquire_montreal.py`; `tests/eu22/test_acquire_montreal.py` + `tests/eu22/fixtures/montreal_{roll,roofs}_fixture.geojson`; `openubem/outputs/eu02/CA-MTL-PLATEAU/` (01 clean, 02 residential / excluded manifests, counts, source); `openubem/outputs/eu_evidence/EU-22/CA-MTL-PLATEAU/{acquisition_report.json,boundary.geojson,boundary.sha256,licences/,raw/}`.
- **Result:** CRS EPSG:32618; 12 census tracts chosen (densest 4620150.00, then touching tracts by nearest centroid: 4620149, 151, 152, 148, 153, 147, 154, 155, 156, 146, 157); 544 residential buildings (638 clipped, 94 non-residential, 0 unknown). Coverage of the 544: storeys 523 (96.14 %), year 528 (97.06 %), dwellings 530 (97.43 %), use code 544 (100 %). Dwellings source: 486 observed, 44 observed_split, 14 missing. 41 roofs in no lot, 46 roofs in several lots, 91 lots hold several buildings.
- **Test status:** `python -m pytest tests/eu22/test_acquire_montreal.py` 10 passed (hand split 6 → 4+2, 5 → 2+2+1; −1 / 0 / 9999 / 1599 / 1600 handling; centroid in no lot → empty; CRS EPSG:32618; split_residential on the fixture).
- **Deviations / plan-vs-data conflicts:**
  1. 🔴 The footprint layer `CARTO_BAT_TOIT` (the polygon layer of Bâtiments 2D) is a roof layer that merges attached buildings: 1,330 of 1,841 roofs that hold a lot centroid hold more than one (median 4 lots, max 64 lots per roof). The plan's rule (building takes the one lot at its centroid) therefore gives a roof only one lot's dwellings: the 544 manifest buildings carry 3,529 dwellings while the roll lists 13,534 dwellings on the 3,105 residential lots inside the boundary (26 %). The 544 count is in range but the buildings are block roofs, not plexes. Not accepted; manager decision needed (no alternative applied).
  2. The roll has many evaluation units per lot polygon (45,673 rows, 23,371 distinct polygons; condos share one polygon). Applied: units grouped by identical polygon; dwellings = sum over residential units only when every residential unit has a count (308 residential lots left without a count); year = mode over residential units (tie → earliest); storeys = max; residential if any unit has a 1000–1999 code. Plan §4 is silent on this.
  3. Null markers in the live roll are blank (NaN) and `ANNEE_CONSTRUCTION = 9999` (1,665 rows); −1 is also handled. Year 1600 (1 row) is kept, per the plan wording "before 1600".
  4. The roof layer has no building id; `osm_id` = `CA-MTL-<GeoPackage FID>` (`_partN` for multi-part roofs). Source CRS in the file is NAD83(CSRS) / MTM zone 8 (EPSG:2950), not EPSG:32188.
  5. The dataset hosts block the default curl User-Agent (reply "RBAC: access denied", 19 bytes); a browser User-Agent works. The debug-references file was not touched (shared file); entry text to add: "RBAC: access denied — donnees.montreal.ca rejects the default curl User-Agent. Fix: send -A 'Mozilla/5.0'."
  6. D-EU-151 expansion picks tracts touching the growing union (nearest to the first tract's centroid); candidates restricted to tracts ≥ 50 % inside the borough. Roofs under 20 m² are dropped by the shared cleaner (843 of 3,259).
- **Notes:** raw files are 2.1 GB under `raw/` (the roll GeoJSON and roof GPKG are extracted copies of the zips). Licences saved: CC BY 4.0 legal code, Open Government Licence – Canada page, CKAN metadata of both datasets.

#### T01 (rerun after amendment) — Acquire and clip Montréal — completed 2026-10-08

- **Artifacts:** `scripts/eu22/acquire_montreal.py` (new `split_roofs_by_lots`, `dwelling_agreement`; centroid join removed); `tests/eu22/test_acquire_montreal.py` (+2 tests, id helper); regenerated `openubem/outputs/eu02/CA-MTL-PLATEAU/` (01 clean, 02 residential / excluded manifests, counts, source) and `openubem/outputs/eu_evidence/EU-22/CA-MTL-PLATEAU/{acquisition_report.json,boundary.geojson,boundary.sha256}`. Raw downloads reused, no new download.
- **Result:** 3,259 roof parts cut into 16,219 roof ∩ lot pieces; 9,091 pieces under 15 m² dropped (36,342 m² in all, whole borough); the shared cleaner then dropped 606 more under 20 m²; 15,613 buildings borough-wide. D-EU-151 on the new count: first tract 4620159.00 alone holds 423 residential (running 423, below 500); added 4620160.00 (+302, running 725). Residential 725 (779 clipped: 18 non-residential, 36 unknown). Dwellings: site total 2,183 vs roll residential dwellings in the boundary lots 2,188 (ratio 0.9977; 4 of 708 lots have no count). Coverage of the 725: storeys 700 (96.55 %), year 710 (97.93 %), dwellings 721 (99.45 %), use code 725 (100 %). Dwellings source: 683 observed, 38 observed_split, 4 missing. `osm_id` unique, CRS EPSG:32618, `provenance_geometry` = `MTL_BATIMENT2D_SPLIT_BY_LOT`.
- **Test status:** `python -m pytest tests/eu22/test_acquire_montreal.py -q` 12 passed (10 earlier, adapted to the new ids, plus: roof over 3 lots gives 3 buildings, areas sum within 0.5 %, own year / storeys / dwellings; small piece dropped and counted, site dwelling total within 10 % of roll).
- **Deviations:**
  1. The shared cleaner (`finalize_footprints`, step 6) drops footprints under 20 m², so pieces of 15–20 m² are dropped there (606 borough-wide), not kept; the shared file was not touched.
  2. Roof area outside every lot is kept as its own piece (`…-NOLOT`) with no attributes when ≥ 15 m² (class unknown; 913 borough-wide, 15 roofs touch no lot); the amendment is silent on it.
  3. A multi-polygon piece gets a `-k` suffix on its `osm_id`; `lot_id` is `LOT<index>` assigned in roll order.
- **Notes:** 105 roofs are covered by overlapping lot polygons (stacked roll polygons, up to 31 times the roof area); identical copies are merged by the cleaner's overlap rule, partial overlaps are not. In the boundary the dwelling total still matches the roll, so no correction was applied.

#### T02 — Canadian construction records — completed 2026-10-08

- **Artifacts:** `openubem/data/construction/national_specs/ca_spec.json` (24 entries), `openubem/data/construction/tabula_archetypes_ca.json` (24 records, built with `national_records.build_records`, donor SE), `tests/eu22/test_records_ca.py` (14 tests), CA section appended at the end of `openubem/data/construction/TABULA_PROVENANCE.md`.
- **Test status:** `python -m pytest tests/eu22/test_records_ca.py -q` 14 passed; `test_records_tools.py` 13 passed. U-values never increase from CA.01 to CA.06 for any type; window share 0.142 to 0.172.
- **`_TABULA_PERIODS["CA"]` (not written; `construction_sets.py` is shared):** `((0, 1945, "CA.01"), (1946, 1960, "CA.02"), (1961, 1977, "CA.03"), (1978, 1983, "CA.04"), (1984, 2011, "CA.05"), (2012, 9999, "CA.06"))`
- **Type x period table** (SFH and TH are identical in U-values; flat area = a_c_ref / n_apartment):

| type | period | U wall | U roof | U floor | U window | share | n_air | flat m2 |
|---|---|---|---|---|---|---|---|---|
| SFH/TH | CA.01 | 0.625 | 0.263 | 0.625 | 4.00 | 0.142 | 0.510 | 106.2 (donor) |
| SFH/TH | CA.02 | 0.556 | 0.238 | 0.625 | 4.00 | 0.172 | 0.345 | 106.2 |
| SFH/TH | CA.03 | 0.503 | 0.233 | 0.625 | 3.00 | 0.168 | 0.319 | 106.2 |
| SFH/TH | CA.04 | 0.405 | 0.205 | 0.556 | 3.00 | 0.159 | 0.270 | 106.2 |
| SFH/TH | CA.05 | 0.353 | 0.182 | 0.526 | 2.85 | 0.153 | 0.229 | 106.2 |
| SFH/TH | CA.06 | 0.232 | 0.139 | 0.334 | 2.00 | 0.152 | 0.200 (donor) | 106.2 |
| MFH | CA.01 to CA.06 | same U, share, n_air as above | | | | | | 95.7, 56.0, 49.2, 105.0, 86.1, 103.2 |
| AB | CA.01 to CA.06 | same U, share, n_air as above | | | | | | 64.9 (pooled, all periods) |

- **Deviations:**
  1. SE has only SFH and MFH: TH took the SE SFH donor, AB the SE MFH donor (stamped `ASSUMED:donor`). Pairing by period overlap: CA.01 and CA.02 to SE.01, CA.03 to SE.02, CA.04 to SE.03, CA.05 to SE.05 (tie with SE.04, 10 years each; the period midpoint decides), CA.06 to SE.05 (nearest).
  2. Existing-stock values (CA.01 to CA.05) come from the CSDDRD paper (Swan, Ugursal, Beausoleil-Morrison, eSim 2008, p.149 Table 3), single-detached national vintage columns; no Québec by vintage and no multi-unit data found. Straddling periods use year-weighted means; the 1990-2003 column is extended to 2011. These are survey averages that include retrofits, so they sit above code minimums of the time (REENB 1983 wall RSI 2.38).
  3. CA.01 to CA.04 window U (4.0, 4.0, 3.0, 3.0) are `ASSUMED`: no Canadian window-by-vintage source found. CA.05 window U 2.85 is the REENB glass limit (ACQ fiche p.3). CA.06 values are from the 22 Feb 2012 Gazette officielle draft Partie 11 (Tables 11.2.2.1.A, 11.2.2.4.A); the adopted text was not checked.
  4. CA.06 keeps the donor infiltration, g-value and thermal-bridge add-on; all periods keep donor g-value and thermal-bridge add-on.
  5. The basement-wall RSI (CSDDRD) and foundation-wall RSIT (Partie 11) feed the below-grade floor slot (`ASSUMED`). Infiltration n = ACH50 / 20 (`ASSUMED` divisor). Window share is the CSDDRD "percent window of living space wall area" read as window / (window + wall) (`ASSUMED`).
  6. Mean flat area for MFH and AB is measured on the Montréal roll (borough REM21 = Plateau, SUPERFICIE_BATIMENT / NOMBRE_LOGEMENT, taken as total floor area): MFH = 3-4 storeys per period, AB = 5+ storeys pooled (every period cell below 50 records). SFH and TH keep the donor single dwelling.
  7. `build_records` used the C01 ratio fallback on 28 slots over the 24 records (wall_1, wall_2, roof_1, window_1; listed as `RATIO_FALLBACK: <slot>` in each record's `parameter_assumptions`): the donor slot has a negative extra resistance, so the series formula cannot hold. The test lists them instead of requiring none.
- **Notes:** the draft-text caveat and the KR/FI/AM sections sit above the CA section in `TABULA_PROVENANCE.md`; CA was appended last. `scripts/eu22/acquire_montreal.py` was not touched.

#### T03 — Prepare (S3) — completed 2026-10-09

- **Artifacts:** `openubem/outputs/eu_evidence/EU-11/CA-MTL-PLATEAU_dw_2026-10-09/` (idfs 710, `fleet.lst`, `summary.json`, `prepared_buildings.csv`, `excluded_buildings.csv`, `layouts/` 710 side-cars).
- **Result:** attempted 725, prepared 710 (97.9 %), status `PREPARED_FOR_SPEED`; weather `ca_montreal_tmyx_2009_2023.epw`. 15 left out, all `MISSING_CENSUS_UNIT_DATA`. 22 more homes were first blocked by `MISSING_OBSERVED_STOREY_COUNT` and recovered by neighbour imputation (they stay in `excluded_buildings.csv` as history, and are in the prepared 710). Five most common exclusion reasons: only two exist (`MISSING_OBSERVED_STOREY_COUNT` 22 recovered, `MISSING_CENSUS_UNIT_DATA` 15 final).
- **Test status:** every residential building is prepared (710) or listed with a reason (15 final); 710 + 15 = 725. The log line `intersect_match raised IndexError, purging and retrying with match() alone` appeared once, and the run completed.
- **Deviations:** none to the command. Side-cars were added in S5 (see T04).

#### T04 — S4 + S5 — completed 2026-10-09

- **Artifacts:** `openubem/outputs/eu_evidence/EU-11/CA-MTL-PLATEAU_win_2026-10-09/` (idfs 710, `fleet.lst` 710, `md5_2026-10-09.txt` 710, `origin_offset.json`, `windows.csv` 710 rows, `degenerate_2026-10-09.csv`, `division_classes.csv`, `left_out.csv`); `openubem/outputs/eu_evidence/EU-11/integrity_2026-10-02/{CA-MTL-PLATEAU_win_2026-10-09_integrity.csv,summary_win_2026-10-09.csv}`.
- **Result S4:** window assembly 710 rows, 0 errors; degenerate step: 710 IDFs, changed 0, deleted 0, errors 0.
- **Result S5:** integrity I1..I13 failures out of 710: I5 = 1, I6 = 1 (the same home: `CA-MTL-45635-LOT018965`, stem `fad595baeda14882`, I5 value 1, I6 value 0.283), all other checks 0; I13 is `NOT_APPLICABLE_NEW_SITE` (no reference tree). 1 of 710 = 0.14 %, below the 1 % stop. Division: OK 669, V3_divided_wrapped_flat 21, S1_one_flat_per_floor_by_data 11, V1_divided_shape_rule_broken 7, U3_cut_breaks_hard_rule_C4_C5 2; kept (OK / V3 / S1) 701 = 98.7 % (limit 85 %); left out 9. `IDF_FALLBACK` 0 (`class_source` all `LAYOUT_SIDECAR`).
- **Window share vs record share:** median difference 0.000 (to 1e-11); 694 homes hit the record share exactly (0.142 to 0.172); 16 homes have window 0 because their outdoor wall is 0 m2 (fully shared walls), which makes the largest difference equal to the record share (0.172). Integrity I9 passes on all 694 evaluated homes.
- **Deviations:** (1) the emitter for a new site reads `left_out.csv` from the `_dw_` tree, which only the scorer writes (circular): ran `python -m scripts.emit_eu11_layout_sidecars --district CA-MTL-PLATEAU --evidence-root CA-MTL-PLATEAU=<dw tree> --population-manifest CA-MTL-PLATEAU=<dw tree>/prepared_buildings.csv` (documented flag, no code change; already in the debug references from the Cape Town run). A first scorer run before the side-cars gave 710 `IDF_FALLBACK`; it was overwritten by the second run. (2) `12_drop_degenerate.py` was called with `--districts CA --shift CA` (the country code, as in the plan's `cc`).
- **Notes:** `RBAC: access denied` entry from T01 added to `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`.

#### T05 — Plan pages (S6) — completed 2026-10-09 (STOP: manager audit before any run)

- **Artifacts:** `docs/docs_ACTIVE/europeanLocations/plans3D/PLANS_CA-MTL-PLATEAU_2026-10-09.html` (1.79 MB); link row added to `plans3D/index.html`.
- **Result:** the builder writes straight into `plans3D/`, so the page there is the only copy (no separate copy to compare). 710 buildings drawn: PASS 690, GENERIC 11 (the S1 homes), UNRESOLVED 9 (the 9 left-out homes, all flagged), FAIL 0, ERROR 0, UNDIVIDED 0.
- **Test status:** `--verify`: P1 710 of 710; P2 buildings 710 of 710, storeys 1600 of 1600; P3 page parses, EUI keys 0 (no EUI on the page), storey list 710 of 710. No `http(s)://` URL in the page (offline). Verify lists 5 small gross-area differences between zones and page (under 0.5 m2), no storey or dwelling mismatch.
- **Deviations:** the plan writes `--verify` on the build command; the script either builds or verifies, so build and verify were two runs with the same arguments.

#### T06 — Speed (manager) — submitted 2026-10-09
- **Artifacts:** `CA-MTL-PLATEAU_win_2026-10-09/speed_jobs.txt`; Speed fleet `/speed-scratch/o_iseri/fleets/EU22_CA-MTL-PLATEAU_win_2026-10-09/`.
- **Deviations:** none. Owner approval of the page: "montreal looks okay" (2026-10-09); the grey homes the owner named are left-out homes. All 710 IDFs run; the 9 left-out homes are dropped at results by building id.
- **Test status:** staging: fleet.lst 710 = local IDFs 710 = remote IDFs 710. Job 1442166, `--array=1-710%32 --time=7-00:00:00 --mem=32G`. At submission the account CPU cap was held by 4J/5J runs (`AssocGrpCpuLimit`); tasks start as CPUs free.
- **Notes:** results expected over 701 homes.

#### T07 — Harvest and results (S8) — completed 2026-10-10

- **Artifacts:** `openubem/outputs/eu_evidence/EU-11/CA-MTL-PLATEAU_win_2026-10-09/{ca_mtl_plateau_manifest.csv,summary.json}` (harvest); `openubem/outputs/eu_evidence/EU-22/CA-MTL-PLATEAU/results/EU22_results_CA-MTL-PLATEAU_2026-10-09_{per_home.csv,per_home.json,summary.csv,summary.json}`, copied byte-identical (cmp, 4 of 4) to `docs/docs_ACTIVE/europeanLocations/results/`.
- **Result:** Speed job 1442166 (710 tasks COMPLETED) fetched over ssh: 710 task folders, 710 manifest rows, all 710 passed the completion gate (return code 0, "Completed Successfully" in `eplusout.err` and `eplusout.end`), failed 0. Harvest pooled EUI over all 710 runs 136.605 kWh/m2 (includes the 9 left-out homes). Results: 710 - 9 left out = 701 rows, 701 with result, runs without result 0 (`runs_without_result` = []). EUI (space-heating demand only) 140.903 kWh/m2 = 27,297,981.6 kWh over 193,735.7 m2; per home mean 145.4, median 141.8, min 56.5, max 265.7; by type MFH 457 homes 143.8, TH 232 homes 129.5, SFH 12 homes 218.6.
- **Test status:** rows 701 = correctly divided homes (701 kept in T04); every row has a result; the 9 left-out homes are listed in `left_out_not_correctly_divided` (9). Result building ids equal the side-car population ids (701 of 701).
- **Deviations:** none.
- **Notes:** the harvest used the Speed login node for `tar`/`scp` only (no compute). No error solved, nothing added to the debug references.

#### T08 — Viewer and side-cars for 6J (S9) — completed 2026-10-10

- **Artifacts:** `openubem/outputs/3D/eu_CA-MTL-PLATEAU_viewer.html` (926,644 bytes) and `eu_CA-MTL-PLATEAU_data/{buildings.csv,sources.json,index.html}`, mirrored to `docs/docs_ACTIVE/europeanLocations/outputs_3D/` (byte-identical, `cmp` and `diff -rq` empty); side-cars `openubem/outputs/eu_evidence/EU-11/CA-MTL-PLATEAU_win_2026-10-09/layouts/` (701 files) and `sidecar_population.csv` (701 rows); flat counts `CA-MTL-PLATEAU_merged_win_2026-10-09/flat_counts_2026-10-09.csv` (779 rows).
- **Result:** viewer simulated 701 = results rows 701; left out (undivided) 9, no IDF 15, idf_only 0. Flat counts by status: simulated 701, undivided_excluded 9, not_residential 54, no_model 15, run_failed 0. Side-car flat count: `new_count` over simulated = 1,797; `dwellings_used` over the 701 correctly divided homes = 1,797; sum of `dwellings_total` over the 701 side-car JSON files = 1,797. All equal. The viewer shows no EU-21 check badges (0 hit, 710 miss: no evidence file for a new site, as C07 noted).
- **Test status:** `tests/test_eu18c_viewer_geometry_only.py -k CA` = 1 passed. `tests/eu22` = 249 passed, 3 failed (1,340 s). Failures: `test_nocore_sweep.py::test_switches_off_idf_and_sidecar_identical_to_2026_10_09[FI-HEL-KALLIO]` and `::test_sweep_on_five_vienna_homes_score_ok_or_v3` (the switches test passed 3 of 3 when rerun alone; the Vienna test's rerun printed no assertion lines but its pass line was not captured, so treat it as unconfirmed; `openubem/geometry/european_nocore.py` and `scripts/run_eu_s2_district_campaign.py` show as modified in `git status`, another executor's edits); `test_weather_folds.py::test_original_folds_keep_their_year_candidates` (`assert {'kr'} <= {'am','at',...,'za'}`: the fold table now holds `kr`, the test's expected set does not; not touched, reported). None concerns CA.
- **Deviations:** (1) side-cars: `--evidence-root CA-MTL-PLATEAU=<_win_ tree>` as the manager note says; the `_dw_/layouts/` set (710 files) is untouched. (2) The viewer generator also rewrote nothing for the other cities (their files carry older timestamps). The `M` marks on four `sources.json` under `openubem/outputs/3D/` in `git status` predate this run (mtime 2026-10-08).
- **Notes:** no error solved, nothing added to the debug references.
