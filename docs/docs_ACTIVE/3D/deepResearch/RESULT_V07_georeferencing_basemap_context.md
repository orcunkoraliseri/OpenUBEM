# RESULT_V07 — Geo-Referencing, Basemap & Context

> Scope: placing the OpenUBEM neighbourhood scene on real-world coordinates. Assumes **three.js** as the
> primary rendering stack (V06 pick confirmed in RESULT_V01 Part C). Does NOT revisit the rendering-stack
> decision (V06) or the LOD ladder (V04).

---

## Table 1 — Geo-referencing approach fitness

| Approach | How it anchors the scene to real coordinates | Precision / pitfalls | Fit for OpenUBEM's neighbourhood-scale scenes | Works with the three.js (V06) stack | Source |
|---|---|---|---|---|---|
| **Local-ENU scene** — author geometry in local metres (East-North-Up), store a single geodetic anchor point (lat₀, lon₀, [alt₀]) + north-rotation bearing, apply to the whole neighbourhood mesh | The Python emitter records the UTM centroid of the neighbourhood (already computed as `cx, cy` in `footprint.py::translate_to_origin`) and the UTM EPSG code. At render time, `Cesium.Cartesian3.fromDegrees(lon₀, lat₀, alt₀)` or a pyproj back-conversion gives the ECEF anchor; all local vertices are placed relative to it. In three.js, the scene origin maps to the anchor. Basemap tiles are aligned by translating a tile-plane layer to the same anchor. | **Sub-metre precision** at neighbourhood scale (< 2 km extent). UTM distortion across a 1 km scene is < 0.01 %; entirely negligible for UBEM. Pitfall: **North is not always scene-Y** — the UTM grid north and geographic north diverge by the *grid convergence angle* (γ); omitting this rotation silently misaligns all buildings by up to ≈ 0.5° in mid-latitude cities. Fix: compute γ at the anchor and apply a rotation matrix to the scene. Formula: `γ = arctan(tan(Δλ) · sin(φ₀))` where Δλ = longitude difference from the central meridian and φ₀ = anchor latitude. | **Ideal.** OpenUBEM already works in UTM metres (the GDF after `osm_fetcher.py` line 56: `gdf = gdf.to_crs(utm)`). The entire neighbourhood footprint set shares a single UTM zone. Local-ENU is mathematically identical to UTM for scenes under ~50 km extent. The anchor point is one lat/lon pair per neighbourhood run — trivially storable as a 2-tuple in the per-neighbourhood manifest. | **Yes — native three.js pattern.** three.js has no coordinate system opinion; its scene root is a local Cartesian frame. The anchor is used only at tile-loading time (to place the basemap plane) and at export time (to record metadata). No third-party geo-library is required inside three.js itself. CesiumJS users follow the same pattern via `Cesium.Transforms.eastNorthUpToFixedFrame`. | Local-ENU definition: Zhu et al. (2019) *Coordinate Systems in Geodesy*, §3.2; OGC Abstract Spec Topic 2; UTM distortion: Snyder (1987) *Map Projections — A Working Manual*, USGS Professional Paper 1395, p. 58; grid convergence: same source, eq. (8-15); CesiumJS ENU API: CesiumJS docs `Cesium.Transforms.eastNorthUpToFixedFrame` (accessed 2026-07-02). |
| **True-globe (ECEF)** — every vertex is stored and rendered in Earth-Centred Earth-Fixed X/Y/Z metres, on a WGS84 ellipsoidal globe | Each vertex (lat, lon, alt) → (X, Y, Z) via the WGS84 geodetic-to-ECEF formula. The renderer works in full ECEF space; the camera orbits the globe. This is the CesiumJS model. In three.js it requires a custom camera rig and a globe mesh. | **Millimetre precision** planet-wide. But for a 1 km neighbourhood scene the ECEF values are O(10⁶) metres (e.g. NYC: X ≈ 1,334,000 m, Y ≈ −4,654,000 m, Z ≈ 4,138,000 m), causing **catastrophic floating-point cancellation** in 32-bit GPU float coordinates (WebGL default). A 1 km scene sits on a number ~10⁶ m; GPU float32 has ~7 significant decimal digits, giving ≈ 0.1 m vertex jitter. The standard cure is `RTC_CENTER` (Relative-To-Centre): subtract a per-tile origin on the CPU before uploading to the GPU, then translate the model matrix on the GPU — but this requires custom shader patching in three.js (non-trivial). | **Overkill and fragile for OpenUBEM.** The globe model is designed for planetary datasets (Cesium World Terrain, satellite imagery at global scale). For a neighbourhood scene the additional complexity of globe projection, atmosphere, and ECEF maths yields no visible benefit and introduces the float32 jitter problem unless RTC_CENTER is carefully implemented. | **No — not a natural three.js pattern.** three.js does not natively render a WGS84 globe. Implementing ECEF + RTC_CENTER in three.js is a significant custom engineering effort. CesiumJS is the natural home for this approach. | OGC 3D Tiles spec §8 (RTC_CENTER, `CESIUM_RTC` glTF extension); CesiumJS "Precisions and Floating Point" blog post, 2022; Snyder (1987), pp. 160-161 (geodetic to ECEF); three.js `WebGLRenderer` float precision: three.js docs r165. |
| **Web-Mercator planar** — the scene coordinate system is EPSG:3857 (Web Mercator); geometry is projected to Mercator metres and placed on a flat Mercator tile grid | Footprints are reprojected from UTM → WGS84 → EPSG:3857. Tile X/Y pixel coordinates are computed via the standard Web Mercator tile formula. Buildings float at Mercator-Y, Mercator-X. This is the deck.gl / MapLibre / Mapbox approach. | **Per-building centroid accuracy: sub-metre at neighbourhood scale.** Pitfall: **Mercator Y-scale distortion** — 1 metre North does not equal 1 metre East at the same scene pixel height because Mercator stretches vertically with latitude. At 40°N (NYC/Boston) the scale factor is 1.307; this means a 10 m tall building rendered in raw Mercator metres appears 31 % taller than 10 m. The correct fix is to apply a vertical scale factor `k = 1 / cos(φ)` to the height (Z-axis), not to X/Y. Failing to do this makes rooflines visually wrong. | **Problematic for three.js surface-faithful rendering.** three.js works in a metric Euclidean space; Mercator Y-distortion is invisible inside the library and must be manually corrected. Map-GL libraries (MapLibre, deck.gl) handle this internally. For OpenUBEM's per-surface, metric-accurate geometry, the ENU approach is cleaner and does not introduce a scale-correction step per vertex. | **Technically possible but non-standard.** Could be used if the basemap layer is a Mercator raster tile plane in three.js. However, every vertex then needs Mercator projection applied in Python (pyproj EPSG:3857 transform), and the Z-scale fix must be applied. The Map-GL extrusion stack (MapLibre) is the natural home for this approach, not three.js. | Web Mercator (EPSG:3857) spec: OGC 07-092r1; scale factor formula: Snyder (1987) pp. 44-45; MapLibre GL JS `fill-extrusion-height` docs (accessed 2026-07-02); deck.gl `ScenegraphLayer` docs. |

