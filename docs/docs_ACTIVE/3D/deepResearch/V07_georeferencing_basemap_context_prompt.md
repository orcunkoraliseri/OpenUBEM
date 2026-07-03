# Deep-Research Prompt V07 — GEO-REFERENCING, BASEMAP & CONTEXT

> SCOPE GUARD — READ FIRST. This prompt owns **placing the scene on real-world coordinates**: lat/lon →
> local coordinate transforms, terrain, satellite/OSM basemaps, context/neighbour buildings and their
> shading, and OpenUBEM's specific coordinate-system pitfall (the pipeline renders in **recentred local
> metres**, losing the real lat/lon that exists upstream). It is NOT the rendering library decision (that is
> `V06` — assume its pick and work within it), and NOT the LOD ladder (that is `V04`). See
> `00_README_3dviz_prompt_set.md` for shared facts, roster, conventions.

---

## What this document is

The geo-referencing decision for the viewer. OpenUBEM's `footprint_collector` stage holds real lat/lon for
every OSM footprint it ingests, but by the time geometry reaches `visualizer_adapter.py`/`idf_to_*`, it has
been **recentred into local metres** (an EnergyPlus/simulation convention — IDF geometry is defined in a
local Cartesian frame with `GlobalGeometryRules` relative/absolute coordinates and per-zone origin offsets,
not global coordinates). A web viewer that wants to place a neighbourhood on a real basemap, show terrain,
or render true-to-life shading from neighbouring (non-simulated) buildings must recover or re-derive that
geo-reference. This prompt decides how, and whether the effort is worth it for OpenUBEM's MVP given the two
hard constraints (a paid basemap/terrain service is a reproducibility risk).

## Role

Geospatial-reference-systems / web-cartography analyst. Ground every claim in the actual coordinate-
transform math and library support: **local ENU (East-North-Up) vs. ECEF vs. Web Mercator** projections,
**CesiumJS's** `Cesium.Transforms` / `Cesium.Cartesian3.fromDegrees` geo-referencing model, **MapLibre
GL's** Web-Mercator-tile coordinate system, **glTF's** `CESIUM_RTC`/3D-Tiles `transform` mechanism for
placing a locally-authored glTF at a geodetic anchor, and **OSM/terrain data sources** (OpenStreetMap tile
servers, SRTM/terrain-RGB DEMs, MapTiler, Cesium World Terrain). Ground the licence/cost comparison in each
provider's actual terms of service.

## Why this matters (so you scope correctly)

Every static render OpenUBEM produces today throws away the real-world location — a neighbourhood axo PNG
could be anywhere. A web viewer that wants a basemap, satellite context, or believable shading from
surrounding (unsimulated) buildings needs the geo-reference back, and needs it **exactly right** — a
mis-projected anchor silently shifts every building, which is a faithful-to-model failure even though the
building geometry itself is untouched. This also intersects the reproducibility constraint directly: several
basemap/terrain providers are paid or usage-metered, which would make OpenUBEM's viewer depend on a service
outside its control.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Geo-referencing approach fitness

| Approach | How it anchors the scene to real coordinates | Precision/pitfalls | Fit for OpenUBEM's neighbourhood-scale scenes | Works with the `V06` stack candidates | Source |
|---|---|---|---|---|---|
| Local-ENU scene (author in local metres, single geodetic anchor point + rotation) |  |  |  |  |  |
| True-globe (Cesium ECEF, full geodetic per-vertex) |  |  |  |  |  |
| Web-Mercator planar (MapLibre/Mapbox tile coordinate system) |  |  |  |  |  |

### Table 2 — Basemap/terrain options, licence & cost

| Provider/source | Data type (street map / satellite / terrain DEM) | Licence | Requires an API key / paid tier at OpenUBEM's expected usage? | Self-hostable / offline option? | Verdict against the reproducibility constraint | Source |
|---|---|---|---|---|---|---|
| OpenStreetMap raster/vector tiles |  |  |  |  |  |  |
| MapTiler |  |  |  |  |  |  |
| Cesium Ion (terrain + imagery) |  |  |  |  |  |  |
| Mapbox (satellite/terrain) |  |  |  |  |  |  |
| Self-hosted tile server (e.g. from local OSM extract) |  |  |  |  |  |  |

### Table 3 — Recovering the geo-reference from OpenUBEM's pipeline

| Question | Answer + source |
|---|---|
| Where exactly does real lat/lon live upstream (`footprint_collector` — which field/file)? |  |
| What projection is it in, and what transform is needed to place it correctly (e.g. lat/lon → UTM → local ENU)? |  |
| What is the exact "recentre" operation the current static renderer performs, and can it be inverted/logged so the geo-reference is recoverable without re-deriving it from scratch? |  |
| Should the pipeline stop recentring for the web-viewer export path, or keep it and store the anchor transform alongside the geometry (per `V05`'s attribute-schema pattern)? |  |

### Table 4 — Context buildings & shading vs. faithful-to-model

| Question | Answer + source |
|---|---|
| Should unsimulated neighbour buildings be shown as context/shading masses (OSM footprint + estimated height) and how should the viewer visually distinguish them from real simulated buildings (so a user cannot mistake a context mass for a modelled result)? |  |
| Does adding terrain/context introduce any geometry OpenUBEM did not simulate, and how does the field (or should OpenUBEM) disclose that in the view? |  |
| What is the peer-tool practice (ubem.io, CEA, 3DCityDB) for showing simulated vs. context buildings differently? (cite `V02`) |  |

---

## Part C — Synthesis (the geo-referencing decision)

Give: (1) the **recommended geo-referencing approach** for OpenUBEM's MVP (local-ENU-with-anchor vs.
true-globe vs. Web-Mercator-planar), tied to the `V06` stack pick; (2) the **recommended basemap/terrain
source**, explicitly flagging any paid/licensed option as non-default and naming the free/self-hostable
fallback; (3) the **concrete pipeline change** needed to stop losing the geo-reference (where in
`footprint_collector`→geometry-export the anchor must be captured and carried through); (4) the **context-
building disclosure rule** so unsimulated masses are never visually confusable with real results.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C decision.
3. Cite the projection math / library docs (CesiumJS, MapLibre, glTF `CESIUM_RTC`) and each basemap
   provider's actual terms-of-service page for licence/cost claims.
4. **"Confidence and caveats":** which precision or cost claim is an estimate vs. a verified provider term.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Trace the exact point in the OpenUBEM pipeline where lat/lon is lost**, and state the minimal fix.
- **Flag every paid/metered basemap or terrain provider explicitly** — this is the reproducibility
  constraint; name the free/self-hostable default.
- **Address how context (unsimulated) buildings are visually distinguished from real results** —
  faithful-to-model applies to what is *implied* on screen, not just what is geometrically exact.
- **No fabricated precision;** flag GAPs. **Stay on topic** — the *geo-referencing, basemap, and context*
  question only, not the rendering stack pick (`V06`) or the LOD ladder (`V04`).
