# Prompt 2 — Robust polygon-offset / perimeter-zone algorithms that avoid slivers and self-intersection

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** Our perimeter zones are made by offsetting the footprint inward, then splitting the ring into edge zones. On non-convex footprints this naive offset produces **slivers, self-intersections, and inverted (negative-area) zones** — the exact failures crashing EnergyPlus. Our current plan side-steps this with a coarse fallback (one-zone-per-floor). This prompt investigates whether a **more robust geometry algorithm** could keep proper core/perimeter zones on awkward shapes instead of falling back — i.e. is there a better fix that preserves thermal fidelity? It is the "is graceful degradation the best we can do, or is there a principled alternative" question, answered from the computational-geometry and BEM literature.

---

```
You are a computational-geometry and building-energy-modeling researcher. I need a rigorous, citeable
review of ROBUST algorithms for generating PERIMETER thermal zones by offsetting a building footprint
polygon inward, with the goal of AVOIDING the degeneracies that occur on non-convex / concave
footprints: razor-thin sliver zones, self-intersecting offset rings, inverted (negative signed-area)
zones, and collapse of the interior "core" region.

Do deep web research across computational-geometry literature, BEM tool source code, and papers.
Address:

1. THE STRAIGHT SKELETON approach: explain how the straight skeleton (and the related medial axis)
   is used to partition a polygon into perimeter "offset" regions plus a core, why it is more robust
   than naive buffering for concave polygons, and its known failure modes. Name concrete software
   libraries that compute it (e.g. CGAL straight_skeleton_2, the `scikit-geometry` binding,
   `bpypolyskel`, the OSM2World / Blender-OSM roof-skeleton code, any Python-accessible option) and
   note license + maturity for each.

2. NAIVE INWARD OFFSET / BUFFERING (e.g. Shapely `parallel_offset` / `buffer(-d)`, Clipper /
   pyclipper `ClipperOffset`): document WHY it produces slivers and self-intersections on concave
   shapes, what "miter limit" and "join style" do, and whether Clipper/pyclipper's offset is more
   robust than Shapely's for this use. Cite docs.

3. SLIVER / DEGENERACY DETECTION & CLEANUP: established criteria and tolerances for detecting and
   removing degenerate polygons — minimum area threshold, minimum perimeter-zone width, signed-area /
   winding-order checks (shoelace), aspect-ratio / thinness ratio, Douglas–Peucker simplification
   tolerance, snap-rounding. Give the commonly cited numeric thresholds and where they come from.

4. ZONE-MERGING as an alternative to dropping: methods that MERGE a degenerate perimeter sliver into
   an adjacent valid zone (rather than deleting it or falling back to a single zone), preserving more
   of the core/perimeter structure. Cite any BEM tool or paper that does this.

5. PRACTICAL RECOMMENDATION for a Python pipeline that currently uses Shapely + geomeppy: rank the
   realistic options — (a) keep naive offset + fall back to one-zone-per-floor on any degeneracy
   [our current plan], (b) switch the offset to pyclipper/Clipper with a miter limit, (c) adopt a
   straight-skeleton library, (d) merge slivers into neighbors — by robustness, implementation effort,
   external-dependency cost, and license compatibility with an open-source (permissive) project. Be
   explicit about which option best balances correctness vs. effort for a handful of pathological
   buildings out of thousands.

Output as clean markdown: a numbered section per topic, a final ranked-recommendation table
[Option | Robustness | Effort | New dependency + license | Fidelity kept], and a full citation
(title, author/org, year, URL, access date) for every claim. If a library's robustness on concave
polygons is unverified, SAY SO EXPLICITLY. Flag anything you are not fully confident about.

WHEN FINISHED: save your full response as a markdown file named
`RESULT_2_robust_offset_algorithms.md` in the SAME FOLDER as this prompt document
(`docs/implementation/phaseC_combinedResim/deepResearch`).
```

---

**After researching, save your full response as a markdown file named**
`RESULT_2_robust_offset_algorithms.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\implementation\phaseC_combinedResim\deepResearch`
