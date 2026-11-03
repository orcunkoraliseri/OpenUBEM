# Deep-Research Prompt V03 — SCENE GEOMETRY & INTERCHANGE FORMATS (turning OpenUBEM IDF/OSM geometry into a web-renderable scene)

> SCOPE GUARD — READ FIRST. This prompt makes **one decision**: the file/data format OpenUBEM's scene
> geometry is serialized into for the browser — glTF 2.0/`.glb` vs. OGC 3D Tiles vs. CityJSON vs.
> extruded-GeoJSON — and whether/how the existing `idf_to_collada`/`idf_to_obj` `collect_geometry` pipeline
> can feed it. It is NOT the rendering library that consumes the format (that is `V06`), NOT the internals
> of how attributes bind to features once the format is picked (that is `V05` — reference it, don't answer
> it), and NOT the LOD ladder semantics or CityGML LOD numbering (that is `V04` — reference it, don't answer
> it). See `00_README_3dviz_prompt_set.md` for shared facts, roster, conventions.

---

## What this document is

The geometry-serialization decision for the viewer. OpenUBEM's only existing geometry-to-file paths are
**desktop-CAD exporters** — `idf_to_collada.py` (COLLADA 1.4.1 `.dae`), `idf_to_obj.py` (Wavefront
`.obj`+`.mtl`), and `idf_to_sketchup.py` (Ruby) — all sharing one `collect_geometry` grouping (site →
building → zone → per-category: wall/roof/ceiling/floor/window/shading), units metre, Z-up, targeting
SketchUp/Rhino, not a browser. Separately, `visualizer_adapter.py` parses IDF geometry directly (no
eppy/IDD), honouring `GlobalGeometryRules` relative/absolute coordinates and per-zone origin offsets, for
its static matplotlib renders. Neither path produces a web-consumable scene. This prompt decides which
interchange format the pipeline should emit instead (or in addition), and whether `collect_geometry` is
reusable as the geometry-extraction layer feeding a new emitter, given OpenUBEM is one-IDF-per-building and
a neighbourhood is many-IDFs, with two named LODs (surfaces-only vs. surfaces+sub-surfaces).

## Role

3D-graphics / geospatial-data-format analyst. Ground every claim in the actual specs and their reference
implementations: **glTF 2.0** (Khronos Group ratified spec, `KhronosGroup/glTF` repo, `EXT_mesh_features` /
`EXT_structural_metadata` extensions), **OGC 3D Tiles 1.0/1.1** (Open Geospatial Consortium standard,
Cesium's `3d-tiles` repo and `3d-tiles-tools`), **CityJSON** (the CityJSON spec at cityjson.org, its
Python `cjio` library, and its relationship to CityGML LOD0–4), and **extruded GeoJSON** (RFC 7946 +
MapLibre/Mapbox `fill-extrusion` layer spec). Cross-check against how the peer tools from `V02` (ubem.io,
CEA, 3DCityDB, the Torino heat-map repo) actually serialize their geometry, and against the rendering-stack
capabilities decided in `V06` where already available.

## Why this matters (so you scope correctly)

The format choice is the hinge between the Python pipeline and every browser-side capability downstream: it
determines whether per-surface attributes can bind at all (`V05`), whether the two LODs can be expressed as
distinct artifacts or one streamable hierarchy (`V04`), what the rendering stack in `V06` can actually load,
and whether the scene stays **faithful-to-model** (a lossy converter that merges surfaces or drops
sub-surfaces corrupts the geometry it claims to represent) and **reproducible/self-contained** (a format
requiring a proprietary converter or paid tiling service breaks the open-source delivery). Getting this
wrong forces a rewrite of every downstream prompt's assumptions.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Format-by-format capability matrix

