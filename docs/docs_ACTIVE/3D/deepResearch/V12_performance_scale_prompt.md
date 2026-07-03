# Deep-Research Prompt V12 — PERFORMANCE & SCALE (interactive rendering of a whole neighbourhood)

> SCOPE GUARD — READ FIRST. This prompt owns **making hundreds-to-thousands of buildings render
> interactively in-browser** — instancing, tiling/3D-Tiles streaming, mesh simplification per LOD, draw-call
> budgets, and low-end/mobile targets. It is NOT the LOD *semantics* (that is `V04` — assume its ladder and
> ask only "can we render it fast"), and NOT the rendering-stack pick itself (that is `V06` — reference its
> ceilings, don't re-decide the stack). See `00_README_3dviz_prompt_set.md` for shared facts, roster,
> conventions.

> RESEARCH BUDGET — KEEP IT BOUNDED. Run this cheaply, in a SINGLE pass. Hard caps: **≤6 web searches and
> ≤10 page fetches, total.** After that pass, fill the required tables + Part C and STOP — do not iterate
> toward "comprehensive." Deliverable is the tables + Part C only: no preamble, no literature review beyond
> what the cells and synthesis need. Any cell you cannot fill within budget = mark it `GAP`; do not spend
> extra searches chasing one cell. **Do NOT spawn sub-agents or invoke skills to do this research** — run
> the searches yourself with plain web-search/fetch only; delegating to agents or skills multiplies token
> spend. If run by a Sonnet employee: model Sonnet, effort medium.

---

## What this document is

The scale-engineering decision for a viewer whose subject is, by definition, a **neighbourhood** — many
IDFs, each with a full set of walls/roofs/floors/windows/shading surfaces. OpenUBEM's static renderer has no
scale problem today because it never has to stay interactive: `neighbourhood_morphology.py` renders a whole
neighbourhood to a single PNG once, off-line, at whatever cost that takes. A browser viewer must instead hit
an interactive frame rate while a user orbits, recolours, and drills into a neighbourhood that could be
tens, hundreds, or (per the shared facts) potentially thousands of buildings. This prompt decides the
concrete techniques and thresholds that keep that interactive, without silently distorting or dropping
geometry.

## Role

Real-time-rendering / geospatial-performance-engineering analyst. Ground every technique claim in
established real-time-graphics practice: **GPU instancing** (glTF `EXT_mesh_gpu_instancing`, WebGL
instanced-draw calls), **3D Tiles streaming and refinement** (OGC 3D Tiles spec — tileset hierarchies,
ADD/REPLACE refinement, screen-space-error-driven loading), **mesh simplification/decimation** algorithms
(quadric-error-metric simplification and its use in progressive/LOD mesh pipelines), **frustum and occlusion
culling** (standard WebGL/three.js/CesiumJS practice), and any published performance benchmark for
neighbourhood/city-scale WebGL rendering (e.g. published 3D Tiles or CityGML-at-scale case studies).

## Why this matters (so you scope correctly)

A viewer that looks great on a 20-building demo and grinds to a halt (or silently drops buildings) on a
real 500-building cell is not shippable — and OpenUBEM's own no-silent-caps discipline (never silently
truncate a result set) applies here just as much as it does to the simulation pipeline. This prompt must be
explicit about which techniques are lossless engineering optimizations (instancing, culling — free
performance, no geometry distortion) versus which are lossy simplifications that risk violating
faithful-to-model, and must never let a technique quietly drop or degrade a building without that being
logged and surfaced to the user.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Scale techniques

| Technique | What it buys | Cost (implementation complexity / geometry fidelity trade-off) | Fit for OpenUBEM's neighbourhood LOD (masses-only) vs. building LOD (detailed) | Source |
|---|---|---|---|---|
| GPU instancing (repeated geometry, e.g. identical window units) |  |  |  |  |
| Batching (merge draw calls across static geometry) |  |  |  |  |
| 3D-Tiles streaming (load only what's in view, at the needed detail) |  |  |  |  |
| Mesh decimation/simplification per LOD |  |  |  |  |
| Frustum + occlusion culling |  |  |  |  |

### Table 2 — Building-count regimes

| Regime | Recommended technique(s) | Recommended stack alignment (cross-ref `V06`) | Expected interactive frame-rate class (rough order of magnitude, flag as estimate) | Source |
|---|---|---|---|---|
| Tens of buildings |  |  |  |  |
| Hundreds of buildings |  |  |  |  |
| Thousands of buildings |  |  |  |  |

### Table 3 — Faithful-to-model tension — which simplifications are off-limits

| Technique | Does it alter geometry a user could mistake for the real simulated shape? | Does it alter or hide a colour-encoded value? | Verdict (safe to use freely / use only at neighbourhood LOD / never use) | Source |
|---|---|---|---|---|
| Mesh decimation on a building being colour-heat-mapped |  |  |  |  |
| Impostor/billboard replacement at extreme distance |  |  |  |  |
| Culling a building entirely out of the frame |  |  |  |  |
| Merging distinct buildings into one batched mesh for draw-call reduction |  |  |  |  |

### Table 4 — Budgets and mobile target

| Metric | Target/budget | Source |
|---|---|---|
| Draw calls per frame (desktop target) |  |  |
| Triangle count per frame (desktop target) |  |  |
| Memory footprint ceiling (desktop browser tab) |  |  |
| Mobile/low-end target (if in scope — state whether OpenUBEM should target mobile at all) |  |  |

---

## Part C — Synthesis (the scale strategy)

Give: (1) the **recommended technique stack** for OpenUBEM's realistic neighbourhood sizes (state the
regime from Table 2 that OpenUBEM's actual cells fall into, citing the building-count figures the manager
already has, or flag as GAP if unknown to the researcher); (2) an explicit **"never silently drop a
building" rule** — how culling/streaming must be logged or surfaced (e.g. a visible "N buildings outside
view" indicator) rather than quietly vanishing data, consistent with OpenUBEM's no-silent-caps discipline;
(3) the **off-limits list** from Table 3 stated as a hard rule; (4) the single **biggest scale risk** for
OpenUBEM's specific geometry (e.g. high per-building surface count from detailed sub-surfaces) and its
mitigation.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C strategy.
3. Cite the 3D Tiles spec, glTF instancing extension spec, and any published city-scale WebGL performance
   benchmark for every numeric claim; separate cited benchmarks from your own estimates.
4. **"Confidence and caveats":** which frame-rate/building-count claim is a rough estimate vs. a
   benchmarked figure.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **State explicitly, per technique, whether it can silently drop or distort buildings** — and if so,
  mandate a visible disclosure mechanism (no silent caps).
- **Separate lossless techniques (instancing, culling, streaming) from lossy ones (decimation, impostors)**
  and give a clear verdict on where lossy techniques are/aren't acceptable given faithful-to-model.
- **Tie the recommendation to a concrete building-count regime**, not a generic "use LOD."
- **No fabricated precision;** flag GAPs (especially frame-rate numbers). **Stay on topic** — the
  *performance/scale engineering* only, not the LOD semantics (`V04`) or the stack pick (`V06`).
