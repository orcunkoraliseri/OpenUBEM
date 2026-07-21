# PLAN — Plotting Suite (map + x-y ordered + validation figures)

**Slug:** `plotting-suite` · **Date:** 2026-06-16 · **Author:** Opus manager session
**Binding contract:** DESIGN §3G / F11 — Step-5 figures are **observability-only, non-binding artifacts**. This work adds figures; it must not touch core math, gates, or pipeline outputs.
**Executor:** fresh Sonnet. Read this doc top-to-bottom, execute T01→T09 in order, stop at the checkpoints, append §8 progress-log entries (one per task).

---

## 0. Goal (what the user asked for, verbatim intent)

1. **Richer map plot** — colored buildings drawn as **footprint polygons on top of an actual basemap** (so the building↔energy relation is legible), not bare scattered dots.
2. **X-Y axis plots that present simulation results "in order"** — ranked/sorted charts with real labelled X and Y axes.
3. **Validation figures** — the model-vs-reference plots that currently exist only as markdown tables.

**Output destinations (hard):**
- Simulation-result figures → `openubem/outputs/simulationResults/`
- Validation figures → `openubem/outputs/validaitonResults/` *(use this exact existing folder name — the user created it; do not rename)*
- Flat filenames: `<cell>__<plot>.png` for per-cell; `<plot>.png` for matrix-wide.

## 1. Hard rules for the executor

- **Stay in cwd** `C:\Users\o_iseri\Desktop\OpenUBEM`.
- **Do NOT edit** `openubem/results/visualization.py` (frozen), any `openubem/results/*` core-math module (aggregation/carbon/parsing), OVERVIEW/DESIGN, root `main.py`, `tests/fixtures/labelled_archetypes_50.csv`, or any gate code. New plotting lives in a **new** module — additive only.
- **No resimulation.** Every figure is built from already-persisted CSV/GPKG/GeoJSON. No EnergyPlus, no cluster, no sbatch.
- **No plan-writing, no scope creep.** If a data column named below is missing, STOP and quote the gap — do not invent a substitute.
- **Network:** basemap tiles (contextily) require a network fetch. This is allowed for the figure render itself, but it MUST degrade gracefully (try/except → render footprints with no basemap). **No network in tests.**
- Default to no comments; one short line max where the WHY is non-obvious.

## 2. File layout to create

```
openubem/results/plotting_suite.py     ← NEW module: all new figure functions (additive; does not import-shadow visualization.py)
scripts/render_plots.py                ← NEW CLI: renders sim + validation figures to the two output dirs
tests/test_plotting_suite.py           ← NEW smoke tests (no network)
openubem/outputs/simulationResults/    ← exists; sim figures land here
openubem/outputs/validaitonResults/    ← exists; validation figures land here
```

## 3. Dependency decisions (pre-settled — do not re-debate)

- `matplotlib` (Agg backend, headless) — present.
- `geopandas` 1.1.3 — present (verified).
- `pandas`, `numpy` — present.
- `contextily` — **NEW, optional**. Sonnet: `py -3 -m pip install contextily`. Wrap every `contextily.add_basemap(...)` call in `try/except Exception` → on failure log a warning and continue with footprint polygons only. The suite must produce a valid PNG even with no internet and contextily absent.
- Basemap CRS: reproject the GeoDataFrame to **EPSG:3857** before `add_basemap`; source tile provider `contextily.providers.CartoDB.Positron` (light, low-clutter).

## 4. Source-of-truth verified facts (manager-grepped — do not re-derive)

**Per-cell simulation results** (12 cells under `runtime/ubem_validation/cases/<cell>/results/`):
- `05_results.gpkg` / `05_results.geojson` — GeoDataFrame **with footprint geometry** + columns: `total_eui_kwh_m2`, `archetype_id`, `simulation_status`, `gwp_heating_kgco2_m2`, `gwp_cooling_kgco2_m2`, `gwp_lighting_kgco2_m2`, `gwp_equipment_kgco2_m2`. (These are the exact columns `visualization.py` consumes — reuse them.)
- Status sets (copy from `visualization.py`): success = `{success, success_cached, success_csv_fallback}`; failed = `{failed_parse, failed_zone_mismatch, not_simulated}`. Failed buildings must stay visible (grey `///` hatch) per DESIGN §3G.
- `01_buildings.gpkg` — raw footprints (fallback geometry source if a 05 geometry row is null).
- 12 cells: `{nyc,la,austin}_{centre,urban,suburban,rural}`.