| Format | Geometry fidelity (arbitrary polygons / triangulated only) | Sub-surface support (windows/doors as distinct features) | Per-feature attribute support (native or via extension) | LOD / tiling support | Typical file size (order of magnitude, per building / per neighbourhood) | Python emitter available (library + maintenance state) | Web-stack support (which of V06's candidates load it natively) | Source |
|---|---|---|---|---|---|---|---|---|
| glTF 2.0 / `.glb` |  |  |  |  |  |  |  |  |
| OGC 3D Tiles (1.0/1.1) |  |  |  |  |  |  |  |  |  |
| CityJSON |  |  |  |  |  |  |  |  |  |
| Extruded GeoJSON (`fill-extrusion`) |  |  |  |  |  |  |  |  |  |
| **OpenUBEM (current)** | Exact IDF polygons, no forced triangulation | Yes — windows/doors are distinct surfaces in `collect_geometry` | Per-category colour only (not structured attributes) | None (single static export per building/neighbourhood) | COLLADA `.dae` / OBJ, desktop-CAD scale, not web-optimized | `idf_to_collada.py`, `idf_to_obj.py`, `idf_to_sketchup.py` (all working, desktop-CAD targets only) | None — not consumed by any web stack | `idf_reader/idf_to_collada.py`, `idf_to_obj.py`, `idf_to_sketchup.py` |

### Table 2 — Mapping OpenUBEM's geometry primitives onto each format's constructs

| OpenUBEM primitive | glTF 2.0 construct | 3D Tiles construct | CityJSON construct | Extruded-GeoJSON construct | Faithful mapping or lossy? (say what is lost) |
|---|---|---|---|---|---|
| Opaque surface (wall/roof/ceiling/floor), arbitrary polygon with 3D vertex list |  |  |  |  |  |
| Sub-surface (window/door), coplanar-offset polygon |  |  |  |  |  |
| Shading surface (translucent) |  |  |  |  |  |
| Per-category material colour (wall `#d4a574`, roof/ceiling `#8b5e3c`, floor `#c0c0c0`, window `#5dade2`) |  |  |  |  |  |
| Site → building → zone grouping (the `collect_geometry` hierarchy) |  |  |  |  |  |
| One IDF per building, many IDFs per neighbourhood (assembling the whole scene) |  |  |  |  |  |

### Table 3 — Conversion path from IDF to each format

| Format | Reuse `collect_geometry` as the extraction layer? (yes/adapt/no) | New emitter needed (library + rough effort) | Where the emitter would sit in the pipeline (new module vs. extend existing exporter) | Round-trip risk (does the target format allow re-deriving the exact IDF surfaces for validation, per `V14`) | Source |
|---|---|---|---|---|---|
| glTF 2.0 / `.glb` |  |  |  |  |  |
| 3D Tiles |  |  |  |  |  |
| CityJSON |  |  |  |  |  |
| Extruded GeoJSON |  |  |  |  |  |

### Table 4 — Fit to OpenUBEM's two hard constraints

| Question | Answer + source |
|---|---|
| Which format(s) preserve exact IDF surface/sub-surface geometry with zero forced simplification (faithful-to-model)? |  |
| Which format(s) are producible by an open-source Python library with no proprietary converter or paid tiling step? |  |
| Which format(s) can express BOTH LODs (surfaces-only neighbourhood mass vs. surfaces+sub-surfaces building) as one coherent asset or a clean pair of assets, without duplicated authoring? |  |
| Is a **single format** sufficient for both LODs and both scales (one building vs. hundreds), or does the field's practice favor a **hybrid** (e.g. glTF per building + a lightweight extruded-footprint layer for the neighbourhood mass)? |  |

---

## Part C — Synthesis (the format decision)

Give: (1) the **single recommended primary format** for OpenUBEM's scene geometry, with the 2–3 decisive
reasons (fidelity + Python emitter maturity + hard-constraint fit first); (2) the **fallback or
complementary format** if the primary cannot express one of OpenUBEM's two LODs or the neighbourhood scale
cleanly; (3) an explicit statement of **what happens to `collect_geometry`** — keep as-is and wrap with a
new emitter, adapt its internals, or note it does not transfer; (4) the **downstream implications** for
`V04` (does the format naturally express the LOD ladder or does LOD switching need to be handled at the
scene-assembly level) and `V05` (does the format carry attributes natively or does it need a side-channel).

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C decision.
3. Cite the ratified spec text (Khronos glTF 2.0 spec, OGC 3D Tiles spec, cityjson.org spec, RFC 7946) and
   the Python library's own docs for every capability and emitter claim; separate spec guarantees from
   library-specific limitations.
4. **"Confidence and caveats":** which format's Python-emitter maturity or file-size-at-scale claim is
   least evidenced.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Force a ranked decision** — a primary format + fallback/complement, not "any of these works."
- **Explicitly resolve whether `collect_geometry` (the existing site→building→zone→category extraction) is
  reusable** for the recommended format's emitter — this is the concrete reuse question `V15` will build
  its migration map on.
- **Respect the two hard constraints** (faithful-to-model — no forced triangulation/decimation that loses
  real geometry; reproducible/self-contained/open-source — no proprietary converter or paid tiler required
  to produce the format).
- **No fabricated precision;** flag GAPs (especially file-size estimates). **Stay on topic** — the *format
  choice and geometry mapping* only, not the rendering library (`V06`), attribute-binding internals (`V05`),
  or LOD semantics (`V04`).
