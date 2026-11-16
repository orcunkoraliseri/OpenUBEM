# Manager Handoff & Session Continuity Prompt — OpenUBEM × GeoLibre (Opt-In GIS Workspace)

**Date:** 2026-11-16  
**Workspace Root:** `/Users/orcunkoraliseri/Desktop/OpenUBEM`  
**Python Environment:** `/Users/orcunkoraliseri/Desktop/OpenUBEM/.venv/bin/python3` (`Python 3.11.4`, `geolibre 3.8.0`, `pytest 9.2.0`, `geopandas 1.1.4`, `shapely 2.2.0`, `osmnx 1.9.4`)  
**Target Directory:** `/Users/orcunkoraliseri/Desktop/OpenUBEM/docs/docs_ACTIVE/GeoLibre/`

---

## START HERE — COPY-PASTE PROMPT FOR NEXT SESSION

> Copy and paste the block below into a fresh coding/manager session opened at `/Users/orcunkoraliseri/Desktop/OpenUBEM`.

```markdown
You are the technical manager continuing the OpenUBEM × GeoLibre integration.
Workspace root: /Users/orcunkoraliseri/Desktop/OpenUBEM
Python venv: /Users/orcunkoraliseri/Desktop/OpenUBEM/.venv/bin/python3

Read the handoff and implementation docs before editing:
- /Users/orcunkoraliseri/Desktop/OpenUBEM/docs/docs_ACTIVE/GeoLibre/PROMPT_MANAGER_geolibre_handoff.md
- /Users/orcunkoraliseri/Desktop/OpenUBEM/docs/docs_ACTIVE/GeoLibre/README_geolibre_implementation.md

Current status as of 2026-11-16 (Session Close):
1. Optional dependency `geolibre >= 3.8; python_version >= '3.11'` is wired under `[project.optional-dependencies]` in `pyproject.toml` and installed (`geolibre 3.8.0`) in `.venv`.
2. Implemented `openubem/viz/geolibre_export.py`, `scripts/export_geolibre_project.py`, `tests/test_geolibre_export.py`, and documentation across `docs/docs_ACTIVE/GeoLibre/`, `docs/docs_EXPLANATION/`, and `README.md`.
3. Wired dual-viewer generation into the neighbourhood pipeline: `openubem/results/__init__.py` (`aggregate_results(..., export_html=True, export_geolibre=None)`), `scripts/generate_eu_3d_viewers.py`, and `scripts/update_eu_outputs_3d.py` (`--no-geolibre` opt-out) now emit both the existing 3D viewer and the GeoLibre bundle together.
4. Generated GeoLibre previews for all 10 showcase districts under `openubem/outputs/geolibre_companion/<SITE>/` (`ES-MAD-BERRUGUETE`, `FR-LYO-HAUTCOEURPENTES`, `GB-LDN-STDUNSTANS`, `IT-BOL-GALVANI2`, `AT-VIE-RUDOLFSHEIM`, `FI-HEL-KALLIO`, `HU-BUD-ERZSEBETVAROS`, `AM-EVN-NORNORK`, `CA-MTL-PLATEAU`, and internal-licence `ZA-CPT-WOODSTOCK`).
5. Verification passed: 69 passed in 16.92s across `tests/test_geolibre_export.py`, `tests/test_results_aggregator.py`, `tests/test_gmaps_stage6_and_companion.py`, `tests/test_viz_attribute_binding.py`, `tests/test_viz_cityjson_emitter.py`, and `tests/test_viz_context_features.py`.
6. Protected files (`docs/docs_VALIDATION/`, `openubem/semantic/building_classifier.py`, `openubem/viz/viewer_export.py`, `openubem/viz/basemap_raster.py`, `openubem/data/fixtures/fusion/`) remain untouched. Changes are currently uncommitted in the working tree.
7. Never run bare `git status` across the whole repo; always pass explicit pathspecs (`git status --porcelain -- <paths>`).

Ask the owner which follow-up milestone to prioritize next:
(A) Live browser verification of `openubem/outputs/geolibre_companion/<SITE>/geolibre_viewer.html` or `.geolibre.json` in `geolibre.app`,
(B) Interactive Jupyter notebook walkthrough in `notebooks/` using `create_geolibre_map`,
(C) Optional Stage 6 UTCI GeoTIFF / COG raster layer attachment in `.geolibre.json`, or
(D) Reviewing and committing the GeoLibre integration cleanly.
```

