# Deep-Research Prompt V02 — PEER-TOOL 3D VIEWER TEARDOWN (how shipped UBEM/city tools build interactive 3D)

> SCOPE GUARD — READ FIRST. This is the **"what do peer tools actually do"** anchor for the set. The
> deliverable is a sourced, tool-by-tool account of how established UBEM / city-energy / geospatial tools
> turn simulated buildings into an **interactive 3D web experience** — the data they render from, the
> stack they use, the LODs they expose, the interactions they support, and **whether/how they colour by a
> simulation output**. It is NOT the abstract taxonomy (that's `V01`), NOT the format decision (`V03`),
> and NOT the library pick (`V06`); it is *what shipped tools do and what OpenUBEM should copy*. See
> `00_README_3dviz_prompt_set.md` for shared facts, roster, conventions.

---

## What this document is

A fill-in-the-blanks comparison across the tools OpenUBEM benchmarks itself against, plus the two exemplars
the user named. OpenUBEM's own handling is known and pre-filled: static matplotlib axonometrics + CAD
exports, **no interactive web viewer at all**. The question the manager must answer from this table: *when
a UBEM/city tool wants to let a user navigate a neighbourhood and see energy results in 3D, what does it
actually build — and which single, well-documented design should OpenUBEM adopt as its MVP?*

## Role

UBEM / geospatial-tooling research analyst. Trace every behaviour to the tool's own documentation, source
code, published paper, or live demo: **ubem.io** (Ang, Reinhart et al. — the generator + its 3D gallery),
**City Energy Analyst / CEA** (Fonseca et al. — its dashboard / Plotly/deck outputs), **UMI** (Dogan &
Reinhart — Rhino + any WebGL export), **the `fereshtehsabeghi/Torino-3d-heat-mapping` repo** (the user's
named per-building web heat-map — read its actual stack/data), **3DCityDB + web-map-client / CesiumJS**
city viewers, **kepler.gl / deck.gl** urban dashboards, **MapLibre/Mapbox GL fill-extrusion** city-energy
demos, **ArcGIS Urban / ArcGIS API for JavaScript** scene layers, **Speckle** (AEC web viewer), and
**SimStadt/CitySim** outputs. Include the İşeri et al. in-repo work's visualization approach if any.

## Why this matters (so you scope correctly)

OpenUBEM's static-only status quo may be a genuine gap versus tools that ship a browser viewer, or the
field may mostly stop at dashboards + 2D maps. If ≥3 peer UBEM tools deliver an interactive per-building
output heat-map on a real basemap, that is a concrete, citable design target for OpenUBEM's viewer. If most
UBEM tools stop at static images or 2D choropleths and only *city-model* (non-energy) tools do true 3D,
that reframes the ambition. This prompt converts "we only have static PNGs" into "here is exactly what the
field ships, and the one design we should clone first."

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Stack & data: what each tool renders, from what, with what technology

| Tool | Interactive 3D web viewer? (or static/2D only) | Rendering stack (Cesium / deck.gl / MapLibre / three.js / engine) | Geometry data it renders (footprint-extrude / CityGML / mesh / IDF) | Geo-referenced on a basemap? | Source |
|---|---|---|---|---|---|
| ubem.io |  |  |  |  |  |
| CEA (City Energy Analyst) |  |  |  |  |  |
| UMI |  |  |  |  |  |
| Torino-3d-heat-mapping (named exemplar) |  |  |  |  |  |
| 3DCityDB web-map-client / Cesium |  |  |  |  |  |
| kepler.gl / deck.gl |  |  |  |  |  |
| MapLibre / Mapbox GL (energy demos) |  |  |  |  |  |
| ArcGIS Urban / ArcGIS JS |  |  |  |  |  |
| Speckle |  |  |  |  |  |
| **OpenUBEM (current)** | No — static PNG + CAD only | matplotlib (static); COLLADA/OBJ/SketchUp export | Parsed IDF surfaces + sub-surfaces | No (recentred local metres) | `idf_reader/visualizer_adapter.py`, `idf_to_*` |

### Table 2 — LOD & interaction grammar

| Tool | Neighbourhood LOD (masses/surfaces only)? | Building LOD (windows / sub-surfaces)? | Interactions (orbit / select / isolate / filter / section / walkthrough) | Time-slider for hourly/temporal results? | Source |
|---|---|---|---|---|---|
| ubem.io |  |  |  |  |  |
| CEA |  |  |  |  |  |
| UMI |  |  |  |  |  |
| Torino-3d-heat-mapping |  |  |  |  |  |
| 3DCityDB / Cesium |  |  |  |  |  |
| kepler.gl / deck.gl |  |  |  |  |  |
| MapLibre / Mapbox GL |  |  |  |  |  |
| ArcGIS Urban |  |  |  |  |  |
| **OpenUBEM (current)** | Axonometric masses (static) | Windows drawn (static PNG) | None (static image) | No | `idf_reader/*` |

### Table 3 — Output/attribute coloring (the heat-map question)

| Tool | Colours by simulation output (EUI/demand/carbon)? | Categorical (function) + sequential (population) coloring? | Per-surface heat-map (solar/irradiance) or per-building only? | Legend + classification shown? | Source |
|---|---|---|---|---|---|
| ubem.io |  |  |  |  |  |
| CEA |  |  |  |  |  |
| Torino-3d-heat-mapping |  |  |  |  |  |
| 3DCityDB / Cesium |  |  |  |  |  |
| kepler.gl / deck.gl |  |  |  |  |  |
| MapLibre / Mapbox GL |  |  |  |  |  |
| ArcGIS Urban |  |  |  |  |  |
| **OpenUBEM (current)** | No (per-category material colour only) | No | Per-category only, not output-driven | No | `idf_reader/visualizer_adapter.py` |

### Table 4 — Delivery, reproducibility & constraint fit

| Tool | Delivery (static file / static site / hosted service) | Needs a paid service or proprietary engine? | Open-source / self-hostable? | Producible from a Python pipeline? | Source |
|---|---|---|---|---|---|
| ubem.io |  |  |  |  |  |
| CEA |  |  |  |  |  |
| Torino-3d-heat-mapping |  |  |  |  |  |
| 3DCityDB / Cesium |  |  |  |  |  |
| kepler.gl / deck.gl |  |  |  |  |  |
| MapLibre / Mapbox GL |  |  |  |  |  |
| Speckle |  |  |  |  |  |
| **OpenUBEM (current)** | Static PNG / CAD file in `outputs/` | No | Yes | Yes | project convention |

---

## Part C — Synthesis (per-behaviour verdict)

For **each dimension** (stack/data, LOD & interaction, output-coloring, delivery), give an explicit
verdict: (a) does OpenUBEM's static-only status quo lag, match, or exceed the majority of peer tools; (b)
the single most-cited design the field uses for an interactive UBEM output view (e.g. "N tools use MapLibre
fill-extrusion coloured by a per-building metric"); (c) whether the named exemplars (Torino heat-map,
ubem.io) are clone-worthy MVPs or too narrow. End with the **one best-documented, constraint-compatible
design OpenUBEM should adopt first** and the tool it is cloned from.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C per-dimension verdict.
3. Cite each tool's documentation / paper / repo / live demo explicitly; flag undocumented behaviour as
   GAP. **Read the Torino repo's actual code/README** — do not guess its stack.
4. **"Confidence and caveats":** which tool's interactive-3D behaviour is least documented.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Cover ≥6 peer tools** plus the two named exemplars (Torino heat-map, ubem.io).
- **For every tool, state explicitly whether it ships an interactive 3D web viewer and whether it colours
  by a simulation output** — a tool that "only does 2D choropleth" or "only static images" is a valid,
  citable finding.
- **Note delivery model + whether a paid service/proprietary engine is required** (the reproducibility
  constraint), and whether it is producible from Python.
- **No fabricated precision;** flag GAPs. **Stay on topic** — shipped-tool *interactive-3D behaviour* only,
  not the abstract taxonomy (`V01`) or format internals (`V03`).
