# MEASUREMENT — OPEN-17 T08: does a source even exist for the six unwired targets? (2026-08-21 night)

> Executes T08 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-live-items-2026-08-21-night.md`.
> Measurement only. No imputer wired, no config touched.
> Script: `scripts/analysis/open17_t08_source_inventory_2026-08-21b.py`
> CSV: `openubem/outputs/comparisons/open17_t08_source_inventory_2026-08-21b.csv`

## Population and columns

All twelve `evidence/open48_refleet4/<cell>/01_buildings.gpkg`, **8,160 buildings**. Each gpkg has
**24 columns** (23 non-geometry + `geometry`), identical across all 12 cells (verified by direct
comparison, not assumed):

`osm_id, crs_utm, building_tag, function_tag, levels, height_m, year_built, postcode, underground,
roof_shape, roof_height_m, footprint_area_m2, perimeter_m, surplus_tags, provenance_levels,
provenance_height_m, provenance_year_built, provenance_building_tag, provenance_function_tag,
provenance_postcode, provenance_geometry, data_quality_flag, geometry`.

`surplus_tags` is a per-row JSON string of leftover raw OSM tags not mapped to a named column
(e.g. `addr:postcode`, `building:levels`, `amenity`, `height`) — it is the only place a source for
the six targets could hide outside the named columns.

## C16 — reproduction of F11 before doing anything else

| target | n_null (raw) | n_needs_value (provenance ≠ `OSM_OBSERVED`) | placeholder token(s) found |
|---|---:|---:|---|
| levels | 7,719 | 7,719 | `OSM_MISSING` |
| function_tag | 0 | 7,741 | `OSM_MISSING` |
| postcode | 4,183 | 4,183 | `OSM_MISSING` |
| building_tag | 0 | 4,105 | `OSM_GENERIC` |
| height_m | 2,806 | 2,806 | `OSM_MISSING` |
| geometry | 0 | 0 | — |

Exact match to F11 on all seven counts (year_built included for the check, not itself in scope
here). **Pass.**

## Method

For each of the six targets, checked two kinds of alternate source: (a) other named gpkg columns
whose content plausibly duplicates the target (`roof_height_m` for `height_m`; no plausible named
column exists for the other five — `roof_shape` was considered for `building_tag` and rejected, it
describes roof geometry, not building use, and would have been an invented association, not a
source), and (b) specific OSM tag keys inside `surplus_tags` that map onto the target semantically:

| target | candidate `surplus_tags` keys checked |
|---|---|
| levels | `building:levels`, `levels`, `building:min_level` |
| height_m | `height`, `building:height`, `height_raw`, `ele` |
| postcode | `addr:postcode`, `postal_code` |
| function_tag | `amenity`, `shop`, `tourism`, `office`, `leisure`, `craft`, `healthcare`, `landuse` |
| building_tag | `building`, `building:use` |

A row counts as having a usable source if any checked key/column is present and non-empty, **among
rows that need a value** (provenance ≠ `OSM_OBSERVED` / `OSM_GENERIC` as applicable).

## C17 — result, one line per target

| target | n_needs_value | n_with_plausible_source | pct of n_needs_value | source exists? |
|---|---:|---:|---:|---|
| levels | 7,719 | 0 | 0.00 % | **no** |
| function_tag | 7,741 | 139 | 1.80 % | yes (thin) |
| postcode | 4,183 | 1 | 0.02 % | yes (negligible) |
| building_tag | 4,105 | 1 | 0.02 % | yes (negligible) |
| height_m | 2,806 | 25 | 0.89 % | yes (thin) |
| geometry | 0 | 0 | n/a | n/a — nothing needed |

**`levels` has no source anywhere in the corpus.** Zero of 7,719 needs-a-value rows carry any of
`building:levels`, `levels`, or `building:min_level` in `surplus_tags`, and there is no other named
column that could feed it. This is the largest hole on OPEN-17's list (94.6 % of the fleet) and it
is **not fillable from anything on disk** — closing it requires a new acquisition source, not a
router change.

The other four fillable-in-principle targets (`function_tag`, `postcode`, `building_tag`,
`height_m`) each have a real but thin trickle of alternate-source rows in `surplus_tags` (0.02–1.80 %
of their respective needs-value populations) — present, not absent, but too small to move any of
F11's headline percentages materially even if fully wired. `roof_height_m`, the one plausible named
alternate column for `height_m`, is **non-null for 0 of the 2,806 needs-value rows** — it exists as a
column but carries no data at fleet scale in this corpus.

`geometry` needs nothing (0 of 8,160) — the source-existence question does not apply.

## Test status

- **C16 — pass.** All seven F11 counts reproduce exactly.
- **C17 — reported above, one line per target.**

## Remedy shape (NOT applied)

None proposed. The finding that `levels` has zero source anywhere in this corpus, and that the other
four have only a thin trickle, is offered as input to the user's decision on whether router-wiring
work for OPEN-17 is worth doing versus a new acquisition source — not a recommendation.
