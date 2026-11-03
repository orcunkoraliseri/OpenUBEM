# Deep-Research Prompt V08 — NAVIGATION, SELECTION & INTERACTION GRAMMAR

> SCOPE GUARD — READ FIRST. This prompt owns the **interaction grammar** of the viewer: camera/navigation
> modes (orbit/pan/zoom, first-person walkthrough), LOD/level switching triggers (neighbourhood ↔ building ↔
> zone), building select/highlight/isolate, section/clipping planes, and measurement. It is NOT the UI
> panels/time-slider/linked-chart layer around the scene (that is `V10`), and NOT the coloring system (that
> is `V09`). Treat this as "what the mouse/keyboard/touch does to the camera and the selection state" only.
> See `00_README_3dviz_prompt_set.md` for shared facts, roster, conventions.

> RESEARCH BUDGET — KEEP IT BOUNDED. Run this cheaply, in a SINGLE pass. Hard caps: **≤6 web searches and
> ≤10 page fetches, total.** After that pass, fill the required tables + Part C and STOP — do not iterate
> toward "comprehensive." Deliverable is the tables + Part C only: no preamble, no literature review beyond
> what the cells and synthesis need. Any cell you cannot fill within budget = mark it `GAP`; do not spend
> extra searches chasing one cell. **Do NOT spawn sub-agents or invoke skills to do this research** — run
> the searches yourself with plain web-search/fetch only; delegating to agents or skills multiplies token
> spend. If run by a Sonnet employee: model Sonnet, effort medium.

---

## What this document is

The interaction specification for a viewer that today has **zero interactivity** — OpenUBEM's only 3D
output is a static matplotlib PNG (fixed 4-view NE/SE/SW/NW axonometric) or a desktop-CAD file opened in
external software (SketchUp/Rhino), where navigation happens outside OpenUBEM entirely. This prompt defines
the interaction grammar the new in-browser viewer must implement: how a user orbits/pans/zooms a
neighbourhood of masses, drills into one building to see its windows (crossing the `V04` LOD boundary),
selects and isolates a single building or surface, cuts a section through a building, and (optionally)
measures. It must ground each interaction in what the `V06`-recommended stack can actually expose as an
API, not invent capabilities the stack lacks.

## Role

3D-interaction / UX-for-geospatial-scenes analyst. Ground the interaction-pattern claims in recognized
practice: **CesiumJS** camera/entity-picking APIs, **MapLibre/Mapbox GL** `queryRenderedFeatures` + fly-to
camera APIs, **three.js** `OrbitControls`/`PointerLockControls`/raycasting-based picking, established
**BIM/AEC-viewer conventions** for section planes (Autodesk Forge Viewer, Speckle, IFC.js), and the peer
tools already catalogued in `V02` (ubem.io, CEA, Torino heat-map, 3DCityDB web-map-client) for what
interactions they actually ship.

## Why this matters (so you scope correctly)

The interaction grammar is what turns a "renderable scene" into a tool a user can actually explore — without
it, `V03`–`V07`'s work is just a picture. It is also directly bounded by `V06`'s stack pick: an interaction
this prompt recommends that the chosen stack cannot support (e.g. true section-cut clipping in a
tile-streamed CesiumJS scene) must be flagged as infeasible, not prescribed anyway. Priority matters too —
not every interaction is MVP; this prompt must separate must-have navigation from nice-to-have measurement
tooling.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Interaction inventory

| Interaction | What it does | Peer-tool precedent (cite `V02` findings or a named tool) | Priority for MVP (must-have / should-have / defer) | Source |
|---|---|---|---|---|
| Orbit/pan/zoom camera |  |  |  |  |
| First-person walkthrough |  |  |  |  |
| Neighbourhood → building LOD drill-down (click/zoom trigger) |  |  |  |  |
| Building → neighbourhood zoom-out |  |  |  |  |
| Select/highlight a single building |  |  |  |  |
| Isolate a building (hide/dim the rest) |  |  |  |  |
| Select/highlight a single surface (wall/window) |  |  |  |  |
| Section/clipping plane through a building |  |  |  |  |
| Measurement (distance/area on the scene) |  |  |  |  |

### Table 2 — Camera/navigation mode fitness

| Mode | Best for | Weakness at OpenUBEM's neighbourhood scale (hundreds+ buildings) | Supported natively by the `V06`-class stacks (state which) | Source |
|---|---|---|---|---|
| Orbit (target-locked) |  |  |  |  |  |
| Free-fly / first-person walkthrough |  |  |  |  |  |
| Map-tilt (2.5D pitch/bearing, MapLibre/Mapbox style) |  |  |  |  |  |

### Table 3 — Selection & isolation mechanics

| Question | Answer + source |
|---|---|
| How does picking work at neighbourhood scale (per-object ID picking vs. GPU colour-picking vs. tile feature-query) and does it scale to hundreds of buildings without a frame-rate hit? |  |
| How does "isolate" interact with the LOD ladder — does isolating a building auto-trigger the `V04` drill-down to building LOD, or are they independent actions? |  |
| Can a surface (not just a building) be individually selectable given the geometry format from `V03` (does it carry per-surface feature IDs)? |  |
| What is the peer-tool precedent for isolate/highlight in a UBEM context (cite `V02`)? |  |

### Table 4 — Fit to constraints and the chosen stack

| Question | Answer + source |
|---|---|
| Which interactions does the `V06`-recommended stack support natively vs. require custom implementation for? |  |
| Does any interaction risk implying false precision (faithful-to-model) — e.g. a measurement tool reporting a dimension more precise than the source geometry actually is? |  |
| Are any interactions blocked by the reproducible/self-contained constraint (e.g. a picking service requiring a server round-trip)? |  |
| What is the minimal MVP interaction set OpenUBEM should ship first? |  |

---

## Part C — Synthesis (the interaction grammar spec)

Give: (1) the **MVP interaction set** — the must-have list from Table 1 with a one-line implementation note
each, tied to the `V06` stack's actual API; (2) the **drill-down trigger design** — exactly what user action
crosses from neighbourhood LOD to building LOD and back (click, zoom-threshold, explicit UI button — commit
to one); (3) an explicit **deferred list** with the reason (stack limitation, low value, or scale risk); (4)
any interaction that the chosen stack **cannot** do, flagged for `V10`/`V12` to design around.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C spec.
3. Cite the stack's official API docs (CesiumJS/MapLibre/three.js) and the `V02` peer-tool findings for
   every interaction-precedent claim.
4. **"Confidence and caveats":** which interaction's feasibility at neighbourhood scale is least evidenced
   (no working example found).
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Every interaction in Table 1 must get an explicit MVP priority** — no interaction left unranked.
- **Ground picking/selection feasibility in the actual `V06`-recommended stack's API**, not a generic "any
  WebGL app can do this."
- **Flag any interaction that risks implying false precision** (faithful-to-model).
- **No fabricated precision;** flag GAPs. **Stay on topic** — the *camera/selection/interaction grammar*
  only, not the UI panels/time-slider (`V10`) or the coloring system (`V09`).
