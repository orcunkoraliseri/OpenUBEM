# I01 — Full 12-cell characterization

Source: independent `geopandas.read_file` of each cell's
`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg` (read-only).
Script: `scratchpad/e-utci-09-investigation/i01_characterize_12cells.py`. CSV twin:
`openubem/outputs/comparisons/i01_e_utci_09_12cell_characterization.csv`.

Rows below are sorted by `height_m` NaN% ascending to expose the cluster structure.

## Core table

| cell | rows | native CRS (metric, used as-is) | `height_m` NaN n (%) | `levels` NaN n (%) | footprint area m² min/mean/max | geometry: null/empty/invalid/non-poly | `building_tag`: n_distinct / empty / top5 |
|---|---|---|---|---|---|---|---|
| la_rural | 149 | EPSG:32611 | 1 (0.671%) | 146 (97.987%) | 28.31 / 509.08 / 22443.66 | 0/0/0/0 | 6 / 0 / yes:113; industrial:14; warehouse:11; house:8; residential:2 |
| la_suburban | 1343 | EPSG:32611 | 15 (1.117%) | 1337 (99.553%) | 20.08 / 194.98 / 6869.20 | 0/0/0/0 | 12 / 0 / house:1261; yes:40; residential:12; apartments:10; civic:6 |
| nyc_urban | 1779 | EPSG:32618 | 40 (2.248%) | 1762 (99.044%) | 20.39 / 176.77 / 11077.47 | 0/0/0/0 | 10 / 0 / yes:1512; garage:220; apartments:29; construction:8; school:3 |
| la_urban | 618 | EPSG:32611 | 42 (6.796%) | 587 (94.984%) | 23.37 / 773.03 / 10330.11 | 0/0/0/0 | 13 / 0 / apartments:299; house:93; commercial:63; residential:63; yes:52 |
| austin_urban | 425 | EPSG:32614 | 47 (11.059%) | 421 (99.059%) | 20.87 / 572.04 / 22109.98 | 0/0/0/0 | 7 / 0 / yes:399; apartments:11; retail:4; parking:4; hospital:3 |
| nyc_centre | 738 | EPSG:32618 | 121 (16.396%) | 602 (81.572%) | 21.28 / 1143.41 / 155536.02 | 0/0/0/0 | 19 / 0 / yes:581; commercial:54; hotel:33; theatre:20; office:14 |
| la_centre | 226 | EPSG:32611 | 45 (19.912%) | 147 (65.044%) | 20.05 / 1833.95 / 17661.13 | 0/0/0/0 | 19 / 0 / yes:76; retail:52; commercial:37; apartments:21; roof:10 |
| austin_suburban | 437 | EPSG:32614 | 114 (26.087%) | 391 (89.474%) | 20.07 / 273.84 / 6972.27 | 0/0/0/0 | 14 / 0 / yes:365; retail:20; commercial:16; roof:11; demountable:8 |
| **— gap: no cell between 26.09% and 84.50% —** | | | | | | | |
| austin_centre | 413 | EPSG:32614 | 349 (84.504%) | 295 (71.429%) | 24.28 / 1013.05 / 8225.32 | 0/0/0/0 | 19 / 0 / yes:305; roof:29; office:18; retail:18; commercial:10 |
| nyc_suburban | 1589 | EPSG:32618 | 1589 (100.000%) | 1589 (100.000%) | 20.52 / 114.64 / 5132.61 | 0/0/0/0 | 3 / 0 / house:979; yes:320; garage:290 |
| nyc_rural | 198 | EPSG:32618 | 198 (100.000%) | 198 (100.000%) | 21.87 / 243.86 / 3884.80 | 0/0/0/0 | 12 / 0 / yes:157; residential:13; house:9; commercial:4; hotel:4 |
| austin_rural | 245 | EPSG:32614 | 245 (100.000%) | 244 (99.592%) | 34.89 / 631.49 / 10992.63 | 0/0/0/0 | 9 / 0 / yes:185; retail:21; commercial:11; semidetached_house:9; roof:7 |

