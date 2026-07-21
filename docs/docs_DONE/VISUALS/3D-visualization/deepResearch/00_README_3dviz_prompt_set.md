# 3D Interactive Visualization — Deep-Research Prompt Set (INDEX)

> READ FIRST. This set is about a **new capability**, not a fix to an existing one: an **interactive,
> browser-based 3D viewer** that lets a user *enter and navigate* the neighbourhoods OpenUBEM simulates
> across multiple cities, inspect them at two levels of detail (**neighbourhood level — surfaces / masses
> only, for 3D navigation**; **building level — surfaces + sub-surfaces / windows**), and **colour the
> scene by attribute** — function/archetype (categorical), population (sequential), and simulation
> **outputs** such as EUI / energy demand / carbon (a heat-map, in the spirit of the
> `fereshtehsabeghi/Torino-3d-heat-mapping` reference and the ubem.io gallery). It is NOT about *how the
> model geometry is generated* (that is the `layoutgenerator/` and `simulation-Resolution/` sets), NOT
> about *which archetype a building becomes* (`input-framework/`), and NOT about the simulation physics.
> It is about the **presentation layer**: taking what the pipeline already produced — real OSM footprints,
> IDF surfaces/sub-surfaces, and per-building/per-surface results — and rendering it as an interactive 3D
> experience in the browser. Run each prompt in your deep-research tool (Gemini Antigravity); save the
> answer beside it as `RESULT_<id>_<slug>.md`. The manager audits each RESULT and only then drafts
> `PLAN_3dviz_implementation.md`.

---

## The exact decision this set must inform

OpenUBEM today can render its buildings only as **static images and desktop-CAD files** — never as an
interactive scene a user can orbit, walk, filter, and recolour in a browser. Concretely, the existing
visualization assets (in the sibling `idf_reader` codebase, the geometry/plotting ancestor of OpenUBEM)
are:

- **Static matplotlib axonometrics** — `visualizer_adapter.py::render_idf_to_base64` renders a single IDF
  to a PNG (4-view NE/SE/SW/NW driver in `idf_reader/main.py`), parsing geometry *directly from the IDF*
  (no eppy/IDD), honouring `GlobalGeometryRules` relative/absolute coords and per-zone origin offsets,
  drawing opaque surfaces then windows in a second pass, 1:1:1 metre aspect. Per-category colours: wall
  `#d4a574`, roof/ceiling `#8b5e3c`, floor `#c0c0c0`, window `#5dade2`, shading translucent green.
- **Neighbourhood axonometrics** — `neighbourhood_morphology.py` renders whole-neighbourhood axonometrics
  and "full-floor" axonometrics (many IDFs at once) to PNG.
- **Desktop-CAD exporters** — `idf_to_collada.py` (COLLADA 1.4.1 `.dae`), `idf_to_obj.py` (Wavefront
  `.obj`+`.mtl`), `idf_to_sketchup.py` (Ruby + `collect_geometry`), all sharing one `collect_geometry`
  grouping (site → building → zone → per-category), units metre, Z-up. These target **SketchUp/Rhino**,
  not the web, and are not interactive.

**None of this is interactive, web-deliverable, or output-driven.** The user wants the equivalent of the
Torino web heat-map and the ubem.io viewers: a user opens a URL (or a self-contained file), sees the
neighbourhood as 3D masses, navigates it, drills into one building to see its windows, and recolours the
whole scene by function, by population, or by a **simulation result** (EUI, hourly demand, carbon,
per-surface solar). This set must decide **how the field builds such a viewer**, **which technology stack
and data formats fit OpenUBEM's Python→static-output pattern**, and **exactly what to reuse from the
existing static/CAD assets vs. build new.**

The proposed shape of the feature — the thing this set must validate, refine, or replace against the
field's practice — is:

> **A pipeline stage that converts each simulated neighbourhood (IDF geometry + OSM footprints +
> per-building/per-surface results) into a web-renderable 3D scene, served through an interactive viewer
> with two LODs (neighbourhood = surfaces/masses only; building = surfaces + sub-surfaces), camera
> navigation, building selection/isolation, and attribute-driven recolouring (categorical function,
> sequential population, diverging/sequential energy-output heat-maps) with legends — deployable as a
> reproducible, self-contained artifact the user can open without proprietary software.**

The set decomposes into: **(a) how the field does it** (`V01`, `V02`), **(b) the data model & interchange
formats** (`V03`–`V05`), **(c) the rendering technology & geo-referencing** (`V06`, `V07`), **(d) the
interaction / UX / coloring** (`V08`–`V10`), and **(e) outputs, scale, deployment, validation, and
concrete asset reuse** (`V11`–`V15`).

