# PLAN — 3D viewer debug: every building must show EUI + archetype; sharper basemap

- **Slug:** `3dviz-debug-representation`
- **Date:** 2026-07-03
- **Binding contract:** the frozen specs behind the 3D arc (`docs/docs_ACTIVE/3D/PLAN_3dviz_implementation.md`
  §0 faithful-to-model, §9 manager rulings, V09 colour/accessibility). This debug plan is a
  **correction of the T22 muting default**, which the main PLAN itself flagged as *"a reversible
  manager default pending the user's veto"* (PLAN line 1177). The user has now vetoed it.
- **Parent PLAN:** `docs/docs_ACTIVE/3D/PLAN_3dviz_implementation.md` (T01–T22 done, CP-4 audited).
  This doc does NOT renumber that plan; it adds a self-contained debug arc **D01–D06**. When D06
  closes, append a one-line pointer + progress entries back into the parent PLAN §8.

---

## 1. Problem statement (what the user reported)

On opening `austin_centre`, `austin_rural`, `austin_suburban` viewers:

1. **"Most buildings have no EUI / no archetype — transparent volumes."**
2. **"Building count in the .html does not match the `phaseE_overview_grid.png` grid."**
3. **General:** basemap image resolution looks low / blurry.

## 2. Root-cause diagnosis (manager, already verified — do NOT re-debate)

**Cause A — the T22 footprint-only muting swallows the scene.** `colormaps.mjs::buildingFillColor`
(line ~105) short-circuits: `if (heightMissing(attrs)) return FOOTPRINT_ONLY_MUTED` — a flat beige
`#E4DFD6` — **before** the EUI/archetype lookup, and `buildingFillOpacity` returns `0.45` for the
same buildings. `heightMissing` is true whenever `data_quality_flag` contains `no_height`
(OSM had no height tag; height is imputed to 1 storey / 3.5 m). The EUI **and** archetype are REAL
simulation outputs and are present in the payload — they are simply painted over with beige and made
translucent. Because OSM height coverage is sparse in most US cells, this hides most or all buildings:

| cell | n | no_height | % muted |
|---|---|---|---|
| nyc_centre | 738 | 121 | 16% |
| nyc_urban | 1779 | 40 | 2% |
| **nyc_suburban** | 1589 | 1589 | **100%** |
| **nyc_rural** | 198 | 198 | **100%** |
| la_centre | 226 | 45 | 20% |
| la_urban | 618 | 42 | 7% |
| la_suburban | 1343 | 15 | 1% |
| la_rural | 149 | 1 | 1% |
| **austin_centre** | 413 | 349 | **85%** |
| austin_urban | 425 | 47 | 11% |
| **austin_suburban** | 437 | 114 | 26% |
| **austin_rural** | 245 | 245 | **100%** |
| **TOTAL** | 8160 | 2806 | **34%** |

The three cells the user opened are exactly the worst cases (85%, 100%, 26%). Fixing Cause A is the
whole of Fix A.

**Cause B — the "count mismatch" is NOT a data defect.** For every cell,
`len(05_results.csv) == len(04_simulation_manifest.parquet) == len(01_buildings.gpkg) ==` the number
of CityObjects embedded in the HTML (verified: austin_centre 413/413/413/413, all with `total_eui`
and `archetype_id`; `context` placeholder features = 0). Every building is simulated and present. The
perceived shortfall is a **visual** consequence of Cause A: translucent beige buildings recede into
the background so the scene looks far sparser than the solid choropleth grid. Fixing Cause A fixes the
perception. **No re-simulation, no geometry change, no data backfill is required or permitted here.**

**Cause C — basemap is upsampled, hence blurry.** `basemap_raster.generate_basemap` fetches with
`zoom="auto"`, which under-selects the tile zoom: source `fetched_px` is only 768×768 (austin_centre)
to 1024×1280 (nyc), then bilinearly **upsampled** to `target_px=2048`. Stretching ~800 px to 2048 is
the blur. Fetching at a higher zoom so the native raster ≥ the output grid removes the upsampling.

## 3. Hard rules for the executor

- Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`. Do not write plans; execute this one.
- **Faithful-to-model is still binding.** Nothing on screen may be fabricated. This fix REMOVES a
  visual override so the REAL bound EUI/archetype shows — it does not invent data.
- **No geometry change. No re-simulation. No attribute backfill.** Only viewer colour/opacity logic,
  basemap fetch resolution, the bundle rebuild, and re-export.
- Default to no comments; one short line max when the WHY is non-obvious.
- Do NOT leak `node_modules/` / `package.json` / `package-lock.json` into the repo — keep the
  esbuild + puppeteer toolchain in the session scratchpad only (same discipline as T21/T22).
- Stop-and-report at the checkpoint in §7 before copying anything to `openubem/outputs/3D`.
- If any DESIGN/spec point is ambiguous, STOP and quote it — do not invent.

## 4. Files this arc touches (exhaustive)

```
openubem/viz/shell/colormaps.mjs        ← Fix A: remove fill/opacity muting override
openubem/viz/shell/viewer_app.mjs       ← Fix A: legend row for footprint-only (outline, not beige swatch)
openubem/viz/shell/viewer.js            ← rebuilt esbuild bundle (vendored artifact)
tests/viz_js/viewer_logic.test.mjs      ← update the T22 muting assertions to the new contract
openubem/viz/basemap_raster.py          ← Fix B: higher-resolution fetch (zoom/target_px)
docs/.../phaseE/<cell>/06_basemap_utm.png|.json   ← regenerated higher-res basemap cache (12 cells)
docs/docs_ACTIVE/3D/outputs/<cell>_viewer.html    ← regenerated (12 cells) — PRIMARY delivery dir
openubem/outputs/3D/<cell>_viewer.html            ← copied here ONLY after the §7 audit passes
```

Do not touch any other file. Do not edit the parent PLAN except to append progress entries at the end.

## 5. Source-of-truth verified facts (manager already grepped these)

- **F-A1** `colormaps.mjs:104-116` `buildingFillColor` — first line `if (heightMissing(attrs)) return
  FOOTPRINT_ONLY_MUTED.slice();`. Removing it lets footprint-only buildings flow to the normal
  EUI-ramp / archetype-sector return, exactly like every other building.
- **F-A2** `colormaps.mjs:118-120` `buildingFillOpacity` — returns `FOOTPRINT_ONLY_OPACITY (0.45)`
  when `heightMissing`, else `1.0`.
- **F-A3** The footprint-only status already has a NON-destructive cue that must stay: the
  dashed-magenta outline overlay `viewer_app.mjs::_buildFlatFootprintOverlay` (line ~304, colour
  `0xff5fb0`, `LineDashedMaterial`) drawn per building where `heightMissing`, PLUS the detail-pane
  flat-footprint badge (`flatFootprintBadge`, "Height: not in OSM — footprint only…"). Both are
  independent of the fill and MUST remain. `heightMissing` / `flatFootprintBadge` stay as-is.
- **F-A4** Legend rows referencing the beige swatch: `viewer_app.mjs` lines ~510 and ~527
  (`${this._swatch(FOOTPRINT_ONLY_MUTED)} … footprint only (no OSM height)` in BOTH the archetype and
  EUI legends).
- **F-A5** Node tests asserting the OLD muting contract to rewrite:
  `tests/viz_js/viewer_logic.test.mjs` lines ~214-260 (block header "T22 … muted placeholder
  restyle"): the tests at ~217, ~234, ~256 assert footprint-only returns `FOOTPRINT_ONLY_MUTED` /
  opacity `0.45`. The `heightMissing` tests (~188-206) and `flatFootprintBadge` test (~210) are
  CORRECT and must stay green unchanged.
- **F-B1** `basemap_raster.generate_basemap` signature already exposes `target_px:int=2048` and
  `zoom:int|str="auto"`. The single network boundary is `_fetch_tile_image(... zoom=zoom ...)`.
  The two-pass reproject (Pass 1 learns aspect at natural res; Pass 2 resamples to target grid) is
  correct and must be preserved — only the inputs change.
- **F-C1** Re-export entry point: `openubem.viz.viewer_export.export_viewer_from_run(run_id, results_dir,
  manifest_path, out_dir, basemap_path=...)`. Geometry comes from the IDFs referenced by `manifest_path`
  (`idf_path` column). Attributes come from `results_dir/05_results.csv` + `01_buildings.gpkg`.
- **F-C2** IDFs are reachable two ways (verified on disk): (a) live Temp
  `C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\phaseE_er33\<cell>\step3\` (manifest +
  `idfs/*.idf`, all present); (b) durable per-cell archive
  `docs/.../phaseE/<cell>/<cell>_step3_idfs_archive.zip` containing `step3/03_idf_manifest.parquet`
  + `step3/idfs/*.idf`. Also `docs/.../phaseE/<cell>/04_simulation_manifest.parquet` carries the
  same `idf_path` values pointing at the Temp dir.

## 6. Manager decisions — PRE-DECIDED, do not re-open

1. **Footprint-only buildings render their REAL EUI (or archetype) colour at FULL opacity (1.0).**
   The "no OSM height" fact is conveyed ONLY by (a) the existing dashed-magenta outline overlay and
   (b) the detail-pane badge. No fill tint, no translucency.
2. **Keep `FOOTPRINT_ONLY_MUTED` / `FOOTPRINT_ONLY_OPACITY` exported** (harmless constants) so the
   diff stays minimal, but they are no longer read by `buildingFillColor` / `buildingFillOpacity`.
   (Executor may delete them instead IF it also cleans every import/test reference in the same commit;
   default is keep-but-unused.)
3. **Legend:** replace the beige footprint-only swatch row (both legends) with a short dashed-line
   indicator labelled `footprint only (no OSM height) — dashed outline`. A tiny inline SVG/CSS dashed
   line is fine; do not invent a new colour beyond the existing `#ff5fb0` outline hue.
4. **Basemap resolution target:** `target_px = 3072`, and fetch at a zoom high enough that the native
   fetched raster is **≥ the output grid in the long axis (no upsampling)** — in practice `auto`+1
   or `auto`+2. Concretely: compute contextily's auto zoom, then step zoom up until `fetched_px`
   long-axis ≥ `target_px` (cap the step at +3 to avoid a tile explosion). Verify effective
   resolution ≤ ~0.6 m/px per cell. **File-size guard:** each regenerated HTML must stay **< 45 MB**;
   if any cell exceeds it, drop that cell's `target_px` to 2560 and note it. Report the per-cell
   `fetched_px`, output px, m/px, and HTML size in the progress log.
5. **Primary output dir is `docs/docs_ACTIVE/3D/outputs/`.** Copy to `openubem/outputs/3D/` ONLY
   after the §7 manager audit greenlights. Overwrite the existing files in both dirs (same 12 names).
6. Regenerated `06_basemap_utm.png/.json` overwrite the cached basemaps in each
   `docs/.../phaseE/<cell>/` dir (they are the reproducibility anchor; higher-res is an improvement).

## 7. Task list

### D01 — Fix A: un-mute footprint-only fill + opacity (`colormaps.mjs`)
- **What:** In `buildingFillColor`, delete the `if (heightMissing(attrs)) return FOOTPRINT_ONLY_MUTED…`
  short-circuit so footprint-only buildings flow to the normal EUI/archetype return. In
  `buildingFillOpacity`, return `1.0` unconditionally (or delete the `heightMissing` branch).
- **Why:** Cause A (§2). EUI + archetype are real and must be shown for every building (user ask;
  faithful-to-model — this removes an override, invents nothing).
- **How:** Keep the `heightMissing` import only if still referenced; if the two functions were its
  only users in this file, drop the now-dead import. Do NOT touch `heightMissing` /
  `flatFootprintBadge` themselves. Decision §6.1/§6.2.
- **How to test:** covered by D03.

### D02 — Fix A: legend row + keep the outline cue (`viewer_app.mjs`)
- **What:** Replace the two beige-swatch footprint-only legend rows (§5 F-A4) with a dashed-outline
  indicator row (decision §6.3). Confirm `_buildFlatFootprintOverlay` and the detail-pane
  `flatFootprintBadge` path are untouched and still fire.
- **Why:** Footprint-only must remain legible after the fill un-mute, via outline + badge, not fill.
- **How:** Minimal DOM/CSS; reuse `#ff5fb0`. No new palette entries.
- **How to test:** visual, confirmed in D05 LIVE_SMOKE screenshots.

### D03 — Update the node muting tests to the new contract (`viewer_logic.test.mjs`)
- **What:** Rewrite the three T22 assertions (§5 F-A5): footprint-only building now returns its
  **EUI ramp colour** (NOT `FOOTPRINT_ONLY_MUTED`) in EUI mode, its **archetype sector colour** in
  archetype mode, and `buildingFillOpacity` returns **1.0** for a `no_height` building. Keep the
  `heightMissing` and `flatFootprintBadge` tests unchanged and green. Retitle the block from
  "muted placeholder" to reflect the new "footprint-only still shows its value" contract.
- **Why:** Tests are the contract; they must assert the corrected behaviour.
- **How to test:** `node --test tests/viz_js/` — full suite green.

### D04 — Fix B: higher-resolution basemap fetch (`basemap_raster.py`)
- **What:** Implement decision §6.4 — `target_px=3072` default and a zoom-bump loop so the native
  fetched raster is not upsampled. Preserve the two-pass reproject and the non-fatal
  fetch-failure→`None` contract exactly.
- **Why:** Cause C (§2).
- **How:** If `zoom == "auto"`, resolve contextily's auto zoom (e.g. via
  `contextily.tile._calculate_zoom(w,s,e,n)`), then increment until `max(src_w,src_h) >= target_px`
  or +3 reached; pass that int to `_fetch_tile_image`. Leave an explicit-int `zoom` arg honoured
  verbatim. Keep everything else identical.
- **How to test:** unit test with the existing monkeypatched `_fetch_tile_image` (assert the fetch is
  called with an int zoom ≥ auto when a small bbox would otherwise upsample); real resolution proven
  in D05.

### D05 — Regenerate all 12 viewers into `docs/docs_ACTIVE/3D/outputs/` + LIVE_SMOKE
- **What:** (1) Rebuild `viewer.js` via the exact `BUILD.md` esbuild command (pinned `three@0.155.0`,
  `cityjson-threejs-loader@0.4.0`, the 3 `--alias` flags), toolchain in scratchpad only. (2) Re-fetch
  the higher-res basemap for all 12 cells (overwrite each `06_basemap_utm.png/.json`). (3)
  `export_viewer_from_run` for all 12 → `out_dir=docs/docs_ACTIVE/3D/outputs`. Use the durable archive
  zips (unzip to scratch, use `step3/03_idf_manifest.parquet`) as the manifest source; the live Temp
  `phaseE_er33` dir is an acceptable shortcut if every `idf_path` verifies present. VERIFY each cell's
  IDF paths exist before export.
- **Why:** Ship Fix A + Fix B across every cell.
- **How to test — LIVE_SMOKE (headless Chromium / Puppeteer, scratchpad toolchain):**
  - Per cell: `n_buildings` equals `len(05_results.csv)` (count parity — directly answers the user's
    "count mismatch"); `has_basemap=True`.
  - Open ≥3 cells from `file://` incl. austin_centre + one 100%-no_height cell (nyc_suburban or
    austin_rural): **0 genuine network requests, 0 console errors** (the inline `data:` texture URI is
    not a network request — same as T20/T22).
  - **Fix A proof:** in a ≥85%-no_height cell, assert via the live API that a `no_height` building now
    carries a viridis EUI colour in its vertex-colour buffer (NOT `#E4DFD6`) and full opacity; capture
    a before/after overview screenshot showing the cell now reads as a coloured EUI field, not beige.
  - **Fix B proof:** report each cell's `fetched_px`, output px, m/px, HTML size; screenshot one cell's
    basemap showing sharper streets than the prior 2048-upsampled version.
  - Offline re-check (the 5-regex external-fetch grep) clean on the 3 opened cells.
- **Deliverable to manager:** a short `openubem/outputs/3D/debug_regen_report.md` (or under the debug
  dir) with the per-cell table + screenshot paths. **STOP here for manager audit (§7 checkpoint).**

> **CHECKPOINT — STOP after D05.** Do NOT copy to `openubem/outputs/3D` yet. Report: the colormaps
> diff, the basemap diff, the node+python test summaries, the 12-cell parity/size/resolution table,
> and the Fix-A before/after screenshots. Wait for manager greenlight.

### D06 — Copy to `openubem/outputs/3D/` + parent-PLAN progress entries (AFTER audit)
- **What:** Once the manager greenlights D05: copy all 12 regenerated `<cell>_viewer.html` to
  `openubem/outputs/3D/` (overwrite). Append D01–D06 progress entries to the parent PLAN §8 and add a
  one-line pointer from the parent PLAN to this debug doc. Tick the master checklist if it references
  the 3D arc.
- **Why:** User: "when we complete the task fully we can create another copy under `openubem/outputs/3D`."
- **How to test:** both dirs hold the same 12 files, byte-identical; `git status` shows no
  `node_modules`/toolchain leak.

## 8. Stop-and-report points
1. **After D03** — Fix A code + tests done, before touching Python/basemap. (Quick sanity that the
   node suite is green on the new contract.)
2. **After D05** — the binding checkpoint above (manager audit before the `openubem/outputs/3D` copy).

## 9. Progress log
_(Executor appends one entry per completed task here, per project convention.)_

#### D01 — Fix A: un-mute footprint-only fill + opacity (`colormaps.mjs`) — completed 2026-07-03
- Artifacts: `openubem/viz/shell/colormaps.mjs` (`buildingFillColor` no longer
  short-circuits on `heightMissing`; `buildingFillOpacity` returns `1.0`
  unconditionally; dropped the now-dead `heightMissing` import per §6.1/§6.2;
  `FOOTPRINT_ONLY_MUTED`/`FOOTPRINT_ONLY_OPACITY` kept exported but unused,
  comment updated to say so).
- Deviations: none.
- Test status: covered by D03 (node suite green, see below).
- Notes: `heightMissing`/`flatFootprintBadge` in `viewer_logic.mjs` untouched.

#### D02 — Fix A: legend row + keep the outline cue (`viewer_app.mjs`) — completed 2026-07-03
- Artifacts: `openubem/viz/shell/viewer_app.mjs` (both legend blocks — archetype
  and EUI — now render `_dashedLegendRow()` instead of the beige
  `FOOTPRINT_ONLY_MUTED` swatch row; dropped the now-unused
  `FOOTPRINT_ONLY_MUTED` import); `openubem/viz/shell/viewer.css`
  (`.ubem-swatch-dashed` — transparent box, dashed top border, reuses
  `#ff5fb0`, no new palette entry). `_buildFlatFootprintOverlay` and
  `flatFootprintBadge` call sites unchanged.
- Deviations: none.
- Test status: visual only per plan — confirmed in D05 LIVE_SMOKE screenshots.
- Notes: legend row label reads "footprint only (no OSM height) — dashed
  outline".

#### D03 — Update the node muting tests to the new contract (`viewer_logic.test.mjs`) — completed 2026-07-03
- Artifacts: `tests/viz_js/viewer_logic.test.mjs` — rewrote the 3 T22
  assertions (§5 F-A5) to the corrected contract: footprint-only building now
  returns its real EUI ramp colour (not `FOOTPRINT_ONLY_MUTED`) in EUI mode,
  its real archetype-sector colour in archetype mode, and `buildingFillOpacity`
  returns `1.0` unconditionally. Retitled the block header from "muted
  placeholder restyle" to the D03 framing. Kept the two
  `FOOTPRINT_ONLY_MUTED`-byte-distinctness tests (constant is still exported,
  §6.2) with updated wording ("kept but unused"). `heightMissing` (4 tests) and
  `flatFootprintBadge` (1 test) unchanged and green.
- Deviations: none.
- Test status: `node --test tests/viz_js/*.test.mjs` — 33/33 pass, 0 fail.
- Notes: none.

#### D04 — Fix B: higher-resolution basemap fetch (`basemap_raster.py`) — completed 2026-07-03
- Artifacts: `openubem/viz/basemap_raster.py` — new `_resolve_zoom()` helper
  (pure local `mercantile` tile-count math, no extra network call) resolves
  `zoom="auto"` to the smallest int in `{auto, auto+1, auto+2, auto+3}` whose
  estimated native raster long-axis `>= target_px`, capped at the provider's
  `max_zoom` when known; explicit int `zoom` still honoured verbatim (F-B1).
  `generate_basemap` default `target_px` raised `2048 -> 3072`. Sidecar now
  records the resolved int `zoom`, not the literal `"auto"`. Two-pass
  reproject and fetch-failure->`None` contract untouched.
  `tests/test_viz_basemap_raster.py` — added
  `test_generate_basemap_bumps_auto_zoom_to_avoid_upsampling` (real ~1.5 km
  cell-scale bbox — the existing 100 m unit fixture already saturates the
  provider's `max_zoom` so it can't exercise a bump) and
  `test_generate_basemap_explicit_int_zoom_honoured_verbatim`.
- Deviations: none.
- Test status: `pytest tests/test_viz_basemap_raster.py -v` — 6/6 pass (4
  pre-existing + 2 new). Full `pytest tests/ -k viz` — 54/54 pass (no
  regressions elsewhere in the viz suite).
- Notes: sanity-checked against a realistic Austin-scale bbox (1.5 km):
  auto zoom 16 -> fetched ~768-1024 px long axis (matches the bug report);
  resolved zoom 18 -> ~3328 px long axis, no upsampling at `target_px=3072`,
  effective resolution ~0.45 m/px.

#### D05 — Regenerate all 12 viewers + LIVE_SMOKE — completed 2026-07-03
- Artifacts:
  - `openubem/viz/shell/viewer.js` — rebuilt via the exact `BUILD.md` esbuild
    command (pinned `three@0.155.0` + `cityjson-threejs-loader@0.4.0` + the 3
    `--alias` flags), toolchain in session scratchpad only.
  - 12 × `docs/docs_ACTIVE/3D/outputs/<cell>_viewer.html` (regenerated, all
    mtimes 10:03–10:11).
  - 12 × `docs/docs_VALIDATION/.../phaseE/<cell>/06_basemap_utm.png` + `.json`
    (higher-res, overwritten, all mtimes 10:02–10:11).
  - `docs/docs_ACTIVE/3D/debug/debug_regen_report.md` (per-cell parity+size+
    resolution table + screenshot paths).
  - 6 screenshots in `docs/docs_ACTIVE/3D/debug/Image-outputs/`:
    `austin_centre_before/after.png`, `nyc_suburban_before/after.png`,
    `austin_centre_basemap_after.png`, `austin_centre_basemap.png`.
- Deviations:
  - IDF manifest source = live Temp `phaseE_er33/<cell>/step3/
    03_idf_manifest.parquet` (the explicitly-permitted §D05 shortcut) rather
    than unzipping the durable archive — verified every `idf_path` present on
    disk for all 12 cells (0 missing across 8,160) before export, so the
    STOP-guard condition is satisfied.
  - Three rural cells exceed the plan's "~0.6 m/px" guideline (nyc_rural 0.708,
    la_rural 1.075, austin_rural 0.772) — flagged in the report. The binding
    Fix-B requirement (no upsampling: fetched long-axis ≥ output long-axis, §6.4)
    holds for all 12; rural m/px is higher purely because those cells span a
    larger extent inside the fixed `target_px=3072` grid, not the Cause-C blur.
    No cell needed the `target_px=2560` file-size fallback (largest HTML
    nyc_centre 37.89 MB < 45 MB).
- Test status:
  - Count parity: 12/12 `n_buildings == len(05_results.csv)`; basemap: 12/12
    `has_basemap=true`.
  - Opened austin_centre + nyc_suburban (100% no_height) + la_rural from
    `file://`: 0 network requests, 0 console errors each.
  - Fix-A proof (live API): austin_centre `relation/13781131` (no_height, EUI
    172.04) → viridis `[70,190,111]` alpha 1.0 (not #E4DFD6); nyc_suburban
    `way/1010383033` (no_height, EUI 143.66) → viridis `[72,36,116]` alpha 1.0.
  - Offline 5-regex external-fetch grep: 0 violations on all 12.
  - Node `tests/viz_js/*.test.mjs` 33/33; Python `test_viz_basemap_raster.py`
    6/6; `pytest -k viz` 54/54.
- Notes: `git status` shows no `node_modules`/`package.json`/`package-lock.json`
  leak. STOP at §7/§8 checkpoint — D06 (copy to `openubem/outputs/3D/`) NOT
  started, awaits manager audit.

#### D06 — Copy to `openubem/outputs/3D/` + parent-PLAN progress entries — completed 2026-07-03
- Artifacts: 12 × `openubem/outputs/3D/<cell>_viewer.html` (overwrote the stale
  07:55 copies via `Copy-Item`, byte-identical to
  `docs/docs_ACTIVE/3D/outputs/<cell>_viewer.html` — no regeneration); one
  progress-log pointer entry appended to
  `docs/docs_ACTIVE/3D/PLAN_3dviz_implementation.md` §8.
- Deviations: none.
- Test status: 12/12 byte-size match confirmed (source vs
  `openubem/outputs/3D/`) — austin_centre 13,572,598; austin_rural 4,483,257;
  austin_suburban 7,845,929; austin_urban 12,328,988; la_centre 15,658,566;
  la_rural 3,229,393; la_suburban 16,955,757; la_urban 21,908,719;
  nyc_centre 39,732,337; nyc_rural 3,577,583; nyc_suburban 9,671,385;
  nyc_urban 24,931,655 — all MATCH.
- Notes: `git status` shows no `node_modules`/toolchain leak. This closes the
  D01–D06 arc; parent PLAN §8 now points here.