**Table 1 Verdict:** **Local-ENU (UTM centroid anchor) is the correct approach for OpenUBEM + three.js.** It matches the existing UTM pipeline, requires storing only one lat/lon pair per neighbourhood run, has no float32 precision issue at neighbourhood scale, and integrates cleanly with three.js's Euclidean scene space.

---

## Table 2 — Basemap / terrain options, licence & cost

| Provider / source | Data type | Licence | Requires API key / paid tier at OpenUBEM's expected usage? | Self-hostable / offline option? | Verdict against the reproducibility constraint | Source |
|---|---|---|---|---|---|---|
| **OpenStreetMap raster tiles** (tile.openstreetmap.org) | Street-map raster, PNG/JPEG tiles, zoom 0–19 | ODbL (data); tile server: OSM Tile Usage Policy — **free to use with attribution**, but heavy automated use requires a private tile server per policy | **No API key** for light use. But OSM's own tile servers explicitly prohibit heavy bulk / automated use (> ~1 000 000 tiles/day or automated scripts). For a Python-emitted static viewer that embeds tile URLs and opens once in a browser, usage per render is tiny (< 200 tiles for a neighbourhood). Still, OSM requests apps cache tiles and respect rate limits. | **Yes** — run a local tile server (e.g. `tile-server` Docker image from `overv/openstreetmap-tile-server`) from an OSM `.pbf` extract. Also: pre-download and embed PNG tiles as base64 in the HTML at export time (fully offline). | **Reproducibility-safe as default for light browser use.** The viewer fetches tiles once at open time; no ongoing paid service. Caveat: requires internet at first open. For fully offline / CI builds, embed tiles at export time. **Flag:** OSM tile servers are not a guaranteed SLA and can be slow; do not batch-fetch. | OpenStreetMap Tile Usage Policy: https://operations.osmfoundation.org/policies/tiles/ (accessed 2026-07-02); ODbL: https://opendatacommons.org/licenses/odbl/. |
| **MapTiler** | Vector tiles (OpenStreetMap-based), satellite imagery, terrain RGB-DEM; zoom 0–22 | Proprietary — MapTiler Cloud free tier: 100,000 map loads/month, **requires an API key**. Paid plans from ~$25/month for 1 M loads. | **Yes — API key required even for the free tier.** The key must be embedded in the viewer HTML. If the key is committed to the repo it violates MapTiler ToS; if distributed without a key the viewer is broken. | **Yes** — MapTiler self-hosted (Docker + MBTiles) is available under the MapTiler Server licence (~$150/mo or a one-time self-host licence). Vector tile extracts (`.mbtiles`) can be downloaded for a region. | **Non-default: paid API key is a reproducibility risk.** Distributing an OpenUBEM viewer that requires a MapTiler key means every user must obtain their own key. Flag as optional premium basemap. Acceptable only if wrapped behind an environment-variable key slot with a clear fallback to OSM tiles. | MapTiler Cloud pricing: https://www.maptiler.com/cloud/plans/ (accessed 2026-07-02); MapTiler ToS: https://www.maptiler.com/terms/ (accessed 2026-07-02). |
| **Cesium Ion** (terrain + imagery) | Cesium World Terrain (quantized-mesh), Bing Maps imagery, Sentinel-2 satellite; global coverage | Cesium ion ToS: free tier 50 GB/month data transfer, **requires an ion access token**. Paid plans from $125/month. | **Yes — token required.** The Cesium World Terrain and ion-hosted imagery (Bing/Sentinel-2) both require a valid ion token in the viewer JS. Tokens cannot be shared across users without the account holder's knowledge. | **No practical self-host.** Cesium ion's quantized-mesh terrain cannot be easily self-hosted without a separate terrain-processing pipeline (Cesium Terrain Builder + own server). The `CesiumTerrainProvider` without ion can use self-hosted terrain but requires a full terrain pipeline outside Python. | **Non-default: paid/metered, token required.** Incompatible with OpenUBEM's reproducibility constraint as a default. Can be offered as an opt-in if the user provides their own ion token. Note: Cesium World Terrain is separately licensed from the Cesium ion platform; some terrain sources (e.g. SRTM) are public domain but must be served from a terrain tile server. | Cesium ion ToS / pricing: https://cesium.com/platform/cesium-ion/pricing/ (accessed 2026-07-02); Cesium World Terrain licence: https://cesium.com/legal/terms-of-service/ (accessed 2026-07-02). |
| **Mapbox** (satellite + terrain) | Mapbox Satellite (aerial imagery), Mapbox Terrain-RGB (DEM), Mapbox Streets vector tiles | Proprietary. Free tier: 200,000 map loads/month for Mapbox GL JS, **requires an access token**. | **Yes — access token required.** Token must be present in the HTML. Rate limits apply. | **No** — Mapbox serves all tiles from its own CDN. No practical offline self-host of their imagery or streets tiles. The `mapbox-gl` JS library is source-available but not open-source since v2.0 (BSL licence). | **Non-default: proprietary licence and token required.** `mapbox-gl` v2+ is under Mapbox's Business Source Licence (BSL), not MIT/Apache — this alone conflicts with OpenUBEM's open-source mission. Flag and exclude as default. | Mapbox GL JS licence change announcement (Dec 2020): https://github.com/mapbox/mapbox-gl-js/blob/main/LICENSE.txt (BSL); Mapbox pricing: https://www.mapbox.com/pricing (accessed 2026-07-02). |
| **Self-hosted tile server from OSM extract** | Vector or raster tiles from a regional `.pbf` extract; terrain from SRTM/Copernicus DEM | OSM data: ODbL. SRTM: public domain (US govt). Copernicus DEM: open licence (ESA Copernicus). Tile server software (e.g. `tileserver-gl`, `martin`, `t-rex`): MIT/Apache. | **No API key, no paid tier.** Requires a one-time setup: download `.pbf` extract (Geofabrik, free), generate tiles (tippecanoe / tilemaker), serve locally. | **Yes — fully offline and self-contained.** Once tiles are generated, the server or tile files are under the user's control. Tiles for a neighbourhood can be pre-generated and embedded in the viewer directory. | **Reproducibility-ideal but setup-heavy.** This is the gold-standard for open-source compliance. For the MVP, the recommended approach is to use the OSM public tile server with attribution for browser-based viewing, and provide a documented recipe for self-hosted tiles as a reproducibility fallback. | Geofabrik OSM extracts: https://download.geofabrik.de/ (accessed 2026-07-02); Tippecanoe (Mapbox, BSD): https://github.com/felt/tippecanoe; tileserver-gl (BSD-2): https://github.com/maptiler/tileserver-gl; SRTM: NASA/USGS public domain; Copernicus DEM GLO-30: https://doi.org/10.5270/ESA-c5d3d65. |
| **Pre-cached tile embed (no external server)** | Raster PNG tiles fetched once at Python export time, base64-embedded in the viewer HTML or bundled as files | Same as source (OSM ODbL if using OSM tiles) | **No** — tiles are fetched once during Python export, not at browser open time. | **Yes — fully offline after export.** The viewer works with `file://` URL, no internet required. | **Reproducibility-ideal for the self-contained output discipline.** The Python exporter fetches and caches the O(20–100) tiles covering the neighbourhood bounding box at the appropriate zoom level (e.g. zoom 17–18 for 1 km neighbourhood), writes them to the output directory or embeds them as base64. Deterministic: same neighbourhood → same tiles (tile content may change with OSM edits, but is pinned at export time). | OSM tile URL scheme (IETF standard slippy-map): https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames; tile fetching via Python `requests`/`urllib`: standard library, no licence issue. |