All 12 gpkg layers arrive already in a projected, metric per-city UTM CRS (`EPSG:32618` NYC,
`EPSG:32611` LA, `EPSG:32614` Austin) — no reprojection was needed or performed; areas above are
computed directly in that native CRS.

Geometry validity: **0 invalid, 0 non-Polygon, 0 empty, 0 null geometries across all 12 cells,
12,809 total rows.** Row counts and footprint-area ranges are plausible city-fabric numbers in
every cell, including the 4 height-affected ones.

## `data_quality_flag` distribution (top values per cell)

| cell | top `data_quality_flag` values (value:count) |
|---|---|
| nyc_centre | generic_tag,no_floors,no_function,no_year:391; generic_tag,no_function,no_year:75; generic_tag,no_floors,no_function,no_height:38; no_floors:36; no_floors,no_year:34 |
| nyc_urban | generic_tag,no_floors,no_function,no_year:1468; no_floors,no_year:250; generic_tag,no_floors,no_function,no_height,no_year:21; no_floors,no_height,no_year:12; generic_tag,no_floors,no_year:10 |
| nyc_suburban | no_floors,no_height,no_year:1269; generic_tag,no_floors,no_function,no_height,no_year:310; generic_tag,no_floors,no_height,no_year:10 |
| nyc_rural | generic_tag,no_floors,no_function,no_height,no_year:113; generic_tag,no_floors,no_height,no_year:43; no_floors,no_height,no_year:41; generic_tag,no_floors,no_height:1 |
| la_centre | no_floors:68; (empty flag):37; generic_tag,no_floors,no_function,no_year:18; generic_tag,no_floors,no_function,no_height,no_year:17; no_floors,no_year:16 |
| la_urban | no_floors:510; no_floors,no_year:20; generic_tag,no_floors,no_function,no_height,no_year:18; generic_tag,no_floors,no_function,no_year:16; (empty flag):16 |
| la_suburban | no_floors:1288; generic_tag,no_floors,no_function,no_year:27; generic_tag,no_floors,no_function,no_height,no_year:10; (empty flag):6; no_floors,no_year:6 |
| la_rural | generic_tag,no_floors,no_function:91; no_floors:31; generic_tag,no_floors,no_function,no_year:14; no_floors,no_year:5; generic_tag,no_floors,no_year:4 |
| austin_centre | generic_tag,no_floors,no_function,no_height,no_year:142; no_floors,no_height,no_year:53; generic_tag,no_floors,no_height,no_year:49; generic_tag,no_function,no_height,no_year:45; generic_tag,no_floors,no_function,no_year:42 |
| austin_urban | generic_tag,no_floors,no_function,no_year:351; generic_tag,no_floors,no_function,no_height,no_year:34; no_floors,no_year:17; generic_tag,no_floors,no_year:10; no_floors,no_height,no_year:8 |
| austin_suburban | generic_tag,no_floors,no_function,no_year:301; generic_tag,no_floors,no_function,no_height,no_year:57; no_height,no_year:39; no_floors,no_year:16; no_floors,no_height,no_year:12 |
| austin_rural | generic_tag,no_floors,no_function,no_height,no_year:131; no_floors,no_height,no_year:60; generic_tag,no_floors,no_height,no_year:53; generic_tag,no_function,no_height,no_year:1 |

Every `no_height` flag row lines up with a `height_m` NaN row (F-02 confirmed at fleet scale). The
flag composition also confirms `year_built` and `no_floors`/`levels` are broadly sparse in **every**
cell regardless of the height cluster — see the "other columns" table below.

## `building_tag` / tag sanity

All 12 cells: `building_tag` is **never empty/absent** (0 empty rows in every cell) and has a
plausible, city-appropriate distribution (`house`/`apartments`/`residential` dominate suburban/rural
cells; `yes`/`commercial`/`office`/`retail`/`hotel` dominate centre/urban cells). `n_distinct` ranges
3 (nyc_suburban) to 19 (nyc_centre, la_centre, austin_centre). No sign of a broken/degenerate tag
fetch in either cluster.

