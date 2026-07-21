# TASK — Phase-E Overview-Grid Footprint Map

- **Date:** 2026-06-28
- **Author:** Manager (Opus session)
- **Executor:** Sonnet
- **Binding context:** `REPORT_phaseE_final.md` (the figure this feeds). This is a reporting-layer task: **no simulation, no OSM re-fetch, no IDF generation.**

## Objective

The Phase-E results tree stores only **centroids in a per-building local frame** (`05_results.gpkg` = `Point`, bounds ~80×150 m near origin) — unusable for a geographic map. The real building **footprints survive on disk** in the volatile runtime temp dir for all 12 cells, in true UTM coordinates, and join to the results **100% by `osm_id`**. This task (1) persists those footprints into the durable results tree, then (2) renders a true Phase-E overview-grid map of building total-EUI.

## Hard rules for the executor

- Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`. Do not run any EnergyPlus / simulation / OSM fetch.
- Do not edit OVERVIEW/DESIGN docs. No `.py` under `docs/`.
- Default to no code comments (one line max where the WHY is non-obvious).
- **Load-bearing gotcha:** the geometry inside `05_results.gpkg` is a local-frame point and is GARBAGE for mapping. You MUST take polygon geometry from `01_buildings.gpkg` and attach the EUI columns from `05_results` by an `osm_id` merge. Never plot the results-file geometry.
- Stop and ask if any cell's `osm_id` join is < 100% (it was verified at 100% — a miss means something changed).

## Source-of-truth verified facts (already checked by manager)

- 12 cells = {`nyc`,`la`,`austin`} × {`centre`,`urban`,`suburban`,`rural`}.
- **Footprint source (per cell):** `%LOCALAPPDATA%\Temp\ubem_validation\phaseE\<cell>\01_buildings.gpkg` — `Polygon`, real UTM CRS (Austin 32614, LA 32611, NYC 32618). Row counts match results exactly. **This temp dir is volatile — persist before relying on it (T01 first).**
- **Results source (per cell):** `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/05_results.gpkg`. Relevant columns: `osm_id`, `total_eui_kwh_m2`, `simulation_status` (`success` vs other).
- `osm_id` join footprint↔results = **100% in every cell** (verified).
- Project convention: **all figures go to `openubem/outputs/` (flat).**

## File layout to create

```
docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg   ← persisted copy (12 files)
openubem/outputs/phaseE_overview_grid.png                                          ← the figure
scripts/validation/phaseE_overview_grid.py                                         ← the driver (glue script, ok under scripts/)
```

## Task list

### T01 — Persist the 12 footprint files (do this FIRST)
- **What:** Copy `%LOCALAPPDATA%\Temp\ubem_validation\phaseE\<cell>\01_buildings.gpkg` → `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg` for all 12 cells.
- **Why:** Temp is volatile; if it clears, the footprints are gone and the only fallback is a step-1 re-fetch. Persisting first makes the rest reproducible.
- **How:** Plain file copy. Do not modify/re-project the gpkg on copy — keep it byte-identical.
- **Test:** Assert 12 destination files exist and each opens as a non-empty `Polygon` GeoDataFrame with an `osm_id` column.

### T02 — Build the per-cell map GeoDataFrames
- **What:** For each cell, read the persisted `01_buildings.gpkg`, merge `total_eui_kwh_m2` + `simulation_status` from `05_results.gpkg` on `osm_id` (left join on footprints).
- **Why:** Footprint geometry + results attributes = mappable Phase-E layer.
- **How:** `gdf = footprints.merge(results[['osm_id','total_eui_kwh_m2','simulation_status']], on='osm_id', how='left')`. Drop the results geometry before merge to avoid a geometry-column clash. Keep each cell in its native UTM (panels are independent; no common CRS needed).
- **Test:** For each cell assert `footprint_count == results_row_count` and the merged `osm_id` match rate == 100%. Print per-cell median `total_eui_kwh_m2` as a sanity check.

### T03 — Render the overview grid
- **What:** One figure, **3 rows (city: NYC / LA / Austin) × 4 cols (density ring: centre / urban / suburban / rural)**, each panel = building footprints colored by `total_eui_kwh_m2`.
- **Why:** The Phase-E "overview grid" deliverable for the report.
- **How:**
  - Colormap `YlOrRd` to match the existing per-cell `eui_choropleth.png`.
  - **Shared color scale** across all 12 panels (single shared colorbar). Use a robust range to stop the NYC supertall (~765 kWh/m²) washing everything out: `vmin = 0`, `vmax = 95th percentile of pooled total_eui across all 12 cells` (print the chosen vmax). Buildings above vmax clip to the top color.
  - Buildings with `simulation_status != 'success'` (or null EUI): render grey with a hatch, and add a single "Failed/not simulated" legend entry (match the per-cell choropleth style).
  - Each panel: title = cell name, equal aspect, axes off. Row/column labels for city and density ring. Figure suptitle: "Phase-E — Building Total EUI (kWh/m²/yr)".
  - Save `openubem/outputs/phaseE_overview_grid.png` at ~150–200 dpi, `bbox_inches='tight'`.
- **Test:** Assert the PNG exists and is > 100 KB. Eyeball: 12 populated panels, shared colorbar, denser cells visibly busier.

## Stop-and-report

Single checkpoint at end of T03. Append a progress-log entry below (one per task), report: 12 files persisted (paths), the chosen vmax, per-cell median EUI table, and the figure path. Do not edit `REPORT_phaseE_final.md` — the manager wires the figure into the report after audit.

## Progress log

#### T01 — Persist 12 footprint files — completed 2026-06-28

- **Artifacts:** `docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg` (12 files, all Polygon / UTM, all > 0 rows, all with `osm_id` column)
- **Deviations:** Temp dir `%LOCALAPPDATA%\Temp\ubem_validation\phaseE\` was already cleared (volatile, as warned). Primary copy-source gone. User explicitly approved Option 2: re-fetch from OSM using `ingest_buildings(location=(lat,lon), radius_m=radius_m)` with identical CELL_CONFIGS params. This restored 100% accuracy for austin_urban (425/425, confirmed by live re-fetch vs 417/425 from stale cases centroids).
- **Test status:** All 12 assertions pass — file exists, non-empty, osm_id column present, geometry in {Polygon, MultiPolygon}.
- **Notes:** austin_urban went from 417 (stale cases) → 425 (re-fetch) = exact match to phaseE results. Fetch triggered no rate-limit warnings.

#### T02 — Build per-cell map GeoDataFrames — completed 2026-06-28

- **Artifacts:** 12 in-memory GeoDataFrames (footprint Polygon + EUI attributes, native UTM per city). Medians logged below.
- **Deviations:** None.
- **Test status:** All 12 cells: `fp_count == res_count` and `osm_id` match == 100%.
- **Notes:**

| Cell | fp | res | match | median EUI (kWh/m²/yr) |
|---|---|---|---|---|
| nyc_centre | 738 | 738 | 738 (100%) | 180.1 |
| nyc_urban | 1779 | 1779 | 1779 (100%) | 144.7 |
| nyc_suburban | 1589 | 1589 | 1589 (100%) | 205.5 |
| nyc_rural | 198 | 198 | 198 (100%) | 159.6 |
| la_centre | 226 | 226 | 226 (100%) | 143.1 |
| la_urban | 618 | 618 | 618 (100%) | 103.9 |
| la_suburban | 1343 | 1343 | 1343 (100%) | 106.6 |
| la_rural | 149 | 149 | 149 (100%) | 130.0 |
| austin_centre | 413 | 413 | 413 (100%) | 135.6 |
| austin_urban | 425 | 425 | 425 (100%) | 121.0 |
| austin_suburban | 437 | 437 | 437 (100%) | 119.9 |
| austin_rural | 245 | 245 | 245 (100%) | 117.8 |

#### T03 — Render overview grid — completed 2026-06-28

- **Artifacts:** `openubem/outputs/phaseE_overview_grid.png` (1486 KB, 150 dpi, 3 rows × 4 cols)
- **Deviations:** None.
- **Test status:** File exists, size = 1486 KB > 100 KB threshold. Chosen shared vmax = **414.6 kWh/m²/yr** (p95 of pooled EUI across all 12 cells). Colormap YlOrRd, single shared colorbar, hatch for failed/not-simulated buildings.
- **Notes:** No failed buildings detected in any cell (all 8,160 simulated, `simulation_status == 'success'`). Hatch legend present but unused in this run.

**TASK COMPLETE — moved to debugs/ 2026-06-28**
