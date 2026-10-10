# PLAN — new neighbourhood: Helsinki, Finland (`FI-HEL-KALLIO`)

## 1. Header

- **Slug:** `eu-new-city-FI-helsinki-2026-10-08` · **Date:** 2026-10-08
- **Owner requests (verbatim, 2026-10-08):** "can you prepare implemeantion plan for each new city, lets go …\implementation"; "i will sleep can yo uhandle the plans and executions"; "follow same piplien for new cities as well, floor plan division, window to wall ratio etc."
- **Parent plan:** `PLAN_eu-new-cities-00-common-2026-10-08.md` — its §2 rules, §4 decisions and §6.2 steps S3–S9 apply unchanged. Read it first.
- **DESIGN pointers:** DR10 brief line 11; DR11 brief lines 21–30; `rules/RULES_dwelling_layout_groups_nocore_2026-10-08.html`.
- **Site:** `FI-HEL-KALLIO`, country `FI`, fold `fi`, CRS EPSG:32635, MTUS survey year 2009. District: Kallio (Helsinki district 11 and its peruspiiri).
- **Goal:** 500–1,000 residential buildings, same pipeline as the four cities. Helsinki has observed storeys, years and dwelling counts per building, so it should be the cleanest of the seven.

## 2. Hard rules for the executor

Common plan §2 rules 1–12, plus: raw downloads only under `openubem/outputs/eu_evidence/EU-22/FI-HEL-KALLIO/raw/<source>/` (untrusted data, `python -I`); licence text captured into `…/licences/`; no edit to any shared file of the common plan §3 (STOP and report instead).

## 3. File layout

| Path | Status | Task |
|---|---|---|
| `scripts/eu22/acquire_helsinki.py` | new | T01 |
| `tests/eu22/test_acquire_helsinki.py`, `tests/eu22/fixtures/helsinki_*.json` | new | T01 |
| `openubem/outputs/eu_evidence/EU-22/FI-HEL-KALLIO/…` | new | T01 |
| `openubem/outputs/eu02/FI-HEL-KALLIO/{01_buildings_clean,02_residential_manifest}.gpkg` | new | T01 |
| `openubem/data/construction/national_specs/fi_spec.json` | new | T02 |
| `openubem/data/construction/tabula_archetypes_fi.json` | new | T02 |
| `openubem/data/construction/TABULA_PROVENANCE.md` | edit: FI section | T02 |
| `tests/eu22/test_records_fi.py` | new | T02 |

## 4. Dependency decisions (pinned)

- **Buildings:** Helsinki WFS `https://kartta.hel.fi/ws/geoserver/avoindata/wfs`, layer `avoindata:Rakennukset_alue_rekisteritiedot`, EPSG:3879. Licence expected CC BY 4.0 — capture the text from the Helsinki map service / HRI page; if the licence is not open, STOP.
- **Fields:** `i_kerrlkm` storeys, `c_valmpvm` completion date (year = first 4 digits), `i_asuinhuoneistojen_lkm` dwellings (→ `observed_dwellings`), `c_kayttark` use class. Provenance `HELSINKI_REKISTERI_OBSERVED`. If a field name differs on the live layer, use the live one and record it.
- **Use / type:** Finnish building classification codes in `c_kayttark`: `011` → `detached`; `021`, `022` → `terrace`; `032` → `apartments`; other residential codes (`012`, `013`, `039`, `041` and any code the layer labels as residential) → residential with an empty tag, typed by D-EU-154. Non-residential codes are dropped by `split_residential` (set `function_tag` from the code label). Read the code list the layer uses and record the mapping table in the report.
- **Height:** not needed when storeys are observed; if the layer has a height field, keep it as `height_m`.
- **Sub-unit:** osa-alue (sub-district) boundaries from the Helsinki district WFS layer (`avoindata:Maavesi_osa_alueet` or the layer the service lists for "osa-alue"), inside the Kallio peruspiiri, ranked by residential buildings per km², densest first; D-EU-151. **Amendment 2026-10-08 night (manager, after T01):** the peruspiiri holds 458 (<500), so per the amended D-EU-151 keep the whole Kallio peruspiiri and add touching osa-alue from outside it, nearest centroid first, until ≥500. A building with no `c_kayttark` whose `tyyppi` is `Asuinrakennus` is residential (`function_tag` = `tyyppi:Asuinrakennus`), type by D-EU-154.
- **Construction (D-EU-152), donor SE.** Periods (from the Finnish building code C3 editions): `FI.01` ≤1975, `FI.02` 1976–1977, `FI.03` 1978–1984, `FI.04` 1985–2002, `FI.05` 2003–2007, `FI.06` 2008–2009, `FI.07` 2010+. U-values from the Ministry of the Environment C3 thermal-insulation code editions (1976, 1978, 1985, 2003, 2007, 2010) for walls, roofs, ground floors and windows; values for ≤1975 from a cited Finnish existing-stock study (search: VTT or Aalto "Finnish residential building stock U-values by construction year"; the Aalto building material inventory dataset). Window g-value, infiltration and window share: cite Finnish sources; else donor `ASSUMED`. Mean flat area per type from Statistics Finland dwellings by building type (cite the table).

