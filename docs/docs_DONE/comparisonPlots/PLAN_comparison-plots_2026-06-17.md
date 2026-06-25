# PLAN — Comparison Plots + Overview-Grid Basemap

**Slug:** comparison-plots
**Date:** 2026-06-17
**Author:** Phase-C manager session (Opus)
**Binding contract:** OpenUBEM CLAUDE.md governance + `openubem/results/plotting_suite.py`
existing patterns. This is a **reporting-layer figure task** — no resimulation, no DESIGN
change, no gate/core-math edits.

User request (verbatim intent): (1) add an "EUI comparison" of the 12-cell overview grid —
delivered as **three separate comparison plots**; (2) give the 12-cell overview grid the same
**map background** the single-cell `*__eui_map.png` already has. All four outputs save to
`openubem/outputs/comparisons/`.

---

## 1. Hard rules for the executor (Sonnet)

- Stay in cwd `C:\Users\o_iseri\Desktop\OpenUBEM`. Do not `cd` elsewhere.
- **Do not write plans.** Execute this doc top-to-bottom. If a fact here conflicts with the
  code, STOP and quote the conflict — do not invent.
- **Edit only these files:** `openubem/results/plotting_suite.py`,
  `scripts/render_plots.py`, `tests/test_plotting_suite.py`. Nothing else.
- **Do NOT touch** `openubem/results/visualization.py` (frozen), any gate/simulation module,
  `05_results.*` artifacts, OVERVIEW/DESIGN docs, or `r7_service_loads.csv` (read-only input).
- **Additive only:** new functions are added; the only modification to an existing function is
  T01 (basemap into `plot_overview_grid`). Do not change the math or signatures of
  `plot_eui_map`, `_load_cell_footprints`, `_load_cell_gdf`, `_save`.
- Default to **no comments**; one short line max where the WHY is non-obvious.
- All figures land in `openubem/outputs/comparisons/` (the `COMPARE_DIR` constant). Never bury
  under `docs/`.
- Do not commit (git is handled externally). Do not run EnergyPlus, sbatch, or any network call
  except the basemap tile fetch that `contextily` already performs in `plot_eui_map`.

## 2. File layout to touch

```
openubem/results/plotting_suite.py   ← +3 new plot fns, +1 ref-loader helper, +basemap in grid
scripts/render_plots.py              ← +_render_comparison(), +"comparison" to --only choices
tests/test_plotting_suite.py         ← +smoke tests for the 3 new fns
openubem/outputs/comparisons/        ← 4 PNGs land here (1 regenerated, 3 new)
```

## 3. Dependency decisions (pre-decided — do not re-debate)

- **Single per-building source for all three comparison plots** = `docs/validations/overAll/results/r7_service_loads.csv`
  (it already carries `cell`, `total_eui_kwh_m2`, `total_eui_reconstructed_kwh_m2`,
  `simulation_status`, `reconstruction_applied` for all 8 152 buildings). Read it once per plot
  with pandas. Do **not** re-open the 12 `05_results.gpkg` files for the comparison plots.