## NaN% for every other column (fleet-wide observations)

Columns **0% NaN in all 12 cells** (fully populated, both clusters): `osm_id`, `crs_utm`,
`building_tag`, `footprint_area_m2`, `perimeter_m`, `surplus_tags`, all six `provenance_*` columns,
`data_quality_flag`, `underground`.

Columns that are **broadly sparse in every cell, uncorrelated with the height/levels cluster**
(caveat: `function_tag` and `roof_shape` are `str` columns using an **empty-string sentinel**, not
`NaN` — `.isna()` reports 0% for them; the real "unset" rate is reported here via empty-string count
instead):

| column | sentinel type | range across all 12 cells | notes |
|---|---|---|---|
| `year_built` | NaN | 3.6% (la_suburban) – 100.0% (nyc_urban, austin_urban, austin_rural) | high and variable in **both** good- and bad-height clusters (e.g. nyc_urban: height 2.2% NaN but year_built 100% NaN) — independent of the height gap |
| `postcode` | NaN | 28.0% (nyc_centre) – 100.0% (la_rural) | same pattern, independent of the height gap |
| `roof_height_m` | NaN | 99.86% (nyc_centre) – 100.0% (10 of 12 cells) | essentially always missing everywhere, both clusters |
| `function_tag` | empty string | 74.7% (nyc_rural) – 99.6% (la_suburban) empty | secondary/optional OSM sub-tag, sparse everywhere, uncorrelated with height cluster |
| `roof_shape` | empty string | 83.1% (nyc_centre) – 100.0% (7 of 12 cells) | same pattern |

**None of these other-column gaps track the good/bad `height_m` cluster split** — e.g. la_urban
(good cluster, 6.8% height NaN) has 95.8% `postcode` NaN, while austin_centre (bad cluster, 84.5%
height NaN) has only 46.2% `postcode` NaN. This is normal per-field OSM tagging-density variance,
not a differential defect riding alongside the height/levels gap.

## Cross-check vs T26 harvest CSV

Independently-derived `height_m` NaN counts match `t26_utci_cluster_cell_summary.csv`'s
`n_excluded_no_height` / `pct_excluded_no_height` **exactly** on row counts for all 12 cells; percent
figures agree to within ≤0.0005 percentage points (floating-point display rounding only, e.g.
nyc_centre 16.3960% here vs 16.3957% in the CSV). No discrepancy.

## F-08 5-cell spot-check reproduction

All 5 F-08 rows (nyc_suburban, nyc_rural, austin_rural, austin_centre, nyc_centre) reproduce
**exactly** — row counts, `height_m`/`levels` NaN%, footprint area min/mean/max, and 0 invalid
geometries all match F-08 to the stated precision.

## Load-bearing answer

**The gap is cleanly scoped to the `height_m`/`levels` fields — not a broader footprint/inventory
problem.** Row counts, geometry validity (0 invalid/non-Polygon/empty/null in all 12,809 rows across
12 cells), footprint-area ranges, and `building_tag` presence/distribution are all healthy in every
cell, including the 4 height-affected ones. Other broadly-sparse columns (`year_built`, `postcode`,
`roof_height_m`, and the empty-string-sentinel `function_tag`/`roof_shape`) are sparse **uniformly
across both clusters** and do not track the height/levels split — normal OSM per-field tagging
density, not a wider fetch failure.

**The distribution is cleanly bimodal, no borderline cell.** Sorted `height_m` NaN%: 0.67%, 1.12%,
2.25%, 6.80%, 11.06%, 16.40%, 19.91%, 26.09% (8 "good" cells) — then a **58-percentage-point gap** —
84.50%, 100.00%, 100.00%, 100.00% (4 "bad" cells: `austin_centre`, `nyc_suburban`, `nyc_rural`,
`austin_rural`). No cell falls in the 26–84% range. `austin_centre` (84.50%) is the closest to a
"borderline" case but sits far closer to the bad cluster than to the good one.
