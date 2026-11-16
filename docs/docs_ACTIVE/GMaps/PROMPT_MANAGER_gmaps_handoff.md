# Manager Handoff & Session Continuity Prompt — OpenUBEM × Google Maps Platform (Opt-In Extensions)

**Date:** 2026-11-13  
**Workspace Root:** `/Users/orcunkoraliseri/Desktop/OpenUBEM`  
**Python Environment:** `/Users/orcunkoraliseri/Desktop/OpenUBEM/.venv/bin/python3` (`Python 3.11.4`, `pytest 9.2.0`, `geopandas 1.1.4`, `rasterio 1.4.1`, `shapely 2.2.0`, `osmnx 1.9.4`, `pvlib 0.16.1`, `pyarrow 26.0.1`, `scipy 1.17.1`, editable `openubem.pth`)  
**Git HEAD at session close:** `27e110685` (`main`; GMaps modules, tests, and `docs/docs_EXPLANATION/` updates are currently uncommitted in the working tree)  
**Target Directory:** `/Users/orcunkoraliseri/Desktop/OpenUBEM/docs/docs_ACTIVE/GMaps/`

---

## START HERE — COPY-PASTE PROMPT FOR NEXT SESSION

> Copy and paste the block below into a fresh coding/manager session opened at `/Users/orcunkoraliseri/Desktop/OpenUBEM`.

```markdown
You are the technical manager continuing the OpenUBEM × Google Maps Platform (GMaps) integration arc.
Workspace root: /Users/orcunkoraliseri/Desktop/OpenUBEM
Python venv: /Users/orcunkoraliseri/Desktop/OpenUBEM/.venv/bin/python3

Read the handoff document before making any edits or running live API calls:
/Users/orcunkoraliseri/Desktop/OpenUBEM/docs/docs_ACTIVE/GMaps/PROMPT_MANAGER_gmaps_handoff.md

Current status as of 2026-11-13:
1. All opt-in, default-OFF Google Maps Platform modules across acquisition, Stage 2 fusion, Stage 6 forecast/air-quality/canopy microclimate, 3D companion web export, CLI scripts, offline test suites, and `docs/docs_EXPLANATION/` updates are implemented on disk.
2. Offline verification passed after final edits: 11 passed in tests/test_gmaps_*.py and 198 passed across 5 existing/updated regression suites (209 total offline tests passed; mocked HTTP + synthetic tmp_path fixtures).
3. Live API execution has NOT been run yet because GOOGLE_MAPS_API_KEY (and BigQuery credentials) were not configured in this environment, and the `<gmp-map-3d>` companion HTML has not yet been tested in a live browser with a key.
4. Protected files (`docs/docs_VALIDATION/`, `openubem/semantic/building_classifier.py`, `openubem/viz/viewer_export.py`, `openubem/viz/basemap_raster.py`, `openubem/data/fixtures/fusion/`) remain untouched, and `FUSION_SOURCES_BY_TARGET` stays `{}` by default.
5. Never run bare `git status` across the whole repo (millions of tracked/simulation files hang it); always pass explicit pathspecs (`git status --porcelain -- <paths>`).

Start by summarizing this state briefly and asking the owner which next milestone to run first:
(A) Live `GOOGLE_MAPS_API_KEY` smoke test on a sample neighbourhood (cache capture + `offline=True` replay),
(B) Accuracy benchmarking of Solar DSM-DEM / Canopy CDSM-TDSM / Places enrichment against existing ground-truth runs,
(C) Live browser verification of `companion_3d_app.html` (`<gmp-map-3d>`) & AI Studio prompt workflow, or
(D) Reviewing and committing the current GMaps changes cleanly.
```

---

## 1. Mission & Design Constraints