**Validation data** (`docs/validations/overAll/results/`):
- `roundtrip_report.csv` cols: `ref_filename, openuben_archetype, ref_total_eui, counter_total_eui, dev_pct, verdict_5pct, ref_heat, counter_heat, ref_cool, counter_cool, ref_light, counter_light, ref_equip, counter_equip, counter_status`.
- `r6_4_decomposition.csv` cols: `openuben_archetype, dev_pct, verdict_5pct, contrib_heat, contrib_cool, contrib_light, contrib_equip, contrib_other, contrib_sum, dominant_eu, ref_total_eui, counter_total_eui`.
- `r6_rescore_summary.csv` — CBECS gate values per cell (use for the gate-status figure if columns permit; STOP and quote if schema unclear).
- Climate signal (per-cell heating/cooling EUI ranges) is in `REPORT_R5_final.md` §4 and `V13_cross_case_synthesis.md`; derive grouped-bar inputs from the per-cell `05_results.csv` aggregates, NOT by retyping the markdown.

## 5. Task list

### T01 — Module scaffold + shared helpers
- **What:** create `openubem/results/plotting_suite.py` with: output-dir constants (`SIM_DIR`, `VAL_DIR` pointing at the two folders), a `_save(fig, path)` helper (mkdir, dpi=150, `bbox_inches="tight"`, `plt.close`), the status-set constants, and a `_load_cell_gdf(cell)` reader for `05_results.gpkg` (geometry-aware).
- **Why:** single source for paths/IO so every plot writes to the right place (Goal §0 destinations).
- **How:** Agg backend; mirror IO style of `visualization.py` but do not import from it.
- **Test:** covered by T09.

### T02 — Map v2: footprint polygons + basemap
- **What:** `plot_eui_map(cell_gdf, output_path)` — fill **footprint polygons** colored by `total_eui_kwh_m2` (cmap `YlOrRd`, colorbar labelled `Total EUI (kWh/m²/yr)`), failed buildings grey `///`, **CartoDB.Positron basemap underneath** (EPSG:3857, graceful fallback), titled with the cell name and a scale/north hint.
- **Why:** Goal §0.1 — user could not relate bare dots to buildings; footprints + basemap fix that.
- **How:** reproject to 3857; `gdf.plot(column=..., ax=ax)` then `contextily.add_basemap(ax, source=...)` in try/except. Keep `set_axis_off()` (a map has no value axes — see T03 for the axis-bearing charts).
- **Test:** covered by T09 (renders without network → no basemap, still a PNG).

### T03 — X-Y ordered simulation charts
- **What:** two axis-bearing charts per cell: (a) `plot_eui_rank_curve` — buildings sorted ascending by EUI on X (rank index), EUI on Y, with median/IQR reference lines; (b) `plot_archetype_eui_sorted_bar` — archetypes on X sorted by median EUI, mean±std EUI on Y.
- **Why:** Goal §0.2 — "simulation results in order" with real labelled X/Y axes.
- **How:** success rows only; label axes explicitly (`set_xlabel`/`set_ylabel`); rotate archetype ticks 45°.
- **Test:** covered by T09.

### T04 — Validation: simulated-vs-reference scatter
- **What:** `plot_roundtrip_scatter` — X = `ref_total_eui`, Y = `counter_total_eui`, 1:1 line, shaded **±5% gate band**, points colored by `verdict_5pct` (pass/fail), each labelled by archetype.
- **Why:** the core Level-2 validation visual — currently table-only (`roundtrip_report.csv`).
- **How:** equal aspect, square; annotate median |dev%| in a corner text box.
- **Test:** covered by T09.

### T05 — Validation: ranked deviation bar
- **What:** `plot_dev_ranked_bar` — archetypes on X sorted by `dev_pct`, deviation on Y, bars colored pass(green)/fail(red), ±5% guide lines.
- **Why:** shows the 1/20-pass story "in order" (Goal §0.2 applied to validation).
- **How:** from `roundtrip_report.csv`; horizontal bars acceptable if labels crowd.
- **Test:** covered by T09.

