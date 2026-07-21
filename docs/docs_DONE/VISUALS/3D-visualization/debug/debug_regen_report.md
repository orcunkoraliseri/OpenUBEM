# 3D viewer debug regen report (D05)

- **Date:** 2026-07-03
- **Plan:** `docs/docs_ACTIVE/3D/debug/PLAN_3dviz_debug_representation.md` (D01–D05)
- **Delivery dir (this arc):** `docs/docs_ACTIVE/3D/outputs/<cell>_viewer.html` (12 cells).
  Copy to `openubem/outputs/3D/` is **D06, gated on manager audit — NOT done here.**
- **Bundle:** `openubem/viz/shell/viewer.js` rebuilt via the exact `BUILD.md` esbuild
  command (pinned `three@0.155.0` + `cityjson-threejs-loader@0.4.0` + 3 `--alias` flags),
  toolchain in session scratchpad only. `git status`: no `node_modules`/`package.json`/
  `package-lock.json` leaked.
- **IDF source:** live Temp `phaseE_er33/<cell>/step3/03_idf_manifest.parquet` — every
  `idf_path` verified present on disk for all 12 cells (0 missing across 8,160 buildings).

## Per-cell table

Count parity = `n_buildings` (CityObjects embedded in HTML) vs `len(05_results.csv)`.
`m/px` = max(extent_utm) / max(output_px). All HTML < 45 MB (largest nyc_centre 37.89 MB).

| cell | n_bld | csv rows | parity | basemap | fetched_px | zoom | output_px | m/px | HTML (MB) |
|---|---|---|---|---|---|---|---|---|---|
| nyc_centre     | 738  | 738  | ✅ | ✅ | 4096×3584 | 18 | 3072×2687 | 0.610 | 37.89 |
| nyc_urban      | 1779 | 1779 | ✅ | ✅ | 2816×3072 | 18 | 2832×3072 | 0.456 | 23.78 |
| nyc_suburban   | 1589 | 1589 | ✅ | ✅ | 5376×5376 | 19 | 3072×3061 | 0.403 | 9.22  |
| nyc_rural      | 198  | 198  | ✅ | ✅ | 4864×3328 | 18 | 3072×2111 | 0.708 | 3.41  |
| la_centre      | 226  | 226  | ✅ | ✅ | 5376×5376 | 19 | 3072×3058 | 0.438 | 14.93 |
| la_urban       | 618  | 618  | ✅ | ✅ | 5376×5120 | 19 | 3072×2916 | 0.438 | 20.89 |
| la_suburban    | 1343 | 1343 | ✅ | ✅ | 5120×4864 | 19 | 3072×2909 | 0.419 | 16.17 |
| la_rural       | 149  | 149  | ✅ | ✅ | 3328×2816 | 17 | 3072×2599 | 1.075 | 3.08  |
| austin_centre  | 413  | 413  | ✅ | ✅ | 5120×4864 | 19 | 3072×2908 | 0.435 | 12.94 |
| austin_urban   | 425  | 425  | ✅ | ✅ | 5376×5120 | 19 | 3072×2915 | 0.456 | 11.76 |
| austin_suburban| 437  | 437  | ✅ | ✅ | 4864×4608 | 19 | 3072×2900 | 0.412 | 7.48  |
| austin_rural   | 245  | 245  | ✅ | ✅ | 3840×4608 | 18 | 2579×3072 | 0.772 | 4.28  |

**Totals:** 8,160 buildings across 12 cells; 12/12 count parity; 12/12 basemap present;
0 HTML ≥ 45 MB.

### Resolution note (m/px)
The binding Fix-B requirement — **no upsampling: fetched raster long-axis ≥ output grid
long-axis** — holds for all 12 cells, so streets/labels render crisply (see basemap
closeup). The plan's "~0.6 m/px" is a guideline sized for a ~1.5 km neighbourhood; the
three **rural** cells (nyc_rural 0.708, la_rural 1.075, austin_rural 0.772) exceed it
because they cover a much larger geographic extent inside the fixed `target_px=3072`
grid. This is inherent to extent ÷ pixels, not the upsampling blur that Cause C was
about — those cells are still non-upsampled. Flagged for manager visibility; no cell
required the `target_px=2560` file-size fallback (all < 45 MB at 3072).

## LIVE_SMOKE (headless Chromium / Puppeteer, scratchpad toolchain)

- **Count parity + basemap:** 12/12 `n_buildings == len(05_results.csv)`, 12/12
  `has_basemap=true`. Directly answers the user's "count mismatch" — every simulated
  building is present; the shortfall was purely the beige-mute visual (Cause A/B).
- **Offline 5-regex external-fetch grep:** 0 violations on all 12 cells.
- **Opened ≥3 cells from `file://`** (austin_centre, nyc_suburban [100% no_height],
  la_rural): **0 genuine network requests, 0 console errors** each (inline `data:` URIs
  excluded, as designed).
- **Fix-A proof (live viewer API):**
  - `austin_centre` (85% no_height): building `relation/13781131`,
    `data_quality_flag="no_height,no_year|GROUPMODE_MED"`, `total_eui_kwh_m2=172.04` →
    vertex-colour buffer = viridis `[70,190,111]` (linear-space `r=0.061,g=0.515,b=0.159`),
    **alpha=1.0**. NOT `#E4DFD6`.
  - `nyc_suburban` (100% no_height): building `way/1010383033`, `no_height` flag,
    `total_eui_kwh_m2=143.66` → viridis `[72,36,116]`, **alpha=1.0**. NOT `#E4DFD6`.
- **Fix-B proof:** basemap closeup (20 m scale) shows sharp streets/footprint outlines
  with no upsampling blur; per-cell `fetched_px`/`output_px`/`m/px`/HTML size in the
  table above.

## Screenshots (`docs/docs_ACTIVE/3D/debug/Image-outputs/`)

| file | what it shows |
|---|---|
| `austin_centre_before.png` | BEFORE — 85%-no_height cell, most buildings flat beige (EUI hidden) |
| `austin_centre_after.png`  | AFTER — same cell now a full viridis EUI field, dashed outlines mark footprint-only |
| `nyc_suburban_before.png`  | BEFORE — 100%-no_height cell, entire scene blank beige |
| `nyc_suburban_after.png`   | AFTER — same cell fully coloured EUI field |
| `austin_centre_basemap_after.png` | Fix-B — basemap closeup (buildings hidden), sharp streets at 20 m scale |
| `austin_centre_basemap.png` | AFTER overview (basemap + coloured buildings), reference framing |

Before/after use the same camera framing (default neighbourhood view) so the un-mute is
immediately obvious.

## Tests
- Node: `node --test tests/viz_js/*.test.mjs` → **33/33 pass**.
- Python: `pytest tests/test_viz_basemap_raster.py` → **6/6 pass**;
  `pytest tests/ -k viz` → **54/54 pass** (no regressions).
