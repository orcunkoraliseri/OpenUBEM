# RESULT V05 - Attribute Binding & Data Schema
## Deep-Research Answer: how OpenUBEM attributes attach to geometry and reach the browser

> Prompt answered: `V05_attribute_binding_data_schema_prompt.md`
> Date: 2026-07-02
> Scope guard honoured: this document decides the binding mechanism and schema only. It does not re-open geometry format choice (`V03`) or thematic colouring (`V09`).

---

## Table 1 - Attribute inventory

| Attribute | OpenUBEM source (file/field) or "NOT AVAILABLE - needs source" | Data type | Granularity (per-building / per-surface / per-zone) | Temporal (static / annual / 8760-hourly) | Source |
|---|---|---|---|---|---|
| Function / archetype (DOE prototype name) | `openubem/semantic/building_classifier.py::archetype_id` from `building_tag` + `function_tag` | categorical string | per-building | static | `README.md` Step 2.0; `openubem/semantic/building_classifier.py` |
| Vintage / `year_built` | `openubem/acquisition/osm_fetcher.py::year_built` (from OSM `start_date`; can be imputed through vintage resolution) | integer / nullable integer | per-building | static | `README.md` tag flattening; `openubem/acquisition/osm_fetcher.py`; `openubem/semantic/imputation.py` |
| Number of floors / footprint area | `levels` (OSM `building:levels`) / `footprint_area_m2`; downstream `num_floors` in the IDF build | integer / float | per-building | static | `README.md` Step 1 tag flattening; `openubem/acquisition/osm_fetcher.py`; `openubem/idf/builder.py` |
| Population (per building) | `NOT AVAILABLE - needs source (see Table 3)` | integer / float | per-building | static | New dependency; no current OpenUBEM field |
| Annual EUI (kWh/m2/yr) | `openubem/results/parser.py::total_eui_kwh_m2`; optional reconstructed `openubem/results/service_loads.py::total_eui_reconstructed_kwh_m2` | float | per-building | annual | `openubem/results/parser.py`; `README.md` Step 5I; `openubem/results/service_loads.py` |
| Per-building end-uses | `heating_eui_kwh_m2`, `cooling_eui_kwh_m2`, `lighting_eui_kwh_m2`, `equipment_eui_kwh_m2`, `fans_eui_kwh_m2`; reconstructed additions `vent_fans_eui_recon_kwh_m2`, `pumps_eui_recon_kwh_m2`, `swh_dhw_eui_recon_kwh_m2`, `refrig_eui_recon_kwh_m2`, `cooking_other_eui_recon_kwh_m2` | float(s) | per-building | annual | `openubem/results/parser.py`; `openubem/results/service_loads.py`; `README.md` Step 5E / 5I |
| Carbon | `gwp_heating_kgco2_m2`, `gwp_cooling_kgco2_m2`, `gwp_lighting_kgco2_m2`, `gwp_equipment_kgco2_m2`, `gwp_total_kgco2_m2` | float | per-building | annual | `openubem/results/carbon.py`; `README.md` Step 5E |
| Hourly demand (8760) | `eplusout.sql` / `eplusout.csv` parsed by `openubem/results/parser.py::parse_building_sql` and `parse_building_csv`; hourly variables are declared in `openubem/idf/outputs.py::STANDARD_OUTPUTS` | time series float | per-building, with zone-granular source rows | 8760-hourly | `openubem/idf/outputs.py`; `openubem/results/parser.py`; `README.md` Step 5B / 5D |
| Per-surface solar irradiance / other per-surface EnergyPlus output | `NOT AVAILABLE - needs source` | float | per-surface | 8760-hourly or annual | `openubem/idf/outputs.py` does not emit a surface-irradiance variable today |
| Resolution mode (`building`/`floor`/`zone`/`auto`) | `openubem/idf/builder.py::resolution_mode`; zoning choice from `openubem/geometry/zoning.py::decide_zoning_strategy` | enum string | per-building | static | `openubem/idf/builder.py`; `openubem/geometry/zoning.py`; `tests/test_step3_orchestrator.py` |
| Imputed/low-confidence flag on any input | `data_quality_flag` plus field-level `provenance_*` and `confidence_*` columns; lineage summary `imputed_fields_count` and `mean_imputation_confidence` | string + tier fields | per-building / per-field | static | `openubem/semantic/provenance.py`; `openubem/semantic/imputation.py`; `openubem/semantic/spatial_impute.py`; `openubem/semantic/building_classifier.py`; `openubem/acquisition/osm_fetcher.py` |

---