## 5. Facts with citations

- Common plan §5.
- Field list from the feasibility research (2026-10-08): `i_kerrlkm`, `c_valmpvm`, `i_asuinhuoneistojen_lkm`, `c_kayttark`.
- No TABULA data exists for Finland (workbook country list measured 2026-10-08: AT BE BG CY CZ DE DK ES FR GB GR HU IE IT NL NO PL RS SE SI).

## 6. Tasks

#### T01 — Acquire and clip Helsinki

**What / Why.** As Vienna T01: one script, raw saved, standard manifests, report. Pipeline step 1.

**How.** Download the building layer for the Kallio peruspiiri bounding box (paged), reproject to EPSG:32635, map fields per §4 into `SCHEMA_COLUMNS` (`osm_id` = `FI-HEL-<building id field>`; `observed_dwellings` column added), `finalize_footprints`, choose sub-units by D-EU-151, clip, `split_residential`, `write_manifests`. No census columns are needed if year coverage is ≥ 98 %; if lower, report and STOP (the manager decides whether a census route is needed).

**How to test.** `tests/eu22/test_acquire_helsinki.py` on a 20-feature fixture: schema complete; `c_valmpvm` "1928-01-01"-style and year-only forms both parse; `i_kerrlkm = 0` or null → no observed storeys; code mapping per §4; CRS EPSG:32635. Live: count in 500–1,000; coverage lines for storeys, year, dwellings, use.

#### T02 — Finnish construction records

**What.** Write `national_specs/fi_spec.json` (every value with `source` or `ASSUMED:`), build `tabula_archetypes_fi.json` with `national_records.build_records` (common C01), add the FI section to `TABULA_PROVENANCE.md` with the full source list.

**Why.** D-EU-152.

**How.** One entry per building type present in the site (SFH, TH, MFH, AB) × period of §4. Donor = the SE record of the same type whose period overlaps most (record the pairing). Use web search to find the C3 editions' required U-values; quote the table/page in `source`.

**How to test.** `tests/eu22/test_records_fi.py`: key set = IT record; periods tile ≤1975 … 2010+ per type; U-values decrease (or stay equal) from older to newer periods for walls, roofs and windows — any increase printed and explained in the log; window share 0.05–0.50; every value has `source` or `ASSUMED`. Print a table of type × period × (U wall, U roof, U window, share).

#### T03 — Prepare (S3) · T04 — Finish tree + integrity + classes (S4, S5) · T05 — Plan pages (S6, then STOP) · T06 — Speed (manager) · T07 — Harvest + results (S8) · T08 — Viewer + side-cars (S9)
Exactly as the common plan §6.2 with `SITE=FI-HEL-KALLIO`, `cc=FI`.

## 7. Stop-and-report points

