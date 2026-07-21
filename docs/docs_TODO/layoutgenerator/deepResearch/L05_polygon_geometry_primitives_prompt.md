# Deep-Research Prompt L05 — POLYGON GEOMETRY PRIMITIVES (offset, skeleton, medial axis, decomposition — the slicing toolkit)

> SCOPE GUARD — READ FIRST. This is the **algorithms** prompt — the computational-geometry toolkit that
> physically cuts an arbitrary footprint into corridor + core + perimeter zones. Deliver a method-by-
> method appraisal of the primitives (**inward offset / buffer**, **straight skeleton**, **medial axis**,
> **rectangular / convex polygon decomposition**, **polygon partitioning / slab-strip cutting**),
> stating for each: what it computes, which shape it slices well, its robustness/failure modes, and its
> availability in the Python geometry stack OpenUBEM uses (`shapely`, `geomeppy`, and candidate libs).
> Do NOT classify shapes (that's `L04`), do NOT define the room program placed into the slices (that's
> `L06`+), and do NOT design the corridor rules (that's `L06`). See
> `00_README_layoutgenerator_prompt_set.md` for shared facts.

---

## What this document is

The engineering-primitives reference. Once `L04` has classified a footprint, `layoutGenerator.py` must
*cut* it — place a corridor along the spine, offset the perimeter band, split an L into rectangular
wings. Each of those is a named computational-geometry operation with known algorithms, libraries, and
failure modes. OpenUBEM today uses exactly one primitive — `shapely` inward `buffer(-4.57)` — and it
fails on courtyards (donut core → E+ Fatal) and narrow shapes (empty core). This prompt gives the manager
the full toolkit and, critically, **which primitives are available and robust in `shapely`/`geomeppy`
vs. which need a new dependency**, so the plan can pick implementable methods.

## Role

Computational-geometry / GIS-algorithms research analyst with a Python-implementation focus. Ground each
primitive in its canonical source: **inward offsetting / Minkowski erosion** (`shapely.buffer` negative,
and the CGAL/Clipper polygon-offset literature); **straight skeleton** (Aichholzer & Aurenhammer 1996;
the `scikit-geometry`/CGAL and `bpypolyskel` implementations); **medial axis** (Blum; `scipy`/`skimage`
medial-axis transform on rasterized polygons); **rectangular decomposition / partition into rectangles**
(the orthogonal-polygon partition literature); **convex decomposition** (Hertel–Mehlhorn; `CGAL`);
**trapezoidal/slab decomposition**. For each, name the concrete Python library and whether it is
maintained and license-compatible.

## Why this matters (so you scope correctly)

The whole feasibility of `layoutGenerator.py` hinges on which of these primitives is robust and available.
A straight skeleton gives a clean corridor spine for an L/U/T but is notoriously fragile numerically and
under-supported in pure Python; rectangular decomposition is more robust but blocky; the medial axis needs
rasterization (introducing a resolution parameter — a zero-fitted-parameters risk). This prompt must tell
the manager the *robust, implementable* path, not the theoretically-elegant one.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — The geometry-primitive catalogue

| Primitive | What it computes | Shape it slices well | Output (lines / sub-polygons / skeleton graph) | Failure / numerical-robustness mode | Source |
|---|---|---|---|---|---|
| Negative buffer / inward offset (Minkowski erosion) |  | compact convex | perimeter band + core |  | Clipper/CGAL |
| Straight skeleton |  | L/U/T/most | roof/spine skeleton graph |  | Aichholzer & Aurenhammer |
| Medial axis (transform) |  | elongated / corridor spine | centerline |  | Blum; skimage |
| Rectangular (orthogonal) decomposition |  | rectilinear L/U/T/O | set of rectangles |  |  |
| Convex decomposition |  | any simple polygon | set of convex parts |  | Hertel–Mehlhorn |
| Slab / trapezoidal decomposition |  | any | vertical strips |  |  |
| Skeleton-guided offset (corridor = offset of skeleton) |  | L/U/T | corridor polygon |  |  |

### Table 2 — Availability & fitness in OpenUBEM's stack

| Primitive | Available in `shapely`? | Available in a maintained Python lib (name + license)? | Needs rasterization (introduces a resolution param)? | Pure-geometry / zero-fitted-parameters? | Implementable now vs. new dependency |
|---|---|---|---|---|---|
| Negative buffer | **Yes** (`buffer(-d)`) | — | No | Yes | now (already used) |
| Straight skeleton |  |  |  |  |  |
| Medial axis |  |  |  |  |  |
| Rectangular decomposition |  |  |  |  |  |
| Convex decomposition |  |  |  |  |  |
| Slab decomposition |  |  |  |  |  |

### Table 3 — Which primitive for which shape → which zoning output

| Footprint class (from L04) | Recommended primitive(s) | Resulting zone layout | Why this primitive | Source |
|---|---|---|---|---|
| Compact rectangle | negative buffer | core + 4 perimeter | already works |  |
| L / U / T | ? | corridor spine + perimeter rooms, or wings each core/perim |  |  |
| O / courtyard | ? | perimeter ring + inner-ring corridor (no solid core) |  |  |
| Elongated slab | ? | single central corridor + 2 room rows |  |  |
| Irregular blob | ? | fallback (single-zone-per-floor) |  |  |

### Table 4 — Robustness engineering (avoiding the geomeppy E+ Fatal)

| Risk | Mitigation from the literature/practice | Source |
|---|---|---|
| Sliver polygons from offset (degenerate zones) |  |  |
| Non-manifold / self-touching offset result |  |  |
| Donut/hole core → mismatched inter-floor vertices (OpenUBEM's current fatal) |  |  |
| Vertex-count explosion (E+ zone-surface limits / runtime) |  |  |
| Small-angle / near-collinear vertices |  |  |

---

## Part C — Synthesis (the implementable toolkit)

Give: (1) the **recommended primitive per shape class** — the robust, `shapely`-expressible choice, not
the elegant-but-fragile one; (2) an explicit **build-vs-add-dependency** call for each non-`shapely`
primitive (straight skeleton, decomposition) with the specific library name, maintenance status, and
license; (3) the **robustness recipe** that avoids the current geomeppy fatal (courtyard/donut handling,
sliver cleanup, vertex-count cap); (4) whether any primitive introduces a resolution/tuning parameter that
threatens zero-fitted-parameters, and how to pin it.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C toolkit synthesis.
3. Cite the algorithm's canonical source and, separately, the Python-library docs for availability.
4. **"Confidence and caveats":** which primitive's Python maturity is least certain.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **For every primitive, state the concrete Python library + license + maintenance status** — "exists in
  CGAL" is not enough; name the usable Python binding or say GAP.
- **Explicitly give the courtyard/donut mitigation** — this is OpenUBEM's current hard failure.
- **Flag any primitive that needs a rasterization resolution or tuning parameter** (zero-fitted-parameters
  risk) and how to fix it to a published value.
- **No fabricated precision;** flag GAPs. **Stay on topic** — geometry *algorithms & libraries* only, not
  shape detection (`L04`) or room programs (`L06`+).
