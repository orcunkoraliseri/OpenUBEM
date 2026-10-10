# PLAN — new neighbourhood: Cape Town, South Africa (`ZA-CPT-WOODSTOCK`)

## 1. Header

- **Slug:** `eu-new-city-ZA-capetown-2026-10-08` · **Date:** 2026-10-08
- **Owner requests (verbatim, 2026-10-08):** "can you prepare implemeantion plan for each new city, lets go …\implementation"; "i will sleep can yo uhandle the plans and executions"; "follow same piplien for new cities as well, floor plan division, window to wall ratio etc."
- **Parent plan:** `PLAN_eu-new-cities-00-common-2026-10-08.md` (§2 rules, §4 decisions, §6.2 steps S3–S9). Read it first.
- **DESIGN pointers:** DR10 brief line 11; DR11 brief lines 21–30; `rules/RULES_dwelling_layout_groups_nocore_2026-10-08.html`.
- **Site:** `ZA-CPT-WOODSTOCK`, country `ZA`, fold `za`, CRS EPSG:32734 (UTM 34 South), MTUS survey year 2010. District: Woodstock / Salt River.
- **Goal:** 500–1,000 residential buildings, same pipeline.
- **Known blockers:** (a) the City's footprint layer states no named licence ("Copyright City of Cape Town"); (b) there is no open per-building year built. Building may proceed for internal checks, but **nothing goes to 6J** until the owner accepts the licence position and the year route (stop points 1 and 3).

## 2. Hard rules for the executor

Common plan §2 rules 1–12, plus: raw downloads only under `openubem/outputs/eu_evidence/EU-22/ZA-CPT-WOODSTOCK/raw/<source>/` (untrusted, `python -I`); the portal's terms text captured verbatim into `…/licences/`; never email or contact the City; no edit to shared files (STOP instead).

## 3. File layout

| Path | Status | Task |
|---|---|---|
| `scripts/eu22/acquire_capetown.py` | new | T01 |
| `tests/eu22/test_acquire_capetown.py`, fixtures | new | T01 |
| `openubem/outputs/eu_evidence/EU-22/ZA-CPT-WOODSTOCK/…` | new | T01 |
| `openubem/outputs/eu02/ZA-CPT-WOODSTOCK/{01_buildings_clean,02_residential_manifest}.gpkg` | new | T01 |
| `openubem/data/construction/national_specs/za_spec.json`, `tabula_archetypes_za.json` | new | T02 |
| `openubem/data/construction/TABULA_PROVENANCE.md` | edit: ZA section | T02 |
| `tests/eu22/test_records_za.py` | new | T02 |

## 4. Dependency decisions (pinned)