1. After T01 + T02 (data, sub-units, records table).
2. After T05 (pages before any run; manager audits and submits).
3. After T08 (results; manager's final check and message to 6J).

## 8. Progress log

(One entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes.)

#### T01 — Acquire and clip Helsinki — completed 2026-10-08

- **Artifacts:** `scripts/eu22/acquire_helsinki.py`; `tests/eu22/test_acquire_helsinki.py`, `tests/eu22/fixtures/helsinki_buildings.json` (20 features), `tests/eu22/fixtures/helsinki_code_labels.json`; `openubem/outputs/eu02/FI-HEL-KALLIO/{01_buildings_clean,02_residential_manifest,02_excluded_manifest}.gpkg` + `01_source.json`, `02_exclusion_counts.json`; `openubem/outputs/eu_evidence/EU-22/FI-HEL-KALLIO/{acquisition_report.json,boundary.geojson,boundary.sha256,licences/helsinki_buildings_licence.txt,raw/helsinki_wfs/,raw/statfi_classification/,raw/hri_page/}`.
- **Result:** 1,869 features downloaded (Kallio peruspiiri 301 bounding box), 1,658 after the seven-step clean, 858 inside the chosen boundary, **509 residential**. CRS EPSG:32635. Licence CC BY 4.0 (HRI page captured).
- **Sub-units (D-EU-151):** the Kallio peruspiiri holds only 458 residential buildings, so the named unit is below 500. Ranked by residential buildings per km² inside the peruspiiri, densest first: 113 Torkkelinmäki (102 buildings) first. Then touching osa-alue added nearest centroid first: 101 Vilhonvuori (running 171), 121 Harju (261), 112 Linjat (375), 111 Siltasaari (408), 122 Alppila (509). Stop at 509 (500–1,000). Harju and Alppila lie outside the peruspiiri (they touch it).
- **Coverage (residential manifest, n=509):** storeys 509 (100 %); year 508 (99.8 %, ≥ 98 % so no census route needed); dwellings 508 (99.8 %); use code 509 (100 %).
- **Code mapping:** labels from Statistics Finland Classification of Buildings 1994 (the layer carries codes only). Residential = codes 01x–04x. Present: 011 detached (3 in manifest), 012/013 empty tag (2/3), 021 terrace (5), 032 apartments (0), 039 Other blocks of flats, empty tag (496). Full table in `acquisition_report.json` → `code_mapping`.
- **Deviations / interpretations:** (1) Residential is decided by `c_kayttark` only. Buildings with no use code (145 in the clipped set, 40 of them typed `Asuinrakennus` in the layer's own `tyyppi`) go to the excluded manifest as `unknown`; the manager may want them reviewed. (2) D-EU-151 says to add neighbours that "touch it": implemented as touching the growing union (1 m tolerance), pool = all Helsinki osa-alue, nearest centroid to the first unit. (3) `observed_dwellings` and `c_kayttark` are extra columns on both manifests (beyond the 23 schema columns). (4) `c_valmpvm` is read as a string (OGR converts it to UTC datetimes and would shift the year); year = first 4 digits, valid 1500–2026. (5) Field names on the live layer matched the plan.
- **Test status:** `python -I -m pytest tests/eu22/test_acquire_helsinki.py` → 8 passed. Live run: `python -I scripts/eu22/acquire_helsinki.py`.
- **Notes:** no shared file was edited. Not yet added to the debug-references file (no error to register).

#### T01 (rerun after amendment) — Acquire and clip Helsinki — completed 2026-10-08

- **Artifacts:** `scripts/eu22/acquire_helsinki.py` (new `_expand_whole_district`, `ring_bounds`, `read_pages` over several page folders, `tyyppi` rule in `map_buildings`); `tests/eu22/test_acquire_helsinki.py` (+5 tests); regenerated `openubem/outputs/eu02/FI-HEL-KALLIO/{01_buildings_clean,02_residential_manifest,02_excluded_manifest}.gpkg` + `01_source.json`, `02_exclusion_counts.json`; `openubem/outputs/eu_evidence/EU-22/FI-HEL-KALLIO/{boundary.geojson,boundary.sha256,acquisition_report.json}`; new raw folder `raw/helsinki_wfs/pages_ring/`. (The boundary file is `boundary.geojson`; the script has never written a `.gpkg` boundary.)
- **Units used (D-EU-151 amended):** the whole Kallio peruspiiri kept (osa-alue 101, 112, 111, 102, 103, 104, 113 — all fully inside), holding **487** residential buildings (458 by use code + 29 by the `tyyppi` rule within the unit; below 500). Then touching osa-alue from outside, nearest centroid to the peruspiiri centroid first: **121 Harju, +101, running total 588**. Stop (≥ 500, ≤ 1,000). Next nearest touching ones (Hermanninmäki, Vallila, Alppila, …) not needed.
- **Residential count:** **588** (clipped 900 = 588 residential + 211 non-residential + 101 unknown; 40 of the 588 have no use code and enter by `tyyppi:Asuinrakennus`).
- **Coverage (residential manifest, n=588):** storeys 580 (98.64 %); year 580 (98.64 %, ≥ 98 % so no census route needed); dwellings 578 (98.30 %); use code 548 (93.20 %; the 40 without code are the `tyyppi` ones).
- **Deviations / interpretations:** (1) The first run downloaded only the peruspiiri bounding box, which does not cover the outside neighbours, so a second paged download (`pages_ring/`, bounding box of every osa-alue touching the peruspiiri, 6,426 buildings after merge, de-duplicated by `id`) was needed; the earlier `pages/` were reused unchanged. Because of it `01_buildings_clean` now holds 4,887 buildings (whole ring box), not 1,658; the boundary clip still gives 900. (2) "Touch" is tested against the peruspiiri itself (not the growing union), so only first-ring units can be added. (3) When the peruspiiri holds ≥ 500 the old densest-first path still applies (unchanged). (4) A building with a use code keeps its code class even if `tyyppi` says `Asuinrakennus`.
- **Test status:** `python -I -m pytest tests/eu22/test_acquire_helsinki.py -q` → 13 passed (8 earlier + 5 new: whole district kept and nearest outside added; stop at threshold in nearest-first order; old path when district reaches the low bound; no-code `Asuinrakennus` residential with tag; other type stays unknown and code wins). Live run: `python -I scripts/eu22/acquire_helsinki.py`.
- **Notes:** no shared file edited. The earlier entry's numbers (509 residential, Alppila added) are superseded by this entry.

#### T02 — Finnish construction records — completed 2026-10-08

- **Artifacts:** `openubem/data/construction/national_specs/fi_spec.json` (28 entries = SFH, TH, MFH, AB × FI.01–FI.07; every value carries a `source` with document, section and page, or `ASSUMED:`); `openubem/data/construction/tabula_archetypes_fi.json` (28 records, IT key set); `tests/eu22/test_records_fi.py` (12 tests); FI section of `openubem/data/construction/TABULA_PROVENANCE.md`.
- **Sources (all retrieved 2026-10-08):** Motiva, "Tyypillisiä olemassa olevien vanhojen rakennusten alkuperäisiä suunnitteluarvoja" (Energiatodistusoppaan 2018 liite, 1.11.2018), §2.1 walls pp.5–7, §2.2 roof pp.7–8, §2.3 floors pp.8–10, §2.4 windows pp.11–12 (rows RIL 1969, 1975/1976, 1978, 1985, 2007); original C3 2003 §3.2.1 p.5 and original C3 2010 §3.2.1 p.7 (read from the ym.fi PDFs, values agree with Motiva); Statistics Finland, Dwellings and Housing Conditions 2009, appendix table 2, 2009 row: detached 108.0, attached 71.1, blocks of flats 56.5 m² per dwelling.
- **Deviations / interpretations:** (1) **SE has no TH and no AB record** (workbook SE rows are SFH and MFH only, national series `SE.N.`): TH takes the SE SFH record and AB takes the SE MFH record of the paired period, stated in `donor_pairing_note` and in each record's `parameter_assumptions`. (2) Donor pairing by period overlap: FI.01→SE.01, FI.02→SE.03, FI.03→SE.03, FI.04→SE.04, FI.05→SE.05, FI.06 and FI.07→SE.05 (SE ends 2005, nothing overlaps; nearest). (3) Mass class: SFH/TH use the "≤ 100 kg/m²" wall and roof values, MFH/AB the "> 100 kg/m²" values for FI.01–FI.03 (class assignment `ASSUMED`, stated in `source`); from FI.04 on the code has one value. (4) FI.01 (≤ 1975) uses the RIL 1969 recommendation south of the Oulu–Kajaani–Kuhmo line (Helsinki is south): a recommendation, not a measured stock mean; the stock-mean graph (Motiva Fig. 7, VTT 1975) is not readable as numbers. (5) Motiva labels the first regulation "1975 määräykset"; it is used for FI.02 (1976–1977). The FI.06 (2007 edition) values come from Motiva only; the 2007 original was not retrieved. (6) Floor U is the ground-contact value (matches the donor floor slot). Door U is not overridable and stays the donor's. (7) `wwr`, `g_gl_window`, `delta_u_tb_w_m2k` and `n_air_infiltration_h_1`: no Finnish source found by period (C3 gives only a reference window area of 15 % of floor area and an n50 ≈ 1 1/h recommendation); donor values kept and tagged `ASSUMED`. (8) **Defect in C01 `national_records._build_record`** (lines 223–226): it writes the new U into `u_components_w_m2k` before `rescale_transmission` reads it as the old U, so a plain `build_records` leaves every `h_transmission_*` equal to the donor's (checked: FI.05, FI.06, FI.07 identical). The committed `tabula_archetypes_fi.json` was built with `build_records` and a wrapper that hands `rescale_transmission` the donor's original `u_components_w_m2k` (the fix the amendment implies); `national_records.py` was not edited. Fix for the manager: build the `new_u` dict first and assign `components[index]` only after `rescale_transmission` has run. The other four non-TABULA T02s will hit the same defect.
- **Test status:** `python -m pytest tests/eu22/test_records_fi.py -q` → 12 passed. U-value increases between consecutive periods: none. Window share 0.099–0.184 (all in 0.05–0.50). Ratio-fallback slots: 0. Record window heat loss equals area × new U for all 28.
- **Type × period table (U in W/m²K; share = window ÷ (window + wall); H_tr = h_transmission_w_m2k):**

| type | period | U wall | U roof | U floor | U window | share | H_tr |
|---|---|---|---|---|---|---|---|
| SFH, TH | FI.01 | 0.470 | 0.410 | 0.470 | 3.14 | 0.099 | 2.853 |
| SFH, TH | FI.02 | 0.400 | 0.350 | 0.400 | 3.10 | 0.099 | 2.400 |
| SFH, TH | FI.03 | 0.290 | 0.230 | 0.400 | 2.10 | 0.099 | 1.948 |
| SFH, TH | FI.04 | 0.280 | 0.220 | 0.360 | 2.10 | 0.099 | 1.880 |
| SFH, TH | FI.05 | 0.250 | 0.160 | 0.250 | 1.40 | 0.099 | 1.036 |
| SFH, TH | FI.06 | 0.240 | 0.150 | 0.240 | 1.40 | 0.099 | 1.003 |
| SFH, TH | FI.07 | 0.170 | 0.090 | 0.160 | 1.00 | 0.099 | 0.689 |
| MFH, AB | FI.01 | 0.810 | 0.470 | 0.470 | 3.14 | 0.184 | 1.437 |
| MFH, AB | FI.02 | 0.700 | 0.350 | 0.400 | 3.10 | 0.184 | 1.234 |
| MFH, AB | FI.03 | 0.350 | 0.290 | 0.400 | 2.10 | 0.184 | 0.873 |
| MFH, AB | FI.04 | 0.280 | 0.220 | 0.360 | 2.10 | 0.184 | 0.801 |
| MFH, AB | FI.05 | 0.250 | 0.160 | 0.250 | 1.40 | 0.184 | 0.468 |
| MFH, AB | FI.06 | 0.240 | 0.150 | 0.240 | 1.40 | 0.184 | 0.457 |
| MFH, AB | FI.07 | 0.170 | 0.090 | 0.160 | 1.00 | 0.184 | 0.321 |

- **For C03:** `_TABULA_PERIODS["FI"] = ((0, 1975, "FI.01"), (1976, 1977, "FI.02"), (1978, 1984, "FI.03"), (1985, 2002, "FI.04"), (2003, 2007, "FI.05"), (2008, 2009, "FI.06"), (2010, 9999, "FI.07"))`. Archetype ids are `FI.N.<TYPE>.<NN>.Gen.ReEx.001.001`; `construction_period` is `FI.NN`. Mean flat areas: SFH 108.0, TH 71.1, MFH 56.5, AB 56.5 m² (national, not Helsinki-specific).
- **Notes:** no shared file edited besides the append-only FI section of `TABULA_PROVENANCE.md`. The `[OPEN]` defect in item (8) is not yet in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (outside the files this task may write); the manager should register it.

#### T03 — Prepare (S3) — completed 2026-10-09

- **Artifacts:** `openubem/outputs/eu_evidence/EU-11/FI-HEL-KALLIO_dw_2026-10-09/` (`prepared_buildings.csv`, `fi_hel_kallio_manifest.csv`, `fleet.lst`, `excluded_buildings.csv`, `summary.json`, `idfs/`, `schedules/`, `weather/`). Weather: `openubem/data/weather/fi_helsinki_tmyx_2009_2023.epw` (typical year, D-EU-163).
- **Result:** 588 residential buildings attempted, **580 prepared (98.6 %)**, 8 excluded. All 8 have one reason, `MISSING_CENSUS_UNIT_DATA` (no construction year; Helsinki has no census route, D-EU-154). Type: AB 508, MFH 53, SFH 15, TH 4. Period: FI.01 386, FI.07 145, FI.04 38, FI.03 10, FI.02 1. Geometry outcome: layout emitted 456, best effort 120, imputed count 2, interzone-mismatch rerouted 1, fallback pending 1. Storeys observed 580; dwellings observed 578.
- **Deviations:** (1) The single-process command measured 4 IDFs in 28 min (about 2.5 min per building, about 24 h in all), so it was stopped (13 IDFs discarded) and S3 ran as 4 parallel `prepare --only-ids` parts (ids dealt largest footprint first, 147 each) into temporary `_dwpart<k>_` trees, then merged into `FI-HEL-KALLIO_dw_2026-10-09` (rows sorted by `building_id`, 8 base exclusions de-duplicated, `summary.json` recomputed: prepared 580, census counters added). Row-level inputs are the same as a single run; IDFs are byte-identical per building by construction (each building is built independently). The merge script is not in the repo (scratchpad only). The temporary part trees were deleted. (2) 4 local processes (limit 10 across executors).
- **Test status:** `summary.json` counts: attempted 588, prepared 580, excluded 8. Every residential building is prepared or in `excluded_buildings.csv` (580 + 8 = 588). Prepared share 98.6 % (>= 80 %). Exclusion reasons: 1 (`MISSING_CENSUS_UNIT_DATA` 8).
- **Notes:** no shared file edited. Debug reference added (single-process time and the parallel recipe).

#### T04 — Finish tree + integrity + classes (S4, S5) — STOPPED at S5 2026-10-09 (correctly divided share 79.0 % < 85 %)

- **Artifacts:** `openubem/outputs/eu_evidence/EU-11/FI-HEL-KALLIO_win_2026-10-09/` (580 IDFs, `windows.csv`, `origin_offset.json`, `md5_2026-10-09.txt`, `degenerate_2026-10-09.csv`, `dwelling_counts_2026-10-09.csv`, `division_classes.csv`, `left_out.csv`); `openubem/outputs/eu_evidence/EU-11/FI-HEL-KALLIO_dw_2026-10-09/layouts/` (580 side-cars); `openubem/outputs/eu_evidence/EU-11/integrity_2026-10-02/FI-HEL-KALLIO_win_2026-10-09_integrity.csv`.
- **S4:** `assemble_win_source`: `windows.csv` 580 rows, errors 0. `12_drop_degenerate`: 580 IDFs, degenerate 0, errors 0. `fleet.lst` = `idfs/` = `md5_2026-10-09.txt` = 580 stems (set-equal); `origin_offset.json` present (dx 385000, dy 6672000, EPSG:32635).
- **S5 integrity (580 homes), failures per check:** I1 0, I2 3, I3 1, I4 0, I5 0, I6 1, I7 4, I8 0 (2 not applicable), I9 0, I10 0, I11 0, I12 0, I13 not applicable (580). Largest 4 of 580 = 0.7 % (< 1 %).
- **Side-cars and classes:** `IDF_FALLBACK` 0 (580 `LAYOUT_SIDECAR`). Classes: OK 229, V3 wrapped flat 229, V1 shape rule broken 120, U4 other box 1, U1 cut lost at IDF write 1. Correctly divided (OK + V3) = **458 of 580 = 79.0 %**; left out 122 (`left_out.csv`). **Below the 85 % limit, so STOP; rules stay frozen, the manager decides.**
- **Window share (`windows.csv`, achieved vs record target):** median difference 0.0000, largest 0.1837 (FI-HEL-765458, FI-HEL-772011, FI-HEL-747273 and 2 more differ by more than 0.01 of share; 5 homes in all).
- **Deviations:** (1) Side-car emitter run as 4 parallel processes, each with `--population-manifest SITE=<quarter of prepared_buildings.csv>` (the plan command fails: it reads a `left_out.csv` that only `score_division` writes; already registered by the ZA plan). All 580 side-cars written, 0 failures. (2) `--workers 4` for S4 and S5 instead of 8 and 10 (shared machine). (3) The integrity csv went to the default `integrity_2026-10-02/` folder. (4) Classes by type: AB 187 OK / 203 V3 / 116 V1 / 1 U1 / 1 U4; MFH 24 / 25 / 4; SFH 14 OK / 1 V3; TH 4 OK. 116 of the 120 V1 homes are AB.
- **Notes:** T05 (plan pages) was not run: the S5 STOP applies before it.

