# Deep-Research Prompt V04 — LEVEL-OF-DETAIL MODEL (the neighbourhood ↔ building ↔ zone LOD ladder)

> SCOPE GUARD — READ FIRST. This prompt owns **the LOD ladder itself**: what geometry each named LOD shows,
> how it maps onto the CityGML LOD0–4 standard, and how it ties to OpenUBEM's `building`/`floor`/`zone`/
> `auto` **resolution modes**. It is NOT the file format the geometry is serialized in (that is `V03`), and
> NOT the camera/UI mechanics of switching LOD while navigating (that is `V08`). Treat this as the semantic
> definition of "what does each level show and when is a building even capable of showing it" — not the
> format or the interaction. See `00_README_3dviz_prompt_set.md` for shared facts, roster, conventions.

---

## What this document is

The semantic contract for the viewer's detail ladder. The user named two LODs explicitly: **neighbourhood
level — surfaces/masses only, for 3D navigation** and **building level — surfaces + sub-surfaces/windows**.
Separately, OpenUBEM's simulation pipeline already has a **resolution-mode** concept
(`building`/`floor`/`zone`/`auto`, recently implemented per the simulation-Resolution arc) that determines
how much *interior* detail a given building was actually simulated with — a `building`-mode building has no
real zone subdivision to show even if the viewer wanted to display one; a `zone`-mode building does. This
prompt must reconcile the viewer's two named LODs with the CityGML LOD0–4 standard vocabulary, and pin
exactly how the viewer's detail ladder should read (or refuse to read) a building's resolution mode so it
never displays detail the model does not actually have.

## Role

Geospatial-standards / UBEM-geometry analyst. Ground the LOD taxonomy in the **CityGML 3.0 / CityGML 2.0
LOD concept** (OGC standard, LOD0 footprint → LOD1 block/extrusion → LOD2 surfaces+roof shape → LOD3
surfaces+openings/sub-surfaces → LOD4 interior/room-level), its restatement in **CityJSON's LOD0–3.2
scheme**, and how peer 3D-Tiles / CesiumJS practice implements discrete or continuous LOD switching. Cross-
reference the İşeri et al. in-repo resolution-mode work and OpenUBEM's own `simulation-Resolution` design
docs (do not re-derive their content — cite and reuse the mode definitions verbatim).

## Why this matters (so you scope correctly)

Every attribute-binding, coloring, and performance decision downstream depends on which LOD is showing:
`V05` needs to know whether per-zone attributes exist to bind at a given LOD, `V09` needs to know whether a
zone-level colour breakdown is even offerable, and `V12` needs the LOD ladder to know which detail level is
affordable at neighbourhood scale. Most importantly, this is a **faithful-to-model** flashpoint: if the
viewer's "zone LOD" renders a uniform zone grid on a building that was actually simulated in `building`
mode, it fabricates detail the model never computed — a direct violation of the first hard constraint.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — The LOD ladder

| Viewer LOD | Geometry shown | CityGML/CityJSON LOD equivalent | OpenUBEM resolution mode it maps to | Building count feasible at this LOD (order of magnitude) | Source |
|---|---|---|---|---|---|
| Neighbourhood (masses/surfaces only) |  |  |  |  |  |
| Building (surfaces + sub-surfaces / windows) |  |  |  |  |  |
| Zone (interior subdivision, if available) |  |  |  |  |  |

### Table 2 — CityGML/CityJSON LOD0–4 vs. OpenUBEM's two named LODs

| CityGML/CityJSON LOD | Standard definition | Does OpenUBEM's geometry data (IDF surfaces/sub-surfaces) support representing it today? | Which of OpenUBEM's two named LODs (if any) it corresponds to | Source |
|---|---|---|---|---|
| LOD0 (footprint/roof edge) |  |  |  |  |
| LOD1 (block extrusion, no roof shape) |  |  |  |  |
| LOD2 (roof shape + surface differentiation) |  |  |  |  |
| LOD3 (+ openings: windows/doors as separate geometry) |  |  |  |  |
| LOD4 (+ interior/room-level) |  |  |  |  |

### Table 3 — LOD-switching mechanics fitness

| Switching mechanic | How it works | Fit for OpenUBEM's neighbourhood→building drill-down | Fit for a scale-driven fallback (crowded neighbourhood auto-downgrading detail) | Source |
|---|---|---|---|---|
| Discrete swap (load a different asset on click/zoom threshold) |  |  |  |  |
| Continuous/geometric LOD (progressive mesh simplification) |  |  |  |  |
| Tile-based streaming (3D Tiles refinement — ADD/REPLACE) |  |  |  |  |

### Table 4 — Fit to constraints, including faithful-to-model

| Question | Answer + source |
|---|---|
| How should the viewer refuse or flag a zone-level view for a `building`-mode-simulated building (no real zone data exists)? |  |
| Should LOD be purely geometric (what mesh is loaded) or also **data-gated** (what attributes are even offerable at that LOD, tied to resolution mode)? |  |
| Does any peer practice (CityGML LOD, 3D Tiles refinement) generate synthetic in-between detail via mesh simplification that could be mistaken for real simulated detail — and how do they disclose this? |  |
| What is the minimal, honest LOD ladder OpenUBEM can ship given today's data (two real LODs; is a third "zone" LOD viable now or a future gap)? |  |

---

## Part C — Synthesis (the LOD ladder decision)

Give: (1) the **concrete LOD ladder** OpenUBEM should implement now (how many levels, exact geometry per
level, CityGML equivalent cited); (2) the **resolution-mode gating rule** — precisely how a building's
`building`/`floor`/`zone`/`auto` mode constrains which LOD/attributes the viewer may show for it, stated as
an explicit rule the manager can put in a PLAN doc; (3) whether a **zone-level LOD is viable today** or
should be deferred as a documented gap; (4) the **downstream note for `V08`** on what a "drill down" click
must trigger (asset swap vs. re-fetch) given the chosen switching mechanic.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C decision.
3. Cite the CityGML/CityJSON LOD clauses explicitly (spec section numbers) and the OpenUBEM
   simulation-Resolution design doc for the resolution-mode definitions; do not re-derive mode semantics
   from scratch.
4. **"Confidence and caveats":** which LOD-mapping claim is the analyst's own interpretation vs. a directly
   cited standard clause.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **State the CityGML/CityJSON LOD equivalent for every viewer LOD** — no "roughly LOD2-ish" without citing
  the clause.
- **Explicitly tie every LOD level to a resolution mode gate** — this is where faithful-to-model is
  operationalized for detail level; a LOD must never display interior detail a building was not actually
  simulated with.
- **Respect the two hard constraints**, with special weight on faithful-to-model (no fabricated detail on
  drill-down).
- **No fabricated precision;** flag GAPs. **Stay on topic** — the *LOD semantics and resolution-mode tie*
  only, not the interchange format (`V03`) or the click/zoom interaction mechanics (`V08`).