This arc integrates relevant Google Maps Platform capabilities (Acquisition, Solar API DSM/DEM/Insights, Places API, BigQuery Geospatial Analytics / Street View & Places Insights scouting, Weather API forecast, Air Quality API ambient context, and Photorealistic 3D Tiles `<gmp-map-3d>` + AI Studio companion) into OpenUBEM **without breaking offline-first scientific reproducibility**.

### Hard Guardrails (Never Violate)
1. **Strictly opt-in, default-OFF:** `openubem/config.py` keeps `FUSION_SOURCES_BY_TARGET: dict = {}` empty by default. Standard Stage 1–6 runs with no overrides must produce unchanged behavior.
2. **Never auto-run or commit credentials:** Keys load at runtime via `resolve_gmaps_api_key` (`api_key` arg -> `GOOGLE_MAPS_API_KEY` env -> `.env`), and `build_cache_key` excludes API keys/credentials from SHA-256 disk cache keys. Never hardcode keys in source, artifacts, or tests.
3. **Report-only separation (`assert_no_eui_columns`):** Validation benchmarks and measured disclosure data never contaminate simulation inputs.
4. **Honest provenance & no overclaiming:**
   - Solar height fusion stamps `FUSED_GMAPSSOLAR_HIGH` only with true DEM subtraction; morphological nDSM fallback or derived `levels` uses `MED`.
   - Places enrichment excludes `CLOSED_PERMANENTLY`, uses spatial containment (`FUSED_GMAPSPLACES_HIGH`) or 10 m nearest-footprint fallback (`MED`) with energy-intensity tie-breaking, and **never overwrites observed OSM classes/tags**.
   - Street View Insights fusion stamps `FUSED_GMAPSSVI_MED`.
   - Ambient AQI attachment uses `GMAPS_AIR_QUALITY_AMBIENT_NOT_DISPERSED` — it is **macro-scale regional ambient context, NOT street-canyon pollutant dispersion** (which remains unbuilt).
5. **Protected / frozen paths (do not modify unless explicitly instructed by owner):**
   - `docs/docs_VALIDATION/` (output helpers `_default_output_dir` / `resolve_companion_output_dir` must redirect outputs out of frozen validation dirs)
   - `openubem/semantic/building_classifier.py`
   - `openubem/viz/viewer_export.py` and `openubem/viz/basemap_raster.py`
   - `openubem/data/fixtures/fusion/`
6. **Git performance rule:** Never run bare `git status` or `git diff` across the repo root. Always scope commands: `git status --porcelain -- openubem/ scripts/ tests/ docs/docs_EXPLANATION/ docs/docs_ACTIVE/GMaps/`.

---

## 2. Implemented Architecture & Inventory (Verified on Disk)

### A. Configuration & Core HTTP Client
- [openubem/config.py](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/config.py): Added default-OFF settings (`GMAPS_CACHE_DIR` / `OPENUBEM_GMAPS_CACHE`, `GMAPS_TIMEOUT_S` / `OPENUBEM_GMAPS_TIMEOUT_S`, `FUSION_GMAPS_SOLAR_NDSM_PATH`, `FUSION_GMAPS_SOLAR_DSM_PATH`, `FUSION_GMAPS_SOLAR_DEM_PATH`, `FUSION_GMAPS_PLACES_PATH`, `FUSION_GMAPS_SVI_PATH`, `FUSION_GMAPS_SVI_FIELDS`); `FUSION_SOURCES_BY_TARGET` remains `{}`.
- [openubem/acquisition/gmaps_client.py](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/acquisition/gmaps_client.py): `GmapsHttpClient`, `resolve_gmaps_api_key`, `build_cache_key`, `GmapsAuthError`, `GmapsOfflineError`, `download_binary`, `assert_no_eui_columns`.