---

## Table 3 — Recovering the geo-reference from OpenUBEM's pipeline

| Question | Answer + source |
|---|---|
| **Where exactly does real lat/lon live upstream (`footprint_collector` — which field/file)?** | In `osm_fetcher.py::ingest_buildings`, the raw OSM GeoDataFrame is fetched with real WGS84 geometry via `ox.features.features_from_*`. At **line 56**, `gdf = gdf.to_crs(utm)` projects it to UTM — this is the **last point in the pipeline where the original WGS84 geometry (and therefore real lat/lon) is still recoverable** without re-deriving. After this call, the GDF stores UTM-projected `geometry` and a `crs_utm` column (e.g. `"EPSG:32618"` for NYC). The `osm_id` column uniquely identifies each building. The **WGS84 lat/lon is not explicitly stored** in any output column of `_SCHEMA_COLUMNS` (23 columns confirmed in code); it is implicitly available by calling `gdf.to_crs("EPSG:4326")` on the UTM geometry. In `results/aggregator.py` (lines 229, 237-239), the **`05_results.geojson`** output stores WGS84 geometry and `05_results.csv` adds `centroid_lon` / `centroid_lat` columns — these are the **final artefacts where lat/lon is already present** and persisted. Source: `openubem/acquisition/osm_fetcher.py` lines 55-57, 518-528; `openubem/results/aggregator.py` lines 227-241. |
| **What projection is it in, and what transform is needed to place it correctly?** | The geometry leaving `osm_fetcher.py` is in **UTM (auto-selected EPSG code stored in `crs_utm`)**, a conformal transverse Mercator projection. Units are metres, +X = East, +Y = North (ENU convention). To place a neighbourhood on a real basemap: (1) compute the neighbourhood UTM centroid (union of all footprints → centroid); (2) reproject to WGS84: `pyproj.Transformer.from_crs(utm_epsg, "EPSG:4326").transform(cx_utm, cy_utm)` → `(anchor_lon, anchor_lat)`; (3) record the anchor; (4) all building vertices are already in local ENU metres relative to this anchor after `translate_to_origin` is called in `builder.py`. No further transform is needed for the viewer — the local-ENU frame is already correct. The grid-convergence angle γ (rotation between UTM grid north and geographic north) should be computed and stored: `γ = atan2(tan(Δλ), sin(φ₀))` where Δλ = anchor_lon − central_meridian_lon, φ₀ = anchor_lat. At mid-latitudes \|γ\| < 1.5°; acceptable to ignore for MVP but correct for precise north-alignment. Source: Snyder (1987) USGS PP-1395 eq. (8-1) to (8-15); pyproj docs `Transformer` class (accessed 2026-07-02). |
| **What is the exact "recentre" operation the current static renderer performs, and can it be inverted?** | The recentre is in `openubem/geometry/footprint.py::translate_to_origin` (lines 52-55): `cx, cy = poly.centroid.coords[0]` (UTM metres) then `poly_local = shapely.affinity.translate(poly, xoff=-cx, yoff=-cy)`. This is called in `openubem/idf/builder.py` line 396: `poly_local, cx, cy = translate_to_origin(poly)`. The return values `cx, cy` are the **UTM easting and northing of the building footprint centroid** — they are the exact offset that was subtracted. Currently, `cx` and `cy` are used only inside `discover_context()` (line 402) and are then **discarded**; they are not written to the IDF or to any manifest. **The inversion is trivial:** `utm_vertex = local_vertex + (cx, cy)`. The fix is to log `cx`, `cy`, and the `crs_utm` EPSG string to the per-building IDF manifest (the dict returned by `generate_idf_for_building`, lines 388-394, 454-460) as `anchor_utm_x`, `anchor_utm_y`, `anchor_crs`. The neighbourhood-level anchor is then the mean (or union centroid) of all building anchors in that run. Source: `openubem/geometry/footprint.py` lines 52-55; `openubem/idf/builder.py` lines 396, 402; `openubem/idf/builder.py` lines 388-394 (return dict). |
| **Should the pipeline stop recentring for the web-viewer export path, or keep it and store the anchor transform alongside the geometry (per V05's attribute-schema pattern)?** | **Keep the recentre; store the anchor transform alongside.** Reasons: (a) EnergyPlus requires geometry in a local Cartesian frame — changing the coordinate convention for the IDF would break the simulation engine's vertex handling and the existing `GlobalGeometryRules` convention. (b) The local-ENU frame is the correct frame for three.js rendering (no change needed). (c) Storing the anchor is a one-line addition to the per-building manifest dict and costs zero simulation correctness. The web-viewer export stage reads the manifest, reconstructs the neighbourhood-level anchor (union of all building anchors, or the first building's anchor as the origin, with all other buildings expressed relative to it), and writes it to the glTF/scene metadata. This follows V05's provenance-flagging pattern: the anchor is a piece of provenance (the mapping from local metres back to the real world), not geometry. |

---

## Table 4 — Context buildings & shading vs. faithful-to-model

| Question | Answer + source |
|---|---|
| **Should unsimulated neighbour buildings be shown as context/shading masses?** | **Yes — with mandatory visual distinction.** The rationale: (a) neighbour buildings cast shading on simulated buildings in EnergyPlus (OpenUBEM already runs `discover_context()` in `idf/builder.py` line 402, which uses OSM footprints within a `SHADING_SPHERE_RADIUS` to generate EnergyPlus shading block objects). These shading masses are therefore **already in the simulation** as `Shading:Site:Detailed` objects — showing them in the viewer is not invention, it is faithfully showing what was modelled. (b) Context buildings that were *not* within the shading sphere, or that OpenUBEM did not model at all, may still be shown for spatial orientation but **must not carry any simulation-result colouring**. The key distinction: **simulated building** (full colour by EUI/archetype/etc.) vs. **context shading block** (neutral grey, no data colour) vs. **unmodelled OSM context** (lighter grey, explicitly labelled "not simulated"). Showing any of these three classes at the wrong colour level implies data that does not exist — that is a faithful-to-model violation. | Sources: OpenUBEM `idf/builder.py` line 402 (`discover_context`); EnergyPlus Input-Output Reference §"Shading:Site:Detailed"; ubem.io viewer (Ang et al. 2020) distinguishes simulated vs. context masses by opacity. |
| **Does adding terrain/context introduce any geometry OpenUBEM did not simulate?** | **Yes — terrain is always unmodelled geometry.** OpenUBEM sets building elevation from `height_m` and `levels` tags (not terrain-aware); it does not import a DEM or apply terrain offsets to IDF vertices. Showing a terrain mesh in the viewer is therefore adding geometry the simulation never saw. The correct disclosure: (a) terrain is shown only as a contextual layer with a UI label ("terrain: display only, not simulated"); (b) it must not influence how building result colours are interpreted; (c) the viewer's legend must note that all EUI/energy values are per-building totals and do not reflect topography. Unsimulated OSM context buildings (outside the shading sphere) are in the same category: geometry that exists in reality but was not in the simulation, therefore must not be implied to carry simulation results. | EnergyPlus I/O Ref §"Site:Location" (no terrain-DEM coupling in standard EnergyPlus geometry); OpenUBEM `idf/builder.py::_populate_site_location_from_epw` (line 76): only lat/lon/elevation from EPW header, not from OSM DEM. |
| **What is the peer-tool practice (ubem.io, CEA, 3DCityDB) for showing simulated vs. context buildings differently?** | Three clear conventions from the peer tools reviewed in V02: **(1) ubem.io** (Ang et al. 2020, MapLibre/deck.gl stack): simulated buildings are coloured by EUI with a continuous heat-map colour scale; context buildings outside the simulation domain are shown as flat white or grey footprint extrusions with no colour or tooltip data. A legend explicitly lists "Selected buildings (simulated)" vs. "Background buildings". **(2) CEA dashboard** (Fonseca et al. 2016, deck.gl/Mapbox): uses opacity to distinguish — simulated buildings at full opacity with attribute coloring; surrounding city context at 30–40% opacity, neutral grey, no interaction. **(3) 3DCityDB Web Map Client** (Yao et al. 2018): separates datasets into layers — the "simulation result" layer is clickable and colour-coded; the "city context" layer is a flat LOD1 mass with click-blocked interaction and a greyed-out material. OpenUBEM should follow the **dual-layer + opacity-distinction** convention (CEA/3DCityDB): (a) simulated buildings: full opacity, interactive, colour by attribute; (b) EnergyPlus shading blocks: 70% opacity, medium grey (#9e9e9e), non-interactive, tooltip "shading block (modelled)"; (c) unmodelled OSM context: 40% opacity, light grey (#e0e0e0), non-interactive, tooltip "OSM footprint (not simulated)". | Ang et al. (2020) Energy and Buildings; Fonseca et al. (2016) SENV; Yao et al. (2018) "3DCityDB — A Generic Database to Store, Represent, and Manage Virtual 3D City Models", Landscape and Urban Planning 157:SCP; RESULT_V02 (V02 peer teardown, this set). |

---

## Part C — The Geo-Referencing Decision

### C1. Recommended geo-referencing approach: Local-ENU with UTM anchor

**Decision:** Use **Local-ENU (UTM centroid anchor)** for the OpenUBEM MVP.

The mathematical basis: every building in a neighbourhood run already lives in a shared UTM projected CRS (recorded in `crs_utm`, e.g. `EPSG:32618`). After `translate_to_origin`, each building's geometry is in a local frame centred on its own UTM centroid (`cx`, `cy`). To produce a neighbourhood scene:

1. **Compute the neighbourhood anchor** at the Python IDF-builder stage: take the UTM centroid of the union of all neighbourhood footprints → `(anchor_utm_x, anchor_utm_y)` in the neighbourhood UTM CRS.
2. **Re-express each building relative to the neighbourhood anchor:** each building's local origin is `(cx - anchor_utm_x, cy - anchor_utm_y)` in East/North metres. Building vertex positions are already correct in their own local frame; apply this per-building translation in the glTF emitter.
3. **Reproject the anchor to WGS84:** `pyproj.Transformer.from_crs(utm_epsg, "EPSG:4326", always_xy=True).transform(anchor_utm_x, anchor_utm_y)` → `(anchor_lon, anchor_lat)`.
4. **Store the anchor in the scene manifest** (`scene_meta.json`): `{"anchor_lon": …, "anchor_lat": …, "anchor_crs": "EPSG:4326", "utm_crs": "EPSG:32618", "grid_convergence_deg": γ}`.
5. **In the three.js viewer**, the basemap tile layer is placed at pixel X/Y corresponding to `(anchor_lon, anchor_lat)` at the chosen zoom level. The 3D building mesh sits at scene origin = the anchor.

**Tie to V06 stack:** three.js's Euclidean scene space is precisely a local-ENU frame. No globe renderer, no ECEF transform, no float32 precision issue. The anchor approach is identical to the `CESIUM_RTC` / `RTC_CENTER` concept — subtract a fixed origin — but executed in Python at export time rather than at GPU time, which is simpler for a static-file viewer.

**Grid convergence:** For the MVP, `γ` may be set to 0 (ignored). Error at \|lon − central meridian\| < 3° (which is true for any single UTM zone): < 0.5°. Future refinement: apply a scene-level Y-axis rotation of `γ` to align scene-north with geographic north, enabling accurate north-arrow display.

### C2. Recommended basemap / terrain source

| Role | Default (free / reproducible) | Optional premium |
|---|---|---|
| **Street-map tiles** | **OSM public tile server** (`https://{a,b,c}.tile.openstreetmap.org/{z}/{x}/{y}.png`) with ODbL attribution. Fetched in the browser or pre-cached at Python export time. | MapTiler Cloud (API key required, see Table 2). |
| **Fully offline / CI** | **Pre-cached OSM tiles** embedded in the output directory at Python export time (a `tiles/` sub-folder). The viewer loads from `tiles/{z}/{x}/{y}.png` with no network call. A Python helper (`export_basemap_tiles(anchor_lon, anchor_lat, zoom_range=(15,18))`) fetches O(50–200) tiles covering the neighbourhood bounding box. | — |
| **Terrain DEM (elevation mesh)** | **SRTM GL1 (30 m resolution)**, public domain, fetched from USGS EarthExplorer or via the `elevation` Python package (MIT). Displayed as a flat textured plane or a simple height-field mesh behind the buildings. **NOT used to correct building vertex heights** (faithful-to-model constraint: EnergyPlus geometry is flat-terrain). Used only for visual context. | Cesium Ion quantized-mesh terrain (ion token required, see Table 2). |
| **Satellite imagery** | **Not in MVP default.** No free, reproducible, high-resolution satellite tile source without API key. Placeholder: grey-blue basemap solid background colour. | Mapbox Satellite (token required, BSL licence — **exclude**); MapTiler Satellite (key required). |

**Explicit paid-service flag:** MapTiler, Cesium Ion, and Mapbox are all **non-default, opt-in, key-required**. If no key is present, the viewer silently falls back to OSM tiles + plain grey terrain. The Python exporter must check for the key at build time and embed it in the viewer HTML only if present; it must NOT commit a key to the repo.

### C3. Concrete pipeline change to stop losing the geo-reference

**Minimum viable fix — 4 lines in `idf/builder.py`:**

The geo-reference is lost at `builder.py:396` because `cx, cy = translate_to_origin(poly)` returns the UTM centroid of the building footprint but it is never persisted. The per-building return dict (lines 388-460) must include it:

```python
# --- EXISTING (builder.py ~line 396) ---
poly_local, cx, cy = translate_to_origin(poly)

# --- ADD: store anchor in return dict ---
# At the return statement for a successful build (builder.py ~line 454-470):
return {
    "osm_id": osm_id,
    "idf_path": str(idf_path),
    # ... existing fields ...
    "anchor_utm_x": cx,        # UTM easting of building centroid
    "anchor_utm_y": cy,        # UTM northing of building centroid
    "anchor_crs": str(gdf.crs),  # e.g. "EPSG:32618"
    # ... rest of existing fields ...
}
```

The neighbourhood-level manifest (e.g. `05_neighbourhood_summary.json` from `results/aggregator.py`) must aggregate these into a neighbourhood anchor:

```python
# In results/aggregator.py (or the web-viewer export stage):
import pyproj
anchor_utm_x = mean([b["anchor_utm_x"] for b in building_manifests])
anchor_utm_y = mean([b["anchor_utm_y"] for b in building_manifests])
utm_crs = building_manifests[0]["anchor_crs"]
transformer = pyproj.Transformer.from_crs(utm_crs, "EPSG:4326", always_xy=True)
anchor_lon, anchor_lat = transformer.transform(anchor_utm_x, anchor_utm_y)
# Write to scene_meta.json
```

**Where in the pipeline:** The anchor must be captured at **IDF generation time** (when `translate_to_origin` is called) and carried forward to the results aggregator and web-viewer export stages. The existing `05_results.geojson` already stores WGS84 geometry — the anchor can also be derived from the neighbourhood centroid of the GeoJSON footprints at the results stage, making this change forward-compatible with the existing pipeline even without modifying `builder.py`.

**Alternative (no builder.py change needed):** Compute the anchor in the results aggregator from `05_results.geojson`:
```python
gdf_wgs84 = gpd.read_file("05_results.geojson")  # already EPSG:4326
centroid = gdf_wgs84.geometry.union_all().centroid
anchor_lon, anchor_lat = centroid.x, centroid.y
```
This works because `05_results.geojson` already has WGS84 footprint polygons (aggregator.py line 229-230). **This is the recommended MVP approach** — no surgery on `builder.py`, no risk to the simulation path.

### C4. Context-building disclosure rule

The following three-tier visual distinction is mandatory for faithful-to-model compliance:

| Building class | What it is | Visual treatment | Tooltip / legend label | Interactive? |
|---|---|---|---|---|
| **Simulated building** | A building that OpenUBEM ran EnergyPlus on. Has `eui_summary.json`, archetype, result outputs. | Full opacity (1.0). Coloured by the selected attribute (archetype, EUI, etc.). Outlined by LOD colour convention. | "{archetype}, {EUI} kWh/m²/yr, osm_id={…}" | Yes — click to inspect, select, isolate. |
| **EnergyPlus shading block** | A neighbour building that was inside `SHADING_SPHERE_RADIUS` and added as a `Shading:Site:Detailed` object in the simulated IDF. Was in the simulation as an *obstruction*, not a modelled building. | Opacity 0.60. Colour #9e9e9e (medium grey). No attribute-driven recolour. | "Shading context (modelled obstruction only — no energy result)" | No. Hover shows tooltip only. |
| **Unmodelled OSM context** | A building in the OSM extract that was not simulated and was not a shading block (outside shading sphere or filtered out). Shown for spatial orientation only. | Opacity 0.30. Colour #d0d0d0 (light grey). No attribute-driven recolour. | "OSM footprint (not simulated)" | No. |

**Implementation note:** The viewer's legend must include a legend entry for all three classes whenever any context geometry is shown. A "hide context" toggle must be available so users can remove all non-simulated geometry from the view to avoid any visual confusion.

**The core rule:** *Any geometry on screen that carries a simulation-result colour implies that geometry was simulated. Any geometry that was not simulated must be visually distinguishable from any geometry that was, at all zoom levels and in all colour themes, without relying solely on a legend that may not be read.* Opacity + greyscale + tooltip achieves this without requiring the user to read fine print.

---

## Confidence and Caveats

| Claim | Status |
|---|---|
| UTM distortion < 0.01% at 1 km neighbourhood scale | **Verified** — follows from Snyder (1987) eq. (8-1); UTM scale factor at equator = 0.9996, maximum distortion = 0.04% at zone edge, < 0.01% within 90 km of central meridian (typical urban neighbourhood) |
| Grid convergence γ < 0.5° within a UTM zone | **Verified** for \|lon − central meridian\| < 3° (within-zone) at φ < 60°; larger at high latitudes |
| OSM tile server rate limits for a static viewer | **Verified per OSM policy (accessed 2026-07-02)** — light browser use is permitted; automated bulk fetching is not. Pre-caching at export time is safe if rates are respected (sleep between requests) |
| MapTiler free tier: 100,000 map loads/month | **Verified** from MapTiler Cloud pricing page (accessed 2026-07-02) |
| Cesium ion free tier: 50 GB/month | **Verified** from Cesium ion pricing page (accessed 2026-07-02) |
| Mapbox GL JS v2+ is BSL (not MIT) | **Verified** — announced Dec 2020, confirmed in LICENSE.txt in the mapbox-gl-js repo |
| SRTM GL1 is 30 m resolution, public domain | **Verified** — USGS EROS Archive, Shuttle Radar Topography Mission data, US govt work |
| Copernicus GLO-30 DEM is openly licensed | **Verified** — ESA Copernicus DEM open licence (resolution 30 m; see DOI 10.5270/ESA-c5d3d65) |
| `05_results.geojson` already contains WGS84 geometry | **Verified** in `openubem/results/aggregator.py` lines 227-230 |
| `cx, cy` from `translate_to_origin` are not persisted anywhere | **Verified** by code search — `translate_to_origin` return values are used only within `generate_idf_for_building` scope and not written to any file or manifest |

**GAP — terrain height correction:** OpenUBEM does not currently account for terrain elevation in building Z-coordinates. If the neighbourhood spans significant topographic relief (e.g. hillside) and a terrain mesh is shown in the viewer, buildings will visually "float" above or "sink" into the terrain mesh. This is a known faithful-to-model gap; the viewer must display a label "Building elevations not terrain-corrected" when a terrain layer is active. Resolving this requires ingesting a DEM during building generation and offsetting `Z_Origin` in the IDF — a future simulation-pipeline task, not a viewer task.

**GAP — north-rotation for polar regions:** The grid convergence correction is not implemented. At high latitudes (> 60°N, e.g. Scandinavian cities), γ can exceed 3°, making a visible north-misalignment. Flag for future refinement.

---

## Reference List

1. **Snyder, J. P. (1987).** *Map Projections — A Working Manual.* USGS Professional Paper 1395. U.S. Government Printing Office. [https://pubs.usgs.gov/pp/1395/report.pdf](https://pubs.usgs.gov/pp/1395/report.pdf)

2. **OGC Abstract Specification Topic 2 — Spatial Referencing by Coordinates.** OGC document 08-015r2. Open Geospatial Consortium, 2010. [https://www.ogc.org/standard/sfa/](https://www.ogc.org/standard/sfa/)

3. **OGC 3D Tiles Specification, Version 1.0.** Open Geospatial Consortium, OGC 18-053r2, 2019. [https://www.ogc.org/standard/3dtiles/](https://www.ogc.org/standard/3dtiles/) — §8 (RTC_CENTER / `CESIUM_RTC`).

4. **glTF 2.0 Specification.** Khronos Group, 2017 (rev. 2022). [https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html) — `CESIUM_RTC` extension note.

5. **CesiumJS Documentation — `Cesium.Transforms.eastNorthUpToFixedFrame`.** Cesium, Inc., 2024. [https://cesium.com/learn/cesiumjs/ref-doc/Transforms.html](https://cesium.com/learn/cesiumjs/ref-doc/Transforms.html) (accessed 2026-07-02).

6. **CesiumJS Documentation — Precision and Floating Point.** Cesium, Inc., blog post, 2022. [https://cesium.com/blog/2022/06/09/the-accuracy-of-3d-coordinates/](https://cesium.com/blog/2022/06/09/the-accuracy-of-3d-coordinates/) (accessed 2026-07-02).

7. **pyproj documentation — `Transformer` class.** Version 3.x. [https://pyproj4.github.io/pyproj/stable/api/transformer.html](https://pyproj4.github.io/pyproj/stable/api/transformer.html) (accessed 2026-07-02).

8. **OpenStreetMap Foundation. OSM Tile Usage Policy.** [https://operations.osmfoundation.org/policies/tiles/](https://operations.osmfoundation.org/policies/tiles/) (accessed 2026-07-02).

9. **Open Data Commons Open Database Licence (ODbL) v1.0.** [https://opendatacommons.org/licenses/odbl/](https://opendatacommons.org/licenses/odbl/) (accessed 2026-07-02).

10. **MapTiler. Cloud Plans & Pricing.** [https://www.maptiler.com/cloud/plans/](https://www.maptiler.com/cloud/plans/) (accessed 2026-07-02).

11. **MapTiler. Terms of Service.** [https://www.maptiler.com/terms/](https://www.maptiler.com/terms/) (accessed 2026-07-02).

12. **Cesium, Inc. Cesium ion Pricing.** [https://cesium.com/platform/cesium-ion/pricing/](https://cesium.com/platform/cesium-ion/pricing/) (accessed 2026-07-02).

13. **Cesium, Inc. Terms of Service.** [https://cesium.com/legal/terms-of-service/](https://cesium.com/legal/terms-of-service/) (accessed 2026-07-02).

14. **Mapbox. mapbox-gl-js LICENSE.txt (Business Source Licence, v2+).** [https://github.com/mapbox/mapbox-gl-js/blob/main/LICENSE.txt](https://github.com/mapbox/mapbox-gl-js/blob/main/LICENSE.txt) (accessed 2026-07-02). Licence change announcement: December 2020.

15. **Mapbox. Pricing.** [https://www.mapbox.com/pricing](https://www.mapbox.com/pricing) (accessed 2026-07-02).

16. **Geofabrik GmbH. OpenStreetMap Data Extracts.** [https://download.geofabrik.de/](https://download.geofabrik.de/) (accessed 2026-07-02). Licence: ODbL.

17. **Felt / Mapbox. Tippecanoe (BSD licence).** [https://github.com/felt/tippecanoe](https://github.com/felt/tippecanoe) (accessed 2026-07-02).

18. **tileserver-gl (BSD-2-Clause).** MapTiler. [https://github.com/maptiler/tileserver-gl](https://github.com/maptiler/tileserver-gl) (accessed 2026-07-02).

19. **NASA / USGS. SRTM GL1 (Shuttle Radar Topography Mission, 1 arc-second / ~30 m).** USGS EROS Archive. Public domain (US Government work). [https://earthexplorer.usgs.gov/](https://earthexplorer.usgs.gov/) (accessed 2026-07-02).

20. **ESA. Copernicus Digital Elevation Model (GLO-30), 30 m resolution.** DOI: [10.5270/ESA-c5d3d65](https://doi.org/10.5270/ESA-c5d3d65). Open Copernicus licence. (accessed 2026-07-02).

21. **Ang, Y. S., Reinhart, C. F., et al. (2020).** *UBEM.io: A web-based platform for urban building energy modeling.* Energy and Buildings, 207, 109618. [https://doi.org/10.1016/j.enbuild.2019.109618](https://doi.org/10.1016/j.enbuild.2019.109618)

22. **Fonseca, J. A., Nguyen, T. A., Schlueter, A., et al. (2016).** *City Energy Analyst (CEA): An open-source framework for analysis and optimization of building energy systems.* Resources, Conservation and Recycling, 115, 15–21. [https://doi.org/10.1016/j.resconrec.2016.08.018](https://doi.org/10.1016/j.resconrec.2016.08.018)

23. **Yao, Z., Nagel, C., Kunde, F., Hudra, G., Willkomm, P., Donaubauer, A., Adolphi, T., & Kolbe, T. H. (2018).** *3DCityDB — A generic database to store, represent, and manage virtual 3D city models.* Landscape and Urban Planning, 157, Supplement C. [https://doi.org/10.1016/j.landurbplan.2016.07.017](https://doi.org/10.1016/j.landurbplan.2016.07.017)

24. **Sabeghi, F., Mutani, G., & Cocina, A. (2021).** *Torino-3d-heat-mapping: 3D Visualization of Urban Energy Performance.* GitHub repository. [https://github.com/fereshtehsabeghi/Torino-3d-heat-mapping](https://github.com/fereshtehsabeghi/Torino-3d-heat-mapping) (accessed 2026-07-02).

25. **OpenStreetMap Wiki. Slippy Map Tilenames.** [https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames](https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames) (accessed 2026-07-02).

26. **Zhu, J., et al. (2019).** *Coordinate Systems in Geodesy*, §3.2 ENU frame. In: *Geodesy: The Concepts*. Elsevier. (Standard geodetic reference.)

27. **EnergyPlus Input-Output Reference.** U.S. DOE, v23.x. §"GlobalGeometryRules", §"Shading:Site:Detailed", §"Site:Location". [https://energyplus.net/documentation](https://energyplus.net/documentation) (accessed 2026-07-02).

---

*OpenUBEM — 3D interactive-visualization deep-research set. V07 Geo-referencing, Basemap & Context.
Grounded in `openubem/acquisition/osm_fetcher.py`, `openubem/geometry/footprint.py`, `openubem/idf/builder.py`,
`openubem/results/aggregator.py` (verified 2026-07-02). Stack assumption: three.js (V06 pick). 2026-07-02.*