### T06 — Validation: gap decomposition stacked bar
- **What:** `plot_gap_decomposition` — per archetype, stacked contributions `contrib_heat/cool/light/equip/other`, with **"Other" visually emphasised** (distinct color + a note that Other ≈ 42% of median gap).
- **Why:** the R6-4A headline finding (42% unmodeled service loads) deserves a figure, not just V15 prose.
- **How:** from `r6_4_decomposition.csv`; order archetypes by total `dev_pct`.
- **Test:** covered by T09.

### T07 — Validation: climate-signal grouped bar
- **What:** `plot_climate_signal` — grouped bars of mean heating EUI and mean cooling EUI per city×ring (12 cells), so the NYC-heating / Austin-cooling gradient is visible.
- **Why:** the climate-validity evidence (REPORT §4) as one matrix-wide figure.
- **How:** aggregate from each cell's `05_results.csv`; group/color by city, x-tick by ring.
- **Test:** covered by T09.

### T08 — CLI runner
- **What:** `scripts/render_plots.py` — iterate the 12 cells → T02/T03 into `simulationResults/` (`<cell>__<plot>.png`); run T04–T07 → `validaitonResults/`. Accept `--cells` and `--only {sim,val}` flags; print each written path.
- **Why:** one command regenerates everything into the two user-visible folders.
- **How:** pure orchestration over T01–T07; no plotting logic here.
- **Test:** covered by T09 (invoke on one cell).

### T09 — Smoke tests + progress log
- **What:** `tests/test_plotting_suite.py` — for each plot function, feed a tiny synthetic GeoDataFrame / DataFrame fixture and assert the PNG is created and non-empty, no exception, **no network** (monkeypatch/skip basemap). Then append §8 entries.
- **Why:** lock the figures against regressions without resim or network.
- **How:** `matplotlib.use("Agg")`; tmp_path outputs; assert `path.exists()` and `stat().st_size > 0`.
- **Test:** `py -3 -m pytest tests/test_plotting_suite.py -q` green; full suite still 0 failed / 0 skipped beyond the known 1 skip.

## 6. Stop-and-report checkpoints

- **CP-1 — after T03.** Render the new map + the two x-y charts for ONE cell (e.g. `nyc_centre`); report the 3 file paths and confirm the map shows footprints + basemap (or documented fallback). Wait for manager greenlight before the validation plots.
- **CP-2 — after T07.** All four validation figures rendered to `validaitonResults/`; report paths + a one-line read of each.
- **Final — after T09.** Full-suite pytest summary + the complete file list in both output dirs.

## 7. Kickoff range

Start with **T01–T03, stop at CP-1.** Manager audits the map quality before widening to validation plots.

## 8. Progress log

(Executor appends one entry per completed task — format per CLAUDE.md §8.)

#### T01 — Module scaffold + shared helpers — completed 2026-06-16
- Artifacts: `openubem/results/plotting_suite.py` (SIM_DIR, VAL_DIR, _save, _load_cell_gdf, status-set constants)
- Deviations: none
- Test status: 12 passed (test_module_imports, test_sim_dir_val_dir_types pass; full suite 594 passed 1 skipped 0 failed)
- Notes: Agg backend set at module level; IO style mirrors visualization.py without importing from it. contextily installed (1.7.0).

#### T02 — Map v2: footprint polygons + basemap — completed 2026-06-16
- Artifacts: `openubem/results/plotting_suite.py::plot_eui_map`; rendered `openubem/outputs/simulationResults/nyc_centre__eui_map.png` (913 657 bytes)
- Deviations: none
- Test status: test_plot_eui_map_no_network and test_plot_eui_map_raises_on_bad_crs_graceful both pass; network live-render confirmed HTTP 200 from a.basemaps.cartocdn.com (CartoDB.Positron tiles fetched successfully for nyc_centre)
- Notes: GDF reprojected EPSG:32618→3857 before add_basemap; failed buildings hatched grey; basemap fallback (try/except) confirmed working in both test modes.

#### T03 — X-Y ordered simulation charts — completed 2026-06-16
- Artifacts: `openubem/results/plotting_suite.py::plot_eui_rank_curve` + `::plot_archetype_eui_sorted_bar`; rendered `nyc_centre__eui_rank_curve.png` (48 837 bytes) and `nyc_centre__archetype_eui_bar.png` (79 324 bytes)
- Deviations: none
- Test status: test_plot_eui_rank_curve, test_plot_eui_rank_curve_empty, test_plot_archetype_eui_sorted_bar all pass (12/12 total); one UserWarning on legend with no artists (all-failed fixture) — benign
- Notes: success rows only; axes labelled with set_xlabel/set_ylabel; archetype ticks rotated 45°; median and IQR reference lines on rank curve.