## Table 2 - Binding mechanism per format

| Format (from `V03`) | How it carries per-feature metadata | Supports per-surface (sub-mesh) granularity, not just per-object? | Query/lookup pattern in the browser | Source |
|---|---|---|---|---|
| glTF 2.0 (+ `EXT_mesh_features`/`EXT_structural_metadata`) | Attach feature IDs to mesh primitives using `_FEATURE_ID_n` vertex attributes, texture channels, or index-based IDs; attach metadata through `EXT_structural_metadata` property tables keyed by feature ID. | Yes, if each surface/sub-surface is its own feature ID or primitive. | Pick a rendered primitive, resolve feature ID, read the matching property-table row, then filter/style in the viewer. | [glTF 2.0 spec](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html) `sec. 3.7.2`, `sec. 3.12`, `sec. 5.19.4`; [EXT_mesh_features README](https://github.com/CesiumGS/glTF/tree/3d-tiles-next/extensions/2.0/Vendor/EXT_mesh_features) lines 286-303; [EXT_structural_metadata README](https://github.com/CesiumGS/glTF/tree/3d-tiles-next/extensions/2.0/Vendor/EXT_structural_metadata) |
| 3D Tiles (batch table / structural metadata) | 1.0 batch tables key metadata by per-tile batch IDs; 1.1 moves to structured metadata attached to tilesets, tiles, tile content, and tile content groups, with GLB content carrying the actual geometry. | Yes, but only if the tile content itself preserves per-surface feature IDs; the tileset hierarchy is tile-granular, not surface-aware by itself. | Select a tile or feature in the Cesium-style scene graph, then resolve the row in the batch table / structured metadata payload. | [CesiumGS/3d-tiles README](https://github.com/CesiumGS/3d-tiles) lines 278-316; 3D Tiles 1.1 release notes in same README |
| CityJSON (attribute dictionaries) | Store per-building attributes directly in `CityObjects[id].attributes`; use `geometry[].lod` plus semantic surface lists for surface-level binding. Stable object IDs can be the OpenUBEM building ID / `osm_id`. | Yes, natively. Surfaces, sub-surfaces, and LODs are first-class CityJSON concepts. | Load object by ID, then read its `attributes` or the semantic-surface entry for the selected surface. | [cityjson/specs repo](https://github.com/cityjson/specs) and [CityJSON paper](https://doi.org/10.1186/s40965-019-0064-0) |
| Extruded GeoJSON (`properties`) | Use feature-level `properties`; the geometry is a 2D footprint plus height/extrusion only. | No. It cannot represent distinct surfaces or openings faithfully. | Filter or style by feature `properties`; no sub-surface lookup exists. | [RFC 7946](https://www.rfc-editor.org/rfc/rfc7946) and [MapLibre fill-extrusion docs](https://maplibre.org/maplibre-style-spec/layers/#fill-extrusion) |

---

## Table 3 - Population sourcing options

| Option | Method | Granularity achievable (per-building?) | Accuracy/caveats | Licence/cost | Verdict |
|---|---|---|---|---|---|
| Census block/tract disaggregation | Dasymetric / areal interpolation from coarse census counts onto building footprints or parcels, optionally weighted by land-use or building area. See [Boo et al. 2021](https://arxiv.org/abs/2106.07461) and [Metzger et al. 2022](https://arxiv.org/abs/2211.04039). | Yes, if footprints/parcels exist; otherwise grid/parcel level. | Best portable method, but still an estimate. Sensitive to ancillary-data quality and to MAUP / boundary choice. | Census counts are usually free; footprint / parcel layers vary by city and licence. | Preferred default when a census source exists; still imputed, not observed. |
| OSM `building:levels` + footprint-area occupancy heuristic | Estimate floors from `building:levels`, multiply by footprint area, then apply an occupancy-density assumption. OSM metadata and building height proxies are supported by [Li et al. 2023](https://arxiv.org/abs/2307.02574), [Singla 2024](https://arxiv.org/abs/2411.04612), and OSM building-type coverage work in [Arruda et al. 2024](https://arxiv.org/abs/2409.05692). | Yes, per-building. | Cheapest and most portable, but the weakest statistically: `building:levels` coverage is sparse, mixed-use buildings break the heuristic, and occupancy density varies sharply by use class and city. | Free OSM / ODbL, no licence cost. | Fallback only; acceptable for rough ranking, not for asserting true population. |
| Dwelling-unit count from residential DOE archetype occupancy assumptions | For residential archetypes, infer dwelling units or occupants from DOE/OpenStudio prototype occupancy assumptions and multiply by unit count or resident-per-unit defaults. OpenUBEM already bundles DOE prototype schedules and loads for the archetype pipeline. | Yes, but only for residential archetypes. | More defensible than a pure area heuristic for prototype-style residential stock, but it is still model-assumed occupancy, not observed population. Poor fit for commercial / mixed-use / non-residential buildings. | Free; based on bundled DOE/OpenStudio prototype libraries and OpenUBEM internal defaults. | Use only as a coarse residential fallback when census-style allocation is unavailable. |
| Other (national statistics agency building-level datasets, if any exist for OpenUBEM's cities) | City assessor / cadastral / parcel / unit registers where a municipality publishes building-level unit counts or occupants directly. Examples are city-specific rather than cross-city, and there is no single harmonized source across NYC / LA / Boston / Torino-style cells. | Sometimes yes, but only where a city publishes it. | Accuracy can be high when the register is authoritative, but coverage and schema differ by city, and many sources do not expose population directly. | Mixed: municipal open data is often free; cadastral access may be restricted or paid. | Opportunistic augmentation only. Not a stable cross-city population strategy. |

---

## Table 4 - Fit to constraints, including provenance

| Question | Answer + source |
|---|---|
| Which binding mechanism keeps attributes exactly traceable to their source file/field, with no derived/interpolated values presented as real? | **CityJSON** is the cleanest traceable binding because the source field names can live directly in `CityObjects[id].attributes`, and the geometry stays as the original polygon list instead of being triangulated into a separate render-only representation. Use `osm_id` / building ID as the stable object key and store the raw OpenUBEM field names unchanged. |
| How does an imputed or low-confidence input travel with its attribute through the chosen binding mechanism? | Keep a field-level `provenance_<field>` sibling plus a `confidence_<field>` sibling when a value is filled, and keep row-level `data_quality_flag` for aggregate audit tokens. OpenUBEM already implements the token grammar in `openubem/semantic/provenance.py` (`{METHOD}_{SOURCE}_{TIER}`) and the append-only flag path in `openubem/semantic/spatial_impute.py`. Add `imputed_fields_count` and `mean_imputation_confidence` as optional summary columns. |
| Is the chosen mechanism producible deterministically from Python with no proprietary tooling? | Yes. CityJSON can be emitted with stdlib `json` or `cjio`, and the provenance layer is already pure Python. No paid converter or proprietary exporter is required. |
| What is the concrete schema-versioning story if the pipeline adds a new output field later? | Add the new field as a new key in `attributes` or a new semantic property, and bump a top-level schema version / hash. Existing object IDs and geometry do not need to change, but the CityJSON asset should be re-exported so the browser bundle sees the new field. In other words: schema extension is additive; geometry re-export is still the authoritative build step. |

---

## Part C - Synthesis (the attribute schema decision)

### 1. Concrete binding mechanism

OpenUBEM should bind attributes through **CityJSON** as the authoritative interchange format, using:

- `CityObjects[<osm_id>].attributes` for per-building attributes.
- `CityObjects[<osm_id>].geometry[*].lod` to separate the neighbourhood mass view from the building-detail view.
- CityJSON semantic surfaces for per-surface and sub-surface data.
- `provenance_<field>` and `confidence_<field>` siblings for any imputed or low-confidence field.
- `data_quality_flag` as the row-level audit string, with `|`-separated tokens.

That keeps the source-to-scene mapping direct: field name -> CityJSON attribute key -> browser lookup by building ID. It also matches the `V03` decision that CityJSON is the primary interchange format.

### 2. Population verdict

**Verdict: no direct population field today. Omit population until a source exists, and treat it as a new dependency.**

If the viewer needs a placeholder before a better source is available, the least-bad portable fallback is census disaggregation. The OSM heuristic is weaker, and the DOE dwelling-unit assumption is only defensible for residential archetypes. I would not silently synthesize a "real" population column from the current OpenUBEM pipeline.

### 3. Provenance-flag design

Use a two-layer design:

- Field-level: `provenance_<field>` plus `confidence_<field>`.
- Row-level: `data_quality_flag` with append-only tokens from `openubem/semantic/provenance.py`.

Recommended tokens and conventions:

- Observed or untouched values stay unflagged in `provenance_*`.
- Imputed values carry a provenance token such as `HOTDECK_NEIGHBOR_HIGH`, `GROUPMODE_MED`, or `DEFAULT_ASHRAE901_LOW`.
- Spatially blocked rows carry `SPATIAL_CLUSTER_MNAR_BLOCKED`.
- The summary layer can expose `imputed_fields_count` and `mean_imputation_confidence` for UI badges and filtering.

This is enough for `V14` to surface confidence honestly without polluting the geometry schema.

### 4. GAP list

- `Population (per building)` - no defensible current source in OpenUBEM.
- `Per-surface solar irradiance / other per-surface EnergyPlus output` - not emitted by the current output configuration; would require new `Output:Variable` wiring and parser support.

---

## Confidence and caveats

- **Least evidenced portable population option for NYC / LA / Boston / Torino-style cells:** the **OSM `building:levels` + footprint-area heuristic**. OSM coverage is uneven, mixed-use stock breaks the occupancy assumption, and the result is only a proxy.
- **Best portable default:** census disaggregation, if a census product and a plausible ancillary layer are available.
- **Most defensible residential fallback when census data is missing:** DOE/prototype dwelling-unit assumptions, but only for residential archetypes.
- **Least portable overall:** city-specific assessor / cadastre datasets, because they are not harmonized across the four city families and may not expose population at all.

---

## Reference list

1. **Khronos Group.** *glTF 2.0 Specification*, version 2.0.1. Published 2021-10-11. https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html

2. **CesiumGS / Khronos.** *EXT_mesh_features* README in the glTF 3d-tiles-next branch. Accessed 2026-07-02. https://github.com/CesiumGS/glTF/tree/3d-tiles-next/extensions/2.0/Vendor/EXT_mesh_features

3. **CesiumGS / Khronos.** *EXT_structural_metadata* README in the glTF 3d-tiles-next branch. Accessed 2026-07-02. https://github.com/CesiumGS/glTF/tree/3d-tiles-next/extensions/2.0/Vendor/EXT_structural_metadata

4. **CesiumGS.** *CesiumGS/3d-tiles* repository README and version history. Accessed 2026-07-02. https://github.com/CesiumGS/3d-tiles

5. **cityjson/specs.** CityJSON specifications repository and Bikeshed source. Accessed 2026-07-02. https://github.com/cityjson/specs

6. **Ledoux, H., Arroyo Ohori, K., Kumar, K., Dukai, B., Labetski, A., Vitalis, S.** "CityJSON: a compact and easy-to-use encoding of the CityGML data model." *Open Geospatial Data, Software and Standards* 4(1), 2019. DOI: 10.1186/s40965-019-0064-0

7. **Butler, H., Daly, M., et al.** *RFC 7946: The GeoJSON Format*. IETF, 2016. https://www.rfc-editor.org/rfc/rfc7946

8. **Boo, G., Darin, E., Leasure, D. R., Dooley, C. A., Chamberlain, H. R., Lazar, A. N., Tschirhart, K., Sinai, C., Hoff, N. A., Batumbo, A., Rimoin, A. W., Tatem, A. J.** "High-resolution population estimation using household survey data and building footprints." arXiv, 2021. https://arxiv.org/abs/2106.07461

9. **Metzger, N., Vargas-Munoz, J. E., Daudt, R. C., Kellenberger, B., Ton-That Whelan, T., Ofli, F., Imran, M., Schindler, K., Tuia, D.** "Fine-grained Population Mapping from Coarse Census Counts and Open Geodata." arXiv, 2022. https://arxiv.org/abs/2211.04039

10. **Li, H., Yuan, Z., Dax, G., Kong, G., Fan, H., Zipf, A., Werner, M.** "Semi-supervised Learning from Street-View Images and OpenStreetMap for Automatic Building Height Estimation." arXiv, 2023. https://arxiv.org/abs/2307.02574

11. **Singla, J. G.** "Population estimation using 3D city modelling and Carto2S datasets - A case study." arXiv, 2024. https://arxiv.org/abs/2411.04612

12. **Arruda, H. F. de, Reia, S. M., Ruan, S., Atwal, K. S., Kavak, H., Anderson, T., Pfoser, D.** "Extracting the U.S. building types from OpenStreetMap data." arXiv, 2024. https://arxiv.org/abs/2409.05692

13. **OpenUBEM internal sources.** `README.md`; `openubem/acquisition/osm_fetcher.py`; `openubem/semantic/building_classifier.py`; `openubem/semantic/imputation.py`; `openubem/semantic/provenance.py`; `openubem/semantic/spatial_impute.py`; `openubem/idf/outputs.py`; `openubem/results/parser.py`; `openubem/results/service_loads.py`; `openubem/results/carbon.py`; `openubem/idf/builder.py`; `openubem/geometry/zoning.py`.

*V05 RESULT - OpenUBEM 3D visualization deep-research set. 2026-07-02.*