- **Footprints + height:** City of Cape Town "2D Building Footprints Low Detail", ArcGIS REST `https://citymaps.capetown.gov.za/agsext/rest/services/Theme_Based/ODP_SPLIT_12/MapServer/11` (the `ODP_SPLIT_n` folder is renumbered from time to time: list `Theme_Based/` first and find the layer by name), `f=geojson`, 2,000 records per page. `BLD_HGHT` = mean roof height from the 2023 LiDAR (provenance `CPT_LIDAR_2023_MEASURED`). Storeys = `max(1, round(BLD_HGHT / 3.0))` (D-EU-154). Source CRS Hartebeesthoek94 / Lo19 (confirm the EPSG code from the service's spatial reference).
- **Residential use:** no open zoning layer. A footprint is residential when OSM marks it residential (building tags `house`, `terrace`, `apartments`, `residential`, `semidetached_house`, `detached`), or when it lies inside OSM `landuse=residential` and OSM marks it as nothing else. Footprints with `BLD_HGHT` < 2.0 m are dropped as sheds (not a home). Report the count by each route. OSM tags `terrace` / `detached` / `apartments` pass through as `building_tag`.
- **Year built — no rule yet.** Look, in this order, for: (a) a City heritage inventory or heritage overlay layer with a period / date per site; (b) OSM `start_date`; (c) any other open per-building or per-block age source. Report coverage of each. If none reaches 50 % of residential buildings → STOP at point 1; the owner decides (for example one assumed period for the whole area). Do not assign years without that ruling.
- **Sub-unit:** City "Official Planning Suburbs" (or Stats SA 2022 sub-places) covering Woodstock, Salt River, Observatory, ranked by residential buildings per km², densest first; D-EU-151.
- **Amendment 2026-10-08 night (manager, after T01 stop):**
  - **Level below the suburb:** Woodstock holds 1,115 (>1,000), so the next level is street blocks inside Woodstock. Blocks are polygons bounded by OSM `highway` lines, built the same way as the Yerevan T01 script (reuse it by import or copy its block function into `acquire_capetown.py`). They are ranked by residential buildings per km², densest first, and touching blocks are added nearest centroid first until ≥500, never >1,000 (D-EU-151).
  - **Year from heritage period labels:** normalise "C" to "Century". Century N covers (N−1)·100 to (N−1)·100+99. "Early" is +0 to +32, "Mid" +33 to +66, "Late" +67 to +99, and "Early-Mid" +0 to +66. "17th-18th" is 1600–1799, and "Early-Mid 19th" is 1800–1866. The reference year is the midpoint rounded down; for example "Early 20th" gives 1916 and "Mid 20th" gives 1949. A label whose range starts after the survey year 2010 ("Mid 21st Century", 10 sites) gives no year.
  - **How labels are written:** each labelled building gets `census_unit_id` = `HERITAGE:<site id>`, `census_period_counts` = `{label: 1}`, and the label→year map goes into the report's `period_years`. A building with no label gets its street block's label counts (`census_unit_id` = `BLOCK:<id>`); a tie means no year, and the building is excluded under D-EU-154. Year provenance follows the census rung, never `_OBSERVED`.
  - **Licence:** the City licence text says non-commercial and no redistribution without permission. Building and running go ahead. Nothing from Cape Town goes to 6J until the owner rules (stop point 3).
- **Construction (D-EU-152), donor ES.** Periods: `ZA.01` ≤1950 (older masonry), `ZA.02` 1951–2011 (no thermal requirement), `ZA.03` 2012+ (SANS 10400-XA, climate zone 4). Values: roof total R 3.7 m²K/W for zone 4 (SANS 10400-XA, two sources agree — cite both); walls: the feasibility sources conflict (0.35 … 2.2 W/m²K) — find the deemed-to-satisfy wall rule in SANS 10400-XA / SANS 204 text and cite it, else `ASSUMED` with the reason; pre-2011 walls / roofs from a cited South African study (CSIR or the Stellenbosch 2016 typology thesis, handle 10019.1/100440), else donor `ASSUMED`. Windows: single glazing for ZA.01–02 unless a source says otherwise.

## 5. Facts with citations

- Common plan §5.
- Layer facts (1,444,950 polygons metro-wide, 99.98 % with a height, fields `DATA_SRC`, `ACQS_PRD`, `ACQS_MTHD`, `BLD_HGHT`) from the feasibility research (2026-10-08).
- Weather fold `za`, UTC +2, survey year 2010 (southern-hemisphere winter in June–August; no change to the converter).

## 6. Tasks

#### T01 — Acquire and clip Cape Town
**How.** Page through the layer for the suburbs' bounding box; save raw pages; reproject to EPSG:32734; fetch OSM buildings + landuse for the same box (Overpass, saved raw); residential rule; year search per §4 (report only); `SCHEMA_COLUMNS` (`osm_id` = `ZA-CPT-<OBJECTID>`); `finalize_footprints`; sub-units; clip; `split_residential`; `write_manifests`; report.
**How to test.** Fixture: paging stops at the last page; height → storeys; the residential rule per route; < 2.0 m dropped; CRS EPSG:32734. Live: count 500–1,000; coverage lines; year coverage per source.

#### T02 — South African construction records
As Helsinki T02 with donor ES, periods of §4, tests in `tests/eu22/test_records_za.py`.

#### T03 — Prepare (S3) · T04 — S4 + S5 · T05 — Plan pages (S6, then STOP) · T06 — Speed (manager) · T07 — S8 · T08 — S9
Common plan §6.2 with `SITE=ZA-CPT-WOODSTOCK`, `cc=ZA`, only after the owner's ruling on the year route. S9 side-cars for 6J only after the owner's ruling on the licence. **Manager note 2026-10-09:** year route accepted (D-EU-161) and licence cleared (D-EU-160); T03 starts once the `za` weather fold is pinned.

## 7. Stop-and-report points

1. After T01 + T02 (licence text, year coverage, owner ruling needed). 2. After T05. 3. Before S9 side-cars (licence ruling).

## 8. Progress log

(One entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes.)

#### T02 — South African construction records — completed 2026-10-08

- **Artifacts:** `openubem/data/construction/national_specs/za_spec.json`; `openubem/data/construction/tabula_archetypes_za.json` (12 records, built by `national_records.build_records`); `tests/eu22/test_records_za.py`; ZA section appended to `openubem/data/construction/TABULA_PROVENANCE.md`.
- **Deviations:** (1) ZA.02 MFH donor is `ES.ME.MFH.04`, not ES.05 (the ES.05 MFH record has zero window area and a non-numeric window U, so wwr rescale is impossible). (2) The Stellenbosch 2016 thesis (hdl 10019.1/100440) full text was blocked (HTTP 429); only its abstract was read, so pre-2011 walls, roof, window, infiltration and window share are `ASSUMED` with reasons. (3) The 0.35 masonry wall minimum was seen only in a search summary of a municipal report and was not used. (4) Window share is the 15 % of net floor area rule (SANS 10400-XA 4.4.4.1) converted with donor geometry, applied to all periods as `ASSUMED`. (5) No building-type list from T01 exists yet, so all four types were built.
- **Test status:** `python -m pytest tests/eu22/test_records_za.py` 11 passed; `tests/eu22` 154 passed. Key set equals IT; periods tile 0..1950, 1951..2011, 2012..9999; U wall, roof, window never increase with newer period; shares 0.08-0.49; every override carries a source or `ASSUMED:`; committed JSON equals a rebuild.
- **Notes:** `_TABULA_PERIODS["ZA"]` for C03 = `((0, 1950, "ZA.01"), (1951, 2011, "ZA.02"), (2012, 9999, "ZA.03"))`. Sourced values (NHBRC Technical Guidelines Energy Efficiency, Tables 1, 2, 4, 5; Swartland article for the roof): roof ZA.03 R 3.7 (U 0.2703, zone 4); brick wall total R 0.42 (U 2.381). The conflict 0.35 ... 2.2 resolves as: 1.9 / 2.2 are non-masonry limits. Roof 3.7 is also quoted by the Swartland article, while the 2013 GreenCape slide states a 2.7-3.5 range; the NHBRC table (3.7 for zones 1 and 4) was used. Type x period table (U wall / U roof / U window / window share):

| Type | ZA.01 (<=1950) | ZA.02 (1951-2011) | ZA.03 (2012+) |
|---|---|---|---|
| AB | 2.381 / 2.632 / 5.35 / 0.216 | 2.381 / 2.632 / 5.35 / 0.487 | 2.381 / 0.270 / 5.35 / 0.201 |
| MFH | 2.381 / 2.632 / 5.35 / 0.214 | 2.381 / 2.632 / 5.35 / 0.109 | 2.381 / 0.270 / 5.35 / 0.227 |
| SFH | 2.381 / 2.632 / 5.35 / 0.106 | 2.381 / 2.632 / 5.35 / 0.081 | 2.381 / 0.270 / 5.35 / 0.091 |
| TH | 2.381 / 2.632 / 5.35 / 0.090 | 2.381 / 2.632 / 5.35 / 0.199 | 2.381 / 0.270 / 5.35 / 0.214 |

#### T02 (amended) — South African window share from donor — completed 2026-10-08

- **Artifacts:** `openubem/data/construction/national_specs/za_spec.json` (every `wwr` entry removed); `openubem/data/construction/tabula_archetypes_za.json` (rebuilt); ZA section of `openubem/data/construction/TABULA_PROVENANCE.md`; `tests/eu22/test_records_za.py`.
- **Deviations:** Manager ruling replaces T02 deviation (4): converting "15 % of floor area" through the Spanish donor geometry gave shares 0.08-0.49 that reflect the donor building, so South Africa keeps the donor window share, as Finland, Korea and Armenia do. Tests: wwr pin removed from `test_overrides_land_in_records`; share range widened to 0.05-0.55 (donor AB.02 share is 0.522).
- **Test status:** `python -m pytest -q tests/eu22/` = 160 passed.
- **Notes:** window share min 0.067, median 0.194, max 0.522 (ASSUMED, donor). The share column of the type x period table in the first T02 entry is superseded by these values.

#### T01 — Acquire and clip Cape Town — STOPPED 2026-10-08 (district-size rule: first unit over the cap; manifests not written)

- **Artifacts:** `scripts/eu22/acquire_capetown.py` (stages `download`, `osm`, `build`); `tests/eu22/test_acquire_capetown.py` (16 tests, no fixture files, frames built in code); evidence under `openubem/outputs/eu_evidence/EU-22/ZA-CPT-WOODSTOCK/`: `raw/cct_footprints/` (4 pages + layer metadata), `raw/cct_suburbs/`, `raw/cct_heritage/`, `raw/osm/` (36 Overpass tiles, sha256 in `osm_tiles_sha256.json`), `licences/` (`CCT_footprints_use_limitation.txt`, layer metadata XML, OSM copyright page, ODbL 1.0 page), `acquisition_report.json`; `openubem/outputs/eu02/ZA-CPT-WOODSTOCK/01_buildings_clean.{gpkg,log,schema.json}` (6,472 buildings of the three-suburb box, nothing clipped). NOT written: `boundary.geojson`, `02_residential_manifest.gpkg`.
- **Stop reason (D-EU-151, quoted):** "If it holds more than 1,000, go one statistical level down … take the unit named first in the city plan's ranked list … never pass 1,000." Units used with running counts (residential buildings, densest first): WOODSTOCK 1,115 (350.6/km2) → OBSERVATORY 965 (275.7) → SALT RIVER 283 (102.5); named three together 2,363. The first unit, Woodstock, already holds 1,115 > 1,000, and the plan names no level below the suburb (Stats SA 2022 sub-places are named only as an alternative to the suburbs, not as a level below). No clipping done. Owner or manager ruling needed.
- **Residential count:** 3,731 of the 6,472 buildings in the box are residential (all three suburbs and surroundings): 1,516 by route (a) OSM residential tag, 2,215 by route (b) untagged inside OSM `landuse=residential`. Sheds dropped (height < 2.0 m): 99; 300 more removed by the shared cleaner (area < 20 m2 or duplicate overlap). Per-site route counts are not yet available (no clip).
- **Coverage (residential, three suburbs, n = 2,363):** storeys 100 % (from `BLD_HGHT`, `max(1, round(h / 3.0))`, provenance `CPT_LIDAR_2023_HEIGHT_DERIVED`; no height missing); height 100 % (2023 LiDAR mean roof height, `DATA_SRC` LiDAR 6,574 / aerial imagery 297 of 6,871); year built 0 % assigned (none assigned, per plan).
- **Year search (report only):** (a) City Heritage Inventory (`ODP_SPLIT_3` layer 2, field `PRD`, a period label, not a year): 2,021 of 2,363 = 85.5 % by representative point; Heritage Inventory Objects (layer 1): 0; (b) OSM `start_date`: 2 = 0.08 %; (c) no other open per-building age source found (web search; City open data portal lists no year-built layer; the City's building footprint layers carry only acquisition period). Best single source 85.5 % ≥ 50 %, so the year STOP rule is not triggered. Period labels (13 values: "Early 20th C" 734, "Early-Mid 20th Century" 555, "Early 20th Century" 168, "Mid 20th C" 164, "Late 19th C" 125, "Mid 20th Century" 119, "Late 20th Century" 61, "Late 19th Century" 41, "Early 21st Century" 28, "Mid 21st Century" 10, "17th-18th C" 8, "Early-Mid 19th C" 6, "17th-18th Century" 2) still need a rule that turns a label into a year; the plan has none, so no year was written.
- **Licence (captured 2026-10-08, layer metadata `resConst/useLimit`, verbatim in `licences/CCT_footprints_use_limitation.txt`):** "No restrictions on the digital file for non-commercial purposes. All rights reserved. No part of this data may be reproduced or transmitted in any form or by any means … without permission from the City of Cape Town Geomatics Branch. Where the data is used as a basis for or as an insertion in a map, acknowledgment must be made to the source of such data as well as the copyright of the CCT." No named licence (no CC / OGL identifier); non-commercial wording, no redistribution without permission. ~~Stop point 3 stands.~~ **Manager note 2026-10-09:** stop point 3 cleared by D-EU-160 (6J is the owner's own project); conditions in common plan §4.
- **Deviations:** (1) Footprints fetched for the bounding box of the three named suburbs (+150 m) only, not the wider box including touching suburbs, because the server needs about 40-60 s per 2,000-record page and returned 503 on the large box; touching suburbs are therefore not downloaded (they would be needed only for the "fewer than 500" expansion, which does not apply). (2) Overpass requested in a 6x6 tile grid with `[timeout:180]` (the full-box query and the `maxsize` header were refused). (3) "Nothing else" for route (b) read as: no matched OSM building, or matched `building=yes` with none of the keys amenity / shop / office / tourism / leisure / industrial / craft / man_made / healthcare / military / emergency / public_transport / railway / power / historic; an OSM footprint match needs the OSM polygon to cover at least 50 % of the City footprint. (4) Source CRS: the service WKT is Transverse Mercator, central meridian 19, WGS84 ellipsoid, datum Hartebeesthoek94 (Lo19 grid); the server was asked for `outSR=4326` and the result reprojected to EPSG:32734 (confirmed `clean.crs` = EPSG:32734). (5) Added manifest-side field `heritage_period` (only in the code path after the stop; not yet produced).
- **Test status:** `python -m pytest tests/eu22/test_acquire_capetown.py` 16 passed (paging stops at last page, exact-multiple page, transfer-limit flag; height to storeys; sheds < 2.0 m dropped; residential rule per route; untagged outside landuse not residential; tag pass-through; CRS EPSG:32734). Live run reached the sub-unit step and stopped as above.
- **Notes:** 3 debug-reference entries added (Overpass header 504, ArcGIS 503 on a large box, empty Overpass tile). Next after a ruling on the district rule: re-run `python -I scripts/eu22/acquire_capetown.py build`, which then writes the boundary, clip, split and `02_residential_manifest.gpkg`. T02 is already logged above.

#### T01 (rerun after amendment) — Acquire and clip Cape Town — completed 2026-10-08

- **Artifacts:** `scripts/eu22/acquire_capetown.py` (new stage `highways`; `label_year`, `heritage_site`, `own_heritage`, `street_block_ids`, `attach_census`, `period_years_for`, `year_split`, `blocks_used`; `street_blocks` / `choose_blocks` / `ROAD_CLASSES` imported from `scripts/eu22/acquire_yerevan.py`, unedited); `tests/eu22/test_acquire_capetown.py` (34 tests); new raw folder `openubem/outputs/eu_evidence/EU-22/ZA-CPT-WOODSTOCK/raw/osm_highways/` (9 Overpass tiles of a 3x3 grid, queries, `download_log.json` with sha256); `openubem/outputs/eu_evidence/EU-22/ZA-CPT-WOODSTOCK/{boundary.geojson,boundary.sha256,acquisition_report.json}`; `openubem/outputs/eu02/ZA-CPT-WOODSTOCK/{01_buildings_clean.gpkg,02_residential_manifest.gpkg,02_excluded_manifest.gpkg,02_exclusion_counts.json}`. Existing raw downloads reused unchanged.
- **Blocks used (D-EU-151, inside WOODSTOCK, 1,115 residential, densest per km2 first, then touching blocks nearest centroid first):** 1239 highway ways (motorway, trunk, primary, secondary, tertiary, residential, motorway_link, trunk_link, primary_link, secondary_link, tertiary_link) gave 310 blocks; 43 used, residential added = running total: B0003 +18 = 18, B0011 +8 = 26, B0002 +20 = 46, B0009 +21 = 67, B0014 +18 = 85, B0007 +6 = 91, B0015 +15 = 106, B0010 +19 = 125, B0008 +11 = 136, B0031 +12 = 148, B0006 +18 = 166, B0024 +9 = 175, B0036 +33 = 208, B0012 +10 = 218, B0017 +21 = 239, B0004 +19 = 258, B0005 +19 = 277, B0022 +17 = 294, B0019 +11 = 305, B0016 +22 = 327, B0023 +18 = 345, B0025 +11 = 356, B0020 +24 = 380, B0021 +15 = 395, B0028 +11 = 406, B0013 +0 = 406, B0027 +15 = 421, B0180 +0 = 421, B0026 +7 = 428, B0112 +0 = 428, B0175 +0 = 428, B0039 +0 = 428, B0113 +0 = 428, B0040 +14 = 442, B0114 +0 = 442, B0109 +0 = 442, B0176 +0 = 442, B0000 +0 = 442, B0030 +28 = 470, B0029 +28 = 498, B0001 +0 = 498, B0111 +0 = 498, B0037 +36 = 534. Stopped at the first total of 500 or more: **534**. No block skipped for the 1,000 cap. Boundary area 0.5702 km2.
- **Residential count:** 534 residential in the manifest (572 footprints clipped; 38 non-residential, 0 unknown). Routes: 357 OSM residential tag, 177 untagged inside `landuse=residential`. Sheds under 2.0 m dropped earlier: 99.
- **Year coverage (534 residential):** own heritage label with a year 474 (88.76 %); block label with a year 51 (9.55 %); no year 9 (1.69 %) = 6 own label "Mid 21st Century" (no year by rule) + 3 block ties. Census columns: 480 `HERITAGE:<site id>` (all with a label; 480 of 534 = 89.9 %), 54 `BLOCK:<id>`. `year_built` stays empty (no `_OBSERVED` year). `period_years` written to the report: {"Early 20th C": 1916, "Early 20th Century": 1916, "Early 21st Century": 2016, "Early-Mid 20th Century": 1933, "Late 19th C": 1883, "Late 19th Century": 1883, "Late 20th Century": 1983, "Mid 20th C": 1949, "Mid 20th Century": 1949}; no year: ['Mid 21st Century'].
- **Storeys and height coverage:** storeys 534 of 534 (100 %, `max(1, round(BLD_HGHT / 3.0))`, provenance `CPT_LIDAR_2023_HEIGHT_DERIVED`); height 534 of 534 (100 %, 2023 LiDAR). Storeys: 1 -> 50, 2 -> 421, 3 -> 62, 4 -> 1. Types: house 354, apartments 3, untagged 177.
- **Deviations:** (1) Road classes are the Yerevan list (no `unclassified`, `living_street` or `service`); the City's OSM roads gave 310 blocks, many small (6-36 residential each), so 43 blocks were needed. (2) `choose_blocks` takes its expansion pool from all touching blocks, not only those inside Woodstock: two chosen blocks lie mostly outside it (B0013 0.7 % inside, B0176 18.3 % inside), both with 0 residential; B0109 is 87.8 % inside; every other chosen block is at least 99.8 % inside. (3) Rule read literally: "Early 21st Century" (2000-2032) gives 2016, later than the survey year 2010 and in period ZA.03 (2012+); 11 own-label buildings carry it, plus any block that leads with it. The rule only voids labels whose range starts after 2010. (4) Block label counts use labelled residential buildings only (all labels, including "Mid 21st Century"); a block whose leading label has no year gives no year. (5) Heritage Inventory Objects layer matched 0 buildings; the `HERITAGE:OBJ<id>` fallback prefix exists but was never used. (6) Previous report keys `year_stop` and the district-size STOP were replaced by the block rule.
- **Test status:** `python -m pytest -q tests/eu22/test_acquire_capetown.py` = 34 passed (13 labels -> year or none; unreadable labels; unlabeled building takes its block's counts and non-residential labels are not counted; `period_years` map; year split; block selection stops at the first total of 500 or more: 240 + 200 + 150 = 590, not 5 blocks).
- **Notes:** Licence position unchanged (stop point 3): nothing from Cape Town goes to 6J until the owner rules. Build command: `python -I scripts/eu22/acquire_capetown.py build` (highways: `... highways`). Manifest carries `census_unit_id`, `census_period_counts`, `heritage_period`.

#### T03 — Prepare (S3) — completed 2026-10-09

- **Artifacts:** `openubem/outputs/eu_evidence/EU-11/ZA-CPT-WOODSTOCK_dw_2026-10-09/` (`prepared_buildings.csv`, `excluded_buildings.csv`, `summary.json`, `fleet.lst`, `idfs/` 525, `schedules/`, `weather/`, `za_cpt_woodstock_manifest.csv`).
- **Deviations:** none. Weather was the pinned registry file `za_capetown_tmyx_2009_2023.epw` (sha256 5c045a95...b67f; typical year, D-EU-163).
- **Test status:** 534 attempted, 525 prepared (98.3 %, above the 80 % bar), 9 excluded; every residential building is prepared or listed. Exclusion reasons (only two): `UNMAPPABLE_PERIOD_Mid_21st_Century` 6 (label with no year, by rule), `CENSUS_UNIT_PERIOD_TIE_Early_20th_C_Late_19th_C` 3 (street-block tie, no year, D-EU-154). Imputation recovered 0.
- **Notes:** one process, no EnergyPlus run.

#### T04 — Finish the tree (S4) and integrity sweep with division classes (S5) — completed 2026-10-09

- **Artifacts:** `openubem/outputs/eu_evidence/EU-11/ZA-CPT-WOODSTOCK_win_2026-10-09/` (525 IDFs, `fleet.lst` 525, `md5_2026-10-09.txt` 525, `origin_offset.json` dx 263000 / dy 6241000 EPSG:32734, `windows.csv` 525, `dwelling_counts_2026-10-09.csv`, `division_classes.csv`, `left_out.csv`, `degenerate_2026-10-09.csv`); `ZA-CPT-WOODSTOCK_dw_2026-10-09/layouts/` (525 side-cars); integrity table `openubem/outputs/eu_evidence/EU-11/integrity_2026-10-02/ZA-CPT-WOODSTOCK_win_2026-10-09_integrity.csv`.
- **Deviations:** the side-car emitter was run with `--population-manifest ZA-CPT-WOODSTOCK=<dw tree>/prepared_buildings.csv`, because for a new site it otherwise reads `left_out.csv`, which the scorer writes afterwards (circular; debug reference added). Side-cars first, then scorer, as in the C06 amendment.
- **Test status:** degenerate IDFs 0 (changed 0, deleted 0, errors 0). Integrity failures out of 525: I1, I2, I4, I5, I6, I9, I10, I11, I12, I13 = 0; I3 = 1 and I7 = 1 (both ZA-CPT-75823, 0.19 %; below the 1 % bar). `IDF_FALLBACK` 0 (525 `LAYOUT_SIDECAR`). Classes: OK 507, V3_divided_wrapped_flat 14, S1_one_flat_per_floor_by_data 3, V1_divided_shape_rule_broken 1 (ZA-CPT-74724, left out). Correctly divided 524 of 525 = 99.8 % (bar 85 %). Window share, measured vs record: median difference 3e-12, largest 0.099; only 2 homes differ by more than 0.01 (ZA-CPT-74340 and ZA-CPT-74701, target 0.099, achieved 0: no window placed).
- **Notes:** left out of results: 1 home. `windows.csv` `u` is 4.4 for 429 homes (record-derived value including thermal-bridge handling by the window module), not checked against the T02 5.35 table; flagged for the manager.

#### T05 — Plan pages (S6) — completed 2026-10-09

- **Artifacts:** `docs/docs_ACTIVE/europeanLocations/plans3D/PLANS_ZA-CPT-WOODSTOCK_2026-10-09.html` (1.15 MB, written directly into `plans3D/`, so no separate copy); row added to `plans3D/index.html` with the credit "City of Cape Town" and an internal-use note. The four existing pages were not touched (mtimes 10-08).
- **Deviations:** none. `--verify` run after the build.
- **Test status:** build line: 525 buildings, PASS 520, FAIL 1, GENERIC 3, ERROR 0, UNDIVIDED 0, UNRESOLVED 1. Verify: P1 525 of 525; P2 buildings 525 of 525, storeys 1062 of 1062; P3 page parses, 0 EUI keys, storey list 525 of 525. No external URL in the page. The left-out home (ZA-CPT-74724) carries the badge "FLOOR PLAN NOT RESOLVED - LEFT OUT OF RESULTS". `python -m pytest -q tests/eu22`: 238 passed.
- **Notes:** STOP point 2 reached. Manager audit before any run. Nothing submitted to Speed, no EnergyPlus run.

#### T06 — Speed (manager) — submitted 2026-10-09
- **Artifacts:** `ZA-CPT-WOODSTOCK_win_2026-10-09/speed_jobs.txt`; Speed fleet `/speed-scratch/o_iseri/fleets/EU22_ZA-CPT-WOODSTOCK_win_2026-10-09/`.
- **Deviations:** none. Owner approval of the page: "yes okay keep goin with cape town" (2026-10-09). All 525 IDFs run; the 1 left-out home (ZA-CPT-74724) is dropped at results by building id.
- **Test status:** staging: fleet.lst 525 = local IDFs 525 = remote IDFs 525. Job 1442187, `--array=1-525%32 --time=7-00:00:00 --mem=32G`. Account CPU cap held mostly by 4J/5J runs at submission; tasks start as CPUs free.
- **Notes:** results expected over 524 homes. City of Cape Town footprints stay internal; never published.

#### T07 — Harvest and results (S8) — completed 2026-10-10

- **Artifacts:** `openubem/outputs/eu_evidence/EU-11/ZA-CPT-WOODSTOCK_win_2026-10-09/{za_cpt_woodstock_manifest.csv,summary.json}` (harvest, 525 rows); `openubem/outputs/eu_evidence/EU-22/ZA-CPT-WOODSTOCK/results/EU22_results_ZA-CPT-WOODSTOCK_2026-10-09_{per_home.csv,per_home.json,summary.csv,summary.json}`; byte-identical copies in `docs/docs_ACTIVE/europeanLocations/results/` (4 of 4 `cmp` equal).
- **Deviations:** none. Fetch went over ssh with the `bash -lc` wrapper; nothing ran on the Speed login node.
- **Test status:** job 1442187: 525 task directories extracted, run 525, success 525 (return code 0, "Completed Successfully" in `eplusout.err` and `eplusout.end`), failed 0. Manifest rows 525; left out 1 (ZA-CPT-74724, V1); kept 524; with result 524; runs without result 0. Rows = correctly divided homes (524). EUI (heating only, ideal loads): 54.151969 kWh/m2 over 265,365.19 m2 (14,370,047.655 kWh); per-home min 21.10, median 57.21, max 149.76. The harvest's own pooled figure over all 525 homes (including the left-out home) is 54.0661; the published figure is the 524-home one.
- **Notes:** the EUI is space heating only and this is the first southern-hemisphere site on the `za` typical-year file; do not compare with the four fleet sites without that caveat.

#### T08 — Viewer and side-cars (S9) — completed 2026-10-10

- **Artifacts:** `openubem/outputs/3D/eu_ZA-CPT-WOODSTOCK_viewer.html` (567,439 bytes) and `eu_ZA-CPT-WOODSTOCK_data/{buildings.csv,index.html,sources.json}`, mirrored byte-identical (`cmp`/`diff -rq` clean) to `docs/docs_ACTIVE/europeanLocations/outputs_3D/`; `…/ZA-CPT-WOODSTOCK_win_2026-10-09/{layouts/ (524 side-cars),sidecar_population.csv (524 rows)}`; `…/ZA-CPT-WOODSTOCK_merged_win_2026-10-09/flat_counts_2026-10-09.csv` (572 rows). Debug reference bullet extended (same circular `left_out.csv` error, now at S9). Internal only: nothing published, nothing sent to 6J.
- **Deviations:** (1) The plan's `--district SITE …` for the side-car step was read as `--evidence-root SITE=<win tree>`: `left_out.csv` and the harvested manifest are in the `_win_` tree, so the `_dw_` tree fails with `FileNotFoundError ... left_out.csv`. The 525 earlier side-cars in `_dw_/layouts/` (S5) were not touched; the post-run set is in `_win_/layouts/`. (2) The viewer was built with no EU-21 check badges (join 0 hit / 525 miss), as in the C07 notes. (3) The viewer's geometry note shows an empty "( tree;" where a tree name should be (template text, cosmetic, not fixed here).
- **Test status:** viewer simulated count 524 = results rows 524 (idf_only 0, no_idf 9, undivided/left out 1). Flat counts: simulated 524, run_failed 0, undivided_excluded 1, not_residential 38, no_model 9. Side-car flat count: sum of `new_count` over simulated = 1,036 = sum of `dwellings_used` in `sidecar_population.csv` (524 homes) = sum of `dwellings_total` over the 524 side-car JSONs = 1,036. `python -m pytest -q tests/test_eu18c_viewer_geometry_only.py -k ZA` = 1 passed. `python -m pytest -q tests/eu22` = 233 passed, 1 failed: `test_weather_folds.py::test_original_folds_keep_their_year_candidates` (`'kr'` appears in the registry targets but not in the test's expected set). The failure comes from the uncommitted Korea weather-registry change, not from Cape Town; not touched.
- **Notes:** the 9 homes with no IDF are the 9 excluded at prepare (6 "Mid 21st Century" label, 3 block ties).