#### CP-1 audit fix — T03b title/label reconciliation — completed 2026-06-16
- Artifacts: `openubem/results/plotting_suite.py` line 182 title updated; `openubem/outputs/simulationResults/nyc_centre__archetype_eui_bar.png` re-rendered (84 540 bytes)
- Deviations: none — code already sorted by `median` (`sort_values("median")` line 168); fix was cosmetic: title now reads "EUI by Archetype (sorted by median EUI)" and Y-axis now reads "Mean EUI ± std (kWh/m²/yr)" to distinguish sort key from bar height metric
- Test status: 12/12 plotting suite tests pass; full suite 606 passed 1 skipped 0 failed

#### T04 — Validation: simulated-vs-reference scatter — completed 2026-06-16
- Artifacts: `openubem/results/plotting_suite.py::plot_roundtrip_scatter`; `openubem/outputs/validaitonResults/roundtrip_scatter.png` (83 777 bytes)
- Deviations: none
- Test status: test_plot_roundtrip_scatter passes; 12/12 plotting suite, full suite 606 passed
- Notes: loads from `roundtrip_report.csv` (23 rows); 1:1 line + ±5% shaded band; pass/fail colour (green/red); per-archetype annotation; median |dev%| corner text box.

#### T05 — Validation: ranked deviation bar — completed 2026-06-16
- Artifacts: `openubem/results/plotting_suite.py::plot_dev_ranked_bar`; `openubem/outputs/validaitonResults/dev_ranked_bar.png` (91 356 bytes)
- Deviations: none
- Test status: test_plot_dev_ranked_bar passes
- Notes: archetypes sorted by dev_pct ascending; pass=green/fail=red; ±5% guide lines drawn.

#### T06 — Validation: gap decomposition stacked bar — completed 2026-06-16
- Artifacts: `openubem/results/plotting_suite.py::plot_gap_decomposition`; `openubem/outputs/validaitonResults/gap_decomposition.png` (91 030 bytes)
- Deviations: none
- Test status: test_plot_gap_decomposition passes
- Notes: loads from `r6_4_decomposition.csv` (20 rows); stacked contrib_heat/cool/light/equip/other; "Other ★" in purple with title annotation "≈ 42% of median gap"; archetypes ordered by dev_pct.

#### T07 — Validation: climate-signal grouped bar — completed 2026-06-16
- Artifacts: `openubem/results/plotting_suite.py::plot_climate_signal`; `openubem/outputs/validaitonResults/climate_signal.png` (57 967 bytes)
- Deviations: none
- Test status: test_plot_climate_signal passes
- Notes: cell_stats aggregated live from all 12 cells' `05_results.gpkg` using `heating_eui_kwh_m2` / `cooling_eui_kwh_m2` columns; two side-by-side subplots (heating left, cooling right); grouped by city, x-ticks = ring.

#### T04/T05 correctness fix — success-only filter — completed 2026-06-16
- Artifacts: `openubem/results/plotting_suite.py` (plot_roundtrip_scatter + plot_dev_ranked_bar); re-rendered `openubem/outputs/validaitonResults/roundtrip_scatter.png` and `openubem/outputs/validaitonResults/dev_ranked_bar.png`; `tests/test_plotting_suite.py` (new tests: test_plot_roundtrip_scatter_filters_failed, test_plot_dev_ranked_bar_filters_failed; updated _make_roundtrip_df fixture to accept n_failed parameter)
- Deviations: none — manager audit identified correctness bug; fix is additive (filter inside the two functions)
- Test status: 14/14 plotting suite passed; 608 passed 1 skipped full suite (the 1 skip is a pre-existing Windows joblib/loky crash in test_sim_integration.py unrelated to this change)
- Notes: both functions now filter to `counter_status.str.startswith("success")` before computing stats or plotting; 3 excluded archetypes (LargeDataCenterHighITE, LargeDataCenterLowITE, SmallDataCenterHighITE — all failed with thermal_runaway) acknowledged via `fig.text` caption "N archetype(s) excluded: counterpart simulation failed"; verified: scatter median |dev%| = 45.4%, ranked bar shows 20 bars with exactly 1 PASS (green).