---

## 1. Mission & Design Constraints

Integrates GeoLibre (`opengeos/GeoLibre`, MIT) into OpenUBEM as an opt-in interactive GIS companion and dual-viewer pipeline target without disturbing core physics simulation or deterministic offline viewer guarantees.

### Hard Guardrails (Never Violate)
1. **Optional dependency only:** Keep `[project] dependencies` in `pyproject.toml` free of `geolibre` / `anywidget` so headless CLI and SLURM cluster environments stay lean and Python 3.10+ remains supported.
2. **Read-only stage inputs & validation protection:** Never modify `docs/docs_VALIDATION/`. `resolve_geolibre_output_dir` redirects `docs_VALIDATION/` source runs to `openubem/outputs/geolibre_companion/<cell>` and raises `ValueError` on explicit `docs_VALIDATION/` output targets.
3. **Honest provenance & caveats:** Never overwrite raw `height_m` or `provenance_*` (display extrusion uses a dedicated `extrusion_height_m` column). Always attach Stage 6 unvalidated-UTCI and macro-scale `GMAPS_AIR_QUALITY_AMBIENT_NOT_DISPERSED` caveats to layer `descriptiveMetadata.abstract` and `sources_manifest.json`.
4. **Strict JSON & credential redaction:** Sanitize all `NaN`/`Inf`/`pd.NA` values to `None` before serializing (`allow_nan=False`), and pass generated projects through `geolibre.project.redact_credentials`.
5. **Licensing respect:** `ZA-CPT-WOODSTOCK` footprints/results carry internal-only licence restrictions in `README.md`; keep its generated GeoLibre outputs local/internal only.
6. **Protected paths untouched:** `docs/docs_VALIDATION/`, `openubem/semantic/building_classifier.py`, `openubem/viz/viewer_export.py`, `openubem/viz/basemap_raster.py`, `openubem/data/fixtures/fusion/`.
7. **Git performance rule:** Never run bare `git status` across the repo root; always pass explicit pathspecs.

---

## 2. Implemented Inventory

- [pyproject.toml](../../../pyproject.toml): Added `[project.optional-dependencies] -> geolibre`.
- [openubem/viz/geolibre_export.py](../../../openubem/viz/geolibre_export.py): `has_geolibre`, `resolve_geolibre_output_dir`, `load_openubem_buildings_for_geolibre`, `select_active_metric`, `build_geolibre_project`, `export_geolibre_bundle`, `create_geolibre_map` (supporting both EU-11/EU-22 `eui_heating_kwh_m2` and Step-5 `05_results.gpkg` `heating_eui_kwh_m2` / `total_eui_kwh_m2` / `gwp_total_kgco2_m2` / `iod` schemas, plus pure-Python fallback emitter when `geolibre` is absent).
- [openubem/results/__init__.py](../../../openubem/results/__init__.py): Added `export_geolibre: bool | None = None` to `aggregate_results`; enabling `export_html=True` (`OPENUBEM_EXPORT_HTML=1`) now generates both `export_viewer` and `export_geolibre_bundle(output_dir)` non-fatally.
- [scripts/export_geolibre_project.py](../../../scripts/export_geolibre_project.py): Standalone CLI entrypoint (`--run-dir`, `--output-dir`, `--buildings-path`, `--results-csv`, `--district`, `--color-by`, `--colormap`, `--basemap`, `--scheme`, `--class-count`, `--no-extrude`, `--no-story-map`).
- [scripts/generate_eu_3d_viewers.py](../../../scripts/generate_eu_3d_viewers.py) & [scripts/update_eu_outputs_3d.py](../../../scripts/update_eu_outputs_3d.py): Updated `build_district` and `update_district_viewer` to also build and mirror `eu_<DISTRICT>_geolibre/` alongside `eu_<DISTRICT>_viewer.html` (with `--no-geolibre` opt-out).
- [tests/test_geolibre_export.py](../../../tests/test_geolibre_export.py): 6 tests covering constant-height Stage 1/2 resilience, Stage 5 CSV join + `NaN` sanitization + `geolibre.load_project` round-trip, Stage 6 UTCI + context + caveats, `create_geolibre_map` widget creation, CLI + `docs_VALIDATION` guard, and `aggregate_results` dual-viewer emission / `export_geolibre=False` opt-out.
- [docs/docs_ACTIVE/GeoLibre/README_geolibre_implementation.md](README_geolibre_implementation.md): Technical implementation reference & Madrid verification record.
- [docs/docs_EXPLANATION/OpenUBEM_geolibre_integration.md](../../docs_EXPLANATION/OpenUBEM_geolibre_integration.md) and [docs/docs_EXPLANATION/OpenUBEM_fundamentals.md](../../docs_EXPLANATION/OpenUBEM_fundamentals.md): Explanatory guide & §8.7 fundamentals integration.
- [README.md](../../../README.md): Quickstart section & Documentation Map links.