| Concern | Prompt(s) | What it must decide |
|---|---|---|
| Solution-space map + peer practice | `V01`, `V02` | the taxonomy of interactive 3D city/UBEM visualization; what shipped tools (ubem.io, CEA, Cesium/3DCityDB, kepler/deck.gl, Torino heat-map, ArcGIS Urban, Speckle) actually render, from what data, with what interactions |
| Scene data model & interchange | `V03`, `V05` | how OpenUBEM geometry + attributes become a web scene (glTF/glb, 3D Tiles, CityJSON, GeoJSON-extrude); how per-building/per-surface attributes bind to geometry |
| Level-of-detail model | `V04` | the neighbourhood (surfaces-only) ↔ building (surface+sub-surface) ↔ zone LOD ladder, its CityGML LOD1–3 mapping, and its tie to the pipeline's `building`/`floor`/`zone` resolution modes |
| Rendering technology + geo | `V06`, `V07` | three.js vs deck.gl vs CesiumJS vs MapLibre vs game-engine; geo-referencing, basemap/terrain, context |
| Interaction / UX / coloring | `V08`, `V09`, `V10` | navigation & selection; thematic coloring + colormaps + legends + accessibility; data-driven UI panels, time-slider, linked charts |
| Outputs, scale, deploy, validate, reuse | `V11`–`V15` | mapping simulation outputs onto geometry; performance at neighbourhood scale; deployment/architecture; accessibility/reproducibility/provenance; **exact reuse of the idf_reader static/CAD assets** |

---

## The prompts

