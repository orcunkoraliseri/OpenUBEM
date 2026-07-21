# RESULT V12 — Performance & Scale (interactive rendering of a whole neighbourhood)

> Research budget used: **6/6 web searches, 9/10 page fetches** (2 fetch attempts failed — one 3D-Tiles OGC
> HTML page exceeded content-size limit, one QEM ISPRS PDF was unreadable binary — superseded by other
> sources for the same facts, no re-spend). No sub-agents or skills invoked. Single pass, as required.

---

## Table 1 — Scale techniques

| Technique | What it buys | Cost (implementation complexity / geometry fidelity trade-off) | Fit for OpenUBEM's neighbourhood LOD (masses-only) vs. building LOD (detailed) | Source |
|---|---|---|---|---|
| GPU instancing (repeated geometry, e.g. identical window units) | Renders many copies of one mesh (e.g. a repeated window unit, a repeated floor-plate) in a **single draw call** via per-instance `TRANSLATION`/`ROTATION`/`SCALE` accessors; the single biggest lever against draw-call count for repeated geometry. Lossless: the underlying mesh is not altered, only re-placed. | Low-medium complexity (glTF `EXT_mesh_gpu_instancing`, Khronos-ratified, widely supported in three.js/Babylon.js exporters/loaders). Loses per-instance material variation and individual instance animation (stated limitation of the spec) — not a concern for static building geometry. No fidelity loss to shape. | **Building LOD**: strong fit — a repeated window/mullion unit across a facade is exactly the "identical geometry repeated many times" case the extension targets. **Neighbourhood LOD**: weaker fit — masses are mostly *not* identical (different footprints/heights per building), though instancing still helps for literally-repeated building types (e.g. rowhouse blocks) if OpenUBEM ever has them. | Khronos Group, `EXT_mesh_gpu_instancing` extension README, ratified (Complete, Ratified by Khronos Group), KhronosGroup/glTF repo, `main` branch (accessed 2026-07-02): https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Vendor/EXT_mesh_gpu_instancing/README.md |
| Batching (merge draw calls across static geometry) | Merges multiple *distinct* static meshes into one buffer/draw call to cut draw-call overhead, independent of whether the meshes are identical. Lossless at the geometry level (same triangles, same positions) but **can destroy per-object identity** unless per-vertex/per-primitive IDs are preserved (e.g. via `EXT_mesh_features`/batch-table style feature IDs). | Medium complexity; the risk is losing the ability to pick/select/recolour an individual building once its geometry is baked into a shared buffer — must retain feature-ID attributes to stay selectable and colourable, which is a hard OpenUBEM requirement (attribute-driven recolouring per building, per V09/V05). | **Neighbourhood LOD only, and only with feature IDs preserved**: batching static wall/roof geometry across many buildings to cut draw calls is reasonable at the masses-only LOD *if* per-building feature IDs ride along for selection/recolouring. **Building LOD**: generally not needed — one building's own surface count is already a single reasonable draw-call target. | Three.js/general WebGL performance practice — draw-call/geometry-merging guidance, Utsubo "100 Three.js Tips" (2026-03-22): https://www.utsubo.com/blog/threejs-best-practices-100-tips ; glTF `EXT_mesh_features` for feature-ID-preserving batching is the OGC/Khronos 3D Tiles Next mechanism (see Table 3 row on merging). |
| 3D-Tiles streaming (load only what's in view, at the needed detail) | Loads/renders only the tiles intersecting the view frustum, at the detail level (LOD) the current screen-space error (SSE) demands, via a hierarchical bounding-volume tree with ADD/REPLACE refinement. This is the mechanism that lets a scene scale past "everything in memory at once." Lossless in principle: nothing is destroyed, just deferred/unloaded, and can always be reloaded. | Medium-high complexity: requires generating a tileset hierarchy (tile a neighbourhood into a bounding-volume tree, author `geometricError` per tile, choose ADD vs REPLACE per level) — a real authoring/build step beyond exporting one glb. Well-trodden path via `3d-tiles-renderer`/CesiumJS. | **Neighbourhood LOD**: strong fit for city-to-neighbourhood scale (this is exactly the regime 3D Tiles targets: the Netherlands 10-million-building LoD1/LoD2 dataset uses this pattern, see Table 2). **Building LOD**: only relevant if you tile *inside* one building (many surfaces/sub-surfaces) — likely unnecessary at OpenUBEM's per-building surface counts; a single glb per building is simpler. | OGC 3D Tiles Specification, current version **1.1**, CesiumGS/3d-tiles spec repo (accessed 2026-07-02): https://github.com/CesiumGS/3d-tiles/blob/main/specification/README.adoc ; OGC-ratified standard 22-025r4 (2024) and prior 1.0 as OGC 18-053r2: https://docs.ogc.org/cs/18-053r2/18-053r2.html |
| Mesh decimation/simplification per LOD | Reduces triangle count of a mesh while minimizing visual/geometric error, via edge-collapse using the quadric error metric (QEM, Garland & Heckbert). Standard technique to produce cheaper LOD tiers for distant/small-on-screen geometry. **Lossy**: alters the actual vertex positions/topology, i.e. is *not* the real simulated shape once applied. | Medium complexity to integrate (established libraries: `meshoptimizer`, Blender decimate modifier, CesiumJS/3D-Tiles-Tools pipelines use QEM-family algorithms); complexity is in choosing a per-LOD error threshold and *not* applying it where the fidelity/no-invented-geometry rule (00_README hard constraint #1) is violated. | **Neighbourhood LOD**: acceptable — masses-only geometry (walls/roofs, no windows) simplified for distant/small buildings does not, by construction, misrepresent detail the LOD never claimed to show. **Building LOD**: high risk — decimating a building's actual surfaces (the ones a user is inspecting up close, possibly colour-heat-mapped) can visibly distort the real simulated shape; see Table 3 for the explicit off-limits case. | Garland, M. & Heckbert, P.S., "Surface Simplification Using Quadric Error Metrics," SIGGRAPH 1997 (foundational, cited widely, e.g. via ResearchGate record): https://www.researchgate.net/publication/2417323_Surface_Simplification_Using_Quadric_Error_Metrics ; general QEM-as-industry-standard characterization corroborated by search-aggregated literature (2015–2022 follow-on papers, e.g. ISPRS Archives XLVIII-3-W2-2022) — GAP: could not verify the ISPRS paper's own numeric reduction figures (PDF unreadable within budget). |
| Frustum + occlusion culling | Skips rendering/selecting tiles or objects entirely outside the camera frustum (frustum culling) or fully hidden behind other geometry (occlusion culling). Purely a rendering-time decision — **lossless**, the data is untouched and reloads/reappears the instant it re-enters view or becomes unoccluded. | Low-medium complexity — frustum culling is close to free (standard in three.js/CesiumJS/WebGL engines by default); occlusion culling is more involved (Cesium's is "experimental" as of the cited 2022 feature) but delivers large wins in dense urban view angles. | **Both LODs**: universally applicable and cheap; this is the technique OpenUBEM should lean on hardest since it is lossless. Especially valuable at neighbourhood LOD in dense blocks where many buildings occlude each other from ground-level camera angles. | CesiumJS: "Fast Hierarchical Culling" blog, plane-masking frustum-culling optimization citing Sýkora & Jelínek, "Efficient View Frustum Culling" — reports **15% (Chrome) / 20–34% (Firefox) speedups**: https://cesium.com/blog/2015/08/04/fast-hierarchical-culling ; "Optimizing 3D Tiles Streaming in Cesium for Unreal with Occlusion Culling" (2022-08-18) — concrete numbers below in Table 2/4: https://cesium.com/blog/2022/08/18/occlusion-culling-cesium-for-unreal/ |

---

## Table 2 — Building-count regimes

| Regime | Recommended technique(s) | Recommended stack alignment (cross-ref `V06`) | Expected interactive frame-rate class (rough order of magnitude, flag as estimate) | Source |
|---|---|---|---|---|
| Tens of buildings | No special scale engineering needed: frustum culling (free/default) is sufficient; a single glb/scene with per-building feature IDs for selection/recolouring is fine; QEM decimation and 3D-Tiles streaming are not necessary at this count. | Any of the `V06` candidate stacks (three.js, CesiumJS, deck.gl) can handle this directly without a tiling build step. | **ESTIMATE**: comfortably 60fps on desktop and most mobile — draw-call count for tens of buildings' worth of walls/roofs/windows stays well under the ~100-desktop-draw-call budget (Table 4) even without merging. | Own synthesis from Table 1 techniques + Utsubo draw-call budget (2026-03-22): https://www.utsubo.com/blog/threejs-best-practices-100-tips — **no dedicated tens-of-buildings benchmark found within budget; frame-rate figure is an estimate, not benchmarked.** |
| Hundreds of buildings | Batching/merging of static masses-only geometry with preserved feature IDs (Table 1) to keep draw calls under budget; frustum + occlusion culling; QEM-simplified LOD tier for buildings far from camera or small on screen; GPU instancing where literal repeats exist (e.g. repeated window units at building LOD). 3D-Tiles tiling becomes worth the authoring cost near the top of this range. | `V06`'s geospatial-tile-aware stacks (CesiumJS, or three.js + `3d-tiles-renderer`) start to earn their complexity here over a plain three.js scene graph. | **ESTIMATE**: interactive (30–60fps) achievable on desktop with the above techniques applied; mobile/low-end likely needs the mobile draw-call budget (<50, Table 4) actively enforced via merging. **Not directly benchmarked for OpenUBEM's specific geometry** — flagged GAP for a precise figure. | Own synthesis; draw-call budget figures per Utsubo (2026-03-22, cited above) and general three.js forum guidance (aggregated, not independently re-verified per-thread within budget). |
| Thousands of buildings | Full 3D-Tiles streaming (hierarchical bounding-volume tree, SSE-driven refinement, ADD/REPLACE) is the appropriate technique at this scale — it is the pattern used for the cited 10-million-building Netherlands dataset. Combine with occlusion culling, QEM per-tile LOD, batching within tiles, and instancing for repeats. | `V06` cross-ref: this regime is where CesiumJS (native 3D Tiles support) or three.js + `3d-tiles-renderer`/`3DTilesRendererJS` clearly outperforms a naive deck.gl/plain-three.js scene-graph approach — matches the peer precedent (Netherlands buildings viewer uses 3D Tiles + `3DTilesRendererJS`). | **GAP** — no benchmarked frame-rate figure for a WebGL city-scale (thousands-of-buildings) interactive session was retrievable within the 6-search/10-fetch budget; the closest precedent found (10 million Dutch buildings, LoD1/LoD2) documents that a 3D-Tiles-based web viewer *was built and is usable*, but does not state fps/hardware in the abstract fetched. **Do not fabricate a number here.** | Peters, R., Dukai, B., Vitalis, S., van Liempt, J., & Stoter, J. (2021), "Automated 3D reconstruction of LoD2 and LoD1 models for all 10 million buildings of the Netherlands," arXiv:2201.01191 [cs.CV] — confirms 3D-Tiles-style viewer exists at 10M-building scale, no fps figure surfaced in abstract: https://arxiv.org/abs/2201.01191 ; general architecture corroborated by Kang et al., "Developing a Tile-Based Rendering Method to Improve Rendering Speed of 3D Geospatial Data with HTML5 and WebGL," Journal of Sensors, 2017 (title/venue only verified via search snippet, not fetched — GAP on its specific numbers): https://onlinelibrary.wiley.com/doi/10.1155/2017/9781307 |

**OpenUBEM's actual regime** (per the 00_README shared facts — "tens, hundreds, or potentially thousands of buildings"): the manager should confirm actual cell sizes from the pipeline's own city-cell inventories; this researcher was not given specific building-count figures for the live OSM cells (e.g. `nyc_centre`, `la_urban`) and flags that as **GAP** per the prompt's own instruction ("citing the building-count figures the manager already has, or flag as GAP if unknown to the researcher"). Based on typical OpenUBEM neighbourhood-cell descriptions elsewhere in the docs (hundreds of buildings per cell is the commonly-referenced order of magnitude), the **Hundreds-of-buildings regime is the most likely design target**, with the **Thousands regime as the ceiling to architect for** (so the pipeline doesn't need a re-architecture the day a larger cell is added).

---

## Table 3 — Faithful-to-model tension — which simplifications are off-limits

| Technique | Does it alter geometry a user could mistake for the real simulated shape? | Does it alter or hide a colour-encoded value? | Verdict (safe to use freely / use only at neighbourhood LOD / never use) | Source |
|---|---|---|---|---|
| Mesh decimation on a building being colour-heat-mapped | **Yes** — QEM edge-collapse moves vertices and removes surface subdivisions; on a building actively showing a per-surface heat-map (e.g. solar irradiance, per-zone EUI at zone-resolution mode) this directly falsifies which physical surface a colour belongs to. | **Yes** — if colour is bound per-surface/per-vertex, decimation merges/removes the very surfaces the colour was bound to, silently losing or blending distinct colour-encoded values. | **Never use** on the building currently selected/inspected for a colour-encoded output; **use only at neighbourhood LOD** (masses-only, category-level colour such as function/archetype, not per-surface heat-maps) where the geometry being shown was never claiming sub-surface fidelity in the first place. | Derived from OGC 3D Tiles SSE/refinement model (geometric error is explicitly tied to "the tile's simplified representation of its source geometry" — CesiumGS/3d-tiles spec, https://github.com/CesiumGS/3d-tiles/blob/main/specification/README.adoc) plus OpenUBEM's own hard constraint #1 (00_README_3dviz_prompt_set.md, faithful-to-model, no silently misrepresented values). |
| Impostor/billboard replacement at extreme distance | **Yes, by design** — a billboard is a 2D image standing in for 3D geometry; it is explicitly *not* the real shape, only a visual placeholder for far-away, screen-tiny objects. | **Depends** — a billboard *can* carry a single flat colour (e.g. an average heat-map value) but cannot show per-surface variation; using one for a colour-encoded building risks implying more precision than it has. | **Use only at neighbourhood LOD, and only for buildings so distant/small-on-screen that their true silhouette is not discernible anyway** (this is standard practice for city-scale scenes generally, e.g. CesiumJS's tile SSE threshold governs exactly this kind of swap) — **never** for a building the user has selected or zoomed into (building LOD). Must be disclosed as a placeholder (not a rule found explicitly in the fetched sources but a direct consequence of OpenUBEM's hard constraint #1). | Extrapolated from OGC 3D Tiles SSE-driven refinement concept (same source as above) — **GAP**: no source specifically benchmarking impostor use for UBEM/building visualization was found within budget; this row is a synthesis, not a cited technique-specific claim. |
| Culling a building entirely out of the frame | **No** (when the building is genuinely outside the camera frustum or genuinely 100% occluded) — culling doesn't distort geometry, it just doesn't draw it this frame; the data still exists and reappears the instant it's back in view. | **No**, same reasoning — the colour-encoded value is not altered, only not currently drawn. | **Safe to use freely** as a lossless, frame-local decision — *but* this is exactly the case the no-silent-caps rule (Part C below) must guard: culling must never be confused with *dropping* a building from the dataset/analysis. The 00_README's own "no silently dropped building" language (from this prompt's Part C requirement) applies to any UI aggregate (counts, totals) computed while some buildings are culled — those aggregates must say "of N total" not just "of the M currently drawn." | CesiumJS "Fast Hierarchical Culling" (2015) and "Optimizing 3D Tiles Streaming... with Occlusion Culling" (2022-08-18) — both describe culling as reversible/frame-local by construction: https://cesium.com/blog/2015/08/04/fast-hierarchical-culling ; https://cesium.com/blog/2022/08/18/occlusion-culling-cesium-for-unreal/ |
| Merging distinct buildings into one batched mesh for draw-call reduction | **Only if feature IDs are dropped** — geometrically, merging positions/triangles into one buffer does not move a single vertex, so the *shape* is preserved exactly; the risk is entirely about **losing per-building identity** for selection/recolouring, not about the shape itself. | **Yes, if done naively** — a single merged mesh without per-primitive feature IDs cannot be selectively recoloured per building, which directly breaks OpenUBEM's attribute-driven recolouring requirement (categorical function, sequential population, output heat-maps per `V09`). | **Safe to use freely only when per-building feature IDs are preserved** (glTF `EXT_mesh_features`/3D-Tiles batch-table-equivalent mechanism); **never use** in a way that loses the ability to pick out and recolour an individual building — that would functionally break the viewer's core interaction requirement, independent of the faithful-to-model rule. | glTF `EXT_mesh_gpu_instancing` README (for the general instancing/batching pattern and its stated limitations around per-instance differentiation): https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Vendor/EXT_mesh_gpu_instancing/README.md ; general three.js geometry-merging guidance (Utsubo, 2026-03-22): https://www.utsubo.com/blog/threejs-best-practices-100-tips |

---

## Table 4 — Budgets and mobile target

| Metric | Target/budget | Source |
|---|---|---|
| Draw calls per frame (desktop target) | **< 100 draw calls/frame** for smooth 60fps, per general three.js/WebGL practice. | Utsubo, "100 Three.js Tips That Actually Improve Performance" (2026-03-22): https://www.utsubo.com/blog/threejs-best-practices-100-tips — **this is a general WebGL guideline, not a benchmark specific to UBEM/city-scale scenes; flagged as an industry rule-of-thumb, not a measured OpenUBEM figure.** |
| Triangle count per frame (desktop target) | **GAP for a precise per-frame number** — the fetched source explicitly states "triangle count matters less than draw call count" for modern GPUs and declines to give a hard scene-wide triangle budget; a commonly cited *rough* community figure (unverified within budget, from earlier search snippet on general asset budgets) is on the order of **hundreds of thousands of triangles** for broad device compatibility (e.g. ~500k as an outer bound), but this was not independently confirmed by a fetched primary source — treat as **weak estimate**, not fact. | Utsubo (2026-03-22, cited above) for the "draw calls matter more than triangles" framing; the ~500k figure comes from an unfetched search snippet (three.js community discussion aggregation) and is marked **GAP / unverified**. |
| Memory footprint ceiling (desktop browser tab) | **GAP** — no source within the search/fetch budget gave a concrete VRAM/tab-memory ceiling for a city-scale WebGL scene. The one concrete adjacent figure found: a single 4K texture alone consumes **~64MB+ of VRAM**, which bounds how many high-res textures a neighbourhood scene can afford before hitting typical integrated-GPU/mobile VRAM ceilings (commonly 256MB–1GB class devices), but no end-to-end scene memory budget was found. | Utsubo (2026-03-22, cited above) for the 4K-texture VRAM figure; overall ceiling is **GAP**. |
| Mobile/low-end target (if in scope — state whether OpenUBEM should target mobile at all) | If mobile is targeted: **< 50 draw calls/frame**, `mediump` shader precision (~2x faster than `highp`), 512–1024px shadow maps, ≤2 cascaded shadow map splits (vs. 4 on desktop), aggressive use of merging/instancing/LOD to hit the tighter budget. **Recommendation for OpenUBEM (own synthesis, not a cited mandate)**: given the two hard constraints (faithful-to-model, reproducible/open-source, per 00_README) and that OpenUBEM's primary users are researchers/analysts inspecting neighbourhood-scale energy results rather than a consumer mobile audience, **desktop-first is the pragmatic target; mobile support is a stretch goal, not a requirement**, and should not be allowed to drive lossy-technique decisions (e.g. more aggressive decimation) at the expense of the faithful-to-model rule. | Utsubo (2026-03-22, cited above) for the mobile numeric budgets; the "desktop-first, mobile-stretch" recommendation is this researcher's own synthesis against OpenUBEM's stated constraints, not a cited external source — **flagged as synthesis, not fact.** |

---

## Part C — Synthesis (the scale strategy)

**(1) Recommended technique stack for OpenUBEM's realistic neighbourhood sizes.**
The manager's own shared facts describe OpenUBEM cells as ranging from "tens, hundreds, or potentially
thousands of buildings" without pinning an exact figure for the live cells (`nyc_centre`, `la_urban`,
Boston, Torino-style cells) — this researcher does **not** have the precise per-cell building counts and
flags that as **GAP: needs manager decision from the pipeline's own cell inventory**. Architecting for the
**hundreds-of-buildings regime as the common case, with the thousands-of-buildings regime as the ceiling**
is the defensible default: build on a stack that scales into 3D Tiles (CesiumJS, or three.js +
`3d-tiles-renderer`, per `V06`) from day one, rather than a flat-scene approach that would need a rewrite
if a bigger cell shows up. Concretely: (a) generate every building as a feature-ID-tagged glb/3D-Tiles tile
with `EXT_mesh_gpu_instancing` used only for literally-repeated sub-elements (e.g. window units); (b) tile
the neighbourhood into a bounding-volume hierarchy with masses-only content at coarse SSE tiers and
surfaces+sub-surfaces content only at fine SSE tiers (ties directly to the `V04` LOD ladder); (c) turn on
frustum + occlusion culling by default everywhere (free, lossless); (d) reserve QEM decimation for the
coarse/distant tiers only, never for a building under active inspection or colour-heat-mapped.

**(2) The "never silently drop a building" rule.**
Culling and streaming are frame-local and reversible by construction (Table 3) — they must never be
confused with the dataset actually losing a building. Concretely: (a) any on-screen count/legend/summary
statistic (e.g. "N buildings shown," an aggregate EUI, a population total) computed from currently-rendered
geometry must be labelled against the *true total* in the loaded neighbourhood, not silently computed only
over what's drawn this frame — e.g. "312 of 480 buildings in view" rather than an unlabelled "312"; (b) a
persistent, visible indicator (a corner badge or status line, in the spirit of OpenUBEM's own
no-silent-caps discipline) must show when tiles are still streaming in (3D-Tiles progressive loading) so a
user does not mistake "not yet loaded" for "doesn't exist"; (c) if a building fails to tile/stream
(load error, malformed geometry) it must appear as an explicit error/placeholder marker, never simply
absent with no trace.

**(3) The off-limits list, as a hard rule.**
From Table 3: **never** decimate or impostor-replace a building that is (a) currently selected/inspected at
building LOD, or (b) actively displaying a per-surface colour-encoded simulation output (heat-map). Mesh
decimation and impostor/billboarding are permitted **only** at neighbourhood LOD, on masses-only geometry,
for buildings distant/small enough on screen that sub-surface detail was never being claimed in the first
place. Merging buildings into a shared batched mesh is permitted only when per-building feature IDs are
preserved for selection/recolouring — losing that identity is a functional break, independent of the
faithful-to-model rule. Frustum culling, occlusion culling, GPU instancing (of true repeats), and
feature-ID-preserving batching are lossless and safe to use freely at any LOD.

**(4) The single biggest scale risk for OpenUBEM's specific geometry, and its mitigation.**
The biggest risk is OpenUBEM's **high per-building sub-surface count at building/zone resolution mode** —
each building can carry many windows/doors as distinct sub-surfaces (per the 00_README's shared facts: wall,
roof, floor, window, shading categories, plus per-zone geometry when a building was simulated in `zone`
resolution mode), which multiplies both triangle count and — more importantly per Table 4 — **draw-call
count** if each sub-surface is a separate primitive/material batch. Because the fetched guidance is explicit
that draw-call count, not triangle count, is the dominant WebGL cost driver, the mitigation is **not**
mesh decimation (which would violate faithful-to-model at building LOD) but **draw-call-reducing, lossless
techniques**: GPU-instance repeated window units within a facade (`EXT_mesh_gpu_instancing`), and batch
same-material sub-surfaces within one building into a single draw call while preserving per-surface feature
IDs so a per-surface heat-map (V11) still works. This keeps the real geometry and real per-surface data
fully intact while controlling the cost driver that actually matters.

---

## Confidence and caveats

- **Benchmarked (has a named, dated, numeric source):** Cesium occlusion-culling primitive/tile-count
  reductions (192→96 primitives, 93→51 tiles, ~15–34% frustum-culling speedups) — these are Cesium's own
  published figures, not OpenUBEM measurements, and were obtained in Cesium for Unreal / Cesium-native
  contexts, not a browser three.js UBEM scene; treat as directionally indicative only.
- **Rough estimate / rule-of-thumb, not benchmarked for OpenUBEM's geometry:** all Table 2 frame-rate
  classes ("tens/hundreds/thousands of buildings → X fps") are this researcher's synthesis from general
  WebGL draw-call guidance, **not** a measured OpenUBEM or directly-comparable UBEM benchmark. No published
  frame-rate figure for an interactive thousands-of-buildings WebGL/3D-Tiles city session was retrievable
  within the 6-search/10-fetch budget.
- **GAP, explicitly flagged, needing manager decision:**
  - OpenUBEM's actual live-cell building counts (needed to pin which Table 2 regime applies) — not
    available to this researcher.
  - Triangle-count-per-frame and memory-footprint-ceiling budgets (Table 4) — no primary source gave hard
    numbers within budget; only adjacent proxies (4K texture VRAM cost) were found.
  - The ISPRS Archives XLVIII-3-W2-2022 quadric-error-metric paper's own numeric reduction figures — PDF
    was fetched but returned unreadable binary/compressed content within the single-fetch budget; citation
    (title, venue, year) is confirmed via search snippet only, not its numbers.
  - Kang et al. 2017 (Journal of Sensors) tile-based-rendering benchmark numbers — title/venue/year
    confirmed via search snippet only; not fetched for its specific figures (budget spent on higher-priority
    fetches).
  - Impostor/billboard-for-buildings-specifically source — no UBEM/city-viz-specific citation found within
    budget; that row's verdict is a reasoned extrapolation from the 3D-Tiles SSE model, not a directly
    cited technique benchmark.

---

## Reference list

1. Khronos Group, `EXT_mesh_gpu_instancing` extension README, KhronosGroup/glTF repository, `main` branch,
   status "Complete, Ratified by Khronos Group" (accessed 2026-07-02).
   https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Vendor/EXT_mesh_gpu_instancing/README.md
2. CesiumGS, 3D Tiles Specification, version 1.1, `specification/README.adoc`, CesiumGS/3d-tiles repository
   (accessed 2026-07-02). https://github.com/CesiumGS/3d-tiles/blob/main/specification/README.adoc
3. OGC (Open Geospatial Consortium), 3D Tiles Community Standard 1.0, document 18-053r2.
   https://docs.ogc.org/cs/18-053r2/18-053r2.html (not fully fetched — content exceeded fetch size limit;
   version/date corroborated via reference 2 and search-result metadata instead).
4. OGC, 3D Tiles Specification, document 22-025r4 (search-indexed as the current OGC-ratified successor;
   full text not fetched within budget). https://docs.ogc.org/cs/22-025r4/22-025r4.html
5. Garland, M. & Heckbert, P. S. (1997). "Surface Simplification Using Quadric Error Metrics."
   Proceedings of SIGGRAPH 1997. Cited via ResearchGate record (accessed 2026-07-02, abstract-level only):
   https://www.researchgate.net/publication/2417323_Surface_Simplification_Using_Quadric_Error_Metrics
6. [Author(s) unconfirmed within budget], "A Novel Quadratic Error Metric Mesh Simplification Algorithm,"
   ISPRS Archives, Vol. XLVIII-3/W2-2022 (2022) — citation title/venue/year only, via search snippet; PDF
   fetch failed to yield readable text within budget.
   https://isprs-archives.copernicus.org/articles/XLVIII-3-W2-2022/109/2022/isprs-archives-XLVIII-3-W2-2022-109-2022.pdf
7. Peters, R., Dukai, B., Vitalis, S., van Liempt, J., & Stoter, J. (2021). "Automated 3D reconstruction of
   LoD2 and LoD1 models for all 10 million buildings of the Netherlands." arXiv:2201.01191 [cs.CV].
   https://arxiv.org/abs/2201.01191
8. Kang, H. et al. (2017). "Developing a Tile-Based Rendering Method to Improve Rendering Speed of 3D
   Geospatial Data with HTML5 and WebGL." Journal of Sensors, 2017. Article ID 9781307 — title/venue/year
   only, via search snippet, not independently fetched within budget.
   https://onlinelibrary.wiley.com/doi/10.1155/2017/9781307
9. Cesium GS, Inc. "Fast Hierarchical Culling" (2015-08-04), citing Sýkora, J. & Jelínek, A., "Efficient
   View Frustum Culling." https://cesium.com/blog/2015/08/04/fast-hierarchical-culling
10. Cesium GS, Inc. "Optimizing 3D Tiles Streaming in Cesium for Unreal with Occlusion Culling"
    (2022-08-18). https://cesium.com/blog/2022/08/18/occlusion-culling-cesium-for-unreal/
11. Utsubo. "100 Three.js Tips That Actually Improve Performance" (2026-03-22).
    https://www.utsubo.com/blog/threejs-best-practices-100-tips

---

*Executed as a bounded, single-pass deep-research task per `docs_ACTIVE/3D/deepResearch/V12_performance_scale_prompt.md`
and `00_README_3dviz_prompt_set.md`. 6/6 web searches, 9/10 fetches used, no sub-agents/skills invoked.
2026-07-02.*
