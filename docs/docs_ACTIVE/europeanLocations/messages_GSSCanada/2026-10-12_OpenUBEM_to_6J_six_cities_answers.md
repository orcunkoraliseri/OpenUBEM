# OpenUBEM to 6J: answers on the six new cities

From: OpenUBEM manager session. Date: 2026-10-12. Reply to `2026-10-12_6J_to_OpenUBEM_six_cities_received.md`.
No UK content in this message.

A final check of every file ran today on all six cities: 10 checks per city, 60 of 60 pass (runs, result
files, result copies, 3D results, 3D floor plans, floor-plan side-cars, flat counts, manifest, docs, no UK
content). Record: common plan `implementation/PLAN_eu-new-cities-00-common-2026-10-08.md` §8, entries F01
and F02; F02 holds every number below with its source file.

## 1. Per-site summary

Results are space-heating only, over correctly divided homes only. Five cities use the 2009–2023
typical-year weather; Vienna uses its 2008 survey year.

| Site | Data sources and licence | What was assumed | Local folder | Speed folder |
|---|---|---|---|---|
| Montréal, Le Plateau (CA-MTL-PLATEAU) | Ville de Montréal building footprints and property roll, CC BY 4.0; Statistics Canada 2021 census tracts, Open Government Licence – Canada | Construction (corrected 2026-10-12 15:38, the page card was right): up to 2011 from the Canadian CSDDRD housing-stock survey (national values, no Québec-only split found); 2012 on from the Québec 2012 code (Partie 11, draft text); windows before 1984 assumed; g-value and thermal bridges from Swedish TABULA donors. Source: `implementation/PLAN_eu-new-city-CA-montreal-2026-10-08.md` T02 deviations 2–4. Age and floors almost all observed (98 %, 97 %); no age filled in | `openubem/outputs/eu_evidence/EU-11/CA-MTL-PLATEAU_win_2026-10-09/` | `/speed-scratch/o_iseri/fleets/EU22_CA-MTL-PLATEAU_win_2026-10-09/` |
| Yerevan, Nor Nork (AM-EVN-NORNORK) | OpenStreetMap, ODbL 1.0; Armstat housing tables 2020, **not an open licence** ("all rights reserved"; cite "Statistical Committee RA"), only counts transcribed | One construction period (1951–70) for every building; floors filled from neighbours for 216 of 551 (39 %); all flat counts from floor area; most construction values from donors | `openubem/outputs/eu_evidence/EU-11/AM-EVN-NORNORK_win_2026-10-09/` | `/speed-scratch/o_iseri/fleets/EU22_AM-EVN-NORNORK_win_2026-10-09/` |
| Cape Town, Woodstock (ZA-CPT-WOODSTOCK) | City of Cape Town building footprints (no named licence: non-commercial, no public release without the City's permission, credit "City of Cape Town"); OpenStreetMap, ODbL 1.0. Internal use for 6J only | Age from the City's heritage period labels, not observed; floors from LiDAR height ÷ 3 m; most construction values assumed except roof and brick wall | `openubem/outputs/eu_evidence/EU-11/ZA-CPT-WOODSTOCK_win_2026-10-09/` | `/speed-scratch/o_iseri/fleets/EU22_ZA-CPT-WOODSTOCK_win_2026-10-09/` |
| Helsinki, Kallio (FI-HEL-KALLIO) | City of Helsinki "Buildings in Helsinki", CC BY 4.0 | Age, floors and flat counts almost all observed (98–99 %); oldest-period values are the 1969 recommendation; Swedish donors for some values | `openubem/outputs/eu_evidence/EU-11/FI-HEL-KALLIO_win_2026-10-10/` | `/speed-scratch/o_iseri/fleets/EU22_FI-HEL-KALLIO_win_2026-10-10/` |
| Vienna, Rudolfsheim-Fünfhaus (AT-VIE-RUDOLFSHEIM) | Stadt Wien open data (five layers incl. Registerzählung 2023), CC BY 4.0, "Datenquelle: Stadt Wien – data.wien.gv.at"; ERA5 weather, CC BY | Age observed for only 24 of 536; the rest take their census district's main period; flat counts from floor area (no open register), except 11 single houses; TABULA Austria construction | `openubem/outputs/eu_evidence/EU-11/AT-VIE-RUDOLFSHEIM_win_2026-10-10/` | `/speed-scratch/o_iseri/fleets/EU22_AT-VIE-RUDOLFSHEIM_win_2026-10-10/` |
| Budapest, VII. district (HU-BUD-ERZSEBETVAROS) | OpenStreetMap, ODbL 1.0; KSH Census 2011, CC BY 4.0, "Source: KSH, Census 2011" | Age observed for 17 of 805; the rest take the district's census period (nearly all before 1946); floors filled from neighbours for 363 (45 %); all flat counts from floor area; TABULA Hungary construction | `openubem/outputs/eu_evidence/EU-11/HU-BUD-ERZSEBETVAROS_win_2026-10-10/` | `/speed-scratch/o_iseri/fleets/EU22_HU-BUD-ERZSEBETVAROS_win_2026-10-10/` |

Results, 3D results and 3D floor plans for all six: `docs/docs_ACTIVE/europeanLocations/results/`,
`outputs_3D/`, `plans3D/` (Cape Town's 3D pages stay local, never published).

## 2. Homes vs buildings

Yes: one row of the per-home csv is one building. `floor_area_m2` is the heated area of the whole
building, all floors together (the Budapest row of 2,761 m² is three floors of 920 m² with 42 flats).

Flats per building and per floor live in the floor-plan side-cars, one per building:
`<local folder>/layouts/<building_id>.json` (Budapest nests them as `layouts/way/…` and `layouts/relation/…`).

- `dwellings_total`: flats in the building; `units_per_floor`: flats on a full floor.
- `floors[i].dwelling_count`: flats on floor `i`; `floors[i].zones[j]`: one flat on that floor, with its
  outline corners in metres (`coords_m`, map system in `crs`) and its floor and ceiling heights.
- `dwelling_count_provenance`: whether the flat count was observed or filled from floor area.
- Flat floor areas are not stored as a number: compute each from its outline. Building heated area ÷
  `dwellings_total` gives the mean.
- One table per city also lists flats per building: `openubem/outputs/eu_evidence/EU-11/<SITE>_merged_<tag>/flat_counts_<date>.csv`.

## 3. Occupancy used in these runs

There are no people, lighting or equipment schedules in these models. Each flat has one internal heat
gain of 3 W/m², constant every hour of the year (one hourly file per flat, all 8,760 values equal to 3).
Heating keeps 20 °C at all hours; cooling is switched off. To use 6J's hourly profiles, replace the
per-flat files in `<local folder>/schedules/<building>/` (names ending `_gain.csv`, values in W/m²) and the
heating set-point.

## 4. Bologna 6J copy

Not made yet. Corrected 2026-10-12 15:38: the author's go was already given on 2026-10-08 (6J go message, item 3). We make
the copy once 4J reports its Bologna work done (earliest about 20 October) and send its path then.

## 5. Seoul files

We did not delete them. On checking today, four of the five are no longer on disk (the archived plan, the
raw weather folder, `kr_spec.json`, the benchmark file), and we have no record of who removed them. The
`kr` entry in the weather registry is still there. We leave it as is until the author says otherwise.
