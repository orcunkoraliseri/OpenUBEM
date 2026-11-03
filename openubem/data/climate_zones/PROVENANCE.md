# PROVENANCE — ashrae_climate_zones.gpkg

## Sources

| Artifact | URL | Retrieved | SHA-256 |
|---|---|---|---|
| Census cb_2023_us_county_500k | https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_county_500k.zip | 2026-06-10 | 99d6597b1fc7767deef62e01d28d8b5dcbd578e151855f7dc0d173cbf5bf0868 |
| ResStock County and PUMA TSV | https://raw.githubusercontent.com/NREL/resstock/main/project_national/housing_characteristics/County%20and%20PUMA.tsv | 2026-06-10 | 012b867ac314f7b61a4fad3f62acadb9f53d25abf4f4797ee7a53ee1ebde6cc1 |
| ashrae_climate_zones.gpkg (emitted) | (local) | 2026-06-10 | 74a84a58354fbdf5591a539349a08c138640c053b5502515def3c4ac95192734 |

## Edition

ASHRAE 169-2013-consistent county→zone assignments sourced from the NREL ResStock
housing-characteristics matrix (Dependency=ASHRAE IECC Climate Zone 2004).  Each county
is assigned the zone with the highest probability mass in that matrix (deterministic:
all probabilities in the ResStock data are 0 or 1 for IECC climate zones).

OQ-1 resolution (PLAN §4 F16): pinned to ASHRAE 169-2013-consistent edition to match
the bundled 90.1-2019 construction tables.  IECC-2021 re-assignments not applied.

ResStock zone tokens 7A, 7AK, 7B → F3 vocab token `7`; 8AK → `8`.

## License

US Census Bureau cartographic boundary files: public domain (US government work).
NREL ResStock housing characteristics: Creative Commons Attribution 4.0 International
(https://github.com/NREL/resstock/blob/main/LICENSE.md).

## Layer spec

- Layer name: `counties`
- CRS: EPSG:4326
- Columns: `county_geoid` (5-digit FIPS, str), `state_abbrev` (2-letter USPS, str),
  `climate_zone` (16-token closed vocab per DESIGN line 64), `geometry`
- Row count: 3133 (territories with no zone assignment dropped: 102)
- `county_geoid` is unique

## Fixture-city validation (all passed)

| City | county_geoid | Expected zone | Got |
|---|---|---|---|
| Miami-Dade FL | 12086 | 1A | 1A |
| Maricopa AZ | 04013 | 2B | 2B |
| San Francisco CA | 06075 | 3C | 3C |
| Suffolk MA | 25025 | 5A | 5A |
| Cook IL | 17031 | 5A | 5A |
| Denver CO | 08031 | 5B | 5B |
| St. Louis MN | 27137 | 7 | 7 |
| Fairbanks NS AK | 02090 | 8 | 8 |

## Refresh

Re-run `scripts/build_climate_zones_gpkg.py` from the project root with network access.


## epw_stations.csv

| Artifact | URL | Retrieved | SHA-256 |
|---|---|---|---|
| Region4_USA_TMYx KML | https://climate.onebuilding.org/sources/Region4_USA_TMYx_EPW_Processing_locations.kml | 2026-06-10 | 23bff4bc13542efaa8ee33e9d983e94417ef22b981f18d8087200730440d20ae |
| epw_stations.csv (emitted) | (local) | 2026-06-10 | 4005ab18c5731f8a73a7a3c9f993a8f88ccc132d96a9e0d7d26939f48bbcc3a6 |

- Rows: 2919 unique US weather stations (TMYx editions)
- Columns: station_id (WMO 6-digit str), name, state, lat, lon, url, tmy_edition
- TMYx edition policy: newest edition kept where multiple exist (OQ-3, PLAN §5 P2)
- License: data from climate.onebuilding.org — free for non-commercial use; see
  https://climate.onebuilding.org/

## Refresh

Re-run `scripts/build_epw_stations_csv.py` from the project root with network access.


## epw_stations.csv

| Artifact | URL | Retrieved | SHA-256 |
|---|---|---|---|
| Region4_USA_TMYx KML | https://climate.onebuilding.org/sources/Region4_USA_TMYx_EPW_Processing_locations.kml | 2026-06-10 | 23bff4bc13542efaa8ee33e9d983e94417ef22b981f18d8087200730440d20ae |
| epw_stations.csv (emitted) | (local) | 2026-06-10 | e5bb0c1a786fb96d5c317792db555f1ab5a5519ee2729317c2aaea381c243deb |

- Rows: 2919 unique US weather stations (TMYx editions)
- Columns: station_id (WMO 6-digit str), name, state, lat, lon, url, tmy_edition
- TMYx edition policy: newest edition kept where multiple exist (OQ-3, PLAN §5 P2)
- License: data from climate.onebuilding.org — free for non-commercial use; see
  https://climate.onebuilding.org/

## Refresh

Re-run `scripts/build_epw_stations_csv.py` from the project root with network access.
