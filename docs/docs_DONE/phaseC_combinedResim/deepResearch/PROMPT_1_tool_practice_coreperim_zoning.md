# Prompt 1 — How established UBEM/BEM tools generate core/perimeter zones and handle degenerate footprints

**Run this in Google Antigravity (deep web research). Save the answer per the instruction at the bottom.**

**Why this prompt:** OpenUBEM slices each building footprint into a *core* zone plus *perimeter* zones (ASHRAE-style automatic thermal zoning) before EnergyPlus simulation. On real OpenStreetMap footprints this step fails on awkward shapes — multi-part polygons, razor-thin "sliver" perimeter zones, inverted winding, and mismatched interzone surface vertex counts — which either crash EnergyPlus or drop the building. Our proposed fix is **graceful degradation**: any degenerate decomposition falls back to a coarser "one thermal zone per floor" model. Before we commit to that, we need a literature/tooling review of **how mature urban and single-building energy-modeling tools actually do automatic core/perimeter zoning, and specifically what they do when the geometry is too awkward to zone cleanly.** This prompt gathers concrete examples and named strategies — not opinions.

---

```
You are a building-energy-modeling tools analyst. I need a rigorous, citeable review of how
established Urban Building Energy Modeling (UBEM) and building-energy-modeling (BEM) tools perform
AUTOMATIC THERMAL ZONING of a building footprint into a CORE zone plus PERIMETER zones, and — most
importantly — what FALLBACK or robustness strategy each uses when a footprint is too awkward to zone
cleanly (non-convex / concave footprints, narrow wings, courtyards/interior holes, multi-part
polygons, slivers).

Do deep web research across documentation, source code, and peer-reviewed papers. Cover at least
these tools (add others if relevant):
- City Energy Analyst (CEA)
- URBANopt + NREL openstudio-standards (the create-typical/space-type + zoning logic)
- Ladybug Tools: Dragonfly / Honeybee (the "perimeter offset" / core-perimeter zoning component)
- ORNL AutoBEM / AutoBEM2
- UMI (MIT) and the umi/archetype workflow
- TEASER (RWTH) and CityBES (LBNL)
- geomeppy (the library OpenUBEM uses) and the EnergyPlus "Floorplan/auto-zoning" features
- OpenStudio's "make perimeter/core zones" measure(s)

For EACH tool, report:
1. WHETHER it auto-generates core+perimeter zones, and the exact ALGORITHM/method named in its docs
   or code (e.g. fixed perimeter-depth offset, straight skeleton, medial axis, polygon buffering /
   inward offset, intersect/match). Cite the doc page, source file, or paper.
2. The PERIMETER DEPTH it uses (commonly ~4.57 m / 15 ft) and whether it is configurable.
3. ROBUSTNESS / FAILURE HANDLING — the key question: what happens when the footprint is concave,
   has a courtyard hole, produces a self-intersecting or zero/negative-area perimeter ring, or yields
   a sliver zone? Does the tool (a) fall back to a single zone / one-zone-per-floor, (b) simplify the
   footprint first, (c) skip the building, (d) use a more robust offset algorithm, or (e) something
   else? Quote the doc/code where this is stated.
4. Whether the tool SIMPLIFIES or pre-cleans footprints (vertex collapse tolerance, convex-hull,
   buffer(0), largest-part selection for multi-polygons) before zoning, and the tolerances used.

Then give a SYNTHESIS section:
- A comparison table [Tool | Zoning method | Perimeter depth | Degenerate-shape fallback | Pre-clean/simplify | Source].
- The most common fallback strategy across tools, and whether "fall back to one-zone-per-floor (or a
  single core zone) when perimeter zoning degenerates" is an ACCEPTED, documented practice in the field.
- Any tool that uses a MORE ROBUST perimeter-offset algorithm (e.g. straight skeleton) specifically
  to avoid slivers/self-intersection — name it and the library it uses.

Output as clean markdown with the comparison table and a full citation (title, author/org, year, URL,
access date) for every claim. If a tool's behavior on degenerate footprints is undocumented, SAY SO
EXPLICITLY rather than guessing. Flag anything you are not fully confident about.

WHEN FINISHED: save your full response as a markdown file named
`RESULT_1_tool_practice_coreperim_zoning.md` in the SAME FOLDER as this prompt document
(`docs/implementation/phaseC_combinedResim/deepResearch`).
```

---

**After researching, save your full response as a markdown file named**
`RESULT_1_tool_practice_coreperim_zoning.md` **in this folder:**
`C:\Users\o_iseri\Desktop\OpenUBEM\docs\implementation\phaseC_combinedResim\deepResearch`