---

## 3. Verification Snapshot (2026-11-16 Session Close)

- **Pytest verification (`69 passed, 15 warnings in 16.92s`):**
  `/Users/orcunkoraliseri/Desktop/OpenUBEM/.venv/bin/pytest -v tests/test_geolibre_export.py tests/test_results_aggregator.py tests/test_gmaps_stage6_and_companion.py tests/test_viz_attribute_binding.py tests/test_viz_cityjson_emitter.py tests/test_viz_context_features.py`
  *(Note: `test_aggregate_results_exports_both_viewers` monkeypatches `openubem.viz.viewer_export.export_viewer` to avoid requiring IDF files while exercising real `aggregate_results` + `export_geolibre_bundle` against `tests/fixtures/golden_sql/`.)*
- **All 10 Showcase District Previews Generated (`openubem/outputs/geolibre_companion/<SITE>/`):**
  - `ES-MAD-BERRUGUETE`: 1,194 footprints (1,119 with `eui_heating_kwh_m2`)
  - `FR-LYO-HAUTCOEURPENTES`: 530 (501)
  - `GB-LDN-STDUNSTANS`: 1,242 (1,215)
  - `IT-BOL-GALVANI2`: 1,220 (1,035)
  - `AT-VIE-RUDOLFSHEIM`: 536 (517)
  - `FI-HEL-KALLIO`: 588 (542)
  - `HU-BUD-ERZSEBETVAROS`: 805 (757)
  - `AM-EVN-NORNORK`: 551 (535)
  - `CA-MTL-PLATEAU`: 725 (701)
  - `ZA-CPT-WOODSTOCK` *(internal licence)*: 534 (524)
- **Style & Syntax Gates:** `<= 88`-char line length, type hints, and Google-style docstrings verified via AST check on `geolibre_export.py`, `export_geolibre_project.py`, and `test_geolibre_export.py`; `ast.parse` verified on `openubem/results/__init__.py`, `generate_eu_3d_viewers.py`, and `update_eu_outputs_3d.py`.
- **Gaps not yet executed:** Live browser rendering of `geolibre_viewer.html` / `.geolibre.json` in `geolibre.app`, live JupyterLab widget rendering of `create_geolibre_map`, and end-to-end execution of `generate_eu_3d_viewers.py` / `update_eu_outputs_3d.py` after adding the GeoLibre hook.

---

## 4. Recommended Future Backlog

1. **Live Browser & Jupyter Verification:** Open one of the generated `geolibre_viewer.html` files (e.g., `ES-MAD-BERRUGUETE/geolibre_viewer.html`) in a browser and verify 3D extrusions, DuckDB-WASM SQL, and Story Map camera transitions, plus `create_geolibre_map` in JupyterLab.
2. **Interactive Notebook Template (`notebooks/`):** Add an example Jupyter notebook demonstrating `create_geolibre_map`, interactive layer restyling, and reading back drawn ROIs (`m.user_rois()`).
3. **Stage 6 Raster / COG Overlay Support:** Optionally attach `06_mc_utci_*.tif` layers via local HTTP/COG or classified PNG bounds inside `.geolibre.json` alongside `06_mc_summary.gpkg`.
4. **Git Review & Commit:** Review uncommitted GeoLibre (and GMaps) changes with scoped `git diff` and commit cleanly.
