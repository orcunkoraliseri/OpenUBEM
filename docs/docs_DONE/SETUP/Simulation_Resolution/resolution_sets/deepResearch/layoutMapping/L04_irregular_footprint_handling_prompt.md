# Deep-Research Prompt L04 — IRREGULAR FOOTPRINT handling (adapting a prototype layout to real shapes)

> SCOPE GUARD — READ FIRST. This is a **geometry-robustness** task. The deliverable is how peer tools and
> the literature adapt a standardized prototype zone layout to **non-rectangular real footprints** —
> L/U/T shapes, slivers, very large or very small polygons, courtyards — including geometry
> **simplification/decomposition** steps and the **fallback ladder** to coarser zoning when the detailed
> layout cannot be built. It is NOT about the perimeter-split rule itself (Prompt L02) or corridors
> (L03); it is about surviving messy GIS geometry. If you are writing about anything other than **how
> irregular footprints are handled/simplified/fallen-back and the source**, stop and return to the tables.
> See `00_README_layout_mapping_prompt_set.md` for the decision, shared facts, conventions.

---

## What this document is

A fill-in-the-blanks request on geometry robustness. Real OSM footprints are noisy and non-convex;
geomeppy core/perim and any prototype-layout step can fatal (vertex mismatch, empty core, self-intersecting
offset). OpenUBEM already reverts to `one_zone_per_floor` for narrow/courtyard cases — we need the broader,
sourced ladder of simplification and fallback used by tools that auto-zone at city scale. Treat each cell
as a question.

## Role

UBEM geometry research analyst. Trace to: tool docs (URBANopt/OpenStudio geometry measures, CityBES
raster approach, AutoBEM polygon handling), **shapely/geomeppy** offset behaviour, computational-geometry
methods (Douglas–Peucker simplification, convex decomposition, straight skeleton, bounding-box proxy), and
UBEM papers reporting footprint-quality fallbacks. SI.

## Why this matters (so you scope correctly)

A detailed prototype layout is worthless if it crashes 10 % of a city's buildings. The question is how far
to push the detailed layout before degrading gracefully: simplify the polygon first? decompose into convex
parts and zone each? or detect the failure and drop to core/perimeter or single-zone? We need a sourced,
deterministic ladder so `zone` mode never crashes and the degradation is reported, not silent.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Footprint pre-processing before zoning

| Step | Purpose | Typical parameter | Used by | Source |
|---|---|---|---|---|
| Polygon simplification (Douglas–Peucker) | drop GIS noise vertices | tolerance ~? m |  |  |
| Convex decomposition | zone each convex part |  |  |  |
| Bounding-box / oriented-bbox proxy | last-resort regularization |  |  |  |
| Straight-skeleton partition |  |  |  |  |

### Table 2 — Behaviour per shape class

| Shape class | Detailed layout feasible? | Recommended handling | Fallback if it fails | Source |
|---|---|---|---|---|
| Rectangle / near-rectangle |  |  |  |  |
| L / U / T |  |  |  |  |
| Long thin sliver (width < 2× perimeter depth) |  | (perimeter-only) | one_zone_per_floor |  |
| Courtyard / donut |  |  | one_zone_per_floor (preserve) |  |
| Very small (< 100 m²) |  |  | one_zone_per_floor |  |
| Very large / many-sided |  |  |  |  |

### Table 3 — The fallback ladder (graceful degradation)

| Tier | Condition to trigger | Action | Source |
|---|---|---|---|
| 1 (detailed) |  | prototype layout (units + corridor / core+perim) |  |
| 2 |  | generic core + perimeter |  |
| 3 |  | one_zone_per_floor |  |
| 4 |  | single_zone |  |

### Table 4 — How peer tools report/handle degradation

| Tool | Detects bad geometry? | Degrades silently or logged? | City-scale success rate reported? | Source |
|---|---|---|---|---|
| URBANopt |  |  |  |  |
| CityBES |  |  |  |  |
| AutoBEM |  |  |  |  |

---

## Part C — Synthesis (robustness ladder)

Give: (1) the **pre-processing** OpenUBEM should apply to a raw OSM polygon before zoning (simplification
tolerance, when to decompose); (2) the **deterministic fallback ladder** (Table 3) with exact trigger
conditions, preserving the existing narrow/courtyard reverts; (3) the rule that **degradation is logged
per building** (which tier each building used) so coverage is auditable, never silent. Tie triggers to
measurable footprint properties (area, width/depth ratio, vertex count, has-hole).

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C robustness ladder.
3. Cite computational-geometry methods + ≥2 tools' real handling.
4. **"Confidence and caveats":** the shape most likely to slip through and crash E+ anyway.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Give a deterministic, ordered fallback ladder** with measurable triggers.
- **Preserve** the existing narrow-core and courtyard reverts to `one_zone_per_floor`.
- **Require per-building logging** of the tier used (no silent degradation).
- **No fabricated precision;** flag GAPs. **Stay on topic** — irregular-footprint geometry only.
