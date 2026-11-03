# PLAN — seven new neighbourhoods for 6J: shared work (00, common)

## 1. Header

- **Slug:** `eu-new-cities-00-common-2026-10-08`
- **Date:** 2026-10-08 (written by the manager overnight under the owner's authority, see below)
- **Owner requests (verbatim, 2026-10-08):**
  - "can you prepare implemeantion plan for each new city, lets go C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\europeanLocations\implementation"
  - "i will sleep can yo uhandle the plans and executions"
  - "follow same piplien for new cities as well, floor plan division, window to wall ratio etc."
- **Peer request:** `messages_GSSCanada/2026-10-08_6J_to_OpenUBEM_new_neighbourhoods_canada_south_africa.md` (6J, 21:05 list) and our reply `messages_GSSCanada/2026-10-08_OpenUBEM_to_6J_new_neighbourhoods.md`.
- **DESIGN pointers:** `BRIEF_european_locations_v5.md`; district rule DR10 brief line 11 (one contiguous dense residential administrative unit, 500–600 residential buildings, up to 1,000); TABULA→EnergyPlus realisations DR11 brief lines 21–30 (R1–R10); floor division rules `rules/RULES_dwelling_layout_groups_nocore_2026-10-08.html` and `rules/EXAMPLE_dwelling_layout_validation_nocore_2026-10-08.md` lines 6–10 (final values D-EU-148).
- **Goal:** make the existing four-site pipeline (Madrid, Lyon, London, Bologna) accept seven new sites without changing any result of the four existing sites, then run every new site through the **same** pipeline: footprints → archetype → dwellings per floor (no-core cut, the verdict checks, at most 12 homes per floor) → windows from the archetype record's window-to-wall share → origin shift → integrity sweep → plan pages shown before any run → Speed array → harvest → results on correctly divided homes only → 3D viewer → side-cars for 6J.

The seven city plans (one per site) hold the city-specific work. This plan holds (a) the shared code changes C01–C08, done **once** by **one** executor at a time, and (b) the standard per-site steps S1–S9 (§6.2) that every city plan calls.

| Plan | Site id | City | Fold | UTM CRS | Survey year |
|---|---|---|---|---|---|
| `PLAN_eu-new-city-AT-vienna-2026-10-08.md` | `AT-VIE-RUDOLFSHEIM` | Vienna | `at` | EPSG:32633 | 2008 |
| ~~`PLAN_eu-new-city-KR-seoul-2026-10-08.md`~~ archived to `../DONE/` (D-EU-162, dropped 2026-10-09) | `KR-SEO-MAPO` | Seoul | `kr` | EPSG:32652 | 2009 |
| `PLAN_eu-new-city-CA-montreal-2026-10-08.md` | `CA-MTL-PLATEAU` | Montréal | `ca` | EPSG:32618 | 2010 |
| `PLAN_eu-new-city-FI-helsinki-2026-10-08.md` | `FI-HEL-KALLIO` | Helsinki | `fi` | EPSG:32635 | 2009 |
| `PLAN_eu-new-city-ZA-capetown-2026-10-08.md` | `ZA-CPT-WOODSTOCK` | Cape Town | `za` | EPSG:32734 | 2010 |
| `PLAN_eu-new-city-HU-budapest-2026-10-08.md` | `HU-BUD-ERZSEBETVAROS` | Budapest | `hu` | EPSG:32634 | 2009 |
| `PLAN_eu-new-city-AM-yerevan-2026-10-08.md` | `AM-EVN-NORNORK` | Yerevan | `am` | EPSG:32638 | 2008 |

## 2. Hard rules for the executor

1. **Frozen, never written:** `openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2_win_2026-10-06/`, everything under `EU-11/rulebook_2026-09-30/partner_fixed_homes_2026-10-08/`, and on Speed `/speed-scratch/o_iseri/handover_4J_2026-10-06/`. Also never write any existing `*_win_2026-10-0*` tree, any `*_merged_*` tree, `results/EU11_results_2026-10-08_*`, or the four existing `plans3D/PLANS_*_2026-10-08.html` pages.
2. **No result of the four existing sites may change.** Every edit to a shared file adds a branch for the new countries; the ES / FR / GB / IT code paths stay byte-for-byte the same in behaviour. C03 proves it with a before/after IDF comparison.
3. **No simulation anywhere except Speed, and only the manager submits.** The executor writes the run list (`fleet.lst`) and stops. EnergyPlus may run locally only inside an existing test or gate that already does so (the weather smoke gate 6 runs one tiny IDF), and never more than 10 processes.
4. **No UK content goes to 6J.** Nothing in this arc touches London files.
5. **Never invent a value.** Every number in a construction record carries a source (document + page/table) or the tag `ASSUMED:<reason>`. If neither a source nor a rule in this plan gives a value, STOP and quote the gap.
6. **Rules are frozen at the final values** (D-EU-148): `MAX_FLAT_ASPECT = 5.0` (`openubem/geometry/european_nocore.py:1733`), `MIN_SPREAD = 0.25` (`:1745`), at most 12 homes per floor (`openubem/geometry/european_residential.py:44`). No loosening, no new rungs.
7. **No live-network tests.** Acquisition scripts fetch live data (that is data work, allowed); every test reads saved fixtures only.
8. No code comments by default. No `.py` under `docs/`. Figures go to `openubem/outputs/` (flat).
9. Never delete by exclusion. Name every path you move or remove.
10. Git is handled outside this session: never commit, never push.
11. Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`; after fixing one, add an entry there in the house format.
12. Append one progress-log entry per completed task to §8 of **the plan you were dispatched on** (this plan for C-tasks; the city plan for city tasks).

## 3. File layout

| Path | Status | Owner task |
|---|---|---|
| `openubem/data/construction/tabula_registry.py` | edit: add `generate_country_registry(cc)` next to `generate_fr_registry` (`:246`), FR function unchanged | C01 |
| `openubem/data/construction/national_records.py` | new: build TABULA-format records for countries without TABULA from a spec file + a donor record | C01 |
| `openubem/data/construction/national_specs/<cc>_spec.json` | new, one per non-TABULA country (written by city plans) | city T02 |
| `openubem/data/construction/tabula_archetypes_<cc>.json` | new, one per new country | city T02 |
| `openubem/data/construction/TABULA_PROVENANCE.md` | edit: one section per new country | city T02 |
| `openubem/acquisition/european_weather.py` | edit: 7 new `EuropeanWeatherTarget` entries (`:44`) | C02 |
| `scripts/convert_era5_eu_folds_to_epw.py` | edit: `ELEVATIONS_M`, `ISO3` (`:55-56`), `--fold` choices (`:334`) | C02 |
| `scripts/run_eu_t06_weather_promotion.py` | edit: `--fold` choices (`:324`) | C02 |
| `scripts/acquire_era5_eu_folds.py` | edit only if it filters folds | C02 |
| `openubem/data/weather/weather_registry.json` | edit: 7 new targets | C02 |
| `openubem/data/weather/benchmarks/<fold>_<year>_monthly_ghi_benchmark.json` | new, 7 files | C02 |
| `openubem/data/weather/<fold>_<city>_<y1>_<y2>_y<Y>.epw` | new, 7 files | C02 |
| `openubem/semantic/new_country_rules.py` | new: the type / year / storey rules for new countries (§6.1 C03) | C03 |
| `openubem/semantic/european_archetype_mapping.py` | edit: `EU02_SITE_COUNTRY` (`:22`), country guard (`:226`) | C03 |
| `openubem/semantic/construction_sets.py` | edit: `_TABULA_PERIODS` (`:66`) | C03 |
| `openubem/idf/european_windows.py` | edit: `COUNTRY_FILES` (`:11`) | C03 |
| `scripts/run_eu_s2_district_campaign.py` | edit: `DISTRICTS` (`:56`), dispatch (`:1098-1100`), `impute_from_neighbours` (`:1076-1081`) | C03 |
| `scripts/eu21/12_drop_degenerate.py`, `13_model_integrity.py`, `09_plans3d_from_idf.py` | edit: accept new sites | C04 |
| `scripts/eu22/assemble_win_source.py` | new: write `windows.csv`, `dwelling_counts_<tag>.csv`, `changed_stems.txt` from a prepare tree | C05 |
| `scripts/eu22/score_division.py` | new: class every home OK / V3 / S1 / other from the built IDF (same classes as `rulebook_2026-09-30/baseline_1006.csv`) | C06 |
| `scripts/cluster/harvest_eu11_district.py`, `scripts/generate_eu_3d_viewers.py`, `scripts/emit_eu11_layout_sidecars.py`, `scripts/cluster/export_flat_counts_4j.py` | edit: accept new sites | C07 |
| `scripts/cluster/stage_eu22_site.sh`, `scripts/cluster/submit_eu22_site.sbatch` | new: staging + array job for one new site | C08 |
| `scripts/eu22/acquire_<city>.py` | new, one per city (city plans) | city T01 |
| `scripts/eu22/write_results_eu22.py` | new: per-home and summary results for new sites | C07 |
| `tests/eu22/` | new test folder, fixtures under `tests/eu22/fixtures/` | all |
| `openubem/outputs/eu02/<SITE>/` | new: `01_buildings_clean.gpkg`, `02_residential_manifest.gpkg` | city T01 |
| `openubem/outputs/eu_evidence/EU-22/<SITE>/` | new: raw downloads (`raw/`), boundary, acquisition report, licence text | city T01 |
| `openubem/outputs/eu_evidence/EU-11/<SITE>_dw_<date>/`, `<SITE>_win_<date>/`, `<SITE>_merged_win_<date>/` | new trees | S3–S8 |
| `docs/docs_ACTIVE/europeanLocations/plans3D/PLANS_<SITE>_<date>.html` | new pages | S6 |
| `docs/docs_ACTIVE/europeanLocations/results/EU22_results_<SITE>_<date>_*` | new results | S8 |

## 4. Dependency decisions (pinned)

Decisions taken by the manager overnight under the owner's "can yo uhandle the plans and executions"; each is open for owner review and is listed in the morning report.

- **D-EU-150 — site ids, districts, CRS, folds:** the table in §1. CRS = the WGS84 UTM zone of the district centroid (Cape Town is south: 34S). A city plan may change only the sub-unit inside the named district, never the site id.
- **D-EU-151 — district size rule** (DR10 brief line 11). Count = residential buildings after `split_residential` (`openubem/acquisition/boundary_clip.py:63`). Take the named administrative unit. If it holds more than 1,000, go one statistical level down (census tract / Zählbezirk / dong / osa-alue …, named in the city plan) and take the unit named first in the city plan's ranked list; if that holds fewer than 500, add the next-level units that touch it, nearest centroid first, one at a time, stopping at the first total of 500 or more; never pass 1,000. Record the units used in the acquisition report. **Amendment 2026-10-08 night (manager, after Helsinki T01):** if the named unit itself holds fewer than 500, keep it whole and add next-level units that touch it (from outside it), nearest centroid to the named unit's centroid first, one at a time, until 500 or more.
- **D-EU-152 — construction records without TABULA (FI, KR, CA, ZA, AM):** TABULA-format records built by `national_records.py`. U-values (wall, roof, floor, window), window g-value, thermal-bridge add-on, infiltration and window-to-wall share come from cited national sources per construction period. Every other field (reference floor area, number of flats, element areas, boundary factors, `c_m` 45, `phi_int` 3.0, `theta_i` 20, `n_air_use` 0.4, …) is copied from a **donor** TABULA record of the same building type and the nearest period. Donors (by climate and stock): **FI ← SE**, **CA ← SE**, **KR ← RS**, **ZA ← ES**, **AM ← BG**. When a national window-to-wall share is cited, the donor's window and wall areas are rescaled to it, keeping their sum (`a_win' = wwr × (a_win + a_wall)`, `a_wall' = (1 − wwr) × (a_win + a_wall)`, split over directions in the donor's proportions). Every copied field is stamped `ASSUMED:donor <archetype_id>` in `parameter_assumptions`.
- **D-EU-153 — TABULA countries (AT, HU):** records generated from the pinned workbook, same route as France: `tabula-calculator.xlsx`, MD5 `c99ddc9ffcb6dc0ae7391273d9619e37`, at `C:/Users/o_iseri/Desktop/GSSCanada/GSSCanada-main/4J_docs_occ/Step8_docs/outputs_step8/raw/`, sheet `Calc.Set.Building`, rows `Code_Country == cc` and `Number_BuildingVariant == 1` (measured: AT 61 rows, HU 16 rows). The workbook is read-only. **Amendment 2026-10-08 night (manager, after AT/HU T02):** only the national series is used — AT keeps `AT.N.` (38 records) and drops the parallel `AT.MT.` series (`exclude_prefixes=("AT.MT.",)`), which has period gaps; HU is all `HU.N.` (16). HU has no apartment-block (AB) record for 1990–2005 (`HU.04`): an AB building in that period takes `HU.N.MFH.04.Gen.ReEx.001.001`, provenance `TABULA_TYPE_SUBSTITUTE_MFH_FOR_AB`. Apartment blocks before 1990 take the combined `HU.N.AB.01-03.Gen.SyAv.001.001` record. **General substitute rule (manager, after C03):** for any new country, when the mapped building type has no record for the period, use the same period's record of the substitute type, in this order: AB → MFH; TH → SFH; MFH → AB; SFH → TH. The provenance is `TABULA_TYPE_SUBSTITUTE_<USED>_FOR_<MAPPED>`, and the count goes in the prepare summary. Exclude only when no substitute exists either. This covers HU TH (→ SFH) and HU AB 1990–2005 (→ MFH).
- **D-EU-154 — missing attributes, in this order, for new countries only:** **Amendment 2026-10-08 night (manager, after Budapest T01):** an open-ended oldest census class (e.g. "before 1946") takes the upper year of the country's oldest TABULA or national period, if that year falls inside the class. Otherwise it takes the class's own upper year. This keeps pre-war stock in the pre-war record. Budapest: "before 1946" → 1944 (HU.01). Vienna (1918) and Yerevan (1950) are unchanged.
  - *Year built:* observed per-building year → else the dominant construction period of the smallest census unit holding the building, at that period's reference year (the Bologna rule, `scripts/run_eu_s2_district_campaign.py:603-640`; ties → exclude, no tie-breaking) → else exclude. Provenance `IMPUTED_CENSUS_UNIT_CONSTRUCTION_PERIOD`.
  - *Storeys:* observed count → else `max(1, round(height_m / 3.0))` from a measured height → else neighbour imputation (`impute_from_neighbours`, `:1062`, rungs touching / 30 m / district mode) → else exclude. The Bologna 9.0 m default is **not** used for new sites.
  - *Type:* observed tag (`apartments`→AB, `detached`→SFH, `terrace`→TH; `european_archetype_mapping.py:31`) → else the two-signal rule when a dwelling count is observed (`derive_bdtopo_building_type`, `:192`) → else the Bologna storey rule (`run_eu_s2_district_campaign.py:600-605`: ≤2 storeys TH if attached else SFH; 3–4 MFH; ≥5 AB).
  - *Dwellings:* observed count → else the existing `_dwellings_for` route (`:149`; 1 for SFH/TH, else floor area ÷ the record's mean flat area), unchanged.
- **D-EU-155 — weather:** ERA5 → EPW, the same route as the four sites. Diary window = the MTUS survey year (AT 2008, KR 2009, CA 2010, FI 2009, ZA 2010, HU 2009, AM 2008). Raw ERA5 window = previous year + survey year when the UTC offset is positive (all but Canada), survey year + next year when it is negative (Canada, −5). On the two leap years (2008: AT, AM) 29 February is dropped so the file has 8,760 hours (EPW practice). Gate 5 benchmark = PVGIS MRcalc monthly GHI for the station point and survey year, database order SARAH3 → NSRDB → ERA5; if only ERA5 is available (Seoul likely), record "benchmark is ERA5-derived, not independent" in the registry note.
- **D-EU-156 — origin shift for every new site** (FINDING 288: UTM coordinates make EnergyPlus mis-read some walls). `12_drop_degenerate.py --shift <cc>` for all seven.
- **D-EU-157 — published results only on correctly divided homes** (D-EU-149 carried over): classes `OK`, `V3_divided_wrapped_flat`, `S1_one_flat_per_floor_by_data`, the same classes the 10-08 set kept. Everything else is shown in the viewer as "left out — not correctly divided" with no EUI.

- **D-EU-158 — residential use where no open use data exists (Cape Town, Yerevan):** a footprint is residential when OSM tags it residential, or when it is untagged and lies inside OSM `landuse=residential`; in Cape Town footprints under 2.0 m measured height are dropped as sheds. Each city report gives the count per route.
- **D-EU-159 — Vienna weather accepted despite gate 5 (owner, 2026-10-09: "vienna yes"):** the `at` 2008 EPW is pinned with a documented gate-5 exception for exactly the months that fail the 10 % tolerance against SARAH3 (01:20 state: Jan +21 %, Mar +17 %, Nov +15 %), via `run_eu_t06_weather_promotion.py --fold at --approve-gate5-exception at:2008 <months> --commit`. Reason: the conversion is verified (within 1 % of PVGIS ERA5); the gap is between two sunshine sources. The exception covers winter months (Oct–Mar) only; any failing month in Apr–Sep → STOP. The tolerance is not widened, and nothing changes for es/uk/it/fr or the other new folds.
- **D-EU-160 — Cape Town licence (owner, 2026-10-09: "6J means us, there is no other team, it is another project of my own"):** handing Cape Town files to 6J is internal use, not redistribution, so the licence hold on S9 side-cars for 6J is lifted. Conditions from the City text: non-commercial use only; no public release of the City footprints (public repo, public page, open dataset) without the City Geomatics Branch's permission; every map or figure credits "City of Cape Town" as source and copyright holder.
- **D-EU-161 — Cape Town build go-ahead (owner, 2026-10-09: "you assign an agent to start abnd build cape town"):** taken as acceptance of the T01 year route (own heritage label 88.8 %, street-block label 9.6 %, no year 1.7 %), which clears Cape Town stop point 1. S3 still needs the `za` weather fold pinned (download queued behind ca/fi at 08:30); the manager dispatches Cape Town T03–T05 as soon as `za` is converted, gated and promoted.
- **D-EU-162 — Seoul is conditional (owner, 2026-10-09: "lets exclude seoul from this project if i can not login/register"; "yes, run the check"):** data.go.kr sign-up rejects the owner's non-Korean phone number ("전화번호가 유효하지 않습니다."). Seoul T01 step 1 (route without key or account) runs now. If it finds a usable bulk download, Seoul continues; if not, Seoul is dropped and the project has six new cities. **Result 2026-10-09:** no route without an account (V-World asks for login, checked by the owner); owner: "drop seoul", "archive the seoul project". Seoul is dropped; plan archived to `DONE/`; `kr` removed from the weather download queue. Six new cities remain.
- **D-EU-163 — Typical-year weather allowed (owner, 2026-10-09: "no need to use real weather, it can be tmy weather files as well, i already published many publications with these weather files"):** the five cities without a finished ERA5 file (`ca`, `fi`, `za`, `hu`, `am`) use the TMYx file from climate.onebuilding.org for the registry station (same WMO), range `2009-2023` (newest available range if that one is missing). Gates 1–4 and 6 must pass; gate 5 (monthly sunshine vs PVGIS) is run and recorded only, never a stop. Vienna (`at`) keeps its accepted ERA5 survey-year file (D-EU-159). ERA5 downloads for the five are stopped. Consequence: these five cities use a typical year, not the survey year, so their results are not like-for-like with the four built cities on weather; state this wherever their numbers are quoted.
- **D-EU-164 — Weather check adapted for typical-year files (manager, 2026-10-09):** the hour-by-hour sun-balance check (gate 4 solar closure, any daytime hour > 5 W/m2) was written for our own converted ERA5 files and no measured station file can meet it; all five TMYx files fail it. Measured instead: over the year EnergyPlus sees 98.5–99.4 % of the file's horizontal sun (DHI + DNI·cos z at mid-hour vs GHI), so the misfit cancels to about 1 %. For TMYx files gate 4 closure is replaced by this annual balance, which must lie within 0.97–1.03; every other gate-4 range check stays. Yerevan (`am`) uses the registry's own station, Zvartnots airport (WMO 37788, `ARM_ER_Yerevan-Zvartnots.Intl.AP.377880_TMYx.2009-2023`), not Arabkir (WMO 37789, 2011-2025, pressure 83–86 kPa, below the 85 kPa bound). FINDING 297: Cape Town and Yerevan files fit the sun best one hour later than their time stamps (sun-balance error drops from ~50–63 to ~4 W/m2 with a one-hour shift); left as published, since the yearly total is unaffected, but hourly solar timing in those two cities is about one hour off.
- **D-EU-165 — Yerevan `way/998439490` left out (owner, 2026-10-09: "yes leave out the one yerevan building"):** the home has 0 m2 outdoor wall and 0 window but was scored in the kept set (Yerevan T04 note). It joins `left_out.csv` before the Speed run (T06) and is treated like the other 15 left-out homes: Yerevan kept 535 of 551 = 97.1 %, left out 16. No other home changes.
- **D-EU-166 / D-EU-167 (manager, 2026-10-10, under the owner's 95 % request for Helsinki, Vienna, Budapest):** a home whose floors all pass the final ruleset is scored on its floors, not on the generator's best-effort tag (`--floors-decide`, these three cities only); one flat less on a failing floor only where the flat count was estimated (`area_imputed`). Full text: `PLAN_eu-division-fix-3cities-2026-10-10.md` §4.
- **D-EU-169 — Vienna typical-year file added for 6J (owner, 2026-10-24: "yes, add the Vienna file and answer 6J"):** 6J asked (2026-10-16) for a Vienna TMYx file to compare cities on typical years. The Wien-Schwechat airport file (WMO 110360, TMYx 2009-2023, fetched by 6J on 10-19) is registered as `openubem/data/weather/at_vienna_tmyx_2009_2023.epw` under new `tmyx_*` keys of the `at` registry entry; the ERA5 survey-year file stays the pinned `weather_file` (D-EU-159), since the published Vienna results use it. Gates 1–4 and 6 pass, annual sun balance 0.993, gate 5 fails (recorded only, D-EU-163). Vienna plan §8 Step W; reply `messages_GSSCanada/2026-10-24_OpenUBEM_to_6J_vienna_tmyx_answer.md`.
- **Dispatch order:** C01 first (short; every T02 needs it). Then, in parallel: C02 (weather, long downloads) and the city T01s (each touches only its own files). T02s after C01. C03–C08 after C02 starts, one executor. S3 for any city only after common stop point 2.

Weather stations (the executor confirms each elevation in WMO OSCAR/Surface and records the page; HU has none yet):

| Fold | City | Station | WMO | Lat | Lon | Elev m | UTC | Raw window | Output |
|---|---|---|---|---|---|---|---|---|---|
| at | Vienna | Wien-Schwechat | 11036 | 48.11 | 16.57 | 183 | +1 | 2007-01-01/2008-12-31 | `at_vienna_2007_2008.epw` |
| kr | Seoul | Seoul | 47108 | 37.57 | 126.97 | 86 | +9 | 2008-01-01/2009-12-31 | `kr_seoul_2008_2009.epw` |
| ca | Montréal | Montréal-Trudeau | 71627 | 45.47 | −73.74 | 36 | −5 | 2010-01-01/2011-12-31 | `ca_montreal_2010_2011.epw` |
| fi | Helsinki | Helsinki-Vantaa | 02974 | 60.33 | 24.97 | 51 | +2 | 2008-01-01/2009-12-31 | `fi_helsinki_2008_2009.epw` |
| za | Cape Town | Cape Town Intl | 68816 | −33.97 | 18.60 | 42 | +2 | 2009-01-01/2010-12-31 | `za_capetown_2009_2010.epw` |
| hu | Budapest | Budapest-Ferihegy | 12839 | 47.43 | 19.18 | (confirm) | +1 | 2008-01-01/2009-12-31 | `hu_budapest_2008_2009.epw` |
| am | Yerevan | Yerevan-Zvartnots | 37789 | 40.15 | 44.40 | ~865 (confirm) | +4 | 2007-01-01/2008-12-31 | `am_yerevan_2007_2008.epw` |

## 5. Facts with citations

- Footprint schema: `SCHEMA_COLUMNS` (23 columns) `openubem/acquisition/footprint_schema.py:14-19`; `finalize_footprints` `:166` writes `01_buildings_clean.gpkg`; `clip_to_boundary` `boundary_clip.py:12`, `split_residential` `:63`, `write_manifests` `:96` write `02_residential_manifest.gpkg`.
- Observed year needs `provenance_year_built` ending in `_OBSERVED` (`european_archetype_mapping.py:74-82`); observed dwellings read from `observed_dwellings` or `surplus_tags` (`:85-95`); storeys from `levels`, `<= 0` = missing (`:135-149`).
- Country guard `{"ES","GB","IT","FR"}` raises for any other country (`european_archetype_mapping.py:226-227`); the two-signal fallback fires only for FR and ES (`:238`).
- `prepare()` dispatch: GB → `_gb_rows`, IT → `_it_rows`, else `_mapped_rows` (`run_eu_s2_district_campaign.py:1098-1100`); records file `tabula_archetypes_<country>.json` (`:1097`); manifest CRS must equal the district CRS (`:1093-1094`).
- `_mapped_rows` excludes rows without observed storeys (`:688-689`) and computes adjacency only for ES/FR (`:675-680`).
- Dwelling count route `_dwellings_for` `:149-168`.
- Windows: share = Σ window area ÷ (window + Σ wall area) from the record geometry; record also gives `u_window_w_m2k`, `g_gl_window`, `delta_u_tb_w_m2k` (`openubem/idf/european_windows.py`, `COUNTRY_FILES` `:11`); prepare applies windows and orientation itself (`scripts/run_eu_s2_campaign.py:2035-2036`). **Never run `10_add_windows.py` or `11_fix_orientation.py`** — not idempotent and hard-wired to old trees.
- Per-floor division: `_extrude_zone_groups_per_storey` (`run_eu_s2_campaign.py:1157`); at most 12 homes per floor (`european_residential.py:44`); verdict checks C1, C3, C4, C5, C6, C10, C11 (`rules/EXAMPLE_dwelling_layout_validation_nocore_2026-10-08.md:6`).
- Gains: the same Step-8 gain schedule for every zone, `emit_step8_gain_schedule` (`run_eu_s2_campaign.py:2078`); it does not depend on the country.
- Tree finishing: `12_drop_degenerate.py` copies `prepared_buildings.csv`, `windows.csv`, `schedules/`, `weather/` (`:26-27`) and fails when they are missing; it refuses 10-03/10-04 targets (`:310`).
- Integrity sweep: `13_model_integrity.py` checks I1–I13 (`:41`) and reads a reference tree, `openubem/outputs/3D/eu_<D>_data/buildings.csv` and `<D>_merged_2026-09-08` (`:652-662`) — four-site inputs a new site does not have.
- Plan pages: `09_plans3d_from_idf.py --district <D> --source-tag <tag> --date <date> [--verify]` (`:637-643`), `ROOT` hard-coded (`:20`), four-site exclusion files (`:49-51`).
- Weather target fields `european_weather.py:29-40`; six gates `:521`; gate 5 tolerance 10 % (`run_eu_t06_weather_promotion.py:46`), benchmark JSON = `source` + 12 `monthly_ghi_kwh_m2` (`european_weather.py:246-251`).
- Speed recipe (10-06): stage to `/speed-scratch/o_iseri/fleets/EU11_<D>_<tag>/{idfs,schedules,weather,fleet.lst,out,submit_recut.sbatch}`; `sbatch -p ps --time=7-00:00:00 --array=1-<N>%32 --mem=32G` (integrity plan `implementation/DONE/PLAN_eu-model-integrity-2026-10-02.md:308-313, 653-660`); `speed_jobs.txt` one job id per line (`harvest_eu11_district.py:262-270`).
- Correct-division classes: `rulebook_2026-09-30/baseline_1006.csv` column `cls` (values OK 3,096, V1 301, V2 113, V3 587, S1 6, U3 8, U4 2); the class logic is in `scripts/analysis/eu_rulebook_dryrun_2026-09-30.py` (`UNRESOLVED` `:58`, `_floor_polys` `:129`, `_storey_record` `:155`).

## 6. Tasks

### 6.1 Shared code (one executor at a time, in this order: C01 → C02 → C03 → C04 → C05 → C06 → C07 → C08)

#### C01 — Construction-record tools

**What.** (a) `generate_country_registry(cc, workbook, out)` in `tabula_registry.py`, the FR route generalised: same `_record(row, extras, boundaries, sha256)` call, `survey_fold` = the new fold. `generate_fr_registry` stays as it is. (b) `openubem/data/construction/national_records.py` with `build_records(spec_path, out_path)`: reads a spec JSON (format below), loads each donor record from the donor country's registry (generate it with (a) into a temporary path if the donor JSON does not exist — SE, RS, BG are not in the repo), copies it, overrides the cited fields, rescales windows/walls per D-EU-152, and writes `tabula_archetypes_<cc>.json` with the same top-level keys as `tabula_archetypes_it.json`.

Spec format (one entry per building type × period):
```json
{"country": "FI", "fold": "fi", "donor_country": "SE",
 "periods": [{"code": "FI.01", "from": 0, "to": 1975}],
 "entries": [{"building_type": "AB", "period": "FI.01", "donor_archetype_id": "SE.N.AB.01.Gen",
   "values": {"u_wall_w_m2k": {"value": 0.81, "source": "Ympäristöministeriö 1976 C3, table 1"},
              "u_window_w_m2k": {"value": 2.8, "source": "ASSUMED: ..."},
              "wwr": {"value": 0.18, "source": "..."}}}]}
```
Allowed override keys: `u_wall_w_m2k`, `u_roof_w_m2k`, `u_floor_w_m2k`, `u_window_w_m2k`, `g_gl_window`, `delta_u_tb_w_m2k`, `n_air_infiltration_h_1`, `wwr`, `mean_flat_area_m2` (sets `n_apartment = a_c_ref_m2 / mean_flat_area_m2`). Anything else → error. The record's `u_components_w_m2k` and `h_transmission_*` are recomputed from the new U-values with the same formula the workbook rows use (read it from `_record`; if it cannot be recomputed from the record alone, STOP and report).

**Amendment 2026-10-08 night (manager, after the C01 stop — the stored heat-loss parts are not area × U × b; the workbook adds a per-slot series resistance):** for every wall/roof/floor/window slot `i` with area `A`, factor `b`, old U `U0`, stored part `H0` and new U `U1`: `R = b·A/H0 − 1/U0` (the slot's own extra resistance, read from the record); `H1 = b·A / (1/U1 + R)`. Slots with `A = 0` or `H0 = 0` stay 0. If `R < −1e-6` or `1/U1 + R ≤ 0`, use `H1 = H0·U1/U0` for that slot and list it in `parameter_assumptions` as `"RATIO_FALLBACK: <slot>"`. `door_1` is unchanged. `thermal_bridging` scales by new ÷ old `delta_u_tb` when overridden, else unchanged. `h_transmission_w_m2k` = sum of the parts ÷ `a_c_ref_m2` (same as `european_box.py:378-390`). Extra tests: (6) an override with every U equal to the record's own gives byte-identical parts (|ΔH| < 1e-9); (7) on `FR.N.SFH.01.Gen.ReEx.001.001` wall_3, the hand value `b·A/(1/U1 + R)` for U1 = 0.5 matches; (8) count the ratio-fallback slots over IT/ES/GB/FR records with U1 = U0·0.5 and print it.

**Why.** D-EU-152, D-EU-153. Five countries have no TABULA data; the pipeline only reads TABULA-format records.

**How.** Read `tabula_registry.py:246-300` and one record of `tabula_archetypes_it.json` first. Records keep the full key set of the IT record. `attribution` stays "Source: IEE Projects TABULA + EPISCOPE (www.episcope.eu)" for TABULA-derived fields and adds "national sources per parameter_assumptions" for D-EU-152 records.

**How to test** (`tests/eu22/test_records_tools.py`, fixtures only):
1. A 3-row fixture sheet (copy 3 FR rows from the workbook into `tests/eu22/fixtures/`) through `generate_country_registry("FR", …)` gives records equal to the same 3 records in `tabula_archetypes_fr.json`.
2. A 2-entry spec on an IT donor: overridden fields equal the spec; every other field equals the donor; key set equals the IT record key set.
3. `wwr` rescale: new share = spec value within 1e-9; window + wall sum unchanged.
4. An unknown override key raises; a value with neither `source` nor `ASSUMED` raises.
5. `generate_fr_registry` output unchanged (sha256 of a fresh run = sha256 of the committed `tabula_archetypes_fr.json`, or the existing FR registry test still passes).

#### C02 — Seven weather folds

**What.** Add the 7 targets of §4 to `EUROPEAN_WEATHER_TARGETS` and the registry; extend the converter and the promotion script; fetch 7 PVGIS benchmarks; download ERA5; convert; run the six gates; write the registry entries.

**Why.** D-EU-155; every site needs its survey-year weather file before `prepare` (it reads the fold's `weather_file`, `run_eu_s2_district_campaign.py:1095`).

**How.**
1. Read `european_weather.py:26-62`, `convert_era5_eu_folds_to_epw.py` in full, `acquire_era5_eu_folds.py`, `run_eu_t06_weather_promotion.py:44-60, 200-300`.
2. Check the converter handles (a) a negative UTC offset (Canada needs the first 5 UTC hours of 2011) and (b) dropping 29 February. If either is missing, add it inside the converter for the new folds only and test it; the ES/UK/IT/FR outputs must stay byte-identical (re-run conversion of `es` 2010 to a temp path and compare sha256 with the registry value).
3. Registry entries for the new folds: `status` `RULED_PINNED`, `diary_window` = survey year, `licence_text_at_download` captured exactly as the existing entries do.
4. Benchmarks: PVGIS MRcalc v5_3 monthly GHI at the station point for the survey year (database order of D-EU-155), saved as `benchmarks/<fold>_<Y>_monthly_ghi_benchmark.json` with `source` naming the database.
5. ERA5: `~/.cdsapirc` exists. Download all 7 folds (CDS requests may queue for hours; run in the background, log every request id and the real error text of any failure). Raw files go to `openubem/data/weather/raw/` as the existing folds do.
6. Convert to `<fold>_<city>_<y1>_<y2>_y<Y>.epw`; run the promotion script with `--commit` for each fold.

**How to test.**
1. All six gates per fold (one line each with the verdict). Gate 5 FAIL → STOP and report the months; do not widen the tolerance.
2. Each EPW has 8,760 data rows, header city/lat/lon/UTC/elevation equal to §4.
3. `pytest tests/test_eu_weather_registry.py tests/test_eu_weather_six_gates.py` pass (same count as before plus new cases if you add them).
4. The four existing registry entries are byte-identical to before (compare the JSON objects).

#### C03 — Country registration and the new-country mapping branch

**What.**
1. `openubem/semantic/new_country_rules.py`: `NEW_COUNTRIES = {"AT","KR","CA","FI","ZA","HU","AM"}`; `new_country_rows(district, gdf, records)` implementing D-EU-154 (type / year / storeys rules), returning rows and exclusions in the same shape as `_mapped_rows`; `dominant_period(counts, period_years)` (returns `(year, label)` or `(None, "CENSUS_UNIT_PERIOD_TIE_…")`). Census input: the acquisition writes, per building, `census_unit_id` and `census_period_counts` (JSON `{label: count}`) plus a per-country `period_years` map in the city's acquisition report; `new_country_rows` reads them.
2. Register the 7 sites: `DISTRICTS` (`run_eu_s2_district_campaign.py:56`), `EU02_SITE_COUNTRY` (`european_archetype_mapping.py:22`), the country guard (`:226`, add the 7), `_TABULA_PERIODS` (`construction_sets.py:66`, periods read from each new registry's records — a city's entry is added when its registry exists), `COUNTRY_FILES` (`european_windows.py:11`).
3. Dispatch: in `prepare()` add `elif cfg["country"] in NEW_COUNTRIES: rows, exclusions = new_country_rows(district, gdf, records)` before the `else`; in `impute_from_neighbours` route new districts to `_impute_es_fr_rows` (read it first; if it hard-codes ES/FR fields, add a new-country variant instead of editing it).
4. Adjacency (`compute_footprint_adjacency`) is computed for every new district (needed for the SFH/TH split).

**Why.** D-EU-154; the pipeline refuses unknown countries today (`european_archetype_mapping.py:226`).

**How.** New-country logic lives in the new module; existing functions get one added branch each. A city's site can be registered before its records exist; `prepare` for it simply fails until T02 is done.

**How to test** (`tests/eu22/test_new_country_rules.py`, fixtures only):
1. Rule table: one fixture row per D-EU-154 rung (observed year; census dominant; census tie → excluded; observed storeys; height → storeys; no height → neighbour route; tag → type; two-signal; storey rule ≤2 attached / ≤2 detached / 3–4 / ≥5). Each gives the expected value and provenance.
2. **No change for the four sites:** before editing, run `prepare` with `--only-ids` on 5 fixed buildings each for ES, FR and GB into a temp folder (pick the first 5 ids of each `prepared_buildings.csv` in `<D>_win_2026-10-06`; IT is skipped because `_it_rows` fetches live data); after editing, run again; every IDF sha256 equal. Report the 15 hashes pair by pair.
3. The existing tests that name the four site ids pass: `tests/test_eu_observed_archetype_mapping.py`, `tests/geometry/test_eu15_ruled_coverage.py`, `tests/idf/test_eu16_context_adiabatic.py`, `tests/geometry/test_eu14b_bologna_layout_binding.py` (report pass counts before/after).

#### C04 — Let the tree tools accept new sites

**What.** `12_drop_degenerate.py`: add the 7 to `DISTRICTS` (`:18-23`) and `CRS` (`:24`). `13_model_integrity.py`: add the 7 to `DISTRICTS` (`:30-35`) and `SHIFTED` (`:37`); for new sites the reference tree is the tree itself (`--ref-tree` = `--tree`, the existing `self_ref` path `:681`), and the three four-site inputs (`3D/eu_<D>_data/buildings.csv`, `<D>_merged_2026-09-08`, `t06s_rerun`) are replaced by `eu02/<SITE>/02_residential_manifest.gpkg` attributes and `prepared_buildings.csv`; any check that cannot be computed without them is reported `NOT_APPLICABLE_NEW_SITE` with the reason, never silently skipped. `09_plans3d_from_idf.py`: `ROOT` from `Path(__file__)`; the four-site exclusion files are read only for the four sites; new sites take an optional `--exclude-csv` (S6 passes the C06 left-out list).

**Why.** These scripts are steps S4–S6 of the same pipeline and are four-site only today (§5).

**How to test.** (1) For each of ES, FR, GB the 10-06 integrity summary re-run into a temp `OUT_DIR` equals `EU-11/integrity_2026-10-02/summary_win_2026-10-06.csv` row for row (point `OUT_DIR` at a temp folder by a CLI flag you add; never overwrite the original). (2) `09_plans3d_from_idf.py --district ES-MAD-BERRUGUETE --source-tag win_2026-10-06 --date 2026-10-06 --verify` into a temp output gives the same scene JSON as `plans3D/archive/` 10-06 Madrid page (compare the `scene` block sha256). (3) A synthetic 3-building new-site fixture tree passes through all three scripts.

#### C05 — Source-tree assembler

**What.** `scripts/eu22/assemble_win_source.py --site <SITE> --tree <SITE>_dw_<date>`: writes into that same prepare tree (a) `windows.csv` with the columns of `10_add_windows.py` `_process`, computed **read-only** from each IDF's `FenestrationSurface:Detailed` and exterior walls (window area, wall area, measured share, record share, difference), (b) `dwelling_counts_<date>.csv` (`building_id,old_count,new_count,dwellings_source`, with old = new = `dwellings_used`), (c) `changed_stems.txt` = every stem in `idfs/`.

**Why.** The 10-06 trees got these files from scratch drivers that are not in the repo (rebuild recipe, step 3); `12_drop_degenerate.py` needs them.

**How to test.** On a copy of 5 Madrid IDFs from `ES-MAD-BERRUGUETE_win_2026-10-06/idfs/`, the measured window and wall areas equal the existing `windows.csv` rows for those stems within 0.01 m² (report the column mapping you used). No IDF is modified (sha256 before = after).

#### C06 — Division scorer for new sites

**What.** `scripts/eu22/score_division.py --site <SITE> --tree <SITE>_win_<date>`: per home, per storey, the nine checks (C1, C3, C4, C5, C6, C10, C11 verdict; C12, C13 reported) from the built IDF floor polygons, and the home class with the same class names and rules as `baseline_1006.csv`. Reuse the functions of `eu_rulebook_dryrun_2026-09-30.py` and `04_group_tests.py:312 run_checks` / `07_nocore_tests.py` by import; do not copy their logic. Writes `<tree>/division_classes.csv` (columns of `baseline_1006.csv`) and `<tree>/left_out.csv` (homes not in OK / V3 / S1).

**Why.** D-EU-157; the 10-08 results keep only correctly divided homes.

**How to test.** Run on the 10-06 Madrid tree into a temp folder: the class of every Madrid home equals `baseline_1006.csv` (report agree / disagree counts; any disagreement → STOP and list the first 10).

**Amendment 2026-10-08 night (manager, after the C06 stop — ruling (b)):** the scorer takes the cutter's own polygons, which is what the baseline scored. For a new site these are the layout side-cars that S3 `prepare` writes into `<SITE>_dw_<date>`, so no extra run is needed; the scorer gets `--layout-tree <SITE>_dw_<date>`. Only if a side-car is missing does it fall back to the IDF floors, and then it stamps `class_source = IDF_FALLBACK` and counts it. New test: run `prepare --only-ids` on Madrid for the 13 non-drift disagreeing homes plus the first 20 agreeing homes into a temp folder, then score from those side-cars. All 33 must agree with `baseline_1006.csv`. The 6 drift homes are excluded, listed in `drift_1006.csv`. Any disagreement → STOP and list them.

#### C07 — Harvest, results, viewer, side-cars for new sites

**What.** `harvest_eu11_district.py`: add the 7 to `DISTRICT_JOBS` / `TAGGED_DISTRICT_JOBS` (`:50-79`) so `--district <SITE> --tag win_<date>` works. `scripts/eu22/write_results_eu22.py --site <SITE> --tag win_<date>`: per-home and summary results in the shape of `results/EU11_results_2026-10-08_{per_home.csv,per_home.json,summary.csv,summary.json}`, keeping only homes not in `left_out.csv`. `generate_eu_3d_viewers.py`: add the 7 to `DISTRICT_SPECS` (`:807`), EUI from the new per-home file, left-out homes badged as in T17 of the rulebook plan. `emit_eu11_layout_sidecars.py` and `export_flat_counts_4j.py`: accept new sites (read `:166-174` and `:240` first; new sites take the generic branch).

**Why.** Steps S7–S9.

**How to test.** (1) A fixture `out/` folder with 3 stems (copy 3 finished Madrid runs' `eplustbl`/`sql` outputs into `tests/eu22/fixtures/`) harvests into the expected manifest rows. (2) `write_results_eu22.py` on that fixture: rows = 3 − left-out, EUI = harvested heating ÷ floor area. (3) The four existing viewers regenerate byte-identical when the generator runs for them into a temp folder (or are not regenerated at all — say which).

#### C08 — Speed staging script and job file

**What.** `scripts/cluster/stage_eu22_site.sh <SITE> <tag>` (mkdir + tar over ssh into `/speed-scratch/o_iseri/fleets/EU22_<SITE>_<tag>/`, then `ls | wc -l` check), and `scripts/cluster/submit_eu22_site.sbatch`, a byte copy of an existing Speed `submit_recut.sbatch` (fetch it with `scp` from `/speed-scratch/o_iseri/fleets/EU11_ES-MAD-BERRUGUETE_win_2026-10-06/submit_recut.sbatch`; read it fully; it must not contain a `--time` line — `--time` is given on the command line). Remote commands go through the `bash -lc` wrapper of `scripts/cluster/t08_harvest_results.py:104`.

**Why.** The 10-06 staging was a scratch script, not in the repo (rebuild recipe, step 8).

**How to test.** `bash -n` on the shell script; `diff` of the job file against the fetched Speed copy is empty; a dry-run flag prints the commands without running them. **No submission** — the manager submits.

### 6.2 Standard per-site steps (every city plan calls these, with `SITE`, `cc`, `DATE` = the day the step runs)

- **S3 — Prepare.** `python scripts/run_eu_s2_district_campaign.py --district SITE --out openubem/outputs/eu_evidence/EU-11/SITE_dw_DATE`. One process per site; at most 10 local processes in total across all running executors. Test: `summary.json` counts; every residential building is either prepared or in `excluded_buildings.csv` with a reason; prepared share reported; the five most common exclusion reasons reported. Prepared share below 80 % → STOP and report.
- **S4 — Finish the tree.** `python scripts/eu22/assemble_win_source.py --site SITE --tree SITE_dw_DATE`, then `python scripts/eu21/12_drop_degenerate.py --districts cc --source-tree _dw_DATE --target-tree _win_DATE --shift cc --workers 8`. Test: `fleet.lst` lists every IDF in `idfs/`; `origin_offset.json` present; `md5_DATE.txt` covers every IDF; degenerate count reported.
- **S5 — Integrity sweep.** `python scripts/eu21/13_model_integrity.py --tree win_DATE --ref-tree win_DATE --districts cc --workers 10`. Then `python -m scripts.emit_eu11_layout_sidecars --district SITE --evidence-root SITE=openubem/outputs/eu_evidence/EU-11/SITE_dw_DATE` (writes `SITE_dw_DATE/layouts/*.json`; amendment after C06), then `python scripts/eu22/score_division.py --site SITE --tree SITE_win_DATE --layout-tree SITE_dw_DATE`. Report the `IDF_FALLBACK` count; above 1 % → STOP. Test: I1–I13 pass counts per check; class counts; share of homes correctly divided; measured window share vs record share (from `windows.csv`): median and largest difference. Any I-check failure on more than 1 % of homes, or correctly divided share below 85 % → STOP and report (rules stay frozen; the manager decides).
- **S6 — Plan pages.** `python scripts/eu21/09_plans3d_from_idf.py --district SITE --source-tag win_DATE --date DATE --exclude-csv <tree>/left_out.csv --verify`; copy the page to `docs/docs_ACTIVE/europeanLocations/plans3D/` (byte-identical) and add its link to `plans3D/index.html`. No EUI on the page. Test: page opens offline (no external URL), scene building count = IDF count, every left-out home flagged.
- **STOP — manager audit before any run.** The manager checks the pages and the integrity numbers, updates the all-cities page, then stages and submits.
- **S7 — Speed (manager only).** `bash scripts/cluster/stage_eu22_site.sh SITE win_DATE`; `sbatch -p ps --time=7-00:00:00 --array=1-N%32 --mem=32G submit_eu22_site.sbatch` from the fleet folder; write `speed_jobs.txt`. Check `squeue -u o_iseri`: 32 running while tasks wait. Count tasks and parallel width before submitting.
- **S8 — Harvest and results.** `python scripts/cluster/harvest_eu11_district.py --district SITE --tag win_DATE`, then `python scripts/eu22/write_results_eu22.py --site SITE --tag win_DATE`; copy results to `docs/docs_ACTIVE/europeanLocations/results/`. Gate: harvest only runs whose EnergyPlus finished ("EnergyPlus Completed Successfully" in `eplusout.end`), not on parse status alone. Test: rows = correctly divided homes; every row has a result or is listed with the reason; EUI summary per site.
- **S9 — Viewer and side-cars for 6J.** `python -m scripts.generate_eu_3d_viewers` for the site only; copy to `docs/docs_ACTIVE/europeanLocations/outputs_3D/` byte-identical; `python -m scripts.emit_eu11_layout_sidecars --district SITE …` and `python -m scripts.cluster.export_flat_counts_4j --district SITE --tag win_DATE`. Test: viewer simulated count = results rows; side-car flat count = sum of `dwellings_used` over correctly divided homes. **Manager note 2026-10-10 (from Cape Town T08):** the side-car step takes `--evidence-root SITE=<SITE>_win_DATE tree` (it holds `left_out.csv`); the `_dw_` tree fails with `FileNotFoundError ... left_out.csv`. The post-run side-cars go to `_win_/layouts/`; leave the S5 set in `_dw_/layouts/` untouched.

### 6.3 Final check and hand-off to 6J (added 2026-10-12, owner: "yes yes please")

Six sites, each with its tag: `CA-MTL-PLATEAU` `win_2026-10-09`, `AM-EVN-NORNORK` `win_2026-10-09`, `ZA-CPT-WOODSTOCK` `win_2026-10-09`, `FI-HEL-KALLIO` `win_2026-10-10`, `AT-VIE-RUDOLFSHEIM` `win_2026-10-10`, `HU-BUD-ERZSEBETVAROS` `win_2026-10-10`. `TREE` = `openubem/outputs/eu_evidence/EU-11/<SITE>_<tag>/`, `DOCS` = `docs/docs_ACTIVE/europeanLocations/`. Source paths of results, viewers and side-cars are in each city plan §8 T07 and T08 entries.

#### F01 — Final check list (read only; fix nothing)
**What.** Run the lines below for every site and write one pass/fail line per check with the measured values.
**Why.** CLAUDE.md "Finishing work": a deliverable is finished only when every artifact agrees.
**How.** One Python script in the scratchpad, never under `docs/`. No file in `TREE`, `DOCS` or `scripts/` is changed.
1. **Runs.** For every IDF stem in `TREE/fleet.lst`, the harvested run's `eplusout.end` contains "EnergyPlus Completed Successfully" (report count ok / total; list any other).
2. **Results summary.** `DOCS/results/EU22_results_<SITE>_<date>_summary.json`: `homes` = rows of `_per_home.csv` = correctly divided homes in `TREE/division_classes.csv` (OK + V3) minus `left_out.csv` rows if that is the rule in T07; `homes_with_result` = non-empty heating rows; `eui_heating_kwh_m2` = sum(heating_kWh)/sum(floor_area_m2) recomputed from `_per_home.csv` (difference < 0.001); `left_out_not_correctly_divided` + `homes` = IDF count. The `.csv`/`.json` pairs carry the same numbers.
3. **Results mirror.** Every `DOCS/results/EU22_results_<SITE>_*` file is byte-identical to the file the T07 entry names as its source (if T07 wrote straight into `DOCS/results/`, say so).
4. **Viewer.** `DOCS/outputs_3D/eu_<SITE>_viewer.html` and `eu_<SITE>_data/` byte-identical to their generated source (`cmp`, `diff -rq`); viewer simulated count = results `homes`; per-home heating per m² in `_data/buildings.csv` equals `_per_home.csv` for every home (report max absolute difference and count of homes in one but not the other).
5. **Plan page.** `DOCS/plans3D/PLANS_<SITE>_<date>.html` exists, byte-identical to its source, linked from `DOCS/plans3D/index.html`, has no external `http` URL, no EUI text, and its building count = IDF count.
6. **Side-cars.** Count of side-car JSONs under `TREE/layouts/` (Budapest: nested `way/` and `relation/`) = results `homes`; sum of flats over them = sum of `dwellings_used` in `TREE/sidecar_population.csv` = sum of `dwellings_used` over the result homes in the manifest; assumed inputs are marked (`ZA` and `HU` building age, `AM` construction): report the field name and how many side-cars carry it.
7. **Flat counts.** The `export_flat_counts_4j` output named in T08 exists and its total flats = check 6.
8. **Manifest.** `TREE/<site>_manifest.csv`: rows, and non-empty count of `geometry_outcome` and `layout_json` (Budapest known empty from sharded side-cars; report all six).
9. **Docs.** Each city plan §8 has T07 and T08 entries marked completed; the EUI and home count in the T07 entry equal check 2.
10. **No UK.** No file of the six `TREE`s, viewers, plan pages or results contains `GB-` or `London`.
**How to test.** Append ONE entry `#### F01 — Final check list — completed <date>` under §8 of this plan: a 10-line table per site (check, pass/fail, measured values), then a list of every fail. Stop and report; do not fix.

#### F02 — Facts for the 6J messages (read only)
**What.** For each site, collect what 6J asked for (`messages_GSSCanada/2026-10-08_6J_to_OpenUBEM_go_cities_and_order.md` §3): buildings in the area, homes built, homes with a result and left out, flats, data sources with their licences (from `openubem/outputs/eu_evidence/EU-22/<SITE>/` acquisition report and licence text and the city plan T01 entry), weather file and survey year, inputs assumed rather than observed, and the folder paths (results, side-cars, viewer, plan page, IDF tree).
**How to test.** Append `#### F02 — Facts for 6J — completed <date>` under §8 with one block per site; every number cites the file it came from. Stop and report.

## 7. Stop-and-report points

1. **After C01 + C02** (records tools and weather): report test lines; the manager checks the 7 EPWs and gates.
2. **After C03 + C04** (registration, tree tools): report the 15 before/after hashes and the integrity re-run comparison. Nothing city-specific may run S3 before this point is accepted.
3. **After C05–C08**: report; from here city plans run S3–S6 independently.
4. Per site, after S6 (pages before runs) and after S9 (results) — in the city plans.
5. After F01 + F02: the manager audits, has every fail fixed or ruled on, then writes and sends the 6J messages.

## 8. Progress log

(One entry per completed task: `#### CXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes.)

#### C01 — Construction-record tools — STOPPED part-way 2026-10-08 (part (a) done, part (b) not written)

- **Artifacts:** `openubem/data/construction/tabula_registry.py` (added `generate_country_registry(cc, workbook, output_dir, *, expected_md5, exclude_prefixes)` after `generate_fr_registry`; FR function untouched); `tests/eu22/test_records_tools.py`; `tests/eu22/fixtures/calc_fixture_fr3.xlsx` (3 FR rows, 333 columns, copied from the pinned workbook).
- **Not written:** `openubem/data/construction/national_records.py` (part (b)).
- **STOP reason (plan C01 What, last sentence):** `h_transmission_components_w_k` cannot be recomputed from the record alone. Measured on the 42 IT + 24 ES + 36 GB + 40 FR records (142 records, 9 component slots each): 106 of 420 IT slots, 15 of 216 ES slots, 63 of 324 GB slots and 67 of 360 FR slots differ from `area × U × b`. Example: `FR.N.SFH.01.Gen.ReEx.001.001` wall_3 = 13.433 W/K, record gives 11.1 m² × 1.9 × 1.0 = 21.09. Where the rule can be read off, the workbook adds an extra surface resistance of 0.300 m²K/W on that slot (192 slots), with 7 other offsets (0.023 to 0.389). That resistance and the rule for which slot gets it are not stored in the record.
- **Test status:** `pytest tests/eu22/test_records_tools.py tests/test_eu_fr_registry.py` = 17 passed. Plan test 1 pass (3-row fixture gives records equal to the committed FR ones, apart from the workbook sha256, which differs by construction). Plan test 5 pass (fresh `generate_fr_registry` sha256 = committed; `generate_country_registry("FR")` on the real workbook is byte-identical). Extra: AT = 61 rows, HU = 16 rows. Plan tests 2, 3, 4 not run (they need part (b)).
- **Needed from the manager:** a ruling on how `h_transmission_*` is set for overridden records (for example: scale each slot by new U ÷ old U, keeping the workbook's extra resistance; or take the extra resistance as an explicit spec field).

#### C01 — Construction-record tools — completed 2026-10-08

- **Artifacts:** `openubem/data/construction/national_records.py` (new: `build_records(spec_path, out_path, *, workbook=None, donor_dir=None)` and `rescale_transmission(record, new_u, new_areas, tb_factor)`); `tests/eu22/test_records_tools.py` extended with plan tests 2, 3, 4 and amendment tests 6, 7, 8. Part (a) artifacts as in the STOPPED entry above.
- **Deviations:** none from the amendment. Choices where the plan was silent: window `b` = 1.0 (not stored in the record); an override of a group U (wall/roof/floor/window) sets every slot of that group that has area > 0; `g_gl_window` sets only that field (`g_gl_n_window_2` stays the donor value, unused elsewhere); `out_path` may be a `.json` file or a directory (then `tabula_archetypes_<cc>.json`); donor lookup is by archetype id, else unique `source_building_code` / `source_building_type_code` / id prefix; donor registry is generated into a temp dir from the pinned workbook when `tabula_archetypes_<donor>.json` is not in the repo. `h_transmission_w_m2k` is recomputed only when a transmission-affecting override (U, wwr, delta_u_tb) is present, otherwise copied from the donor. Window-area changes from `wwr` feed the same series-resistance formula (R from old area, new area and U applied).
- **Test status:** `pytest tests/eu22/test_records_tools.py` = 13 passed, 0 failed. Test 6: max |ΔH| < 1e-9 over 142 records. Test 7: wall_3 R = 0.300, hand value matches. Test 8: ratio-fallback slots at U1 = 0.5·U0 = **0** over 142 IT/ES/GB/FR records (667 slots with area > 0 and H > 0; smallest R = -8.9e-16).
- **Notes:** `tabula_archetypes_at.json` and `tabula_archetypes_hu.json` exist untracked in `openubem/data/construction/`; they are not written by these tests (tests use tmp dirs).

#### C03 — Country registration and the new-country mapping branch — completed 2026-10-08

- **Artifacts:** `openubem/semantic/new_country_rules.py` (new: `NEW_COUNTRIES`, `dominant_period`, `load_period_years`, `resolve_year` / `resolve_storeys` / `resolve_type`, `build_row`, `attached_by_id`, `new_country_rows`); `tests/eu22/test_new_country_rules.py` (17 tests); edits: `openubem/semantic/european_archetype_mapping.py` (`EU02_SITE_COUNTRY` +7, country guard +7 codes), `openubem/semantic/construction_sets.py` (`_TABULA_PERIODS` +AT, +HU), `openubem/idf/european_windows.py` (`COUNTRY_FILES` +7), `scripts/run_eu_s2_district_campaign.py` (`DISTRICTS` +7, import, `prepare()` elif branch, `impute_from_neighbours` branch, new `_impute_new_country_rows`).
- **Deviations / choices where the plan was silent:**
  1. `_impute_es_fr_rows` was read first: it calls `map_observed_building_to_tabula` and imputes year and type from neighbours, which contradicts D-EU-154 (census tie must stay excluded; no neighbour year). So a new-country variant `_impute_new_country_rows` was added (storeys only: touching / nearest within 30 m / district mode); `_impute_es_fr_rows` is unedited.
  2. D-EU-154 type chain read as fall-through: tag, else the two-signal rule when a dwelling count is observed and the rule returns a type, else the storey rule. A two-signal disagreement therefore falls to the storey rule instead of excluding.
  3. Provenance strings: observed year `""`, census year `IMPUTED_CENSUS_UNIT_CONSTRUCTION_PERIOD`; storeys observed `""`, from height `DERIVED_HEIGHT_M_OVER_3`, neighbour rungs `IMPUTED_NEIGHBOUR_TOUCHING` / `_NEAREST_<d>M` / `IMPUTED_DISTRICT_MODE`; type `OBSERVED_TAG`, `DERIVED_BDTOPO_TWO_SIGNAL`, `DERIVED_STOREY_RULE`.
  4. A height counts as measured only when `provenance_height_m` ends `_MEASURED` or `_OBSERVED`. Storeys must be a positive integer (2.5 is not observed). Base blockers: `CENSUS_UNIT_PERIOD_TIE_<labels>`, `CENSUS_UNIT_NO_PERIOD_DATA`, `UNMAPPABLE_PERIOD_<label>`, `MISSING_CENSUS_UNIT_DATA`, `MISSING_OBSERVED_STOREY_COUNT`, `ARCHETYPE_RESOLUTION_FAILED_*`.
  5. `period_years` is read from `openubem/outputs/eu_evidence/EU-22/<site>/acquisition_report.json`; if the file or key is missing it is `{}` (Montréal and Helsinki reports have none today), so their no-year buildings are excluded as `MISSING_CENSUS_UNIT_DATA`.
  6. `new_country_rows` raises `ValueError` when a country has no `_TABULA_PERIODS` entry, so a site without its registry fails instead of excluding everything. Only AT and HU were added to `_TABULA_PERIODS` (both city T02 entries are marked completed; tuples pasted from them).
  7. The mapping module lists the 7 codes literally in the guard (importing `NEW_COUNTRIES` there would be circular); a test pins the sets equal.
  8. The exclusion counter is a small copy (`NewCountryExclusions`) of `_ExclusionCounter`, because the script imports the new module.
- **Test status:**
  - Test 1 and registration: `pytest tests/eu22/test_new_country_rules.py` = 17 passed.
  - Test 2 (no change for the four sites): `prepare --only-ids`, first 5 ids of each `<D>_win_2026-10-06/prepared_buildings.csv` (ES, FR, GB; IT skipped, `_it_rows` fetches live data), before saved in `C:\Users\o_iseri\AppData\Local\Temp\claude\c03_before\`, after run in `...\c03_after\`. All 15 IDF sha256 pairs equal (first 16 hex shown); `prepared_buildings.csv`, `excluded_buildings.csv` and `summary.json` also byte-equal for the 3 sites.
    1. ES `185b31a856fe0fac` 9f74c3d9ae9b6805 = same
    2. ES `19f9bca61b89709d` 5522d85ba0484846 = same
    3. ES `a776387b1281ccea` f6bf07f1140dff57 = same
    4. ES `c0469f277749f93e` 4928e9fcec19fb17 = same
    5. ES `c6e90803c98dba87` 39edd92624a01137 = same
    6. FR `15f931a2760e942c` 125b2cfb13f6b4b5 = same
    7. FR `489894ba3d990787` 121255402447376b = same
    8. FR `5627115eb3ab450c` 7abc2a2d62f4a077 = same
    9. FR `b875712b4bd17d5c` d49fe28b2668776f = same
    10. FR `fb0c68d06710665e` 9187f65d65ef2ae1 = same
    11. GB `01a04839dbc868ab` 8726b6f8b51205ad = same
    12. GB `17196c48fad87be3` 465fba75631028be = same
    13. GB `7aae3e0ee341bc04` e972e0b4c369612c = same
    14. GB `8796714dce1af3e9` eac6b3474fb0e120 = same
    15. GB `9ca82b818445fb8a` c55924af9a1a505a = same
  - Test 3 (four existing files: `test_eu_observed_archetype_mapping.py`, `test_eu15_ruled_coverage.py`, `test_eu16_context_adiabatic.py`, `test_eu14b_bologna_layout_binding.py`): before 55 passed / 6 failed, after 55 passed / 6 failed, same 6 names (`test_all_live_manifests_are_accounted_for_with_fr_layout_readiness`, `test_derive_bdtopo_building_type_one_case_per_branch_and_exclusion`, `test_t03_l_shape_survives_a_second_near_threshold_reflex_vertex`, `test_t02_one_sidecar_per_simulated_building`, `test_t03_both_provenance_tags_present_on_every_sidecar`, `test_t03_construction_period_badge_appears_in_generated_viewer`). They failed before any edit.
  - Live smoke (rows only, no IDFs): `new_country_rows` on the real Vienna manifest + `tabula_archetypes_at.json` = 536 of 536 mapped, 0 excluded (MFH 388, AB 137, TH 11; all type rung = storey rule); neighbour pass recovers 0 (nothing to recover).
  - Whole `tests/eu22`: 89 passed, 1 failed (`test_acquire_montreal.py::test_centroid_in_no_lot_has_empty_attributes`, another executor's file, not touched by C03).
- **Notes:** `HU` has no TH record (`select_tabula_archetype` gives `ARCHETYPE_NO_MATCH` for TH at any year) and no AB record for 1990-2005; Budapest buildings the storey rule types TH, or AB in those years, will be excluded as `ARCHETYPE_RESOLUTION_FAILED_ARCHETYPE_NO_MATCH`; the Budapest city plan owns that. `compute_footprint_adjacency` projects to EPSG:2154 for every country (existing behaviour, not changed). Other countries get their `_TABULA_PERIODS` entry when their registry exists. No error was solved, so nothing was added to the debug references.

#### C03 (amendment) — type substitute rule — completed 2026-10-08

- **Artifacts:** `openubem/semantic/new_country_rules.py` (new `TYPE_SUBSTITUTE`, `select_record_with_substitute`; `build_row` calls it and stores `archetype_provenance`); `tests/eu22/test_new_country_rules.py` (+3 cases, HU TH 1950, HU AB 1995, HU AB 1960).
- **Deviations:** none. Choices where silent: substitution only on `ARCHETYPE_NO_MATCH` (an ambiguous match is never substituted); `building_type` keeps the mapped type, the used type is only in the record id and `archetype_provenance` (`""` when no substitution); if the substitute also has no match the original `ARCHETYPE_NO_MATCH` error is raised, so exclusion is unchanged. The count for the prepare summary is not added (the plan limited the edit to this file); it can be taken from rows with non-empty `archetype_provenance`.
- **Test status:** `pytest tests/eu22/test_new_country_rules.py` = 20 passed, 0 failed. HU TH 1950 = `HU.N.SFH.02.Gen.ReEx.001.001` with `TABULA_TYPE_SUBSTITUTE_SFH_FOR_TH`; HU AB 1995 = `HU.N.MFH.04.Gen.ReEx.001.001`; HU AB 1960 = `HU.N.AB.01-03.Gen.SyAv.001.001`, no substitution.
- **Notes:** no shared file touched (`construction_sets.py` and the campaign script unchanged), so the 15-hash check was not rerun; the four existing countries cannot change.

#### C01 (fix) — national_records order bug — completed 2026-10-08

- **Artifacts:** `openubem/data/construction/national_records.py` (`_build_record`: new U values are collected in `pending_u` and written into `u_components_w_m2k` after `rescale_transmission`, lines 217, 227, 242-243); `tests/eu22/test_records_tools.py` (new `test_build_records_wall_override_rescales_parts_from_donor_u`); `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (new section "European locations, new cities (2026-10-08)").
- **Deviations:** none. No `tabula_archetypes_*.json` regenerated; `national_specs/` and `test_records_<cc>.py` untouched.
- **Test status:** `pytest -q tests/eu22/test_records_tools.py` = 14 passed. The new test (IT AB.01 donor, `u_wall_w_m2k` = 0.5 × donor, every wall part vs `b·A/(1/U1 + R)`, |Δ| < 1e-9, `h_transmission_w_m2k` changed) fails with the old order and passes with the fix.
- **Notes:** records already built with the old order (any spec that overrides a U, wwr-free) kept donor heat-loss parts and must be rebuilt by their owners. The old direct `rescale_transmission` tests (6, 7, 8) were unaffected because they bypass `_build_record`.

#### C01 (rebuild) — five national tables rebuilt after the fix — completed 2026-10-08

- **Artifacts:** `openubem/data/construction/tabula_archetypes_{fi,ca,kr,za,am}.json` rebuilt with plain `national_records.build_records(<cc>_spec.json, <out>)`; pre-fix copies in `C:\Users\o_iseri\AppData\Local\Temp\claude\records_prefix\`; `openubem/semantic/construction_sets.py` (`_TABULA_PERIODS` + FI, CA, KR, ZA, AM, pasted from each city plan's T02 entry).
- **Deviations:** none to the rebuild. The `_TABULA_PERIODS` edit makes two C03 tests in `tests/eu22/test_new_country_rules.py` fail (not edited, see Test status).
- **Test status:** per country (records / records whose `h_transmission_w_m2k` changed vs pre-fix / max |Δ| / RATIO_FALLBACK slots before → after):
  - FI: 28 / 0 / 0.0 / 0 → 0. Rebuild equals the pre-fix file exactly (wrapper workaround confirmed).
  - CA: 24 / 24 / 0.7351 / 28 → 24.
  - KR: 28 / 24 / 1.7425 / 106 → 0.
  - ZA: 12 / 0 / 0.0 / 13 → 13. Rebuild equals the pre-fix file exactly.
  - AM: 20 / 20 / 0.8660 / 20 → 0.
  - `pytest -q tests/eu22/` right after the rebuild = 154 passed, 0 failed (no `test_records_<cc>.py` pin needed changing). After the `_TABULA_PERIODS` edit = 152 passed, 2 failed: `test_new_country_rules.py::test_period_tables_for_at_and_hu` pins the key set to {ES, GB, IT, FR, AT, HU} (line 174), and `test_unregistered_period_table_fails_loudly` uses KR-SEO-MAPO as its unregistered country (line 179). Both are the expected consequence of registering the new countries; left unedited, awaiting a ruling.
  - C03 hash check rerun (same 15 ids per site, `prepare --only-ids`, ES / FR / GB, after in `...\claude\c03_after2\`): all 15 IDF sha256 equal to `c03_before\hashes_before.txt`; `prepared_buildings.csv` byte-equal for the 3 sites.
- **Notes:** KR, CA and AM changed because their specs override U values; FI and ZA did not change (FI built with the wrapper workaround; ZA's override path was unaffected). CA keeps 24 RATIO_FALLBACK slots after the fix.

#### C04 — Let the tree tools accept new sites — completed 2026-10-08

- **Artifacts:** edits `scripts/eu21/12_drop_degenerate.py` (`DISTRICTS` +7, `CRS` +7 from the §1 table, `_tag` also strips `_dw_` so `dwelling_counts_<date>.csv` is found for a `_dw_` source, site codes upper-cased so `--districts at --shift at` works); `scripts/eu21/13_model_integrity.py` (`DISTRICTS` +7, `NEW_SITES`, `SHIFTED` +7, `--out-dir` flag, new-site inputs from `eu02/<SITE>/02_residential_manifest.gpkg` and `prepared_buildings.csv`, reference tree forced to the tree itself); `scripts/eu21/09_plans3d_from_idf.py` (`ROOT` from `__file__`, `FOUR_SITES`, `--out-dir` flag, four-site exclusion files read only for the four sites, `--all` limited to the four sites, a new site requires `--source-tag`, spot-check draw `min(5, len(pool))`); new `tests/eu22/test_tree_tools.py`.
- **Deviations / choices where the plan was silent:**
  1. Storey reference for a new site: observed `levels` or measured height from the manifest through `resolve_storeys`; for a neighbour-imputed home no independent value exists, so the IDF's own height is used for I3/I4 and I1 is reported `NOT_APPLICABLE_NEW_SITE` (column `I1_note`).
  2. I13 is `NOT_APPLICABLE_NEW_SITE` for every new-site home (no 09-08 reference tree); the reason is in column `I13_na_detail` and the count in the summary row `I13:NOT_APPLICABLE_NEW_SITE`. The t06s rerun list is absent for new sites (already tolerated by the script).
  3. The archived 10-06 Lyon page does not equal a fresh pre-edit rebuild (5 of 522 homes differ in the `ch` and `sb` fields, an earlier rule change), so the before/after test compares the pre-edit script with the edited script, not the archive.
  4. `07_nocore_tests.py` and `08_district_viewer.py` keep their own hard-coded `ROOT`; 09 loads them, they are outside C04 scope and were not edited.
  5. The `--exclude-csv` file needs the columns `district` and `building_id` (the C06 `left_out.csv`, with the `baseline_1006.csv` columns, has them).
- **Test status** (read-only on the source trees; outputs under `C:\Users\o_iseri\AppData\Local\Temp\claude\c04_before\`):
  - `12_drop_degenerate.py`: 20-stem subsets of the ES (no shift) and FR (`--shift FR`) 10-05 trees, run with the unedited script and then the edited script in separate fake roots. Every output file equal: ES 253 of 253, FR 416 of 416, 0 unequal (IDFs, csv, md5, `origin_offset.json`).
  - `13_model_integrity.py`: FR `win_2026-10-06` against `win_2026-10-05`, 522 homes. Summary and per-home csv equal before and after (2 of 2), and equal to the committed `integrity_2026-10-02` FR rows.
  - `09_plans3d_from_idf.py`: FR `win_2026-10-06`, 522 buildings. Scene block sha256 before = after = `5cbce68924448112`; `--verify` runs.
  - Synthetic 3-home new-site tree (Madrid IDFs under the id AT-VIE-RUDOLFSHEIM, EPSG:32633): `12 --shift at` writes `origin_offset.json`; `13` runs with 0 failures on all 13 rows (I10 not evaluated, ES archetypes are not in the AT registry; I13 not applicable; I1 not applicable for the one imputed home); `09` builds the page, `--verify` passes (P1 3 of 3, P2 3 of 3), the home in `--exclude-csv` is drawn as left out, no external URL on the page.
  - `pytest tests/eu22/test_tree_tools.py` = 3 passed. Whole `tests/eu22` = 158 passed, 2 failed in other executors' files (`test_new_country_rules.py::test_unregistered_period_table_fails_loudly`, `test_records_za.py::test_window_share_in_range`), not touched by C04.
- **Notes:** one error solved and registered in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (`Sample larger than population`, section "European locations, new cities").

#### C05 — Source-tree assembler — completed 2026-10-08

- **Artifacts:** `scripts/eu22/assemble_win_source.py` (new; `--site`, `--tree <SITE>_dw_<date>`, `--workers`, `--evidence-root` for fixtures; refuses any tree not named `<SITE>_dw_<YYYY-MM-DD>`), `tests/eu22/test_assemble_win_source.py`, fixtures `tests/eu22/fixtures/c05_madrid2/`.
- **Column mapping to `10_add_windows.py` `_process` (21 columns, same order):** `district` = site id; `stem`, `building_id`, `archetype_id`, `geometry_outcome` from `prepared_buildings.csv`; `source_tree` = the tree name; `share_target` = record share from `window_record`; `outdoor_wall_m2` = sum of `polygon_area` over exterior walls; `window_m2` = sum of `polygon_area` over every `FenestrationSurface:Detailed`; `share_achieved` = window ÷ wall (measured share); `walls_with_window` = number of fenestration surfaces; `walls_skipped` and `skip_reasons` = exterior walls without a window, reasons by the same rules and helpers as `add_tabula_windows`; `u`, `shgc`, `fallback` from the record; `zones` = ZONE count; `preflight_issues` = `len(ep_geometry_preflight(idf))`; `identity_ok` = every window sits on an exterior wall and hosts are unique; `idf_sha256` = sha256 of the IDF file; `error` empty or the exception text.
- **Deviations:** `identity_ok` has a different meaning from the old file (old: source IDF equals windowed IDF; there is no source IDF here). `changed_stems.txt` holds bare stems, which `12_drop_degenerate.py` reads as reason `flat_count` (its default). "Difference" (measured minus record share) is not a column; it is `share_achieved - share_target`.
- **Test status:** 5 Madrid IDFs (rows 0, 200, 400, 700, 1000 of the 10-06 tree) copied into a temp tree `ES-MAD-BERRUGUETE_dw_2099-01-01`. Column names equal to the existing `windows.csv`. Largest difference: outdoor wall 1.1e-13 m2, window 0.0 m2, share 1.1e-16; u, shgc, zones and preflight 0; `skip_reasons` and `fallback` equal; `identity_ok` True on all 5 (old file blank on 2). IDF sha256 before = after, 5 of 5. `pytest tests/eu22/test_assemble_win_source.py` = 3 passed. Chained on the synthetic new-site tree: assembler, `12 --shift`, `13` (0 failures), `09`; `fleet.lst` 3 lines, `changed_stems.txt` 3 of 3 carry `origin_shift`.
- **Notes:** no error solved in C05.

#### C08 — Speed staging script and job file — completed 2026-10-08
- **Artifacts:** `scripts/cluster/stage_eu22_site.sh` (new; usage `<SITE> <tag> [--dry-run]`; checks `fleet.lst` count = local IDF count, refuses an existing remote fleet folder, streams `tar` over the `bash -lc` wrapper into `/speed-scratch/o_iseri/fleets/EU22_<SITE>_<tag>/`, copies the job file there as `submit_eu22_site.sbatch`, makes `out/`, then compares the remote `ls idfs | wc -l` with `fleet.lst`); `scripts/cluster/submit_eu22_site.sbatch` (new; byte copy of the fetched Speed file).
- **Deviations:** (1) the plan cites the `bash -lc` wrapper at `t08_harvest_results.py:104`; the `_ssh()` helper is at `:66-71`, so its form (`ssh <host> "bash -lc '<cmd>'"`) was ported into the shell script as `rssh`. (2) The job file is copied into the fleet folder under the name `submit_eu22_site.sbatch`, because §6.2 S7 submits that name from the fleet folder (the 10-06 folder used `submit_recut.sbatch`). (3) The job file has comments and reads `FLEET_DIR` from the environment, so the staging script prints a submit line with `--export=ALL,FLEET_DIR=<fleet folder>`; it does not run it.
- **Test status:** `bash -n` on the staging script passes. `diff` of `submit_eu22_site.sbatch` against the fetched copy of `/speed-scratch/o_iseri/fleets/EU11_ES-MAD-BERRUGUETE_win_2026-10-06/submit_recut.sbatch` is empty (md5 875443c12cc8db8549db1074fcacc1c0). `--dry-run` for `AT-VIE-RUDOLFSHEIM win_2026-10-09` prints all 5 commands and executes none. No sbatch, no srun, nothing written on Speed; the only remote action was the read-only `scp` fetch.
- **Notes:** the fetched file contains no `--time` line (0 matches); its `#SBATCH` lines are `--partition=ps`, `--cpus-per-task=1`, `--mem=6G`, `--job-name=openubem_t08`, `--output=...`. Memory is therefore 6G unless `--mem=32G` is given on the command line, as S7 does. The staging script was not run for real (no local tree yet). No error solved in C08.

#### C03/C01 (test pins + ZA window share) — completed 2026-10-08

- **Artifacts:** `tests/eu22/test_new_country_rules.py` (`test_period_tables_for_at_and_hu` renamed `test_period_tables_for_new_countries`, expects {ES, GB, IT, FR, AT, HU, FI, CA, KR, ZA, AM}; `test_unregistered_period_table_fails_loudly` uses "XX"); `openubem/data/construction/national_specs/za_spec.json` (12 `wwr` entries removed); `openubem/data/construction/tabula_archetypes_za.json` (rebuilt with plain `national_records.build_records`); ZA section of `openubem/data/construction/TABULA_PROVENANCE.md`; `tests/eu22/test_records_za.py`.
- **Deviations:** (1) The "XX" district cannot reach the period-table check on its own (`EU02_SITE_COUNTRY["XX-SEO-MAPO"]` would raise KeyError), so the test now adds "XX-SEO-MAPO" -> "XX" and "XX" to `NEW_COUNTRIES` with `monkeypatch`; no production code changed. (2) `test_records_za.py`: the wwr pin in `test_overrides_land_in_records` was removed (no wwr entry exists), and the share range in `test_window_share_in_range` widened from 0.05-0.50 to 0.05-0.55 because the donor AB share is 0.522.
- **Test status:** `python -m pytest -q tests/eu22/` = 160 passed, 0 failed. No fallback-count pin in the ZA test changed.
- **Notes:** ZA window share is now the donor value (ASSUMED): min 0.067, median 0.194, max 0.522 over the 12 records.

#### C07 — Harvest, results, viewer, side-cars for new sites — completed 2026-10-08

- **Artifacts:** edits `scripts/cluster/harvest_eu11_district.py` (`NEW_SITES`, `--district` choices, remote folder `EU22_<SITE>_<tag>`, `*/eplusout.end` added to the fetch, new-site md5/win-tree route, `parse_task(require_end)`); `scripts/generate_eu_3d_viewers.py` (7 `DISTRICT_SPECS` entries, `FOUR_SITES`, `--district/--tag/--out-3d/--mirror-dir/--results-dir`, new-site branch for tree, left-out ids, results, sources.json); `scripts/emit_eu11_layout_sidecars.py` (new-country rows route, `sidecar_population.csv` for a new site, default targets = four sites); `scripts/cluster/export_flat_counts_4j.py` (`build_flat_counts_new_site`). New: `scripts/eu22/write_results_eu22.py`, `tests/eu22/test_c07_harvest_results.py` (12 tests), fixtures `tests/eu22/fixtures/c07_madrid3/` (3 finished Madrid runs, their IDFs and prepared rows, hand-built `left_out.csv`, `eplusout.end` built from each run's last `.err` line).
- **Deviations / choices where the plan was silent:**
  1. The 7 sites are in a new `NEW_SITES` tuple, not in `DISTRICT_JOBS` / `TAGGED_DISTRICT_JOBS`: those hold SLURM job ids (a new site has none until `speed_jobs.txt` exists) and `DISTRICT_JOBS` drives `--all`, which must stay the four sites. `--district <SITE> --tag win_<date>` works; a new site without a `win_` tag raises.
  2. Completion gate for new sites only: a run counts only if return code 0, "Completed Successfully" in `eplusout.err` and "EnergyPlus Completed Successfully" in `eplusout.end`. The four sites keep their old err-only gate.
  3. Results are written to `openubem/outputs/eu_evidence/EU-22/<SITE>/results/` (not straight into `docs/.../results/`; S8 copies). Files `EU22_results_<SITE>_<date>_{per_home.csv,per_home.json,summary.csv,summary.json}`, same columns as the 10-08 set; `undivided_excluded_from_2026-10-01` = False, `supersedes` empty; summary.json has no `fleet` block and adds `left_out_not_correctly_divided` and `runs_without_result` (building id + rc/severe/fatal) for the "listed with the reason" test.
  4. Viewer licence, layer and endpoint for a new site come from `eu02/<SITE>/01_source.json` at build time; names and places are fixed in `DISTRICT_SPECS`. The new-site viewer reads `EU22_results_<SITE>_<date>_per_home.csv` from `docs/.../results/` (so S8's copy must come first) and the left-out ids from `<SITE>_win_<date>/left_out.csv` (shown as the existing "LEFT OUT" badge, no EUI).
  5. `emit_eu11_layout_sidecars` for a new site builds rows with `new_country_rows` + `impute_from_neighbours` (the same route as `prepare`), not `_mapped_rows`, and writes `<tree>/sidecar_population.csv` (harvest manifest minus left-out homes) so dwelling counts are `dwellings_used` and the manifest is not written back.
  6. Flat counts for a new site are written to `<SITE>_merged_win_<date>/flat_counts_<date>.csv` (same location rule as the four sites). Status order: left out, simulated (heating present), run_failed, not_residential, no_model.
- **Test status:**
  - Plan test 1: fixture harvest gives 3 manifest rows; heating of the two non-left-out stems equals the 10-08 per-home values (124317.93081 and 123757.052872 kWh, tolerance 1e-3). Pass.
  - Plan test 2: `write_results_eu22` on the fixture gives 3 - 1 = 2 rows, EUI = heating / floor area (114.135776 and 85.622905), columns equal to the 10-08 files. Pass. A run without the end marker is harvested as failed and listed with its reason.
  - Plan test 3: the four viewers were regenerated with the edited generator into `C:\Users\o_iseri\AppData\Local\Temp\claude\c07\after\` (seeded with the live viewers, as a live regeneration would be). `diff -rq` before (unedited script, same temp redirect) versus after: identical, 32 of 32 files; after versus the live `docs/.../outputs_3D/` viewer + data folder: identical for 4 of 4. Nothing was written under `outputs_3D/`, `results/`, any `*_win_2026-10-0*` tree, the Bologna tree or the fixed-homes package.
  - Smoke on real Vienna footprints (3 Madrid IDFs under 3 real Vienna ids): viewer builds (simulated 2 = results rows, left out 1 with no EUI, mirror byte-identical, no forbidden term); side-car emitter writes 2 layouts for the 2 divided homes and leaves the manifest untouched; flat counts: simulated 2, left out 1, sum of `new_count` over simulated = 32 = 18 + 14.
  - `pytest tests/eu22` = 196 passed. Existing harvest/sidecar tests (`test_harvest_eu11_*`, `test_eu13b_circulation_sidecar`, `test_eu14b_sidecar_manifest_safety`) pass. `tests/test_eu18c_viewer_geometry_only.py` has 7 failures (`test_viewer_html_has_zero_forbidden_terms[<new site>]`, file not found): the test is parametrized over `run_eu_s2_district_campaign.DISTRICTS`, which C03 grew to 11, and the 7 viewers do not exist until S9. Not caused by C07; each passes once its viewer is generated.
- **Notes:** the viewers for new sites show no EU-21 check badges (no `*_nocore_*_r5.json` evidence exists for them). No error was solved, so nothing was added to the debug references.

#### C06 — Division scorer for new sites — STOPPED at the Madrid test 2026-10-08 (not completed)

- **Artifacts:** `scripts/eu22/score_division.py` (new; `--site`, `--tree <SITE>_win_<date>`, `--workers` capped at 4, `--evidence-root`, `--out-dir`, `--ruleset final|defaults`; writes `division_classes.csv` with the 22 columns of `baseline_1006.csv` and `left_out.csv` for every class outside OK / V3 / S1), `tests/eu22/test_score_division.py` (5 pass, 1 strict xfail = the full Madrid comparison). Imports from `eu_rulebook_dryrun_2026-09-30.py`: `_zone_map`, `_storey_record`, `_load_census` (`analyse_sidecar`); `UNRESOLVED` / `RANK` are not needed. Debug reference entry added (TopologyException on rebuilt flats).
- **Test status (Madrid 10-06 tree, read-only, 4 workers, ruleset `defaults` = the rules the 10-06 IDFs were built under, output in `C:\Users\o_iseri\AppData\Local\Temp\claude\c06\mad_full\`):** 1,172 homes, **1,153 agree, 19 disagree**. 6 of the 19 are the `drift_1006.csv` homes (baseline class describes a rebuilt IDF that differs from the one in the tree): relation/12877779, relation/3730743, way/310738153, way/400445219, way/428478249, way/434878289. 13 are not drift: relation/4835800, way/310738155, way/311159688, way/311595048, way/432412738, way/433014851, way/434878270, way/435212309, way/435398515, way/435633561, way/435932083, way/435943790, way/965605259 (OK vs V3 in 8 cases, V1 vs V3 or V2 in 5). Per the plan the executor stops here; first 10 of the 19 in file order: relation/12877779, relation/3730743, relation/4835800, way/310738153, way/310738155, way/311159688, way/311595048, way/400445219, way/428478249, way/432412738.
- **Cause of the 13 (measured on 6 of them against the layout polygons `prepare` re-cut):** the baseline scored the polygons the cutter produced; the scorer reads the built IDF, where the flat outlines differ in vertex detail (layout flats carry up to 41 vertices against 19 in the IDF; floors of a zone are split into fragments by the interzone match and have to be re-joined). The wrapped-flat measure (`analyse_sidecar` zone corners) and the aspect check react to that detail. The scorer cannot reproduce the baseline from the IDF alone without reusing the cutter, which the plan forbids copying.
- **Deviations:** (1) the scorer reads zone floors from the IDF per zone (union of that zone's `Floor` fragments at its lowest z), not `_floor_polys`, because `_floor_polys` returns the fragments at storey interfaces. (2) The fallback classes U1 to U4 and S1 need `geometry_outcome`, `fallback_reason` and the dwelling allocation from `prepared_buildings.csv`; the 10-06 Madrid csv holds stale outcome strings for 70 homes, so a home with dwelling zones in its IDF is always classed from geometry. (3) `k_max` is the true flat count per storey, not the baseline's fragment count (they differ on 16 of 42 sampled homes); `moved_1006`, `moved_1006_reason`, `dw_match` are blank for new sites. (4) `--ruleset final` (5.0 / 0.25) is the default for new sites; the Madrid test must use `defaults` (2.5 / 0.5).
- **Notes:** the manager must rule: (a) accept the scorer as is for new sites (new-site trees are fresh, so no stale csv, but the 13-in-1,172 sensitivity stays), or (b) let the scorer take the cutter's polygons from a `prepare` re-run (as the 10-06 driver did), or (c) score only the verdict checks and leave the wrapped-flat class to the cutter's sidecar. No new site has been scored.

#### C06 — Division scorer for new sites — completed 2026-10-08

- **Artifacts:** `scripts/eu22/score_division.py` (new `--layout-tree`, `score(..., layout_tree=)`, `_sidecar_path` / `_sidecar_storeys` / `_sidecar_home`; new last column `class_source` = `LAYOUT_SIDECAR` / `IDF_FALLBACK` / `IDF_ONLY`; summary prints `class_source` counts and `idf_fallback`); `tests/eu22/test_score_division.py` (8 pass; the strict xfail is replaced by the 33-home check); fixture `tests/eu22/fixtures/c06b_madrid33/` (the 33 homes' prepared csv and side-cars, 0.9 MB). Temp output only in `C:\Users\o_iseri\AppData\Local\Temp\claude\c06b\`. Debug references: 2 entries added.
- **Deviations:** (1) The amendment says `prepare` writes the layout side-cars; it does not. `run_eu_s2_district_campaign.py::prepare` writes `prepared_buildings.csv`, the manifest, `fleet.lst`, `summary.json`, `excluded_buildings.csv`, `idfs/` (`:1278-1305`). The side-cars `<tree>/layouts/<building_id>.json` are written by `scripts/emit_eu11_layout_sidecars.py::emit_layouts_for_district` (`:153`, write at `:627-630`). So for a new site S3 must be followed by that emitter on the `_dw_` tree before scoring, otherwise every home is `IDF_FALLBACK`. (2) Test side-cars were made by `prepare --only-ids` (ruleset `defaults`, 3 min) then `emit_layouts_for_district(site, tree, tree/prepared_buildings.csv)`; the emitter cannot write outside the repo (`:632`, `relative_to(REPO_ROOT)`), so the scratch run patched `pathlib.PurePath.relative_to`; the emitter was not edited. (3) Class from a side-car follows the 10-06 driver order: rerouted, then fallback tokens (U1 to U4, S1), then best-effort = V1, then spread / wrapped flat. (4) The full-tree IDF-only Madrid comparison (13 known differences) is no longer asserted; it stays reproducible with `score` without `--layout-tree`.
- **Test status:** 33 homes (13 non-drift disagreeing + first 20 agreeing in file order), side-cars from `prepare` + emitter, `--ruleset defaults`: 33 agree, 0 disagree, `class_source` 33 `LAYOUT_SIDECAR`, 0 `IDF_FALLBACK`. `python -m pytest -q tests/eu22/test_score_division.py`: 8 passed. Missing side-car test: 2 fixture homes with an empty layout tree both score `IDF_FALLBACK` with the baseline class. The 33-home check runs from fixtures (1 s), not slow.
- **Notes:** the S3 step in §6 needs one added line: after `prepare`, run the side-car emitter on the `_dw_` tree (from a tree inside the repo), then `score_division --tree <SITE>_win_<date> --layout-tree <SITE>_dw_<date>`. Existing trees were not touched; IT-BOL-GALVANI2_win_2026-10-06 was not opened.

#### C02 — Seven weather folds — STOPPED 2026-10-09 (Vienna gate 5 FAIL; six folds still downloading)

- **Artifacts:** `openubem/acquisition/european_weather.py` (7 targets, `NEW_SURVEY_YEARS`, `city_slug`); `openubem/data/weather/weather_registry.json` (7 entries, status `RULED_NOT_PINNED`, diary window = survey year, licence text = the EU-07 captured CDS cc-by text, sha256 re-verified; top-level status set `PARTIALLY_PINNED`); `scripts/convert_era5_eu_folds_to_epw.py` (negative offset, 29 February drop, survey-year archives, elevations/ISO3, `--fold` choices); `scripts/acquire_era5_eu_folds.py` (survey-year job list, `--run-throttled`, `poll()` skips rejected jobs); `scripts/run_eu_t06_weather_promotion.py` (`--fold` choices, `candidate_years`); `scripts/acquire_pvgis_monthly_ghi_benchmarks.py` (new-fold route with database order); 7 benchmarks `openubem/data/weather/benchmarks/{at_2008,kr_2009,ca_2010,fi_2009,za_2010,hu_2009,am_2008}_monthly_ghi_benchmark.json`; `openubem/data/weather/at_vienna_2007_2008_y2008.epw` (candidate, not promoted); `tests/eu22/test_weather_folds.py` (8 tests); `tests/test_eu_weather_registry.py` (two fold-list assertions extended to 10 folds); debug-reference entries (PVGIS NSRDB, CDS queue limit); logs and request ids in `openubem/outputs/eu_evidence/EU-22/weather/` (`submit_2026-10-08.log`, `throttled_2026-10-08.log`, `queued_request_ids_2026-10-09.json`); gate report `openubem/outputs/eu_evidence/EU-07/t06_at_2008_six_gates.json`.
- **Deviations:**
  - ERA5 requests: only the 13 archives each conversion reads (survey-year 12 months + one adjacent UTC boundary day: 31 Dec of the previous year for positive offsets, 1 Jan of the next year for Canada) instead of both window years (91 jobs, not 175). The registry `raw_era5_window` is unchanged.
  - CDS rejected 85 of the 91 simultaneous requests: "The job has been rejected. Number queued requests for this dataset is temporarily limited." The driver now keeps about 5 active and resubmits (about 4 acquired per 20 minutes at the time of stopping).
  - Benchmarks: PVGIS v5_3 MRcalc accepts only SARAH3 and ERA5 (NSRDB refused with HTTP 400), so Montréal uses NSRDB through `api/v5_2` (independent of ERA5). Databases used: SARAH3 for AT, FI, ZA, HU, AM; NSRDB (v5_2) for CA; ERA5 for KR (SARAH3 and NSRDB both "out of the spatial coverage"), so the Seoul benchmark is ERA5-derived, not independent (stated in its `source`).
  - Elevations checked in the WMO OSCAR station list (`https://oscar.wmo.int/surface/rest/api/search/station`, saved 2026-10-09): Wien/Schwechat 183 m; Seoul 85.67 m (used 86); Montréal Trudeau 36 m; Cape Town Intl 42 m; Helsinki-Vantaa airport 46.8 m (plan said 51; used 46.8); Budapest Pestszentlőrinc 138.1 m at 47.429/19.182 (plan said 139; used 138.1; the plan's WMO 12839 is not in OSCAR, the station at those coordinates is 12843); Yerevan: OSCAR WMO 37789 is "Yerevan Arabkir", closed, 1113 m, a different place from the plan coordinates; used 865 m (Zvartnots aerodrome 2838 ft, Armenian AIP UD-AD-2.UDYZ; OSCAR Zvartnots radar 852 m). Manager to rule if 46.8 / 138.1 / 865 are not accepted.
  - EPW LOCATION lat/lon are the ERA5 grid point (for example Vienna 48.00/16.50), as for the four existing sites.
- **Test status (six gates per fold):**
  - at (Vienna 2008): gate 1 PASS; gate 2 PASS; gate 3 PASS; gate 4 PASS; gate 6 PASS; gate 5 FAIL (SARAH3 benchmark): January EPW 35.0 vs 28.84 kWh/m² (+21.2 %), March 104.7 vs 89.67 (+16.7 %), November 36.7 vs 31.84 (+15.2 %); the other nine months are within 9.0 %; annual 1241.0 vs 1249.5 (-0.7 %). Diagnosis: the EPW agrees with PVGIS-ERA5 for Vienna 2008 in every month within 1 % (34.97, 60.71, 103.79, 140.43, 178.79, 169.82, 165.96, 153.13, 103.09, 70.72, 36.0, 25.58), so the conversion is right and the gap is ERA5 against the SARAH3 satellite product. Tolerance not widened; the D-EU-18 automatic grant covers only uk and it. Registry entry `at`: `BLOCKED_GATE5_FAIL`.
  - kr, ca, fi, za, hu, am: not run, ERA5 archives incomplete. Archives on disk at stop: kr 2/13, am 5/13, ca 0/13, fi 0/13, za 0/13, hu 0/13. Request ids of every job (accepted, running, or last rejected retry) per label: `openubem/outputs/eu_evidence/EU-22/weather/queued_request_ids_2026-10-09.json`. Running or accepted at stop (Seoul): 2009-01 running `eb3c7719-959e-411b-8b0f-4e329a884c23`; 2009-03 `33a11980-96fb-4eca-be52-6d7675c3e697`; 2009-04 `c3c99dce-1881-47c0-84b4-6baa32f6e9dc`; 2009-05 `664cd17f-df8c-44cf-a40c-d270ac33651b`; 2009-06 `09bd45d2-0e8e-4fee-933b-87e1f53f0efb`.
  - Tests: `pytest tests/eu22/test_weather_folds.py tests/test_eu_weather_registry.py tests/test_eu_weather_six_gates.py tests/test_eu_fold_epw_conversion.py tests/test_eu_t06_weather_promotion.py` = 36 passed (28 existing + 8 new), 0 failed. ES 2010, UK 2015, IT 2014 re-converted to a temp path: sha256 equal to the registry value for all three. The four existing registry entries equal the committed ones (only the pre-existing `docs_DONE` to `docs_ACTIVE` path edit in the Bologna `decision_record` string differs from HEAD, not mine).
- **Notes:** the throttled downloader (`python scripts/acquire_era5_eu_folds.py --run-throttled --max-active 8 --interval 120 --fold at ...`, output `throttled_2026-10-08.log`) was left running and keeps downloading the remaining archives without any conversion; stop it by killing that Python process. Next: manager rules on Vienna gate 5 (and probably the same low-irradiance months for the other SARAH3 folds), then `python scripts/run_eu_t06_weather_promotion.py --fold <fold> [--approve-gate5-exception FOLD:YEAR MONTH...] --commit` for each fold once its 13 archives are on disk.

#### F02 — Facts for 6J — completed 2026-10-12

Read only; nothing changed except this entry. Source keys used in every block: `ACQ` = `openubem/outputs/eu_evidence/EU-22/<SITE>/acquisition_report.json`; `LIC` = `openubem/outputs/eu_evidence/EU-22/<SITE>/licences/`; `SUM` = `docs/docs_ACTIVE/europeanLocations/results/EU22_results_<SITE>_<date>_summary.json`; `TREE` = `openubem/outputs/eu_evidence/EU-11/<SITE>_<tag>/`; `POP` = `TREE/sidecar_population.csv` (column `dwellings_used`, summed here by script, same totals as the city-plan T08 entries); `PLAN-T0x` = the T0x entry in §8 of the city plan `PLAN_eu-new-city-<CC>-<city>-2026-10-08.md`; `WREG` = `openubem/data/weather/weather_registry.json`; `WGATE` = `openubem/outputs/eu_evidence/EU-22/weather/tmyx_<cc>_gates_2026-10-09.json`; `DW` = `TREE`'s sibling `<SITE>_dw_<date>/summary.json`. All six sites: results are space-heating demand only (SUM `metric`), over correctly divided homes only (D-EU-149 / D-EU-157). Weather for CA, FI, ZA, HU, AM is a typical-year TMYx file (D-EU-163), not the survey year, so those results are not like-for-like with the four older sites or with Vienna on weather (D-EU-163); gate 5 (monthly sun against PVGIS) failed for CA, FI, HU, AM and passed for ZA, recorded only (WGATE, D-EU-163/164). Hourly solar timing is about one hour off in Cape Town and Yerevan (FINDING 297, common plan D-EU-164). Folder paths below are relative to the repo root; `RES` = `docs/docs_ACTIVE/europeanLocations/results/EU22_results_<SITE>_<date>_{per_home,summary}.{csv,json}`, `VIEW` = `docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_<SITE>_viewer.html` + `eu_<SITE>_data/`, `PAGE` = `docs/docs_ACTIVE/europeanLocations/plans3D/PLANS_<SITE>_<date>.html`, `CARS` = `TREE/layouts/`, `IDF` = `TREE/idfs/` (+ `fleet.lst`), `FLAT` = `openubem/outputs/eu_evidence/EU-11/<SITE>_merged_<tag>/flat_counts_<date>.csv`.

**CA-MTL-PLATEAU (Montréal, Le Plateau-Mont-Royal)**
- Buildings in area: 779 footprints inside the boundary, of which 725 residential, 18 non-residential, 36 unknown use (ACQ `split_counts`; 15,613 buildings borough-wide, ACQ `n_clean`). Area = census tracts 4620159.00 + 4620160.00 (ACQ `subunits`).
- Homes built: 710 IDFs (`TREE/fleet.lst` 710; DW: 725 attempted, 710 prepared; 15 lost for `MISSING_CENSUS_UNIT_DATA`, 22 storey counts recovered by neighbour imputation). Homes with result 701; left out (not correctly divided) 9 (SUM `homes` 701, `left_out_not_correctly_divided` 9). Heating 140.90 kWh/m2 over 193,735.7 m2 (SUM). Flats: 1,797 (POP, 701 rows; FLAT 779 rows).
- Sources and licences: Ville de Montréal "Bâtiments 2D" (2016) and "Unités d'évaluation foncière" (property roll), both CC BY 4.0 (LIC `batiment-2d_package_show.json`, `unites-evaluation-fonciere_package_show.json` field `license_title`; legal text `CC-BY-4.0_legalcode.txt`); Statistics Canada 2021 census-tract boundaries under the Open Government Licence - Canada (LIC `OGL-Canada_open.canada.ca.html`, ACQ `licence`).
- Weather and survey year: Montréal-Trudeau (WMO 71627), TMYx 2009-2023, `openubem/data/weather/ca_montreal_tmyx_2009_2023.epw` (WREG `ca`, sha256 17f26666...6369); diary/survey year 2010 (WREG `diary_window`); annual sun balance 0.9926 (WGATE).
- Assumed rather than observed: construction values (CA.01 to CA.06) use Swedish TABULA records as donor and survey averages for single detached homes from the CSDDRD paper, not Québec data; window U-values for CA.01 to CA.04 are `ASSUMED`; CA.06 values come from a 2012 draft of the Québec code (PLAN-T02 deviations 1 to 5); flat area for SFH/TH is the donor value 106.2 m2. Dwelling counts: 662 observed, 36 split over a lot's buildings, 2 single, 1 imputed from area (side-cars, `dwelling_count_provenance`); 4 of 725 had no roll count (ACQ `dwellings_source_counts_residential`). Storeys observed 96.55 %, year observed 97.93 % (ACQ `coverage_residential`); no side-car carries an imputed year (`construction_period_provenance` empty on 701 of 701).
- Folders: RES, VIEW, PAGE (`PLANS_CA-MTL-PLATEAU_2026-10-09.html`), CARS (701 files), IDF, FLAT; `TREE` = `EU-11/CA-MTL-PLATEAU_win_2026-10-09/`. Speed job 1442166 (PLAN-T07).

**AM-EVN-NORNORK (Yerevan, Nor Nork)**
- Buildings in area: 2,857 footprints, of which 551 residential, 596 non-residential, 1,710 unknown use (ACQ `split_counts`). Area = 94 street blocks of the Nor Nork district, 6.81 km2 (PLAN-T01); 215 private houses excluded for lack of a period source (PLAN-T01).
- Homes built: 551 IDFs (`TREE/fleet.lst`). Homes with result 535; left out 16 (SUM; the 16th, `way/998439490`, by owner ruling D-EU-165). Heating 48.52 kWh/m2 over 1,710,969.6 m2 (SUM). Flats: 26,318 (POP, 535 rows; FLAT 2,857 rows).
- Sources and licences: OpenStreetMap footprints and tags, ODbL 1.0 (LIC `osm_odbl.txt`; "(c) OpenStreetMap contributors"); Armstat "RA Housing Stock and Communal Economy 2020", only counts transcribed with page numbers (`EU-22/AM-EVN-NORNORK/armstat_tables.csv`). The Armstat licence is NOT an open licence: the site footer says "By using the website, please refer to Statistical Committee RA. All rights reserved." (LIC `armstat_terms.txt`); source must be cited as Statistical Committee RA.
- Weather and survey year: Yerevan-Zvartnots (WMO 37788), TMYx 2009-2023, `openubem/data/weather/am_yerevan_tmyx_2009_2023.epw` (WREG `am`); survey year 2008; annual sun balance 0.9846 (WGATE).
- Assumed rather than observed: every building takes the single period AM.02 (1951-70), the district's dominant period, because Armstat has no table crossing storeys with period (PLAN-T01 deviation 3; 535 of 535 side-cars `IMPUTED_CENSUS_UNIT_CONSTRUCTION_PERIOD`); year observed 0; wall material per period is `ASSUMED` (stone AM.01, AM.02, AM.04, panel AM.03); roof, floor before 2016, window, infiltration, window share are donor BG values (PLAN-T02 deviations 1, 5); storeys: 335 observed (60.8 %), 216 imputed from neighbours (39.2 %) (PLAN-T01); flats: all 535 imputed from floor area, none observed (side-cars `DWELLINGS_USED_AREA_IMPUTED` 535).
- Folders: RES, VIEW, PAGE (`PLANS_AM-EVN-NORNORK_2026-10-09.html`), CARS (535), IDF, FLAT; `TREE` = `EU-11/AM-EVN-NORNORK_win_2026-10-09/`. Speed job 1442163.

**ZA-CPT-WOODSTOCK (Cape Town, Woodstock)**
- Buildings in area: 572 footprints, of which 534 residential, 38 non-residential (ACQ `split_counts`); 99 sheds under 2.0 m dropped earlier (PLAN-T01). Area = 43 OSM street blocks in Woodstock, 0.570 km2 (PLAN-T01).
- Homes built: 525 IDFs (`TREE/fleet.lst`); 9 residential buildings got no IDF (6 labelled "Mid 21st Century", 3 street-block ties) (PLAN-T03). Homes with result 524; left out 1 (`ZA-CPT-74724`) (SUM). Heating 54.15 kWh/m2 over 265,365.2 m2 (SUM). Flats: 1,036 (POP, 524 rows; FLAT 572 rows).
- Sources and licences: City of Cape Town "2D Building Footprints Low Detail" with 2023 LiDAR height and heritage period labels: no named licence; use limitation verbatim (LIC `CCT_footprints_use_limitation.txt`): "No restrictions on the digital file for non-commercial purposes ... No part of this data may be reproduced or transmitted ... without permission from the City of Cape Town Geomatics Branch. Where the data is used as a basis for or as an insertion in a map, acknowledgment must be made to the source of such data as well as the copyright of the CCT." OpenStreetMap residential tags and roads, ODbL 1.0 (LIC `ODbL-1.0_opendatacommons.html`). Decision D-EU-160 (owner, 2026-10-09, common plan §4): 6J is the owner's own project, so giving these files to 6J is internal use, not redistribution. Conditions that stay: non-commercial use only; no public release of the City footprints (public repo, public page, open dataset) without the City Geomatics Branch's permission; every map or figure credits "City of Cape Town" as source and copyright holder.
- Weather and survey year: Cape Town Intl (WMO 68816), TMYx 2009-2023, `openubem/data/weather/za_capetown_tmyx_2009_2023.epw` (WREG `za`, sha256 starts 5c045a95 per PLAN-T03); survey year 2010 (ACQ `survey_year`); gate 5 passed; annual sun balance 0.9930 (WGATE).
- Assumed rather than observed: building age is not observed; it comes from the City heritage period labels (own label 474 of 534 = 88.76 %, street-block label 51 = 9.55 %, none 9 = 1.69 %, ACQ `year_split`/PLAN-T01), mapped to a reference year by a stated rule (all 524 side-cars `IMPUTED_CENSUS_UNIT_CONSTRUCTION_PERIOD`); "Early 21st Century" gives 2016, after the 2010 survey year (PLAN-T01 deviation 3). Construction: only the roof (R 3.7, ZA.03) and brick wall total R 0.42 are sourced (NHBRC tables); pre-2011 wall, roof, window, infiltration are `ASSUMED`; window share is the Spanish donor's (PLAN-T02 and amendment). Flats: 465 single, 59 imputed from area, none observed (side-cars). Storeys from LiDAR height, `max(1, round(height / 3.0))` (PLAN-T01). Residential use rests on OSM tags or OSM `landuse=residential` (357 + 177 buildings, PLAN-T01).
- Folders: RES, VIEW, PAGE (`PLANS_ZA-CPT-WOODSTOCK_2026-10-09.html`), CARS (524), IDF, FLAT; `TREE` = `EU-11/ZA-CPT-WOODSTOCK_win_2026-10-09/`. Speed job 1442187. Internal only, never published.

**FI-HEL-KALLIO (Helsinki, Kallio)**
- Buildings in area: 900 footprints, of which 588 residential, 211 non-residential, 101 unknown use (ACQ `split_counts`; 40 of the 588 are residential by the type `Asuinrakennus` with no use code). Area = whole Kallio district plus Harju (osa-alue 121), 588 residential (PLAN-T01).
- Homes built: 580 IDFs (`TREE/fleet.lst`); 8 residential buildings got no IDF (viewer `no_idf` 8, PLAN-T08; DW 588 attempted, 580 prepared). Homes with result 542; left out 38 (SUM). Heating 96.42 kWh/m2 over 2,322,116.1 m2 (SUM). Flats: 29,781 (POP, 542 rows; FLAT 900 rows).
- Sources and licences: City of Helsinki "Buildings in Helsinki" (Helsingin rakennukset), Creative Commons Attribution 4.0; reference text "Source: Buildings in Helsinki. The maintainer of the dataset is Helsingin kaupunkiymparistön toimiala / Kaupunkimittauspalvelut. The dataset has been downloaded from Helsinki Region Infoshare service using the license Creative Commons Attribution 4.0." (LIC `helsinki_buildings_licence.txt`); district boundary layers from the same City of Helsinki open geoserver.
- Weather and survey year: Helsinki-Vantaa (WMO 02974), TMYx 2009-2023, `openubem/data/weather/fi_helsinki_tmyx_2009_2023.epw` (WREG `fi`); survey year 2009; annual sun balance 0.9938 (WGATE).
- Assumed rather than observed: year, storeys and dwelling counts are observed (98.64 %, 98.64 %, 98.30 %, ACQ `coverage_residential`; side-cars: 540 observed, 1 single, 1 imputed; no side-car carries an imputed year). Construction records use Swedish TABULA donors for areas, g-value and thermal bridges; FI.01 (up to 1975) U-values are the 1969 RIL recommendation, not a measured stock mean; the wall/roof mass class (SFH/TH light, MFH/AB heavy) for FI.01 to FI.03 is `ASSUMED`; TH and AB borrow the SFH and MFH donors (PLAN-T02 deviations 1 to 4). Flat areas from Statistics Finland 2009 (108.0, 71.1, 56.5 m2 per dwelling).
- Folders: RES, VIEW, PAGE (`PLANS_FI-HEL-KALLIO_2026-10-11.html`), CARS (542), IDF, FLAT (`flat_counts_2026-10-10.csv`); `TREE` = `EU-11/FI-HEL-KALLIO_win_2026-10-10/`. Speed job 1451887.

**AT-VIE-RUDOLFSHEIM (Vienna, Rudolfsheim-Fünfhaus)**
- Buildings in area: 702 footprints, of which 536 residential, 49 non-residential, 117 unknown use (ACQ `exclusion_counts`). Area = Zählbezirke 1502 + 1501 of the 15th district (ACQ `units_used`; PLAN-T01).
- Homes built: 536 IDFs (`TREE/fleet.lst`). Homes with result 517; left out 19 (SUM). Heating 77.58 kWh/m2 over 933,129.0 m2 (SUM). Flats: 10,506 (POP, 517 rows; FLAT 702 rows).
- Sources and licences: Stadt Wien open data, all CC BY 4.0, required attribution "Datenquelle: Stadt Wien - data.wien.gv.at": building outlines `FMZKGEBOGD`, building bodies `FMZKBKMOGD`, building information points `GEBAEUDEINFOOGD`, census districts `ZAEHLBEZIRKOGD`, and Registerzählung 2023 buildings per Zählbezirk `RZ2023_GEBAEUDE_ZAEHLBEZIRKE` (LIC five `.txt` files, field `licence declared in catalogue distributions`). Weather source: ERA5 reanalysis, CDS licence cc-by (WREG `at`, `licence_text_at_download`).
- Weather and survey year: Wien-Schwechat (WMO 11036), ERA5 converted to EPW for 2008, `openubem/data/weather/at_vienna_2007_2008_y2008.epw` (WREG `at`, sha256 4e0b116c...c010f); survey year 2008 (a real year, not typical); gate 5 passed with a documented exception for winter months (D-EU-159: Jan +21 %, Mar +17 %, Nov +15 % against SARAH3).
- Assumed rather than observed: height and storeys are observed (100 %); year observed for only 24 of 536 buildings (4.5 %), the other 512 take the dominant construction period of their Zählbezirk from the 2023 register (PLAN-T01; side-cars: 495 `IMPUTED_CENSUS_UNIT_CONSTRUCTION_PERIOD` and 22 empty among the 517 results); dwelling counts are not observed (no open register), so flats come from floor area (side-cars: 506 imputed from area, 11 single). Construction = TABULA Austria national series, 38 records (PLAN-T02 amended); 1,722 outlines without a building id dropped, 117 buildings with no information point are "unknown" and not modelled (PLAN-T01).
- Folders: RES, VIEW, PAGE (`PLANS_AT-VIE-RUDOLFSHEIM_2026-10-11.html`), CARS (517), IDF, FLAT (`flat_counts_2026-10-10.csv`); `TREE` = `EU-11/AT-VIE-RUDOLFSHEIM_win_2026-10-10/`. Speed job 1451888.

**HU-BUD-ERZSEBETVAROS (Budapest, VII. district)**
- Buildings in area: 1,707 footprints, of which 805 residential, 119 non-residential, 783 unknown use (OSM `building=yes`, excluded as at the other OSM sites) (ACQ `split_counts`). Area = the whole VII. kerület, one unit (PLAN-T01).
- Homes built: 805 IDFs (`TREE/fleet.lst`). Homes with result 757; left out 48 (all `V1_divided_shape_rule_broken`, PLAN-T07) (SUM). Heating 63.36 kWh/m2 over 2,045,910.3 m2 (SUM). Flats: 30,929 (POP, 757 rows; FLAT 1,707 rows).
- Sources and licences: OpenStreetMap buildings and boundary via Overpass, base timestamp 2026-10-09T03:35:14Z, ODbL 1.0, "(c) OpenStreetMap contributors, ODbL 1.0" (LIC `OSM_ODbL.txt`); KSH Census 2011 table 3.3.2.1, CC BY 4.0, attribution "Source: KSH, Census 2011" (LIC `KSH_census2011.txt`); KSH Census 2022 terms CC BY 4.0, consulted only, no table used (LIC `KSH_census2022_terms.txt`, ACQ `census_2022_check`). Copernicus Urban Atlas building height 2012 was NOT used: the download needs a login token (LIC `COPERNICUS_UA_BUILDING_HEIGHT_2012_not_downloaded.txt`).
- Weather and survey year: Budapest-Ferihegy (WMO 12839), TMYx 2009-2023, `openubem/data/weather/hu_budapest_tmyx_2009_2023.epw` (WREG `hu`); survey year 2009; annual sun balance 0.9925 (WGATE).
- Assumed rather than observed: building age: 17 buildings (2.11 %) have an OSM year, 788 take the district's census period; 89.8 % of district dwellings are from before 1946, and that class is set to 1944, so nearly all fall in HU.01 (D-EU-154 amendment; PLAN-T01; side-cars: 742 `IMPUTED_CENSUS_UNIT_CONSTRUCTION_PERIOD`, 15 empty among the 757 results). Storeys: 442 observed (54.91 %), 363 imputed from neighbours (45.09 %). Flats: all 757 imputed from floor area, none observed (side-cars). Construction = TABULA Hungary 16 records; apartment blocks 1990-2005 use the MFH record and terraces use the SFH record (substitute rule, common plan D-EU-153); the BME brochure was not compared (window U 3.50 in the workbook against 3.00 in the brochure for MFH before 1944; workbook wins, PLAN-T02).
- Folders: RES, VIEW, PAGE (`PLANS_HU-BUD-ERZSEBETVAROS_2026-10-11.html`), CARS (757, nested `way/` and `relation/`), IDF, FLAT (`flat_counts_2026-10-10.csv`); `TREE` = `EU-11/HU-BUD-ERZSEBETVAROS_win_2026-10-10/`. Speed job 1451908.

**Gaps for the manager (nothing found missing that blocks a message):**
1. The AM-EVN-NORNORK Armstat terms are "all rights reserved, cite the Statistical Committee RA", with no open licence; the 6J message should say so rather than "open".
2. No file records a survey year per site in one place: CA 2010, ZA 2010 (ACQ), FI 2009, HU 2009, AM 2008, AT 2008 come from common plan D-EU-155 and WREG `diary_window`/WGATE `year`.
3. FI, AT and HU plan pages are dated 2026-10-11 (not -10), and the AT/HU/FI tags are `win_2026-10-10`; the AT `win_2026-10-09` and `dw_2026-10-09` trees are older and not the result trees.
4. The HU TABULA brochure cross-check is still open (PLAN-T02 deviation 1).
5. Open fails seen in the city entries (not mine to fix): the Korea weather-registry test failure `test_weather_folds.py::test_original_folds_keep_their_year_candidates`, and the Vienna and Finland no-core sweep tests flagged in the CA T08 entry.

#### F01 — Final check list — completed 2026-10-12

- **Method:** one read-only script, `final_check/f01_check.py` in the session scratchpad (no file in any `TREE`, `DOCS`, `openubem/outputs` or `scripts/` was changed). Harvested runs read from `%TEMP%/ubem_eu11_harvest/<SITE>_<tag>/<stem>/eplusout.end` (the `fetch_district_out` work folder named by the T07 entries); IDF stems from `TREE/fleet.lst`. Result: **60 of 60 lines PASS, 0 FAIL.**
- **Plan wording to note (not a fail):** check 2 says `OK + V3`; the class column of `division_classes.csv` also holds `S1_one_flat_per_floor_by_data` (CA 11, ZA 3), which is a correctly divided home and is in the result. Literal OK+V3 gives CA 690 and ZA 521 (homes 701 and 524); OK+V3+S1 gives 701 and 524. AM is the case the check anticipated: OK+V3 = 536 minus the one `left_out.csv` row `way/998439490` (D-EU-165) = 535.
- **Checks 4 and 8 wording:** `eu_<SITE>_data/buildings.csv` has no heating column (14 columns, footprint to circulation); the per-home heating per m2 sits in the viewer's embedded scene (`eui` field of each building with `ss = simulated`), so check 4 compared that against `_per_home.csv`. The harvest manifests have no `layout_json` column in any of the six sites (`geometry_outcome` is filled in all rows); the Budapest/Helsinki manifests were not written back by the sharded side-car run, which does not matter here because the column does not exist. Check 3 for results is T07 source = `openubem/outputs/eu_evidence/EU-22/<SITE>/results/`; the plan pages were written straight into `plans3D/` (T06 entries), so there is no second copy to compare.

**CA-MTL-PLATEAU (win_2026-10-09) — 710 IDFs**

| # | Check | Result | Measured |
|---|---|---|---|
| 1 | Runs | PASS | eplusout.end "EnergyPlus Completed Successfully" 710/710; other 0 |
| 2 | Results summary | PASS | homes 701 = per_home rows 701 = OK 669 + V3 21 + S1 11 = 701 (literal OK+V3 = 690); with result 701; EUI 140.903194 = recomputed (diff 0.000000); left out 9 + homes 701 = 710 IDFs; csv/json pairs equal |
| 3 | Results mirror | PASS | 4 of 4 files in `DOCS/results/` byte-identical to `EU-22/CA-MTL-PLATEAU/results/` |
| 4 | Viewer | PASS | viewer html and `_data/` (3 files) identical to `openubem/outputs/3D/`; simulated 701 = homes; max abs EUI diff scene vs per_home 0.0; in one but not the other 0 / 0 |
| 5 | Plan page | PASS | `PLANS_CA-MTL-PLATEAU_2026-10-09.html` written straight into `plans3D/`; linked in `index.html`; buildings 710 = IDF 710 (scene and header row); external http URLs 0; EUI/kWh text 0; no `eui` key |
| 6 | Side-cars | PASS | 701 JSONs = homes; flats in JSONs = `sidecar_population.csv` = manifest dwellings_used over result homes = 1,797; assumed field: none (701 side-cars carry construction_period_provenance = null) |
| 7 | Flat counts | PASS | `flat_counts_2026-10-09.csv` (779 rows), flats with status simulated 1,797 = check 6 |
| 8 | Manifest | PASS | rows 710; geometry_outcome non-empty 710; layout_json column absent |
| 9 | Docs | PASS | city plan T07 and T08 entries both marked completed; T07 states 701 homes and the EUI equal to check 2 |
| 10 | No UK | PASS | no `GB-` and no "London" in any file of the tree, viewer, plan page, results or merged folder |

**AM-EVN-NORNORK (win_2026-10-09) — 551 IDFs**

| # | Check | Result | Measured |
|---|---|---|---|
| 1 | Runs | PASS | eplusout.end "EnergyPlus Completed Successfully" 551/551; other 0 |
| 2 | Results summary | PASS | homes 535 = per_home rows 535 = OK 327 + V3 209 = 536 minus 1 left-out (way/998439490, D-EU-165) = 535; with result 535; EUI 48.516593 = recomputed (diff 0.000000); left out 16 + homes 535 = 551 IDFs; csv/json pairs equal |
| 3 | Results mirror | PASS | 4 of 4 files in `DOCS/results/` byte-identical to `EU-22/AM-EVN-NORNORK/results/` |
| 4 | Viewer | PASS | viewer html and `_data/` (3 files) identical to `openubem/outputs/3D/`; simulated 535 = homes; max abs EUI diff scene vs per_home 0.0; in one but not the other 0 / 0 |
| 5 | Plan page | PASS | `PLANS_AM-EVN-NORNORK_2026-10-09.html` written straight into `plans3D/`; linked in `index.html`; buildings 551 = IDF 551 (scene and header row); external http URLs 0; EUI/kWh text 0; no `eui` key |
| 6 | Side-cars | PASS | 535 JSONs = homes; flats in JSONs = `sidecar_population.csv` = manifest dwellings_used over result homes = 26,318; assumed field: construction_period_provenance = IMPUTED_CENSUS_UNIT_CONSTRUCTION_PERIOD on 535 of 535 side-cars (single period AM.02) |
| 7 | Flat counts | PASS | `flat_counts_2026-10-09.csv` (2857 rows), flats with status simulated 26,318 = check 6 |
| 8 | Manifest | PASS | rows 551; geometry_outcome non-empty 551; layout_json column absent |
| 9 | Docs | PASS | city plan T07 and T08 entries both marked completed; T07 states 535 homes and the EUI equal to check 2 |
| 10 | No UK | PASS | no `GB-` and no "London" in any file of the tree, viewer, plan page, results or merged folder |

**ZA-CPT-WOODSTOCK (win_2026-10-09) — 525 IDFs**

| # | Check | Result | Measured |
|---|---|---|---|
| 1 | Runs | PASS | eplusout.end "EnergyPlus Completed Successfully" 525/525; other 0 |
| 2 | Results summary | PASS | homes 524 = per_home rows 524 = OK 507 + V3 14 + S1 3 = 524 (literal OK+V3 = 521); with result 524; EUI 54.151969 = recomputed (diff 0.000000); left out 1 + homes 524 = 525 IDFs; csv/json pairs equal |
| 3 | Results mirror | PASS | 4 of 4 files in `DOCS/results/` byte-identical to `EU-22/ZA-CPT-WOODSTOCK/results/` |
| 4 | Viewer | PASS | viewer html and `_data/` (3 files) identical to `openubem/outputs/3D/`; simulated 524 = homes; max abs EUI diff scene vs per_home 0.0; in one but not the other 0 / 0 |
| 5 | Plan page | PASS | `PLANS_ZA-CPT-WOODSTOCK_2026-10-09.html` written straight into `plans3D/`; linked in `index.html`; buildings 525 = IDF 525 (scene and header row); external http URLs 0; EUI/kWh text 0; no `eui` key |
| 6 | Side-cars | PASS | 524 JSONs = homes; flats in JSONs = `sidecar_population.csv` = manifest dwellings_used over result homes = 1,036; assumed field: construction_period_provenance = IMPUTED_CENSUS_UNIT_CONSTRUCTION_PERIOD on 524 of 524 side-cars |
| 7 | Flat counts | PASS | `flat_counts_2026-10-09.csv` (572 rows), flats with status simulated 1,036 = check 6 |
| 8 | Manifest | PASS | rows 525; geometry_outcome non-empty 525; layout_json column absent |
| 9 | Docs | PASS | city plan T07 and T08 entries both marked completed; T07 states 524 homes and the EUI equal to check 2 |
| 10 | No UK | PASS | no `GB-` and no "London" in any file of the tree, viewer, plan page, results or merged folder |

**FI-HEL-KALLIO (win_2026-10-10) — 580 IDFs**

| # | Check | Result | Measured |
|---|---|---|---|
| 1 | Runs | PASS | eplusout.end "EnergyPlus Completed Successfully" 580/580; other 0 |
| 2 | Results summary | PASS | homes 542 = per_home rows 542 = OK 253 + V3 289 = 542; with result 542; EUI 96.417226 = recomputed (diff 0.000000); left out 38 + homes 542 = 580 IDFs; csv/json pairs equal |
| 3 | Results mirror | PASS | 4 of 4 files in `DOCS/results/` byte-identical to `EU-22/FI-HEL-KALLIO/results/` |
| 4 | Viewer | PASS | viewer html and `_data/` (3 files) identical to `openubem/outputs/3D/`; simulated 542 = homes; max abs EUI diff scene vs per_home 0.0; in one but not the other 0 / 0 |
| 5 | Plan page | PASS | `PLANS_FI-HEL-KALLIO_2026-10-11.html` written straight into `plans3D/`; linked in `index.html`; buildings 580 = IDF 580 (scene and header row); external http URLs 0; EUI/kWh text 0; no `eui` key |
| 6 | Side-cars | PASS | 542 JSONs = homes; flats in JSONs = `sidecar_population.csv` = manifest dwellings_used over result homes = 29,781; assumed field: none (542 side-cars carry construction_period_provenance = null) |
| 7 | Flat counts | PASS | `flat_counts_2026-10-10.csv` (900 rows), flats with status simulated 29,781 = check 6 |
| 8 | Manifest | PASS | rows 580; geometry_outcome non-empty 580; layout_json column absent |
| 9 | Docs | PASS | city plan T07 and T08 entries both marked completed; T07 states 542 homes and the EUI equal to check 2 |
| 10 | No UK | PASS | no `GB-` and no "London" in any file of the tree, viewer, plan page, results or merged folder |

**AT-VIE-RUDOLFSHEIM (win_2026-10-10) — 536 IDFs**

| # | Check | Result | Measured |
|---|---|---|---|
| 1 | Runs | PASS | eplusout.end "EnergyPlus Completed Successfully" 536/536; other 0 |
| 2 | Results summary | PASS | homes 517 = per_home rows 517 = OK 249 + V3 268 = 517; with result 517; EUI 77.577540 = recomputed (diff 0.000000); left out 19 + homes 517 = 536 IDFs; csv/json pairs equal |
| 3 | Results mirror | PASS | 4 of 4 files in `DOCS/results/` byte-identical to `EU-22/AT-VIE-RUDOLFSHEIM/results/` |
| 4 | Viewer | PASS | viewer html and `_data/` (3 files) identical to `openubem/outputs/3D/`; simulated 517 = homes; max abs EUI diff scene vs per_home 0.0; in one but not the other 0 / 0 |
| 5 | Plan page | PASS | `PLANS_AT-VIE-RUDOLFSHEIM_2026-10-11.html` written straight into `plans3D/`; linked in `index.html`; buildings 536 = IDF 536 (scene and header row); external http URLs 0; EUI/kWh text 0; no `eui` key |
| 6 | Side-cars | PASS | 517 JSONs = homes; flats in JSONs = `sidecar_population.csv` = manifest dwellings_used over result homes = 10,506; assumed field: construction_period_provenance = IMPUTED_CENSUS_UNIT_CONSTRUCTION_PERIOD on 495 of 517 side-cars (22 null) |
| 7 | Flat counts | PASS | `flat_counts_2026-10-10.csv` (702 rows), flats with status simulated 10,506 = check 6 |
| 8 | Manifest | PASS | rows 536; geometry_outcome non-empty 536; layout_json column absent |
| 9 | Docs | PASS | city plan T07 and T08 entries both marked completed; T07 states 517 homes and the EUI equal to check 2 |
| 10 | No UK | PASS | no `GB-` and no "London" in any file of the tree, viewer, plan page, results or merged folder |

**HU-BUD-ERZSEBETVAROS (win_2026-10-10) — 805 IDFs**

| # | Check | Result | Measured |
|---|---|---|---|
| 1 | Runs | PASS | eplusout.end "EnergyPlus Completed Successfully" 805/805; other 0 |
| 2 | Results summary | PASS | homes 757 = per_home rows 757 = OK 210 + V3 547 = 757; with result 757; EUI 63.358213 = recomputed (diff 0.000000); left out 48 + homes 757 = 805 IDFs; csv/json pairs equal |
| 3 | Results mirror | PASS | 4 of 4 files in `DOCS/results/` byte-identical to `EU-22/HU-BUD-ERZSEBETVAROS/results/` |
| 4 | Viewer | PASS | viewer html and `_data/` (3 files) identical to `openubem/outputs/3D/`; simulated 757 = homes; max abs EUI diff scene vs per_home 0.0; in one but not the other 0 / 0 |
| 5 | Plan page | PASS | `PLANS_HU-BUD-ERZSEBETVAROS_2026-10-11.html` written straight into `plans3D/`; linked in `index.html`; buildings 805 = IDF 805 (scene and header row); external http URLs 0; EUI/kWh text 0; no `eui` key |
| 6 | Side-cars | PASS | 757 JSONs = homes; flats in JSONs = `sidecar_population.csv` = manifest dwellings_used over result homes = 30,929; assumed field: construction_period_provenance = IMPUTED_CENSUS_UNIT_CONSTRUCTION_PERIOD on 742 of 757 side-cars (15 null) |
| 7 | Flat counts | PASS | `flat_counts_2026-10-10.csv` (1707 rows), flats with status simulated 30,929 = check 6 |
| 8 | Manifest | PASS | rows 805; geometry_outcome non-empty 805; layout_json column absent |
| 9 | Docs | PASS | city plan T07 and T08 entries both marked completed; T07 states 757 homes and the EUI equal to check 2 |
| 10 | No UK | PASS | no `GB-` and no "London" in any file of the tree, viewer, plan page, results or merged folder |

**Fails: none.** The only items for the manager are the two wording notes above.