### B. Data Acquisition & BigQuery Scouting
- [openubem/acquisition/gmaps_solar_fetcher.py](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/acquisition/gmaps_solar_fetcher.py): `derive_ndsm_from_solar_dsm` (DEM subtraction + morphological `minimum_filter` fallback), `extract_canopy_cdsm_tdsm` (`crown_depth_fraction=0.6`), `parse_building_insights`.
- [openubem/acquisition/gmaps_places_fetcher.py](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/acquisition/gmaps_places_fetcher.py): `parse_places_response` (filters `CLOSED_PERMANENTLY`).
- [openubem/acquisition/gmaps_bigquery_scout.py](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/acquisition/gmaps_bigquery_scout.py): Strict table-ID validation + `@param`-parameterized BigQuery queries (`execute_parameterized_bq_query`), `summarize_places_insights_df` (`high_process_load_alert`), and `summarize_svi_df`.

### C. Stage 2 Semantic Fusion
- [openubem/semantic/gmaps_fusion.py](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/semantic/gmaps_fusion.py): `GmapsSolarSource`, `GmapsPlacesSource`, `StreetViewInsightsSource` (`gmaps_solar`, `gmaps_places`, `gmaps_svi`), `enrich_buildings_with_solar_insights` (`roof_shape` updates when pitch `> 5°`), `enrich_buildings_with_gmaps_places`.
- [openubem/semantic/fusion.py](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/semantic/fusion.py): Imports `gmaps_fusion` at module bottom to register sources without changing default fusion cascades.

### D. Stage 6 Microclimate Forecast, Canopy & Ambient AQI
- [openubem/microclimate/gmaps_weather.py](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/gmaps_weather.py): `fetch_hourly_weather_forecast` (up to 240 h, `nextPageToken` pagination, local-time shift via `displayDateTime.utcOffset`), `convert_wind_speed_to_ms`, `estimate_irradiance_from_cloud_cover`.
- [openubem/microclimate/gmaps_air_quality.py](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/gmaps_air_quality.py): `parse_air_quality_response`, `fetch_ambient_air_quality`, `attach_ambient_air_quality` (`GMAPS_AIR_QUALITY_AMBIENT_NOT_DISPERSED`).
- [openubem/microclimate/window.py](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/window.py): Added `mode="forecast"` support in `select_window`, including `AnnualEnergyPlusWindowRefusedError` guard when `> 240 h` and `wall_temp_tier="energyplus"`.
- [openubem/microclimate/__init__.py](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/microclimate/__init__.py): Added optional `weather_df_override`, `weather_location_override`, `air_quality_context`, and `06_mc_risk_alerts.json` emission in `run_step6()`.
- [scripts/run_step6_gmaps_forecast.py](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/scripts/run_step6_gmaps_forecast.py): Opt-in CLI (`--run-dir`, `--output-dir`, `--buildings-path`, `--hours`, `--weather-json`, `--air-quality-json`, `--with-air-quality`, `--lat`, `--lon`, `--wall-temp-tier`, `--vegetation-tier`, `--wind-tier`, `--res-m`, `--buffer-m`, `--cdsm-path`, `--tdsm-path`, `--dem-path`).

### E. Online 3D Companion & AI Studio Export
- [openubem/viz/gmaps_web_export.py](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/openubem/viz/gmaps_web_export.py): `export_gmaps_companion_bundle` generating `buildings_wgs84.geojson`, `sources_manifest.json`, `companion_3d_app.html` (`<gmp-map-3d>`), and `ai_studio_prompt.md`.
- [scripts/export_gmaps_3d_companion.py](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/scripts/export_gmaps_3d_companion.py): CLI wrapper (`--run-dir`, `--output-dir`, `--buildings-path`).