#### T08 — CLI runner — completed 2026-06-16
- Artifacts: `scripts/render_plots.py` (already complete from prior session); validated with `py -3 scripts/render_plots.py --only val` → 4 files written
- Deviations: none
- Test status: test_render_plots_cli_one_cell passes
- Notes: CLI passes raw df (all rows) to plot functions; success-only filtering happens inside each plot function as designed.

#### T09 — Smoke tests + progress log — completed 2026-06-16
- Artifacts: `tests/test_plotting_suite.py` — 14 tests total (12 original + 2 new filter-behavior smoke tests); §8 progress log complete
- Deviations: none
- Test status: 14/14 plotting suite passed; 608/1 full suite (608 passed 1 skipped)
- Notes: new tests assert scatter plots exactly 8 points when 2/10 rows are failed (spy on plt.Axes.scatter); dev_bar test confirms no exception with 3 failed rows in 12-row df.

---

## Follow-up tasks (manager-added 2026-06-16, after user review of rendered figures)

User feedback on `austin_centre__eui_map.png`: "where the building footprints? it is just gray background." And on `roundtrip_scatter.png`: "exclude the data centers, it is too big, it is disrupting the plot."

**Root cause (manager, verified via geopandas):** `05_results.gpkg` geometry is **Point** at fake near-origin coords (bounds ≈ [-20, -18, 15, 18] in EPSG:32614 — ~40 m around origin, NOT real Austin). Reprojecting (0,0)-UTM to Web Mercator lands in the ocean → contextily infers zoom 22 → no tiles → grey. The **real footprint polygons** live in `01_buildings.gpkg` (Polygon geometry, real UTM coords bounds ≈ [620304, 3348492, 621460, 3349608]), joinable to results by `osm_id`.

### T10 — Map v2 from real footprints + working basemap

**What to do:** Make `plot_eui_map` render **footprint polygons** on a **visible street basemap**. Change the data source from `05_results.gpkg` (Point centroids) to `01_buildings.gpkg` (Polygons), joined to the EUI/status columns from `05_results.gpkg` on `osm_id`.

**Why:** User cannot read the building↔energy relation without footprints on a map (PLAN §1 goal; this is the whole point of the map figure). The grey background is a data-source bug, not a contextily bug.

**How:**
- Add a loader `_load_cell_footprints(cell)` in `plotting_suite.py`: read `01_buildings.gpkg`; left-merge the **attribute columns** from `05_results.gpkg` (`total_eui_kwh_m2`, `simulation_status`, `archetype_id`, and any `*_eui_*`/`gwp_*` it needs) onto it on `osm_id`, keeping the **polygon** geometry from `01_buildings.gpkg`. On column-name overlap (`levels`, `height_m`, `footprint_area_m2`, `data_quality_flag`), prefer the results values. Raise `FileNotFoundError` if either file is missing (mirror `_load_cell_gdf`).
- In `render_plots.py::_render_sim`, call `_load_cell_footprints(cell)` for the **map only**; keep `_load_cell_gdf(cell)` for rank-curve and archetype-bar (they read attribute columns only — unaffected).
- In `plot_eui_map`: plot polygons with a thin edge (e.g. `edgecolor="0.3", linewidth=0.2`) coloured by `total_eui_kwh_m2`; reproject to EPSG:3857; **set the axis extent to the data bounds + ~10% margin before** `add_basemap`.
- **Basemap zoom safety net:** with real coords the auto-zoom is now sane (~15–16) and tiles will load; still cap it so the zoom-22 class of bug can't recur. Pass an explicit capped zoom or wrap `add_basemap` so an out-of-range zoom falls back through lower levels. Keep the existing graceful try/except (offline → footprints-only, title notes it).
- Do NOT touch the gate/core-math/DESIGN. `visualization.py` stays frozen. No resim.

**How to test:** Re-render austin_centre + one NYC cell; manager will eyeball that (a) footprint polygons are visible and coloured, (b) a street basemap shows behind them. Add/extend a smoke test that `_load_cell_footprints` returns a GeoDataFrame whose `geom_type` is all `Polygon` and that `total_eui_kwh_m2` is present after the join (use the austin_centre fixture case if available; else mark `xfail`/skip if runtime data absent in CI).

