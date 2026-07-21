# Deep-Research Prompt V01 — INTERACTIVE 3D CITY/UBEM VISUALIZATION LANDSCAPE & METHOD TAXONOMY

> SCOPE GUARD — READ FIRST. This is the **framing / taxonomy** task for the whole 3D-viz set. Its job is
> to map the solution space so every downstream prompt scopes cleanly. Answer two things only: (1) **what
> classes of method exist for building an interactive, browser-based 3D visualization of a
> city/neighbourhood energy model** (WebGL-library / geospatial-tiles / CityGML-viewer / game-engine /
> notebook-widget), and (2) **when each class is appropriate** as a function of building count, need for
> geo-referencing, output-coloring demands, and delivery constraints. Do NOT tear down specific tools
> (that is `V02`), do NOT pick the concrete rendering library (that is `V06`), and do NOT specify the
> interchange formats (that is `V03`). See `00_README_3dviz_prompt_set.md` for shared facts, roster,
> conventions.

---

## What this document is

A structured landscape survey of **interactive 3D visualization for urban building energy models**.
OpenUBEM today can only produce **static** 3D (matplotlib axonometric PNGs) and **desktop-CAD** exports
(COLLADA/OBJ/SketchUp) — nothing a user can orbit, filter, or recolour in a browser. Before designing the
viewer we need the field's own map: which *families* of method exist for turning a set of simulated
buildings into a navigable, output-coloured 3D web scene, what each needs as input, at what building count
each stays interactive, and which delivery model each implies. This prompt tells the manager which family
OpenUBEM's proposed "Python → web scene → interactive viewer" approach belongs to, and what its recognized
alternatives are.

## Role

UBEM / geospatial-visualization / web-3D research analyst. Ground the taxonomy in recognized sources: the
**UBEM visualization literature** (ubem.io — Ang, Reinhart et al.; UMI; CEA; the İşeri et al. in-repo
work), the **geospatial-web stack** (OGC **3D Tiles** + **CesiumJS**; **CityGML/CityJSON** viewers;
**MapLibre/Mapbox** fill-extrusion; **kepler.gl/deck.gl**), the **general web-3D libraries** (three.js,
Babylon.js, WebGL/WebGPU), and the **game-engine-to-web** path (Unreal/Unity/PlayCanvas). Distinguish
clearly between *scientific output visualization* (few buildings, high-fidelity per-surface results,
faithful to the model) and *mass city rendering* (thousands of buildings, LOD-streamed, context-heavy) —
they pull the design in different directions and OpenUBEM sits between them.

## Why this matters (so you scope correctly)

The method family determines everything downstream: the data formats (`V03`), the rendering library
(`V06`), the LOD ladder (`V04`), the achievable building count (`V12`), and the delivery model (`V13`). It
also decides whether the viewer can stay **faithful-to-model** and **reproducible/self-contained** (the
two hard constraints) — a heavy GIS-server family fails the second; a naive single-mesh dump fails the
first at scale. OpenUBEM's proposed approach — *emit a web-renderable scene + attributes from the Python
pipeline, view it in a browser* — must be located in this taxonomy and confirmed (or corrected) as the
defensible family for a Python-based, open-source, neighbourhood-scale UBEM.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — The method families for interactive 3D UBEM/city visualization