- **Reference for Plot A** = the region-correct CBECS-2018 weighted-mean site EUI, recomputed
  from `inputs/reports/cbecs_2018_{region}_eui.csv` as `np.average(eui_kwh_m2, weights=finalwt)`.
  Recompute (don't hard-code) so the figure can't silently drift; the provenance values in §5
  are the cross-check.
- **contextily** is already a working dependency (used by `plot_eui_map`). Reuse the exact
  zoom-fallback pattern. No new packages.
- Colormap stays **`YlOrRd`** for EUI continuity with the existing maps.
- Figure DPI/save go through the existing `_save()` helper (150 dpi, tight bbox).

## 4. Source-of-truth verified facts (manager-grepped 2026-06-17)

`openubem/results/plotting_suite.py`:
- L28 `COMPARE_DIR = _BASE/"openubem"/"outputs"/"comparisons"`.
- L33 `_SUCCESS_STATUSES = {"success","success_cached","success_csv_fallback"}`.
- L40 `_save(fig, path) -> Path` (mkdirs, 150 dpi, closes fig).
- L92 `plot_eui_map(...)` — basemap pattern to mirror: L102-107 `to_crs(epsg=3857)` with
  try/except; L138-156 contextily loop `for zoom in (None,17,16,15,14,13)` over
  `ctx.providers.CartoDB.Positron`, `basemap_ok` flag, graceful warn-and-continue.
- L455 `_CITIES = ["nyc","la","austin"]`; L456 `_RINGS = ["centre","urban","suburban","rural"]`.
- L459 `plot_overview_grid(output_path=None) -> (Path, vmin, vmax)` — 3×4 grid; L520 already
  reprojects each panel to EPSG:3857; L497 `figsize=(16,12)`; shared `YlOrRd` norm vmin/vmax =
  2nd/98th pct; **L518/L464 explicitly "no basemap"** — this is what T01 changes.

`docs/validations/overAll/results/r7_service_loads.csv` — 8 152 rows; cols include
`total_eui_kwh_m2`, `total_eui_reconstructed_kwh_m2`, `cell`, `simulation_status`,
`reconstruction_applied`, `archetype_id`.

`inputs/reports/cbecs_2018_{region}_eui.csv` — cols `pba_code,pba_label,sqft,eui_kwh_m2,finalwt`.
Region weighted-mean site EUI (provenance cross-check, kWh/m²·yr):
- `middle_atlantic` = **237.3**  (→ NYC cells)
- `pacific`         = **188.4**  (→ LA cells)
- `west_south_central` = **222.8**  (→ Austin cells)
- `new_england`    = 220.9  (R5 baseline only — **do NOT use** for region-correct)

**Region map (verified vs `r6_rescore_summary.csv` + `cases/austin_centre/r6_gates_report.txt`):**
`nyc → middle_atlantic`, `la → pacific`, `austin → west_south_central`.

`scripts/render_plots.py` — L17-32 imports from plotting_suite; L118 `_render_overview()` calls
`plot_overview_grid(COMPARE_DIR/"eui_overview_grid.png")`; L124 `main()`; L128 `--only` choices
`["sim","val","overview"]`; `_ALL_CELLS` at L38.

## 5. Task list

### T01 — Basemap into the overview grid (request #2)
- **What:** Modify `plot_overview_grid` so each of the 12 panels renders its footprints on a
  CartoDB.Positron basemap (like `plot_eui_map`), instead of on white.
- **Why:** User wants the grid panels to match the single-cell map's geographic context.
- **How:** Panels already reproject to EPSG:3857 (L520). After the success/failed `.plot(...)`
  calls for each panel, before `set_axis_off`, set the panel extent to the panel's
  `total_bounds` + 10% margin (mirror `plot_eui_map` L131-136) **then** run the same contextily
  zoom-fallback loop on that panel's `ax`. Wrap in try/except; on failure leave the panel on
  white (current behaviour) — never raise. Keep `linewidth`/`edgecolor` as-is but consider
  raising panel polygon `alpha` slightly is NOT required — leave styling unchanged except the
  basemap. Keep the shared colorbar, suptitle, and `(path, vmin, vmax)` return signature
  **unchanged**. Performance note: 12 tile fetches is acceptable; do not parallelize.
- **How to test:** Covered by T07 (visual) + T06 (smoke: still returns a 3-tuple, file exists).

### T02 — Plot A: simulated vs CBECS reference (per cell)
- **What:** New fn `plot_eui_vs_reference(output_path: Path|None=None) -> Path`, saving
  `COMPARE_DIR/"eui_vs_cbecs_reference.png"` by default. Plus a small helper
  `_cbecs_region_mean(region: str) -> float` that reads `inputs/reports/cbecs_2018_{region}_eui.csv`
  and returns `np.average(eui_kwh_m2, weights=finalwt)`.
- **Why:** Show, per cell, how modeled mean EUI sits against the region-correct CBECS benchmark.
- **How:** Read r7 CSV; keep rows with `simulation_status ∈ _SUCCESS_STATUSES`; group by `cell`,
  take mean `total_eui_kwh_m2`. Map each cell's city prefix → region → reference via the §4
  region map + `_cbecs_region_mean`. Order cells exactly as
  `[f"{c}_{r}" for c in _CITIES for r in _RINGS]`. Draw a grouped/paired horizontal or vertical
  bar per cell: modeled mean vs region reference; annotate each pair with
  `dev% = (model-ref)/ref*100` (sign retained; negative = under). Title:
  `"OpenUBEM — Modeled EUI vs CBECS-2018 region reference (per cell)"`. Note in a small caption
  that reference is the region weighted-mean (NYC=Mid-Atlantic, LA=Pacific, Austin=W-S-Central).
- **How to test:** T06 smoke (returns Path, file exists, `_cbecs_region_mean("pacific")` ≈ 188.4
  within ±1.0).

### T03 — Plot B: simulated vs service-load reconstructed (per cell)
- **What:** New fn `plot_sim_vs_reconstructed(output_path: Path|None=None) -> Path`, saving
  `COMPARE_DIR/"eui_sim_vs_reconstructed.png"`.
- **Why:** Visualize the V16 service-load uplift per cell (the r7 deliverable).
- **How:** Read r7 CSV; keep rows with `reconstruction_applied == True`; group by `cell`; take
  mean of `total_eui_kwh_m2` (sim) and `total_eui_reconstructed_kwh_m2` (recon). Same cell order
  as T02. Paired bars per cell (sim vs recon); annotate uplift% =
  `(recon-sim)/sim*100`. Add a one-line caption flagging the food-service caveat (food-service
  uplift ~+203% inflates any cell with QSR/restaurants; see V16 §4). Title:
  `"OpenUBEM — Simulated vs Service-Load-Reconstructed EUI (per cell)"`.
- **How to test:** T06 smoke (returns Path, file exists). Optional: assert recon mean ≥ sim mean
  for every cell (reconstruction only adds energy).

### T04 — Plot C: cross-cell EUI summary
- **What:** New fn `plot_cross_cell_eui(output_path: Path|None=None) -> Path`, saving
  `COMPARE_DIR/"eui_cross_cell_summary.png"`.
- **Why:** One figure comparing the 12 cells' building-EUI distributions against each other.
- **How:** Read r7 CSV; keep `simulation_status ∈ _SUCCESS_STATUSES`; per cell take the
  `total_eui_kwh_m2` series. Draw a **box plot** (matplotlib `ax.boxplot`, `showfliers=False`)
  of the 12 cells, **ranked by median ascending**, shared y-axis, cell labels rotated. Overlay
  the median value as text. Title:
  `"OpenUBEM — Building EUI distribution by cell (ranked by median)"`. Y-label
  `"Total EUI (kWh/m²/yr)"`. Cap y at a sane percentile (e.g. 99th of pooled) so QSR outliers
  don't flatten the boxes — `showfliers=False` plus an explicit `set_ylim` top.
- **How to test:** T06 smoke (returns Path, file exists, ≤12 boxes).

### T05 — Wire into render_plots.py
- **What:** Add `_render_comparison()` that calls `plot_eui_vs_reference`,
  `plot_sim_vs_reconstructed`, `plot_cross_cell_eui` (each into `COMPARE_DIR`), and add
  `"comparison"` to the `--only` choices in `main()`. Import the 3 new fns.
- **Why:** Make the new plots reproducible from the CLI like the existing ones.
- **How:** Mirror `_render_overview()` style (mkdir COMPARE_DIR, log each path). Default run
  (no `--only`) should render comparison plots **in addition to** the existing sim/val/overview
  groups — append the call in `main()`'s default branch. `--only overview` must still regenerate
  the now-basemapped grid.
- **How to test:** Covered by T07.

### T06 — Tests
- **What:** Add smoke tests to `tests/test_plotting_suite.py` for the 3 new fns +
  `_cbecs_region_mean`, plus a regression assertion that `plot_overview_grid` still returns a
  3-tuple.
- **Why:** Lock the contract; catch import/signature breakage.
- **How:** Tests may write to a tmp_path and assert the returned Path exists and is non-empty.
  `_cbecs_region_mean("pacific")` within ±1.0 of 188.4. Use existing test fixtures/conventions in
  the file; if the r7 CSV or CBECS CSVs are required and present on disk, read them directly
  (these are committed inputs, not synthetic fixtures). If a required input is absent, `skip`
  with a clear reason rather than fail.
- **How to test:** `pytest tests/test_plotting_suite.py -q`.

### T07 — Render + manager visual audit (STOP-and-report)
- **What:** Run `python scripts/render_plots.py --only comparison` then
  `--only overview`; confirm the 4 PNGs in `openubem/outputs/comparisons/`:
  `eui_overview_grid.png` (now with basemaps), `eui_vs_cbecs_reference.png`,
  `eui_sim_vs_reconstructed.png`, `eui_cross_cell_summary.png`.
- **Why:** Figures are the deliverable; only a visual check confirms correctness.
- **How:** Report file sizes + mtimes and any basemap-unavailable warnings. Do not judge visual
  quality yourself — hand back to the manager for the visual sign-off.
- **How to test:** Manager reviews the 4 PNGs.

## 6. Stop-and-report points

- **CP-1 — after T04:** all three comparison fns + the grid basemap exist and import cleanly.
  Report signatures and a one-line dry-run (each fn callable). Manager reviews before wiring.
- **CP-2 — after T07:** rendered + tested. Report pytest summary + the 4 file paths/sizes +
  warnings. Manager does the visual sign-off.

## 7. Progress log

#### T01 — Basemap into the overview grid — completed 2026-06-17
- Artifacts: `openubem/results/plotting_suite.py` (modified `plot_overview_grid`)
- Deviations: none — exact zoom-fallback loop from `plot_eui_map` mirrored; extent set before basemap call; graceful except on failure; panel `alpha`/`linewidth` unchanged.
- Test status: `test_plot_overview_grid_returns_3tuple` PASSED (runtime cells present; 5/5 suite passed).
- Notes: basemap fetches 12 tiles at runtime; graceful warn-and-continue on any tile failure.

#### T02 — Plot A: simulated vs CBECS reference — completed 2026-06-17
- Artifacts: `openubem/results/plotting_suite.py` (`_cbecs_region_mean`, `plot_eui_vs_reference` added)
- Deviations: none — reads r7 CSV, groups by cell, maps city→region→CBECS mean via `np.average`; provenance cross-check: pacific=188.36 (expect 188.4 ±1), middle_atlantic=237.34 (expect 237.3), west_south_central=222.77 (expect 222.8).
- Test status: `test_cbecs_region_mean_pacific` PASSED, `test_plot_eui_vs_reference` PASSED.
- Notes: dev% annotated above each pair; caption names region mapping.

#### T03 — Plot B: simulated vs service-load reconstructed — completed 2026-06-17
- Artifacts: `openubem/results/plotting_suite.py` (`plot_sim_vs_reconstructed` added)
- Deviations: none — filters `reconstruction_applied == True`; grouped paired bars sim vs recon; uplift% annotated; food-service caveat caption included.
- Test status: `test_plot_sim_vs_reconstructed` PASSED.
- Notes: produces 89 778 byte PNG.

#### T04 — Plot C: cross-cell EUI summary — completed 2026-06-17
- Artifacts: `openubem/results/plotting_suite.py` (`plot_cross_cell_eui` added)
- Deviations: none — boxplot ranked by median ascending; `showfliers=False`; y-cap at 99th pct; median value text overlay.
- Test status: `test_plot_cross_cell_eui` PASSED.
- Notes: produces 75 912 byte PNG; 12 boxes confirmed (all 12 cells present in r7 CSV).

#### T05 — Wire into render_plots.py — completed 2026-06-17
- Artifacts: `scripts/render_plots.py` (`_render_comparison()` added; `"comparison"` added to `--only` choices; 3 new fns imported; default no-flag run now calls `_render_comparison()`)
- Deviations: none — mirrors `_render_overview()` style; all 3 fns routed into COMPARE_DIR; default branch appends comparison call after overview.
- Test status: covered by T07 (CLI smoke confirmed).
- Notes: `--only comparison` logs 3 Written lines; `--only overview` logs 1 Written line with vmin/vmax.

#### T06 — Tests — completed 2026-06-17
- Artifacts: `tests/test_plotting_suite.py` (added `test_plot_sim_vs_reconstructed_recon_ge_sim`; confirmed 5 CP-1 smoke tests still present and passing)
- Deviations: none — optional recon >= sim assertion added as a separate test; reads r7 CSV directly per plan §T06 guidance; skips if CSV absent.
- Test status: `pytest tests/test_plotting_suite.py -q` → **24 passed, 1 warning in 28.27s**. The 1 warning is a pre-existing matplotlib "no artists with labels" from `test_plot_eui_rank_curve_empty`, unrelated to this task.
- Notes: all 5 CP-1 smoke tests (cbecs_region_mean, eui_vs_reference, sim_vs_reconstructed, cross_cell_eui, overview_grid_3tuple) confirmed passing.

#### T07 — Render + manager visual audit — completed 2026-06-17
- Artifacts: 4 PNGs in `openubem/outputs/comparisons/`:
  - `eui_overview_grid.png` — 1 027 102 bytes, mtime 2026-06-17 11:18:58
  - `eui_vs_cbecs_reference.png` — 86 225 bytes, mtime 2026-06-17 11:18:41
  - `eui_sim_vs_reconstructed.png` — 89 778 bytes, mtime 2026-06-17 11:18:41
  - `eui_cross_cell_summary.png` — 75 912 bytes, mtime 2026-06-17 11:18:41
- Deviations: none.
- Test status: see T06 (24 passed). CLI exits 0 for both `--only comparison` and `--only overview`.
- Notes: 12 "Basemap unavailable (No module named 'contextily')" warnings on `--only overview` — graceful fallback working as designed; `contextily` not installed in this environment. Overview grid rendered footprints-only. Manager visual sign-off pending.

#### MANAGER CLOSEOUT — completed 2026-06-17
- **contextily gap caught + fixed:** CP-2 reported the grid basemap silently falling back to white because `contextily` was absent from `.venv` (undeclared dependency — the original `*__eui_map.png` basemaps relied on it ad-hoc). Manager installed `contextily==1.7.0` into `.venv` (+ rasterio/mercantile/xyzservices/affine/geopy) and re-rendered.
- **Re-render result:** `eui_overview_grid.png` now **2 388 229 bytes** (was 1 027 102) — basemaps confirmed rendering in all 12 panels; no "basemap unavailable" warning. Three comparison PNGs re-rendered identically.
- **Manager visual sign-off — ALL 4 PASS:**
  - `eui_overview_grid.png` — CARTO street basemap visible under EUI footprints in every panel (request #2 satisfied).
  - `eui_vs_cbecs_reference.png` — region refs correctly grouped (NYC 237 / LA 188 / Austin 223); dev% signs verified (nyc_centre 144 vs 237 = −39%).
  - `eui_sim_vs_reconstructed.png` — matches V16 §4 table cell-for-cell (austin_centre 247→425 +72%, nyc_suburban 270→357 +32%); all uplifts positive.
  - `eui_cross_cell_summary.png` — boxplots ranked by median ascending (la_suburban 105 → nyc_rural 227), fliers hidden, y-cap sane.
- **Open follow-up — RESOLVED 2026-06-17 (user-approved):** `contextily >= 1.3` added to core `dependencies` in `pyproject.toml` (runtime dep — `plotting_suite.py` basemaps). Closes the silent-blank-basemap risk on env rebuild.
- **Status: COMPLETE.** All 4 deliverables shipped and visually signed off.
