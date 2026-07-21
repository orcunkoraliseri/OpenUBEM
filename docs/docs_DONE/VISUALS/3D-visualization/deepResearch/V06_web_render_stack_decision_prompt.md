# Deep-Research Prompt V06 — WEB-RENDER STACK DECISION (which library/engine OpenUBEM's viewer should be built on)

> SCOPE GUARD — READ FIRST. This prompt makes **one decision**: the rendering library/engine the viewer is
> built on. Deliver a sourced, weighted comparison of the candidate stacks against OpenUBEM's exact needs
> and constraints, ending in a single recommended primary stack + fallback. It is NOT the abstract method
> taxonomy (`V01`), NOT the peer-tool teardown (`V02`), NOT the interchange-format choice (`V03` — assume
> the scene arrives as glTF/3D-Tiles/GeoJSON as V03 decides), and NOT geo-referencing detail (`V07`). See
> `00_README_3dviz_prompt_set.md` for shared facts, roster, conventions.

---

## What this document is

The load-bearing technology decision for the whole viewer. OpenUBEM must pick a browser rendering stack
that (a) shows a **neighbourhood of hundreds+ buildings** as surfaces/masses and drills into **one building
with sub-surfaces**, (b) recolours the scene by **function / population / energy output** with legends,
(c) can sit on a **real basemap** (geo-referenced), (d) is **generatable from a Python pipeline** and
**deliverable self-contained / open-source with no paid service**. The candidates span three tiers:
geospatial (CesiumJS+3D-Tiles, MapLibre/Mapbox GL, deck.gl/kepler.gl), general web-3D (three.js,
Babylon.js), and game-engine-to-web (Unity/Unreal/PlayCanvas). This prompt weighs them and picks.

## Role

Web-3D / geospatial-visualization engineering analyst. Ground every capability claim in official library
documentation, the OGC specs (3D Tiles, glTF), a benchmark, or a peer tool's usage. Be concrete about
**licensing** (Cesium Ion vs. open CesiumJS; Mapbox GL JS v2+ proprietary licence vs. MapLibre GL fork;
deck.gl/three.js/Babylon MIT-style), **basemap/tile costs** (paid Mapbox/Cesium-Ion tiles vs. free
MapLibre + OSM/MapTiler), and **what breaks the self-contained/offline delivery** OpenUBEM wants. Do not
hand-wave "any of them works" — force a ranked decision.

## Why this matters (so you scope correctly)

This choice cascades into `V03` (formats the stack ingests), `V04` (how LOD is expressed), `V08`
(interaction APIs available), `V11` (per-surface heat-map feasibility), `V12` (scale ceiling), and `V13`
(delivery). A wrong pick — e.g. Mapbox GL JS v2 (proprietary licence + paid tiles) or a game engine
(huge WASM bundle, not Python-native) — violates the reproducible/open-source constraint from day one.
The manager needs a defended primary + fallback, not a menu.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Candidate stacks vs. OpenUBEM capabilities

| Stack | Neighbourhood masses (hundreds+ bldgs) | Building sub-surfaces / windows detail | Per-building recolour (categorical + heat-map) | Per-surface heat-map (solar) | Geo-referenced on a basemap | Max interactive building count (order of magnitude) | Source |
|---|---|---|---|---|---|---|---|
| CesiumJS (+ 3D Tiles) |  |  |  |  |  |  |  |
| MapLibre GL JS |  |  |  |  |  |  |  |
| Mapbox GL JS (v2+) |  |  |  |  |  |  |  |
| deck.gl / kepler.gl |  |  |  |  |  |  |  |
| three.js |  |  |  |  |  |  |  |
| Babylon.js |  |  |  |  |  |  |  |
| Game engine → WebGL (Unity/Unreal/PlayCanvas) |  |  |  |  |  |  |  |

### Table 2 — Licensing, cost & delivery (the reproducibility constraint)

| Stack | Licence | Requires a paid tile/hosting service to function? | Works fully offline / self-contained? | Bundle weight (light / heavy / very heavy) | Python-side generation story (does a Python lib emit for it?) | Source |
|---|---|---|---|---|---|---|
| CesiumJS |  |  |  |  |  |  |
| MapLibre GL JS |  |  |  |  |  |  |
| Mapbox GL JS (v2+) |  |  |  |  |  |  |
| deck.gl / kepler.gl |  |  |  |  |  |  |
| three.js |  |  |  |  |  |  |
| Babylon.js |  |  |  |  |  |  |
| Game engine → WebGL |  |  |  |  |  |  |

### Table 3 — Interaction & data-binding APIs (feeds V08/V09/V10)

| Stack | Picking / selection API (click a building/surface) | Per-feature attribute → colour (data-driven styling) | Runtime restyle without rebuild (switch attribute live) | Section/clipping planes | Camera modes (orbit + first-person walk) | Source |
|---|---|---|---|---|---|---|
| CesiumJS |  |  |  |  |  |  |
| MapLibre GL JS |  |  |  |  |  |  |
| deck.gl |  |  |  |  |  |  |
| three.js |  |  |  |  |  |  |
| Babylon.js |  |  |  |  |  |  |

### Table 4 — Fit to OpenUBEM's two hard constraints

| Question | Answer + source |
|---|---|
| Which stacks keep the viewer faithful-to-model (render exact geometry/values, no lossy simplification forced)? |  |
| Which stacks are fully open-source + self-contained + free-to-host (no Cesium Ion / Mapbox token needed)? |  |
| Which has the cleanest Python→artifact build (a maintained Python emitter or trivial JSON/glTF handoff)? |  |
| Is a single stack enough, or is a **hybrid** (e.g. MapLibre for neighbourhood + three.js/glTF for building drill-down) the field's pattern? |  |

---

## Part C — Synthesis (the stack decision)

Give: (1) the **single recommended primary stack** for OpenUBEM's MVP viewer, with the 2–3 decisive
reasons (constraint fit first); (2) the **fallback / hybrid** if the primary hits a wall (e.g. scale, or
per-surface heat-map fidelity); (3) an explicit **"do not use"** list with the disqualifying reason
(licence, paid tiles, bundle weight, no Python path); (4) the **downstream implications** — which formats
`V03` should target for this stack, and any interaction from Table 3 the stack *cannot* do that `V08`/`V10`
must design around.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C decision.
3. Cite official docs / licence text / a spec / a benchmark for every capability and licensing claim;
   separate measured/benchmarked numbers from your synthesis.
4. **"Confidence and caveats":** which stack's neighbourhood-scale performance claim is least evidenced.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Force a ranked decision** — a primary + fallback, not "any of these works."
- **State licence + paid-service dependency explicitly for every stack** — this is the reproducibility
  constraint and a Mapbox-GL-v2 / Cesium-Ion trap.
- **Address the Python→artifact generation path for the recommended stack** — OpenUBEM is Python; a stack
  with no emission path is a liability, say so.
- **No fabricated precision;** flag GAPs (especially building-count ceilings — cite a benchmark or mark
  GAP). **Stay on topic** — the *rendering stack pick* only, not formats (`V03`) or geo-referencing (`V07`).