| Method family | Core idea | Inputs required | Building count it stays interactive at | Geo-referenced? (on a real basemap) | Output/attribute coloring support | Delivery model (static file / static site / server) | Representative source |
|---|---|---|---|---|---|---|---|
| Raw WebGL-library scene (three.js / Babylon.js) |  |  |  |  |  |  |  |
| Geospatial tile-streaming (3D Tiles + CesiumJS) |  |  |  |  |  |  |  |
| Map-GL fill-extrusion (MapLibre / Mapbox / deck.gl / kepler.gl) |  |  |  |  |  |  |  |
| CityGML/CityJSON dedicated viewer (3DCityDB web-map-client, ninja) |  |  |  |  |  |  |  |
| Game-engine-to-web (Unreal / Unity / PlayCanvas WebGL) |  |  |  |  |  |  |  |
| Notebook / dashboard widget (pydeck, plotly, ipygany, PyVista/trame) |  |  |  |  |  |  |  |
| Static image / desktop-CAD (OpenUBEM's current state) | matplotlib axonometric PNG + COLLADA/OBJ/SketchUp export | parsed IDF geometry | n/a (not interactive) | No (recentred local metres) | Per-category colour only, not output-driven | Static PNG / CAD file | `idf_reader/visualizer_adapter.py`, `idf_to_*` |

### Table 2 — Fitness by OpenUBEM need

Mark ✓ / partial / ✗ with a one-line why.

| OpenUBEM need | Raw WebGL lib | 3D Tiles + Cesium | Map-GL extrusion | CityJSON viewer | Game-engine web | Notebook widget |
|---|---|---|---|---|---|---|
| Neighbourhood LOD — surfaces/masses only, hundreds+ buildings |  |  |  |  |  |  |
| Building LOD — surfaces + sub-surfaces (windows) on drill-down |  |  |  |  |  |  |
| Recolour by function (categorical) / population (sequential) / EUI (heat-map) |  |  |  |  |  |  |
| Per-surface output heat-map (solar/irradiance) — the Torino case |  |  |  |  |  |  |
| Placed on a real basemap / geo-referenced |  |  |  |  |  |  |
| Generatable from a Python pipeline |  |  |  |  |  |  |
| Deliverable self-contained / no paid service |  |  |  |  |  |  |

### Table 3 — Fit to OpenUBEM's two hard constraints, per family

| Method family | Faithful-to-model? (renders exactly the pipeline geometry/values, can flag imputed/degraded) | Reproducible + self-contained + open-source (no proprietary engine / paid tiles)? | Expressible as a Python→web-artifact build? | Verdict for OpenUBEM (adopt / adopt-as-option / skip) |
|---|---|---|---|---|
| Raw WebGL library |  |  |  |  |
| 3D Tiles + Cesium |  |  |  |  |
| Map-GL extrusion |  |  |  |  |
| CityJSON viewer |  |  |  |  |
| Game-engine web |  |  |  |  |
| Notebook widget |  |  |  |  |

### Table 4 — The scientific-output vs. mass-city-rendering distinction

| Question | Answer + source |
|---|---|
| Where do UBEM output-visualizers (ubem.io, CEA, Torino heat-map) sit — faithful few-building scientific view, or mass LOD-streamed city? |  |
| At roughly what building count does a single-mesh WebGL scene stop being interactive (needing tiling/instancing)? |  |
| Which family preserves per-surface fidelity (needed for a solar/EUI-per-surface heat-map) vs. only per-building masses? |  |
| Does OpenUBEM's neighbourhood scale (typically how many buildings per cell?) fall in the "single-scene" or the "must-tile" regime? (state the threshold; flag GAP if unknown) |  |

---

## Part C — Synthesis (the family recommendation)

Give: (1) a one-paragraph verdict on **which method family OpenUBEM's proposed Python→web-scene→browser
viewer belongs to**, and whether the field regards it as sound for neighbourhood-scale output
visualization; (2) the **recommended primary family + fallback** for OpenUBEM (e.g. "Map-GL fill-extrusion
for the neighbourhood LOD → raw-WebGL/glTF detail for the building LOD", or "3D Tiles if the scale demands
it"); (3) an explicit statement of **which families the downstream prompts should detail** (confirming or
revising the V02–V15 split); (4) the single most important thing OpenUBEM's current static-only approach
is missing that the field considers table-stakes for an interactive UBEM viewer.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C synthesis.
3. Cite a UBEM/visualization paper or an official spec/library doc for every family claim; separate
   peer-reviewed sources from tool docs.
4. **"Confidence and caveats":** which family's fitness for a Python-based, self-contained, open-source
   neighbourhood UBEM is least evidenced.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Cover all six method families in Table 1** — no "unknown" without saying what evidence would resolve
  it.
- **Explicitly locate OpenUBEM's proposed Python→web-scene approach within the taxonomy.**
- **Respect the two hard constraints** (faithful-to-model, reproducible/self-contained/open-source) when
  judging admissibility.
- **No fabricated precision;** flag GAPs. **Stay on topic** — the *taxonomy of methods and when each
  applies* only, not per-tool teardown (`V02`), the library pick (`V06`), or formats (`V03`).