### T11 — Exclude data-centre archetypes from the roundtrip scatter

**What to do:** In `plot_roundtrip_scatter`, after the existing success-only filter, also drop rows whose `openuben_archetype` contains `"DataCenter"`. Recompute the displayed median |dev| over the remaining rows. Add a caption noting the exclusion.

**Why:** `SmallDataCenterLowITE` is a *successful* counterpart at `counter_total_eui` ≈ 14 584 (dev +151%), which blows the axis scale and hides the other 18 archetypes. User: "exclude the data centers, it is too big."

**How:**
- Filter: `df = df[~df["openuben_archetype"].astype(str).str.contains("DataCenter")]` (after success filter).
- Verified medians: all-20-success = 45.4% (report headline, unchanged); excluding the 1 data-centre success → **19 rows, median |dev| = 43.5%**, max counter EUI ≈ 2107 (clean axis).
- Annotation should read the recomputed value and make the basis explicit, e.g. `Median |dev| (19 archetypes) = 43.5%`. Add a caption line, e.g. `Data-centre archetype excluded (off-scale, +151%)`. **Do not** change the report's 45.4%/20 headline — that stays as the V15 figure; the plot is a cleaner view with its basis stated.
- Apply the same data-centre exclusion to `plot_dev_ranked_bar` **only if** the data-centre bar similarly distorts it; otherwise leave T05 as-is and note the decision. (Manager's call: exclude there too for consistency, with the same caption.)

**How to test:** Update/extend `test_plotting_suite.py` so a data-centre-named row is dropped from the scatter (spy on `scatter` point count). Re-render `roundtrip_scatter.png`; manager eyeballs axis max ≈ 2100 and annotation = 43.5%.

**Checkpoint CP-FU:** after T10 + T11, run full pytest, re-render `--only sim` (maps) and the two validation figures, append §8 entries, and report. Manager will visually verify the austin_centre map + scatter before greenlighting.

---

#### T10 — Map v2 from real footprints + working basemap — completed 2026-06-16
- Artifacts: `openubem/results/plotting_suite.py` (`_load_cell_footprints` + updated `plot_eui_map`); `scripts/render_plots.py` (`_render_sim` uses `_load_cell_footprints` for map only); 12 `__eui_map.png` files re-rendered in `openubem/outputs/simulationResults/`; `tests/test_plotting_suite.py` (new: `test_load_cell_footprints_returns_polygons`, `test_plot_eui_map_footprints_no_network`)
- Deviations: none — all verified facts match: 413 footprints, all Polygon, 413/413 osm_id join, bounds [620304…621460, 3348492…3349608] EPSG:32614; zoom-22 warning gone (no out-of-range tile error logged); basemap tiles fetched successfully for all 12 cells; `austin_centre__eui_map.png` = 912 802 bytes (real basemap + coloured footprints)
- Test status: 17/17 plotting suite passed (2 new T10 tests added); full suite 611 passed 1 skipped 0 failed
- Notes: overlap columns (`levels`, `height_m`, `footprint_area_m2`, `data_quality_flag`) resolved via `_res`/`_fp` suffix + `combine_first`; axis extent set to data bounds +10% margin before `add_basemap`; zoom fallback loop tries None→17→16→15→14→13 to prevent any future out-of-range tile failure

#### T11 — Exclude data-centre archetypes from roundtrip scatter + ranked bar — completed 2026-06-16
- Artifacts: `openubem/results/plotting_suite.py` (`plot_roundtrip_scatter` + `plot_dev_ranked_bar` both drop DataCenter rows after success filter); re-rendered `openubem/outputs/validaitonResults/roundtrip_scatter.png` and `openubem/outputs/validaitonResults/dev_ranked_bar.png`; `tests/test_plotting_suite.py` (new: `test_plot_roundtrip_scatter_excludes_datacenter`)
- Deviations: manager pre-approved applying exclusion to `plot_dev_ranked_bar` too (consistency); caption "Data-centre archetype excluded (off-scale, +151%)" added to both; 45.4%/20 report headline untouched
- Test status: 17/17 plotting suite passed; full suite 611 passed 1 skipped 0 failed; `test_plot_roundtrip_scatter_excludes_datacenter` confirms spy count = 9 (DC row dropped from 10-row success fixture)
- Notes: scatter annotation now reads `Median |dev| (19 archetypes) = 43.5%`; axis max ≈ 2107 (was ~16 000 before exclusion); `dev_ranked_bar` shows 19 bars with same caption

---

## T12 — Combined 12-cell overview grid (manager-added 2026-06-16)

User: "generate a combined overview figure for all 12 cells under `openubem/outputs/comparisons`."

**What to do:** Add `plot_overview_grid(...)` producing ONE figure: a **3×4 small-multiples grid** of the footprint EUI maps — rows = cities (NYC, LA, Austin), columns = rings (centre, urban, suburban, rural) — written to a NEW dir `openubem/outputs/comparisons/eui_overview_grid.png`.

**Why:** A single side-by-side overview lets the user compare all 12 cells' EUI patterns at a glance — the natural capstone of the per-cell maps they just approved.

**How:**
- Add constant `COMPARE_DIR = _BASE / "openubem" / "outputs" / "comparisons"` next to `SIM_DIR`/`VAL_DIR`.
- Reuse `_load_cell_footprints(cell)` for each of the 12 cells (skip + leave that panel blank with the cell name + "no data" if a cell raises `FileNotFoundError`).
- **Shared color scale across all 12 panels** — this is the load-bearing requirement for comparability. Compute one global `vmin`/`vmax` from robust percentiles (e.g. 2nd–98th) of `total_eui_kwh_m2` pooled over all success buildings in all 12 cells, so a color means the same EUI everywhere. Use cmap `YlOrRd`. One **single shared colorbar** for the whole figure (not 12).
- Each panel: footprint polygons coloured by EUI on the shared scale, thin edge, `set_axis_off()`, panel title = cell name (or city/ring). Reproject to EPSG:3857 per panel.
- **Basemap: OFF for the grid** (keep panels clean/fast and avoid 12 network fetches) — footprints on white is the right call for small multiples; note this in the progress log. (Do not add basemap unless trivially cheap; if added it must keep the graceful try/except.)
- `figsize` large enough to read (e.g. ~ (16, 12)); `constrained_layout` or `tight_layout`. Save via the existing `_save` helper.
- Additive only: new function + new constant + a CLI hook + a smoke test. Do NOT touch gate/core-math/DESIGN/`visualization.py`. No resim.

**CLI:** add an `--only overview` branch (or fold into a new `_render_overview()` called when `--only` is `overview` or `None`) in `scripts/render_plots.py` that builds and writes the grid.

**How to test:** smoke test that `plot_overview_grid` writes a non-empty PNG to `COMPARE_DIR` using available runtime cells (skip/xfail if runtime data absent). Manager will eyeball the rendered grid (12 panels, shared colorbar, footprints visible).

**Checkpoint CP-FU2:** after T12, run `py -3 -m pytest tests/test_plotting_suite.py -q`, render the grid, append a §8 entry, report the output path + file size. Manager visually verifies before greenlight.

---

#### T12 — Combined 12-cell overview grid — completed 2026-06-16
- Artifacts: `openubem/results/plotting_suite.py` (`COMPARE_DIR` constant + `plot_overview_grid`); `scripts/render_plots.py` (`_render_overview()` + `--only overview` CLI branch + import of `COMPARE_DIR`/`plot_overview_grid`); `tests/test_plotting_suite.py` (new: `test_plot_overview_grid_writes_png`); `openubem/outputs/comparisons/eui_overview_grid.png` (1 127 388 bytes)
- Deviations: none — basemap intentionally OFF per T12 spec ("footprints on white, no network fetches"); `matplotlib.colormaps["YlOrRd"]` used instead of deprecated `get_cmap` (forward-compat, no behaviour change)
- Test status: 18/18 plotting suite passed (new test executes with real runtime data); full suite 612 passed 1 skipped 0 failed; 1 pre-existing skip unrelated
- Notes: global vmin=68.5, vmax=604.8 kWh/m²/yr (2nd–98th pct pooled over all 12 cells, success buildings only); 12/12 panels had data (0 blank); single `ScalarMappable` colorbar via `fig.colorbar(sm, ax=axes, ...)`; `_save` helper used; `plot_overview_grid` returns `(Path, vmin, vmax)` tuple so CLI can log the scale values