| # | File | What it learns | Priority |
|---|------|----------------|----------|
| V01 | `V01_interactive_3d_city_viz_landscape_prompt.md` | The full solution space: the method families for interactive web 3D city/UBEM visualization (WebGL-library / geospatial-tiles / CityGML-viewer / game-engine / notebook-widget) and when each is appropriate. Scopes every downstream prompt. | **core** |
| V02 | `V02_peer_tool_3d_viewer_teardown_prompt.md` | Tool-by-tool: how ubem.io, CEA, UMI, 3DCityDB web-map-client / Cesium, kepler.gl / deck.gl, the Torino heat-map, ArcGIS Urban, Speckle, and Rhino/Grasshopper web viewers build their interactive 3D — data, stack, LOD, interactions, output-coloring. | **core** |
| V03 | `V03_scene_geometry_interchange_formats_prompt.md` | How OpenUBEM's IDF/OSM geometry becomes a web-renderable scene: glTF/glb vs 3D Tiles vs CityJSON vs extruded-GeoJSON — sizes, LOD support, attribute support, and reuse of the existing `idf_to_collada`/`idf_to_obj` pipeline. | **core** |
| V04 | `V04_level_of_detail_model_prompt.md` | The viewer LOD ladder: neighbourhood (surfaces/masses only) ↔ building (surface + sub-surface/windows) ↔ zone; CityGML LOD1/LOD2/LOD3 mapping; how to tie viewer LOD to the pipeline's `building`/`floor`/`zone` resolution modes and stream the right detail. | high |
| V05 | `V05_attribute_binding_data_schema_prompt.md` | How per-building and per-surface attributes (function/archetype, population, vintage, EUI, end-uses, carbon) attach to geometry and reach the browser — feature IDs, glTF property/`EXT_mesh_features` tables, 3D-Tiles batch tables, GeoJSON properties — and where **population** data would come from. | **core** |
| V06 | `V06_web_render_stack_decision_prompt.md` | The rendering-stack decision: three.js vs deck.gl vs CesiumJS vs Mapbox/MapLibre GL vs Potree vs Unreal/Unity-for-web — capability, geo-referencing, performance at neighbourhood scale, licensing, and fit to OpenUBEM's Python→static-HTML output pattern. | **core** |
| V07 | `V07_georeferencing_basemap_context_prompt.md` | Geo-referencing the scene: placing neighbourhoods on real coordinates (lat/lon → local ENU), terrain, satellite/OSM basemaps, context/neighbour buildings and their shading, and the coordinate-system pitfalls (OpenUBEM renders in recentred local metres today). | medium |
| V08 | `V08_navigation_selection_interaction_prompt.md` | Camera & navigation (orbit/pan/zoom, first-person walkthrough), LOD/level switching (neighbourhood ↔ building ↔ zone), building select / highlight / isolate, section/clipping planes, measurement — the interaction grammar of a UBEM viewer. | high |
| V09 | `V09_thematic_coloring_legends_accessibility_prompt.md` | Attribute-driven recolouring: categorical (function/archetype), sequential (population), sequential/diverging (EUI / energy / carbon heat-maps); classification methods, colormaps, legends, and colour-blind-safe / light-&-dark accessibility. (Grounded in ColorBrewer/viridis/Okabe-Ito directly — the `dataviz` skill referenced in earlier drafts does not exist; V09 audit.) | **core** |
| V10 | `V10_ui_panels_timeslider_linked_charts_prompt.md` | The data-driven UI around the 3D scene: attribute selector, filtering, an hourly/annual **time-slider**, tooltips/pop-ups, and dashboards that link 2-D charts to the 3-D scene (brushing & linking). | medium |
| V11 | `V11_simulation_output_visualization_prompt.md` | Mapping EnergyPlus **outputs** onto the scene: annual EUI / hourly demand / carbon / comfort per building, per-surface solar-irradiance heat-maps, and temporal animation — the direct Torino-heat-map analogue, grounded in what OpenUBEM emits (`05_results.*` — EUI/end-uses/carbon — + `05_neighbourhood_summary.json`; **not** `eui_summary.json`, which does not exist — V11 audit). | **core** |
| V12 | `V12_performance_scale_prompt.md` | Rendering a whole neighbourhood (hundreds–thousands of buildings) interactively in-browser: instancing, tiling / 3D-Tiles streaming, mesh simplification per LOD, draw-call budgets, and low-end/mobile targets. | high |
| V13 | `V13_deployment_pipeline_architecture_prompt.md` | How the viewer is produced and served: the Python→interchange→viewer build, static-site vs server, self-contained single-file HTML (matching OpenUBEM's outputs discipline) vs streamed tiles, and hosting/offline options. | medium |
| V14 | `V14_accessibility_reproducibility_provenance_prompt.md` | Faithful representation & trust: colour-blind-safe palettes, provenance of what is shown (which resolution mode, which inputs were imputed / low-confidence), reproducible builds, export/share, and validating that the 3-D view does not misrepresent the model. | medium |
| V15 | `V15_openubem_asset_reuse_migration_prompt.md` | The concrete reuse map: exactly what to lift from the `idf_reader` assets (`visualizer_adapter`, `idf_to_collada`/`idf_to_obj`/`idf_to_sketchup` `collect_geometry`, `neighbourhood_morphology` axonometrics) into OpenUBEM's web viewer, what is dead-end, and the remaining gap. | **core** |

> **Load-bearing core: `V01 + V02 + V03 + V05 + V06 + V09 + V11 + V15`.** These decide whether the
> proposed viewer is the field's convention, fix the data formats and rendering stack, lock the coloring
> system, ground the output heat-maps in what OpenUBEM emits, and inventory exactly what existing code we
> reuse. Run them first. Run `V04`/`V08`/`V12` next to pin the LOD ladder, interaction grammar, and scale
> strategy. Treat `V07`/`V10`/`V13`/`V14` as the depth tier, run once the MVP stack is chosen.

---

## Shared facts (all prompts assume these)

Grounded in `idf_reader/visualizer_adapter.py`, `idf_reader/idf_to_collada.py`, `idf_reader/idf_to_obj.py`,
`idf_reader/idf_to_sketchup.py`, `idf_reader/neighbourhood_morphology.py`, and OpenUBEM's pipeline outputs
(verified against code 2026-07-02). Every prompt pre-fills its own **OpenUBEM-current** row from this
list — do not re-derive it.

- **OpenUBEM simulates neighbourhoods across multiple cities** (NYC, LA, Boston, and Torino-style OSM
  cells). Each **building is one IDF / one EnergyPlus run**; a **neighbourhood is many IDFs**. The viewer's
  job is to present a *neighbourhood* (many buildings) with drill-down to one building.
- **The only 3-D OpenUBEM has today is static + desktop-CAD**, all in the `idf_reader` ancestor codebase:
  - Static matplotlib axonometric PNGs (`visualizer_adapter.py`; 4-view driver in `idf_reader/main.py`),
    geometry parsed *directly from the IDF* (no eppy/IDD), honouring `GlobalGeometryRules` relative/absolute
    + per-zone origin offsets; opaque-surfaces-then-windows two-pass; 1:1:1 metre aspect.
  - Neighbourhood + full-floor axonometrics (`neighbourhood_morphology.py` — **correction (V15 audit
    2026-07-02):** its *default* entry point `generate_all()` is a CSV/HTML **metrics** dashboard
    (density/FAR/typology/WWR/HVAC/solar-access); the 3-D axonometric renderers are separate non-default
    functions. This file is more valuable to `V05` (attribute data) than to rendering reuse.).
  - CAD exporters to COLLADA `.dae`, Wavefront `.obj`+`.mtl`, SketchUp `.skp` (Ruby) sharing one
    `collect_geometry` (site→building→zone→category), units metre, Z-up. **Correction (V15 audit
    2026-07-02):** `collect_geometry` is not a standalone module — it is defined **inside
    `idf_to_sketchup.py:726`** (a "SketchUp Ruby exporter") and *imported* by `idf_to_collada.py`/
    `idf_to_obj.py`; and the per-category colour convention below is duplicated across **three**
    independently-maintained dicts with confirmed drift (e.g. window α 0.70 vs 0.55), not one source of truth.
  - **There is no interactive, web, or output-driven viewer** — that is the entire gap this set addresses.
- **Geometry primitives available per building:** surfaces (`wall`/`roof`/`ceiling`/`floor`), sub-surfaces
  (`window`/`door`), and shading, all with 3-D vertex lists. The **two LODs the user named** map cleanly:
  neighbourhood-level = **surfaces only** (walls+roofs, no windows); building-level = **surfaces +
  sub-surfaces** (windows/doors shown).
- **Per-category colour convention already in code** (reuse or supersede): wall `#d4a574`, roof/ceiling
  `#8b5e3c`, floor `#c0c0c0`, window `#5dade2` (edge `#1a6fa8`, α 0.70), shading translucent green.
  Units **metre, Z-up** (matches EnergyPlus + SketchUp).
- **Attributes available per building** for coloring: archetype / **function** (DOE prototype name),
  **vintage / `year_built`**, `num_floors`, `footprint_area_m2`, and simulation **outputs** —
  the Step-5 result tables. **Correction (V11 audit 2026-07-02): there is no `eui_summary.json`.** The real
  exports are per-building `05_results.gpkg` / `05_results.geojson` / `05_results.csv` (**EUI field
  `total_eui_kwh_m2`**, per-building energy **end-uses**, **carbon**) plus `05_neighbourhood_summary.json`.
  Results are **annual + 8760 hourly** (a time-slider is therefore feasible).
- **Population is a *requested* coloring attribute that OpenUBEM does not currently store per building** —
  `V05` must establish where it would come from (census / OSM `building:levels`+area heuristics / dwelling-
  unit counts from the residential archetypes) and flag it as a **new data dependency**, not an existing
  field.
- **Geo-referencing is currently lost in the render.** The static renderers work in **recentred local
  metres**, not lat/lon; the OSM footprints upstream (`footprint_collector`) *do* carry real coordinates.
  A web viewer that places neighbourhoods on a basemap must recover that geo-reference (`V07`).
- **Resolution modes** (`building` / `floor` / `zone` / `auto`): the geometry's interior detail depends on
  the mode the building was simulated in. The viewer's LOD ladder should be *aware* of, and ideally
  *reflect*, this (`V04`) — e.g. a `zone`-mode building can show per-zone coloring; a `building`-mode one
  cannot.
- **Reference exemplars the user named:** `github.com/fereshtehsabeghi/Torino-3d-heat-mapping` (a
  web-browser 3-D per-building heat-map) and **ubem.io** (the UBEM.io gallery of city energy models).
  Treat these as first-class peers alongside the tool roster.
- **OpenUBEM is Python + static outputs.** The pipeline is Python; figure/artifact outputs go to
  `openubem/outputs/` (flat, one findable place). Any recommended viewer must be *generatable from Python*
  and deliverable as a web artifact — flag anything that needs a live paid service, a heavy GIS server, or
  a proprietary engine to even open.

## Two hard constraints (repeat in every recommendation)

1. **Faithful to the model — no invented geometry or values.** The viewer renders **exactly** what the
   pipeline produced: the real OSM footprints, the real IDF surfaces/sub-surfaces, the real simulation
   outputs. It must not fabricate geometry, silently smooth or decimate in a way that misrepresents the
   building, or interpolate a colour value that implies data the model does not have. Where an input was
   **imputed** or the **resolution was degraded**, the viewer must be *able to flag it* (ties to the
   `input/imputation/` and `simulation-Resolution/` arcs). A pretty view that lies about the model is a
   non-starter — say so.
2. **Reproducible, self-contained, open-source-deliverable.** The viewer must be produced
   **deterministically from the pipeline outputs** (Python → interchange format → viewer), and be
   buildable + hostable **without proprietary engines or paid services** — ideally as a self-contained
   artifact the user can open directly (echoing the outputs-discipline "one place the user can actually
   find" rule). Flag any stack that imposes vendor lock-in or a paid tile/hosting dependency, since that
   breaks OpenUBEM's open-source mission.

## Source / tool roster (use across prompts where relevant)

**UBEM/BEM viewers & platforms:** ubem.io (the UBEM.io generator + gallery) · City Energy Analyst / CEA
dashboard · UMI (Dogan & Reinhart) + its Rhino/WebGL outputs · CitySim / SimStadt · AutoBEM/AutoBEM-Geo
web outputs (ORNL) · the İşeri et al. in-repo UBEM work. **Geospatial 3-D web stacks:** CesiumJS + 3D
Tiles · 3DCityDB + its web-map-client · MapLibre GL / Mapbox GL JS (fill-extrusion + custom layers) ·
kepler.gl / deck.gl (Uber/vis.gl) · Giraffe / ArcGIS Urban / ArcGIS API for JavaScript. **General 3-D web
libraries & engines:** three.js · Babylon.js · regl/raw-WebGL/WebGPU · Potree (point clouds) · Unreal /
Unity WebGL / PlayCanvas. **Data formats & standards:** glTF 2.0 / `.glb` (+ `EXT_mesh_features`,
`EXT_structural_metadata`) · OGC 3D Tiles (1.0/1.1) · CityGML / **CityJSON** (LOD0–LOD4) · GeoJSON +
`fill-extrusion` · IFC/BCF · COLLADA `.dae` / Wavefront `.obj` (OpenUBEM's current CAD exports). **Design /
color:** ColorBrewer, matplotlib/`viridis` family. **Correction (V09 audit 2026-07-02): there is no
`dataviz` skill / `references/palette.md` in this project** (earlier drafts referenced one — it does not
exist on disk); the coloring spec is grounded in ColorBrewer/viridis/Okabe-Ito directly, and a house palette
is a `V09`/PLAN decision, not an existing asset to align to. **The user's named exemplars:** `fereshtehsabeghi/Torino-3d-heat-mapping` · ubem.io.

## Conventions for every answer (enforced by each prompt)

1. **Lead with the filled tables**; prose after. Empty / "TBD" cells are failures.
2. Every tool / format / technique carries a **named, dated source** — a peer-reviewed UBEM/visualization
   paper (author, venue, year), a standard/spec (OGC 3D Tiles, glTF, CityGML clause), official library
   docs, or the named exemplar's repo/site. Blogs / vendor marketing pages are last resort, labelled.
3. **Always compare against OpenUBEM's actual current behaviour** (given inline in each prompt from the
   Shared facts above) — say explicitly whether peer practice matches OpenUBEM's static/CAD status quo, is
   more capable, or is heavier than OpenUBEM needs.
4. **No fabricated precision.** If a value (a file size, a frame-rate, a building count) is your synthesis,
   say so. If unpublished, write **"GAP — needs manager decision"** + the closest defensible default and
   its source.
5. **Map onto OpenUBEM's exact reality** — one-IDF-per-building, many-IDFs-per-neighbourhood, the two LODs
   (surfaces-only vs surfaces+sub-surfaces), the `wall/roof/floor/window/shading` categories, the
   `building/floor/zone/auto` resolution modes, `05_results.*` / end-uses / carbon outputs, Python →
   static-artifact delivery — not generic "3-D web dev" in the abstract.
6. **Respect the two hard constraints** in every recommendation: faithful-to-model and
   reproducible/self-contained/open-source. A stack or technique that violates either is a non-starter —
   say so.
7. **Stay on topic per prompt** — do not re-litigate model geometry generation (`layoutgenerator/`),
   resolution-mode selection (`simulation-Resolution/`), archetype classification (`input-framework/`), or
   missing-input imputation (`input/imputation/`). This set is the **presentation / visualization layer**
   only.

---

*OpenUBEM — 3D interactive-visualization deep-research set. Markdown only; binding specs remain
`docs/docs_main/`. Grounded in the `idf_reader` static/CAD visualization assets, OpenUBEM's per-building
IDF + results outputs, and the Torino-3d-heat-mapping / ubem.io exemplars. 2026-07-02.*