### F. Explanatory Docs Updated (`docs/docs_EXPLANATION/`)
- [OpenUBEM_inputs_reference.md](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/docs/docs_EXPLANATION/OpenUBEM_inputs_reference.md) (§5.1 + runtime fetch rule)
- [OpenUBEM_imputation_methods.md](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/docs/docs_EXPLANATION/OpenUBEM_imputation_methods.md) (§4.1 `gmaps_solar`, `gmaps_places`, `gmaps_svi`, `gmaps_bigquery_scout.py`)
- [OpenUBEM_outdoor_analysis_reference.md](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/docs/docs_EXPLANATION/OpenUBEM_outdoor_analysis_reference.md) (§3.3, §3.6, §6)
- [OpenUBEM_fundamentals.md](file:///Users/orcunkoraliseri/Desktop/OpenUBEM/docs/docs_EXPLANATION/OpenUBEM_fundamentals.md) (§8.6, §11)

---

## 3. Verification Status Snapshot (Last Observed 2026-11-13)

- **New feature offline tests — `11 passed, 28 warnings in 4.90s`:**
  - `/Users/orcunkoraliseri/Desktop/OpenUBEM/.venv/bin/pytest -v tests/test_gmaps_client_and_scout.py tests/test_gmaps_fusion_and_enrichment.py tests/test_gmaps_stage6_and_companion.py`
- **Existing/updated regression suites — `198 passed, 40 warnings in 7.78s`:**
  - `/Users/orcunkoraliseri/Desktop/OpenUBEM/.venv/bin/pytest -q tests/test_fusion.py tests/test_fusion_license_guard.py tests/test_microclimate_window.py tests/test_building_classifier.py tests/test_microclimate_step6.py`
- **Gaps not yet executed:**
  1. No live Google Maps API calls (`solar.googleapis.com`, `places.googleapis.com`, `weather.googleapis.com`, `airquality.googleapis.com`) — blocked on missing `GOOGLE_MAPS_API_KEY`.
  2. No live Google BigQuery execution (`gmaps_bigquery_scout.py`) — requires GCP project/credentials and `google-cloud-bigquery` runtime check.
  3. No live browser test of `companion_3d_app.html` (`<gmp-map-3d>`) with a browser-restricted Maps JS key.
  4. Full Stage 1–5 end-to-end tests outside the 5 regression files above were not run in this session.

---

## 4. Recommended Continuation Backlog (In Priority Order)

1. **Live API Key Smoke Test & Offline Cache Freeze**
   - Ask owner to configure `GOOGLE_MAPS_API_KEY` (and confirm billing/quota limits).
   - Pick one small already-completed neighbourhood run under `openubem/outputs/` (never write into `docs/docs_VALIDATION/`), run a tiny live fetch (`--hours 24 --with-air-quality`), inspect responses cached under `GMAPS_CACHE_DIR` (`~/.openubem/gmaps`), then re-run via `offline=True` / saved `--weather-json` & `--air-quality-json` to verify deterministic replay.
2. **Stage 2 / Stage 6 Quantitative Evaluation (Report-Only)**
   - Measure height RMSE / coverage when opting into `gmaps_solar` vs existing OSM/LiDAR ground truth, check Places use-type enrichment recall/precision against observed OSM tags, and inspect Solar-derived `CDSM`/`TDSM` (`extract_canopy_cdsm_tdsm`) inside Stage 6 UTCI runs.
3. **3D Companion Web & AI Studio Verification**
   - Run `scripts/export_gmaps_3d_companion.py --run-dir <sample_run>` -> load `companion_3d_app.html` via local HTTP server in browser -> enter restricted browser Maps API key -> verify extruded polygons, UTCI/AQI/solar tooltips, and `ai_studio_prompt.md` UX.
4. **Geospatial Analytics Playground / BigQuery Scouting Trial**
   - If the owner uses Google Cloud / Geospatial Analytics Playground, run parameterized Places Insights & Street View Insights queries via `gmaps_bigquery_scout.py` and validate district `high_process_load_alert` and `gmaps_svi` outputs.
5. **Repository Cleanliness & Commit**
   - Review `docs/docs_EXPLANATION/` links, `openubem/`, `scripts/`, `tests/`, and this handoff file with the owner before staging a scoped git commit (avoid adding large cache/output binaries).
